"""
Lambda function to handle manual admin interventions on shipments

This function logs admin actions such as:
- Address changes
- Manual cancellations
- Status overrides
- Manual tracking updates

Requirements: 15.3
"""
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional

from audit_trail import create_admin_action_log, create_timeline_entry

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Environment variables
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def handler(event, context):
    """
    Handle admin intervention on shipment
    
    Input:
    {
      "shipment_id": "ship_xxx",
      "action_type": "ADDRESS_CHANGED" | "CANCELLED" | "STATUS_OVERRIDE",
      "details": {
        "new_address": "...",  // for ADDRESS_CHANGED
        "reason": "...",       // for CANCELLED
        "new_status": "..."    // for STATUS_OVERRIDE
      }
    }
    
    Output:
    {
      "success": true,
      "message": "Admin action logged successfully"
    }
    """
    try:
        # Parse request body
        body = parse_request_body(event)
        
        # Validate required fields
        if 'shipment_id' not in body or 'action_type' not in body:
            return error_response(400, 'Missing required fields: shipment_id, action_type')
        
        shipment_id = body['shipment_id']
        action_type = body['action_type']
        details = body.get('details', {})
        
        # Extract user ID from request context
        user_id = extract_user_id(event)
        
        print(f"INFO: Processing admin intervention: {action_type} for {shipment_id} by {user_id}")
        
        # Route to appropriate handler
        if action_type == 'ADDRESS_CHANGED':
            result = handle_address_change(shipment_id, user_id, details)
        elif action_type == 'CANCELLED':
            result = handle_cancellation(shipment_id, user_id, details)
        elif action_type == 'STATUS_OVERRIDE':
            result = handle_status_override(shipment_id, user_id, details)
        else:
            return error_response(400, f'Unknown action type: {action_type}')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': result['message']
            })
        }
        
    except Exception as e:
        print(f"ERROR: Admin intervention failed: {str(e)}")
        return error_response(500, f'Internal server error: {str(e)}')


def parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body from API Gateway event"""
    if 'body' in event:
        if isinstance(event['body'], str):
            return json.loads(event['body'])
        else:
            return event['body']
    else:
        return event


def extract_user_id(event: Dict[str, Any]) -> str:
    """Extract user ID from request context"""
    try:
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub', 'system')
    except Exception:
        return 'system'


def handle_address_change(shipment_id: str, user_id: str, details: Dict) -> Dict:
    """
    Handle address change intervention
    
    Requirements: 15.3
    """
    new_address = details.get('new_address')
    reason = details.get('reason', 'Address correction requested')
    
    if not new_address:
        raise ValueError('new_address is required for ADDRESS_CHANGED action')
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # Create admin action log
    admin_action = create_admin_action_log(
        action_type='ADDRESS_CHANGED',
        user_id=user_id,
        details={
            'new_address': new_address,
            'reason': reason,
            'changed_at': timestamp
        }
    )
    
    # Create timeline entry for address change
    timeline_entry = create_timeline_entry(
        status='address_changed',
        timestamp=timestamp,
        location='Admin Portal',
        description=f'Delivery address updated by admin: {reason}'
    )
    
    # Update shipment in DynamoDB
    shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
    shipments_table.update_item(
        Key={'shipment_id': shipment_id},
        UpdateExpression='SET destination.address = :addr, updated_at = :time, '
                        'admin_actions = list_append(if_not_exists(admin_actions, :empty), :action), '
                        'timeline = list_append(if_not_exists(timeline, :empty), :timeline)',
        ExpressionAttributeValues={
            ':addr': new_address,
            ':time': timestamp,
            ':action': [admin_action],
            ':timeline': [timeline_entry],
            ':empty': []
        }
    )
    
    print(f"INFO: Address changed for {shipment_id} by {user_id}")
    
    # Send notification
    if SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Shipment Address Updated',
                Message=json.dumps({
                    'eventType': 'ADDRESS_CHANGED',
                    'shipment_id': shipment_id,
                    'user_id': user_id,
                    'new_address': new_address,
                    'reason': reason
                })
            )
        except Exception as e:
            print(f"WARNING: Failed to send notification: {str(e)}")
    
    return {'message': f'Address updated successfully for shipment {shipment_id}'}


def handle_cancellation(shipment_id: str, user_id: str, details: Dict) -> Dict:
    """
    Handle shipment cancellation intervention
    
    Requirements: 15.3
    """
    reason = details.get('reason', 'Cancelled by admin')
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # Create admin action log
    admin_action = create_admin_action_log(
        action_type='CANCELLED',
        user_id=user_id,
        details={
            'reason': reason,
            'cancelled_at': timestamp
        }
    )
    
    # Create timeline entry for cancellation
    timeline_entry = create_timeline_entry(
        status='cancelled',
        timestamp=timestamp,
        location='Admin Portal',
        description=f'Shipment cancelled by admin: {reason}'
    )
    
    # Update shipment in DynamoDB
    shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
    shipments_table.update_item(
        Key={'shipment_id': shipment_id},
        UpdateExpression='SET internal_status = :status, updated_at = :time, '
                        'admin_actions = list_append(if_not_exists(admin_actions, :empty), :action), '
                        'timeline = list_append(if_not_exists(timeline, :empty), :timeline)',
        ExpressionAttributeValues={
            ':status': 'cancelled',
            ':time': timestamp,
            ':action': [admin_action],
            ':timeline': [timeline_entry],
            ':empty': []
        }
    )
    
    print(f"INFO: Shipment {shipment_id} cancelled by {user_id}")
    
    # Send notification
    if SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Shipment Cancelled',
                Message=json.dumps({
                    'eventType': 'SHIPMENT_CANCELLED',
                    'shipment_id': shipment_id,
                    'user_id': user_id,
                    'reason': reason
                })
            )
        except Exception as e:
            print(f"WARNING: Failed to send notification: {str(e)}")
    
    return {'message': f'Shipment {shipment_id} cancelled successfully'}


def handle_status_override(shipment_id: str, user_id: str, details: Dict) -> Dict:
    """
    Handle manual status override intervention
    
    Requirements: 15.3
    """
    new_status = details.get('new_status')
    reason = details.get('reason', 'Status manually overridden by admin')
    
    if not new_status:
        raise ValueError('new_status is required for STATUS_OVERRIDE action')
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # Create admin action log
    admin_action = create_admin_action_log(
        action_type='STATUS_OVERRIDE',
        user_id=user_id,
        details={
            'new_status': new_status,
            'reason': reason,
            'overridden_at': timestamp
        }
    )
    
    # Create timeline entry for status override
    timeline_entry = create_timeline_entry(
        status=new_status,
        timestamp=timestamp,
        location='Admin Portal',
        description=f'Status manually set to {new_status} by admin: {reason}'
    )
    
    # Update shipment in DynamoDB
    shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
    shipments_table.update_item(
        Key={'shipment_id': shipment_id},
        UpdateExpression='SET internal_status = :status, updated_at = :time, '
                        'admin_actions = list_append(if_not_exists(admin_actions, :empty), :action), '
                        'timeline = list_append(if_not_exists(timeline, :empty), :timeline)',
        ExpressionAttributeValues={
            ':status': new_status,
            ':time': timestamp,
            ':action': [admin_action],
            ':timeline': [timeline_entry],
            ':empty': []
        }
    )
    
    print(f"INFO: Status overridden for {shipment_id} to {new_status} by {user_id}")
    
    # Send notification
    if SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Shipment Status Overridden',
                Message=json.dumps({
                    'eventType': 'STATUS_OVERRIDE',
                    'shipment_id': shipment_id,
                    'user_id': user_id,
                    'new_status': new_status,
                    'reason': reason
                })
            )
        except Exception as e:
            print(f"WARNING: Failed to send notification: {str(e)}")
    
    return {'message': f'Status updated to {new_status} for shipment {shipment_id}'}


def error_response(status_code: int, message: str) -> Dict:
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message
        })
    }
