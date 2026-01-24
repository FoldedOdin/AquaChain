# AquaChain Security Infrastructure

This directory contains the complete security infrastructure implementation for the AquaChain water quality monitoring system. The security implementation addresses requirements 8.5, 15.5, 2.4, and 15.1 with comprehensive security controls, audit logging, and encryption.

## Overview

The AquaChain security infrastructure implements defense-in-depth security with the following components:

- **Input Validation & Sanitization**: Comprehensive validation to prevent injection attacks
- **Rate Limiting & DDoS Protection**: Exponential backoff and WAF integration
- **CAPTCHA Protection**: reCAPTCHA integration for authentication endpoints
- **Audit Logging**: Comprehensive audit trail for all user actions
- **Compliance Tracking**: Automated compliance monitoring and reporting
- **Data Encryption**: Encryption at rest and in transit with proper key management
- **Key Rotation**: Automated key rotation and management

## Components

### 1. Security Middleware (`lambda/shared/security_middleware.py`)

Provides comprehensive security controls for Lambda functions:

```python
from lambda.shared.security_middleware import secure_endpoint, auth_endpoint

@secure_endpoint(rate_limit=100, validate_schema=schema)
def my_api_handler(event, context):
    # Your API logic here
    pass

@auth_endpoint(rate_limit=10, require_captcha=True)
def login_handler(event, context):
    # Authentication logic here
    pass
```

**Features:**
- Input validation and sanitization
- SQL injection and XSS protection
- Rate limiting with exponential backoff
- CAPTCHA validation for auth endpoints
- Security headers injection
- Path and query parameter validation

### 2. Audit Logger (`lambda/shared/audit_logger.py`)

Comprehensive audit logging system:

```python
from lambda.shared.audit_logger import audit_user_action, AuditEventType

@audit_user_action(AuditEventType.USER_LOGIN, ['authentication'])
def login_handler(event, context):
    # Login logic here
    pass
```

**Features:**
- Structured audit event logging
- Multiple storage destinations (DynamoDB, CloudWatch, S3)
- Cryptographic signatures for integrity
- Compliance report generation
- Anomaly detection and alerting

### 3. Encryption Manager (`lambda/shared/encryption_manager.py`)

Data encryption and key management:

```python
from lambda.shared.encryption_manager import encrypt_sensitive_data, decrypt_sensitive_data

# Encrypt user data
encrypted_data = encrypt_sensitive_data(user_data, 'user_data')

# Decrypt data
decrypted_data = decrypt_sensitive_data(encrypted_data, 'user_data')
```

**Features:**
- KMS-based encryption with context
- Envelope encryption for large data
- Digital signatures for integrity
- Secure backup and recovery
- Automated key rotation

## Infrastructure Setup

### Prerequisites

1. AWS CLI configured with appropriate permissions
2. Python 3.11+ installed
3. Required Python packages: `boto3`, `cryptography`

### Setup Commands

```bash
# Set up complete security infrastructure
cd infrastructure/security
python setup_complete_security.py

# Set up individual components
python encryption_setup.py          # Encryption keys and configuration
python audit_infrastructure.py      # Audit logging infrastructure
python rate_limiting_setup.py       # Rate limiting tables and WAF
```

### Infrastructure Components Created

#### KMS Keys
- `alias/aquachain-master-key` - Master encryption key
- `alias/aquachain-ledger-key` - Ledger data encryption (immutable)
- `alias/aquachain-pii-key` - PII data encryption
- `alias/aquachain-signing-key` - Data integrity signing
- `alias/aquachain-backup-key` - Backup encryption

#### DynamoDB Tables
- `aquachain-audit-logs` - Audit event storage
- `aquachain-compliance-tracking` - Compliance metrics
- `aquachain-rate-limits` - Rate limiting counters

#### S3 Buckets
- `aquachain-audit-archive` - Long-term audit storage
- `aquachain-secure-backups` - Encrypted backup storage

#### CloudWatch Resources
- `/aws/lambda/aquachain-audit` - Audit log group
- Security monitoring alarms
- Custom metrics for security events

## Security Controls

### Input Validation

All API endpoints implement comprehensive input validation:

```python
# Email validation
email = InputValidator.validate_email(user_input['email'])

# Sensor data validation
ph_value = InputValidator.validate_sensor_reading('pH', sensor_data['pH'])

# String sanitization
safe_string = InputValidator.sanitize_string(user_input, max_length=100)
```

### Rate Limiting

Rate limiting is implemented at multiple levels:

- **API Gateway**: 1000 requests/minute per user
- **WAF**: IP-based rate limiting
- **Application**: Function-specific rate limits
- **Authentication**: Stricter limits for auth endpoints

### Audit Logging

All sensitive operations are audited:

```python
# Automatic audit logging with decorators
@audit_user_action(AuditEventType.DATA_EXPORT, ['gdpr', 'compliance'])
def export_data_handler(event, context):
    pass

# Manual audit logging
audit_logger.log_event(AuditEvent(
    event_type=AuditEventType.SECURITY_VIOLATION,
    severity=AuditSeverity.CRITICAL,
    user_id=user_id,
    details={'violation_type': 'unauthorized_access'}
))
```

### Data Encryption

All sensitive data is encrypted:

```python
# Encrypt user PII
encrypted_user = encrypt_sensitive_data(user_profile, 'user_data')

# Encrypt sensor readings
encrypted_readings = encrypt_sensitive_data(sensor_data, 'sensor_data')

# Create secure backup
backup_info = encryption_manager.create_secure_backup(data, 'backup_name')
```

## Compliance Features

### Audit Trail

- **Immutable Storage**: S3 Object Lock for 7-year retention
- **Cryptographic Integrity**: Digital signatures for all audit events
- **Cross-Account Replication**: Read-only audit account for tamper evidence
- **Hash Chain Verification**: Blockchain-inspired integrity verification

### Compliance Reporting

```python
# Generate compliance report
report = audit_logger.generate_compliance_report(
    start_date='2025-01-01',
    end_date='2025-01-31',
    compliance_framework='SOC2'
)
```

### Data Protection

- **Encryption at Rest**: All data encrypted with KMS
- **Encryption in Transit**: TLS 1.2+ for all communications
- **Key Rotation**: Automatic 90-day key rotation
- **Access Controls**: Role-based access with least privilege

## Monitoring and Alerting

### Security Metrics

- Security violations count
- Failed authentication attempts
- Rate limit violations
- Encryption/decryption errors
- Audit logging errors

### CloudWatch Alarms

- High security violation rate
- Sustained authentication failures
- Encryption service errors
- Audit logging failures

### SNS Topics

- `aquachain-security-alerts` - Critical security events
- `aquachain-compliance-alerts` - Compliance violations

## Integration Examples

See `lambda/shared/security_integration_example.py` for complete examples of:

- Secure user registration with CAPTCHA
- Protected data access with audit logging
- Admin endpoints with comprehensive security
- Data export with compliance tracking
- IoT data ingestion with validation

## Security Best Practices

### Development

1. **Always use security decorators** on Lambda functions
2. **Validate all inputs** before processing
3. **Encrypt sensitive data** before storage
4. **Log security events** for audit trail
5. **Use least privilege** for IAM roles

### Operations

1. **Monitor security metrics** regularly
2. **Review audit logs** for anomalies
3. **Test backup recovery** procedures
4. **Validate compliance reports** monthly
5. **Update security configurations** as needed

### Incident Response

1. **Security alerts** trigger immediate investigation
2. **Audit logs** provide forensic evidence
3. **Encrypted backups** enable recovery
4. **Compliance reports** document remediation

## Testing

### Security Testing

```bash
# Run security validation
python -c "
from infrastructure.security.setup_complete_security import CompleteSecuritySetup
setup = CompleteSecuritySetup()
result = setup.validate_security_setup()
print(f'Security Status: {result[\"overall_status\"]}')
"
```

### Penetration Testing

- Input validation bypass attempts
- Authentication bypass testing
- Rate limiting effectiveness
- Encryption key security
- Audit log integrity

## Troubleshooting

### Common Issues

1. **KMS Key Access Denied**
   - Check IAM permissions for Lambda execution role
   - Verify key policy allows service access

2. **Rate Limiting False Positives**
   - Adjust rate limits in security middleware
   - Check DynamoDB table capacity

3. **Audit Logging Failures**
   - Verify DynamoDB table exists and is active
   - Check S3 bucket permissions
   - Validate KMS key access

4. **Encryption Errors**
   - Verify encryption context matches
   - Check KMS key rotation status
   - Validate data format

### Monitoring Commands

```bash
# Check security infrastructure status
aws dynamodb describe-table --table-name aquachain-audit-logs
aws kms describe-key --key-id alias/aquachain-master-key
aws s3api get-bucket-encryption --bucket aquachain-audit-archive

# View recent security events
aws logs filter-log-events --log-group-name /aws/lambda/aquachain-audit --start-time $(date -d '1 hour ago' +%s)000
```

## Maintenance

### Regular Tasks

- **Weekly**: Review security metrics and alerts
- **Monthly**: Generate and review compliance reports
- **Quarterly**: Test backup and recovery procedures
- **Annually**: Security architecture review and updates

### Key Rotation

KMS keys are automatically rotated every 90 days. Manual rotation can be triggered:

```python
from lambda.shared.encryption_manager import encryption_manager
rotation_results = encryption_manager.rotate_keys()
```

## Support

For security-related issues or questions:

1. Check CloudWatch logs for error details
2. Review audit logs for security events
3. Validate infrastructure with setup scripts
4. Contact security team for critical issues

---

**Security Notice**: This infrastructure implements production-grade security controls. Any modifications should be reviewed by the security team and tested thoroughly before deployment.