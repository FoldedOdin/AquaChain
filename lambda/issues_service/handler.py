"""
Issues Service Lambda Handler
Handles issue reports from consumers, stores in DynamoDB, and notifies admins
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# AWS Clients
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

# Environment variables
ISSUES_TABLE_NAME = os.environ.get('ISSUES_TABLE_NAME', 'aquachain-issues')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@aquachain.io')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@aquachain.io')

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,GET,OPTIONS'
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for issue submissions
    """
    try:
        # Handle OPTIONS request for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Handle POST request (submit issue)
        if event.get('httpMethod') == 'POST':
            return handle_submit_issue(event)
        
        # Handle GET request (get issues - admin only)
        if event.get('httpMethod') == 'GET':
            return handle_get_issues(event)
        
        return {
            'statusCode': 405,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Method not allowed'})
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }


def handle_submit_issue(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle issue submission"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        validation_error = validate_issue_form(body)
        if validation_error:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': validation_error})
            }
        
        # Extract user info from JWT (simplified)
        user_id = extract_user_id(event)
        
        # Create issue record
        issue_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        issue_data = {
            'issue_id': issue_id,
            'user_id': user_id or 'anonymous',
            'type': body['type'],
            'title': body['title'],
            'description': body['description'],
            'priority': body.get('priority', 'medium'),
            'device_id': body.get('deviceId'),
            'status': 'open',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Store in DynamoDB
        table = dynamodb.Table(ISSUES_TABLE_NAME)
        table.put_item(Item=issue_data)
        
        # Send email notification to admin
        send_admin_notification(issue_data)
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'issue_id': issue_id,
                'message': 'Issue submitted successfully'
            })
        }
        
    except Exception as e:
        print(f"Error submitting issue: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Failed to submit issue'})
        }


def validate_issue_form(data: Dict[str, Any]) -> Optional[str]:
    """Validate issue form data"""
    required_fields = ['type', 'title', 'description']
    
    for field in required_fields:
        if not data.get(field, '').strip():
            return f'Missing required field: {field}'
    
    # Validate issue type
    valid_types = ['bug', 'feature', 'iot', 'billing', 'other']
    if data['type'] not in valid_types:
        return f'Invalid issue type. Must be one of: {", ".join(valid_types)}'
    
    # Validate priority
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if data.get('priority') and data['priority'] not in valid_priorities:
        return f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'
    
    return None


def extract_user_id(event: Dict[str, Any]) -> Optional[str]:
    """Extract user ID from JWT token (simplified)"""
    try:
        # In a real implementation, you'd decode the JWT token
        # For now, return a placeholder
        auth_header = event.get('headers', {}).get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return 'user-from-jwt'  # Placeholder
        return None
    except:
        return None


def send_admin_notification(issue_data: Dict[str, Any]) -> None:
    """Send email notification to admin about new issue"""
    try:
        subject = f"New Issue Report: {issue_data['title']}"
        
        body = f"""
        A new issue has been reported in AquaChain:
        
        Issue ID: {issue_data['issue_id']}
        Type: {issue_data['type']}
        Priority: {issue_data['priority']}
        Title: {issue_data['title']}
        Description: {issue_data['description']}
        Device ID: {issue_data.get('device_id', 'N/A')}
        User ID: {issue_data['user_id']}
        Created: {issue_data['created_at']}
        
        Please review and respond to this issue promptly.
        """
        
        ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [ADMIN_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        
        print(f"Admin notification sent for issue {issue_data['issue_id']}")
        
    except Exception as e:
        print(f"Failed to send admin notification: {str(e)}")
        # Don't fail the whole request if email fails


def handle_get_issues(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle getting issues (admin only)"""
    try:
        # TODO: Add admin authentication check
        
        table = dynamodb.Table(ISSUES_TABLE_NAME)
        response = table.scan()
        
        issues = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'issues': issues
            })
        }
        
    except Exception as e:
        print(f"Error getting issues: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Failed to get issues'})
        }