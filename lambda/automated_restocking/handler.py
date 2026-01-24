"""
AquaChain Automated Restocking - Intelligent Order Generation
Automatically generates purchase orders based on ML forecasts and inventory levels
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
forecasts_table = dynamodb.Table('AquaChain-Demand-Forecasts')

class AutomatedRestockingEngine:
    """Intelligent automated restocking system"""
    
    def __init__(self):
        self.sns_topic = os.environ.get('RESTOCKING_ALERTS_TOPIC')
        self.max_order_value = float(os.environ.get('MAX_AUTO_ORDER_VALUE', '5000'))
        self.safety_factor = float(os.environ.get('SAFETY_FACTOR', '1.2'))
        
    def process_reorder_event(self, event_detail: Dict) -> Dict:
        """Process automated reorder event from EventBridge"""
        try:
            item_id = event_detail['item_id']
            location_id = event_detail['location_id']
            supplier_id = event_detail.get('supplier_id')
            urgency = event_detail.get('urgency', 'medium')
            
            # Get current inventory status
            inventory_response = inventory_table.get_item(
                Key={'item_id': item_id, 'location_id': location_id}
            )
            
            if 'Item' not in inventory_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Inventory item not found'}
                }
            
            inventory_item = inventory_response['Item']
            
            # Check if auto-reorder is enabled
            if not inventory_item.get('auto_reorder', False):
                logger.info(f"Auto-reorder disabled for item {item_id}")
                return {
                    'statusCode': 200,
                    'body': {'message': 'Auto-reorder disabled for this item'}
                }
            
            # Calculate optimal order quantity
            order_details = self._calculate_optimal_order(inventory_item, urgency)
            
            if not order_details:
                return {
                    'statusCode': 400,
                    'body': {'error': 'Unable to calculate optimal order quantity'}
                }
            
            # Select best supplier
            best_supplier = self._select_optimal_supplier(
                item_id, order_details['quantity'], supplier_id
            )
            
            if not best_supplier:
                return {
                    'statusCode': 400,
                    'body': {'error': 'No suitable supplier found'}
                }
            
            # Create automated purchase order
            po_result = self._create_automated_purchase_order(
                inventory_item, order_details, best_supplier, urgency
            )
            
            if po_result['success']:
                # Update inventory reorder status
                inventory_table.update_item(
                    Key={'item_id': item_id, 'location_id': location_id},
                    UpdateExpression='SET reorder_status = :status, last_reorder_date = :date',
                    ExpressionAttributeValues={
                        ':status': 'ordered',
                        ':date': datetime.utcnow().isoformat()
                    }
                )
                
                # Send notification
                self._send_reorder_notification(po_result['po_data'], urgency)
                
                return {
                    'statusCode': 200,
                    'body': {
                        'message': 'Automated reorder completed successfully',
                        'po_id': po_result['po_data']['po_id'],
                        'supplier': best_supplier['name'],
                        'quantity': order_details['quantity'],
                        'estimated_cost': order_details['estimated_cost']
                    }
                }
            else:
                return {
                    'statusCode': 500,
                    'body': {'error': po_result['error']}
                }
                
        except Exception as e:
            logger.error(f"Error processing reorder event: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to process automated reorder'}
            }
    
    def batch_reorder_analysis(self) -> Dict:
        """Analyze all items and trigger reorders as needed"""
        try:
            # Get all items with auto-reorder enabled
            response = inventory_table.scan(
                FilterExpression='auto_reorder = :enabled AND reorder_status <> :ordered',
                ExpressionAttributeValues={
                    ':enabled': True,
                    ':ordered': 'ordered'
                }
            )
            
            items = response.get('Items', [])
            
            reorders_triggered = 0
            reorders_failed = 0
            
            for item in items:
                try:
                    # Check if reorder is needed
                    if self._needs_reorder(item):
                        # Trigger reorder event
                        event_detail = {
                            'item_id': item['item_id'],
                            'location_id': item['location_id'],
                            'supplier_id': item.get('supplier_id'),
                            'urgency': self._calculate_urgency(item)
                        }
                        
                        # Process reorder
                        result = self.process_reorder_event(event_detail)
                        
                        if result['statusCode'] == 200:
                            reorders_triggered += 1
                        else:
                            reorders_failed += 1
                            logger.warning(f"Failed to reorder item {item['item_id']}: {result.get('body', {}).get('error')}")
                            
                except Exception as e:
                    reorders_failed += 1
                    logger.error(f"Error processing item {item.get('item_id', 'unknown')}: {str(e)}")
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Batch reorder analysis completed',
                    'items_analyzed': len(items),
                    'reorders_triggered': reorders_triggered,
                    'reorders_failed': reorders_failed
                }
            }
            
        except Exception as e:
            logger.error(f"Error in batch reorder analysis: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to complete batch reorder analysis'}
            }
    
    def _calculate_optimal_order(self, inventory_item: Dict, urgency: str) -> Optional[Dict]:
        """Calculate optimal order quantity using ML forecasts and business rules"""
        try:
            item_id = inventory_item['item_id']
            current_stock = inventory_item.get('current_stock', 0)
            reorder_point = inventory_item.get('reorder_point', 0)
            reorder_quantity = inventory_item.get('reorder_quantity', 0)
            safety_stock = inventory_item.get('safety_stock', 0)
            
            # Get demand forecast
            forecast = self._get_demand_forecast(item_id)
            
            if forecast:
                # Use ML-based calculation
                predicted_demand_30d = sum(forecast.get('predictions', []))
                lead_time_days = inventory_item.get('lead_time_days', 7)
                
                # Calculate lead time demand
                daily_demand = predicted_demand_30d / 30
                lead_time_demand = daily_demand * lead_time_days
                
                # Calculate optimal order quantity
                # EOQ-inspired formula with ML adjustments
                optimal_quantity = max(
                    reorder_quantity or 0,
                    int((lead_time_demand + safety_stock) * self.safety_factor)
                )
                
                # Adjust for urgency
                if urgency == 'high':
                    optimal_quantity = int(optimal_quantity * 1.5)
                elif urgency == 'critical':
                    optimal_quantity = int(optimal_quantity * 2.0)
                
            else:
                # Fallback to traditional reorder quantity
                optimal_quantity = reorder_quantity or max(50, reorder_point)
            
            # Calculate estimated cost
            unit_cost = inventory_item.get('unit_cost', 0)
            estimated_cost = optimal_quantity * unit_cost
            
            # Check against maximum order value
            if estimated_cost > self.max_order_value:
                # Reduce quantity to fit budget
                optimal_quantity = int(self.max_order_value / unit_cost) if unit_cost > 0 else optimal_quantity
                estimated_cost = optimal_quantity * unit_cost
            
            return {
                'quantity': optimal_quantity,
                'estimated_cost': estimated_cost,
                'forecast_based': forecast is not None,
                'urgency_adjusted': urgency in ['high', 'critical']
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimal order: {str(e)}")
            return None
    
    def _get_demand_forecast(self, item_id: str) -> Optional[Dict]:
        """Get latest demand forecast for item"""
        try:
            # Get most recent forecast
            response = forecasts_table.query(
                KeyConditionExpression='item_id = :item_id',
                ExpressionAttributeValues={':item_id': item_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                forecast = items[0]
                # Check if forecast is recent (within 7 days)
                forecast_date = datetime.fromisoformat(forecast['forecast_date'].replace('Z', '+00:00'))
                if (datetime.utcnow().replace(tzinfo=forecast_date.tzinfo) - forecast_date).days <= 7:
                    return forecast
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting demand forecast: {str(e)}")
            return None
    
    def _select_optimal_supplier(self, item_id: str, quantity: int, preferred_supplier_id: Optional[str] = None) -> Optional[Dict]:
        """Select the best supplier based on performance, cost, and availability"""
        try:
            # If preferred supplier specified, try that first
            if preferred_supplier_id:
                supplier_response = suppliers_table.get_item(
                    Key={'supplier_id': preferred_supplier_id}
                )
                
                if 'Item' in supplier_response:
                    supplier = supplier_response['Item']
                    if supplier.get('status') == 'active' and self._supplier_can_fulfill(supplier, item_id, quantity):
                        return supplier
            
            # Get all active suppliers that can supply this item
            response = suppliers_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='status = :status',
                ExpressionAttributeValues={':status': 'active'}
            )
            
            suppliers = response.get('Items', [])
            
            # Filter suppliers that can fulfill this item
            eligible_suppliers = []
            for supplier in suppliers:
                if self._supplier_can_fulfill(supplier, item_id, quantity):
                    # Calculate supplier score
                    score = self._calculate_supplier_score(supplier, quantity)
                    eligible_suppliers.append({
                        **supplier,
                        'selection_score': score
                    })
            
            if not eligible_suppliers:
                return None
            
            # Sort by score (highest first)
            eligible_suppliers.sort(key=lambda x: x['selection_score'], reverse=True)
            
            return eligible_suppliers[0]
            
        except Exception as e:
            logger.error(f"Error selecting optimal supplier: {str(e)}")
            return None
    
    def _supplier_can_fulfill(self, supplier: Dict, item_id: str, quantity: int) -> bool:
        """Check if supplier can fulfill the order"""
        try:
            # Check minimum order value
            min_order_value = supplier.get('minimum_order_value', 0)
            unit_cost = 10  # Would get from item-supplier mapping in production
            order_value = quantity * unit_cost
            
            if order_value < min_order_value:
                return False
            
            # Check supplier capabilities (simplified)
            capabilities = supplier.get('capabilities', [])
            if capabilities and 'water_quality_sensors' not in capabilities:
                return False
            
            # Check performance threshold
            performance_score = supplier.get('performance_score', 0)
            if performance_score < 70:  # Minimum acceptable performance
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking supplier fulfillment: {str(e)}")
            return False
    
    def _calculate_supplier_score(self, supplier: Dict, quantity: int) -> float:
        """Calculate supplier selection score"""
        try:
            # Performance score (40% weight)
            performance_score = supplier.get('performance_score', 0) * 0.4
            
            # Lead time score (30% weight) - shorter is better
            lead_time = supplier.get('lead_time_days', 14)
            lead_time_score = max(0, (14 - lead_time) / 14 * 100) * 0.3
            
            # Cost score (20% weight) - would use actual pricing in production
            cost_score = 80 * 0.2  # Placeholder
            
            # Reliability score (10% weight)
            on_time_rate = supplier.get('performance_metrics', {}).get('on_time_delivery_rate', 85)
            reliability_score = on_time_rate * 0.1
            
            total_score = performance_score + lead_time_score + cost_score + reliability_score
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating supplier score: {str(e)}")
            return 0.0
    
    def _create_automated_purchase_order(self, inventory_item: Dict, order_details: Dict, supplier: Dict, urgency: str) -> Dict:
        """Create automated purchase order"""
        try:
            po_id = f"AUTO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Calculate delivery date
            lead_time_days = supplier.get('lead_time_days', 7)
            if urgency == 'critical':
                lead_time_days = max(1, lead_time_days // 2)  # Rush order
            
            expected_delivery = (datetime.utcnow() + timedelta(days=lead_time_days)).isoformat()
            
            # Create PO data
            po_data = {
                'po_id': po_id,
                'supplier_id': supplier['supplier_id'],
                'items': [{
                    'item_id': inventory_item['item_id'],
                    'name': inventory_item['name'],
                    'quantity': order_details['quantity'],
                    'unit_price': inventory_item.get('unit_cost', 0),
                    'total_price': order_details['estimated_cost'],
                    'location_id': inventory_item['location_id']
                }],
                'total_amount': str(order_details['estimated_cost']),
                'currency': 'USD',
                'status': 'pending',
                'approval_status': 'auto_approved' if order_details['estimated_cost'] <= self.max_order_value else 'pending_approval',
                'created_date': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'expected_delivery': expected_delivery,
                'created_by': 'automated_system',
                'order_type': 'automated_restock',
                'urgency': urgency,
                'ml_forecast_used': order_details.get('forecast_based', False),
                'special_instructions': f"Automated restock order - Urgency: {urgency}"
            }
            
            # Store the purchase order
            purchase_orders_table.put_item(Item=po_data)
            
            return {
                'success': True,
                'po_data': po_data
            }
            
        except Exception as e:
            logger.error(f"Error creating automated purchase order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _needs_reorder(self, inventory_item: Dict) -> bool:
        """Check if item needs reordering"""
        try:
            current_stock = inventory_item.get('current_stock', 0)
            reorder_point = inventory_item.get('reorder_point', 0)
            
            # Check if below reorder point
            if current_stock <= reorder_point:
                return True
            
            # Check if forecast indicates upcoming shortage
            forecast = self._get_demand_forecast(inventory_item['item_id'])
            if forecast:
                predicted_demand_7d = sum(forecast.get('predictions', [])[:7])
                if current_stock <= predicted_demand_7d:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking reorder need: {str(e)}")
            return False
    
    def _calculate_urgency(self, inventory_item: Dict) -> str:
        """Calculate urgency level for reorder"""
        try:
            current_stock = inventory_item.get('current_stock', 0)
            safety_stock = inventory_item.get('safety_stock', 0)
            
            if current_stock == 0:
                return 'critical'
            elif current_stock <= safety_stock:
                return 'high'
            else:
                return 'medium'
                
        except Exception as e:
            logger.error(f"Error calculating urgency: {str(e)}")
            return 'medium'
    
    def _send_reorder_notification(self, po_data: Dict, urgency: str):
        """Send notification about automated reorder"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'automated_reorder',
                'po_id': po_data['po_id'],
                'supplier_id': po_data['supplier_id'],
                'total_amount': po_data['total_amount'],
                'urgency': urgency,
                'items_count': len(po_data['items']),
                'approval_status': po_data['approval_status'],
                'expected_delivery': po_data['expected_delivery'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            subject = f"Automated Reorder Created: {po_data['po_id']}"
            if urgency == 'critical':
                subject = f"🚨 URGENT - {subject}"
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=subject
            )
            
        except Exception as e:
            logger.error(f"Error sending reorder notification: {str(e)}")

def lambda_handler(event, context):
    """Main Lambda handler for automated restocking"""
    try:
        # Check if this is an EventBridge event
        if 'source' in event and event['source'] == 'aquachain.inventory':
            # Process reorder event
            restocking_engine = AutomatedRestockingEngine()
            return restocking_engine.process_reorder_event(event['detail'])
        
        # Check if this is a scheduled batch analysis
        elif 'source' in event and event['source'] == 'aws.events':
            # Batch reorder analysis
            restocking_engine = AutomatedRestockingEngine()
            return restocking_engine.batch_reorder_analysis()
        
        # HTTP API request
        else:
            http_method = event.get('httpMethod', '')
            path = event.get('path', '')
            
            # Parse request body
            body = {}
            if event.get('body'):
                body = json.loads(event['body'])
            
            restocking_engine = AutomatedRestockingEngine()
            
            if http_method == 'POST' and path == '/api/restocking/trigger':
                return restocking_engine.process_reorder_event(body)
                
            elif http_method == 'POST' and path == '/api/restocking/batch-analysis':
                return restocking_engine.batch_reorder_analysis()
                
            else:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Endpoint not found'}
                }
            
    except Exception as e:
        logger.error(f"Unhandled error in automated restocking handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': 'Internal server error'}
        }