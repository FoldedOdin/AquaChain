# Data Encryption Integration Guide

This guide explains how to integrate field-level encryption into Lambda functions using the data classification schema.

## Overview

The AquaChain system implements automatic field-level encryption based on data classification:

- **PII** (Personally Identifiable Information): Encrypted with dedicated PII KMS key
- **SENSITIVE**: Encrypted with dedicated SENSITIVE KMS key  
- **INTERNAL**: Not encrypted (access controlled)
- **PUBLIC**: Not encrypted (publicly accessible)

## Quick Start

### 1. Environment Variables

Ensure your Lambda function has these environment variables configured:

```bash
PII_KMS_KEY_ID=alias/aquachain-prod-pii-key
SENSITIVE_KMS_KEY_ID=alias/aquachain-prod-sensitive-key
AWS_REGION=us-east-1
```

### 2. IAM Permissions

Your Lambda execution role needs KMS permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ],
      "Resource": [
        "arn:aws:kms:us-east-1:ACCOUNT_ID:key/PII_KEY_ID",
        "arn:aws:kms:us-east-1:ACCOUNT_ID:key/SENSITIVE_KEY_ID"
      ]
    }
  ]
}
```

## Usage Patterns

### Pattern 1: Using EncryptedDynamoDBClient (Recommended)

The easiest way to integrate encryption is using the `EncryptedDynamoDBClient`:

```python
from encrypted_dynamodb import create_encrypted_table_client

# Create encrypted client
users_table = create_encrypted_table_client('Users')

# Store user data - PII fields automatically encrypted
user_data = {
    'user_id': 'user-123',
    'email': 'john@example.com',  # Encrypted (PII)
    'name': 'John Doe',  # Encrypted (PII)
    'phone': '+1234567890',  # Encrypted (PII)
    'role': 'admin',  # Not encrypted (INTERNAL)
    'created_at': '2025-10-25T12:00:00Z'  # Not encrypted
}

users_table.put_item(user_data)

# Retrieve user data - PII fields automatically decrypted
user = users_table.get_item({'user_id': 'user-123'})
print(user['email'])  # Decrypted value
```

### Pattern 2: Manual Field Encryption

For more control, use the `DataEncryptionService` directly:

```python
from data_encryption_service import get_encryption_service

encryption_service = get_encryption_service()

# Encrypt a single field
encrypted_email = encryption_service.encrypt_field('email', 'john@example.com')

# Decrypt a single field
decrypted_email = encryption_service.decrypt_field('email', encrypted_email)

# Encrypt entire record
user_data = {
    'user_id': 'user-123',
    'email': 'john@example.com',
    'name': 'John Doe',
    'role': 'admin'
}
encrypted_record = encryption_service.encrypt_record(user_data)

# Decrypt entire record
decrypted_record = encryption_service.decrypt_record(encrypted_record)
```

### Pattern 3: Selective Field Encryption

Encrypt only specific fields:

```python
from data_encryption_service import get_encryption_service

encryption_service = get_encryption_service()

user_data = {
    'user_id': 'user-123',
    'email': 'john@example.com',
    'name': 'John Doe',
    'phone': '+1234567890',
    'role': 'admin'
}

# Encrypt only email and phone
encrypted_data = encryption_service.encrypt_fields_in_record(
    user_data,
    fields_to_encrypt=['email', 'phone']
)
```

## Integration Examples

### Example 1: User Management Lambda

```python
import json
import os
from encrypted_dynamodb import create_encrypted_table_client
from structured_logger import get_logger

logger = get_logger(__name__, service='user-management')

# Initialize encrypted DynamoDB client
users_table = create_encrypted_table_client(os.environ['USERS_TABLE'])

def lambda_handler(event, context):
    """Create or update user with automatic PII encryption."""
    
    try:
        user_data = json.loads(event['body'])
        
        # Validate required fields
        required_fields = ['user_id', 'email', 'name']
        if not all(field in user_data for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Store user - PII fields automatically encrypted
        users_table.put_item(user_data)
        
        logger.info(f"Created user {user_data['user_id']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User created successfully'})
        }
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def get_user_handler(event, context):
    """Retrieve user with automatic PII decryption."""
    
    try:
        user_id = event['pathParameters']['user_id']
        
        # Get user - PII fields automatically decrypted
        user = users_table.get_item({'user_id': user_id})
        
        if not user:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Remove sensitive fields before returning
        response_data = {
            'user_id': user['user_id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

### Example 2: Device Management Lambda

```python
import json
import os
from encrypted_dynamodb import create_encrypted_table_client
from structured_logger import get_logger

logger = get_logger(__name__, service='device-management')

# Initialize encrypted DynamoDB client
devices_table = create_encrypted_table_client(os.environ['DEVICES_TABLE'])

def register_device_handler(event, context):
    """Register device with automatic SENSITIVE data encryption."""
    
    try:
        device_data = json.loads(event['body'])
        
        # Validate required fields
        required_fields = ['device_id', 'serial_number', 'mac_address']
        if not all(field in device_data for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Store device - SENSITIVE fields automatically encrypted
        # (serial_number, mac_address, location)
        devices_table.put_item(device_data)
        
        logger.info(f"Registered device {device_data['device_id']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Device registered successfully'})
        }
        
    except Exception as e:
        logger.error(f"Failed to register device: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def list_user_devices_handler(event, context):
    """List user's devices with automatic decryption."""
    
    try:
        user_id = event['pathParameters']['user_id']
        
        # Query devices - SENSITIVE fields automatically decrypted
        from boto3.dynamodb.conditions import Key
        devices = devices_table.query(
            key_condition_expression=Key('user_id').eq(user_id)
        )
        
        # Return device list
        return {
            'statusCode': 200,
            'body': json.dumps({
                'devices': devices,
                'count': len(devices)
            })
        }
        
    except Exception as e:
        logger.error(f"Failed to list devices: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

### Example 3: GDPR Export with Encryption

```python
import json
import os
from data_encryption_service import get_encryption_service
from encrypted_dynamodb import create_encrypted_table_client

encryption_service = get_encryption_service()
users_table = create_encrypted_table_client('Users')
devices_table = create_encrypted_table_client('Devices')

def export_user_data_handler(event, context):
    """Export user data with proper decryption for GDPR compliance."""
    
    try:
        user_id = event['pathParameters']['user_id']
        
        # Get user profile - PII automatically decrypted
        user_profile = users_table.get_item({'user_id': user_id})
        
        # Get user devices - SENSITIVE data automatically decrypted
        from boto3.dynamodb.conditions import Key
        user_devices = devices_table.query(
            key_condition_expression=Key('user_id').eq(user_id)
        )
        
        # Compile export data
        export_data = {
            'export_date': '2025-10-25T12:00:00Z',
            'user_id': user_id,
            'profile': user_profile,
            'devices': user_devices
        }
        
        # All data is already decrypted and ready for export
        return {
            'statusCode': 200,
            'body': json.dumps(export_data, indent=2)
        }
        
    except Exception as e:
        logger.error(f"Failed to export user data: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
```

## Data Classification Reference

### PII Fields (Encrypted with PII KMS Key)
- email
- name, first_name, last_name
- phone, phone_number
- address, street_address, city, state, postal_code, country
- date_of_birth
- ssn, tax_id
- credit_card_number, bank_account_number
- billing_address

### SENSITIVE Fields (Encrypted with SENSITIVE KMS Key)
- password_hash
- api_key, access_token, refresh_token, session_id
- mfa_secret
- security_answer
- serial_number
- mac_address, ip_address
- location, latitude, longitude
- export_url

### INTERNAL Fields (Not Encrypted)
- user_id, device_id, organization_id
- role, department, job_title
- timestamps (created_at, updated_at, last_login)
- status, alert_level
- metric values

### PUBLIC Fields (Not Encrypted)
- Water quality metrics (ph_level, temperature, turbidity, etc.)

## Best Practices

### 1. Always Use Encrypted Clients

```python
# ✅ Good - Automatic encryption/decryption
from encrypted_dynamodb import create_encrypted_table_client
table = create_encrypted_table_client('Users')

# ❌ Bad - Manual encryption required
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')
```

### 2. Handle Encryption Errors

```python
from data_encryption_service import DataEncryptionError

try:
    users_table.put_item(user_data)
except DataEncryptionError as e:
    logger.error(f"Encryption failed: {e}")
    # Handle encryption failure appropriately
    return {'statusCode': 500, 'body': 'Encryption error'}
```

### 3. Validate Configuration

```python
from data_encryption_service import get_encryption_service

encryption_service = get_encryption_service()
validation = encryption_service.validate_encryption_configuration()

if not validation['valid']:
    logger.error(f"Encryption not configured: {validation['errors']}")
    raise Exception("Encryption configuration invalid")
```

### 4. Log Encryption Operations

```python
from structured_logger import get_logger

logger = get_logger(__name__, service='my-service')

# Log when handling PII
logger.info(
    "Processing user data",
    extra={
        'user_id': user_id,
        'contains_pii': True,
        'encryption_enabled': True
    }
)
```

## Testing

### Unit Tests

```python
import unittest
from moto import mock_kms, mock_dynamodb
from data_encryption_service import DataEncryptionService

@mock_kms
class TestDataEncryption(unittest.TestCase):
    
    def setUp(self):
        # Create mock KMS keys
        kms = boto3.client('kms', region_name='us-east-1')
        pii_key = kms.create_key(Description='Test PII Key')
        sensitive_key = kms.create_key(Description='Test Sensitive Key')
        
        os.environ['PII_KMS_KEY_ID'] = pii_key['KeyMetadata']['KeyId']
        os.environ['SENSITIVE_KMS_KEY_ID'] = sensitive_key['KeyMetadata']['KeyId']
        
        self.encryption_service = DataEncryptionService()
    
    def test_encrypt_pii_field(self):
        email = 'test@example.com'
        encrypted = self.encryption_service.encrypt_field('email', email)
        
        self.assertNotEqual(encrypted, email)
        self.assertIsInstance(encrypted, str)
    
    def test_decrypt_pii_field(self):
        email = 'test@example.com'
        encrypted = self.encryption_service.encrypt_field('email', email)
        decrypted = self.encryption_service.decrypt_field('email', encrypted)
        
        self.assertEqual(decrypted, email)
```

## Troubleshooting

### Issue: "KMS key not configured"

**Solution**: Ensure environment variables are set:
```bash
export PII_KMS_KEY_ID=alias/aquachain-prod-pii-key
export SENSITIVE_KMS_KEY_ID=alias/aquachain-prod-sensitive-key
```

### Issue: "Access Denied" when encrypting

**Solution**: Add KMS permissions to Lambda execution role:
```json
{
  "Effect": "Allow",
  "Action": ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": ["arn:aws:kms:REGION:ACCOUNT:key/KEY_ID"]
}
```

### Issue: "Decryption failed"

**Possible causes**:
1. Wrong KMS key used for decryption
2. Encryption context mismatch
3. Data corrupted or not actually encrypted

**Solution**: Check logs for specific error and verify field classification.

## Migration Guide

### Migrating Existing Data

To encrypt existing unencrypted data:

```python
from encrypted_dynamodb import create_encrypted_table_client
import boto3

# Old unencrypted table
old_table = boto3.resource('dynamodb').Table('Users')

# New encrypted client
encrypted_table = create_encrypted_table_client('Users')

# Scan and re-encrypt
response = old_table.scan()
for item in response['Items']:
    # Re-write with encryption
    encrypted_table.put_item(item)
```

## Support

For questions or issues:
1. Check CloudWatch logs for encryption errors
2. Validate KMS key configuration
3. Review IAM permissions
4. Contact the security team for key access issues
