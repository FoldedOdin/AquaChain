# Data Classification and Encryption - Quick Reference

## Quick Start

### 1. Use Encrypted DynamoDB Client

```python
from encrypted_dynamodb import create_encrypted_table_client

# Create client
table = create_encrypted_table_client('Users')

# Store with automatic encryption
table.put_item({
    'user_id': 'user-123',
    'email': 'john@example.com',  # Encrypted
    'name': 'John Doe',  # Encrypted
    'role': 'admin'  # Not encrypted
})

# Retrieve with automatic decryption
user = table.get_item({'user_id': 'user-123'})
```

### 2. Manual Field Encryption

```python
from data_encryption_service import encrypt_field, decrypt_field

# Encrypt
encrypted = encrypt_field('email', 'john@example.com')

# Decrypt
decrypted = decrypt_field('email', encrypted)
```

## Classification Levels

| Level | Description | Encryption | Examples |
|-------|-------------|------------|----------|
| **PUBLIC** | Freely shareable | ❌ No | Water quality metrics |
| **INTERNAL** | Internal use only | ❌ No | IDs, timestamps, status |
| **SENSITIVE** | Business critical | ✅ Yes (SENSITIVE key) | Serial numbers, IP addresses, API keys |
| **PII** | Personal data | ✅ Yes (PII key) | Email, name, phone, address |

## Common Fields

### PII Fields (Encrypted)
```python
'email', 'name', 'first_name', 'last_name'
'phone', 'phone_number'
'address', 'street_address', 'city', 'state', 'postal_code'
'date_of_birth', 'ssn', 'tax_id'
'credit_card_number', 'bank_account_number'
```

### SENSITIVE Fields (Encrypted)
```python
'password_hash', 'api_key', 'access_token', 'session_id'
'serial_number', 'mac_address', 'ip_address'
'location', 'latitude', 'longitude'
'export_url'
```

### INTERNAL Fields (Not Encrypted)
```python
'user_id', 'device_id', 'organization_id'
'role', 'status', 'alert_level'
'created_at', 'updated_at', 'timestamp'
```

### PUBLIC Fields (Not Encrypted)
```python
'ph_level', 'temperature', 'turbidity'
'dissolved_oxygen', 'conductivity', 'tds'
```

## Environment Variables

```bash
PII_KMS_KEY_ID=alias/aquachain-prod-pii-key
SENSITIVE_KMS_KEY_ID=alias/aquachain-prod-sensitive-key
AWS_REGION=us-east-1
```

## IAM Permissions

```json
{
  "Effect": "Allow",
  "Action": [
    "kms:Encrypt",
    "kms:Decrypt",
    "kms:GenerateDataKey"
  ],
  "Resource": [
    "arn:aws:kms:REGION:ACCOUNT:key/PII_KEY_ID",
    "arn:aws:kms:REGION:ACCOUNT:key/SENSITIVE_KEY_ID"
  ]
}
```

## Common Operations

### Store User (PII)
```python
users_table = create_encrypted_table_client('Users')
users_table.put_item({
    'user_id': 'user-123',
    'email': 'john@example.com',  # Auto-encrypted
    'name': 'John Doe',  # Auto-encrypted
    'role': 'admin'
})
```

### Store Device (SENSITIVE)
```python
devices_table = create_encrypted_table_client('Devices')
devices_table.put_item({
    'device_id': 'device-456',
    'serial_number': 'SN123',  # Auto-encrypted
    'mac_address': '00:11:22:33:44:55',  # Auto-encrypted
    'status': 'active'
})
```

### Update with Encryption
```python
users_table.update_item(
    key={'user_id': 'user-123'},
    update_expression='SET email = :email',
    expression_attribute_values={
        ':email': 'new@example.com'  # Auto-encrypted
    }
)
```

### Query with Decryption
```python
from boto3.dynamodb.conditions import Key

users = users_table.query(
    key_condition_expression=Key('organization_id').eq('org-789')
)
# All PII fields auto-decrypted
```

## Error Handling

```python
from data_encryption_service import DataEncryptionError

try:
    table.put_item(user_data)
except DataEncryptionError as e:
    logger.error(f"Encryption failed: {e}")
    # Handle encryption error
```

## Validation

```python
from data_encryption_service import get_encryption_service

service = get_encryption_service()
validation = service.validate_encryption_configuration()

if not validation['valid']:
    print("Errors:", validation['errors'])
```

## Helper Functions

```python
from data_classification import (
    get_field_classification,
    requires_encryption,
    is_gdpr_subject_data
)

# Check classification
classification = get_field_classification('email')
# Returns: DataClassification.PII

# Check if encryption required
needs_encryption = requires_encryption('email')
# Returns: True

# Check if GDPR subject data
is_gdpr = is_gdpr_subject_data('email')
# Returns: True
```

## Troubleshooting

### "KMS key not configured"
```bash
export PII_KMS_KEY_ID=alias/aquachain-prod-pii-key
export SENSITIVE_KMS_KEY_ID=alias/aquachain-prod-sensitive-key
```

### "Access Denied"
Add KMS permissions to Lambda execution role.

### "Decryption failed"
Check that field was encrypted with correct key.

## Best Practices

1. ✅ Always use `EncryptedDynamoDBClient`
2. ✅ Validate encryption configuration on startup
3. ✅ Log encryption operations
4. ✅ Handle `DataEncryptionError` exceptions
5. ❌ Don't cache encrypted data
6. ❌ Don't log decrypted PII values

## Files

- **Classification Schema**: `lambda/shared/data_classification.py`
- **Encryption Service**: `lambda/shared/data_encryption_service.py`
- **DynamoDB Client**: `lambda/shared/encrypted_dynamodb.py`
- **Integration Guide**: `lambda/shared/DATA_ENCRYPTION_INTEGRATION_GUIDE.md`
- **CDK Stack**: `infrastructure/cdk/stacks/data_classification_stack.py`

## Support

See full documentation: `lambda/shared/DATA_ENCRYPTION_INTEGRATION_GUIDE.md`
