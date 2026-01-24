"""
AquaChain Warehouse Management - Handler
Manages warehouse operations, receiving, fulfillment, and quality control
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import uuid
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
s3 = boto3.client('s3')

# Table references
warehouse_table = dynamodb.Table('AquaChain-Warehouse-Locations')
inventory_table = dynamodb.Table('AquaChain-Inventory-Items')
purchase_orders_table = dynamodb.Table('AquaChain-Purchase-Orders')
shipments_table = dynamodb.Table('AquaChain-Shipments')

class WarehouseManager:
    """Core warehouse management operations"""
    
    def __init__(self):
        self.sns_topic = os.environ.get('WAREHOUSE_ALERTS_TOPIC')
        self.s3_bucket = os.environ.get('WAREHOUSE_DOCUMENTS_BUCKET')
        
    def get_warehouse_overview(self) -> Dict:
        """Get warehouse operations overview"""
        try:
            # Get warehouse locations
            locations_response = warehouse_table.scan()
            locations = locations_response.get('Items', [])
            
            # Get pending shipments (inbound)
            inbound_response = purchase_orders_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='status = :status',
                ExpressionAttributeValues={':status': 'shipped'}
            )
            inbound_shipments = inbound_response.get('Items', [])
            
            # Get pending fulfillment orders (outbound)
            outbound_response = shipments_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='status = :status',
                ExpressionAttributeValues={':status': 'pending_fulfillment'}
            )
            outbound_orders = outbound_response.get('Items', [])
            
            # Calculate metrics
            total_locations = len(locations)
            occupied_locations = len([l for l in locations if l.get('status') == 'occupied'])
            occupancy_rate = (occupied_locations / total_locations * 100) if total_locations > 0 else 0
            
            return {
                'statusCode': 200,
                'body': {
                    'overview': {
                        'total_locations': total_locations,
                        'occupied_locations': occupied_locations,
                        'available_locations': total_locations - occupied_locations,
                        'occupancy_rate': round(occupancy_rate, 2),
                        'inbound_shipments': len(inbound_shipments),
                        'outbound_orders': len(outbound_orders)
                    },
                    'inbound_queue': inbound_shipments[:10],  # Latest 10
                    'outbound_queue': outbound_orders[:10],   # Latest 10
                    'alerts': self._get_warehouse_alerts()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting warehouse overview: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve warehouse overview'}
            }
    
    def process_inbound_shipment(self, shipment_data: Dict) -> Dict:
        """Process incoming shipment from supplier"""
        try:
            # Generate receiving ID
            receiving_id = f"RCV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Validate required fields
            required_fields = ['po_id', 'supplier_id', 'items']
            for field in required_fields:
                if field not in shipment_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Get PO details
            po_response = purchase_orders_table.get_item(Key={'po_id': shipment_data['po_id']})
            if 'Item' not in po_response:
                return {
                    'statusCode': 400,
                    'body': {'error': 'Invalid purchase order ID'}
                }
            
            po_data = po_response['Item']
            
            # Create receiving record
            receiving_record = {
                'receiving_id': receiving_id,
                'po_id': shipment_data['po_id'],
                'supplier_id': shipment_data['supplier_id'],
                'received_date': datetime.utcnow().isoformat(),
                'received_by': shipment_data.get('received_by', 'system'),
                'status': 'received',
                'items': shipment_data['items'],
                'quality_check_required': shipment_data.get('quality_check_required', True),
                'notes': shipment_data.get('notes', '')
            }
            
            # Process each item
            processed_items = []
            for item in shipment_data['items']:
                processed_item = self._process_received_item(item, receiving_id)
                processed_items.append(processed_item)
            
            receiving_record['processed_items'] = processed_items
            
            # Update PO status
            purchase_orders_table.update_item(
                Key={'po_id': shipment_data['po_id']},
                UpdateExpression='SET status = :status, actual_delivery_date = :date, receiving_id = :rid',
                ExpressionAttributeValues={
                    ':status': 'delivered',
                    ':date': datetime.utcnow().isoformat(),
                    ':rid': receiving_id
                }
            )
            
            # Store receiving record (could be separate table)
            logger.info(f"Receiving record: {json.dumps(receiving_record)}")
            
            # Send notifications
            self._send_receiving_notification(receiving_record)
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Inbound shipment processed successfully',
                    'receiving_id': receiving_id,
                    'processed_items': processed_items,
                    'quality_check_required': receiving_record['quality_check_required']
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing inbound shipment: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to process inbound shipment'}
            }
    
    def perform_quality_check(self, receiving_id: str, quality_data: Dict) -> Dict:
        """Perform quality check on received items"""
        try:
            # Validate quality data
            required_fields = ['items_checked', 'inspector', 'overall_status']
            for field in required_fields:
                if field not in quality_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Create quality check record
            qc_record = {
                'qc_id': f"QC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                'receiving_id': receiving_id,
                'inspection_date': datetime.utcnow().isoformat(),
                'inspector': quality_data['inspector'],
                'overall_status': quality_data['overall_status'],
                'items_checked': quality_data['items_checked'],
                'defects_found': quality_data.get('defects_found', []),
                'notes': quality_data.get('notes', ''),
                'photos': quality_data.get('photos', [])
            }
            
            # Process quality results for each item
            approved_items = []
            rejected_items = []
            
            for item_check in quality_data['items_checked']:
                item_id = item_check['item_id']
                location_id = item_check['location_id']
                status = item_check['status']
                quantity_approved = item_check.get('quantity_approved', 0)
                quantity_rejected = item_check.get('quantity_rejected', 0)
                
                if status == 'approved' and quantity_approved > 0:
                    # Update inventory for approved items
                    self._update_inventory_after_qc(
                        item_id, location_id, quantity_approved, 'approved'
                    )
                    approved_items.append(item_check)
                
                elif status == 'rejected' and quantity_rejected > 0:
                    # Handle rejected items
                    self._handle_rejected_items(
                        item_id, location_id, quantity_rejected, item_check.get('rejection_reason')
                    )
                    rejected_items.append(item_check)
            
            qc_record['approved_items'] = approved_items
            qc_record['rejected_items'] = rejected_items
            
            # Store QC record
            logger.info(f"Quality check record: {json.dumps(qc_record)}")
            
            # Send notifications if there are issues
            if rejected_items or quality_data['overall_status'] != 'passed':
                self._send_quality_alert(qc_record)
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Quality check completed successfully',
                    'qc_id': qc_record['qc_id'],
                    'overall_status': quality_data['overall_status'],
                    'approved_items': len(approved_items),
                    'rejected_items': len(rejected_items)
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing quality check: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to perform quality check'}
            }
    
    def create_pick_list(self, order_data: Dict) -> Dict:
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
            logger.error(f"Error creating pick list: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create pick list'}
            }
    
    def assign_picker(self, pick_list_id: str, picker_id: str) -> Dict:
        """Assign picker to pick list"""
        try:
            # Update pick list with assigned picker
            # In real implementation, would update pick list table
            
            assignment_record = {
                'pick_list_id': pick_list_id,
                'picker_id': picker_id,
                'assigned_at': datetime.utcnow().isoformat(),
                'status': 'assigned'
            }
            
            logger.info(f"Picker assigned: {json.dumps(assignment_record)}")
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Picker assigned successfully',
                    'pick_list_id': pick_list_id,
                    'picker_id': picker_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error assigning picker: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to assign picker'}
            }
    
    def complete_picking(self, pick_list_id: str, picking_data: Dict) -> Dict:
        """Complete picking process and update inventory"""
        try:
            # Validate picking data
            required_fields = ['picker_id', 'items_picked']
            for field in required_fields:
                if field not in picking_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Process picked items
            picked_items = []
            for item in picking_data['items_picked']:
                item_id = item['item_id']
                location_id = item['location_id']
                quantity_picked = item['quantity_picked']
                
                # Update inventory
                inventory_table.update_item(
                    Key={'item_id': item_id, 'location_id': location_id},
                    UpdateExpression='ADD current_stock :qty SET last_picked = :date',
                    ExpressionAttributeValues={
                        ':qty': -quantity_picked,  # Subtract from inventory
                        ':date': datetime.utcnow().isoformat()
                    }
                )
                
                picked_items.append(item)
            
            # Create picking completion record
            completion_record = {
                'pick_list_id': pick_list_id,
                'picker_id': picking_data['picker_id'],
                'completed_at': datetime.utcnow().isoformat(),
                'items_picked': picked_items,
                'total_items': len(picked_items),
                'notes': picking_data.get('notes', '')
            }
            
            logger.info(f"Picking completed: {json.dumps(completion_record)}")
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Picking completed successfully',
                    'pick_list_id': pick_list_id,
                    'items_picked': len(picked_items)
                }
            }
            
        except Exception as e:
            logger.error(f"Error completing picking: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to complete picking'}
            }
    
    def get_warehouse_locations(self, filters: Optional[Dict] = None) -> Dict:
        """Get warehouse locations with optional filtering"""
        try:
            if filters:
                if 'warehouse_id' in filters:
                    response = warehouse_table.query(
                        IndexName='WarehouseIndex',
                        KeyConditionExpression='warehouse_id = :wid',
                        ExpressionAttributeValues={':wid': filters['warehouse_id']}
                    )
                elif 'status' in filters:
                    response = warehouse_table.query(
                        IndexName='StatusIndex',
                        KeyConditionExpression='status = :status',
                        ExpressionAttributeValues={':status': filters['status']}
                    )
                else:
                    response = warehouse_table.scan()
            else:
                response = warehouse_table.scan()
                
            locations = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'body': {
                    'locations': locations,
                    'count': len(locations),
                    'available_count': len([l for l in locations if l.get('status') == 'available']),
                    'occupied_count': len([l for l in locations if l.get('status') == 'occupied'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting warehouse locations: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve warehouse locations'}
            }
    
    def _process_received_item(self, item: Dict, receiving_id: str) -> Dict:
        """Process individual received item"""
        try:
            item_id = item['item_id']
            quantity_received = item['quantity_received']
            
            # Find optimal storage location
            location = self._find_optimal_location(item_id, quantity_received)
            
            if not location:
                # Create temporary location if no space available
                location = {
                    'location_id': f"TEMP-{uuid.uuid4().hex[:8].upper()}",
                    'zone': 'TEMP',
                    'status': 'temporary'
                }
            
            # Update inventory (pending quality check)
            inventory_table.update_item(
                Key={'item_id': item_id, 'location_id': location['location_id']},
                UpdateExpression='ADD pending_stock :qty SET last_received = :date, receiving_id = :rid',
                ExpressionAttributeValues={
                    ':qty': quantity_received,
                    ':date': datetime.utcnow().isoformat(),
                    ':rid': receiving_id
                },
                ReturnValues='ALL_NEW'
            )
            
            return {
                'item_id': item_id,
                'quantity_received': quantity_received,
                'location_assigned': location['location_id'],
                'status': 'pending_qc'
            }
            
        except Exception as e:
            logger.error(f"Error processing received item: {str(e)}")
            return {
                'item_id': item.get('item_id', 'unknown'),
                'status': 'error',
                'error': str(e)
            }
    
    def _find_optimal_location(self, item_id: str, quantity: int) -> Optional[Dict]:
        """Find optimal storage location for item"""
        try:
            # Get available locations
            response = warehouse_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='status = :status',
                ExpressionAttributeValues={':status': 'available'}
            )
            
            available_locations = response.get('Items', [])
            
            # Simple logic: find location with enough capacity
            for location in available_locations:
                capacity = location.get('capacity', 0)
                current_usage = location.get('current_usage', 0)
                
                if (capacity - current_usage) >= quantity:
                    return location
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding optimal location: {str(e)}")
            return None
    
    def _update_inventory_after_qc(self, item_id: str, location_id: str, quantity: int, status: str):
        """Update inventory after quality check"""
        try:
            if status == 'approved':
                # Move from pending to current stock
                inventory_table.update_item(
                    Key={'item_id': item_id, 'location_id': location_id},
                    UpdateExpression='ADD current_stock :qty, pending_stock :neg_qty SET qc_status = :status',
                    ExpressionAttributeValues={
                        ':qty': quantity,
                        ':neg_qty': -quantity,
                        ':status': 'approved'
                    }
                )
            
        except Exception as e:
            logger.error(f"Error updating inventory after QC: {str(e)}")
    
    def _handle_rejected_items(self, item_id: str, location_id: str, quantity: int, reason: str):
        """Handle rejected items from quality check"""
        try:
            # Move to quarantine or return to supplier
            quarantine_record = {
                'item_id': item_id,
                'location_id': location_id,
                'quantity': quantity,
                'rejection_reason': reason,
                'quarantine_date': datetime.utcnow().isoformat(),
                'status': 'quarantined'
            }
            
            # Update inventory
            inventory_table.update_item(
                Key={'item_id': item_id, 'location_id': location_id},
                UpdateExpression='ADD quarantine_stock :qty, pending_stock :neg_qty',
                ExpressionAttributeValues={
                    ':qty': quantity,
                    ':neg_qty': -quantity
                }
            )
            
            logger.info(f"Items quarantined: {json.dumps(quarantine_record)}")
            
        except Exception as e:
            logger.error(f"Error handling rejected items: {str(e)}")
    
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
            # Simple optimization: sort by zone and shelf
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
            # Simple calculation: 2 minutes per item + travel time
            base_time = len(pick_items) * 2
            
            # Add travel time between zones
            zones = set(item.get('zone', '') for item in pick_items)
            travel_time = len(zones) * 3  # 3 minutes per zone change
            
            return base_time + travel_time
            
        except Exception as e:
            logger.error(f"Error calculating pick time: {str(e)}")
            return len(pick_items) * 5  # Fallback estimate
    
    def _get_warehouse_alerts(self) -> List[Dict]:
        """Get current warehouse alerts"""
        alerts = []
        
        try:
            # Check for overdue shipments
            # Check for capacity issues
            # Check for quality issues
            # This would be more comprehensive in real implementation
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting warehouse alerts: {str(e)}")
            return []
    
    def _send_receiving_notification(self, receiving_record: Dict):
        """Send notification about received shipment"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'shipment_received',
                'receiving_id': receiving_record['receiving_id'],
                'po_id': receiving_record['po_id'],
                'supplier_id': receiving_record['supplier_id'],
                'items_count': len(receiving_record['items']),
                'quality_check_required': receiving_record['quality_check_required'],
                'timestamp': receiving_record['received_date']
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Shipment Received: {receiving_record['receiving_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending receiving notification: {str(e)}")
    
    def _send_quality_alert(self, qc_record: Dict):
        """Send alert for quality issues"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'quality_alert',
                'qc_id': qc_record['qc_id'],
                'receiving_id': qc_record['receiving_id'],
                'overall_status': qc_record['overall_status'],
                'rejected_items': len(qc_record['rejected_items']),
                'inspector': qc_record['inspector'],
                'timestamp': qc_record['inspection_date']
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Quality Alert: {qc_record['qc_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending quality alert: {str(e)}")
    
    def _send_shortage_alert(self, pick_list: Dict):
        """Send alert for inventory shortages"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'inventory_shortage',
                'pick_list_id': pick_list['pick_list_id'],
                'order_id': pick_list['order_id'],
                'unavailable_items': pick_list['unavailable_items'],
                'timestamp': pick_list['created_date']
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Inventory Shortage: {pick_list['pick_list_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending shortage alert: {str(e)}")

def lambda_handler(event, context):
    """Main Lambda handler for warehouse management"""
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parse request body
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        
        warehouse_manager = WarehouseManager()
        
        # Route requests
        if http_method == 'GET' and path == '/api/warehouse/overview':
            return warehouse_manager.get_warehouse_overview()
            
        elif http_method == 'POST' and path == '/api/warehouse/receiving':
            return warehouse_manager.process_inbound_shipment(body)
            
        elif http_method == 'POST' and path == '/api/warehouse/quality-check':
            receiving_id = body.get('receiving_id')
            return warehouse_manager.perform_quality_check(receiving_id, body)
            
        elif http_method == 'POST' and path == '/api/warehouse/pick-list':
            return warehouse_manager.create_pick_list(body)
            
        elif http_method == 'PUT' and '/api/warehouse/pick-list/' in path and '/assign' in path:
            pick_list_id = path_parameters.get('pick_list_id')
            picker_id = body.get('picker_id')
            return warehouse_manager.assign_picker(pick_list_id, picker_id)
            
        elif http_method == 'PUT' and '/api/warehouse/pick-list/' in path and '/complete' in path:
            pick_list_id = path_parameters.get('pick_list_id')
            return warehouse_manager.complete_picking(pick_list_id, body)
            
        elif http_method == 'GET' and path == '/api/warehouse/locations':
            return warehouse_manager.get_warehouse_locations(query_parameters)
            
        else:
            return {
                'statusCode': 404,
                'body': {'error': 'Endpoint not found'}
            }
            
    except Exception as e:
        logger.error(f"Unhandled error in warehouse handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': 'Internal server error'}
        }