"""
AquaChain Supplier Management - Handler
Manages supplier relationships, performance tracking, and automated ordering
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import uuid
import logging
import requests
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
secrets_manager = boto3.client('secretsmanager')

# Table references
suppliers_table = dynamodb.Table('AquaChain-Suppliers')
purchase_orders_table = dynamodb.Table('AquaChain-Purchase-Orders')
inventory_table = dynamodb.Table('AquaChain-Inventory-Items')

class SupplierManager:
    """Core supplier management operations"""
    
    def __init__(self):
        self.sns_topic = os.environ.get('SUPPLIER_ALERTS_TOPIC')
        
    def get_suppliers(self, filters: Optional[Dict] = None) -> Dict:
        """Get suppliers with optional filtering"""
        try:
            if filters:
                if 'supplier_type' in filters:
                    response = suppliers_table.query(
                        IndexName='TypeIndex',
                        KeyConditionExpression='supplier_type = :type',
                        ExpressionAttributeValues={':type': filters['supplier_type']},
                        ScanIndexForward=False  # Sort by performance score descending
                    )
                elif 'status' in filters:
                    response = suppliers_table.query(
                        IndexName='StatusIndex',
                        KeyConditionExpression='status = :status',
                        ExpressionAttributeValues={':status': filters['status']}
                    )
                else:
                    response = suppliers_table.scan()
            else:
                response = suppliers_table.scan()
                
            suppliers = response.get('Items', [])
            
            # Enrich with performance metrics
            for supplier in suppliers:
                supplier['performance_metrics'] = self._calculate_performance_metrics(supplier['supplier_id'])
                
            return {
                'statusCode': 200,
                'body': {
                    'suppliers': suppliers,
                    'count': len(suppliers),
                    'active_count': len([s for s in suppliers if s.get('status') == 'active']),
                    'top_performers': [s for s in suppliers if s.get('performance_score', 0) >= 90]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting suppliers: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve suppliers'}
            }
    
    def create_supplier(self, supplier_data: Dict) -> Dict:
        """Create new supplier"""
        try:
            # Generate supplier ID if not provided
            if 'supplier_id' not in supplier_data:
                supplier_data['supplier_id'] = f"SUP-{uuid.uuid4().hex[:8].upper()}"
            
            # Set default values
            now = datetime.utcnow().isoformat()
            supplier_data.update({
                'created_at': now,
                'updated_at': now,
                'status': 'active',
                'performance_score': Decimal('75'),  # Default starting score
                'total_orders': 0,
                'on_time_deliveries': 0,
                'quality_issues': 0
            })
            
            # Validate required fields
            required_fields = ['supplier_id', 'name', 'supplier_type', 'contact_email']
            for field in required_fields:
                if field not in supplier_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Create the supplier
            suppliers_table.put_item(Item=supplier_data)
            
            return {
                'statusCode': 201,
                'body': {
                    'message': 'Supplier created successfully',
                    'supplier': supplier_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating supplier: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create supplier'}
            }
    
    def update_supplier(self, supplier_id: str, updates: Dict) -> Dict:
        """Update supplier information"""
        try:
            # Get current supplier
            current_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in current_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Supplier not found'}
                }
            
            # Prepare update expression
            update_expression = "SET updated_at = :now"
            expression_values = {':now': datetime.utcnow().isoformat()}
            
            # Build update expression dynamically
            for key, value in updates.items():
                if key != 'supplier_id':  # Don't update primary key
                    update_expression += f", {key} = :{key}"
                    expression_values[f":{key}"] = value
            
            # Update the supplier
            response = suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Supplier updated successfully',
                    'supplier': response['Attributes']
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating supplier: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update supplier'}
            }
    
    def create_purchase_order(self, po_data: Dict) -> Dict:
        """Create new purchase order"""
        try:
            # Generate PO ID if not provided
            if 'po_id' not in po_data:
                po_data['po_id'] = f"PO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Validate supplier exists
            supplier_response = suppliers_table.get_item(
                Key={'supplier_id': po_data['supplier_id']}
            )
            
            if 'Item' not in supplier_response:
                return {
                    'statusCode': 400,
                    'body': {'error': 'Invalid supplier ID'}
                }
            
            supplier = supplier_response['Item']
            
            # Set default values
            now = datetime.utcnow().isoformat()
            po_data.update({
                'created_date': now,
                'updated_at': now,
                'status': 'pending',
                'created_by': po_data.get('created_by', 'system'),
                'approval_status': 'pending'
            })
            
            # Calculate expected delivery date
            lead_time_days = supplier.get('lead_time_days', 7)
            expected_delivery = (datetime.utcnow() + timedelta(days=lead_time_days)).isoformat()
            po_data['expected_delivery'] = expected_delivery
            
            # Validate required fields
            required_fields = ['po_id', 'supplier_id', 'items', 'total_amount']
            for field in required_fields:
                if field not in po_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Check if approval is needed
            approval_needed = self._check_approval_needed(po_data)
            if approval_needed:
                po_data['approval_status'] = 'pending_approval'
                self._send_approval_request(po_data)
            else:
                po_data['approval_status'] = 'auto_approved'
                po_data['status'] = 'approved'
                # Send to supplier if auto-approved
                self._send_po_to_supplier(po_data, supplier)
            
            # Create the purchase order
            purchase_orders_table.put_item(Item=po_data)
            
            return {
                'statusCode': 201,
                'body': {
                    'message': 'Purchase order created successfully',
                    'purchase_order': po_data,
                    'approval_needed': approval_needed
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating purchase order: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create purchase order'}
            }
    
    def get_purchase_orders(self, filters: Optional[Dict] = None) -> Dict:
        """Get purchase orders with optional filtering"""
        try:
            if filters:
                if 'supplier_id' in filters:
                    response = purchase_orders_table.query(
                        IndexName='SupplierOrdersIndex',
                        KeyConditionExpression='supplier_id = :sid',
                        ExpressionAttributeValues={':sid': filters['supplier_id']},
                        ScanIndexForward=False  # Most recent first
                    )
                elif 'status' in filters:
                    response = purchase_orders_table.query(
                        IndexName='StatusIndex',
                        KeyConditionExpression='status = :status',
                        ExpressionAttributeValues={':status': filters['status']}
                    )
                else:
                    response = purchase_orders_table.scan()
            else:
                response = purchase_orders_table.scan()
                
            orders = response.get('Items', [])
            
            # Enrich with supplier information
            for order in orders:
                supplier_response = suppliers_table.get_item(
                    Key={'supplier_id': order['supplier_id']}
                )
                if 'Item' in supplier_response:
                    order['supplier_info'] = supplier_response['Item']
                    
            return {
                'statusCode': 200,
                'body': {
                    'purchase_orders': orders,
                    'count': len(orders),
                    'pending_count': len([o for o in orders if o.get('status') == 'pending']),
                    'total_value': sum(float(o.get('total_amount', 0)) for o in orders)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting purchase orders: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve purchase orders'}
            }
    
    def update_purchase_order_status(self, po_id: str, status: str, notes: Optional[str] = None) -> Dict:
        """Update purchase order status"""
        try:
            # Get current PO
            current_response = purchase_orders_table.get_item(Key={'po_id': po_id})
            
            if 'Item' not in current_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Purchase order not found'}
                }
            
            current_po = current_response['Item']
            
            # Prepare update
            update_expression = "SET #status = :status, updated_at = :now"
            expression_values = {
                ':status': status,
                ':now': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            if notes:
                update_expression += ", notes = :notes"
                expression_values[':notes'] = notes
            
            # Add status history
            status_history = current_po.get('status_history', [])
            status_history.append({
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'notes': notes
            })
            update_expression += ", status_history = :history"
            expression_values[':history'] = status_history
            
            # Update the PO
            response = purchase_orders_table.update_item(
                Key={'po_id': po_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            updated_po = response['Attributes']
            
            # Handle status-specific actions
            if status == 'delivered':
                self._handle_delivery_received(updated_po)
            elif status == 'cancelled':
                self._handle_po_cancelled(updated_po)
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Purchase order status updated successfully',
                    'purchase_order': updated_po
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating purchase order status: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update purchase order status'}
            }
    
    def get_supplier_performance(self, supplier_id: str) -> Dict:
        """Get detailed supplier performance metrics"""
        try:
            # Get supplier info
            supplier_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in supplier_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Supplier not found'}
                }
            
            supplier = supplier_response['Item']
            
            # Get performance metrics
            performance_metrics = self._calculate_performance_metrics(supplier_id)
            
            # Get recent orders
            recent_orders_response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id},
                ScanIndexForward=False,
                Limit=10
            )
            
            recent_orders = recent_orders_response.get('Items', [])
            
            return {
                'statusCode': 200,
                'body': {
                    'supplier': supplier,
                    'performance_metrics': performance_metrics,
                    'recent_orders': recent_orders,
                    'recommendations': self._generate_supplier_recommendations(supplier, performance_metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting supplier performance: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve supplier performance'}
            }
    
    def _calculate_performance_metrics(self, supplier_id: str) -> Dict:
        """Calculate comprehensive supplier performance metrics"""
        try:
            # Get all orders for this supplier
            response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            orders = response.get('Items', [])
            
            if not orders:
                return {
                    'total_orders': 0,
                    'on_time_delivery_rate': 0,
                    'quality_score': 0,
                    'average_lead_time': 0,
                    'total_value': 0
                }
            
            # Calculate metrics
            total_orders = len(orders)
            delivered_orders = [o for o in orders if o.get('status') == 'delivered']
            on_time_orders = [o for o in delivered_orders if self._is_delivery_on_time(o)]
            
            on_time_rate = (len(on_time_orders) / len(delivered_orders)) * 100 if delivered_orders else 0
            
            # Calculate average lead time
            lead_times = []
            for order in delivered_orders:
                if 'actual_delivery_date' in order and 'created_date' in order:
                    created = datetime.fromisoformat(order['created_date'].replace('Z', '+00:00'))
                    delivered = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
                    lead_time = (delivered - created).days
                    lead_times.append(lead_time)
            
            avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            
            # Calculate total value
            total_value = sum(float(o.get('total_amount', 0)) for o in orders)
            
            # Quality score (based on returns, defects, etc.)
            quality_issues = sum(1 for o in orders if o.get('quality_issues', 0) > 0)
            quality_score = max(0, 100 - (quality_issues / total_orders * 100)) if total_orders > 0 else 100
            
            return {
                'total_orders': total_orders,
                'on_time_delivery_rate': round(on_time_rate, 2),
                'quality_score': round(quality_score, 2),
                'average_lead_time': round(avg_lead_time, 1),
                'total_value': round(total_value, 2),
                'delivered_orders': len(delivered_orders),
                'pending_orders': len([o for o in orders if o.get('status') in ['pending', 'approved', 'shipped']])
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def _is_delivery_on_time(self, order: Dict) -> bool:
        """Check if delivery was on time"""
        try:
            if 'expected_delivery' not in order or 'actual_delivery_date' not in order:
                return False
                
            expected = datetime.fromisoformat(order['expected_delivery'].replace('Z', '+00:00'))
            actual = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
            
            return actual <= expected
            
        except Exception:
            return False
    
    def _check_approval_needed(self, po_data: Dict) -> bool:
        """Check if purchase order needs approval"""
        total_amount = float(po_data.get('total_amount', 0))
        
        # Approval thresholds
        if total_amount > 25000:
            return True  # Executive approval needed
        elif total_amount > 5000:
            return True  # Manager approval needed
        else:
            return False  # Auto-approve small orders
    
    def _send_approval_request(self, po_data: Dict):
        """Send approval request notification"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'approval_request',
                'po_id': po_data['po_id'],
                'supplier_id': po_data['supplier_id'],
                'total_amount': po_data['total_amount'],
                'items_count': len(po_data.get('items', [])),
                'created_by': po_data.get('created_by', 'system'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Purchase Order Approval Required: {po_data['po_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending approval request: {str(e)}")
    
    def _send_po_to_supplier(self, po_data: Dict, supplier: Dict):
        """Send purchase order to supplier via API or email"""
        try:
            # Check if supplier has API integration
            if supplier.get('api_endpoint'):
                self._send_po_via_api(po_data, supplier)
            else:
                self._send_po_via_email(po_data, supplier)
                
        except Exception as e:
            logger.error(f"Error sending PO to supplier: {str(e)}")
    
    def _send_po_via_api(self, po_data: Dict, supplier: Dict):
        """Send PO via supplier API"""
        try:
            # Get API credentials from Secrets Manager
            secret_name = f"supplier-api-{supplier['supplier_id']}"
            
            try:
                secret_response = secrets_manager.get_secret_value(SecretId=secret_name)
                credentials = json.loads(secret_response['SecretString'])
            except ClientError:
                logger.warning(f"No API credentials found for supplier {supplier['supplier_id']}")
                return
            
            # Prepare API payload
            api_payload = {
                'purchase_order_id': po_data['po_id'],
                'items': po_data['items'],
                'total_amount': po_data['total_amount'],
                'expected_delivery': po_data['expected_delivery'],
                'delivery_address': po_data.get('delivery_address'),
                'special_instructions': po_data.get('special_instructions')
            }
            
            # Send to supplier API
            headers = {
                'Authorization': f"Bearer {credentials.get('api_key')}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                supplier['api_endpoint'],
                json=api_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Update PO with supplier confirmation
                purchase_orders_table.update_item(
                    Key={'po_id': po_data['po_id']},
                    UpdateExpression='SET supplier_confirmation = :conf, status = :status',
                    ExpressionAttributeValues={
                        ':conf': response.json(),
                        ':status': 'confirmed'
                    }
                )
            else:
                logger.error(f"Supplier API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending PO via API: {str(e)}")
    
    def _send_po_via_email(self, po_data: Dict, supplier: Dict):
        """Send PO via email notification"""
        try:
            message = {
                'type': 'purchase_order',
                'po_id': po_data['po_id'],
                'supplier_email': supplier.get('contact_email'),
                'po_data': po_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"New Purchase Order: {po_data['po_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending PO via email: {str(e)}")
    
    def _handle_delivery_received(self, po_data: Dict):
        """Handle actions when delivery is received"""
        try:
            # Update supplier performance
            supplier_id = po_data['supplier_id']
            
            # Check if delivery was on time
            on_time = self._is_delivery_on_time(po_data)
            
            # Update supplier metrics
            suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression='ADD total_orders :one, on_time_deliveries :on_time',
                ExpressionAttributeValues={
                    ':one': 1,
                    ':on_time': 1 if on_time else 0
                }
            )
            
            # Update inventory levels (would integrate with warehouse system)
            self._update_inventory_from_delivery(po_data)
            
        except Exception as e:
            logger.error(f"Error handling delivery received: {str(e)}")
    
    def _handle_po_cancelled(self, po_data: Dict):
        """Handle actions when PO is cancelled"""
        try:
            # Log cancellation reason
            logger.info(f"PO {po_data['po_id']} cancelled: {po_data.get('notes', 'No reason provided')}")
            
            # Notify relevant parties
            if self.sns_topic:
                message = {
                    'type': 'po_cancelled',
                    'po_id': po_data['po_id'],
                    'supplier_id': po_data['supplier_id'],
                    'reason': po_data.get('notes', 'No reason provided'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                sns.publish(
                    TopicArn=self.sns_topic,
                    Message=json.dumps(message),
                    Subject=f"Purchase Order Cancelled: {po_data['po_id']}"
                )
                
        except Exception as e:
            logger.error(f"Error handling PO cancellation: {str(e)}")
    
    def _update_inventory_from_delivery(self, po_data: Dict):
        """Update inventory levels when delivery is received"""
        try:
            for item in po_data.get('items', []):
                item_id = item.get('item_id')
                quantity_received = item.get('quantity_received', item.get('quantity', 0))
                location_id = item.get('location_id', 'MAIN-WAREHOUSE')
                
                if item_id and quantity_received > 0:
                    # Update inventory
                    inventory_table.update_item(
                        Key={'item_id': item_id, 'location_id': location_id},
                        UpdateExpression='ADD current_stock :qty SET last_received = :date, updated_at = :now',
                        ExpressionAttributeValues={
                            ':qty': quantity_received,
                            ':date': datetime.utcnow().isoformat(),
                            ':now': datetime.utcnow().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error updating inventory from delivery: {str(e)}")
    
    def _generate_supplier_recommendations(self, supplier: Dict, metrics: Dict) -> List[str]:
        """Generate recommendations for supplier management"""
        recommendations = []
        
        # Performance-based recommendations
        on_time_rate = metrics.get('on_time_delivery_rate', 0)
        quality_score = metrics.get('quality_score', 0)
        
        if on_time_rate < 85:
            recommendations.append("Consider discussing delivery performance with supplier")
        
        if quality_score < 90:
            recommendations.append("Review quality control processes with supplier")
        
        if metrics.get('total_orders', 0) > 50 and on_time_rate > 95:
            recommendations.append("Consider negotiating volume discounts")
        
        if supplier.get('status') == 'active' and on_time_rate > 90 and quality_score > 95:
            recommendations.append("Excellent supplier - consider preferred vendor status")
        
        return recommendations

def lambda_handler(event, context):
    """Main Lambda handler for supplier management"""
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parse request body
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        
        supplier_manager = SupplierManager()
        
        # Route requests
        if http_method == 'GET' and path == '/api/suppliers':
            return supplier_manager.get_suppliers(query_parameters)
            
        elif http_method == 'POST' and path == '/api/suppliers':
            return supplier_manager.create_supplier(body)
            
        elif http_method == 'PUT' and '/api/suppliers/' in path:
            supplier_id = path_parameters.get('supplier_id')
            return supplier_manager.update_supplier(supplier_id, body)
            
        elif http_method == 'GET' and '/api/suppliers/' in path and '/performance' in path:
            supplier_id = path_parameters.get('supplier_id')
            return supplier_manager.get_supplier_performance(supplier_id)
            
        elif http_method == 'GET' and path == '/api/purchase-orders':
            return supplier_manager.get_purchase_orders(query_parameters)
            
        elif http_method == 'POST' and path == '/api/purchase-orders':
            return supplier_manager.create_purchase_order(body)
            
        elif http_method == 'PUT' and '/api/purchase-orders/' in path and '/status' in path:
            po_id = path_parameters.get('po_id')
            status = body.get('status')
            notes = body.get('notes')
            return supplier_manager.update_purchase_order_status(po_id, status, notes)
            
        else:
            return {
                'statusCode': 404,
                'body': {'error': 'Endpoint not found'}
            }
            
    except Exception as e:
        logger.error(f"Unhandled error in supplier handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': 'Internal server error'}
        }