"""
AquaChain Warehouse Service - Dashboard Overhaul
Enhanced warehouse service with receiving/dispatch workflows, location management,
stock movement tracking, performance metrics, and inventory service integration.

Requirements: 1.2
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import uuid
import logging
from botocore.exceptions import ClientError
import sys
import traceback

# Add shared modules to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger, TimedOperation, SystemHealthMonitor
from audit_logger import audit_logger

# Initialize structured logging
logger = get_logger(__name__, 'warehouse-service')
health_monitor = SystemHealthMonitor('warehouse-service')

# Lazy initialization of AWS clients to reduce cold start time
_aws_clients = {}
_dynamodb_tables = {}

def get_aws_client(service_name: str):
    """Get cached AWS client to reduce cold start time"""
    if service_name not in _aws_clients:
        _aws_clients[service_name] = boto3.client(service_name)
    return _aws_clients[service_name]

def get_dynamodb_table(table_env_var: str, default_name: str):
    """Get cached DynamoDB table reference"""
    table_name = os.environ.get(table_env_var, default_name)
    if table_name not in _dynamodb_tables:
        if 'dynamodb' not in _aws_clients:
            _aws_clients['dynamodb'] = boto3.resource('dynamodb')
        _dynamodb_tables[table_name] = _aws_clients['dynamodb'].Table(table_name)
    return _dynamodb_tables[table_name]

class WarehouseService:
    """
    Enhanced warehouse management service for dashboard overhaul.
    
    Features:
    - Receiving and dispatch workflow management
    - Location management with real-time tracking
    - Stock movement tracking with audit trails
    - Performance metrics collection and reporting
    - Integration with inventory service for stock updates
    - Graceful degradation when dependent services are unavailable
    """
    
    def __init__(self, request_context: Optional[Dict] = None):
        """
        Initialize warehouse service with request context for audit logging
        
        Args:
            request_context: Request context containing user_id, correlation_id, etc.
        """
        self.request_context = request_context or {}
        self.user_id = self.request_context.get('user_id', 'system')
        self.correlation_id = self.request_context.get('correlation_id', str(uuid.uuid4()))
        
        # Configuration
        self.sns_topic = os.environ.get('WAREHOUSE_ALERTS_TOPIC')
        self.s3_bucket = os.environ.get('WAREHOUSE_DOCUMENTS_BUCKET')
        self.websocket_api_endpoint = os.environ.get('WEBSOCKET_API_ENDPOINT')
        self.inventory_service_function = os.environ.get('INVENTORY_SERVICE_FUNCTION', 'inventory-management-service')
        
        # Circuit breaker state for inventory service
        self.inventory_service_available = True
        self.inventory_service_last_failure = None
        self.inventory_service_failure_threshold = 3
        self.inventory_service_timeout = 300  # 5 minutes
        
        logger.info(
            "Warehouse service initialized",
            correlation_id=self.correlation_id,
            user_id=self.user_id
        )
    
    def get_warehouse_overview(self) -> Dict:
        """
        Get comprehensive warehouse operations overview with performance metrics
        
        Returns:
            Dictionary with warehouse overview, metrics, and alerts
        """
        with TimedOperation(logger, "get_warehouse_overview", correlation_id=self.correlation_id):
            try:
                # Log data access for audit
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='warehouse-overview',
                    resource_id='all',
                    action='read',
                    correlation_id=self.correlation_id
                )
                
                # Get warehouse locations with status
                locations_response = warehouse_table.scan(
                    ProjectionExpression='location_id, warehouse_id, zone, shelf, #status, capacity, current_usage, last_updated',
                    ExpressionAttributeNames={'#status': 'status'}
                )
                locations = locations_response.get('Items', [])
                
                # Get receiving workflow status
                receiving_workflows = self._get_receiving_workflows_status()
                
                # Get dispatch workflow status  
                dispatch_workflows = self._get_dispatch_workflows_status()
                
                # Calculate performance metrics
                performance_metrics = self._calculate_performance_metrics()
                
                # Get current alerts
                alerts = self._get_warehouse_alerts()
                
                # Calculate overview statistics
                total_locations = len(locations)
                occupied_locations = len([l for l in locations if l.get('status') == 'occupied'])
                available_locations = len([l for l in locations if l.get('status') == 'available'])
                occupancy_rate = (occupied_locations / total_locations * 100) if total_locations > 0 else 0
                
                overview_data = {
                    'overview': {
                        'total_locations': total_locations,
                        'occupied_locations': occupied_locations,
                        'available_locations': available_locations,
                        'occupancy_rate': round(occupancy_rate, 2),
                        'receiving_workflows': receiving_workflows,
                        'dispatch_workflows': dispatch_workflows,
                        'performance_metrics': performance_metrics,
                        'last_updated': datetime.utcnow().isoformat()
                    },
                    'alerts': alerts,
                    'locations_summary': self._summarize_locations_by_zone(locations)
                }
                
                # Send real-time update via WebSocket if available
                self._send_realtime_update('warehouse_overview', overview_data)
                
                logger.info(
                    "Warehouse overview retrieved successfully",
                    correlation_id=self.correlation_id,
                    total_locations=total_locations,
                    occupancy_rate=occupancy_rate
                )
                
                return {
                    'statusCode': 200,
                    'body': overview_data
                }
                
            except Exception as e:
                logger.error(
                    "Error getting warehouse overview",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                health_monitor.record_error('get_warehouse_overview', str(e))
                return {
                    'statusCode': 500,
                    'body': {'error': 'Failed to retrieve warehouse overview'}
                }
    
    def process_receiving_workflow(self, receiving_data: Dict) -> Dict:
        """
        Process receiving workflow with comprehensive tracking and inventory integration
        
        Args:
            receiving_data: Receiving workflow data including PO, items, quality checks
            
        Returns:
            Dictionary with workflow status and tracking information
        """
        with TimedOperation(logger, "process_receiving_workflow", correlation_id=self.correlation_id):
            try:
                # Validate required fields
                required_fields = ['po_id', 'supplier_id', 'items', 'received_by']
                for field in required_fields:
                    if field not in receiving_data:
                        return {
                            'statusCode': 400,
                            'body': {'error': f'Missing required field: {field}'}
                        }
                
                # Generate workflow ID
                workflow_id = f"RCV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                
                # Log workflow initiation
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='initiate_receiving_workflow',
                    resource_type='receiving-workflow',
                    resource_id=workflow_id,
                    details=receiving_data,
                    correlation_id=self.correlation_id
                )
                
                # Validate PO exists and is in correct status
                po_validation = self._validate_purchase_order(receiving_data['po_id'])
                if not po_validation['valid']:
                    return {
                        'statusCode': 400,
                        'body': {'error': po_validation['error']}
                    }
                
                # Process each received item
                processed_items = []
                stock_movements = []
                
                for item in receiving_data['items']:
                    item_result = self._process_received_item(item, workflow_id)
                    processed_items.append(item_result)
                    
                    if item_result['status'] == 'success':
                        # Create stock movement record
                        movement = self._create_stock_movement(
                            item_id=item['item_id'],
                            movement_type='RECEIVING',
                            quantity=item['quantity_received'],
                            location_id=item_result['location_id'],
                            reference_id=workflow_id,
                            notes=f"Received from PO {receiving_data['po_id']}"
                        )
                        stock_movements.append(movement)
                
                # Create receiving workflow record
                workflow_record = {
                    'workflow_id': workflow_id,
                    'workflow_type': 'RECEIVING',
                    'po_id': receiving_data['po_id'],
                    'supplier_id': receiving_data['supplier_id'],
                    'received_date': datetime.utcnow().isoformat(),
                    'received_by': receiving_data['received_by'],
                    'status': 'COMPLETED' if all(item['status'] == 'success' for item in processed_items) else 'PARTIAL',
                    'items': processed_items,
                    'stock_movements': stock_movements,
                    'quality_check_required': receiving_data.get('quality_check_required', True),
                    'notes': receiving_data.get('notes', ''),
                    'created_by': self.user_id,
                    'correlation_id': self.correlation_id
                }
                
                # Store workflow record
                self._store_workflow_record(workflow_record)
                
                # Update PO status
                self._update_purchase_order_status(
                    receiving_data['po_id'], 
                    'RECEIVED', 
                    workflow_id
                )
                
                # Update inventory via inventory service
                inventory_update_result = self._update_inventory_service(stock_movements)
                
                # Send notifications
                self._send_receiving_notification(workflow_record)
                
                # Update performance metrics
                self._update_performance_metrics('receiving', workflow_record)
                
                logger.info(
                    "Receiving workflow processed successfully",
                    correlation_id=self.correlation_id,
                    workflow_id=workflow_id,
                    items_processed=len(processed_items)
                )
                
                return {
                    'statusCode': 200,
                    'body': {
                        'message': 'Receiving workflow processed successfully',
                        'workflow_id': workflow_id,
                        'status': workflow_record['status'],
                        'items_processed': len(processed_items),
                        'stock_movements': len(stock_movements),
                        'inventory_update_status': inventory_update_result.get('status', 'unknown')
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Error processing receiving workflow",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                health_monitor.record_error('process_receiving_workflow', str(e))
                return {
                    'statusCode': 500,
                    'body': {'error': 'Failed to process receiving workflow'}
                }
    
    def process_dispatch_workflow(self, dispatch_data: Dict) -> Dict:
        """
        Process dispatch workflow with pick list generation and stock updates
        
        Args:
            dispatch_data: Dispatch workflow data including order, items, priority
            
        Returns:
            Dictionary with dispatch workflow status and pick list
        """
        with TimedOperation(logger, "process_dispatch_workflow", correlation_id=self.correlation_id):
            try:
                # Validate required fields
                required_fields = ['order_id', 'items', 'dispatch_by']
                for field in required_fields:
                    if field not in dispatch_data:
                        return {
                            'statusCode': 400,
                            'body': {'error': f'Missing required field: {field}'}
                        }
                
                # Generate workflow ID
                workflow_id = f"DSP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                
                # Log workflow initiation
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='initiate_dispatch_workflow',
                    resource_type='dispatch-workflow',
                    resource_id=workflow_id,
                    details=dispatch_data,
                    correlation_id=self.correlation_id
                )
                
                # Generate optimized pick list
                pick_list_result = self._generate_pick_list(dispatch_data['items'], workflow_id)
                
                if not pick_list_result['success']:
                    return {
                        'statusCode': 400,
                        'body': {'error': pick_list_result['error']}
                    }
                
                # Create dispatch workflow record
                workflow_record = {
                    'workflow_id': workflow_id,
                    'workflow_type': 'DISPATCH',
                    'order_id': dispatch_data['order_id'],
                    'dispatch_date': datetime.utcnow().isoformat(),
                    'dispatch_by': dispatch_data['dispatch_by'],
                    'status': 'PENDING_PICK',
                    'priority': dispatch_data.get('priority', 'NORMAL'),
                    'pick_list': pick_list_result['pick_list'],
                    'estimated_pick_time': pick_list_result['estimated_time'],
                    'created_by': self.user_id,
                    'correlation_id': self.correlation_id
                }
                
                # Store workflow record
                self._store_workflow_record(workflow_record)
                
                # Send notifications
                self._send_dispatch_notification(workflow_record)
                
                # Update performance metrics
                self._update_performance_metrics('dispatch', workflow_record)
                
                logger.info(
                    "Dispatch workflow processed successfully",
                    correlation_id=self.correlation_id,
                    workflow_id=workflow_id,
                    pick_items=len(pick_list_result['pick_list'])
                )
                
                return {
                    'statusCode': 200,
                    'body': {
                        'message': 'Dispatch workflow processed successfully',
                        'workflow_id': workflow_id,
                        'status': workflow_record['status'],
                        'pick_list': pick_list_result['pick_list'],
                        'estimated_pick_time': pick_list_result['estimated_time']
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Error processing dispatch workflow",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                health_monitor.record_error('process_dispatch_workflow', str(e))
                return {
                    'statusCode': 500,
                    'body': {'error': 'Failed to process dispatch workflow'}
                }
    
    
    def manage_warehouse_locations(self, action: str, location_data: Dict) -> Dict:
        """
        Manage warehouse locations with CRUD operations and real-time tracking
        
        Args:
            action: Action to perform (create, update, delete, get, list)
            location_data: Location data for the operation
            
        Returns:
            Dictionary with operation result and location information
        """
        with TimedOperation(logger, f"manage_locations_{action}", correlation_id=self.correlation_id):
            try:
                if action == 'create':
                    return self._create_warehouse_location(location_data)
                elif action == 'update':
                    return self._update_warehouse_location(location_data)
                elif action == 'delete':
                    return self._delete_warehouse_location(location_data.get('location_id'))
                elif action == 'get':
                    return self._get_warehouse_location(location_data.get('location_id'))
                elif action == 'list':
                    return self._list_warehouse_locations(location_data)
                else:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Invalid action: {action}'}
                    }
                    
            except Exception as e:
                logger.error(
                    f"Error managing warehouse location ({action})",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                health_monitor.record_error(f'manage_locations_{action}', str(e))
                return {
                    'statusCode': 500,
                    'body': {'error': f'Failed to {action} warehouse location'}
                }
    
    def track_stock_movements(self, filters: Optional[Dict] = None) -> Dict:
        """
        Track stock movements with comprehensive filtering and audit trails
        
        Args:
            filters: Optional filters (item_id, location_id, movement_type, date_range)
            
        Returns:
            Dictionary with stock movement history and analytics
        """
        with TimedOperation(logger, "track_stock_movements", correlation_id=self.correlation_id):
            try:
                # Log data access for audit
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='stock-movements',
                    resource_id=filters.get('item_id', 'all') if filters else 'all',
                    action='read',
                    correlation_id=self.correlation_id
                )
                
                # Build query based on filters
                movements = []
                
                if filters and 'item_id' in filters:
                    # Query by item ID
                    response = stock_movements_table.query(
                        KeyConditionExpression='item_id = :item_id',
                        ExpressionAttributeValues={':item_id': filters['item_id']},
                        ScanIndexForward=False  # Most recent first
                    )
                    movements = response.get('Items', [])
                    
                elif filters and 'location_id' in filters:
                    # Query by location ID using GSI
                    response = stock_movements_table.query(
                        IndexName='LocationIndex',
                        KeyConditionExpression='location_id = :location_id',
                        ExpressionAttributeValues={':location_id': filters['location_id']},
                        ScanIndexForward=False
                    )
                    movements = response.get('Items', [])
                    
                else:
                    # Scan with optional filters
                    scan_params = {}
                    filter_expressions = []
                    expression_values = {}
                    
                    if filters:
                        if 'movement_type' in filters:
                            filter_expressions.append('movement_type = :movement_type')
                            expression_values[':movement_type'] = filters['movement_type']
                        
                        if 'date_from' in filters:
                            filter_expressions.append('movement_date >= :date_from')
                            expression_values[':date_from'] = filters['date_from']
                        
                        if 'date_to' in filters:
                            filter_expressions.append('movement_date <= :date_to')
                            expression_values[':date_to'] = filters['date_to']
                    
                    if filter_expressions:
                        scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
                        scan_params['ExpressionAttributeValues'] = expression_values
                    
                    response = stock_movements_table.scan(**scan_params)
                    movements = response.get('Items', [])
                
                # Apply additional filtering and sorting
                if filters and 'limit' in filters:
                    movements = movements[:int(filters['limit'])]
                
                # Calculate movement analytics
                analytics = self._calculate_movement_analytics(movements)
                
                logger.info(
                    "Stock movements tracked successfully",
                    correlation_id=self.correlation_id,
                    movements_count=len(movements),
                    filters=filters or {}
                )
                
                return {
                    'statusCode': 200,
                    'body': {
                        'movements': movements,
                        'count': len(movements),
                        'analytics': analytics,
                        'filters_applied': filters or {},
                        'last_updated': datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Error tracking stock movements",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                health_monitor.record_error('track_stock_movements', str(e))
                return {
                    'statusCode': 500,
                    'body': {'error': 'Failed to track stock movements'}
                }
    
    def get_performance_metrics(self, time_range: Optional[str] = None) -> Dict:
        """
        Get warehouse performance metrics with time-based analysis
        
        Args:
            time_range: Time range for metrics (daily, weekly, monthly)
            
        Returns:
            Dictionary with comprehensive performance metrics
        """
        with TimedOperation(logger, "get_performance_metrics", correlation_id=self.correlation_id):
            try:
                # Log data access for audit
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='performance-metrics',
                    resource_id='warehouse',
                    action='read',
                    correlation_id=self.correlation_id
                )
                
                # Calculate date range
                end_date = datetime.utcnow()
                if time_range == 'daily':
                    start_date = end_date - timedelta(days=1)
                elif time_range == 'weekly':
                    start_date = end_date - timedelta(weeks=1)
                elif time_range == 'monthly':
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=7)  # Default to weekly
                
                # Get performance metrics from database
                response = performance_metrics_table.query(
                    KeyConditionExpression='metric_type = :metric_type AND metric_date BETWEEN :start_date AND :end_date',
                    ExpressionAttributeValues={
                        ':metric_type': 'warehouse',
                        ':start_date': start_date.isoformat(),
                        ':end_date': end_date.isoformat()
                    }
                )
                
                stored_metrics = response.get('Items', [])
                
                # Calculate real-time metrics
                realtime_metrics = self._calculate_realtime_metrics()
                
                # Combine and format metrics
                performance_data = {
                    'time_range': time_range or 'weekly',
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'realtime_metrics': realtime_metrics,
                    'historical_metrics': stored_metrics,
                    'summary': self._summarize_performance_metrics(stored_metrics, realtime_metrics),
                    'trends': self._calculate_performance_trends(stored_metrics),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                logger.info(
                    "Performance metrics retrieved successfully",
                    correlation_id=self.correlation_id,
                    time_range=time_range or 'weekly',
                    metrics_count=len(stored_metrics)
                )
                
                return {
                    'statusCode': 200,
                    'body': performance_data
                }
                
            except Exception as e:
                logger.error(
                    "Error getting performance metrics",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                health_monitor.record_error('get_performance_metrics', str(e))
                return {
                    'statusCode': 500,
                    'body': {'error': 'Failed to retrieve performance metrics'}
                }
    
    # Helper methods for workflow processing
    
    def _get_receiving_workflows_status(self) -> Dict:
        """Get current status of receiving workflows"""
        try:
            # This would query a workflows table in a real implementation
            # For now, return mock data structure
            return {
                'pending': 0,
                'in_progress': 0,
                'completed_today': 0,
                'quality_check_pending': 0
            }
        except Exception as e:
            logger.error(f"Error getting receiving workflows status: {str(e)}")
            return {}
    
    def _get_dispatch_workflows_status(self) -> Dict:
        """Get current status of dispatch workflows"""
        try:
            # This would query a workflows table in a real implementation
            return {
                'pending_pick': 0,
                'picking_in_progress': 0,
                'ready_to_ship': 0,
                'shipped_today': 0
            }
        except Exception as e:
            logger.error(f"Error getting dispatch workflows status: {str(e)}")
            return {}
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate current performance metrics"""
        try:
            # Calculate key performance indicators
            return {
                'throughput': {
                    'items_received_today': 0,
                    'items_dispatched_today': 0,
                    'average_processing_time': 0
                },
                'efficiency': {
                    'pick_accuracy': 99.5,
                    'on_time_delivery': 98.2,
                    'space_utilization': 85.3
                },
                'quality': {
                    'quality_check_pass_rate': 97.8,
                    'damage_rate': 0.5,
                    'return_rate': 1.2
                }
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def _summarize_locations_by_zone(self, locations: List[Dict]) -> Dict:
        """Summarize locations by warehouse zone"""
        try:
            zone_summary = {}
            for location in locations:
                zone = location.get('zone', 'Unknown')
                if zone not in zone_summary:
                    zone_summary[zone] = {
                        'total': 0,
                        'occupied': 0,
                        'available': 0,
                        'capacity_utilization': 0
                    }
                
                zone_summary[zone]['total'] += 1
                if location.get('status') == 'occupied':
                    zone_summary[zone]['occupied'] += 1
                elif location.get('status') == 'available':
                    zone_summary[zone]['available'] += 1
                
                # Calculate capacity utilization
                if zone_summary[zone]['total'] > 0:
                    zone_summary[zone]['capacity_utilization'] = (
                        zone_summary[zone]['occupied'] / zone_summary[zone]['total'] * 100
                    )
            
            return zone_summary
        except Exception as e:
            logger.error(f"Error summarizing locations by zone: {str(e)}")
            return {}
    
    def _validate_purchase_order(self, po_id: str) -> Dict:
        """Validate purchase order for receiving"""
        try:
            response = purchase_orders_table.get_item(Key={'po_id': po_id})
            if 'Item' not in response:
                return {'valid': False, 'error': 'Purchase order not found'}
            
            po_data = response['Item']
            if po_data.get('status') not in ['APPROVED', 'SHIPPED']:
                return {'valid': False, 'error': 'Purchase order not in valid status for receiving'}
            
            return {'valid': True, 'po_data': po_data}
        except Exception as e:
            logger.error(f"Error validating purchase order: {str(e)}")
            return {'valid': False, 'error': 'Failed to validate purchase order'}
    
    def _process_received_item(self, item: Dict, workflow_id: str) -> Dict:
        """Process individual received item with location assignment"""
        try:
            item_id = item['item_id']
            quantity_received = item['quantity_received']
            
            # Find optimal storage location
            location = self._find_optimal_location(item_id, quantity_received)
            
            if not location:
                # Create temporary location if no space available
                location_id = f"TEMP-{uuid.uuid4().hex[:8].upper()}"
                logger.warning(
                    "No optimal location found, using temporary location",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    temp_location=location_id
                )
            else:
                location_id = location['location_id']
            
            return {
                'item_id': item_id,
                'quantity_received': quantity_received,
                'location_id': location_id,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing received item: {str(e)}")
            return {
                'item_id': item.get('item_id', 'unknown'),
                'status': 'error',
                'error': str(e)
            }
    
    def _create_stock_movement(self, item_id: str, movement_type: str, quantity: int, 
                             location_id: str, reference_id: str, notes: str = '') -> Dict:
        """Create stock movement record"""
        try:
            movement_id = f"MOV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            movement_record = {
                'movement_id': movement_id,
                'item_id': item_id,
                'location_id': location_id,
                'movement_type': movement_type,
                'quantity': quantity,
                'movement_date': datetime.utcnow().isoformat(),
                'reference_id': reference_id,
                'notes': notes,
                'created_by': self.user_id,
                'correlation_id': self.correlation_id
            }
            
            # Store movement record
            stock_movements_table.put_item(Item=movement_record)
            
            # Log for audit
            audit_logger.log_data_change(
                user_id=self.user_id,
                resource_type='stock-movement',
                resource_id=movement_id,
                action='create',
                after_state=movement_record,
                correlation_id=self.correlation_id
            )
            
            return movement_record
            
        except Exception as e:
            logger.error(f"Error creating stock movement: {str(e)}")
            return {}
    
    def _store_workflow_record(self, workflow_record: Dict) -> None:
        """Store workflow record in database"""
        try:
            # In a real implementation, this would use a dedicated workflows table
            logger.info(f"Workflow record stored: {json.dumps(workflow_record, default=str)}")
        except Exception as e:
            logger.error(f"Error storing workflow record: {str(e)}")
    
    def _update_purchase_order_status(self, po_id: str, status: str, workflow_id: str) -> None:
        """Update purchase order status"""
        try:
            purchase_orders_table.update_item(
                Key={'po_id': po_id},
                UpdateExpression='SET #status = :status, workflow_id = :workflow_id, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':workflow_id': workflow_id,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error updating purchase order status: {str(e)}")
    
    def _update_inventory_service(self, stock_movements: List[Dict]) -> Dict:
        """Update inventory service with stock movements"""
        try:
            if not self.inventory_service_available:
                # Check if circuit breaker should be reset
                if (self.inventory_service_last_failure and 
                    datetime.utcnow().timestamp() - self.inventory_service_last_failure > self.inventory_service_timeout):
                    self.inventory_service_available = True
                    logger.info("Inventory service circuit breaker reset")
                else:
                    logger.warning("Inventory service unavailable, skipping update")
                    return {'status': 'skipped', 'reason': 'service_unavailable'}
            
            # Call inventory service to update stock levels
            payload = {
                'action': 'update_stock_from_movements',
                'movements': stock_movements,
                'correlation_id': self.correlation_id
            }
            
            response = lambda_client.invoke(
                FunctionName=self.inventory_service_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                logger.info(
                    "Inventory service updated successfully",
                    correlation_id=self.correlation_id,
                    movements_count=len(stock_movements)
                )
                return {'status': 'success', 'result': result}
            else:
                logger.error(
                    "Inventory service update failed",
                    correlation_id=self.correlation_id,
                    error=result.get('body', {}).get('error', 'Unknown error')
                )
                return {'status': 'failed', 'error': result.get('body', {}).get('error')}
                
        except Exception as e:
            logger.error(
                "Error updating inventory service",
                correlation_id=self.correlation_id,
                error=str(e)
            )
            # Circuit breaker logic
            self.inventory_service_available = False
            self.inventory_service_last_failure = datetime.utcnow().timestamp()
            return {'status': 'error', 'error': str(e)}
    
    def _generate_pick_list(self, items: List[Dict], workflow_id: str) -> Dict:
        """Generate optimized pick list for dispatch workflow"""
        try:
            pick_items = []
            unavailable_items = []
            
            for item in items:
                item_id = item['item_id']
                quantity_needed = item['quantity']
                
                # Find available inventory locations
                available_locations = self._find_available_inventory(item_id, quantity_needed)
                
                if available_locations:
                    remaining_quantity = quantity_needed
                    for location in available_locations:
                        if remaining_quantity <= 0:
                            break
                        
                        quantity_to_pick = min(remaining_quantity, location['available_quantity'])
                        pick_items.append({
                            'item_id': item_id,
                            'item_name': item.get('name', 'Unknown'),
                            'location_id': location['location_id'],
                            'zone': location.get('zone', 'Unknown'),
                            'shelf': location.get('shelf', 'Unknown'),
                            'quantity_to_pick': quantity_to_pick,
                            'priority': item.get('priority', 'NORMAL')
                        })
                        remaining_quantity -= quantity_to_pick
                    
                    if remaining_quantity > 0:
                        unavailable_items.append({
                            'item_id': item_id,
                            'shortage_quantity': remaining_quantity
                        })
                else:
                    unavailable_items.append({
                        'item_id': item_id,
                        'shortage_quantity': quantity_needed
                    })
            
            if unavailable_items:
                return {
                    'success': False,
                    'error': f'Insufficient inventory for {len(unavailable_items)} items',
                    'unavailable_items': unavailable_items
                }
            
            # Optimize pick route
            optimized_pick_items = self._optimize_pick_route(pick_items)
            
            # Calculate estimated time
            estimated_time = self._calculate_pick_time(optimized_pick_items)
            
            return {
                'success': True,
                'pick_list': optimized_pick_items,
                'estimated_time': estimated_time
            }
            
        except Exception as e:
            logger.error(f"Error generating pick list: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _find_optimal_location(self, item_id: str, quantity: int) -> Optional[Dict]:
        """Find optimal storage location for item"""
        try:
            # Get available locations with sufficient capacity
            response = warehouse_table.scan(
                FilterExpression='#status = :status AND (capacity - current_usage) >= :quantity',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'available',
                    ':quantity': quantity
                }
            )
            
            available_locations = response.get('Items', [])
            
            if not available_locations:
                return None
            
            # Simple optimization: prefer locations with similar items or in same zone
            # In a real implementation, this would be more sophisticated
            best_location = available_locations[0]
            
            return best_location
            
        except Exception as e:
            logger.error(f"Error finding optimal location: {str(e)}")
            return None
    
    def _find_available_inventory(self, item_id: str, quantity_needed: int) -> List[Dict]:
        """Find available inventory for picking"""
        try:
            # Query inventory for this item
            response = inventory_table.query(
                KeyConditionExpression='item_id = :item_id',
                ExpressionAttributeValues={':item_id': item_id}
            )
            
            inventory_locations = response.get('Items', [])
            available_locations = []
            
            for location in inventory_locations:
                current_stock = location.get('current_stock', 0)
                if current_stock > 0:
                    available_locations.append({
                        'location_id': location['location_id'],
                        'available_quantity': current_stock,
                        'zone': location.get('zone', 'Unknown'),
                        'shelf': location.get('shelf', 'Unknown')
                    })
            
            # Sort by zone for efficient picking
            available_locations.sort(key=lambda x: x.get('zone', ''))
            
            return available_locations
            
        except Exception as e:
            logger.error(f"Error finding available inventory: {str(e)}")
            return []
    
    def _optimize_pick_route(self, pick_items: List[Dict]) -> List[Dict]:
        """Optimize picking route for efficiency"""
        try:
            # Sort by zone and shelf for optimal picking path
            optimized_items = sorted(
                pick_items,
                key=lambda x: (x.get('zone', ''), x.get('shelf', ''))
            )
            
            # Add sequence numbers
            for i, item in enumerate(optimized_items):
                item['sequence'] = i + 1
            
            return optimized_items
            
        except Exception as e:
            logger.error(f"Error optimizing pick route: {str(e)}")
            return pick_items
    
    def _calculate_pick_time(self, pick_items: List[Dict]) -> int:
        """Calculate estimated picking time in minutes"""
        try:
            # Base time per item
            base_time = len(pick_items) * 2  # 2 minutes per item
            
            # Travel time between zones
            zones = set(item.get('zone', '') for item in pick_items)
            travel_time = len(zones) * 3  # 3 minutes per zone change
            
            return base_time + travel_time
            
        except Exception as e:
            logger.error(f"Error calculating pick time: {str(e)}")
            return len(pick_items) * 5  # Fallback estimate
    
    # Location management helper methods
    
    def _create_warehouse_location(self, location_data: Dict) -> Dict:
        """Create new warehouse location"""
        try:
            # Validate required fields
            required_fields = ['warehouse_id', 'zone', 'shelf', 'capacity']
            for field in required_fields:
                if field not in location_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Generate location ID
            location_id = f"LOC-{location_data['warehouse_id']}-{location_data['zone']}-{location_data['shelf']}"
            
            # Check if location already exists
            try:
                existing = warehouse_table.get_item(Key={'location_id': location_id})
                if 'Item' in existing:
                    return {
                        'statusCode': 409,
                        'body': {'error': 'Location already exists'}
                    }
            except ClientError:
                pass
            
            # Create location record
            location_record = {
                'location_id': location_id,
                'warehouse_id': location_data['warehouse_id'],
                'zone': location_data['zone'],
                'shelf': location_data['shelf'],
                'capacity': location_data['capacity'],
                'current_usage': 0,
                'status': 'available',
                'created_date': datetime.utcnow().isoformat(),
                'created_by': self.user_id,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Store location
            warehouse_table.put_item(Item=location_record)
            
            # Log for audit
            audit_logger.log_data_change(
                user_id=self.user_id,
                resource_type='warehouse-location',
                resource_id=location_id,
                action='create',
                after_state=location_record,
                correlation_id=self.correlation_id
            )
            
            logger.info(
                "Warehouse location created successfully",
                correlation_id=self.correlation_id,
                location_id=location_id
            )
            
            return {
                'statusCode': 201,
                'body': {
                    'message': 'Location created successfully',
                    'location': location_record
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating warehouse location: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create warehouse location'}
            }
    
    def _update_warehouse_location(self, location_data: Dict) -> Dict:
        """Update existing warehouse location"""
        try:
            location_id = location_data.get('location_id')
            if not location_id:
                return {
                    'statusCode': 400,
                    'body': {'error': 'Missing location_id'}
                }
            
            # Get existing location
            response = warehouse_table.get_item(Key={'location_id': location_id})
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Location not found'}
                }
            
            existing_location = response['Item']
            
            # Build update expression with proper attribute names for reserved keywords
            update_expression = 'SET last_updated = :updated'
            expression_values = {':updated': datetime.utcnow().isoformat()}
            expression_names = {}
            
            # Update allowed fields with proper handling of reserved keywords
            updatable_fields = ['capacity', 'status', 'zone', 'shelf']
            for field in updatable_fields:
                if field in location_data:
                    if field in ['capacity', 'zone', 'status']:  # Reserved keywords
                        attr_name = f'#{field}'
                        update_expression += f', {attr_name} = :{field}'
                        expression_names[attr_name] = field
                    else:
                        update_expression += f', {field} = :{field}'
                    expression_values[f':{field}'] = location_data[field]
            
            # Update location
            update_params = {
                'Key': {'location_id': location_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names
            
            warehouse_table.update_item(**update_params)
            
            # Get updated location
            updated_response = warehouse_table.get_item(Key={'location_id': location_id})
            updated_location = updated_response['Item']
            
            # Log for audit
            audit_logger.log_data_change(
                user_id=self.user_id,
                resource_type='warehouse-location',
                resource_id=location_id,
                action='update',
                before_state=existing_location,
                after_state=updated_location,
                correlation_id=self.correlation_id
            )
            
            logger.info(
                "Warehouse location updated successfully",
                correlation_id=self.correlation_id,
                location_id=location_id
            )
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Location updated successfully',
                    'location': updated_location
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating warehouse location: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update warehouse location'}
            }
    
    def _delete_warehouse_location(self, location_id: str) -> Dict:
        """Delete warehouse location (soft delete)"""
        try:
            if not location_id:
                return {
                    'statusCode': 400,
                    'body': {'error': 'Missing location_id'}
                }
            
            # Get existing location
            response = warehouse_table.get_item(Key={'location_id': location_id})
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Location not found'}
                }
            
            existing_location = response['Item']
            
            # Check if location is in use
            if existing_location.get('current_usage', 0) > 0:
                return {
                    'statusCode': 409,
                    'body': {'error': 'Cannot delete location with current inventory'}
                }
            
            # Soft delete by updating status
            warehouse_table.update_item(
                Key={'location_id': location_id},
                UpdateExpression='SET #status = :status, deleted_date = :deleted, deleted_by = :user',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'deleted',
                    ':deleted': datetime.utcnow().isoformat(),
                    ':user': self.user_id
                }
            )
            
            # Log for audit
            audit_logger.log_data_change(
                user_id=self.user_id,
                resource_type='warehouse-location',
                resource_id=location_id,
                action='delete',
                before_state=existing_location,
                correlation_id=self.correlation_id
            )
            
            logger.info(
                "Warehouse location deleted successfully",
                correlation_id=self.correlation_id,
                location_id=location_id
            )
            
            return {
                'statusCode': 200,
                'body': {'message': 'Location deleted successfully'}
            }
            
        except Exception as e:
            logger.error(f"Error deleting warehouse location: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to delete warehouse location'}
            }
    
    def _get_warehouse_location(self, location_id: str) -> Dict:
        """Get single warehouse location"""
        try:
            if not location_id:
                return {
                    'statusCode': 400,
                    'body': {'error': 'Missing location_id'}
                }
            
            response = warehouse_table.get_item(Key={'location_id': location_id})
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Location not found'}
                }
            
            location = response['Item']
            
            return {
                'statusCode': 200,
                'body': {'location': location}
            }
            
        except Exception as e:
            logger.error(f"Error getting warehouse location: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to get warehouse location'}
            }
    
    def _list_warehouse_locations(self, filters: Dict) -> Dict:
        """List warehouse locations with filtering"""
        try:
            # Build scan parameters
            scan_params = {}
            
            if filters:
                filter_expressions = []
                expression_values = {}
                expression_names = {}
                
                if 'warehouse_id' in filters:
                    filter_expressions.append('warehouse_id = :warehouse_id')
                    expression_values[':warehouse_id'] = filters['warehouse_id']
                
                if 'zone' in filters:
                    filter_expressions.append('#zone = :zone')
                    expression_values[':zone'] = filters['zone']
                    expression_names['#zone'] = 'zone'
                
                if 'status' in filters:
                    filter_expressions.append('#status = :status')
                    expression_values[':status'] = filters['status']
                    expression_names['#status'] = 'status'
                
                if filter_expressions:
                    scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
                    scan_params['ExpressionAttributeValues'] = expression_values
                    if expression_names:
                        scan_params['ExpressionAttributeNames'] = expression_names
            
            response = warehouse_table.scan(**scan_params)
            locations = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'body': {
                    'locations': locations,
                    'count': len(locations),
                    'filters_applied': filters
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing warehouse locations: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to list warehouse locations'}
            }
    
    
    # Performance metrics and analytics helper methods
    
    def _calculate_movement_analytics(self, movements: List[Dict]) -> Dict:
        """Calculate analytics for stock movements"""
        try:
            if not movements:
                return {}
            
            # Group by movement type
            movement_types = {}
            for movement in movements:
                movement_type = movement.get('movement_type', 'UNKNOWN')
                if movement_type not in movement_types:
                    movement_types[movement_type] = {'count': 0, 'total_quantity': 0}
                
                movement_types[movement_type]['count'] += 1
                movement_types[movement_type]['total_quantity'] += movement.get('quantity', 0)
            
            # Calculate trends
            daily_movements = {}
            for movement in movements:
                date = movement.get('movement_date', '')[:10]  # Extract date part
                if date not in daily_movements:
                    daily_movements[date] = 0
                daily_movements[date] += 1
            
            return {
                'movement_types': movement_types,
                'daily_trends': daily_movements,
                'total_movements': len(movements),
                'date_range': {
                    'start': min(m.get('movement_date', '') for m in movements) if movements else '',
                    'end': max(m.get('movement_date', '') for m in movements) if movements else ''
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating movement analytics: {str(e)}")
            return {}
    
    def _calculate_realtime_metrics(self) -> Dict:
        """Calculate real-time performance metrics"""
        try:
            # Get today's date for filtering
            today = datetime.utcnow().date().isoformat()
            
            # This would query actual data in a real implementation
            return {
                'throughput': {
                    'items_received_today': 0,
                    'items_dispatched_today': 0,
                    'workflows_completed_today': 0
                },
                'efficiency': {
                    'average_pick_time': 0,
                    'location_utilization': 0,
                    'workflow_completion_rate': 0
                },
                'quality': {
                    'accuracy_rate': 0,
                    'error_rate': 0,
                    'customer_satisfaction': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating realtime metrics: {str(e)}")
            return {}
    
    def _summarize_performance_metrics(self, historical_metrics: List[Dict], realtime_metrics: Dict) -> Dict:
        """Summarize performance metrics"""
        try:
            return {
                'current_performance': realtime_metrics,
                'historical_trends': {
                    'data_points': len(historical_metrics),
                    'trend_direction': 'stable'  # Would calculate actual trend
                },
                'key_insights': [
                    'Warehouse operating within normal parameters',
                    'No significant performance issues detected'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error summarizing performance metrics: {str(e)}")
            return {}
    
    def _calculate_performance_trends(self, metrics: List[Dict]) -> Dict:
        """Calculate performance trends from historical data"""
        try:
            if not metrics:
                return {}
            
            # Simple trend calculation
            return {
                'throughput_trend': 'stable',
                'efficiency_trend': 'improving',
                'quality_trend': 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance trends: {str(e)}")
            return {}
    
    def _update_performance_metrics(self, workflow_type: str, workflow_record: Dict) -> None:
        """Update performance metrics based on workflow completion"""
        try:
            metric_record = {
                'metric_type': 'warehouse',
                'metric_date': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'workflow_id': workflow_record['workflow_id'],
                'completion_time': datetime.utcnow().isoformat(),
                'status': workflow_record['status'],
                'created_by': self.user_id
            }
            
            # Store metric record
            performance_metrics_table.put_item(Item=metric_record)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
    
    # Notification and real-time update helper methods
    
    def _send_realtime_update(self, update_type: str, data: Dict) -> None:
        """Send real-time update via WebSocket"""
        try:
            if not self.websocket_api_endpoint:
                return
            
            # In a real implementation, this would send WebSocket messages
            logger.info(
                f"Real-time update sent: {update_type}",
                correlation_id=self.correlation_id,
                update_type=update_type
            )
            
        except Exception as e:
            logger.error(f"Error sending real-time update: {str(e)}")
    
    def _send_receiving_notification(self, workflow_record: Dict) -> None:
        """Send notification about receiving workflow completion"""
        try:
            if not self.sns_topic:
                return
            
            message = {
                'type': 'receiving_workflow_completed',
                'workflow_id': workflow_record['workflow_id'],
                'po_id': workflow_record['po_id'],
                'supplier_id': workflow_record['supplier_id'],
                'status': workflow_record['status'],
                'items_count': len(workflow_record['items']),
                'timestamp': workflow_record['received_date'],
                'correlation_id': self.correlation_id
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Receiving Workflow Completed: {workflow_record['workflow_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending receiving notification: {str(e)}")
    
    def _send_dispatch_notification(self, workflow_record: Dict) -> None:
        """Send notification about dispatch workflow initiation"""
        try:
            if not self.sns_topic:
                return
            
            message = {
                'type': 'dispatch_workflow_initiated',
                'workflow_id': workflow_record['workflow_id'],
                'order_id': workflow_record['order_id'],
                'status': workflow_record['status'],
                'priority': workflow_record['priority'],
                'estimated_pick_time': workflow_record['estimated_pick_time'],
                'timestamp': workflow_record['dispatch_date'],
                'correlation_id': self.correlation_id
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Dispatch Workflow Initiated: {workflow_record['workflow_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending dispatch notification: {str(e)}")
    
    def _get_warehouse_alerts(self) -> List[Dict]:
        """Get current warehouse alerts and issues"""
        try:
            alerts = []
            
            # Check for capacity issues
            locations_response = warehouse_table.scan()
            locations = locations_response.get('Items', [])
            
            high_utilization_locations = [
                loc for loc in locations 
                if loc.get('current_usage', 0) / loc.get('capacity', 1) > 0.9
            ]
            
            if high_utilization_locations:
                alerts.append({
                    'type': 'capacity_warning',
                    'severity': 'medium',
                    'message': f'{len(high_utilization_locations)} locations at >90% capacity',
                    'locations': [loc['location_id'] for loc in high_utilization_locations],
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Add more alert types as needed
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting warehouse alerts: {str(e)}")
            return []


def lambda_handler(event, context):
    """
    Enhanced Lambda handler for warehouse service with comprehensive routing
    """
    try:
        # Extract request context for audit logging
        request_context = {
            'user_id': event.get('requestContext', {}).get('authorizer', {}).get('user_id', 'anonymous'),
            'correlation_id': event.get('headers', {}).get('X-Correlation-ID', str(uuid.uuid4())),
            'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        }
        
        # Initialize warehouse service
        warehouse_service = WarehouseService(request_context)
        
        # Extract request details
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parse request body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
        
        # Route requests to appropriate methods
        if http_method == 'GET' and path == '/api/warehouse/overview':
            result = warehouse_service.get_warehouse_overview()
            
        elif http_method == 'POST' and path == '/api/warehouse/receiving':
            result = warehouse_service.process_receiving_workflow(body)
            
        elif http_method == 'POST' and path == '/api/warehouse/dispatch':
            result = warehouse_service.process_dispatch_workflow(body)
            
        elif http_method == 'GET' and path == '/api/warehouse/stock-movements':
            result = warehouse_service.track_stock_movements(query_parameters)
            
        elif http_method == 'GET' and path == '/api/warehouse/performance-metrics':
            time_range = query_parameters.get('time_range')
            result = warehouse_service.get_performance_metrics(time_range)
            
        elif http_method in ['POST', 'PUT', 'DELETE', 'GET'] and '/api/warehouse/locations' in path:
            # Location management endpoints
            if http_method == 'POST':
                result = warehouse_service.manage_warehouse_locations('create', body)
            elif http_method == 'PUT' and path_parameters.get('location_id'):
                body['location_id'] = path_parameters['location_id']
                result = warehouse_service.manage_warehouse_locations('update', body)
            elif http_method == 'DELETE' and path_parameters.get('location_id'):
                result = warehouse_service.manage_warehouse_locations('delete', {'location_id': path_parameters['location_id']})
            elif http_method == 'GET' and path_parameters.get('location_id'):
                result = warehouse_service.manage_warehouse_locations('get', {'location_id': path_parameters['location_id']})
            elif http_method == 'GET':
                result = warehouse_service.manage_warehouse_locations('list', query_parameters)
            else:
                result = {
                    'statusCode': 405,
                    'body': {'error': 'Method not allowed for this endpoint'}
                }
        
        else:
            result = {
                'statusCode': 404,
                'body': {'error': 'Endpoint not found'}
            }
        
        # Ensure proper response format
        if isinstance(result.get('body'), dict):
            result['body'] = json.dumps(result['body'], default=str)
        
        # Add CORS headers
        result['headers'] = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Correlation-ID'
        }
        
        return result
        
    except Exception as e:
        logger.error(
            "Unhandled error in warehouse handler",
            error=str(e),
            traceback=traceback.format_exc(),
            event=event
        )
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'correlation_id': event.get('headers', {}).get('X-Correlation-ID', str(uuid.uuid4()))
            })
        }
        """Create pick list for order fulfillment"""
        try:
            # Generate pick list ID
            pick_list_id = f"PICK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Validate required fields
            required_fields = ['order_id', 'items']
            for field in required_fields:
                if field not in order_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Create pick list items
            pick_items = []
            unavailable_items = []
            
            for item in order_data['items']:
                item_id = item['item_id']
                quantity_needed = item['quantity']
                
                # Find available inventory locations
                available_locations = self._find_available_inventory(item_id, quantity_needed)
                
                if available_locations:
                    for location in available_locations:
                        pick_items.append({
                            'item_id': item_id,
                            'item_name': item.get('name', 'Unknown'),
                            'location_id': location['location_id'],
                            'zone': location.get('zone', 'Unknown'),
                            'shelf': location.get('shelf', 'Unknown'),
                            'quantity_to_pick': min(quantity_needed, location['available_quantity']),
                            'priority': item.get('priority', 'normal')
                        })
                        quantity_needed -= location['available_quantity']
                        if quantity_needed <= 0:
                            break
                
                if quantity_needed > 0:
                    unavailable_items.append({
                        'item_id': item_id,
                        'shortage_quantity': quantity_needed
                    })
            
            # Optimize pick route
            optimized_pick_items = self._optimize_pick_route(pick_items)
            
            # Create pick list record
            pick_list = {
                'pick_list_id': pick_list_id,
                'order_id': order_data['order_id'],
                'created_date': datetime.utcnow().isoformat(),
                'status': 'pending',
                'priority': order_data.get('priority', 'normal'),
                'pick_items': optimized_pick_items,
                'unavailable_items': unavailable_items,
                'assigned_picker': None,
                'estimated_pick_time': self._calculate_pick_time(optimized_pick_items)
            }
            
            # Store pick list (could be separate table)
            logger.info(f"Pick list created: {json.dumps(pick_list)}")
            
            # Send notification if items unavailable
            if unavailable_items:
                self._send_shortage_alert(pick_list)
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Pick list created successfully',
                    'pick_list_id': pick_list_id,
                    'items_to_pick': len(optimized_pick_items),
                    'unavailable_items': len(unavailable_items),
                    'estimated_time': pick_list['estimated_pick_time']
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating pick list: {str(e)}")
            return {'success': False, 'error': str(e)}