"""
Optimized DynamoDB query functions using GSIs for Phase 4 performance improvements
"""

import boto3
import time
from typing import Dict, List, Optional, Any
from boto3.dynamodb.conditions import Key, Attr
from structured_logger import StructuredLogger

dynamodb = boto3.resource('dynamodb')
logger = StructuredLogger(__name__)

# Performance threshold for query warnings (500ms)
QUERY_PERFORMANCE_THRESHOLD_MS = 500


def query_devices_by_user(
    user_id: str,
    limit: int = 100,
    last_key: Optional[Dict] = None,
    table_name: str = 'aquachain-devices'
) -> Dict[str, Any]:
    """
    Query devices by user using user_id-created_at-index GSI
    
    Args:
        user_id: User ID to query devices for
        limit: Maximum number of items to return
        last_key: Pagination token from previous query
        table_name: DynamoDB table name
        
    Returns:
        Dictionary with items, last_key, and has_more fields
    """
    start_time = time.time()
    table = dynamodb.Table(table_name)
    
    query_params = {
        'IndexName': 'user_id-created_at-index',
        'KeyConditionExpression': Key('user_id').eq(user_id),
        'Limit': limit,
        'ScanIndexForward': False  # Newest first
    }
    
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = table.query(**query_params)
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Log performance metrics
    logger.log('info', 'Query devices by user completed',
        service='dynamodb_queries',
        operation='query_devices_by_user',
        user_id=user_id,
        duration_ms=duration_ms,
        item_count=len(response['Items'])
    )
    
    # Log warning if query exceeds threshold
    if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
        logger.log('warning', f'Query exceeded performance threshold: {duration_ms}ms',
            service='dynamodb_queries',
            operation='query_devices_by_user',
            user_id=user_id,
            duration_ms=duration_ms,
            threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS
        )
    
    return {
        'items': response['Items'],
        'last_key': response.get('LastEvaluatedKey'),
        'has_more': 'LastEvaluatedKey' in response,
        'duration_ms': duration_ms
    }


def query_devices_by_status(
    status: str,
    limit: int = 100,
    last_key: Optional[Dict] = None,
    table_name: str = 'aquachain-devices'
) -> Dict[str, Any]:
    """
    Query devices by status using status-last_seen-index GSI
    
    Args:
        status: Device status (e.g., 'active', 'inactive', 'maintenance')
        limit: Maximum number of items to return
        last_key: Pagination token from previous query
        table_name: DynamoDB table name
        
    Returns:
        Dictionary with items, last_key, and has_more fields
    """
    start_time = time.time()
    table = dynamodb.Table(table_name)
    
    query_params = {
        'IndexName': 'status-last_seen-index',
        'KeyConditionExpression': Key('status').eq(status),
        'Limit': limit,
        'ScanIndexForward': False  # Most recently seen first
    }
    
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = table.query(**query_params)
    
    duration_ms = (time.time() - start_time) * 1000
    
    logger.log('info', 'Query devices by status completed',
        service='dynamodb_queries',
        operation='query_devices_by_status',
        status=status,
        duration_ms=duration_ms,
        item_count=len(response['Items'])
    )
    
    if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
        logger.log('warning', f'Query exceeded performance threshold: {duration_ms}ms',
            service='dynamodb_queries',
            operation='query_devices_by_status',
            status=status,
            duration_ms=duration_ms,
            threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS
        )
    
    return {
        'items': response['Items'],
        'last_key': response.get('LastEvaluatedKey'),
        'has_more': 'LastEvaluatedKey' in response,
        'duration_ms': duration_ms
    }


def query_readings_by_device_and_metric(
    device_id: str,
    metric_type: str,
    limit: int = 100,
    last_key: Optional[Dict] = None,
    table_name: str = 'aquachain-readings'
) -> Dict[str, Any]:
    """
    Query sensor readings by device and metric type using device_id-metric_type-index GSI
    
    Args:
        device_id: Device ID to query readings for
        metric_type: Type of metric (e.g., 'pH', 'turbidity', 'temperature')
        limit: Maximum number of items to return
        last_key: Pagination token from previous query
        table_name: DynamoDB table name
        
    Returns:
        Dictionary with items, last_key, and has_more fields
    """
    start_time = time.time()
    table = dynamodb.Table(table_name)
    
    query_params = {
        'IndexName': 'device_id-metric_type-index',
        'KeyConditionExpression': Key('deviceId').eq(device_id) & Key('metric_type').eq(metric_type),
        'Limit': limit,
        'ScanIndexForward': False  # Newest first
    }
    
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = table.query(**query_params)
    
    duration_ms = (time.time() - start_time) * 1000
    
    logger.log('info', 'Query readings by device and metric completed',
        service='dynamodb_queries',
        operation='query_readings_by_device_and_metric',
        device_id=device_id,
        metric_type=metric_type,
        duration_ms=duration_ms,
        item_count=len(response['Items'])
    )
    
    if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
        logger.log('warning', f'Query exceeded performance threshold: {duration_ms}ms',
            service='dynamodb_queries',
            operation='query_readings_by_device_and_metric',
            device_id=device_id,
            metric_type=metric_type,
            duration_ms=duration_ms,
            threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS
        )
    
    return {
        'items': response['Items'],
        'last_key': response.get('LastEvaluatedKey'),
        'has_more': 'LastEvaluatedKey' in response,
        'duration_ms': duration_ms
    }


def query_readings_by_alert_level(
    alert_level: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    last_key: Optional[Dict] = None,
    table_name: str = 'aquachain-readings'
) -> Dict[str, Any]:
    """
    Query sensor readings by alert level using alert_level-timestamp-index GSI
    
    Args:
        alert_level: Alert level (e.g., 'critical', 'warning', 'normal')
        start_time: Optional start timestamp for range query
        end_time: Optional end timestamp for range query
        limit: Maximum number of items to return
        last_key: Pagination token from previous query
        table_name: DynamoDB table name
        
    Returns:
        Dictionary with items, last_key, and has_more fields
    """
    query_start_time = time.time()
    table = dynamodb.Table(table_name)
    
    # Build key condition expression
    if start_time and end_time:
        key_condition = Key('alert_level').eq(alert_level) & Key('timestamp').between(start_time, end_time)
    elif start_time:
        key_condition = Key('alert_level').eq(alert_level) & Key('timestamp').gte(start_time)
    elif end_time:
        key_condition = Key('alert_level').eq(alert_level) & Key('timestamp').lte(end_time)
    else:
        key_condition = Key('alert_level').eq(alert_level)
    
    query_params = {
        'IndexName': 'alert_level-timestamp-index',
        'KeyConditionExpression': key_condition,
        'Limit': limit,
        'ScanIndexForward': False  # Newest first
    }
    
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = table.query(**query_params)
    
    duration_ms = (time.time() - query_start_time) * 1000
    
    logger.log('info', 'Query readings by alert level completed',
        service='dynamodb_queries',
        operation='query_readings_by_alert_level',
        alert_level=alert_level,
        duration_ms=duration_ms,
        item_count=len(response['Items'])
    )
    
    if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
        logger.log('warning', f'Query exceeded performance threshold: {duration_ms}ms',
            service='dynamodb_queries',
            operation='query_readings_by_alert_level',
            alert_level=alert_level,
            duration_ms=duration_ms,
            threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS
        )
    
    return {
        'items': response['Items'],
        'last_key': response.get('LastEvaluatedKey'),
        'has_more': 'LastEvaluatedKey' in response,
        'duration_ms': duration_ms
    }


def query_user_by_email(
    email: str,
    table_name: str = 'aquachain-users'
) -> Optional[Dict[str, Any]]:
    """
    Query user by email using email-index GSI
    
    Args:
        email: User email address
        table_name: DynamoDB table name
        
    Returns:
        User item if found, None otherwise
    """
    start_time = time.time()
    table = dynamodb.Table(table_name)
    
    response = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(email),
        Limit=1
    )
    
    duration_ms = (time.time() - start_time) * 1000
    
    logger.log('info', 'Query user by email completed',
        service='dynamodb_queries',
        operation='query_user_by_email',
        email=email,
        duration_ms=duration_ms,
        found=len(response['Items']) > 0
    )
    
    if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
        logger.log('warning', f'Query exceeded performance threshold: {duration_ms}ms',
            service='dynamodb_queries',
            operation='query_user_by_email',
            email=email,
            duration_ms=duration_ms,
            threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS
        )
    
    return response['Items'][0] if response['Items'] else None


def query_users_by_organization_and_role(
    organization_id: str,
    role: Optional[str] = None,
    limit: int = 100,
    last_key: Optional[Dict] = None,
    table_name: str = 'aquachain-users'
) -> Dict[str, Any]:
    """
    Query users by organization and optionally role using organization_id-role-index GSI
    
    Args:
        organization_id: Organization ID
        role: Optional role filter (e.g., 'admin', 'technician', 'consumer')
        limit: Maximum number of items to return
        last_key: Pagination token from previous query
        table_name: DynamoDB table name
        
    Returns:
        Dictionary with items, last_key, and has_more fields
    """
    start_time = time.time()
    table = dynamodb.Table(table_name)
    
    # Build key condition expression
    if role:
        key_condition = Key('organization_id').eq(organization_id) & Key('role').eq(role)
    else:
        key_condition = Key('organization_id').eq(organization_id)
    
    query_params = {
        'IndexName': 'organization_id-role-index',
        'KeyConditionExpression': key_condition,
        'Limit': limit
    }
    
    if last_key:
        query_params['ExclusiveStartKey'] = last_key
    
    response = table.query(**query_params)
    
    duration_ms = (time.time() - start_time) * 1000
    
    logger.log('info', 'Query users by organization and role completed',
        service='dynamodb_queries',
        operation='query_users_by_organization_and_role',
        organization_id=organization_id,
        role=role,
        duration_ms=duration_ms,
        item_count=len(response['Items'])
    )
    
    if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
        logger.log('warning', f'Query exceeded performance threshold: {duration_ms}ms',
            service='dynamodb_queries',
            operation='query_users_by_organization_and_role',
            organization_id=organization_id,
            role=role,
            duration_ms=duration_ms,
            threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS
        )
    
    return {
        'items': response['Items'],
        'last_key': response.get('LastEvaluatedKey'),
        'has_more': 'LastEvaluatedKey' in response,
        'duration_ms': duration_ms
    }
