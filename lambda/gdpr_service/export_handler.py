"""
Lambda handler for GDPR data export requests.

This handler processes data export requests, initiates the export process,
and tracks the request status.
"""

import json
import os
import uuid
import sys
from datetime import datetime
from typing import Dict, Any

import boto3

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from error_handler import handle_errors
from errors import ValidationError, AuthorizationError
from structured_logger import StructuredLogger
from data_export_service import DataExportService

logger = StructuredLogger(__name__)


@handle_errors
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for GDPR data export requests.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with request status
    """
    logger.log(
        'info',
        'Processing GDPR export request',
        service='gdpr_export_handler',
        request_id=context.request_id
    )
    
    # Parse request body
    body = json.loads(event.get('body', '{}'))
    user_id = body.get('user_id')
    user_email = body.get('email')
    
    # Validate request
    if not user_id:
        raise ValidationError(
            'user_id is required',
            'MISSING_USER_ID'
        )
    
    # Verify authorization - user can only export their own data
    # In production, extract user_id from JWT token
    requesting_user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    if requesting_user_id and requesting_user_id != user_id:
        raise AuthorizationError(
            'You can only export your own data',
            'UNAUTHORIZED_EXPORT',
            {'requesting_user': requesting_user_id, 'target_user': user_id}
        )
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Create GDPR request record
    dynamodb = boto3.resource('dynamodb')
    gdpr_requests_table = dynamodb.Table(
        os.environ.get('GDPR_REQUESTS_TABLE', 'aquachain-gdpr-requests-dev')
    )
    
    request_record = {
        'request_id': request_id,
        'user_id': user_id,
        'request_type': 'export',
        'status': 'processing',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'user_email': user_email
    }
    
    gdpr_requests_table.put_item(Item=request_record)
    
    logger.log(
        'info',
        'Created GDPR export request record',
        service='gdpr_export_handler',
        request_id=request_id,
        user_id=user_id
    )
    
    # Initiate export process
    try:
        export_service = DataExportService()
        presigned_url = export_service.export_user_data(
            user_id=user_id,
            request_id=request_id,
            user_email=user_email
        )
        
        # Update request status to completed
        gdpr_requests_table.update_item(
            Key={
                'request_id': request_id,
                'created_at': request_record['created_at']
            },
            UpdateExpression='SET #status = :status, updated_at = :updated, export_url = :url, completed_at = :completed',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'completed',
                ':updated': datetime.utcnow().isoformat(),
                ':url': presigned_url,
                ':completed': datetime.utcnow().isoformat()
            }
        )
        
        logger.log(
            'info',
            'GDPR export completed successfully',
            service='gdpr_export_handler',
            request_id=request_id,
            user_id=user_id
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'request_id': request_id,
                'status': 'completed',
                'message': 'Your data export is ready',
                'download_url': presigned_url,
                'expires_in_days': 7
            })
        }
        
    except Exception as e:
        # Update request status to failed
        gdpr_requests_table.update_item(
            Key={
                'request_id': request_id,
                'created_at': request_record['created_at']
            },
            UpdateExpression='SET #status = :status, updated_at = :updated, error_message = :error',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'failed',
                ':updated': datetime.utcnow().isoformat(),
                ':error': str(e)
            }
        )
        
        logger.log(
            'error',
            f'GDPR export failed: {str(e)}',
            service='gdpr_export_handler',
            request_id=request_id,
            user_id=user_id,
            error=str(e)
        )
        
        raise


@handle_errors
def get_export_status(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get the status of a GDPR export request.
    
    Args:
        event: API Gateway event containing request_id
        context: Lambda context object
        
    Returns:
        API Gateway response with request status
    """
    request_id = event.get('pathParameters', {}).get('request_id')
    
    if not request_id:
        raise ValidationError(
            'request_id is required',
            'MISSING_REQUEST_ID'
        )
    
    # Query GDPR requests table
    dynamodb = boto3.resource('dynamodb')
    gdpr_requests_table = dynamodb.Table(
        os.environ.get('GDPR_REQUESTS_TABLE', 'aquachain-gdpr-requests-dev')
    )
    
    # We need to query by request_id (partition key)
    # Since we don't have the sort key (created_at), we'll scan with filter
    response = gdpr_requests_table.query(
        KeyConditionExpression='request_id = :rid',
        ExpressionAttributeValues={
            ':rid': request_id
        }
    )
    
    items = response.get('Items', [])
    
    if not items:
        raise ValidationError(
            'Export request not found',
            'REQUEST_NOT_FOUND',
            {'request_id': request_id}
        )
    
    request_data = items[0]
    
    # Verify authorization
    requesting_user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    if requesting_user_id and requesting_user_id != request_data.get('user_id'):
        raise AuthorizationError(
            'You can only view your own export requests',
            'UNAUTHORIZED_ACCESS'
        )
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'request_id': request_data['request_id'],
            'status': request_data['status'],
            'created_at': request_data['created_at'],
            'updated_at': request_data.get('updated_at'),
            'completed_at': request_data.get('completed_at'),
            'download_url': request_data.get('export_url'),
            'error_message': request_data.get('error_message')
        }, default=str)
    }


@handle_errors
def list_user_exports(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List all export requests for a user.
    
    Args:
        event: API Gateway event
        context: Lambda context object
        
    Returns:
        API Gateway response with list of export requests
    """
    # Get user_id from JWT token
    user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    if not user_id:
        raise AuthorizationError(
            'User not authenticated',
            'UNAUTHENTICATED'
        )
    
    # Query GDPR requests table by user_id
    dynamodb = boto3.resource('dynamodb')
    gdpr_requests_table = dynamodb.Table(
        os.environ.get('GDPR_REQUESTS_TABLE', 'aquachain-gdpr-requests-dev')
    )
    
    response = gdpr_requests_table.query(
        IndexName='user_id-created_at-index',
        KeyConditionExpression='user_id = :uid',
        ExpressionAttributeValues={
            ':uid': user_id
        },
        ScanIndexForward=False,  # Most recent first
        Limit=50
    )
    
    exports = []
    for item in response.get('Items', []):
        if item.get('request_type') == 'export':
            exports.append({
                'request_id': item['request_id'],
                'status': item['status'],
                'created_at': item['created_at'],
                'completed_at': item.get('completed_at'),
                'download_url': item.get('export_url') if item['status'] == 'completed' else None
            })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'exports': exports,
            'count': len(exports)
        }, default=str)
    }
