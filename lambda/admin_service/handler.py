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
import hashlib
from config_validation import (
    validate_configuration, 
    get_validation_rules,
    validate_severity_thresholds,
    validate_notification_channels,
    normalize_threshold_format,
    validate_ml_settings,
    get_ml_settings,
    DEFAULT_ML_SETTINGS
)
import health_monitor

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID') or os.environ.get('USER_POOL_ID')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# DynamoDB tables
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users')
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
AUDIT_TABLE = os.environ.get('AUDIT_TABLE', 'AquaChain-AuditLogs')
CONFIG_TABLE = os.environ.get('CONFIG_TABLE', 'AquaChain-SystemConfig')
CONFIG_HISTORY_TABLE = os.environ.get('CONFIG_HISTORY_TABLE', 'AquaChain-ConfigHistory')

# ============================================================================
# PII MASKING UTILITIES (Security Layer)
# ============================================================================

def _mask_email(email: str) -> str:
    """Mask email showing only first 2 chars and domain"""
    if not email or '@' not in email:
        return 'N/A'
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return '*' * len(local) + '@' + domain
    return local[:2] + '*' * (len(local) - 2) + '@' + domain

def _mask_phone(phone: str) -> str:
    """Mask phone showing only last 4 digits"""
    if not phone:
        return 'N/A'
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) < 4:
        return '*' * len(digits)
    return '*' * (len(digits) - 4) + ' ' + digits[-4:]

def _mask_last_name(last_name: str) -> str:
    """Mask last name showing only first character"""
    if not last_name:
        return 'N/A'
    if len(last_name) <= 1:
        return last_name
    return last_name[0] + '*' * (len(last_name) - 1)

def lambda_handler(event, context):
    """
    Main Lambda handler for admin operations
    """
    try:
        # Handle OPTIONS requests for CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Admin-Password,x-admin-password',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400'  # Cache preflight for 24 hours
                },
                'body': json.dumps({'message': 'OK'})
            }
        
        # Parse request
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        
        logger.info(f"Admin service request: {http_method} {path}")
        
        # Allow /api/devices for all authenticated users (not just admins)
        if path.startswith('/api/devices') and not path.startswith('/api/admin'):
            return _handle_user_device_management(event, http_method, path, query_params)
        
        # Allow /api/profile for all authenticated users (not just admins)
        if path.startswith('/api/profile'):
            return _handle_profile_management(event, http_method, path, body)
        
        # Allow login tracking for all authenticated users (not just admins)
        if path == '/api/admin/users/track-login' and http_method == 'POST':
            return _track_user_login(body)
        
        # Verify admin authorization for admin endpoints
        if not _verify_admin_access(event):
            logger.warning(f"Admin access denied for path: {path}")
            return _create_response(403, {'error': 'Admin access required'})
        
        # Route requests
        if path.startswith('/api/admin/users'):
            return _handle_user_management(http_method, path, body, query_params, path_params, event)
        elif path.startswith('/api/admin/system/metrics'):
            return _handle_system_metrics(http_method)
        elif path.startswith('/api/admin/system'):
            # Extract admin info for audit logging
            request_context = event.get('requestContext', {})
            authorizer = request_context.get('authorizer', {})
            claims = authorizer.get('claims', {})
            admin_id = claims.get('sub') or claims.get('cognito:username', 'unknown')
            ip_address = request_context.get('identity', {}).get('sourceIp', 'unknown')
            
            # Add admin info to query params for audit logging
            query_params = query_params or {}
            query_params['adminId'] = admin_id
            query_params['ipAddress'] = ip_address
            
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
        logger.error(f"Admin service error: {str(e)}", exc_info=True)
        return _create_response(500, {'error': 'Internal server error', 'message': str(e)})

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

def _handle_user_management(method: str, path: str, body: Dict, query_params: Dict, path_params: Dict, event: Dict = None):
    """
    Handle user management operations
    """
    # Check for sensitive data reveal request (GET with reveal=true query param)
    if method == 'GET' and path_params.get('userId') and query_params.get('reveal') == 'true':
        user_id = path_params['userId']
        
        # Extract admin ID from authorizer context
        request_context = event.get('requestContext', {}) if event else {}
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        admin_id = claims.get('sub') or claims.get('cognito:username')
        ip_address = request_context.get('identity', {}).get('sourceIp', 'unknown')
        
        # No password verification - rely on JWT auth + audit logging
        return _get_sensitive_user_data(user_id, admin_id, ip_address, admin_password=None)
    
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
        # Validate USER_POOL_ID is configured
        if not USER_POOL_ID:
            logger.error("USER_POOL_ID environment variable not configured")
            return _create_response(500, {
                'error': 'User pool not configured',
                'message': 'COGNITO_USER_POOL_ID or USER_POOL_ID environment variable is missing'
            })
        
        logger.info(f"Fetching users from User Pool: {USER_POOL_ID}")
        
        limit = int(query_params.get('limit', 50))
        pagination_token = query_params.get('paginationToken')
        
        params = {
            'UserPoolId': USER_POOL_ID,
            'Limit': limit
        }
        
        if pagination_token:
            params['PaginationToken'] = pagination_token
        
        logger.info(f"Calling list_users with params: {params}")
        response = cognito_client.list_users(**params)
        logger.info(f"Successfully fetched {len(response.get('Users', []))} users")
        
        users = []
        for user in response.get('Users', []):
            try:
                # Map Cognito UserStatus to frontend status
                cognito_status = user['UserStatus']
                logger.info(f"Processing user {user['Username']}: Cognito status = {cognito_status}")
                
                if cognito_status == 'CONFIRMED':
                    status = 'active'
                elif cognito_status in ['FORCE_CHANGE_PASSWORD', 'RESET_REQUIRED']:
                    status = 'pending'
                elif cognito_status in ['ARCHIVED', 'COMPROMISED', 'UNKNOWN']:
                    status = 'inactive'
                elif cognito_status == 'UNCONFIRMED':
                    status = 'pending'
                else:
                    status = 'inactive'
                
                logger.info(f"Mapped status for {user['Username']}: from {cognito_status} to {status}")
                
                # Try to get profile data from DynamoDB Users table
                last_login = None
                first_name = None
                last_name = None
                phone = None
                
                try:
                    users_table = dynamodb.Table(USERS_TABLE)
                    user_record = users_table.get_item(Key={'userId': user['Username']})
                    if 'Item' in user_record:
                        item = user_record['Item']
                        last_login = item.get('lastLogin')
                        first_name = item.get('firstName')
                        last_name = item.get('lastName')
                        phone = item.get('phone')
                        logger.info(f"Found profile data for {user['Username']}: firstName={first_name}, lastName={last_name}, phone={phone}")
                    else:
                        logger.info(f"No DynamoDB record found for {user['Username']}")
                except Exception as db_error:
                    logger.warning(f"Could not fetch profile data for {user['Username']}: {str(db_error)}")
                
                # Use DynamoDB data if available, otherwise fall back to Cognito
                user_data = {
                    'userId': user['Username'],
                    'email': _get_user_attribute(user, 'email'),
                    'emailMasked': _mask_email(_get_user_attribute(user, 'email')),
                    'name': _get_user_attribute(user, 'name') or _get_user_attribute(user, 'given_name'),
                    'firstName': first_name or _get_user_attribute(user, 'given_name') or '',
                    'lastName': last_name or _get_user_attribute(user, 'family_name') or '',
                    'lastNameMasked': _mask_last_name(last_name or _get_user_attribute(user, 'family_name') or ''),
                    'phone': phone or _get_user_attribute(user, 'phone_number') or '',
                    'phoneMasked': _mask_phone(phone or _get_user_attribute(user, 'phone_number') or ''),
                    'role': _get_user_groups(user['Username']),
                    'status': status,  # Use mapped status
                    'cognitoStatus': cognito_status,  # Include original for debugging
                    'createdAt': user['UserCreateDate'].isoformat(),
                    'lastModified': user['UserLastModifiedDate'].isoformat(),
                    'lastLogin': last_login,  # Add last login timestamp
                    'enabled': user['Enabled']
                }
                
                logger.info(f"Final user_data status field: {user_data['status']}")
                users.append(user_data)
            except Exception as user_error:
                logger.warning(f"Error processing user {user.get('Username')}: {str(user_error)}")
                continue
        
        result = {
            'users': users,
            'paginationToken': response.get('PaginationToken')
        }
        
        logger.info(f"Returning {len(users)} users")
        return _create_response(200, result)
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Cognito ClientError fetching users: {error_code} - {error_message}")
        logger.error(f"Full error response: {e.response}")
        
        if error_code == 'AccessDeniedException':
            return _create_response(500, {
                'error': 'Access denied to Cognito',
                'message': 'Lambda execution role lacks cognito-idp:ListUsers permission',
                'details': error_message
            })
        else:
            return _create_response(500, {
                'error': 'Failed to fetch users from Cognito',
                'message': error_message,
                'code': error_code
            })
    except Exception as e:
        logger.error(f"Unexpected error fetching users: {str(e)}", exc_info=True)
        return _create_response(500, {
            'error': 'Failed to fetch users',
            'message': str(e)
        })

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
    Get user's Cognito groups and normalize to singular form
    """
    try:
        if not USER_POOL_ID:
            logger.warning("USER_POOL_ID not configured, returning default role")
            return 'consumer'  # Return singular form
        
        response = cognito_client.admin_list_groups_for_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        groups = [group['GroupName'] for group in response.get('Groups', [])]
        group_name = groups[0] if groups else 'consumers'  # Get Cognito group (plural)
        
        # Normalize to singular form for frontend consistency
        return _normalize_role(group_name)
    except ClientError as e:
        logger.warning(f"Error fetching groups for user {username}: {str(e)}")
        return 'consumer'  # Return singular form
    except Exception as e:
        logger.warning(f"Unexpected error fetching groups for user {username}: {str(e)}")
        return 'consumer'  # Return singular form

def _normalize_role(role: str) -> str:
    """
    Normalize role from Cognito group name (plural) to singular form
    Examples:
      consumers -> consumer
      technicians -> technician
      administrators -> administrator
      admin -> admin (no change)
    """
    role_mapping = {
        'consumers': 'consumer',
        'technicians': 'technician',
        'administrators': 'administrator',
        'admin': 'admin',
        'inventory_managers': 'inventory_manager',
        'warehouse_managers': 'warehouse_manager',
        'supplier_coordinators': 'supplier_coordinator',
        'procurement_controllers': 'procurement_controller'
    }
    
    # Return mapped value or original if not in mapping
    return role_mapping.get(role.lower(), role)

def _handle_system_management(method: str, path: str, body: Dict, query_params: Dict):
    """
    Handle system configuration and health monitoring
    """
    if method == 'GET' and path == '/api/admin/system/configuration':
        return _get_system_configuration()
    elif method == 'PUT' and path == '/api/admin/system/configuration':
        # Extract admin info from event for audit logging
        return _update_system_configuration(body, query_params)
    elif method == 'GET' and path == '/api/admin/system/configuration/history':
        return _get_configuration_history(query_params)
    elif method == 'POST' and path == '/api/admin/system/configuration/validate':
        return _validate_configuration_endpoint(body)
    elif method == 'POST' and path == '/api/admin/system/configuration/rollback':
        return _rollback_configuration(body, query_params)
    elif method == 'GET' and path == '/api/admin/system/health':
        return _get_system_health(query_params)
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

def _update_system_configuration(config: Dict, query_params: Dict):
    """
    Update system configuration with validation, versioning, and audit logging
    """
    try:
        # Phase 1: Base configuration validation
        is_valid, errors = validate_configuration(config)
        if not is_valid:
            logger.warning(f"Configuration validation failed: {errors}")
            return _create_response(400, {
                'error': 'Configuration validation failed',
                'validationErrors': errors
            })
        
        # Phase 3a: Severity threshold validation
        all_errors = []
        
        # Validate severity thresholds if present
        if 'alertThresholds' in config and 'global' in config['alertThresholds']:
            thresholds = config['alertThresholds']['global']
            severity_valid, severity_errors = validate_severity_thresholds(thresholds)
            if not severity_valid:
                all_errors.extend(severity_errors)
                logger.warning(f"Severity threshold validation failed: {severity_errors}")
        
        # Validate notification channels if present
        if 'notificationSettings' in config:
            channels_valid, channel_errors = validate_notification_channels(config['notificationSettings'])
            if not channels_valid:
                all_errors.extend(channel_errors)
                logger.warning(f"Notification channel validation failed: {channel_errors}")
        
        # Phase 3b: ML settings validation
        if 'mlSettings' in config:
            ml_valid, ml_errors = validate_ml_settings(config['mlSettings'])
            if not ml_valid:
                all_errors.extend(ml_errors)
                logger.warning(f"ML settings validation failed: {ml_errors}")
        
        # Return all validation errors if any
        if all_errors:
            return _create_response(400, {
                'error': 'Configuration validation failed',
                'validationErrors': all_errors
            })
        
        # Phase 3a: Normalize threshold format for backward compatibility
        config = normalize_threshold_format(config)
        
        # Phase 3b: Apply default ML settings if not provided
        if 'mlSettings' not in config:
            config['mlSettings'] = DEFAULT_ML_SETTINGS.copy()
            logger.info("Applied default ML settings to configuration")
        
        # Get current configuration for diff calculation
        config_table = dynamodb.Table(CONFIG_TABLE)
        current_response = config_table.get_item(Key={'config_id': 'system_config'})
        current_config = current_response.get('Item', {}) if 'Item' in current_response else {}
        
        # Calculate changes (diff)
        changes = _calculate_config_diff(current_config, config)
        
        # Get admin info from query params (passed from handler)
        admin_id = query_params.get('adminId', 'unknown')
        ip_address = query_params.get('ipAddress', 'unknown')
        
        # Generate version identifier
        version_timestamp = datetime.utcnow().isoformat()
        version_id = f"v_{version_timestamp}"
        
        # Get previous version ID
        previous_version = current_config.get('version', 'v_initial')
        
        # Save version to history table
        history_table = dynamodb.Table(CONFIG_HISTORY_TABLE)
        history_entry = {
            'configId': 'SYSTEM_CONFIG',
            'version': version_id,
            'updatedBy': admin_id,
            'updatedAt': version_timestamp,
            'previousVersion': previous_version,
            'changes': changes,
            'fullConfig': config,
            'ipAddress': ip_address
        }
        history_table.put_item(Item=history_entry)
        logger.info(f"Saved configuration version: {version_id}")
        
        # Update current configuration
        config['config_id'] = 'system_config'
        config['version'] = version_id
        config['updated_at'] = version_timestamp
        config['updated_by'] = admin_id
        
        config_table.put_item(Item=config)
        
        # Log audit entry
        _log_config_change(
            admin_id=admin_id,
            action='UPDATE_SYSTEM_CONFIG',
            ip_address=ip_address,
            changes=changes,
            version=version_id
        )
        
        logger.info(f"Configuration updated successfully by {admin_id}, version: {version_id}")
        
        return _create_response(200, {
            'message': 'Configuration updated successfully',
            'version': version_id,
            'changes': changes
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error updating configuration: {str(e)}")
        return _create_response(500, {
            'error': 'Database error occurred',
            'message': str(e)
        })
    except Exception as e:
        logger.error(f"Error updating system configuration: {str(e)}", exc_info=True)
        return _create_response(500, {
            'error': 'Failed to update system configuration',
            'message': str(e)
        })

def _get_system_health(query_params: Dict):
    """
    GET /api/admin/system-health
    Retrieve real-time health status of all monitored services.
    
    Uses the health_monitor module to check IoT Core, Lambda, DynamoDB, SNS,
    and ML Inference services. Supports cache refresh via query parameter.
    
    Query Parameters:
        refresh (optional): 'true' to force cache refresh, default 'false'
    """
    try:
        # Extract refresh query parameter (default to false)
        refresh_param = query_params.get('refresh', 'false').lower() if query_params else 'false'
        force_refresh = refresh_param == 'true'
        
        logger.info(f"System health check requested (force_refresh={force_refresh})")
        
        # Get health status from health_monitor module
        health_data = health_monitor.get_system_health(force_refresh=force_refresh)
        
        logger.info(f"System health check completed: {health_data['overallStatus']}, cacheHit={health_data['cacheHit']}")
        
        return _create_response(200, health_data)
    
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}", exc_info=True)
        return _create_response(500, {
            'error': 'Health check failed',
            'message': str(e),
            'services': []
        })

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

def _handle_profile_management(event, method: str, path: str, body: Dict):
    """
    Handle profile operations for authenticated users
    """
    try:
        # Get user ID from Cognito authorizer
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        
        if not user_id:
            return _create_response(401, {'error': 'User not authenticated'})
        
        if method == 'GET' and path == '/api/profile':
            return _get_user_profile(user_id)
        elif method == 'PUT' and path == '/api/profile/update':
            return _update_user_profile(user_id, body)
        else:
            return _create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Profile management error: {str(e)}", exc_info=True)
        return _create_response(500, {'error': 'Failed to process request', 'message': str(e)})

def _get_user_profile(user_id: str):
    """
    Get user profile from DynamoDB
    """
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            logger.warning(f"User profile not found: {user_id}")
            return _create_response(404, {'error': 'User profile not found'})
        
        profile = response['Item']
        logger.info(f"User profile retrieved: {user_id}")
        
        return _create_response(200, profile)
        
    except ClientError as e:
        logger.error(f"DynamoDB error fetching profile: {str(e)}")
        return _create_response(500, {'error': 'Database error occurred'})
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return _create_response(500, {'error': 'Failed to fetch profile'})

def _update_user_profile(user_id: str, updates: Dict):
    """
    Update user profile information
    """
    try:
        # Validate body is parsed
        if not isinstance(updates, dict):
            logger.error(f"Invalid update data type: {type(updates)}")
            return _create_response(400, {'error': 'Invalid request body'})
        
        logger.info(f"Updating profile for user {user_id} with data: {json.dumps(updates)[:200]}")
        
        # Get current profile
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            logger.warning(f"User profile not found: {user_id}")
            return _create_response(404, {'error': 'User profile not found'})
        
        current_profile = response['Item']
        
        # Prepare update expression
        update_expression = "SET updatedAt = :updated_at"
        expression_values = {':updated_at': datetime.utcnow().isoformat()}
        has_updates = False
        
        # Handle profile updates
        if 'profile' in updates:
            profile_updates = updates['profile']
            for key, value in profile_updates.items():
                if key in ['firstName', 'lastName', 'phone', 'address']:
                    update_expression += f", profile.{key} = :{key}"
                    expression_values[f':{key}'] = value
                    has_updates = True
        
        # Handle preferences updates
        if 'preferences' in updates:
            pref_updates = updates['preferences']
            for key, value in pref_updates.items():
                update_expression += f", preferences.{key} = :pref_{key}"
                expression_values[f':pref_{key}'] = value
                has_updates = True
        
        # If no updates were made, just return current profile
        if not has_updates:
            logger.info(f"No profile updates needed for user: {user_id}")
            return _create_response(200, current_profile)
        
        # Update DynamoDB
        logger.info(f"Updating profile with expression: {update_expression}")
        logger.info(f"Expression values: {expression_values}")
        
        response = table.update_item(
            Key={'userId': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        logger.info(f"User profile updated successfully: {user_id}")
        return _create_response(200, response['Attributes'])
        
    except ClientError as e:
        logger.error(f"DynamoDB ClientError updating profile: {str(e)}")
        logger.error(f"Error response: {e.response}")
        return _create_response(500, {
            'error': 'Database error occurred',
            'message': str(e)
        })
    except Exception as e:
        logger.error(f"Unexpected profile update error: {str(e)}", exc_info=True)
        return _create_response(500, {
            'error': 'Profile update failed',
            'message': str(e)
        })

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
        
        # Extract path parameters
        path_params = event.get('pathParameters') or {}
        
        if method == 'GET' and path == '/api/devices':
            return _get_user_devices(user_id)
        elif method == 'DELETE' and 'deviceId' in path_params:
            device_id = path_params['deviceId']
            return _delete_user_device(user_id, device_id)
        else:
            return _create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"User device management error: {str(e)}")
        return _create_response(500, {'error': 'Failed to process request'})

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

def _delete_user_device(user_id: str, device_id: str):
    """
    Delete a device owned by the user
    Verifies ownership before deletion for security
    """
    try:
        table = dynamodb.Table(DEVICES_TABLE)
        
        # First, verify the device exists and belongs to the user
        response = table.get_item(Key={'deviceId': device_id})
        
        if 'Item' not in response:
            logger.warning(f"Device not found: {device_id}")
            return _create_response(404, {'error': 'Device not found'})
        
        device = response['Item']
        device_owner = device.get('userId', '')
        
        # Verify ownership
        if device_owner != user_id:
            logger.warning(f"User {user_id} attempted to delete device {device_id} owned by {device_owner}")
            return _create_response(403, {'error': 'You do not have permission to delete this device'})
        
        # Delete the device
        table.delete_item(Key={'deviceId': device_id})
        
        logger.info(f"Device {device_id} deleted by user {user_id}")
        
        return _create_response(200, {
            'success': True,
            'message': 'Device deleted successfully'
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error deleting device: {str(e)}")
        return _create_response(500, {'error': 'Database error occurred'})
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        return _create_response(500, {'error': 'Failed to delete device'})

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

def _track_user_login(login_data: Dict):
    """
    Track user login timestamp in DynamoDB
    Expected fields: userId (or email)
    """
    try:
        user_id = login_data.get('userId') or login_data.get('email')
        
        if not user_id:
            return _create_response(400, {'error': 'userId or email is required'})
        
        # Update lastLogin in DynamoDB Users table
        users_table = dynamodb.Table(USERS_TABLE)
        # Use ISO format with 'Z' suffix to indicate UTC
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        try:
            # Try to update existing record
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET lastLogin = :timestamp, updatedAt = :timestamp',
                ExpressionAttributeValues={
                    ':timestamp': current_time
                }
            )
            logger.info(f"Updated lastLogin for user {user_id}")
        except Exception as update_error:
            # If record doesn't exist, create it
            logger.warning(f"User record not found, creating new record for {user_id}")
            users_table.put_item(
                Item={
                    'userId': user_id,
                    'lastLogin': current_time,
                    'createdAt': current_time,
                    'updatedAt': current_time
                }
            )
        
        return _create_response(200, {
            'message': 'Login tracked successfully',
            'userId': user_id,
            'lastLogin': current_time
        })
        
    except Exception as e:
        logger.error(f"Error tracking login: {str(e)}")
        return _create_response(500, {'error': f'Failed to track login: {str(e)}'})

def _create_user(user_data: Dict):
    """
    Create a new user in Cognito and DynamoDB
    Expected fields: firstName, lastName, email, phone, password, role, status
    """
    try:
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'role']
        for field in required_fields:
            if not user_data.get(field):
                return _create_response(400, {'error': f'Missing required field: {field}'})
        
        # Validate email format
        email = user_data['email'].strip().lower()
        if '@' not in email:
            return _create_response(400, {'error': 'Invalid email format'})
        
        # Map frontend roles to Cognito groups
        role_mapping = {
            'consumer': 'consumers',
            'consumers': 'consumers',
            'technician': 'technicians',
            'technicians': 'technicians', 
            'admin': 'administrators',
            'administrator': 'administrators',
            'administrators': 'administrators',
            'inventory_manager': 'inventory_managers',
            'inventory_managers': 'inventory_managers',
            'warehouse_manager': 'warehouse_managers',
            'warehouse_managers': 'warehouse_managers',
            'supplier_coordinator': 'supplier_coordinators',
            'supplier_coordinators': 'supplier_coordinators',
            'procurement_controller': 'procurement_controllers',
            'procurement_controllers': 'procurement_controllers'
        }
        
        role = user_data.get('role', 'consumer').lower()
        cognito_group = role_mapping.get(role, 'consumers')
        
        # Use provided password or generate a secure temporary password
        if user_data.get('password'):
            temp_password = user_data['password']
        else:
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(12))
        
        # Construct full name for Cognito
        full_name = f"{user_data['firstName']} {user_data['lastName']}"
        
        # Create user in Cognito
        user_attributes = [
            {'Name': 'email', 'Value': email},
            {'Name': 'name', 'Value': full_name},
            {'Name': 'email_verified', 'Value': 'true'}
        ]
        
        # Add phone if provided
        if user_data.get('phone'):
            phone = user_data['phone'].strip()
            if phone:
                user_attributes.append({'Name': 'phone_number', 'Value': phone})
        
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=user_attributes,
            TemporaryPassword=temp_password,
            MessageAction='SUPPRESS',  # Don't send email (we'll handle it manually if needed)
            DesiredDeliveryMediums=['EMAIL']  # Specify email as delivery medium
        )
        
        # Get the user sub (unique ID) from Cognito response
        user_sub = None
        for attr in response['User']['Attributes']:
            if attr['Name'] == 'sub':
                user_sub = attr['Value']
                break
        
        # Add user to appropriate Cognito group
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=email,
                GroupName=cognito_group
            )
            logger.info(f"Added user {email} to group {cognito_group}")
        except Exception as group_error:
            logger.warning(f"Failed to add user to group {cognito_group}: {str(group_error)}")
            # Continue - user can still sign in without group
        
        # Set password as permanent (admin-created users can login immediately)
        try:
            cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=email,
                Password=temp_password,
                Permanent=True  # Set as permanent so user status is CONFIRMED
            )
            logger.info(f"Set permanent password for user {email}")
        except Exception as password_error:
            logger.warning(f"Failed to set password: {str(password_error)}")
        
        # Create user profile in DynamoDB
        try:
            users_table = dynamodb.Table(USERS_TABLE)
            user_profile = {
                'userId': user_sub or email,
                'email': email,
                'firstName': user_data['firstName'],
                'lastName': user_data['lastName'],
                'phone': user_data.get('phone', ''),
                'role': role,
                'status': user_data.get('status', 'active'),
                'createdAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            }
            
            users_table.put_item(Item=user_profile)
            logger.info(f"Created user profile in DynamoDB for {email}")
        except Exception as db_error:
            logger.warning(f"Failed to create user profile in DynamoDB: {str(db_error)}")
            # Continue - Cognito user is created
        
        # Return success response with user data
        return _create_response(201, {
            'message': 'User created successfully',
            'user': {
                'userId': user_sub or email,
                'email': email,
                'firstName': user_data['firstName'],
                'lastName': user_data['lastName'],
                'phone': user_data.get('phone', ''),
                'role': role,
                'status': user_data.get('status', 'active'),
                'createdAt': datetime.utcnow().isoformat()
            },
            'temporaryPassword': temp_password if not user_data.get('password') else None,
            'instructions': 'User must change password on first login' if not user_data.get('password') else 'User can login with provided password'
        })
        
    except cognito_client.exceptions.UsernameExistsException:
        logger.error(f"User already exists: {user_data.get('email')}")
        return _create_response(409, {'error': 'User with this email already exists'})
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
    Update an existing user in both Cognito and DynamoDB
    """
    try:
        # Update Cognito attributes
        cognito_attributes = []
        if 'name' in user_data:
            cognito_attributes.append({'Name': 'name', 'Value': user_data['name']})
        if 'email' in user_data:
            cognito_attributes.append({'Name': 'email', 'Value': user_data['email']})
        if 'phone' in user_data:
            # Cognito uses 'phone_number' not 'phone'
            cognito_attributes.append({'Name': 'phone_number', 'Value': user_data['phone']})
            
        if cognito_attributes:
            cognito_client.admin_update_user_attributes(
                UserPoolId=USER_POOL_ID,
                Username=user_id,
                UserAttributes=cognito_attributes
            )
            logger.info(f"Updated Cognito attributes for user {user_id}: {[attr['Name'] for attr in cognito_attributes]}")
        
        # Update user status if provided
        if 'enabled' in user_data:
            if user_data['enabled']:
                cognito_client.admin_enable_user(UserPoolId=USER_POOL_ID, Username=user_id)
            else:
                cognito_client.admin_disable_user(UserPoolId=USER_POOL_ID, Username=user_id)
            logger.info(f"Updated enabled status for user {user_id}: {user_data['enabled']}")
        
        # Update DynamoDB Users table (where profile data is stored)
        users_table = dynamodb.Table(USERS_TABLE)
        update_expression_parts = []
        expression_values = {}
        
        # Map frontend fields to DynamoDB fields
        if 'firstName' in user_data:
            update_expression_parts.append("firstName = :firstName")
            expression_values[':firstName'] = user_data['firstName']
        
        if 'lastName' in user_data:
            update_expression_parts.append("lastName = :lastName")
            expression_values[':lastName'] = user_data['lastName']
        
        if 'phone' in user_data:
            update_expression_parts.append("phone = :phone")
            expression_values[':phone'] = user_data['phone']
        
        if 'email' in user_data:
            update_expression_parts.append("email = :email")
            expression_values[':email'] = user_data['email']
        
        # Always update the updatedAt timestamp
        update_expression_parts.append("updatedAt = :updatedAt")
        expression_values[':updatedAt'] = datetime.utcnow().isoformat()
        
        # Only update DynamoDB if there are fields to update
        if update_expression_parts:
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            logger.info(f"Updated DynamoDB profile for user {user_id}")
        
        return _create_response(200, {'message': 'User updated successfully'})
        
    except ClientError as e:
        logger.error(f"AWS error updating user {user_id}: {str(e)}")
        return _create_response(500, {'error': 'Failed to update user', 'message': str(e)})
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
        return _create_response(500, {'error': 'Failed to update user', 'message': str(e)})

def _delete_user(user_id: str):
    """
    Delete a user from both Cognito and DynamoDB
    """
    try:
        # Delete from Cognito (this is the source of truth)
        cognito_client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=user_id
        )
        logger.info(f"Deleted user {user_id} from Cognito")
        
        # Clean up DynamoDB profile (best effort - don't fail if it doesn't exist)
        try:
            users_table = dynamodb.Table(USERS_TABLE)
            users_table.delete_item(Key={'userId': user_id})
            logger.info(f"Deleted user profile {user_id} from DynamoDB")
        except Exception as db_error:
            logger.warning(f"Failed to delete user profile from DynamoDB: {str(db_error)}")
            # Continue - Cognito deletion is what matters
        
        return _create_response(200, {'message': 'User deleted successfully'})
        
    except cognito_client.exceptions.UserNotFoundException:
        logger.error(f"User not found: {user_id}")
        return _create_response(404, {'error': 'User not found'})
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
    Create standardized API response with proper CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Admin-Password,x-admin-password',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Max-Age': '86400'
        },
        'body': json.dumps(body)
    }


def _handle_system_metrics(method: str):
    """
    Handle system metrics requests - fetch real-time data from AWS services
    """
    if method != 'GET':
        return _create_response(405, {'error': 'Method not allowed'})
    
    try:
        # Get basic metrics from Cognito and CloudWatch
        # Count users from Cognito
        try:
            users_response = cognito_client.list_users(
                UserPoolId=USER_POOL_ID,
                Limit=60
            )
            total_users = len(users_response.get('Users', []))
        except Exception as e:
            logger.warning(f"Failed to get user count: {str(e)}")
            total_users = 0
        
        # Get CloudWatch metrics for API Gateway (if available)
        try:
            # Get API success rate from CloudWatch
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            # This is a simplified version - in production you'd query actual CloudWatch metrics
            api_success_rate = 99.2  # Default value
            system_uptime = 99.7  # Default value
            
        except Exception as e:
            logger.warning(f"Failed to get CloudWatch metrics: {str(e)}")
            api_success_rate = 99.0
            system_uptime = 99.5
        
        # Compile response
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'users': {
                'total': total_users
            },
            'api': {
                'successRate': api_success_rate,
                'avgResponseTime': 250  # milliseconds
            },
            'system': {
                'uptime': system_uptime,
                'status': 'Operational' if system_uptime > 99.0 else 'Degraded'
            }
        }
        
        return _create_response(200, metrics)
        
    except Exception as e:
        logger.error(f"Error fetching system metrics: {str(e)}")
        return _create_response(500, {
            'error': 'Failed to fetch system metrics',
            'message': str(e)
        })


# ============================================================================
# SECURE PII ACCESS ENDPOINT (Audit Logged)
# ============================================================================

def _get_sensitive_user_data(user_id: str, admin_id: str, ip_address: str, admin_password: str = None):
    """
    Retrieve full unmasked PII for a specific user
    SECURITY: This action is audit logged. Password verification removed for MVP.
    
    Security Model:
    - JWT authentication (admin role required) - enforced by API Gateway
    - Audit logging (immutable record) - all PII access is logged
    - 5-minute session timeout - enforced on frontend
    
    NOTE: For production, consider adding password verification via API Gateway configuration
    """
    try:
        # Fetch full user data from DynamoDB
        users_table = dynamodb.Table(USERS_TABLE)
        response = users_table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            return _create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        
        # Log PII access in audit table (immutable record)
        _log_pii_access(
            admin_id=admin_id,
            target_user_id=user_id,
            action='REVEAL_SENSITIVE_DATA',
            ip_address=ip_address,
            details={'password_verification': False, 'method': 'jwt_only'}
        )
        
        # Return full unmasked data
        return _create_response(200, {
            'userId': user_id,
            'email': user_data.get('email', ''),
            'phone': user_data.get('phone', ''),
            'lastName': user_data.get('lastName', ''),
            'revealedAt': datetime.utcnow().isoformat() + 'Z',
            'expiresIn': 300  # 5 minutes in seconds
        })
        
    except Exception as e:
        logger.error(f"Error retrieving sensitive data: {str(e)}")
        return _create_response(500, {'error': 'Failed to retrieve sensitive data'})


def _log_pii_access(admin_id: str, target_user_id: str, action: str, ip_address: str, details: dict = None):
    """
    Log PII access to immutable audit ledger
    SECURITY: Append-only, no updates or deletes allowed
    """
    try:
        audit_table = dynamodb.Table(AUDIT_TABLE)
        
        audit_entry = {
            'audit_id': f"audit-{datetime.utcnow().timestamp()}",
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'adminId': admin_id,
            'targetUserId': target_user_id,
            'action': action,
            'ipAddress': ip_address,
            'details': details or {},
            'immutable': True  # Flag to prevent modifications
        }
        
        audit_table.put_item(Item=audit_entry)
        logger.info(f"Audit log created: {action} by {admin_id} on {target_user_id}")
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to log audit entry: {str(e)}")
        # Don't fail the operation, but log the error


# ============================================================================
# CONFIGURATION VERSIONING & HISTORY
# ============================================================================

def _calculate_config_diff(old_config: Dict, new_config: Dict) -> Dict:
    """
    Calculate differences between old and new configuration
    Returns a dict of changes with old and new values
    """
    changes = {}
    
    def compare_nested(old_dict, new_dict, path=""):
        for key in set(list(old_dict.keys()) + list(new_dict.keys())):
            if key in ['config_id', 'updated_at', 'updated_by', 'version']:
                continue  # Skip metadata fields
            
            current_path = f"{path}.{key}" if path else key
            old_value = old_dict.get(key)
            new_value = new_dict.get(key)
            
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                compare_nested(old_value, new_value, current_path)
            elif old_value != new_value:
                changes[current_path] = {
                    'old': old_value,
                    'new': new_value
                }
    
    compare_nested(old_config, new_config)
    return changes


def _get_configuration_history(query_params: Dict):
    """
    Get configuration version history
    """
    try:
        limit = int(query_params.get('limit', 50))
        
        history_table = dynamodb.Table(CONFIG_HISTORY_TABLE)
        
        # Query all versions for SYSTEM_CONFIG, sorted by version (timestamp) descending
        response = history_table.query(
            KeyConditionExpression='configId = :configId',
            ExpressionAttributeValues={':configId': 'SYSTEM_CONFIG'},
            ScanIndexForward=False,  # Descending order (newest first)
            Limit=limit
        )
        
        history = []
        for item in response.get('Items', []):
            history.append({
                'version': item.get('version'),
                'updatedBy': item.get('updatedBy'),
                'updatedAt': item.get('updatedAt'),
                'previousVersion': item.get('previousVersion'),
                'changes': item.get('changes', {}),
                'ipAddress': item.get('ipAddress', 'unknown')
            })
        
        return _create_response(200, {
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error fetching configuration history: {str(e)}")
        return _create_response(500, {
            'error': 'Failed to fetch configuration history',
            'message': str(e)
        })


def _validate_configuration_endpoint(config: Dict):
    """
    Validate configuration without saving
    """
    try:
        is_valid, errors = validate_configuration(config)
        
        return _create_response(200, {
            'valid': is_valid,
            'errors': errors if not is_valid else []
        })
        
    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        return _create_response(500, {
            'error': 'Validation failed',
            'message': str(e)
        })


def _rollback_configuration(body: Dict, query_params: Dict):
    """
    Rollback configuration to a previous version
    """
    try:
        target_version = body.get('version')
        if not target_version:
            return _create_response(400, {'error': 'Version is required'})
        
        # Get admin info for audit logging
        admin_id = query_params.get('adminId', 'unknown')
        ip_address = query_params.get('ipAddress', 'unknown')
        
        # Fetch the target version from history
        history_table = dynamodb.Table(CONFIG_HISTORY_TABLE)
        response = history_table.get_item(
            Key={
                'configId': 'SYSTEM_CONFIG',
                'version': target_version
            }
        )
        
        if 'Item' not in response:
            return _create_response(404, {'error': 'Version not found'})
        
        target_config = response['Item'].get('fullConfig')
        if not target_config:
            return _create_response(500, {'error': 'Configuration data not found in version'})
        
        # Get current configuration for diff
        config_table = dynamodb.Table(CONFIG_TABLE)
        current_response = config_table.get_item(Key={'config_id': 'system_config'})
        current_config = current_response.get('Item', {}) if 'Item' in current_response else {}
        current_version = current_config.get('version', 'unknown')
        
        # Calculate changes
        changes = _calculate_config_diff(current_config, target_config)
        
        # Create new version for the rollback
        rollback_timestamp = datetime.utcnow().isoformat()
        rollback_version_id = f"v_{rollback_timestamp}"
        
        # Save rollback as new version in history
        history_entry = {
            'configId': 'SYSTEM_CONFIG',
            'version': rollback_version_id,
            'updatedBy': admin_id,
            'updatedAt': rollback_timestamp,
            'previousVersion': current_version,
            'changes': changes,
            'fullConfig': target_config,
            'ipAddress': ip_address,
            'rollbackFrom': current_version,
            'rollbackTo': target_version
        }
        history_table.put_item(Item=history_entry)
        
        # Update current configuration
        target_config['config_id'] = 'system_config'
        target_config['version'] = rollback_version_id
        target_config['updated_at'] = rollback_timestamp
        target_config['updated_by'] = admin_id
        
        config_table.put_item(Item=target_config)
        
        # Log audit entry
        _log_config_change(
            admin_id=admin_id,
            action='ROLLBACK_SYSTEM_CONFIG',
            ip_address=ip_address,
            changes={
                'rollbackFrom': current_version,
                'rollbackTo': target_version,
                'changes': changes
            },
            version=rollback_version_id
        )
        
        logger.info(f"Configuration rolled back by {admin_id} from {current_version} to {target_version}")
        
        return _create_response(200, {
            'message': 'Configuration rolled back successfully',
            'version': rollback_version_id,
            'rolledBackFrom': current_version,
            'rolledBackTo': target_version,
            'changes': changes
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error during rollback: {str(e)}")
        return _create_response(500, {
            'error': 'Database error occurred',
            'message': str(e)
        })
    except Exception as e:
        logger.error(f"Error rolling back configuration: {str(e)}", exc_info=True)
        return _create_response(500, {
            'error': 'Failed to rollback configuration',
            'message': str(e)
        })


def _log_config_change(admin_id: str, action: str, ip_address: str, changes: Dict, version: str):
    """
    Log configuration changes to audit table
    """
    try:
        audit_table = dynamodb.Table(AUDIT_TABLE)
        
        audit_entry = {
            'audit_id': f"config-audit-{datetime.utcnow().timestamp()}",
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'adminId': admin_id,
            'action': action,
            'ipAddress': ip_address,
            'details': {
                'version': version,
                'changes': changes
            },
            'immutable': True
        }
        
        audit_table.put_item(Item=audit_entry)
        logger.info(f"Config change audit log created: {action} by {admin_id}, version: {version}")
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to log config change audit: {str(e)}")
        # Don't fail the operation, but log the error
