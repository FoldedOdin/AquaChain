# Audit Logging Quick Reference

## Import and Initialize

```python
from audit_logger import audit_logger
```

## Common Usage Patterns

### 1. Log Authentication Events

```python
# Login
audit_logger.log_authentication_event(
    event_type='LOGIN',
    user_id='user-123',
    success=True,
    request_context=request_context,
    details={'method': 'password'}
)

# Logout
audit_logger.log_authentication_event(
    event_type='LOGOUT',
    user_id='user-123',
    success=True,
    request_context=request_context
)

# Token refresh
audit_logger.log_authentication_event(
    event_type='TOKEN_REFRESH',
    user_id='user-123',
    success=True,
    request_context=request_context
)
```

### 2. Log Data Access (READ)

```python
audit_logger.log_data_access(
    user_id='user-123',
    resource_type='DEVICE',
    resource_id='device-456',
    operation='GET',
    request_context=request_context,
    details={'query_params': {'status': 'active'}}
)
```

### 3. Log Data Modifications (CREATE/UPDATE/DELETE)

```python
# Create
audit_logger.log_data_modification(
    user_id='user-123',
    resource_type='DEVICE',
    resource_id='device-456',
    modification_type='CREATE',
    previous_values=None,
    new_values={'name': 'New Device', 'status': 'active'},
    request_context=request_context
)

# Update
audit_logger.log_data_modification(
    user_id='user-123',
    resource_type='USER',
    resource_id='user-456',
    modification_type='UPDATE',
    previous_values={'email': 'old@example.com'},
    new_values={'email': 'new@example.com'},
    request_context=request_context
)

# Delete
audit_logger.log_data_modification(
    user_id='user-123',
    resource_type='DEVICE',
    resource_id='device-456',
    modification_type='DELETE',
    previous_values={'name': 'Old Device', 'status': 'active'},
    new_values=None,
    request_context=request_context
)
```

### 4. Log Administrative Actions

```python
audit_logger.log_administrative_action(
    user_id='admin-123',
    action='USER_ROLE_CHANGE',
    target_resource_type='USER',
    target_resource_id='user-456',
    request_context=request_context,
    details={'old_role': 'consumer', 'new_role': 'technician'}
)
```

## Request Context Helper

```python
def _get_request_context(event: Dict) -> Dict:
    """Extract request context from Lambda event"""
    return {
        'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
        'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
        'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
        'source': 'api'
    }

# Usage in Lambda handler
request_context = _get_request_context(event)
```

## Querying Audit Logs

### By User
```python
result = audit_logger.query_logs_by_user(
    user_id='user-123',
    start_time='2025-10-01T00:00:00Z',
    end_time='2025-10-31T23:59:59Z',
    limit=100
)

for log in result['items']:
    print(f"{log['timestamp']}: {log['action_type']}")
```

### By Resource Type
```python
result = audit_logger.query_logs_by_resource(
    resource_type='DEVICE',
    start_time='2025-10-25T00:00:00Z',
    limit=50
)
```

### By Action Type
```python
result = audit_logger.query_logs_by_action_type(
    action_type='AUTH_LOGIN',
    start_time='2025-10-25T00:00:00Z',
    limit=100
)
```

## Action Types Reference

### Authentication
- `AUTH_LOGIN`
- `AUTH_LOGOUT`
- `AUTH_TOKEN_VALIDATION`
- `AUTH_TOKEN_REFRESH`
- `AUTH_PASSWORD_RESET`
- `AUTH_PASSWORD_CHANGE`

### Data Operations
- `CREATE`
- `READ`
- `UPDATE`
- `DELETE`

### Administrative
- `ADMIN_USER_CREATE`
- `ADMIN_USER_DELETE`
- `ADMIN_USER_ROLE_CHANGE`
- `ADMIN_CONFIG_CHANGE`
- `ADMIN_PERMISSION_GRANT`
- `ADMIN_PERMISSION_REVOKE`

## Resource Types

- `USER`
- `DEVICE`
- `READING`
- `ALERT`
- `SERVICE_REQUEST`
- `ORGANIZATION`
- `CONFIGURATION`

## Environment Variables

```bash
AUDIT_LOGS_TABLE=aquachain-dev-audit-logs
AUDIT_LOG_STREAM=AuditLogStream
```

## DynamoDB Table Structure

**Table**: `aquachain-{env}-audit-logs`

**Keys**:
- Partition Key: `log_id` (String)
- Sort Key: `timestamp` (String)

**GSIs**:
1. `user_id-timestamp-index`
2. `resource_type-timestamp-index`
3. `action_type-timestamp-index`

**TTL**: `ttl` attribute (7 years)

## S3 Archive Structure

```
s3://audit-archive-{account}/
  audit-logs/
    year=2025/
      month=10/
        day=25/
          {timestamp}-{uuid}.json.gz
```

## Compliance

- **Retention**: 7 years
- **Encryption**: KMS at rest, TLS in transit
- **Immutability**: S3 Object Lock (compliance mode)
- **GDPR**: Queryable by user, anonymizable on deletion
- **SOC 2**: Complete audit trail with tamper-proof storage

## Troubleshooting

### Check Firehose Status
```bash
aws firehose describe-delivery-stream --delivery-stream-name AuditLogStream
```

### Query DynamoDB
```bash
aws dynamodb query \
  --table-name aquachain-dev-audit-logs \
  --index-name user_id-timestamp-index \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid":{"S":"user-123"}}'
```

### Check S3 Archives
```bash
aws s3 ls s3://audit-archive-{account}/audit-logs/year=2025/month=10/day=25/
```

## Best Practices

1. **Always log**: Log all user actions, data access, and modifications
2. **Include context**: Always provide complete request_context
3. **Be specific**: Use appropriate action_type and resource_type
4. **Don't block**: Audit logging failures should not block operations
5. **Query efficiently**: Use GSIs and time ranges for queries
6. **Monitor**: Set up CloudWatch alarms for delivery failures
