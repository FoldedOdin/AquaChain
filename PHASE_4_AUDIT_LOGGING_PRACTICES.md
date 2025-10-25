# Phase 4 Audit Logging Practices

## Overview

This document defines audit logging practices for the AquaChain IoT water quality monitoring system. Comprehensive audit logging is essential for security monitoring, compliance verification, incident investigation, and regulatory requirements.

## Table of Contents

1. [Audit Logging Principles](#audit-logging-principles)
2. [What to Log](#what-to-log)
3. [Log Format and Structure](#log-format-and-structure)
4. [Implementation Guide](#implementation-guide)
5. [Log Storage and Retention](#log-storage-and-retention)
6. [Log Analysis and Monitoring](#log-analysis-and-monitoring)
7. [Compliance Requirements](#compliance-requirements)
8. [Troubleshooting](#troubleshooting)

---

## Audit Logging Principles

### Core Principles

1. **Completeness**: Log all security-relevant events
2. **Integrity**: Logs must be tamper-proof and immutable
3. **Confidentiality**: Protect sensitive data in logs
4. **Availability**: Logs must be accessible for authorized users
5. **Retention**: Retain logs for required compliance period (7 years)
6. **Performance**: Logging must not impact system performance

### What Makes a Good Audit Log

- **Who**: User or system that performed the action
- **What**: Action that was performed
- **When**: Timestamp of the action
- **Where**: System component or resource affected
- **Why**: Context or reason for the action (if applicable)
- **How**: Method or interface used
- **Result**: Success or failure of the action

---

## What to Log

### Authentication Events

**Required Events**:

| Event | Action Type | Details to Log |
|-------|-------------|----------------|
| User login | `USER_LOGIN` | user_id, ip_address, user_agent, success/failure |
| User logout | `USER_LOGOUT` | user_id, session_duration |
| Password change | `PASSWORD_CHANGE` | user_id, ip_address |
| Password reset request | `PASSWORD_RESET_REQUEST` | email, ip_address |
| Password reset complete | `PASSWORD_RESET_COMPLETE` | user_id, ip_address |
| MFA enabled | `MFA_ENABLED` | user_id |
| MFA disabled | `MFA_DISABLED` | user_id |
| Failed login attempt | `LOGIN_FAILED` | email, ip_address, failure_reason |
| Account locked | `ACCOUNT_LOCKED` | user_id, reason |
| Account unlocked | `ACCOUNT_UNLOCKED` | user_id, admin_id |

**Example**:
```python
audit_logger.log_action(
    user_id=user_id,
    action_type='USER_LOGIN',
    resource_type='authentication',
    resource_id=session_id,
    details={
        'ip_address': request_ip,
        'user_agent': request_user_agent,
        'success': True
    }
)
```

### Data Access Events

**Required Events**:

| Event | Action Type | Details to Log |
|-------|-------------|----------------|
| View user profile | `USER_PROFILE_VIEW` | user_id, viewer_id, profile_id |
| View device data | `DEVICE_DATA_VIEW` | user_id, device_id |
| View sensor readings | `SENSOR_DATA_VIEW` | user_id, device_id, time_range |
| Export data | `DATA_EXPORT` | user_id, export_type, record_count |
| Download report | `REPORT_DOWNLOAD` | user_id, report_type, report_id |

**Example**:
```python
audit_logger.log_action(
    user_id=user_id,
    action_type='SENSOR_DATA_VIEW',
    resource_type='sensor_readings',
    resource_id=device_id,
    details={
        'time_range': {'start': start_time, 'end': end_time},
        'record_count': len(readings)
    }
)
```

### Data Modification Events

**Required Events**:

| Event | Action Type | Details to Log |
|-------|-------------|----------------|
| Create user | `USER_CREATE` | admin_id, new_user_id, role |
| Update user | `USER_UPDATE` | admin_id, user_id, changed_fields |
| Delete user | `USER_DELETE` | admin_id, user_id |
| Create device | `DEVICE_CREATE` | user_id, device_id, device_type |
| Update device | `DEVICE_UPDATE` | user_id, device_id, changed_fields |
| Delete device | `DEVICE_DELETE` | user_id, device_id |
| Update settings | `SETTINGS_UPDATE` | user_id, setting_name, old_value, new_value |

**Example**:
```python
audit_logger.log_action(
    user_id=admin_id,
    action_type='USER_UPDATE',
    resource_type='user',
    resource_id=target_user_id,
    details={
        'changed_fields': ['role', 'email'],
        'old_values': {'role': 'consumer', 'email': 'old@example.com'},
        'new_values': {'role': 'technician', 'email': 'new@example.com'}
    }
)
```

### Administrative Actions

**Required Events**:

| Event | Action Type | Details to Log |
|-------|-------------|----------------|
| Grant permissions | `PERMISSION_GRANT` | admin_id, user_id, permission |
| Revoke permissions | `PERMISSION_REVOKE` | admin_id, user_id, permission |
| Create API key | `API_KEY_CREATE` | admin_id, key_id, scope |
| Revoke API key | `API_KEY_REVOKE` | admin_id, key_id |
| Configuration change | `CONFIG_CHANGE` | admin_id, config_key, old_value, new_value |
| System maintenance | `MAINTENANCE_ACTION` | admin_id, action, affected_systems |

### GDPR Events

**Required Events**:

| Event | Action Type | Details to Log |
|-------|-------------|----------------|
| Data export request | `GDPR_EXPORT_REQUEST` | user_id, request_id |
| Data export complete | `GDPR_EXPORT_COMPLETE` | user_id, request_id, record_count |
| Data deletion request | `GDPR_DELETION_REQUEST` | user_id, request_id |
| Data deletion complete | `GDPR_DELETION_COMPLETE` | user_id, request_id, deleted_items |
| Consent update | `CONSENT_UPDATE` | user_id, consent_type, granted |

### Security Events

**Required Events**:

| Event | Action Type | Details to Log |
|-------|-------------|----------------|
| Suspicious activity | `SECURITY_ALERT` | user_id, alert_type, details |
| Rate limit exceeded | `RATE_LIMIT_EXCEEDED` | user_id, endpoint, request_count |
| Invalid token | `INVALID_TOKEN` | ip_address, token_type |
| Unauthorized access | `UNAUTHORIZED_ACCESS` | user_id, resource, action |
| Data breach detected | `DATA_BREACH` | affected_users, data_types, severity |

---

## Log Format and Structure

### Standard Log Format

All audit logs use a consistent JSON structure:

```json
{
  "timestamp": "2025-10-25T10:30:45.123Z",
  "request_id": "req-abc123",
  "user_id": "user-123",
  "action_type": "USER_LOGIN",
  "resource_type": "authentication",
  "resource_id": "session-456",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "success": true,
  "details": {
    "login_method": "password",
    "mfa_used": true
  }
}
```

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO 8601 | When the action occurred | `2025-10-25T10:30:45.123Z` |
| `request_id` | String | Unique request identifier | `req-abc123` |
| `user_id` | String | User who performed action | `user-123` |
| `action_type` | String | Type of action | `USER_LOGIN` |
| `resource_type` | String | Type of resource affected | `authentication` |
| `resource_id` | String | Identifier of resource | `session-456` |
| `ip_address` | String | Client IP address | `192.168.1.100` |
| `user_agent` | String | Client user agent | `Mozilla/5.0...` |
| `success` | Boolean | Whether action succeeded | `true` |
| `details` | Object | Additional context | `{...}` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `error_code` | String | Error code if action failed |
| `error_message` | String | Error message if action failed |
| `duration_ms` | Number | Action duration in milliseconds |
| `affected_records` | Number | Number of records affected |
| `previous_value` | Any | Previous value before change |
| `new_value` | Any | New value after change |

---

## Implementation Guide

### Using the AuditLogger Class

**Basic Usage**:

```python
from lambda.shared.audit_logger import AuditLogger

# Initialize logger
audit_logger = AuditLogger()

# Log an action
audit_logger.log_action(
    user_id='user-123',
    action_type='DEVICE_CREATE',
    resource_type='device',
    resource_id='device-456',
    details={
        'device_name': 'Home Water Monitor',
        'device_type': 'water_quality_sensor'
    }
)
```

### Lambda Function Integration

**Pattern 1: Decorator**:

```python
from lambda.shared.audit_logger import audit_action

@audit_action(action_type='USER_UPDATE')
def update_user(event, context):
    """Update user with automatic audit logging"""
    user_id = event['user_id']
    updates = event['updates']
    
    # Perform update
    result = users_table.update_item(...)
    
    # Return result (decorator handles logging)
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

**Pattern 2: Explicit Logging**:

```python
def lambda_handler(event, context):
    """Lambda with explicit audit logging"""
    user_id = event['requestContext']['authorizer']['claims']['sub']
    
    try:
        # Perform action
        result = perform_action(event)
        
        # Log success
        audit_logger.log_action(
            user_id=user_id,
            action_type='ACTION_TYPE',
            resource_type='resource',
            resource_id=result['id'],
            success=True,
            details={'result': result}
        )
        
        return {'statusCode': 200, 'body': json.dumps(result)}
        
    except Exception as e:
        # Log failure
        audit_logger.log_action(
            user_id=user_id,
            action_type='ACTION_TYPE',
            resource_type='resource',
            resource_id=None,
            success=False,
            details={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        
        raise
```

### Frontend Integration

**API Service Layer**:

```typescript
// frontend/src/services/apiService.ts

async function apiCall(endpoint: string, options: RequestOptions) {
  const requestId = generateRequestId();
  
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'X-Request-ID': requestId
      }
    });
    
    // Backend logs the action with request_id
    return await response.json();
    
  } catch (error) {
    // Log client-side error
    console.error('API call failed', {
      requestId,
      endpoint,
      error
    });
    throw error;
  }
}
```

### Sensitive Data Handling

**DO NOT log**:
- Passwords or password hashes
- API keys or tokens
- Credit card numbers
- Social security numbers
- Full email addresses (use masked version)

**Masking Example**:

```python
def mask_email(email: str) -> str:
    """Mask email for logging"""
    local, domain = email.split('@')
    masked_local = local[0] + '***' + local[-1] if len(local) > 2 else '***'
    return f"{masked_local}@{domain}"

# Usage
audit_logger.log_action(
    user_id=user_id,
    action_type='PASSWORD_RESET_REQUEST',
    resource_type='authentication',
    resource_id=None,
    details={
        'email': mask_email(email),  # user@example.com -> u***r@example.com
        'ip_address': ip_address
    }
)
```

---

## Log Storage and Retention

### Storage Architecture

**Dual Storage Strategy**:

1. **DynamoDB (AuditLogs table)**: Hot storage for recent logs (90 days)
2. **S3 (via Kinesis Firehose)**: Cold storage for long-term retention (7 years)

### DynamoDB Table Schema

```python
# Table: AuditLogs
# Primary Key: user_id (HASH) + timestamp (RANGE)
# GSI-1: action_type (HASH) + timestamp (RANGE)
# GSI-2: resource_type (HASH) + resource_id (RANGE)
# TTL: 90 days

{
    'user_id': 'user-123',
    'timestamp': '2025-10-25T10:30:45.123Z',
    'request_id': 'req-abc123',
    'action_type': 'USER_LOGIN',
    'resource_type': 'authentication',
    'resource_id': 'session-456',
    'ip_address': '192.168.1.100',
    'user_agent': 'Mozilla/5.0...',
    'success': True,
    'details': {...},
    'ttl': 1735128645  # Unix timestamp for TTL
}
```

### S3 Archival

**Kinesis Firehose Configuration**:

```python
# infrastructure/cdk/stacks/audit_logging_stack.py

firehose_stream = firehose.CfnDeliveryStream(
    self, 'AuditLogStream',
    delivery_stream_type='DirectPut',
    s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
        bucket_arn=audit_bucket.bucket_arn,
        prefix='audit-logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/',
        error_output_prefix='audit-logs-errors/',
        buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
            interval_in_seconds=300,  # 5 minutes
            size_in_m_bs=5
        ),
        compression_format='GZIP'
    )
)
```

**S3 Bucket Configuration**:
- Encryption: AES-256
- Versioning: Enabled
- Object Lock: Enabled (compliance mode)
- Lifecycle: Transition to Glacier after 1 year
- Retention: 7 years

### Retention Policy

| Storage | Retention | Purpose |
|---------|-----------|---------|
| DynamoDB | 90 days | Recent log queries |
| S3 Standard | 1 year | Regular access |
| S3 Glacier | 6 years | Compliance archive |
| **Total** | **7 years** | **Regulatory requirement** |

---

## Log Analysis and Monitoring

### CloudWatch Insights Queries

**Failed Login Attempts**:

```sql
fields @timestamp, user_id, ip_address, details.failure_reason
| filter action_type = "LOGIN_FAILED"
| stats count() by ip_address
| sort count desc
| limit 20
```

**Data Access Patterns**:

```sql
fields @timestamp, user_id, action_type, resource_id
| filter action_type in ["SENSOR_DATA_VIEW", "DEVICE_DATA_VIEW"]
| stats count() by user_id
| sort count desc
```

**Administrative Actions**:

```sql
fields @timestamp, user_id, action_type, resource_type, details
| filter action_type in ["USER_CREATE", "USER_UPDATE", "USER_DELETE", "PERMISSION_GRANT", "PERMISSION_REVOKE"]
| sort @timestamp desc
```

**GDPR Requests**:

```sql
fields @timestamp, user_id, action_type, details
| filter action_type like /GDPR/
| stats count() by action_type
```

### Athena Queries for S3 Archives

**Create External Table**:

```sql
CREATE EXTERNAL TABLE audit_logs (
  timestamp STRING,
  request_id STRING,
  user_id STRING,
  action_type STRING,
  resource_type STRING,
  resource_id STRING,
  ip_address STRING,
  user_agent STRING,
  success BOOLEAN,
  details STRING
)
PARTITIONED BY (year STRING, month STRING, day STRING)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://aquachain-audit-logs/audit-logs/';
```

**Query Historical Data**:

```sql
SELECT user_id, action_type, COUNT(*) as action_count
FROM audit_logs
WHERE year = '2025' AND month = '10'
  AND action_type = 'USER_LOGIN'
GROUP BY user_id, action_type
ORDER BY action_count DESC
LIMIT 100;
```

### Alerting Rules

**CloudWatch Alarms**:

```python
# infrastructure/monitoring/audit_alarms.py

# Alert on excessive failed logins
failed_login_alarm = cloudwatch.Alarm(
    self, 'FailedLoginAlarm',
    metric=cloudwatch.Metric(
        namespace='AquaChain/Audit',
        metric_name='FailedLogins',
        statistic='Sum',
        period=Duration.minutes(5)
    ),
    threshold=10,
    evaluation_periods=1,
    alarm_description='Excessive failed login attempts detected'
)

# Alert on unauthorized access attempts
unauthorized_access_alarm = cloudwatch.Alarm(
    self, 'UnauthorizedAccessAlarm',
    metric=cloudwatch.Metric(
        namespace='AquaChain/Audit',
        metric_name='UnauthorizedAccess',
        statistic='Sum',
        period=Duration.minutes(5)
    ),
    threshold=5,
    evaluation_periods=1,
    alarm_description='Unauthorized access attempts detected'
)
```

---

## Compliance Requirements

### Regulatory Standards

**GDPR (Article 30)**:
- Maintain records of processing activities
- Include purposes of processing
- Include categories of data subjects
- Include categories of personal data
- Include recipients of personal data
- Include retention periods

**SOC 2**:
- Log all access to sensitive data
- Log all administrative actions
- Protect log integrity
- Retain logs for audit period

**HIPAA** (if applicable):
- Log all access to protected health information
- Log all modifications to PHI
- Retain logs for 6 years

### Audit Trail Requirements

**Immutability**:
- Use S3 Object Lock for archived logs
- Use DynamoDB streams for change detection
- Implement log verification checksums

**Completeness**:
- No gaps in log sequence
- All actions are logged
- Failed actions are logged

**Accuracy**:
- Synchronized timestamps (UTC)
- Accurate user attribution
- Complete context information

---

## Troubleshooting

### Common Issues

**Issue: Logs not appearing in DynamoDB**

**Diagnosis**:
```python
# Check if AuditLogger is initialized
audit_logger = AuditLogger()
print(f"Table name: {audit_logger.table_name}")

# Test logging
audit_logger.log_action(
    user_id='test-user',
    action_type='TEST',
    resource_type='test',
    resource_id='test-123'
)
```

**Solutions**:
- Verify IAM permissions for DynamoDB
- Check Lambda environment variables
- Review CloudWatch logs for errors

**Issue: Logs not streaming to S3**

**Diagnosis**:
```bash
# Check Firehose delivery stream status
aws firehose describe-delivery-stream --delivery-stream-name AuditLogStream

# Check S3 bucket for recent files
aws s3 ls s3://aquachain-audit-logs/audit-logs/ --recursive | tail -20
```

**Solutions**:
- Verify Firehose IAM role permissions
- Check Firehose error logs
- Verify S3 bucket policy

**Issue: High DynamoDB costs**

**Diagnosis**:
```python
# Check table metrics
import boto3

cloudwatch = boto3.client('cloudwatch')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='ConsumedWriteCapacityUnits',
    Dimensions=[{'Name': 'TableName', 'Value': 'AuditLogs'}],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300,
    Statistics=['Sum']
)
```

**Solutions**:
- Implement batch writing
- Reduce log verbosity
- Adjust TTL settings
- Consider on-demand pricing

---

## Best Practices

### Do's

✅ Log all security-relevant events  
✅ Use structured JSON format  
✅ Include request correlation IDs  
✅ Mask sensitive data  
✅ Implement log rotation  
✅ Monitor log volume  
✅ Test log queries regularly  
✅ Document custom action types  

### Don'ts

❌ Don't log passwords or secrets  
❌ Don't log full credit card numbers  
❌ Don't log excessive debug information in production  
❌ Don't allow log tampering  
❌ Don't ignore log storage costs  
❌ Don't forget to test log retrieval  
❌ Don't skip log retention policies  

---

## Resources

### Internal Documentation

- [Audit Logging Implementation](AUDIT_LOGGING_IMPLEMENTATION.md)
- [Audit Logging Quick Reference](AUDIT_LOGGING_QUICK_REFERENCE.md)
- [Compliance Reporting Guide](PHASE_4_COMPLIANCE_REPORTING_RUNBOOK.md)

### External Resources

- AWS CloudWatch Logs: https://docs.aws.amazon.com/cloudwatch/
- AWS Kinesis Firehose: https://docs.aws.amazon.com/firehose/
- GDPR Article 30: https://gdpr-info.eu/art-30-gdpr/

---

**Document Version**: 1.0  
**Last Updated**: Phase 4 Implementation  
**Owner**: Security and Compliance Team  
**Review Cycle**: Quarterly
