"""
Example integration of security features into AquaChain Lambda functions.
Shows how to use security middleware, audit logging, and encryption together.
Requirements: 8.5, 15.5, 2.4, 15.1
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

# Import our security components
from .security_middleware import secure_endpoint, auth_endpoint, InputValidator
from .audit_logger import audit_user_action, audit_data_access, AuditEventType, AuditSeverity
from .encryption_manager import encrypt_sensitive_data, decrypt_sensitive_data
from ..auth_service.auth_utils import require_auth

from structured_logger import get_logger

logger = get_logger(__name__, service='security-integration')

# Example 1: Secure user registration endpoint
@auth_endpoint(rate_limit=5, require_captcha=True)  # Strict security for auth
@audit_user_action(AuditEventType.USER_REGISTRATION, ['user_management', 'registration'])
def user_registration_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example of secure user registration with comprehensive security controls.
    """
    try:
        # Input validation is handled by security middleware
        body = json.loads(event['body'])
        
        # Validate specific fields
        validator = InputValidator()
        email = validator.validate_email(body['email'])
        phone = validator.validate_phone(body.get('phone', ''))
        
        # Encrypt sensitive user data
        user_data = {
            'email': email,
            'phone': phone,
            'firstName': body.get('firstName', ''),
            'lastName': body.get('lastName', ''),
            'address': body.get('address', {})
        }
        
        encrypted_user_data = encrypt_sensitive_data(user_data, 'user_data')
        
        # Store user with encrypted data
        # (DynamoDB operations would go here)
        
        # Return success response (no sensitive data)
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'User registered successfully',
                'userId': 'generated-user-id'
            })
        }
        
    except Exception as e:
        logger.error(f"User registration error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Registration failed'})
        }

# Example 2: Secure data access endpoint
@secure_endpoint(rate_limit=100)  # Standard rate limiting
@require_auth(resource='readings', action='read')  # Authentication required
@audit_data_access('sensor_readings', ['data_access', 'sensor_data'])
def get_device_readings_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example of secure device readings access with audit logging.
    """
    try:
        # User context is provided by auth middleware
        user_context = event['userContext']
        device_id = event['pathParameters']['deviceId']
        
        # Validate device access
        if not _user_can_access_device(user_context, device_id):
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Access denied to device'})
            }
        
        # Retrieve encrypted readings from database
        # (This would be actual DynamoDB query)
        encrypted_readings = _get_encrypted_readings(device_id)
        
        # Decrypt readings for response
        decrypted_readings = []
        for encrypted_reading in encrypted_readings:
            try:
                reading_data = decrypt_sensitive_data(encrypted_reading, 'sensor_data')
                decrypted_readings.append(reading_data)
            except Exception as e:
                logger.error(f"Failed to decrypt reading: {e}")
                # Skip corrupted readings rather than failing entirely
                continue
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'deviceId': device_id,
                'readings': decrypted_readings,
                'count': len(decrypted_readings)
            })
        }
        
    except Exception as e:
        logger.error(f"Get readings error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to retrieve readings'})
        }

# Example 3: Admin endpoint with comprehensive security
@secure_endpoint(rate_limit=20)  # Lower rate limit for admin functions
@require_auth(resource='system', action='read')
@audit_user_action(AuditEventType.ADMIN_ACTION, ['admin_activity', 'system_management'])
def admin_system_status_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example of admin endpoint with comprehensive security and audit logging.
    """
    try:
        user_context = event['userContext']
        
        # Verify admin access
        if user_context.get('role') != 'administrators':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Administrator access required'})
            }
        
        # Collect system status (this would be real system checks)
        system_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'api_gateway': 'healthy',
                'lambda_functions': 'healthy',
                'dynamodb': 'healthy',
                'encryption': 'healthy'
            },
            'metrics': {
                'active_devices': 150,
                'daily_readings': 12500,
                'alert_count': 3
            }
        }
        
        # Encrypt sensitive system data before logging
        encrypted_status = encrypt_sensitive_data(system_status, 'sensor_data')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(system_status)
        }
        
    except Exception as e:
        logger.error(f"Admin system status error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to retrieve system status'})
        }

# Example 4: Data export with compliance tracking
@secure_endpoint(rate_limit=10)  # Very low rate limit for data export
@require_auth(resource='audit', action='read')
@audit_user_action(AuditEventType.DATA_EXPORT, ['data_export', 'compliance', 'gdpr'])
def export_user_data_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example of data export endpoint with compliance tracking.
    """
    try:
        user_context = event['userContext']
        export_user_id = event['pathParameters']['userId']
        
        # Verify user can export this data
        if (user_context.get('role') not in ['administrators'] and 
            user_context.get('userId') != export_user_id):
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Cannot export other user data'})
            }
        
        # Collect user data from various sources
        user_export_data = {
            'user_profile': _get_user_profile(export_user_id),
            'device_readings': _get_user_readings(export_user_id),
            'service_requests': _get_user_service_requests(export_user_id),
            'export_metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': user_context.get('userId'),
                'export_reason': event.get('queryStringParameters', {}).get('reason', 'user_request')
            }
        }
        
        # Create secure backup of export data
        from .encryption_manager import encryption_manager
        backup_info = encryption_manager.create_secure_backup(
            user_export_data, 
            f"user_export_{export_user_id}_{int(datetime.utcnow().timestamp())}"
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Data export completed',
                'export_id': backup_info['backup_name'],
                'created_at': backup_info['created_at'],
                'download_url': f"/api/v1/exports/{backup_info['backup_name']}"
            })
        }
        
    except Exception as e:
        logger.error(f"Data export error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Data export failed'})
        }

# Example 5: IoT data ingestion with validation and encryption
@secure_endpoint(rate_limit=1000)  # High rate limit for IoT data
def iot_data_ingestion_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example of IoT data ingestion with comprehensive validation and encryption.
    """
    try:
        # Parse IoT device data
        body = json.loads(event['body'])
        
        # Validate device data structure
        validator = InputValidator()
        
        device_id = validator.validate_device_id(body['deviceId'])
        
        # Validate sensor readings
        readings = body['readings']
        validated_readings = {}
        
        for sensor_type, value in readings.items():
            if sensor_type in ['pH', 'turbidity', 'tds', 'temperature', 'humidity']:
                validated_readings[sensor_type] = validator.validate_sensor_reading(sensor_type, value)
        
        # Validate GPS coordinates
        location = body['location']
        lat, lon = validator.validate_coordinates(location['latitude'], location['longitude'])
        
        # Create processed reading data
        processed_reading = {
            'deviceId': device_id,
            'timestamp': datetime.utcnow().isoformat(),
            'readings': validated_readings,
            'location': {'latitude': lat, 'longitude': lon},
            'diagnostics': body.get('diagnostics', {}),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        # Encrypt sensor data before storage
        encrypted_reading = encrypt_sensitive_data(processed_reading, 'sensor_data')
        
        # Store encrypted reading (would be DynamoDB put_item)
        # _store_encrypted_reading(encrypted_reading)
        
        # Create digital signature for data integrity
        from .encryption_manager import create_data_signature
        signature = create_data_signature(processed_reading)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Data ingested successfully',
                'deviceId': device_id,
                'timestamp': processed_reading['timestamp'],
                'signature': signature['signature'][:16] + '...'  # Truncated for response
            })
        }
        
    except Exception as e:
        logger.error(f"IoT data ingestion error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid sensor data'})
        }

# Helper functions (these would be implemented with actual database operations)
def _user_can_access_device(user_context: Dict[str, Any], device_id: str) -> bool:
    """Check if user has access to device"""
    if user_context.get('role') == 'administrators':
        return True
    
    user_devices = user_context.get('deviceIds', [])
    return device_id in user_devices

def _get_encrypted_readings(device_id: str) -> list:
    """Get encrypted readings from database"""
    # This would be actual DynamoDB query
    return []

def _get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile data"""
    return {}

def _get_user_readings(user_id: str) -> list:
    """Get user's device readings"""
    return []

def _get_user_service_requests(user_id: str) -> list:
    """Get user's service requests"""
    return []

# Example usage in serverless.yml or SAM template:
"""
functions:
  userRegistration:
    handler: lambda.shared.security_integration_example.user_registration_handler
    environment:
      COGNITO_USER_POOL_ID: ${self:custom.cognitoUserPoolId}
      RECAPTCHA_SECRET_ARN: ${self:custom.recaptchaSecretArn}
    events:
      - http:
          path: /api/v1/auth/register
          method: post
          cors: true

  getDeviceReadings:
    handler: lambda.shared.security_integration_example.get_device_readings_handler
    environment:
      COGNITO_USER_POOL_ID: ${self:custom.cognitoUserPoolId}
    events:
      - http:
          path: /api/v1/readings/{deviceId}
          method: get
          cors: true
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: ${self:custom.cognitoAuthorizerId}

  adminSystemStatus:
    handler: lambda.shared.security_integration_example.admin_system_status_handler
    environment:
      COGNITO_USER_POOL_ID: ${self:custom.cognitoUserPoolId}
    events:
      - http:
          path: /api/v1/admin/system/status
          method: get
          cors: true
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: ${self:custom.cognitoAuthorizerId}
"""