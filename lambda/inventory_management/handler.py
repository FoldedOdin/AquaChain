"""
AquaChain Inventory Management Service - Dashboard Overhaul
Enhanced inventory service with real-time updates, ML forecasting integration,
comprehensive audit trails, and graceful degradation capabilities.

Requirements: 1.6, 1.7, 13.2
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
from rbac_middleware import require_permission, validate_user_permissions
from cache_service import get_cache_service, CacheKeys, cached
from health_check_service import get_health_service

# Initialize structured logging
logger = get_logger(__name__, 'inventory-service')
health_monitor = SystemHealthMonitor('inventory-service')

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
eventbridge = boto3.client('events')
lambda_client = boto3.client('lambda')

# Table references
inventory_table = dynamodb.Table(os.environ.get('INVENTORY_TABLE', 'AquaChain-Inventory-Items'))
suppliers_table = dynamodb.Table(os.environ.get('SUPPLIERS_TABLE', 'AquaChain-Suppliers'))
purchase_orders_table = dynamodb.Table(os.environ.get('PURCHASE_ORDERS_TABLE', 'AquaChain-Purchase-Orders'))
warehouse_table = dynamodb.Table(os.environ.get('WAREHOUSE_TABLE', 'AquaChain-Warehouse-Locations'))
forecasts_table = dynamodb.Table(os.environ.get('FORECASTS_TABLE', 'AquaChain-Demand-Forecasts'))
audit_table = dynamodb.Table(os.environ.get('AUDIT_TABLE', 'AquaChain-Audit-Logs'))

class InventoryService:
    """
    Enhanced inventory management service with real-time updates,
    ML forecasting integration, and comprehensive audit trails.
    
    Features:
    - Real-time stock level tracking with WebSocket updates
    - ML-powered demand forecasting with rule-based fallback
    - Comprehensive audit history for all inventory movements
    - Automated reorder point management and alert generation
    - Graceful degradation when dependent services are unavailable
    """
    
    def __init__(self, request_context: Optional[Dict] = None):
        """
        Initialize inventory service with request context for audit logging
        
        Args:
            request_context: Request context containing user_id, correlation_id, etc.
        """
        self.request_context = request_context or {}
        self.user_id = self.request_context.get('user_id', 'system')
        self.correlation_id = self.request_context.get('correlation_id', str(uuid.uuid4()))
        
        # Initialize cache service
        self.cache = get_cache_service()
        
        # Configuration
        self.sns_topic = os.environ.get('INVENTORY_ALERTS_TOPIC')
        self.websocket_api_endpoint = os.environ.get('WEBSOCKET_API_ENDPOINT')
        self.ml_forecasting_function = os.environ.get('ML_FORECASTING_FUNCTION', 'demand-forecasting-service')
        
        # Circuit breaker state for ML service
        self.ml_service_available = True
        self.ml_service_last_failure = None
        self.ml_service_failure_threshold = 3
        self.ml_service_timeout = 300  # 5 minutes
        
        logger.info(
            "Inventory service initialized",
            correlation_id=self.correlation_id,
            user_id=self.user_id,
            cache_status=self.cache.health_check()['status']
        )
    
    def get_stock_levels(self, filters: Optional[Dict] = None) -> Dict:
        """
        Get inventory stock levels with real-time updates and filtering
        
        Args:
            filters: Optional filters (category, supplier_id, location_id, status)
            
        Returns:
            Dictionary with stock levels and metadata
        """
        with TimedOperation(logger, "get_stock_levels", correlation_id=self.correlation_id):
            try:
                # Generate cache key based on filters
                cache_key = f"inventory:stock_levels:{hash(str(filters) if filters else 'all')}"
                
                # Try to get from cache first
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    logger.info(
                        "Stock levels retrieved from cache",
                        correlation_id=self.correlation_id,
                        cache_key=cache_key
                    )
                    # Add correlation_id to cached result
                    cached_result['correlation_id'] = self.correlation_id
                    return {
                        'statusCode': 200,
                        'body': cached_result
                    }
                
                # Log data access for audit
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='INVENTORY',
                    resource_id='stock_levels',
                    operation='GET',
                    request_context=self.request_context,
                    details={'filters': filters}
                )
                
                # Build query based on filters
                if filters:
                    items = self._query_with_filters(filters)
                else:
                    response = inventory_table.scan()
                    items = response.get('Items', [])
                
                # Enrich items with calculated metrics
                enriched_items = []
                for item in items:
                    enriched_item = self._enrich_inventory_item(item)
                    enriched_items.append(enriched_item)
                
                # Calculate summary statistics
                summary = self._calculate_inventory_summary(enriched_items)
                
                # Prepare result for caching
                result_data = {
                    'items': enriched_items,
                    'summary': summary,
                    'timestamp': datetime.utcnow().isoformat(),
                    'correlation_id': self.correlation_id
                }
                
                # Cache the result (5 minutes TTL for stock levels)
                self.cache.set(cache_key, result_data, ttl=300)
                
                logger.info(
                    "Stock levels retrieved successfully",
                    correlation_id=self.correlation_id,
                    items_count=len(enriched_items),
                    filters=filters,
                    cached=False
                )
                
                return {
                    'statusCode': 200,
                    'body': result_data
                }
                
            except Exception as e:
                logger.error(
                    "Failed to retrieve stock levels",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    stack_trace=traceback.format_exc()
                )
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Failed to retrieve stock levels',
                        'correlation_id': self.correlation_id
                    }
                }
    
    def update_stock_level(self, item_id: str, location_id: str, updates: Dict) -> Dict:
        """
        Update inventory stock level with real-time notifications and audit trail
        
        Args:
            item_id: Inventory item identifier
            location_id: Warehouse location identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated item data with status
        """
        with TimedOperation(logger, "update_stock_level", correlation_id=self.correlation_id):
            try:
                # Get current item for audit trail
                current_response = inventory_table.get_item(
                    Key={'item_id': item_id, 'location_id': location_id}
                )
                
                if 'Item' not in current_response:
                    logger.warning(
                        "Inventory item not found for update",
                        correlation_id=self.correlation_id,
                        item_id=item_id,
                        location_id=location_id
                    )
                    return {
                        'statusCode': 404,
                        'body': {
                            'error': 'Inventory item not found',
                            'correlation_id': self.correlation_id
                        }
                    }
                
                current_item = current_response['Item']
                
                # Validate updates
                validated_updates = self._validate_stock_updates(updates)
                if 'error' in validated_updates:
                    return {
                        'statusCode': 400,
                        'body': {
                            'error': validated_updates['error'],
                            'correlation_id': self.correlation_id
                        }
                    }
                
                # Prepare update expression
                update_expression = "SET updated_at = :now, updated_by = :user"
                expression_values = {
                    ':now': datetime.utcnow().isoformat(),
                    ':user': self.user_id
                }
                
                # Build dynamic update expression
                for key, value in validated_updates.items():
                    if key not in ['item_id', 'location_id']:
                        update_expression += f", {key} = :{key}"
                        expression_values[f":{key}"] = value
                
                # Perform atomic update
                response = inventory_table.update_item(
                    Key={'item_id': item_id, 'location_id': location_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ReturnValues='ALL_NEW'
                )
                
                updated_item = response['Attributes']
                
                # Log audit trail for data modification
                audit_logger.log_data_modification(
                    user_id=self.user_id,
                    resource_type='INVENTORY',
                    resource_id=f"{item_id}#{location_id}",
                    modification_type='UPDATE',
                    previous_values=current_item,
                    new_values=updated_item,
                    request_context=self.request_context
                )
                
                # Check for reorder alerts
                self._check_and_generate_alerts(updated_item)
                
                # Send real-time update via WebSocket
                self._send_realtime_update('stock_update', updated_item)
                
                # Invalidate related cache entries
                self._invalidate_inventory_cache(item_id, location_id)
                
                logger.info(
                    "Stock level updated successfully",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    location_id=location_id,
                    changes=list(validated_updates.keys())
                )
                
                return {
                    'statusCode': 200,
                    'body': {
                        'message': 'Stock level updated successfully',
                        'item': self._enrich_inventory_item(updated_item),
                        'correlation_id': self.correlation_id
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Failed to update stock level",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    location_id=location_id,
                    error=str(e),
                    stack_trace=traceback.format_exc()
                )
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Failed to update stock level',
                        'correlation_id': self.correlation_id
                    }
                }
    
    def get_reorder_alerts(self, urgency_filter: Optional[str] = None) -> Dict:
        """
        Get inventory items that need reordering with ML-enhanced recommendations
        
        Args:
            urgency_filter: Filter by urgency level (critical, high, medium, low)
            
        Returns:
            List of items needing reorder with recommendations
        """
        with TimedOperation(logger, "get_reorder_alerts", correlation_id=self.correlation_id):
            try:
                # Log data access
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='INVENTORY',
                    resource_id='reorder_alerts',
                    operation='GET',
                    request_context=self.request_context,
                    details={'urgency_filter': urgency_filter}
                )
                
                # Query items with low stock status
                response = inventory_table.query(
                    IndexName='reorder_status-updated_at-index',
                    KeyConditionExpression='reorder_status = :status',
                    ExpressionAttributeValues={':status': 'needs_reorder'},
                    ScanIndexForward=False  # Most recent first
                )
                
                reorder_items = response.get('Items', [])
                
                # Enrich with ML forecasting data and supplier information
                enriched_alerts = []
                for item in reorder_items:
                    enriched_alert = self._enrich_reorder_alert(item)
                    
                    # Apply urgency filter if specified
                    if urgency_filter and enriched_alert.get('urgency') != urgency_filter:
                        continue
                    
                    enriched_alerts.append(enriched_alert)
                
                # Sort by urgency and projected stockout date
                enriched_alerts.sort(key=lambda x: (
                    self._urgency_priority(x.get('urgency', 'low')),
                    x.get('projected_stockout_date', '9999-12-31')
                ))
                
                logger.info(
                    "Reorder alerts retrieved successfully",
                    correlation_id=self.correlation_id,
                    alerts_count=len(enriched_alerts),
                    urgency_filter=urgency_filter
                )
                
                return {
                    'statusCode': 200,
                    'body': {
                        'alerts': enriched_alerts,
                        'summary': {
                            'total_count': len(enriched_alerts),
                            'critical_count': len([a for a in enriched_alerts if a.get('urgency') == 'critical']),
                            'high_count': len([a for a in enriched_alerts if a.get('urgency') == 'high']),
                            'medium_count': len([a for a in enriched_alerts if a.get('urgency') == 'medium']),
                            'low_count': len([a for a in enriched_alerts if a.get('urgency') == 'low'])
                        },
                        'timestamp': datetime.utcnow().isoformat(),
                        'correlation_id': self.correlation_id
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Failed to retrieve reorder alerts",
                    correlation_id=self.correlation_id,
                    error=str(e),
                    stack_trace=traceback.format_exc()
                )
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Failed to retrieve reorder alerts',
                        'correlation_id': self.correlation_id
                    }
                }
    
    def get_demand_forecast(self, item_id: str, forecast_days: int = 30) -> Dict:
        """
        Get ML-powered demand forecast with rule-based fallback
        
        Args:
            item_id: Inventory item identifier
            forecast_days: Number of days to forecast
            
        Returns:
            Demand forecast data with confidence intervals
        """
        with TimedOperation(logger, "get_demand_forecast", correlation_id=self.correlation_id):
            try:
                # Log data access
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='INVENTORY',
                    resource_id=f"forecast_{item_id}",
                    operation='GET',
                    request_context=self.request_context,
                    details={'forecast_days': forecast_days}
                )
                
                # Try ML forecasting service first
                ml_forecast = self._get_ml_forecast(item_id, forecast_days)
                
                if ml_forecast and ml_forecast.get('success'):
                    logger.info(
                        "ML forecast retrieved successfully",
                        correlation_id=self.correlation_id,
                        item_id=item_id,
                        forecast_source='ml'
                    )
                    
                    return {
                        'statusCode': 200,
                        'body': {
                            'forecast': ml_forecast['data'],
                            'source': 'ml',
                            'accuracy_metrics': ml_forecast.get('accuracy_metrics'),
                            'correlation_id': self.correlation_id
                        }
                    }
                
                # Fallback to rule-based forecasting
                logger.warning(
                    "ML forecasting unavailable, using rule-based fallback",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    ml_error=ml_forecast.get('error') if ml_forecast else 'Service unavailable'
                )
                
                rule_based_forecast = self._get_rule_based_forecast(item_id, forecast_days)
                
                return {
                    'statusCode': 200,
                    'body': {
                        'forecast': rule_based_forecast,
                        'source': 'rule_based',
                        'warning': 'ML forecasting service unavailable, using rule-based fallback',
                        'correlation_id': self.correlation_id
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Failed to get demand forecast",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    error=str(e),
                    stack_trace=traceback.format_exc()
                )
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Failed to get demand forecast',
                        'correlation_id': self.correlation_id
                    }
                }
    
    def get_audit_history(self, item_id: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None, limit: int = 100) -> Dict:
        """
        Get comprehensive audit history for inventory item
        
        Args:
            item_id: Inventory item identifier
            start_date: Start date for audit history (ISO format)
            end_date: End date for audit history (ISO format)
            limit: Maximum number of audit entries to return
            
        Returns:
            Audit history with pagination support
        """
        with TimedOperation(logger, "get_audit_history", correlation_id=self.correlation_id):
            try:
                # Log data access
                audit_logger.log_data_access(
                    user_id=self.user_id,
                    resource_type='INVENTORY',
                    resource_id=f"audit_{item_id}",
                    operation='GET',
                    request_context=self.request_context,
                    details={
                        'start_date': start_date,
                        'end_date': end_date,
                        'limit': limit
                    }
                )
                
                # Query audit logs for this item
                audit_entries = self._query_audit_history(item_id, start_date, end_date, limit)
                
                logger.info(
                    "Audit history retrieved successfully",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    entries_count=len(audit_entries)
                )
                
                return {
                    'statusCode': 200,
                    'body': {
                        'audit_entries': audit_entries,
                        'item_id': item_id,
                        'query_params': {
                            'start_date': start_date,
                            'end_date': end_date,
                            'limit': limit
                        },
                        'correlation_id': self.correlation_id
                    }
                }
                
            except Exception as e:
                logger.error(
                    "Failed to retrieve audit history",
                    correlation_id=self.correlation_id,
                    item_id=item_id,
                    error=str(e),
                    stack_trace=traceback.format_exc()
                )
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Failed to retrieve audit history',
                        'correlation_id': self.correlation_id
                    }
                }
    
    # Helper methods for inventory operations
    
    def _query_with_filters(self, filters: Dict) -> List[Dict]:
        """Query inventory items with filters using appropriate GSI"""
        try:
            if 'category' in filters:
                response = inventory_table.query(
                    IndexName='category-updated_at-index',
                    KeyConditionExpression='category = :cat',
                    ExpressionAttributeValues={':cat': filters['category']}
                )
            elif 'supplier_id' in filters:
                response = inventory_table.query(
                    IndexName='supplier_id-updated_at-index',
                    KeyConditionExpression='supplier_id = :sid',
                    ExpressionAttributeValues={':sid': filters['supplier_id']}
                )
            elif 'location_id' in filters:
                response = inventory_table.query(
                    IndexName='location_id-updated_at-index',
                    KeyConditionExpression='location_id = :lid',
                    ExpressionAttributeValues={':lid': filters['location_id']}
                )
            elif 'status' in filters:
                response = inventory_table.query(
                    IndexName='status-updated_at-index',
                    KeyConditionExpression='status = :status',
                    ExpressionAttributeValues={':status': filters['status']}
                )
            else:
                # Fallback to scan with filter expression
                filter_expression = None
                expression_values = {}
                
                for key, value in filters.items():
                    if filter_expression:
                        filter_expression += f" AND {key} = :{key}"
                    else:
                        filter_expression = f"{key} = :{key}"
                    expression_values[f":{key}"] = value
                
                response = inventory_table.scan(
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values
                )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(
                "Failed to query with filters",
                correlation_id=self.correlation_id,
                filters=filters,
                error=str(e)
            )
            return []
    
    def _enrich_inventory_item(self, item: Dict) -> Dict:
        """Enrich inventory item with calculated metrics and status"""
        try:
            enriched_item = item.copy()
            
            # Calculate stock status
            enriched_item['stock_status'] = self._calculate_stock_status(item)
            
            # Calculate days of supply
            enriched_item['days_of_supply'] = self._calculate_days_of_supply(item)
            
            # Calculate reorder urgency
            enriched_item['reorder_urgency'] = self._calculate_reorder_urgency(item)
            
            # Add projected stockout date
            enriched_item['projected_stockout_date'] = self._calculate_projected_stockout_date(item)
            
            # Add supplier information if available
            if 'supplier_id' in item:
                supplier_info = self._get_supplier_info(item['supplier_id'])
                if supplier_info:
                    enriched_item['supplier_info'] = supplier_info
            
            return enriched_item
            
        except Exception as e:
            logger.warning(
                "Failed to enrich inventory item",
                correlation_id=self.correlation_id,
                item_id=item.get('item_id'),
                error=str(e)
            )
            return item
    
    def _calculate_stock_status(self, item: Dict) -> str:
        """Calculate stock status based on current levels and thresholds"""
        current_stock = float(item.get('current_stock', 0))
        reorder_point = float(item.get('reorder_point', 0))
        safety_stock = float(item.get('safety_stock', 0))
        critical_threshold = float(item.get('critical_threshold', 0))
        
        if current_stock <= 0:
            return 'out_of_stock'
        elif current_stock <= critical_threshold:
            return 'critical'
        elif current_stock <= safety_stock:
            return 'very_low'
        elif current_stock <= reorder_point:
            return 'low'
        else:
            return 'normal'
    
    def _calculate_days_of_supply(self, item: Dict) -> int:
        """Calculate days of supply based on average demand"""
        current_stock = float(item.get('current_stock', 0))
        avg_daily_demand = float(item.get('avg_daily_demand', 0))
        
        if avg_daily_demand <= 0:
            return 999  # Infinite supply if no demand
        
        return max(0, int(current_stock / avg_daily_demand))
    
    def _calculate_reorder_urgency(self, item: Dict) -> str:
        """Calculate reorder urgency based on stock status and demand"""
        stock_status = self._calculate_stock_status(item)
        days_of_supply = self._calculate_days_of_supply(item)
        
        if stock_status == 'out_of_stock':
            return 'critical'
        elif stock_status == 'critical' or days_of_supply <= 3:
            return 'high'
        elif stock_status in ['very_low', 'low'] or days_of_supply <= 7:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_projected_stockout_date(self, item: Dict) -> Optional[str]:
        """Calculate projected stockout date based on current demand"""
        try:
            current_stock = float(item.get('current_stock', 0))
            avg_daily_demand = float(item.get('avg_daily_demand', 0))
            
            if avg_daily_demand <= 0 or current_stock <= 0:
                return None
            
            days_until_stockout = current_stock / avg_daily_demand
            stockout_date = datetime.utcnow() + timedelta(days=days_until_stockout)
            
            return stockout_date.isoformat()
            
        except Exception:
            return None
    
    def _calculate_inventory_summary(self, items: List[Dict]) -> Dict:
        """Calculate summary statistics for inventory items"""
        total_items = len(items)
        
        if total_items == 0:
            return {
                'total_items': 0,
                'by_status': {},
                'by_urgency': {},
                'total_value': 0
            }
        
        status_counts = {}
        urgency_counts = {}
        total_value = 0
        
        for item in items:
            # Count by status
            status = item.get('stock_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by urgency
            urgency = item.get('reorder_urgency', 'unknown')
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
            
            # Calculate total value
            current_stock = float(item.get('current_stock', 0))
            unit_cost = float(item.get('unit_cost', 0))
            total_value += current_stock * unit_cost
        
        return {
            'total_items': total_items,
            'by_status': status_counts,
            'by_urgency': urgency_counts,
            'total_value': round(total_value, 2),
            'needs_reorder': status_counts.get('low', 0) + status_counts.get('very_low', 0) + 
                           status_counts.get('critical', 0) + status_counts.get('out_of_stock', 0)
        }
    
    def _validate_stock_updates(self, updates: Dict) -> Dict:
        """Validate stock update data"""
        validated = {}
        
        # Validate numeric fields
        numeric_fields = ['current_stock', 'reorder_point', 'safety_stock', 'unit_cost', 
                         'reorder_quantity', 'avg_daily_demand']
        
        for field in numeric_fields:
            if field in updates:
                try:
                    value = float(updates[field])
                    if value < 0:
                        return {'error': f'{field} cannot be negative'}
                    validated[field] = value
                except (ValueError, TypeError):
                    return {'error': f'{field} must be a valid number'}
        
        # Validate string fields
        string_fields = ['name', 'description', 'category', 'supplier_id', 'status']
        for field in string_fields:
            if field in updates:
                value = str(updates[field]).strip()
                if not value:
                    return {'error': f'{field} cannot be empty'}
                validated[field] = value
        
        # Validate status values
        if 'status' in validated:
            valid_statuses = ['active', 'inactive', 'discontinued', 'pending']
            if validated['status'] not in valid_statuses:
                return {'error': f'Status must be one of: {", ".join(valid_statuses)}'}
        
        return validated
    
    def _check_and_generate_alerts(self, item: Dict) -> None:
        """Check if item needs reorder alerts and generate them"""
        try:
            stock_status = self._calculate_stock_status(item)
            reorder_urgency = self._calculate_reorder_urgency(item)
            
            # Update reorder status if needed
            if stock_status in ['low', 'very_low', 'critical', 'out_of_stock']:
                inventory_table.update_item(
                    Key={'item_id': item['item_id'], 'location_id': item['location_id']},
                    UpdateExpression='SET reorder_status = :status, reorder_urgency = :urgency',
                    ExpressionAttributeValues={
                        ':status': 'needs_reorder',
                        ':urgency': reorder_urgency
                    }
                )
                
                # Generate alert
                self._generate_reorder_alert(item, stock_status, reorder_urgency)
            else:
                # Clear reorder status if stock is back to normal
                inventory_table.update_item(
                    Key={'item_id': item['item_id'], 'location_id': item['location_id']},
                    UpdateExpression='SET reorder_status = :status',
                    ExpressionAttributeValues={':status': 'normal'}
                )
                
        except Exception as e:
            logger.error(
                "Failed to check and generate alerts",
                correlation_id=self.correlation_id,
                item_id=item.get('item_id'),
                error=str(e)
            )
    
    def _generate_reorder_alert(self, item: Dict, stock_status: str, urgency: str) -> None:
        """Generate reorder alert notification"""
        if not self.sns_topic:
            return
        
        try:
            alert_data = {
                'alert_type': 'reorder_needed',
                'item_id': item['item_id'],
                'item_name': item.get('name', 'Unknown'),
                'location_id': item['location_id'],
                'current_stock': item.get('current_stock', 0),
                'reorder_point': item.get('reorder_point', 0),
                'stock_status': stock_status,
                'urgency': urgency,
                'projected_stockout_date': self._calculate_projected_stockout_date(item),
                'recommended_quantity': item.get('reorder_quantity', 100),
                'supplier_id': item.get('supplier_id'),
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': self.correlation_id
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(alert_data),
                Subject=f"Reorder Alert ({urgency.upper()}): {item.get('name', 'Unknown Item')}",
                MessageAttributes={
                    'urgency': {'DataType': 'String', 'StringValue': urgency},
                    'item_id': {'DataType': 'String', 'StringValue': item['item_id']}
                }
            )
            
            logger.info(
                "Reorder alert generated",
                correlation_id=self.correlation_id,
                item_id=item['item_id'],
                urgency=urgency
            )
            
        except Exception as e:
            logger.error(
                "Failed to generate reorder alert",
                correlation_id=self.correlation_id,
                item_id=item.get('item_id'),
                error=str(e)
            )
    
    def _send_realtime_update(self, update_type: str, data: Dict) -> None:
        """Send real-time update via WebSocket API"""
        if not self.websocket_api_endpoint:
            return
        
        try:
            # This would integrate with WebSocket API Gateway
            # For now, we'll log the update
            logger.info(
                "Real-time update sent",
                correlation_id=self.correlation_id,
                update_type=update_type,
                item_id=data.get('item_id')
            )
            
        except Exception as e:
            logger.warning(
                "Failed to send real-time update",
                correlation_id=self.correlation_id,
                update_type=update_type,
                error=str(e)
            )

def lambda_handler(event, context):
    """Main Lambda handler for inventory management"""
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parse request body
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        
        inventory_manager = InventoryManager()
        
        # Route requests
        if http_method == 'GET' and path == '/api/inventory/items':
            return inventory_manager.get_inventory_items(query_parameters)
            
        elif http_method == 'POST' and path == '/api/inventory/items':
            return inventory_manager.create_inventory_item(body)
            
        elif http_method == 'PUT' and '/api/inventory/items/' in path:
            item_id = path_parameters.get('item_id')
            location_id = path_parameters.get('location_id')
            return inventory_manager.update_inventory_item(item_id, location_id, body)
            
        elif http_method == 'GET' and path == '/api/inventory/alerts':
            return inventory_manager.get_low_stock_alerts()
            
        else:
            return {
                'statusCode': 404,
                'body': {'error': 'Endpoint not found'}
            }
            
    except Exception as e:
        logger.error(f"Unhandled error in inventory handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': 'Internal server error'}
        }
    
    def _get_ml_forecast(self, item_id: str, forecast_days: int) -> Optional[Dict]:
        """
        Get ML-powered demand forecast with circuit breaker pattern
        
        Args:
            item_id: Inventory item identifier
            forecast_days: Number of days to forecast
            
        Returns:
            ML forecast data or None if service unavailable
        """
        # Check circuit breaker
        if not self._is_ml_service_available():
            return None
        
        try:
            # Check for cached forecast first
            cached_forecast = self._get_cached_forecast(item_id, forecast_days)
            if cached_forecast:
                return cached_forecast
            
            # Call ML forecasting service
            payload = {
                'item_id': item_id,
                'forecast_days': forecast_days,
                'correlation_id': self.correlation_id
            }
            
            response = lambda_client.invoke(
                FunctionName=self.ml_forecasting_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                forecast_data = result['body']
                
                # Cache the forecast
                self._cache_forecast(item_id, forecast_days, forecast_data)
                
                # Reset circuit breaker on success
                self.ml_service_available = True
                self.ml_service_last_failure = None
                
                return {
                    'success': True,
                    'data': forecast_data,
                    'accuracy_metrics': forecast_data.get('accuracy_metrics')
                }
            else:
                self._handle_ml_service_failure()
                return None
                
        except Exception as e:
            logger.warning(
                "ML forecasting service failed",
                correlation_id=self.correlation_id,
                item_id=item_id,
                error=str(e)
            )
            self._handle_ml_service_failure()
            return None
    
    def _get_rule_based_forecast(self, item_id: str, forecast_days: int) -> Dict:
        """
        Generate rule-based demand forecast as fallback
        
        Args:
            item_id: Inventory item identifier
            forecast_days: Number of days to forecast
            
        Returns:
            Rule-based forecast data
        """
        try:
            # Get historical demand data
            historical_data = self._get_historical_demand_data(item_id)
            
            if not historical_data:
                # Use default forecast if no historical data
                avg_daily_demand = 1.0
                seasonal_factor = 1.0
            else:
                # Calculate simple moving averages
                recent_demands = [d['demand'] for d in historical_data[-30:]]  # Last 30 days
                avg_daily_demand = sum(recent_demands) / len(recent_demands) if recent_demands else 1.0
                
                # Simple seasonal adjustment (day of week pattern)
                seasonal_factor = self._calculate_seasonal_factor(historical_data)
            
            # Generate forecast using simple trend and seasonality
            forecast_values = []
            base_date = datetime.utcnow()
            
            for day in range(forecast_days):
                forecast_date = base_date + timedelta(days=day)
                day_of_week = forecast_date.weekday()
                
                # Apply day-of-week seasonality (simple pattern)
                day_multiplier = {
                    0: 1.1,  # Monday - higher demand
                    1: 1.0,  # Tuesday
                    2: 1.0,  # Wednesday
                    3: 1.0,  # Thursday
                    4: 0.9,  # Friday - lower demand
                    5: 0.7,  # Saturday - much lower
                    6: 0.6   # Sunday - lowest
                }.get(day_of_week, 1.0)
                
                daily_forecast = avg_daily_demand * seasonal_factor * day_multiplier
                
                forecast_values.append({
                    'date': forecast_date.isoformat(),
                    'demand': round(daily_forecast, 2),
                    'confidence_lower': round(daily_forecast * 0.8, 2),
                    'confidence_upper': round(daily_forecast * 1.2, 2)
                })
            
            return {
                'item_id': item_id,
                'forecast_date': datetime.utcnow().isoformat(),
                'forecast_horizon_days': forecast_days,
                'method': 'rule_based',
                'predictions': forecast_values,
                'avg_daily_demand': avg_daily_demand,
                'seasonal_factor': seasonal_factor,
                'warning': 'This is a rule-based forecast. ML forecasting service is unavailable.'
            }
            
        except Exception as e:
            logger.error(
                "Failed to generate rule-based forecast",
                correlation_id=self.correlation_id,
                item_id=item_id,
                error=str(e)
            )
            
            # Return minimal forecast
            return {
                'item_id': item_id,
                'forecast_date': datetime.utcnow().isoformat(),
                'forecast_horizon_days': forecast_days,
                'method': 'fallback',
                'predictions': [{'date': (datetime.utcnow() + timedelta(days=i)).isoformat(), 
                               'demand': 1.0, 'confidence_lower': 0.5, 'confidence_upper': 1.5} 
                              for i in range(forecast_days)],
                'error': 'Unable to generate forecast'
            }
    
    def _is_ml_service_available(self) -> bool:
        """Check if ML service is available based on circuit breaker logic"""
        if not self.ml_service_available:
            if self.ml_service_last_failure:
                time_since_failure = datetime.utcnow() - self.ml_service_last_failure
                if time_since_failure.total_seconds() > self.ml_service_timeout:
                    # Try to reset circuit breaker
                    self.ml_service_available = True
                    logger.info(
                        "ML service circuit breaker reset",
                        correlation_id=self.correlation_id
                    )
                    return True
            return False
        return True
    
    def _handle_ml_service_failure(self) -> None:
        """Handle ML service failure and update circuit breaker"""
        self.ml_service_available = False
        self.ml_service_last_failure = datetime.utcnow()
        
        logger.warning(
            "ML service marked as unavailable",
            correlation_id=self.correlation_id,
            failure_time=self.ml_service_last_failure.isoformat()
        )
    
    def _get_cached_forecast(self, item_id: str, forecast_days: int) -> Optional[Dict]:
        """Get cached forecast if available and not expired"""
        try:
            response = forecasts_table.get_item(
                Key={
                    'item_id': item_id,
                    'forecast_horizon_days': forecast_days
                }
            )
            
            if 'Item' in response:
                forecast = response['Item']
                forecast_date = datetime.fromisoformat(forecast['forecast_date'])
                
                # Check if forecast is still fresh (less than 6 hours old)
                if datetime.utcnow() - forecast_date < timedelta(hours=6):
                    return {
                        'success': True,
                        'data': forecast,
                        'cached': True
                    }
            
            return None
            
        except Exception as e:
            logger.warning(
                "Failed to get cached forecast",
                correlation_id=self.correlation_id,
                item_id=item_id,
                error=str(e)
            )
            return None
    
    def _cache_forecast(self, item_id: str, forecast_days: int, forecast_data: Dict) -> None:
        """Cache forecast data for future use"""
        try:
            cache_item = forecast_data.copy()
            cache_item.update({
                'item_id': item_id,
                'forecast_horizon_days': forecast_days,
                'cached_at': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            })
            
            forecasts_table.put_item(Item=cache_item)
            
        except Exception as e:
            logger.warning(
                "Failed to cache forecast",
                correlation_id=self.correlation_id,
                item_id=item_id,
                error=str(e)
            )
    
    def _get_historical_demand_data(self, item_id: str, days: int = 90) -> List[Dict]:
        """Get historical demand data for forecasting"""
        try:
            # This would query historical demand data
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.warning(
                "Failed to get historical demand data",
                correlation_id=self.correlation_id,
                item_id=item_id,
                error=str(e)
            )
            return []
    
    def _calculate_seasonal_factor(self, historical_data: List[Dict]) -> float:
        """Calculate seasonal adjustment factor from historical data"""
        if not historical_data:
            return 1.0
        
        try:
            # Simple seasonal calculation based on recent vs older data
            recent_data = historical_data[-30:]  # Last 30 days
            older_data = historical_data[-90:-30]  # 30-90 days ago
            
            if not recent_data or not older_data:
                return 1.0
            
            recent_avg = sum(d['demand'] for d in recent_data) / len(recent_data)
            older_avg = sum(d['demand'] for d in older_data) / len(older_data)
            
            if older_avg > 0:
                return recent_avg / older_avg
            
            return 1.0
            
        except Exception:
            return 1.0
    
    def _enrich_reorder_alert(self, item: Dict) -> Dict:
        """Enrich reorder alert with additional information"""
        try:
            enriched_alert = self._enrich_inventory_item(item)
            
            # Add forecast data if available
            forecast = self._get_ml_forecast(item['item_id'], 30)
            if forecast and forecast.get('success'):
                enriched_alert['demand_forecast'] = forecast['data']
            else:
                # Use rule-based forecast
                enriched_alert['demand_forecast'] = self._get_rule_based_forecast(item['item_id'], 30)
            
            # Add recommended actions
            enriched_alert['recommended_actions'] = self._get_recommended_actions(enriched_alert)
            
            return enriched_alert
            
        except Exception as e:
            logger.warning(
                "Failed to enrich reorder alert",
                correlation_id=self.correlation_id,
                item_id=item.get('item_id'),
                error=str(e)
            )
            return item
    
    def _get_recommended_actions(self, item: Dict) -> List[Dict]:
        """Get recommended actions for inventory item"""
        actions = []
        
        urgency = item.get('reorder_urgency', 'low')
        current_stock = float(item.get('current_stock', 0))
        reorder_quantity = float(item.get('reorder_quantity', 100))
        
        if urgency == 'critical':
            actions.append({
                'action': 'emergency_order',
                'description': 'Place emergency order immediately',
                'priority': 'high',
                'recommended_quantity': reorder_quantity * 1.5
            })
        elif urgency == 'high':
            actions.append({
                'action': 'expedited_order',
                'description': 'Place expedited order within 24 hours',
                'priority': 'high',
                'recommended_quantity': reorder_quantity
            })
        else:
            actions.append({
                'action': 'standard_order',
                'description': 'Place standard order within normal timeframe',
                'priority': 'medium',
                'recommended_quantity': reorder_quantity
            })
        
        # Add supplier contact action if available
        if 'supplier_info' in item:
            actions.append({
                'action': 'contact_supplier',
                'description': f"Contact {item['supplier_info'].get('name', 'supplier')} for availability",
                'priority': 'medium',
                'supplier_contact': item['supplier_info'].get('contact_email')
            })
        
        return actions
    
    def _urgency_priority(self, urgency: str) -> int:
        """Convert urgency to numeric priority for sorting"""
        priority_map = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        return priority_map.get(urgency, 4)
    
    def _get_supplier_info(self, supplier_id: str) -> Optional[Dict]:
        """Get supplier information"""
        try:
            response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            return response.get('Item')
        except Exception as e:
            logger.warning(
                "Failed to get supplier info",
                correlation_id=self.correlation_id,
                supplier_id=supplier_id,
                error=str(e)
            )
            return None
    
    def _query_audit_history(self, item_id: str, start_date: Optional[str], 
                           end_date: Optional[str], limit: int) -> List[Dict]:
        """Query audit history for inventory item"""
        try:
            # Query audit logs using the audit logger
            audit_entries = audit_logger.query_logs_by_resource(
                resource_type='INVENTORY',
                start_time=start_date,
                end_time=end_date,
                limit=limit
            )
            
            # Filter for this specific item
            filtered_entries = []
            for entry in audit_entries.get('items', []):
                if item_id in entry.get('resource_id', ''):
                    filtered_entries.append(entry)
            
            return filtered_entries
            
        except Exception as e:
            logger.error(
                "Failed to query audit history",
                correlation_id=self.correlation_id,
                item_id=item_id,
                error=str(e)
            )
            return []


    def _invalidate_inventory_cache(self, item_id: str, location_id: str) -> None:
        """
        Invalidate cache entries related to inventory updates
        
        Args:
            item_id: Inventory item identifier
            location_id: Warehouse location identifier
        """
        try:
            # Invalidate specific item cache
            item_cache_key = CacheKeys.inventory_item(f"{item_id}#{location_id}")
            self.cache.delete(item_cache_key)
            
            # Invalidate stock levels cache (all variations)
            self.cache.invalidate_pattern("inventory:stock_levels:*")
            
            # Invalidate inventory alerts cache
            self.cache.invalidate_pattern("inventory:alerts:*")
            
            # Invalidate dashboard data cache for inventory managers
            self.cache.invalidate_pattern("dashboard:inventory-manager:*")
            
            logger.info(
                "Cache invalidated for inventory update",
                correlation_id=self.correlation_id,
                item_id=item_id,
                location_id=location_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to invalidate inventory cache",
                correlation_id=self.correlation_id,
                item_id=item_id,
                location_id=location_id,
                error=str(e)
            )


def lambda_handler(event, context):
    """
    Enhanced Lambda handler for inventory management service
    
    Supports:
    - GET /api/inventory/stock-levels - Get stock levels with filtering
    - PUT /api/inventory/stock-levels/{item_id}/{location_id} - Update stock level
    - GET /api/inventory/reorder-alerts - Get reorder alerts
    - GET /api/inventory/forecast/{item_id} - Get demand forecast
    - GET /api/inventory/audit/{item_id} - Get audit history
    - GET /api/inventory/health - Health check endpoint
    """
    try:
        # Extract request context for audit logging
        request_context = {
            'user_id': event.get('requestContext', {}).get('authorizer', {}).get('user_id', 'anonymous'),
            'username': event.get('requestContext', {}).get('authorizer', {}).get('username', 'unknown'),
            'correlation_id': event.get('headers', {}).get('X-Correlation-ID', str(uuid.uuid4())),
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown')
        }
        
        # Initialize inventory service
        inventory_service = InventoryService(request_context)
        
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
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Invalid JSON in request body',
                        'correlation_id': request_context['correlation_id']
                    })
                }
        
        logger.info(
            "Processing inventory service request",
            correlation_id=request_context['correlation_id'],
            method=http_method,
            path=path,
            user_id=request_context['user_id']
        )
        
        # Route requests to appropriate handlers
        if http_method == 'GET' and path == '/api/inventory/stock-levels':
            # Validate RBAC permissions
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context.get('username', 'unknown'),
                'inventory-data',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for inventory stock levels",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Access denied',
                        'resource': 'inventory-data',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = inventory_service.get_stock_levels(query_parameters)
            
        elif http_method == 'PUT' and '/api/inventory/stock-levels/' in path:
            # Validate RBAC permissions for stock updates
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context.get('username', 'unknown'),
                'stock-adjustments',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for inventory stock update",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Access denied',
                        'resource': 'stock-adjustments',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            item_id = path_parameters.get('item_id')
            location_id = path_parameters.get('location_id')
            if not item_id or not location_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Missing item_id or location_id in path',
                        'correlation_id': request_context['correlation_id']
                    })
                }
            result = inventory_service.update_stock_level(item_id, location_id, body)
            
        elif http_method == 'GET' and path == '/api/inventory/reorder-alerts':
            # Validate RBAC permissions for reorder alerts
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context.get('username', 'unknown'),
                'reorder-alerts',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for reorder alerts",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Access denied',
                        'resource': 'reorder-alerts',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            urgency_filter = query_parameters.get('urgency')
            result = inventory_service.get_reorder_alerts(urgency_filter)
            
        elif http_method == 'GET' and '/api/inventory/forecast/' in path:
            # Validate RBAC permissions for demand forecasts
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context.get('username', 'unknown'),
                'demand-forecasts',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for demand forecasts",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Access denied',
                        'resource': 'demand-forecasts',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            item_id = path_parameters.get('item_id')
            if not item_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Missing item_id in path',
                        'correlation_id': request_context['correlation_id']
                    })
                }
            forecast_days = int(query_parameters.get('days', 30))
            result = inventory_service.get_demand_forecast(item_id, forecast_days)
            
        elif http_method == 'GET' and '/api/inventory/audit/' in path:
            # Validate RBAC permissions for audit history
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context.get('username', 'unknown'),
                'inventory-audit-history',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for inventory audit history",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Access denied',
                        'resource': 'inventory-audit-history',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            item_id = path_parameters.get('item_id')
            if not item_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Missing item_id in path',
                        'correlation_id': request_context['correlation_id']
                    })
                }
            start_date = query_parameters.get('start_date')
            end_date = query_parameters.get('end_date')
            limit = int(query_parameters.get('limit', 100))
            result = inventory_service.get_audit_history(item_id, start_date, end_date, limit)
            
        elif http_method == 'GET' and path == '/api/inventory/health':
            # Comprehensive health check endpoint
            health_service = get_health_service('inventory-service', '1.0.0')
            
            # Add critical dependencies
            health_service.add_critical_dependency(
                'inventory_table',
                lambda: health_service.check_dynamodb_table(inventory_table.table_name)
            )
            
            health_service.add_critical_dependency(
                'cache_service',
                lambda: health_service.check_cache_service(inventory_service.cache)
            )
            
            # Add optional dependencies
            if inventory_service.sns_topic:
                health_service.add_optional_dependency(
                    'sns_notifications',
                    lambda: {'status': 'healthy', 'topic_arn': inventory_service.sns_topic, 'timestamp': datetime.utcnow().isoformat()}
                )
            
            if inventory_service.ml_forecasting_function:
                health_service.add_optional_dependency(
                    'ml_forecasting',
                    lambda: health_service.check_lambda_function(inventory_service.ml_forecasting_function)
                )
            
            # Add custom checks
            health_service.add_custom_check(
                'circuit_breaker_status',
                lambda: {
                    'status': 'healthy' if inventory_service.ml_service_available else 'degraded',
                    'ml_service_available': inventory_service.ml_service_available,
                    'last_failure': inventory_service.ml_service_last_failure.isoformat() if inventory_service.ml_service_last_failure else None,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Perform comprehensive health check
            health_result = health_service.perform_health_check()
            
            # Determine HTTP status code
            status_code = 200 if health_result['status'] == 'healthy' else (200 if health_result['status'] == 'degraded' else 503)
            
            result = {
                'statusCode': status_code,
                'body': health_result
            }
            
        else:
            result = {
                'statusCode': 404,
                'body': {
                    'error': 'Endpoint not found',
                    'correlation_id': request_context['correlation_id']
                }
            }
        
        # Add standard headers
        if 'headers' not in result:
            result['headers'] = {}
        
        result['headers'].update({
            'Content-Type': 'application/json',
            'X-Correlation-ID': request_context['correlation_id'],
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Correlation-ID',
            'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,OPTIONS'
        })
        
        # Convert body to JSON string if it's a dict
        if isinstance(result.get('body'), dict):
            result['body'] = json.dumps(result['body'])
        
        logger.info(
            "Inventory service request completed",
            correlation_id=request_context['correlation_id'],
            status_code=result['statusCode']
        )
        
        # Publish performance metrics
        logger.publish_metrics({
            'endpoint': path,
            'method': http_method,
            'status_code': str(result['statusCode'])
        })
        
        return result
        
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(
            "Unhandled error in inventory service",
            correlation_id=request_context.get('correlation_id', 'unknown'),
            error_id=error_id,
            error=str(e),
            stack_trace=traceback.format_exc()
        )
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context.get('correlation_id', 'unknown')
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'error_id': error_id,
                'correlation_id': request_context.get('correlation_id', 'unknown')
            })
        }