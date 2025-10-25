# Phase 4 Infrastructure Quick Reference

Quick commands and information for Phase 4 infrastructure deployment and management.

## Quick Deploy

```bash
# Development
python scripts/deploy-phase4-infrastructure.py --environment dev

# Staging
python scripts/deploy-phase4-infrastructure.py --environment staging

# Production
python scripts/deploy-phase4-infrastructure.py --environment prod
```

## Stack Names

| Stack | Purpose |
|-------|---------|
| `AquaChain-DataClassification-{env}` | KMS keys for encryption |
| `AquaChain-AuditLogging-{env}` | Kinesis Firehose and S3 |
| `AquaChain-GDPRCompliance-{env}` | GDPR tables and buckets |
| `AquaChain-LambdaLayers-{env}` | Shared Lambda dependencies |
| `AquaChain-LambdaPerformance-{env}` | Optimized Lambda functions |
| `AquaChain-Cache-{env}` | ElastiCache Redis cluster |
| `AquaChain-CloudFront-{env}` | CDN distribution |

## Key Resources

### KMS Keys

```bash
# List KMS keys
aws kms list-aliases | grep aquachain

# Get PII key ID
aws kms describe-key --key-id alias/aquachain-dev-pii-key

# Get Sensitive key ID
aws kms describe-key --key-id alias/aquachain-dev-sensitive-key
```

### S3 Buckets

```bash
# List Phase 4 buckets
aws s3 ls | grep aquachain

# GDPR exports bucket
aquachain-gdpr-exports-{account}-{region}

# Compliance reports bucket
aquachain-compliance-reports-{account}-{region}

# Audit logs bucket
aquachain-audit-logs-{account}-{region}
```

### DynamoDB Tables

```bash
# List Phase 4 tables
aws dynamodb list-tables | grep aquachain

# GDPR requests table
aquachain-gdpr-requests-{env}

# User consents table
aquachain-user-consents-{env}

# Audit logs table
aquachain-audit-logs-{env}
```

### ElastiCache

```bash
# Get Redis endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id aquachain-cache-redis-dev \
  --show-cache-node-info

# Get Redis metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name CPUUtilization \
  --dimensions Name=CacheClusterId,Value=aquachain-cache-redis-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### CloudFront

```bash
# Get distribution ID
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='AquaChain Frontend and API dev'].Id" \
  --output text

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"

# Get distribution metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=DISTRIBUTION_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Lambda Layers

```bash
# List layers
aws lambda list-layers | grep aquachain

# Get layer version ARN
aws lambda list-layer-versions \
  --layer-name aquachain-common-layer-AquaChain-LambdaLayers-dev \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text
```

## Common Operations

### Update Lambda Environment Variables

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name AquaChain-Cache-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
  --output text)

# Update Lambda
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --environment "Variables={REDIS_ENDPOINT=$REDIS_ENDPOINT,REDIS_PORT=6379}"
```

### Deploy Frontend to CloudFront

```bash
# Build frontend
cd frontend
npm run build

# Get bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name AquaChain-CloudFront-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text)

# Sync to S3
aws s3 sync build/ s3://$BUCKET/

# Get distribution ID
DIST_ID=$(aws cloudformation describe-stacks \
  --stack-name AquaChain-CloudFront-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"
```

### Check Stack Status

```bash
# Single stack
aws cloudformation describe-stacks \
  --stack-name AquaChain-STACK-NAME-dev \
  --query 'Stacks[0].StackStatus' \
  --output text

# All Phase 4 stacks
for stack in DataClassification AuditLogging GDPRCompliance LambdaLayers LambdaPerformance Cache CloudFront; do
  echo -n "$stack: "
  aws cloudformation describe-stacks \
    --stack-name AquaChain-$stack-dev \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND"
done
```

### View Stack Outputs

```bash
# All outputs for a stack
aws cloudformation describe-stacks \
  --stack-name AquaChain-STACK-NAME-dev \
  --query 'Stacks[0].Outputs'

# Specific output
aws cloudformation describe-stacks \
  --stack-name AquaChain-STACK-NAME-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`KEY_NAME`].OutputValue' \
  --output text
```

### Monitor Audit Logs

```bash
# Check Firehose delivery
aws firehose describe-delivery-stream \
  --delivery-stream-name aquachain-stream-audit-logs-dev

# View Firehose logs
aws logs tail /aws/kinesisfirehose/audit-logs --follow

# List audit log files in S3
aws s3 ls s3://aquachain-audit-logs-{account}-{region}/audit-logs/ --recursive
```

### Test Cache Connection

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name AquaChain-Cache-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
  --output text)

# Test connection (requires redis-cli)
redis-cli -h $REDIS_ENDPOINT ping
```

## Monitoring Commands

### Lambda Performance

```bash
# Cold start metrics
aws cloudwatch get-metric-statistics \
  --namespace AquaChain/Lambda \
  --metric-name DataProcessingColdStarts \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Provisioned concurrency utilization
aws lambda get-provisioned-concurrency-config \
  --function-name aquachain-data-processing-dev \
  --qualifier live
```

### Cache Metrics

```bash
# Cache hit rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name CacheHitRate \
  --dimensions Name=CacheClusterId,Value=aquachain-cache-redis-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### CloudFront Metrics

```bash
# Cache hit ratio
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=DISTRIBUTION_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## Troubleshooting

### Check CloudFormation Events

```bash
# Recent events
aws cloudformation describe-stack-events \
  --stack-name AquaChain-STACK-NAME-dev \
  --max-items 20

# Failed events only
aws cloudformation describe-stack-events \
  --stack-name AquaChain-STACK-NAME-dev \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'
```

### Check Lambda Logs

```bash
# Tail logs
aws logs tail /aws/lambda/FUNCTION-NAME --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/FUNCTION-NAME \
  --filter-pattern "ERROR"
```

### Check Firehose Errors

```bash
# Delivery errors
aws logs filter-log-events \
  --log-group-name /aws/kinesisfirehose/audit-logs \
  --filter-pattern "ERROR"
```

## Cleanup

### Delete Single Stack

```bash
cd infrastructure/cdk
cdk destroy AquaChain-STACK-NAME-dev
```

### Delete All Phase 4 Stacks

```bash
cd infrastructure/cdk

# Delete in reverse order
cdk destroy AquaChain-CloudFront-dev
cdk destroy AquaChain-Cache-dev
cdk destroy AquaChain-LambdaPerformance-dev
cdk destroy AquaChain-LambdaLayers-dev
cdk destroy AquaChain-GDPRCompliance-dev
cdk destroy AquaChain-AuditLogging-dev
cdk destroy AquaChain-DataClassification-dev
```

## Environment Variables

Key environment variables for Lambda functions:

```bash
# Redis
REDIS_ENDPOINT=aquachain-cache-redis-dev.xxxxx.cache.amazonaws.com
REDIS_PORT=6379

# KMS
PII_KMS_KEY_ID=alias/aquachain-dev-pii-key
SENSITIVE_KMS_KEY_ID=alias/aquachain-dev-sensitive-key

# S3
GDPR_EXPORT_BUCKET=aquachain-gdpr-exports-{account}-{region}
COMPLIANCE_REPORTS_BUCKET=aquachain-compliance-reports-{account}-{region}

# DynamoDB
GDPR_REQUESTS_TABLE=aquachain-gdpr-requests-dev
USER_CONSENTS_TABLE=aquachain-user-consents-dev
AUDIT_LOGS_TABLE=aquachain-audit-logs-dev

# Kinesis
AUDIT_LOG_STREAM=aquachain-stream-audit-logs-dev
```

## Cost Monitoring

```bash
# Get cost for Phase 4 resources (last 30 days)
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '30 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://cost-filter.json

# cost-filter.json
{
  "Tags": {
    "Key": "Project",
    "Values": ["AquaChain"]
  }
}
```

## Validation

```bash
# Run validation script
python scripts/validate-phase4-deployment.py --environment dev

# Check specific components
python scripts/validate-phase4-deployment.py --environment dev --component kms
python scripts/validate-phase4-deployment.py --environment dev --component cache
python scripts/validate-phase4-deployment.py --environment dev --component cloudfront
```

## Support

For issues or questions:
1. Check CloudFormation events
2. Review Lambda logs
3. Check AWS service health dashboard
4. Consult deployment guide: `PHASE_4_INFRASTRUCTURE_DEPLOYMENT_GUIDE.md`
