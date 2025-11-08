"""
Lambda handler for GDPR data deletion requests.

This handler processes data deletion requests with a 30-day processing window,
tracks the request status, and stores deletion summaries for compliance.
"""

import json
import os
import uuid
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

import boto3

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from error_handler import handle_errors
from errors import ValidationError, AuthorizationError
from structured_logger import StructuredLogger
from data_deletion_service import DataDeletionService

logger = StructuredLogger(__name__)


@handle_errors
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for GDPR data deletion requests.
    
    This handler creates a deletion request with a 30-day processing window.
    The actual deletion is performed by a scheduled Lambda or can be triggered
    manually after the waiting period.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with request status
    """
    logger.log(
        'info',
        'Processing GDPR deletion request',
        service='gdpr_deletion_handler',
        request_id=context.request_id
    )
    
    # Parse request body
    body = json.loads(event.get('body', '{}'))
    user_id = body.get('user_id')
    user_email = body.get('email')
    immediate = body.get('immediate', False)  # For testing or admin override
    
    # Validate request
    if not user_id:
        raise ValidationError(
            'user_id is required',
            'MISSING_USER_ID'
        )
    
    # Verify authorization - user can only delete their own data
    # In production, extract user_id from JWT token
    requesting_user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    if requesting_user_id and requesting_user_id != user_id:
        raise AuthorizationError(
            'You can only delete your own data',
            'UNAUTHORIZED_DELETION',
            {'requesting_user': requesting_user_id, 'target_user': user_id}
        )
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Calculate processing date (30 days from now, unless immediate)
    created_at = datetime.utcnow()
    if immediate:
        scheduled_deletion_date = created_at
        status = 'processing'
    else:
        scheduled_deletion_date = created_at + timedelta(days=30)
        status = 'pending'
    
    # Create GDPR request record
    dynamodb = boto3.resource('dynamodb')
    gdpr_requests_table = dynamodb.Table(
        os.environ.get('GDPR_REQUESTS_TABLE', 'aquachain-gdpr-requests-dev')
    )
    
    request_record = {
        'request_id': request_id,
        'user_id': user_id,
        'request_type': 'deletion',
        'status': status,
        'created_at': created_at.isoformat(),
        'updated_at': created_at.isoformat(),
        'scheduled_deletion_date': scheduled_deletion_date.isoformat(),
        'user_email': user_email,
        'immediate': immediate
    }
    
    gdpr_requests_table.put_item(Item=request_record)
    
    logger.log(
        'info',
        'Created GDPR deletion request record',
        service='gdpr_deletion_handler',
        request_id=request_id,
        user_id=user_id,
        scheduled_deletion_date=scheduled_deletion_date.isoformat(),
        immediate=immediate
    )
    
    # If immediate deletion requested, process now
    if immediate:
        try:
            deletion_service = DataDeletionService()
            deletion_summary = deletion_service.delete_user_data(
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
                UpdateExpression='SET #status = :status, updated_at = :updated, deletion_summary = :summary, completed_at = :completed',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':updated': datetime.utcnow().isoformat(),
                    ':summary': deletion_summary,
                    ':completed': datetime.utcnow().isoformat()
                }
            )
            
            logger.log(
                'info',
                'GDPR deletion completed immediately',
                service='gdpr_deletion_handler',
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
                    'message': 'Your account and data have been permanently deleted',
                    'deletion_summary': deletion_summary
                }, default=str)
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
                f'GDPR deletion failed: {str(e)}',
                service='gdpr_deletion_handler',
                request_id=request_id,
                user_id=user_id,
                error=str(e)
            )
            
            raise
    
    # Return pending status for scheduled deletion
    return {
        'statusCode': 202,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'request_id': request_id,
            'status': 'pending',
            'message': 'Your deletion request has been received',
            'scheduled_deletion_date': scheduled_deletion_date.isoformat(),
            'days_until_deletion': 30,
            'cancellation_info': 'You can cancel this request within 30 days by contacting support'
        })
    }


@handle_errors
def process_scheduled_deletions(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process scheduled deletion requests that have reached their deletion date.
    
    This handler is triggered by EventBridge on a daily schedule to check for
    pending deletion requests that are ready to be processed.
    
    Args:
        event: EventBridge event
        context: Lambda context object
        
    Returns:
        Summary of processed deletions
    """
    logger.log(
        'info',
        'Processing scheduled GDPR deletions',
        service='gdpr_deletion_handler'
    )
    
    dynamodb = boto3.resource('dynamodb')
    gdpr_requests_table = dynamodb.Table(
        os.environ.get('GDPR_REQUESTS_TABLE', 'aquachain-gdpr-requests-dev')
    )
    
    # Query pending deletion requests
    current_date = datetime.utcnow().isoformat()
    
    response = gdpr_requests_table.query(
        IndexName='status-created_at-index',
        KeyConditionExpression='#status = :status',
        FilterExpression='scheduled_deletion_date <= :current_date',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':status': 'pending',
            ':current_date': current_date
        }
    )
    
    pending_deletions = response.get('Items', [])
    
    logger.log(
        'info',
        f'Found {len(pending_deletions)} pending deletions to process',
        service='gdpr_deletion_handler',
        count=len(pending_deletions)
    )
    
    processed = []
    failed = []
    
    deletion_service = DataDeletionService()
    
    for request in pending_deletions:
        request_id = request['request_id']
        user_id = request['user_id']
        user_email = request.get('user_email')
        created_at = request['created_at']
        
        try:
            # Update status to processing
            gdpr_requests_table.update_item(
                Key={
                    'request_id': request_id,
                    'created_at': created_at
                },
                UpdateExpression='SET #status = :status, updated_at = :updated',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'processing',
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            
            # Perform deletion
            deletion_summary = deletion_service.delete_user_data(
                user_id=user_id,
                request_id=request_id,
                user_email=user_email
            )
            
            # Update status to completed
            gdpr_requests_table.update_item(
                Key={
                    'request_id': request_id,
                    'created_at': created_at
                },
                UpdateExpression='SET #status = :status, updated_at = :updated, deletion_summary = :summary, completed_at = :completed',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':updated': datetime.utcnow().isoformat(),
                    ':summary': deletion_summary,
                    ':completed': datetime.utcnow().isoformat()
                }
            )
            
            processed.append({
                'request_id': request_id,
                'user_id': user_id,
                'status': 'completed'
            })
            
            logger.log(
                'info',
                'Scheduled deletion completed',
                service='gdpr_deletion_handler',
                request_id=request_id,
                user_id=user_id
            )
            
        except Exception as e:
            # Update status to failed
            gdpr_requests_table.update_item(
                Key={
                    'request_id': request_id,
                    'created_at': created_at
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
            
            failed.append({
                'request_id': request_id,
                'user_id': user_id,
                'error': str(e)
            })
            
            logger.log(
                'error',
                f'Scheduled deletion failed: {str(e)}',
                service='gdpr_deletion_handler',
                request_id=request_id,
                user_id=user_id,
                error=str(e)
            )
    
    summary = {
        'processed_count': len(processed),
        'failed_count': len(failed),
        'processed': processed,
        'failed': failed
    }
    
    logger.log(
        'info',
        'Scheduled deletions processing complete',
        service='gdpr_deletion_handler',
        summary=summary
    )
    
    return summary


@handle_errors
def cancel_deletion_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cancel a pending deletion request.
    
    Args:
        event: API Gateway event containing request_id
        context: Lambda context object
        
    Returns:
        API Gateway response with cancellation status
    """
    request_id = event.get('pathParameters', {}).get('request_id')
    
    if not request_id:
        raise ValidationError(
            'request_id is required',
            'MISSING_REQUEST_ID'
        )
    
    # Verify authorization
    requesting_user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    # Query GDPR requests table
    dynamodb = boto3.resource('dynamodb')
    gdpr_requests_table = dynamodb.Table(
        os.environ.get('GDPR_REQUESTS_TABLE', 'aquachain-gdpr-requests-dev')
    )
    
    response = gdpr_requests_table.query(
        KeyConditionExpression='request_id = :rid',
        ExpressionAttributeValues={
            ':rid': request_id
        }
    )
    
    items = response.get('Items', [])
    
    if not items:
        raise ValidationError(
            'Deletion request not found',
            'REQUEST_NOT_FOUND',
            {'request_id': request_id}
        )
    
    request_data = items[0]
    
    # Verify authorization
    if requesting_user_id and requesting_user_id != request_data.get('user_id'):
        raise AuthorizationError(
            'You can only cancel your own deletion requests',
            'UNAUTHORIZED_ACCESS'
        )
    
    # Check if request can be cancelled
    if request_data['status'] != 'pending':
        raise ValidationError(
            f"Cannot cancel request with status '{request_data['status']}'",
            'INVALID_STATUS',
            {'current_status': request_data['status']}
        )
    
    # Update status to cancelled
    gdpr_requests_table.update_item(
        Key={
            'request_id': request_id,
            'created_at': request_data['created_at']
        },
        UpdateExpression='SET #status = :status, updated_at = :updated, cancelled_at = :cancelled',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':status': 'cancelled',
            ':updated': datetime.utcnow().isoformat(),
            ':cancelled': datetime.utcnow().isoformat()
        }
    )
    
    logger.log(
        'info',
        'Deletion request cancelled',
        service='gdpr_deletion_handler',
        request_id=request_id,
        user_id=request_data['user_id']
    )
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'request_id': request_id,
            'status': 'cancelled',
            'message': 'Your deletion request has been cancelled'
        })
    }


@handle_errors
def get_deletion_status(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get the status of a GDPR deletion request.
    
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
    
    response = gdpr_requests_table.query(
        KeyConditionExpression='request_id = :rid',
        ExpressionAttributeValues={
            ':rid': request_id
        }
    )
    
    items = response.get('Items', [])
    
    if not items:
        raise ValidationError(
            'Deletion request not found',
            'REQUEST_NOT_FOUND',
            {'request_id': request_id}
        )
    
    request_data = items[0]
    
    # Verify authorization
    requesting_user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    if requesting_user_id and requesting_user_id != request_data.get('user_id'):
        raise AuthorizationError(
            'You can only view your own deletion requests',
            'UNAUTHORIZED_ACCESS'
        )
    
    # Calculate days remaining if pending
    days_remaining = None
    if request_data['status'] == 'pending':
        scheduled_date = datetime.fromisoformat(request_data['scheduled_deletion_date'])
        current_date = datetime.utcnow()
        days_remaining = max(0, (scheduled_date - current_date).days)
    
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
            'scheduled_deletion_date': request_data.get('scheduled_deletion_date'),
            'days_remaining': days_remaining,
            'completed_at': request_data.get('completed_at'),
            'cancelled_at': request_data.get('cancelled_at'),
            'deletion_summary': request_data.get('deletion_summary'),
            'error_message': request_data.get('error_message')
        }, default=str)
    }


@handle_errors
def list_user_deletions(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List all deletion requests for a user.
    
    Args:
        event: API Gateway event
        context: Lambda context object
        
    Returns:
        API Gateway response with list of deletion requests
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
    
    deletions = []
    for item in response.get('Items', []):
        if item.get('request_type') == 'deletion':
            # Calculate days remaining if pending
            days_remaining = None
            if item['status'] == 'pending':
                scheduled_date = datetime.fromisoformat(item['scheduled_deletion_date'])
                current_date = datetime.utcnow()
                days_remaining = max(0, (scheduled_date - current_date).days)
            
            deletions.append({
                'request_id': item['request_id'],
                'status': item['status'],
                'created_at': item['created_at'],
                'scheduled_deletion_date': item.get('scheduled_deletion_date'),
                'days_remaining': days_remaining,
                'completed_at': item.get('completed_at'),
                'cancelled_at': item.get('cancelled_at')
            })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'deletions': deletions,
            'count': len(deletions)
        }, default=str)
    }
