# Phase 3 Infrastructure Setup - Quick Reference

## Overview

Phase 3 infrastructure provides the foundation for ML model monitoring, IoT certificate lifecycle management, and automated security scanning.

## What Was Created

### ✅ Task 1: Phase 3 Infrastructure Foundation - COMPLETE

#### 1.1 ModelMetrics DynamoDB Table ✅
- **Purpose**: Track ML model performance metrics for drift detection
- **Table Name**: `aquachain-table-model-metrics-{env}`
- **Primary Key**: `model_name` (PK), `timestamp` (SK)
- **GSI**: `DriftScoreIndex` for querying by drift score
- **Features**: TTL enabled (90 days), DynamoDB Streams, Point-in-time recovery

#### 1.2 CertificateLifecycle DynamoDB Table ✅
- **Purpose**: Track IoT device certificate lifecycle for automated rotation
- **Table Name**: `aquachain-table-certificate-lifecycle-{env}`
- **Primary Key**: `device_id` (PK), `certificate_id` (SK)
- **GSI**: 
  - `ExpirationDateIndex` for querying expiring certificates
  - `StatusIndex` for querying by certificate status
- **Features**: DynamoDB Streams for audit logging, Point-in-time recovery

#### 1.3 EventBridge Schedules ✅
- **Certificate Expiration Check**: Daily at 2:00 AM UTC
- **Dependency Scanning**: Weekly on Monday at 3:00 AM UTC
- **SBOM Generation**: Weekly on Monday at 4:00 AM UTC

## Deployment

### Quick Deploy

```bash
# Deploy Phase 3 infrastructure only
cd infrastructure/cdk
./deploy-phase3.sh dev

# Or deploy all stacks including Phase 3
cd ../..
./deploy-all.sh dev
```

### Manual Deploy

```bash
cd infrastructure/cdk

# Install dependencies
pip3 install -r requirements.txt

# Synthesize stack
cdk synth AquaChain-Phase3-dev

# Deploy stack
cdk deploy AquaChain-Phase3-dev
```

## Verification

### Check DynamoDB Tables

```bash
# List tables
aws dynamodb list-tables --query "TableNames[?contains(@, 'model-metrics') || contains(@, 'certificate-lifecycle')]"

# Describe ModelMetrics table
aws dynamodb describe-table --table-name aquachain-table-model-metrics-dev

# Describe CertificateLifecycle table
aws dynamodb describe-table --table-name aquachain-table-certificate-lifecycle-dev
```

### Check EventBridge Rules

```bash
# List rules
aws events list-rules --name-prefix "aquachain-rule"

# Describe specific rule
aws events describe-rule --name aquachain-rule-cert-expiration-check-dev
```

## Integration with Lambda Functions

### ModelMetrics Table Usage

```python
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['MODEL_METRICS_TABLE_NAME'])

# Write metrics
table.put_item(
    Item={
        'model_name': 'water-quality-predictor',
        'timestamp': datetime.utcnow().isoformat(),
        'version': 'v1.2.0',
        'accuracy': 0.95,
        'latency_ms': 180,
        'drift_score': 0.08,
        'prediction_count': 1000,
        'confidence_avg': 0.92,
        'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
    }
)

# Query by drift score
response = table.query(
    IndexName='DriftScoreIndex',
    KeyConditionExpression='model_name = :model AND drift_score > :threshold',
    ExpressionAttributeValues={
        ':model': 'water-quality-predictor',
        ':threshold': 0.15
    }
)
```

### CertificateLifecycle Table Usage

```python
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CERTIFICATE_LIFECYCLE_TABLE_NAME'])

# Track certificate
table.put_item(
    Item={
        'device_id': 'device-001',
        'certificate_id': 'cert-abc123',
        'expiration_date': (datetime.utcnow() + timedelta(days=365)).isoformat(),
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'rotation_history': []
    }
)

# Query expiring certificates
response = table.query(
    IndexName='ExpirationDateIndex',
    KeyConditionExpression='#status = :status AND expiration_date < :date',
    ExpressionAttributeNames={
        '#status': 'status'
    },
    ExpressionAttributeValues={
        ':status': 'active',
        ':date': (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
)
```

### EventBridge Integration

```python
# Lambda function will be automatically triggered by EventBridge
# No additional code needed - just ensure Lambda has proper permissions

# Example Lambda handler for certificate rotation
def lambda_handler(event, context):
    # Event triggered by EventBridge schedule
    print(f"Certificate rotation triggered at {datetime.utcnow()}")
    
    # Query expiring certificates
    # Rotate certificates
    # Update DynamoDB
    
    return {
        'statusCode': 200,
        'body': 'Certificate rotation completed'
    }
```

## Environment Variables for Lambda Functions

Add these to your Lambda function configuration:

```bash
MODEL_METRICS_TABLE_NAME=aquachain-table-model-metrics-dev
CERTIFICATE_LIFECYCLE_TABLE_NAME=aquachain-table-certificate-lifecycle-dev
```

## IAM Permissions Required

Lambda functions need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/aquachain-table-model-metrics-*",
        "arn:aws:dynamodb:*:*:table/aquachain-table-model-metrics-*/index/*",
        "arn:aws:dynamodb:*:*:table/aquachain-table-certificate-lifecycle-*",
        "arn:aws:dynamodb:*:*:table/aquachain-table-certificate-lifecycle-*/index/*"
      ]
    }
  ]
}
```

## Monitoring

### CloudWatch Metrics to Monitor

- `ConsumedReadCapacityUnits` - DynamoDB read usage
- `ConsumedWriteCapacityUnits` - DynamoDB write usage
- `ThrottledRequests` - DynamoDB throttling
- `Invocations` - EventBridge rule invocations
- `FailedInvocations` - EventBridge failures

### Recommended Alarms

```bash
# DynamoDB throttling alarm
aws cloudwatch put-metric-alarm \
  --alarm-name phase3-dynamodb-throttling \
  --alarm-description "Alert on DynamoDB throttling" \
  --metric-name ThrottledRequests \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold

# EventBridge failures alarm
aws cloudwatch put-metric-alarm \
  --alarm-name phase3-eventbridge-failures \
  --alarm-description "Alert on EventBridge failures" \
  --metric-name FailedInvocations \
  --namespace AWS/Events \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 2 \
  --comparison-operator GreaterThanThreshold
```

## Cost Estimation

### DynamoDB
- **Pay-per-request billing**: ~$1.25 per million write requests, ~$0.25 per million read requests
- **Storage**: $0.25 per GB-month
- **Estimated monthly cost**: $5-20 depending on usage

### EventBridge
- **Scheduled rules**: Free
- **Lambda invocations**: Charged separately

### Total Estimated Cost
- **Development**: $5-10/month
- **Production**: $20-50/month

## Troubleshooting

### Stack Deployment Fails

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name AquaChain-Phase3-dev \
  --max-items 20

# Check CDK diff
cdk diff AquaChain-Phase3-dev
```

### Table Not Accessible

```bash
# Verify table exists
aws dynamodb describe-table --table-name aquachain-table-model-metrics-dev

# Check IAM permissions
aws iam get-role-policy --role-name <lambda-role> --policy-name <policy-name>
```

### EventBridge Rule Not Triggering

```bash
# Check rule status
aws events describe-rule --name aquachain-rule-cert-expiration-check-dev

# Check rule targets
aws events list-targets-by-rule --rule aquachain-rule-cert-expiration-check-dev

# Enable rule if disabled
aws events enable-rule --name aquachain-rule-cert-expiration-check-dev
```

## Next Steps

Now that Phase 3 infrastructure is deployed, proceed with:

1. ✅ **Task 1**: Phase 3 infrastructure foundation - COMPLETE
2. ⏳ **Task 2**: Implement ML model performance monitoring
3. ⏳ **Task 3**: Implement training data validation
4. ⏳ **Task 4**: Implement OTA firmware update system
5. ⏳ **Task 5**: Implement device certificate rotation
6. ⏳ **Task 6**: Implement dependency security management
7. ⏳ **Task 7**: Implement SBOM generation
8. ⏳ **Task 8**: Implement performance monitoring dashboard

## Documentation

- **Detailed Documentation**: `infrastructure/cdk/PHASE3_INFRASTRUCTURE.md`
- **Requirements**: `.kiro/specs/phase-3-high-priority/requirements.md`
- **Design**: `.kiro/specs/phase-3-high-priority/design.md`
- **Tasks**: `.kiro/specs/phase-3-high-priority/tasks.md`

## Support

For issues or questions:
1. Check CloudWatch Logs for Lambda errors
2. Review CloudFormation events for deployment issues
3. Verify IAM permissions are correctly configured
4. Ensure environment variables are set correctly

---

**Status**: ✅ Infrastructure Foundation Complete  
**Last Updated**: October 25, 2025  
**Next Task**: Task 2 - ML Model Performance Monitoring
