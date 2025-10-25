# Phase 4 Infrastructure Deployment Guide

This guide provides step-by-step instructions for deploying Phase 4 infrastructure components.

## Overview

Phase 4 infrastructure includes:

1. **Data Classification Stack** - KMS keys for PII and Sensitive data encryption
2. **Audit Logging Stack** - Kinesis Firehose and S3 with Object Lock for immutable audit logs
3. **GDPR Compliance Stack** - S3 buckets and DynamoDB tables for GDPR operations
4. **Lambda Layers Stack** - Shared dependencies to reduce deployment sizes
5. **Lambda Performance Stack** - Provisioned concurrency and optimizations
6. **Cache Stack** - ElastiCache Redis for caching
7. **CloudFront Stack** - CDN for frontend delivery

## Prerequisites

### Required Tools

1. **AWS CLI** (v2.x or later)
   ```bash
   aws --version
   ```

2. **AWS CDK** (v2.x or later)
   ```bash
   npm install -g aws-cdk
   cdk --version
   ```

3. **Python** (3.11 or later)
   ```bash
   python --version
   ```

4. **Node.js** (18.x or later)
   ```bash
   node --version
   ```

### AWS Credentials

Ensure your AWS credentials are configured:

```bash
aws configure
# Or use environment variables:
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Required Permissions

Your AWS user/role needs permissions for:
- CloudFormation (create/update/delete stacks)
- KMS (create/manage keys)
- S3 (create/manage buckets)
- DynamoDB (create/manage tables)
- Kinesis Firehose (create/manage streams)
- ElastiCache (create/manage clusters)
- CloudFront (create/manage distributions)
- Lambda (create/manage functions and layers)
- IAM (create/manage roles and policies)
- VPC (if deploying cache stack)

## Deployment Steps

### Step 1: Prepare the Environment

Navigate to the project root:

```bash
cd /path/to/aquachain
```

Install CDK dependencies:

```bash
cd infrastructure/cdk
npm install
cd ../..
```

### Step 2: Build Lambda Layers

Build the Lambda layers before deployment:

```bash
cd lambda/layers
./build-layers.sh
cd ../..
```

This creates optimized layer packages with shared dependencies.

### Step 3: Bootstrap CDK (First Time Only)

If this is your first CDK deployment in this account/region:

```bash
cd infrastructure/cdk
cdk bootstrap aws://ACCOUNT-ID/REGION
cd ../..
```

Replace `ACCOUNT-ID` with your AWS account ID and `REGION` with your target region.

### Step 4: Dry Run (Recommended)

Perform a dry run to see what will be deployed:

```bash
python scripts/deploy-phase4-infrastructure.py \
  --environment dev \
  --dry-run
```

### Step 5: Deploy Infrastructure

Deploy to your target environment:

**Development:**
```bash
python scripts/deploy-phase4-infrastructure.py \
  --environment dev \
  --region us-east-1
```

**Staging:**
```bash
python scripts/deploy-phase4-infrastructure.py \
  --environment staging \
  --region us-east-1
```

**Production:**
```bash
python scripts/deploy-phase4-infrastructure.py \
  --environment prod \
  --region us-east-1
```

### Step 6: Verify Deployment

The script will automatically verify the deployment. You can also manually check:

```bash
python scripts/validate-phase4-deployment.py \
  --environment dev
```

## Deployment Order

The stacks are deployed in the following order (dependencies are handled automatically):

1. **DataClassification** - Creates KMS keys first (required by other stacks)
2. **AuditLogging** - Creates Kinesis Firehose and S3 (depends on KMS keys)
3. **GDPRCompliance** - Creates GDPR tables and buckets (depends on KMS keys)
4. **LambdaLayers** - Creates shared dependency layers (independent)
5. **LambdaPerformance** - Optimizes Lambda functions (depends on layers)
6. **Cache** - Creates ElastiCache cluster (depends on VPC)
7. **CloudFront** - Creates CDN distribution (can be deployed independently)

## Stack Details

### Data Classification Stack

**Resources Created:**
- KMS key for PII data encryption
- KMS key for Sensitive data encryption
- IAM policies for key access
- Key aliases for easy reference

**Outputs:**
- PII key ARN
- Sensitive key ARN
- Policy ARNs

### Audit Logging Stack

**Resources Created:**
- S3 bucket with Object Lock (7-year retention)
- Kinesis Firehose delivery stream
- IAM role for Firehose
- CloudWatch log group

**Outputs:**
- Audit archive bucket name
- Firehose stream name
- Firehose stream ARN

### GDPR Compliance Stack

**Resources Created:**
- S3 bucket for GDPR exports (30-day retention)
- S3 bucket for compliance reports (7-year retention)
- DynamoDB table: GDPRRequests
- DynamoDB table: UserConsents
- DynamoDB table: AuditLogs

**Outputs:**
- Export bucket name
- Compliance bucket name
- Table names and ARNs

### Lambda Layers Stack

**Resources Created:**
- Common layer (boto3, requests, pydantic, etc.)
- ML layer (numpy, pandas, scikit-learn, etc.)

**Outputs:**
- Common layer ARN
- ML layer ARN

### Lambda Performance Stack

**Resources Created:**
- Optimized data processing Lambda
- Optimized ML inference Lambda
- Provisioned concurrency configurations
- Auto-scaling policies
- CloudWatch alarms for cold starts

**Outputs:**
- Function ARNs
- Alias ARNs

### Cache Stack

**Resources Created:**
- ElastiCache Redis cluster
- Security group for Redis
- Subnet group
- Parameter group

**Outputs:**
- Redis endpoint
- Redis port
- Security group ID

### CloudFront Stack

**Resources Created:**
- CloudFront distribution
- S3 bucket for frontend
- Origin Access Identity
- WAF Web ACL
- SSL certificate (if domain configured)
- Cache policies
- Response headers policies

**Outputs:**
- Distribution ID
- Distribution domain name
- Frontend bucket name
- Frontend URL

## Post-Deployment Configuration

### 1. Update Lambda Environment Variables

Update Lambda functions to use the new infrastructure:

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name AquaChain-Cache-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
  --output text)

# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name aquachain-data-processing-dev \
  --environment "Variables={REDIS_ENDPOINT=$REDIS_ENDPOINT}"
```

### 2. Configure CloudFront Distribution

If using a custom domain, update DNS records:

```bash
# Get CloudFront domain
CF_DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name AquaChain-CloudFront-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionDomainName`].OutputValue' \
  --output text)

# Create Route53 record (example)
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch file://dns-change.json
```

### 3. Deploy Frontend to CloudFront

Build and deploy the frontend:

```bash
cd frontend
npm run build
aws s3 sync build/ s3://FRONTEND_BUCKET_NAME/
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

### 4. Configure Provisioned Concurrency

Adjust provisioned concurrency based on traffic:

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name aquachain-data-processing-dev \
  --qualifier live \
  --provisioned-concurrent-executions 10
```

## Monitoring

### CloudWatch Dashboards

View the performance dashboard:

```bash
aws cloudwatch get-dashboard \
  --dashboard-name AquaChain-Performance-dev
```

### Key Metrics to Monitor

1. **Lambda Performance**
   - Cold start duration
   - Invocation count
   - Error rate
   - Provisioned concurrency utilization

2. **Cache Performance**
   - Redis CPU utilization
   - Cache hit rate
   - Eviction count
   - Network throughput

3. **CloudFront Performance**
   - Cache hit ratio
   - Origin latency
   - 4xx/5xx error rate
   - Data transfer

4. **Audit Logging**
   - Firehose delivery success rate
   - S3 object count
   - Processing latency

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Failed

**Error:** "CDKToolkit stack not found"

**Solution:**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION --force
```

#### 2. Lambda Layer Build Failed

**Error:** "Failed to build layers"

**Solution:**
```bash
cd lambda/layers
chmod +x build-layers.sh
./build-layers.sh
```

#### 3. Stack Deployment Timeout

**Error:** "Stack creation timed out"

**Solution:**
- Check CloudFormation console for detailed error
- Verify IAM permissions
- Check resource limits (e.g., VPC limits, ElastiCache limits)

#### 4. Redis Connection Failed

**Error:** "Cannot connect to Redis"

**Solution:**
- Verify Lambda is in the same VPC as Redis
- Check security group rules
- Verify Redis endpoint in environment variables

#### 5. CloudFront Distribution Not Accessible

**Error:** "403 Forbidden"

**Solution:**
- Verify Origin Access Identity permissions
- Check S3 bucket policy
- Verify CloudFront cache behaviors

### Getting Help

1. Check CloudFormation events:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name AquaChain-STACK-NAME-dev
   ```

2. Check Lambda logs:
   ```bash
   aws logs tail /aws/lambda/FUNCTION-NAME --follow
   ```

3. Check Firehose delivery errors:
   ```bash
   aws logs tail /aws/kinesisfirehose/audit-logs --follow
   ```

## Rollback

If deployment fails or you need to rollback:

### Rollback Single Stack

```bash
cd infrastructure/cdk
cdk destroy AquaChain-STACK-NAME-dev
```

### Rollback All Phase 4 Stacks

```bash
cd infrastructure/cdk
cdk destroy AquaChain-CloudFront-dev
cdk destroy AquaChain-Cache-dev
cdk destroy AquaChain-LambdaPerformance-dev
cdk destroy AquaChain-LambdaLayers-dev
cdk destroy AquaChain-GDPRCompliance-dev
cdk destroy AquaChain-AuditLogging-dev
cdk destroy AquaChain-DataClassification-dev
```

**Note:** Destroy in reverse order to handle dependencies.

## Cost Estimation

Estimated monthly costs for Phase 4 infrastructure:

### Development Environment
- KMS keys: $2/month (2 keys)
- ElastiCache (t3.micro): $12/month
- S3 storage: $5/month (estimated)
- Kinesis Firehose: $5/month (estimated)
- DynamoDB: $5/month (on-demand)
- CloudFront: $10/month (estimated)
- Lambda: $5/month (estimated)
- **Total: ~$44/month**

### Production Environment
- KMS keys: $2/month (2 keys)
- ElastiCache (m5.large): $150/month
- S3 storage: $50/month (estimated)
- Kinesis Firehose: $50/month (estimated)
- DynamoDB: $100/month (estimated)
- CloudFront: $100/month (estimated)
- Lambda: $50/month (estimated)
- **Total: ~$502/month**

**Note:** Actual costs depend on usage patterns and data volume.

## Security Considerations

1. **KMS Keys**
   - Keys are automatically rotated annually
   - Access is restricted via IAM policies
   - Keys are retained in production (cannot be deleted)

2. **S3 Buckets**
   - All buckets have encryption enabled
   - Public access is blocked
   - Versioning is enabled
   - Audit log bucket has Object Lock for immutability

3. **DynamoDB Tables**
   - Encrypted with customer-managed KMS keys
   - Point-in-time recovery enabled in production
   - Backup retention configured

4. **ElastiCache**
   - Deployed in private subnets
   - Security groups restrict access to Lambda only
   - Encryption in transit enabled

5. **CloudFront**
   - WAF enabled with rate limiting
   - HTTPS enforced
   - Security headers configured
   - Access logs enabled

## Compliance

Phase 4 infrastructure supports:

- **GDPR** - Data export, deletion, consent management
- **SOC 2** - Audit logging, encryption, access controls
- **HIPAA** - Encryption at rest and in transit, audit trails
- **ISO 27001** - Security controls, monitoring, incident response

## Next Steps

After successful deployment:

1. ✅ Update Lambda functions to use new layers
2. ✅ Configure cache service in application code
3. ✅ Deploy frontend to CloudFront
4. ✅ Test GDPR export/deletion workflows
5. ✅ Verify audit logging is working
6. ✅ Set up monitoring alerts
7. ✅ Run validation tests
8. ✅ Update documentation

## References

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)
- [CloudFront Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/best-practices.html)
- [Lambda Performance Optimization](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [GDPR Compliance on AWS](https://aws.amazon.com/compliance/gdpr-center/)
