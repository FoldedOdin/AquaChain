# Phase 3 Infrastructure Stack

## Overview

The Phase 3 Infrastructure Stack provides the foundational AWS resources for ML model monitoring, IoT certificate lifecycle management, and automated security scanning.

## Resources Created

### DynamoDB Tables

#### 1. ModelMetrics Table
**Purpose:** Track ML model performance metrics for drift detection and monitoring

**Schema:**
- `model_name` (PK): Name of the ML model
- `timestamp` (SK): ISO 8601 timestamp of the metric
- `version`: Model version
- `accuracy`: Model accuracy metric
- `latency_ms`: Prediction latency in milliseconds
- `drift_score`: Model drift score (0-1)
- `prediction_count`: Number of predictions
- `confidence_avg`: Average confidence score
- `ttl`: Time-to-live for automatic expiration (90 days)

**Indexes:**
- `DriftScoreIndex`: GSI on `model_name` (PK) and `drift_score` (SK) for querying models by drift score

**Features:**
- Point-in-time recovery (production)
- DynamoDB Streams enabled for audit logging
- TTL enabled for automatic data expiration after 90 days
- Pay-per-request billing mode

#### 2. CertificateLifecycle Table
**Purpose:** Track IoT device certificate lifecycle for automated rotation

**Schema:**
- `device_id` (PK): IoT device identifier
- `certificate_id` (SK): Certificate identifier
- `expiration_date`: Certificate expiration date (ISO 8601)
- `status`: Certificate status (active, rotating, deactivated)
- `created_at`: Certificate creation timestamp
- `rotated_at`: Last rotation timestamp
- `rotation_history`: JSON array of rotation events

**Indexes:**
- `ExpirationDateIndex`: GSI on `status` (PK) and `expiration_date` (SK) for querying expiring certificates
- `StatusIndex`: GSI on `status` (PK) and `device_id` (SK) for querying certificates by status

**Features:**
- Point-in-time recovery (production)
- DynamoDB Streams enabled for audit logging
- Pay-per-request billing mode

### EventBridge Schedules

#### 1. Certificate Expiration Check
**Schedule:** Daily at 2:00 AM UTC  
**Purpose:** Check for expiring IoT device certificates and trigger rotation  
**Retry Policy:** 2 attempts, 2-hour max event age

#### 2. Dependency Scanning
**Schedule:** Weekly on Monday at 3:00 AM UTC  
**Purpose:** Scan npm and Python dependencies for vulnerabilities  
**Retry Policy:** 2 attempts, 4-hour max event age

#### 3. SBOM Generation
**Schedule:** Weekly on Monday at 4:00 AM UTC  
**Purpose:** Generate Software Bill of Materials for compliance  
**Retry Policy:** 2 attempts, 4-hour max event age

## Usage

### Deploying the Stack

```bash
cd infrastructure/cdk
cdk deploy AquaChain-Phase3-dev
```

### Connecting Lambda Functions

The stack provides helper methods to connect Lambda functions to EventBridge schedules:

```python
# In your compute stack or Lambda deployment
phase3_stack.add_certificate_rotation_target(certificate_rotation_lambda)
phase3_stack.add_dependency_scan_target(dependency_scanner_lambda)
phase3_stack.add_sbom_generation_target(sbom_generator_lambda)
```

### Accessing Tables from Lambda

```python
import boto3
import os

# ModelMetrics table
model_metrics_table = boto3.resource('dynamodb').Table(
    os.environ['MODEL_METRICS_TABLE_NAME']
)

# CertificateLifecycle table
cert_lifecycle_table = boto3.resource('dynamodb').Table(
    os.environ['CERTIFICATE_LIFECYCLE_TABLE_NAME']
)
```

## Integration with Other Stacks

### Dependencies
- **Security Stack**: Uses KMS keys for encryption at rest
- **Monitoring Stack**: CloudWatch alarms can be added for table metrics

### Dependent Stacks
- **ML Monitoring Lambda**: Writes to ModelMetrics table
- **Certificate Rotation Lambda**: Reads/writes to CertificateLifecycle table
- **Dependency Scanner Lambda**: Triggered by EventBridge schedule
- **SBOM Generator Lambda**: Triggered by EventBridge schedule

## Monitoring

### CloudWatch Metrics

**DynamoDB Metrics:**
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `ThrottledRequests`
- `UserErrors`

**EventBridge Metrics:**
- `Invocations`
- `FailedInvocations`
- `ThrottledRules`

### Recommended Alarms

1. **Table Throttling**: Alert when `ThrottledRequests` > 0
2. **Rule Failures**: Alert when `FailedInvocations` > 2
3. **Stream Processing Lag**: Alert when stream processing falls behind

## Cost Optimization

### DynamoDB
- Uses pay-per-request billing for cost efficiency
- TTL enabled on ModelMetrics to automatically delete old data
- Consider switching to provisioned capacity in production if usage is predictable

### EventBridge
- Schedules are free (no charge for scheduled rules)
- Only pay for Lambda invocations triggered by schedules

## Security

### Encryption
- All tables encrypted at rest using AWS managed keys
- Can be configured to use customer-managed KMS keys

### Access Control
- Tables require IAM permissions for access
- Lambda functions should use least-privilege IAM roles
- DynamoDB Streams enable audit logging

## Troubleshooting

### Table Not Found
Ensure the stack is deployed and check CloudFormation outputs:
```bash
aws cloudformation describe-stacks --stack-name AquaChain-Phase3-dev \
  --query 'Stacks[0].Outputs'
```

### EventBridge Rule Not Triggering
1. Check rule is enabled: `aws events describe-rule --name <rule-name>`
2. Verify Lambda function has EventBridge invoke permissions
3. Check CloudWatch Logs for Lambda execution errors

### DynamoDB Throttling
1. Check current capacity: `aws dynamodb describe-table --table-name <table-name>`
2. Consider switching to provisioned capacity with auto-scaling
3. Review access patterns and optimize queries

## Next Steps

After deploying this stack:

1. **Task 2**: Implement ML model performance monitoring Lambda
2. **Task 3**: Implement training data validation Lambda
3. **Task 4**: Implement OTA firmware update system
4. **Task 5**: Implement device certificate rotation Lambda
5. **Task 6**: Implement dependency security management Lambda
6. **Task 7**: Implement SBOM generation

## References

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [EventBridge Scheduled Rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)
- [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
