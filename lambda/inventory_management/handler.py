"""
AquaChain Inventory Management - Main Handler
Handles all inventory operations including items, suppliers, and purchase orders
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
eventbridge = boto3.client('events')

# Table references
inventory_table = dynamodb.Table('AquaChain-Inventory-Items')
suppliers_table = dynamodb.Table('AquaChain-Suppliers')
purchase_orders_table = dynamodb.Table('AquaChain-Purchase-Orders')
warehouse_table = dynamodb.Table('AquaChain-Warehouse-Locations')
forecasts_table = dynamodb.Table('AquaChain-Demand-Forecasts')

class InventoryManager:
    """Core inventory management operations"""
    
    def __init__(self):
        self.sns_topic = os.environ.get('INVENTORY_ALERTS_TOPIC')
        
    def get_inventory_items(self, filters: Optional[Dict] = None) -> Dict:
        """Get inventory items with optional filtering"""
        try:
            if filters:
                # Apply filters using GSI if needed
                if 'category' in filters:
                    response = inventory_table.query(
                        IndexName='CategoryIndex',
                        KeyConditionExpression='category = :cat',
                        ExpressionAttributeValues={':cat': filters['category']}
                    )
                elif 'supplier_id' in filters:
                    response = inventory_table.query(
                        IndexName='SupplierIndex',
                        KeyConditionExpression='supplier_id = :sid',
                        ExpressionAttributeValues={':sid': filters['supplier_id']}
                    )
                else:
                    response = inventory_table.scan()
            else:
                response = inventory_table.scan()
                
            items = response.get('Items', [])
            
            # Calculate derived metrics
            for item in items:
                item['stock_status'] = self._calculate_stock_status(item)
                item['days_of_supply'] = self._calculate_days_of_supply(item)
                
            return {
                'statusCode': 200,
                'body': {
                    'items': items,
                    'count': len(items),
                    'low_stock_count': len([i for i in items if i.get('stock_status') == 'low']),
                    'out_of_stock_count': len([i for i in items if i.get('stock_status') == 'out'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting inventory items: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve inventory items'}
            }
    
    def update_inventory_item(self, item_id: str, location_id: str, updates: Dict) -> Dict:
        """Update inventory item with audit trail"""
        try:
            # Get current item for audit
            current_response = inventory_table.get_item(
                Key={'item_id': item_id, 'location_id': location_id}
            )
            
            if 'Item' not in current_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Inventory item not found'}
                }
            
            current_item = current_response['Item']
            
            # Prepare update expression
            update_expression = "SET updated_at = :now"
            expression_values = {':now': datetime.utcnow().isoformat()}
            
            # Build update expression dynamically
            for key, value in updates.items():
                if key not in ['item_id', 'location_id']:  # Don't update keys
                    update_expression += f", {key} = :{key}"
                    expression_values[f":{key}"] = value
            
            # Update the item
            response = inventory_table.update_item(
                Key={'item_id': item_id, 'location_id': location_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            updated_item = response['Attributes']
            
            # Check if reorder is needed
            self._check_reorder_needed(updated_item)
            
            # Log audit trail
            self._log_inventory_change(current_item, updated_item, 'UPDATE')
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Inventory item updated successfully',
                    'item': updated_item
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating inventory item: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update inventory item'}
            }
    
    def create_inventory_item(self, item_data: Dict) -> Dict:
        """Create new inventory item"""
        try:
            # Generate item ID if not provided
            if 'item_id' not in item_data:
                item_data['item_id'] = f"INV-{uuid.uuid4().hex[:8].upper()}"
            
            # Set default values
            now = datetime.utcnow().isoformat()
            item_data.update({
                'created_at': now,
                'updated_at': now,
                'status': 'active',
                'reorder_status': 'normal'
            })
            
            # Validate required fields
            required_fields = ['item_id', 'location_id', 'name', 'category', 'current_stock']
            for field in required_fields:
                if field not in item_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Create the item
            inventory_table.put_item(Item=item_data)
            
            # Log audit trail
            self._log_inventory_change(None, item_data, 'CREATE')
            
            return {
                'statusCode': 201,
                'body': {
                    'message': 'Inventory item created successfully',
                    'item': item_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating inventory item: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create inventory item'}
            }
    
    def get_low_stock_alerts(self) -> Dict:
        """Get items that need restocking"""
        try:
            response = inventory_table.query(
                IndexName='ReorderStatusIndex',
                KeyConditionExpression='reorder_status = :status',
                ExpressionAttributeValues={':status': 'low'}
            )
            
            low_stock_items = response.get('Items', [])
            
            # Enrich with supplier information
            for item in low_stock_items:
                if 'supplier_id' in item:
                    supplier_response = suppliers_table.get_item(
                        Key={'supplier_id': item['supplier_id']}
                    )
                    if 'Item' in supplier_response:
                        item['supplier_info'] = supplier_response['Item']
            
            return {
                'statusCode': 200,
                'body': {
                    'low_stock_items': low_stock_items,
                    'count': len(low_stock_items),
                    'urgent_count': len([i for i in low_stock_items if i.get('current_stock', 0) == 0])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting low stock alerts: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve low stock alerts'}
            }
    
    def _calculate_stock_status(self, item: Dict) -> str:
        """Calculate stock status based on current levels"""
        current_stock = item.get('current_stock', 0)
        reorder_point = item.get('reorder_point', 0)
        safety_stock = item.get('safety_stock', 0)
        
        if current_stock == 0:
            return 'out'
        elif current_stock <= safety_stock:
            return 'critical'
        elif current_stock <= reorder_point:
            return 'low'
        else:
            return 'normal'
    
    def _calculate_days_of_supply(self, item: Dict) -> int:
        """Calculate days of supply based on average demand"""
        current_stock = item.get('current_stock', 0)
        avg_daily_demand = item.get('avg_daily_demand', 1)
        
        if avg_daily_demand <= 0:
            return 999  # Infinite supply if no demand
        
        return int(current_stock / avg_daily_demand)
    
    def _check_reorder_needed(self, item: Dict):
        """Check if item needs reordering and trigger if necessary"""
        stock_status = self._calculate_stock_status(item)
        
        if stock_status in ['low', 'critical', 'out']:
            # Update reorder status
            inventory_table.update_item(
                Key={'item_id': item['item_id'], 'location_id': item['location_id']},
                UpdateExpression='SET reorder_status = :status',
                ExpressionAttributeValues={':status': stock_status}
            )
            
            # Send alert
            self._send_reorder_alert(item, stock_status)
            
            # Trigger automated reorder if enabled
            if item.get('auto_reorder', False) and stock_status in ['critical', 'out']:
                self._trigger_automated_reorder(item)
    
    def _send_reorder_alert(self, item: Dict, status: str):
        """Send reorder alert notification"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'alert_type': 'reorder_needed',
                'item_id': item['item_id'],
                'item_name': item.get('name', 'Unknown'),
                'current_stock': item.get('current_stock', 0),
                'reorder_point': item.get('reorder_point', 0),
                'status': status,
                'location_id': item['location_id'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Reorder Alert: {item.get('name', 'Unknown Item')}"
            )
            
        except Exception as e:
            logger.error(f"Error sending reorder alert: {str(e)}")
    
    def _trigger_automated_reorder(self, item: Dict):
        """Trigger automated reorder process"""
        try:
            # Create EventBridge event for automated reorder
            event_detail = {
                'item_id': item['item_id'],
                'location_id': item['location_id'],
                'supplier_id': item.get('supplier_id'),
                'recommended_quantity': item.get('reorder_quantity', 100),
                'urgency': 'high' if item.get('current_stock', 0) == 0 else 'medium'
            }
            
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.inventory',
                        'DetailType': 'Automated Reorder Triggered',
                        'Detail': json.dumps(event_detail)
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error triggering automated reorder: {str(e)}")
    
    def _log_inventory_change(self, old_item: Optional[Dict], new_item: Dict, action: str):
        """Log inventory changes for audit trail"""
        try:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': action,
                'item_id': new_item['item_id'],
                'location_id': new_item['location_id'],
                'changes': {}
            }
            
            if old_item and action == 'UPDATE':
                # Track what changed
                for key, new_value in new_item.items():
                    old_value = old_item.get(key)
                    if old_value != new_value:
                        audit_entry['changes'][key] = {
                            'old': old_value,
                            'new': new_value
                        }
            
            # Store in audit table (would need separate table)
            logger.info(f"Inventory audit: {json.dumps(audit_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging inventory change: {str(e)}")

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