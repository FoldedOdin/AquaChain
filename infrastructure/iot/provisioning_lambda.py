"""
Lambda function for Just-in-Time device provisioning
Validates device credentials and approves/denies provisioning requests
"""

import json
import boto3
import hashlib
import hmac
from typing import Dict, Any, Optional

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Pre-provisioning hook for device validation
    """
    print(f"Provisioning event: {json.dumps(event)}")
    
    try:
        # Extract device information from the event
        parameters = event.get('parameters', {})
        device_id = parameters.get('DeviceId')
        serial_number = parameters.get('SerialNumber')
        certificate_id = event.get('certificateId')
        
        if not device_id or not serial_number:
            return create_response(False, "Missing required parameters")
        
        # Validate device credentials
        if not validate_device_credentials(device_id, serial_number):
            return create_response(False, "Invalid device credentials")
        
        # Check if device is already registered
        if is_device_registered(device_id):
            return create_response(False, "Device already registered")
        
        # Validate serial number format
        if not validate_serial_number_format(serial_number):
            return create_response(False, "Invalid serial number format")
        
        # Additional security checks
        if not perform_security_checks(device_id, serial_number, certificate_id):
            return create_response(False, "Security validation failed")
        
        # Log successful provisioning attempt
        log_provisioning_attempt(device_id, serial_number, certificate_id, True)
        
        # Return success with additional parameters
        return create_response(True, "Device approved for provisioning", {
            'location': 'unknown',
            'provisioningDate': get_current_timestamp(),
            'firmwareVersion': '1.0.0'
        })
        
    except Exception as e:
        print(f"Error in provisioning hook: {str(e)}")
        log_provisioning_attempt(
            parameters.get('DeviceId', 'unknown'),
            parameters.get('SerialNumber', 'unknown'),
            event.get('certificateId', 'unknown'),
            False,
            str(e)
        )
        return create_response(False, f"Internal error: {str(e)}")

def create_response(allow_provisioning: bool, message: str, 
                   additional_parameters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create standardized response for provisioning hook
    """
    response = {
        'allowProvisioning': allow_provisioning,
        'parameterOverrides': additional_parameters or {}
    }
    
    print(f"Provisioning response: {message} - Allow: {allow_provisioning}")
    return response

def validate_device_credentials(device_id: str, serial_number: str) -> bool:
    """
    Validate device credentials against expected format and database
    """
    try:
        # Check device ID format (DEV-XXXX)
        if not device_id.startswith('DEV-') or len(device_id) != 8:
            print(f"Invalid device ID format: {device_id}")
            return False
        
        # Check serial number format (AQ-YYYYMMDD-XXXX)
        if not serial_number.startswith('AQ-') or len(serial_number) != 16:
            print(f"Invalid serial number format: {serial_number}")
            return False
        
        # Validate checksum in serial number
        if not validate_serial_checksum(serial_number):
            print(f"Invalid serial number checksum: {serial_number}")
            return False
        
        # Check against device registry (DynamoDB)
        return check_device_registry(device_id, serial_number)
        
    except Exception as e:
        print(f"Error validating device credentials: {e}")
        return False

def validate_serial_number_format(serial_number: str) -> bool:
    """
    Validate serial number format and checksum
    """
    try:
        # Format: AQ-YYYYMMDD-XXXX
        parts = serial_number.split('-')
        if len(parts) != 3:
            return False
        
        prefix, date_part, suffix = parts
        
        # Validate prefix
        if prefix != 'AQ':
            return False
        
        # Validate date part (YYYYMMDD)
        if len(date_part) != 8 or not date_part.isdigit():
            return False
        
        # Validate suffix (4 hex digits)
        if len(suffix) != 4:
            return False
        
        try:
            int(suffix, 16)  # Check if valid hex
        except ValueError:
            return False
        
        return True
        
    except Exception as e:
        print(f"Error validating serial number format: {e}")
        return False

def validate_serial_checksum(serial_number: str) -> bool:
    """
    Validate serial number checksum using HMAC
    """
    try:
        # Extract components
        parts = serial_number.split('-')
        date_part = parts[1]
        suffix = parts[2]
        
        # Get secret key from environment or Secrets Manager
        secret_key = get_device_secret_key()
        
        # Calculate expected checksum
        data_to_hash = f"AQ-{date_part}"
        expected_checksum = hmac.new(
            secret_key.encode(),
            data_to_hash.encode(),
            hashlib.sha256
        ).hexdigest()[:4].upper()
        
        return suffix.upper() == expected_checksum
        
    except Exception as e:
        print(f"Error validating serial checksum: {e}")
        return False

def check_device_registry(device_id: str, serial_number: str) -> bool:
    """
    Check if device exists in the authorized device registry
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('aquachain-device-registry')
        
        response = table.get_item(
            Key={
                'deviceId': device_id,
                'serialNumber': serial_number
            }
        )
        
        if 'Item' not in response:
            print(f"Device not found in registry: {device_id}")
            return False
        
        device_record = response['Item']
        
        # Check if device is authorized for provisioning
        if device_record.get('status') != 'authorized':
            print(f"Device not authorized: {device_id}")
            return False
        
        # Check if device is already provisioned
        if device_record.get('provisioned', False):
            print(f"Device already provisioned: {device_id}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error checking device registry: {e}")
        return False

def is_device_registered(device_id: str) -> bool:
    """
    Check if device is already registered in IoT Core
    """
    try:
        iot_client = boto3.client('iot')
        
        try:
            iot_client.describe_thing(thingName=device_id)
            return True  # Thing exists
        except iot_client.exceptions.ResourceNotFoundException:
            return False  # Thing doesn't exist
        
    except Exception as e:
        print(f"Error checking device registration: {e}")
        return True  # Fail safe - assume registered to prevent duplicate

def perform_security_checks(device_id: str, serial_number: str, certificate_id: str) -> bool:
    """
    Perform additional security validations
    """
    try:
        # Check for suspicious patterns
        if device_id.lower() in ['test', 'admin']:
            print(f"Suspicious device ID: {device_id}")
            return False
        
        # Rate limiting check
        if check_provisioning_rate_limit(device_id):
            print(f"Rate limit exceeded for device: {device_id}")
            return False
        
        # Certificate validation
        if not validate_certificate_properties(certificate_id):
            print(f"Certificate validation failed: {certificate_id}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error in security checks: {e}")
        return False

def check_provisioning_rate_limit(device_id: str) -> bool:
    """
    Check if device has exceeded provisioning rate limits
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('aquachain-provisioning-attempts')
        
        # Check attempts in last hour
        current_time = get_current_timestamp()
        one_hour_ago = current_time - 3600
        
        response = table.query(
            KeyConditionExpression='deviceId = :device_id AND #timestamp > :time_limit',
            ExpressionAttributeNames={'#timestamp': 'timestamp'},
            ExpressionAttributeValues={
                ':device_id': device_id,
                ':time_limit': one_hour_ago
            }
        )
        
        # Allow maximum 3 attempts per hour
        return len(response['Items']) >= 3
        
    except Exception as e:
        print(f"Error checking rate limit: {e}")
        return False

def validate_certificate_properties(certificate_id: str) -> bool:
    """
    Validate certificate properties and constraints
    """
    try:
        iot_client = boto3.client('iot')
        
        response = iot_client.describe_certificate(certificateId=certificate_id)
        certificate = response['certificateDescription']
        
        # Check certificate status
        if certificate['status'] != 'ACTIVE':
            return False
        
        # Check certificate validity period
        # Add additional certificate validation logic here
        
        return True
        
    except Exception as e:
        print(f"Error validating certificate: {e}")
        return False

def log_provisioning_attempt(device_id: str, serial_number: str, certificate_id: str,
                           success: bool, error_message: str = None):
    """
    Log provisioning attempt for audit and monitoring
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('aquachain-provisioning-attempts')
        
        item = {
            'deviceId': device_id,
            'timestamp': get_current_timestamp(),
            'serialNumber': serial_number,
            'certificateId': certificate_id,
            'success': success,
            'errorMessage': error_message
        }
        
        table.put_item(Item=item)
        
    except Exception as e:
        print(f"Error logging provisioning attempt: {e}")

def get_device_secret_key() -> str:
    """
    Get device secret key from AWS Secrets Manager
    """
    try:
        secrets_client = boto3.client('secretsmanager')
        
        response = secrets_client.get_secret_value(
            SecretId='aquachain/device-provisioning-key'
        )
        
        return response['SecretString']
        
    except Exception as e:
        print(f"Error getting secret key: {e}")
        # Fallback to environment variable (not recommended for production)
        import os
        return os.environ.get('DEVICE_SECRET_KEY', 'default-key')

def get_current_timestamp() -> int:
    """
    Get current Unix timestamp
    """
    import time
    return int(time.time())

def mark_device_as_provisioned(device_id: str, serial_number: str):
    """
    Mark device as provisioned in the registry
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('aquachain-device-registry')
        
        table.update_item(
            Key={
                'deviceId': device_id,
                'serialNumber': serial_number
            },
            UpdateExpression='SET provisioned = :provisioned, provisionedAt = :timestamp',
            ExpressionAttributeValues={
                ':provisioned': True,
                ':timestamp': get_current_timestamp()
            }
        )
        
    except Exception as e:
        print(f"Error marking device as provisioned: {e}")

# Example event structure for testing
EXAMPLE_EVENT = {
    "certificateId": "example-cert-id",
    "parameters": {
        "DeviceId": "DEV-1234",
        "SerialNumber": "AQ-20251019-A1B2"
    }
}