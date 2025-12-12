"""
Lambda function to set quote for device orders with auto-approval logic
"""
import boto3
import json
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
sfn = boto3.client('stepfunctions')

ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'DeviceOrders')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
PROVISION_STATE_MACHINE_ARN = os.environ.get('PROVISION_STATE_MACHINE_ARN')
AUTO_APPROVE_THRESHOLD = int(os.environ.get('AUTO_APPROVE_THRESHOLD', '20000'))


def handler(event, context):
    """
    Set quote for an order with auto-approval for standard quotes
    
    Args:
        event: API Gateway event with quote amount
        context: Lambda context
        
    Returns:
        API Gateway response with updated status
    """
    try:
        order_id = event['pathParameters']['id']
        body = json.loads(event['body'])
        quote_amount = int(body['quoteAmount'])
        
        # Get admin ID from Cognito authorizer
        admin_id = event['requestContext']['authorizer']['claims']['sub']
        admin_name = event['requestContext']['authorizer']['claims'].get('name', 'Admin')
        
        # Get current order
        table = dynamodb.Table(ORDERS_TABLE)
        response = table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'Order not found'})
            }
        
        order = response['Item']
        
        # Validate state transition
        if order['status'] != 'PENDING':
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid state transition. Current status: {order["status"]}'
                })
            }
        
        # Determine if auto-approve
        auto_approved = quote_amount < AUTO_APPROVE_THRESHOLD
        new_status = 'QUOTED_APPROVED' if auto_approved else 'QUOTED'
        timestamp = datetime.utcnow().isoformat()
        
        # Update order
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, quoteAmount = :amount, quotedAt = :time, quotedBy = :admin, updatedAt = :updated, auditTrail = list_append(auditTrail, :audit)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':amount': quote_amount,
                ':time': timestamp,
                ':admin': admin_id,
                ':updated': timestamp,
                ':audit': [{
                    'action': 'QUOTE_SET',
                    'by': admin_id,
                    'byName': admin_name,
                    'at': timestamp,
                    'amount': quote_amount,
                    'autoApproved': auto_approved
                }]
            }
        )
        
        # Publish event
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps({
                    'eventType': 'ORDER_QUOTED',
                    'orderId': order_id,
                    'quoteAmount': quote_amount,
                    'autoApproved': auto_approved,
                    'timestamp': timestamp
                }),
                Subject=f'Order Quoted: {order_id}'
            )
        
        # If auto-approved, trigger provisioning workflow
        if auto_approved and PROVISION_STATE_MACHINE_ARN:
            try:
                sfn.start_execution(
                    stateMachineArn=PROVISION_STATE_MACHINE_ARN,
                    name=f"provision-{order_id}-{int(datetime.now().timestamp())}",
                    input=json.dumps({
                        'orderId': order_id,
                        'deviceSKU': order['deviceSKU'],
                        'userId': order['userId']
                    })
                )
                print(f"Triggered provisioning workflow for order {order_id}")
            except Exception as e:
                print(f"Failed to trigger provisioning: {str(e)}")
        
        print(f"Quote set for order {order_id}: ₹{quote_amount} (auto-approved: {auto_approved})")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'status': new_status,
                'quoteAmount': quote_amount,
                'autoApproved': auto_approved
            })
        }
        
    except Exception as e:
        print(f"Error setting quote: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': 'Internal server error'})
        }
