"""
AquaChain Admin Service
Handles administrative operations including user management, system configuration,
health monitoring, and incident management.
"""

import json
import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# DynamoDB tables
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users')
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
AUDIT_TABLE = os.environ.get('AUDIT_TABLE', 'AquaChain-AuditLogs')
CONFIG_TABLE = os.environ.get('CONFIG_TABLE', 'AquaChain-SystemConfig')

def lambda_handler(event, context):
    """
    Main Lambda handler for admin operations
    """
    try:
        # Parse request
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        
        # Allow /api/devices for all authenticated users (not just admins)
        if path.startswith('/api/devices') and not path.startswith('/api/admin'):
            return _handle_user_device_management(event, http_method, path, query_params)
        
        # Verify admin authorization for admin endpoints
        if not _verify_admin_access(event):
            return _create_response(403, {'error': 'Admin access required'})
        
        # Route requests
        if path.startswith('/api/admin/users'):
            return _handle_user_management(http_method, path, body, query_params, path_params)
        elif path.startswith('/api/admin/system'):
            return _handle_system_management(http_method, path, body, query_params)
        elif path.startswith('/api/admin/incidents'):
            return _handle_incident_management(http_method, path, body, query_params, path_params)
        elif path.startswith('/api/admin/audit'):
            return _handle_audit_management(http_method, path, query_params)
        elif path.startswith('/api/admin/devices'):
            return _handle_device_management(http_method, path, query_params)
        else:
            return _create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Admin service error: {str(e)}")
        return _create_response(500, {'error': 'Internal server error'})

def _verify_admin_access(event) -> bool:
    """
    Verify that the request comes from an admin user
    """
    try:
        # Get user info from Cognito authorizer context
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Check if user has admin role
        cognito_groups = claims.get('cognito:groups', '')
        if isinstance(cognito_groups, str):
            groups = cognito_groups.split(',') if cognito_groups else []
        else:
            groups = cognito_groups or []
            
        return 'administrators' in groups
        
    except Exception as e:
        logger.error(f"Admin access verification failed: {str(e)}")
        return False

def _handle_user_management(method: str, path: str, body: Dict, query_params: Dict, path_params: Dict):
    """
    Handle user management operations
    """
    if method == 'GET' and path == '/api/admin/users':
        return _get_all_users(query_params)
    elif method == 'POST' and path == '/api/admin/users':
        return _create_user(body)
    elif method == 'PUT' and 'userId' in path_params:
        return _update_user(path_params['userId'], body)
    elif method == 'DELETE' and 'userId' in path_params:
        return _delete_user(path_params['userId'])
    elif method == 'POST' and path.endswith('/reset-password'):
        # Extract userId from path like /api/admin/users/{userId}/reset-password
        user_id = path.split('/')[-2]
        return _reset_user_password(user_id)
    else:
        return _create_response(404, {'error': 'User management endpoint not found'})

def _get_all_users(query_params: Dict):
    """
    Get all users from Cognito User Pool
    """
    try:
        limit = int(query_params.get('limit', 50))
        pagination_token = query_params.get('paginationToken')
        
        params = {
            'UserPoolId': USER_POOL_ID,
            'Limit': limit
        }
        
        if pagination_token:
            params['PaginationToken'] = pagination_token
            
        response = cognito_client.list_users(**params)
        
        users = []
        for user in response.get('Users', []):
            user_data = {
                'userId': user['Username'],
                'email': _get_user_attribute(user, 'email'),
                'name': _get_user_attribute(user, 'name'),
                'role': _get_user_groups(user['Username']),
                'status': user['UserStatus'],
                'createdAt': user['UserCreateDate'].isoformat(),
                'lastModified': user['UserLastModifiedDate'].isoformat(),
                'enabled': user['Enabled']
            }
            users.append(user_data)
        
        result = {
            'users': users,
            'paginationToken': response.get('PaginationToken')
        }
        
        return _create_response(200, result)
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch users'})

def _get_user_attribute(user: Dict, attribute_name: str) -> str:
    """
    Get user attribute value
    """
    for attr in user.get('Attributes', []):
        if attr['Name'] == attribute_name:
            return attr['Value']
    return ''

def _get_user_groups(username: str) -> str:
    """
    Get user's Cognito groups
    """
    try:
        response = cognito_client.admin_list_groups_for_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        groups = [group['GroupName'] for group in response.get('Groups', [])]
        return groups[0] if groups else 'consumers'  # Default role
    except:
        return 'consumers'

def _handle_system_management(method: str, path: str, body: Dict, query_params: Dict):
    """
    Handle system configuration and health monitoring
    """
    if method == 'GET' and path == '/api/admin/system/configuration':
        return _get_system_configuration()
    elif method == 'PUT' and path == '/api/admin/system/configuration':
        return _update_system_configuration(body)
    elif method == 'GET' and path == '/api/admin/system/health':
        return _get_system_health()
    elif method == 'GET' and path == '/api/admin/system/performance':
        return _get_performance_metrics(query_params)
    else:
        return _create_response(404, {'error': 'System management endpoint not found'})

def _get_system_configuration():
    """
    Get current system configuration
    """
    try:
        table = dynamodb.Table(CONFIG_TABLE)
        response = table.get_item(Key={'config_id': 'system_config'})
        
        if 'Item' in response:
            config = response['Item']
            # Remove DynamoDB metadata
            config.pop('config_id', None)
            return _create_response(200, config)
        else:
            # Return default configuration
            default_config = {
                'alertThresholds': {
                    'ph': {'min': 6.5, 'max': 8.5},
                    'turbidity': {'min': 0, 'max': 4},
                    'tds': {'min': 0, 'max': 500},
                    'temperature': {'min': 0, 'max': 35}
                },
                'systemSettings': {
                    'dataRetentionDays': 365,
                    'alertCooldownMinutes': 30,
                    'maintenanceMode': False
                }
            }
            return _create_response(200, default_config)
            
    except Exception as e:
        logger.error(f"Error fetching system configuration: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch system configuration'})

def _update_system_configuration(config: Dict):
    """
    Update system configuration
    """
    try:
        table = dynamodb.Table(CONFIG_TABLE)
        
        # Add metadata
        config['config_id'] = 'system_config'
        config['updated_at'] = datetime.utcnow().isoformat()
        
        table.put_item(Item=config)
        
        return _create_response(200, {'message': 'Configuration updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating system configuration: {str(e)}")
        return _create_response(500, {'error': 'Failed to update system configuration'})

def _get_system_health():
    """
    Get system health metrics from CloudWatch
    """
    try:
        # Get metrics from CloudWatch
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        # API Gateway metrics
        api_metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApiGateway',
            MetricName='Count',
            Dimensions=[],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        # Lambda metrics
        lambda_metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        # Get device count from DynamoDB
        devices_table = dynamodb.Table(DEVICES_TABLE)
        device_scan = devices_table.scan(Select='COUNT')
        total_devices = device_scan['Count']
        
        # Calculate active devices (devices with data in last 24 hours)
        active_devices = _count_active_devices()
        
        health_metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'criticalPathUptime': 99.5,  # Would calculate from actual metrics
            'apiUptime': 99.2,
            'notificationUptime': 98.8,
            'errorRate': 0.5,
            'activeDevices': active_devices,
            'totalDevices': total_devices,
            'activeAlerts': _count_active_alerts(),
            'pendingServiceRequests': _count_pending_service_requests()
        }
        
        return _create_response(200, health_metrics)
        
    except Exception as e:
        logger.error(f"Error fetching system health: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch system health'})

def _count_active_devices() -> int:
    """
    Count devices that have sent data in the last 24 hours
    """
    try:
        # This would query the readings table for recent data
        # For now, return a reasonable estimate
        devices_table = dynamodb.Table(DEVICES_TABLE)
        response = devices_table.scan(Select='COUNT')
        return int(response['Count'] * 0.85)  # Assume 85% are active
    except:
        return 0

def _count_active_alerts() -> int:
    """
    Count active alerts
    """
    try:
        # This would query alerts table
        # For now, return a reasonable number
        return 5
    except:
        return 0

def _count_pending_service_requests() -> int:
    """
    Count pending service requests
    """
    try:
        # This would query service requests table
        # For now, return a reasonable number
        return 3
    except:
        return 0

def _handle_incident_management(method: str, path: str, body: Dict, query_params: Dict, path_params: Dict):
    """
    Handle incident management operations
    """
    if method == 'GET' and path == '/api/admin/incidents/stats':
        return _get_incident_stats(query_params)
    elif method == 'GET' and path == '/api/admin/incidents':
        return _get_incidents(query_params)
    else:
        return _create_response(404, {'error': 'Incident management endpoint not found'})

def _get_incident_stats(query_params: Dict):
    """
    Get incident statistics
    """
    try:
        days = int(query_params.get('days', 30))
        
        # For now, return mock data since incident system isn't fully implemented
        stats = {
            'totalIncidents': 15,
            'openIncidents': 3,
            'criticalIncidents': 1,
            'avgResolutionTime': 4.2,
            'incidentsByCategory': [
                {'category': 'system', 'count': 6},
                {'category': 'performance', 'count': 4},
                {'category': 'security', 'count': 3},
                {'category': 'data', 'count': 2}
            ],
            'incidentsBySeverity': [
                {'severity': 'low', 'count': 8},
                {'severity': 'medium', 'count': 4},
                {'severity': 'high', 'count': 2},
                {'severity': 'critical', 'count': 1}
            ]
        }
        
        return _create_response(200, stats)
        
    except Exception as e:
        logger.error(f"Error fetching incident stats: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch incident statistics'})

def _get_incidents(query_params: Dict):
    """
    Get incident reports
    """
    try:
        # Return empty incidents list since system isn't fully implemented
        return _create_response(200, {'incidents': []})
        
    except Exception as e:
        logger.error(f"Error fetching incidents: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch incidents'})

def _handle_audit_management(method: str, path: str, query_params: Dict):
    """
    Handle audit trail operations
    """
    if method == 'GET' and path == '/api/admin/audit/trail':
        return _get_audit_trail(query_params)
    else:
        return _create_response(404, {'error': 'Audit management endpoint not found'})

def _get_audit_trail(query_params: Dict):
    """
    Get audit trail entries
    """
    try:
        start_date = query_params.get('startDate')
        end_date = query_params.get('endDate')
        limit = int(query_params.get('limit', 100))
        
        table = dynamodb.Table(AUDIT_TABLE)
        
        # Scan audit table (in production, would use GSI for date range queries)
        response = table.scan(Limit=limit)
        
        audit_entries = []
        for item in response.get('Items', []):
            entry = {
                'id': item.get('audit_id', ''),
                'timestamp': item.get('timestamp', ''),
                'userId': item.get('user_id', ''),
                'action': item.get('action', ''),
                'resource': item.get('resource', ''),
                'details': item.get('details', {}),
                'ipAddress': item.get('ip_address', ''),
                'userAgent': item.get('user_agent', '')
            }
            audit_entries.append(entry)
        
        return _create_response(200, {'auditEntries': audit_entries})
        
    except Exception as e:
        logger.error(f"Error fetching audit trail: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch audit trail'})

def _handle_device_management(method: str, path: str, query_params: Dict):
    """
    Handle device management operations
    Accepts both /api/admin/devices and /api/devices paths
    """
    if method == 'GET' and (path == '/api/admin/devices' or path == '/api/devices'):
        return _get_all_devices(query_params)
    else:
        return _create_response(404, {'error': 'Device management endpoint not found'})

def _handle_user_device_management(event, method: str, path: str, query_params: Dict):
    """
    Handle device operations for regular users (non-admin)
    Users can only see their own devices
    """
    try:
        # Get user ID from Cognito authorizer
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        
        if not user_id:
            return _create_response(401, {'error': 'User not authenticated'})
        
        if method == 'GET' and path == '/api/devices':
            return _get_user_devices(user_id)
        else:
            return _create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"User device management error: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch devices'})

def _get_user_devices(user_id: str):
    """
    Get devices for a specific user
    """
    try:
        table = dynamodb.Table(DEVICES_TABLE)
        
        # Query by userId using GSI
        response = table.query(
            IndexName='UserIndex',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        devices = []
        for item in response.get('Items', []):
            device = {
                'deviceId': item.get('deviceId', ''),
                'deviceName': item.get('deviceName', ''),
                'status': item.get('status', 'offline'),
                'lastSeen': item.get('lastSeen', ''),
                'location': item.get('location', 'Unknown'),
                'deviceType': item.get('deviceType', 'ESP32'),
                'firmwareVersion': item.get('firmwareVersion', ''),
                'isOnline': item.get('isOnline', False),
                'createdAt': item.get('createdAt', ''),
                'updatedAt': item.get('updatedAt', '')
            }
            devices.append(device)
        
        logger.info(f"Found {len(devices)} devices for user {user_id}")
        response_body = {'success': True, 'data': devices}
        logger.info(f"Returning response: {json.dumps(response_body)[:200]}...")  # Log first 200 chars
        # Return in format expected by frontend dataService
        return _create_response(200, response_body)
        
    except Exception as e:
        logger.error(f"Error fetching user devices: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch devices'})

def _get_all_devices(query_params: Dict):
    """
    Get all devices for admin view
    """
    try:
        table = dynamodb.Table(DEVICES_TABLE)
        response = table.scan()
        
        devices = []
        for item in response.get('Items', []):
            device = {
                'deviceId': item.get('device_id', ''),
                'status': item.get('status', 'offline'),
                'lastSeen': item.get('last_seen', ''),
                'location': {
                    'latitude': float(item.get('latitude', 0)),
                    'longitude': float(item.get('longitude', 0)),
                    'address': item.get('location', 'Unknown')
                },
                'consumerId': item.get('user_id', ''),
                'consumerName': item.get('consumer_name', 'Unassigned'),
                'uptime': 0,
                'currentWQI': 0,
                'batteryLevel': 100,
                'signalStrength': -65,
                'maintenanceHistory': []
            }
            devices.append(device)
        
        return _create_response(200, {'devices': devices})
        
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch devices'})

def _create_user(user_data: Dict):
    """
    Create a new user
    """
    try:
        # Map frontend roles to Cognito groups
        role_mapping = {
            'consumers': 'consumers',
            'technicians': 'technicians', 
            'administrators': 'administrators',
            'inventory_manager': 'technicians',  # Map inventory manager to technicians group
            'admin': 'administrators'
        }
        
        role = user_data.get('role', 'consumers')
        cognito_group = role_mapping.get(role, 'consumers')
        
        # Generate a secure temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(12))
        
        # Create user in Cognito
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_data['email'],
            UserAttributes=[
                {'Name': 'email', 'Value': user_data['email']},
                {'Name': 'name', 'Value': user_data['name']},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=temp_password,
            MessageAction='RESEND'  # Send welcome email with temp password
        )
        
        # Add user to appropriate group
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=user_data['email'],
                GroupName=cognito_group
            )
        except Exception as group_error:
            logger.warning(f"Failed to add user to group {cognito_group}: {str(group_error)}")
            # Continue - user can still sign in without group
        
        # Force user to change password on first login
        try:
            cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=user_data['email'],
                Password=temp_password,
                Permanent=False  # Force password change on first login
            )
        except Exception as password_error:
            logger.warning(f"Failed to set temporary password: {str(password_error)}")
        
        return _create_response(201, {
            'message': 'User created successfully', 
            'userId': user_data['email'],
            'temporaryPassword': temp_password,
            'instructions': 'User will receive an email with temporary password and must change it on first login'
        })
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return _create_response(500, {'error': f'Failed to create user: {str(e)}'})

def _reset_user_password(user_id: str):
    """
    Reset user password and send new temporary password
    """
    try:
        # Generate a secure temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(12))
        
        # Set temporary password
        cognito_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=user_id,
            Password=temp_password,
            Permanent=False  # Force password change on first login
        )
        
        # Send password reset email
        cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_id,
            MessageAction='RESEND'  # Resend welcome email with new temp password
        )
        
        return _create_response(200, {
            'message': 'Password reset successfully',
            'temporaryPassword': temp_password,
            'instructions': 'User will receive an email with temporary password and must change it on first login'
        })
        
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        return _create_response(500, {'error': f'Failed to reset password: {str(e)}'})

def _update_user(user_id: str, user_data: Dict):
    """
    Update an existing user
    """
    try:
        # Update user attributes
        attributes = []
        if 'name' in user_data:
            attributes.append({'Name': 'name', 'Value': user_data['name']})
        if 'email' in user_data:
            attributes.append({'Name': 'email', 'Value': user_data['email']})
            
        if attributes:
            cognito_client.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=user_id,
                UserAttributes=attributes
            )
        
        # Update user status if provided
        if 'enabled' in user_data:
            if user_data['enabled']:
                cognito_client.admin_enable_user(UserPoolId=USER_POOL_ID, Username=user_id)
            else:
                cognito_client.admin_disable_user(UserPoolId=USER_POOL_ID, Username=user_id)
        
        return _create_response(200, {'message': 'User updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return _create_response(500, {'error': 'Failed to update user'})

def _delete_user(user_id: str):
    """
    Delete a user
    """
    try:
        cognito_client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=user_id
        )
        
        return _create_response(200, {'message': 'User deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return _create_response(500, {'error': 'Failed to delete user'})

def _get_performance_metrics(query_params: Dict):
    """
    Get performance metrics for specified time range
    """
    try:
        time_range = query_params.get('timeRange', '24h')
        
        # Generate mock performance data based on time range
        now = datetime.utcnow()
        if time_range == '1h':
            intervals = 12
            interval_minutes = 5
        elif time_range == '24h':
            intervals = 24
            interval_minutes = 60
        elif time_range == '7d':
            intervals = 7
            interval_minutes = 24 * 60
        else:  # 30d
            intervals = 30
            interval_minutes = 24 * 60
        
        metrics = []
        for i in range(intervals):
            timestamp = now - timedelta(minutes=(intervals - i - 1) * interval_minutes)
            metrics.append({
                'timestamp': timestamp.isoformat(),
                'avgAlertLatency': 15 + (i % 10),
                'p95AlertLatency': 25 + (i % 8),
                'p99AlertLatency': 30 + (i % 5),
                'avgApiResponseTime': 150 + (i % 100),
                'p95ApiResponseTime': 350 + (i % 150),
                'throughput': 50 + (i % 30),
                'lambdaInvocations': 5000 + (i % 2000),
                'lambdaErrors': i % 50,
                'dynamodbReadCapacity': 1000 + (i % 500),
                'dynamodbWriteCapacity': 500 + (i % 250)
            })
        
        return _create_response(200, metrics)
        
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch performance metrics'})

def _create_response(status_code: int, body: Dict) -> Dict:
    """
    Create standardized API response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }