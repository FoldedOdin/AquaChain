# Data Classification and Encryption - Deployment Checklist

## Pre-Deployment Validation

### ✅ Code Review
- [ ] Review data classification schema (`lambda/shared/data_classification.py`)
- [ ] Review encryption service implementation (`lambda/shared/data_encryption_service.py`)
- [ ] Review encrypted DynamoDB client (`lambda/shared/encrypted_dynamodb.py`)
- [ ] Review CDK stack (`infrastructure/cdk/stacks/data_classification_stack.py`)
- [ ] Review integration examples (`lambda/user_management/encrypted_user_service.py`)

### ✅ Testing
- [ ] Unit tests for data classification
- [ ] Unit tests for encryption service
- [ ] Integration tests for encrypted DynamoDB operations
- [ ] End-to-end tests with real KMS keys (dev environment)

### ✅ Documentation
- [ ] Review integration guide (`lambda/shared/DATA_ENCRYPTION_INTEGRATION_GUIDE.md`)
- [ ] Review quick reference (`DATA_CLASSIFICATION_QUICK_REFERENCE.md`)
- [ ] Review implementation summary (`TASK_19_DATA_CLASSIFICATION_ENCRYPTION_SUMMARY.md`)

## Deployment Steps

### Step 1: Deploy KMS Keys (Infrastructure)

```bash
cd infrastructure/cdk

# Deploy to dev environment first
cdk deploy DataClassificationStack --context environment=dev

# Verify keys created
aws kms list-aliases | grep aquachain-dev

# Expected output:
# alias/aquachain-dev-pii-key
# alias/aquachain-dev-sensitive-key
```

**Validation:**
- [ ] PII KMS key created
- [ ] SENSITIVE KMS key created
- [ ] Key aliases configured
- [ ] Key rotation enabled
- [ ] Key policies applied

### Step 2: Update Lambda Execution Roles

```bash
# Get Lambda execution role ARN
aws lambda get-function --function-name user-management \
  --query 'Configuration.Role' --output text

# Attach encryption access policy
aws iam attach-role-policy \
  --role-name AquaChain-dev-Lambda-UserManagement \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/AquaChain-dev-Full-Encryption-Access
```

**Validation:**
- [ ] IAM policies attached to Lambda roles
- [ ] KMS permissions granted
- [ ] Test key access from Lambda

### Step 3: Update Lambda Environment Variables

```bash
# Get KMS key IDs
PII_KEY_ID=$(aws kms describe-key --key-id alias/aquachain-dev-pii-key \
  --query 'KeyMetadata.KeyId' --output text)

SENSITIVE_KEY_ID=$(aws kms describe-key --key-id alias/aquachain-dev-sensitive-key \
  --query 'KeyMetadata.KeyId' --output text)

# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name user-management \
  --environment Variables="{
    PII_KMS_KEY_ID=alias/aquachain-dev-pii-key,
    SENSITIVE_KMS_KEY_ID=alias/aquachain-dev-sensitive-key,
    AWS_REGION=us-east-1,
    USERS_TABLE=aquachain-dev-users
  }"
```

**Validation:**
- [ ] Environment variables set
- [ ] Key aliases configured correctly
- [ ] Region configured

### Step 4: Deploy Updated Lambda Functions

```bash
cd lambda/shared

# Package shared layer with new encryption modules
zip -r encryption-layer.zip \
  data_classification.py \
  data_encryption_service.py \
  encrypted_dynamodb.py

# Publish layer
aws lambda publish-layer-version \
  --layer-name aquachain-encryption \
  --zip-file fileb://encryption-layer.zip \
  --compatible-runtimes python3.11

# Update Lambda functions to use layer
aws lambda update-function-configuration \
  --function-name user-management \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:aquachain-encryption:1
```

**Validation:**
- [ ] Lambda layer published
- [ ] Lambda functions updated
- [ ] Dependencies resolved

### Step 5: Test Encryption in Dev Environment

```bash
# Test encryption configuration
aws lambda invoke \
  --function-name user-management \
  --payload '{"action": "validate_encryption"}' \
  response.json

cat response.json
# Expected: {"valid": true, "errors": []}
```

**Test Cases:**
- [ ] Create user with PII encryption
- [ ] Retrieve user with PII decryption
- [ ] Update user with PII encryption
- [ ] Create device with SENSITIVE encryption
- [ ] Query with automatic decryption
- [ ] GDPR export with decryption

### Step 6: Monitor and Validate

```bash
# Check CloudWatch logs for encryption operations
aws logs tail /aws/lambda/user-management --follow

# Monitor KMS API calls
aws cloudwatch get-metric-statistics \
  --namespace AWS/KMS \
  --metric-name NumberOfCalls \
  --dimensions Name=KeyId,Value=$PII_KEY_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Validation:**
- [ ] No encryption errors in logs
- [ ] KMS API calls successful
- [ ] Latency acceptable (<100ms)
- [ ] No throttling errors

### Step 7: Data Migration (If Needed)

```bash
# Run migration script to encrypt existing data
aws lambda invoke \
  --function-name data-migration \
  --payload '{"action": "encrypt_existing_users"}' \
  migration-response.json

# Monitor migration progress
aws logs tail /aws/lambda/data-migration --follow
```

**Validation:**
- [ ] Existing data encrypted
- [ ] No data loss
- [ ] Backup created before migration
- [ ] Migration logs reviewed

### Step 8: Production Deployment

```bash
# Deploy to production
cd infrastructure/cdk
cdk deploy DataClassificationStack --context environment=prod

# Update production Lambda functions
# (Repeat steps 2-4 for production)
```

**Production Checklist:**
- [ ] KMS keys deployed to production
- [ ] Key retention policy set to RETAIN
- [ ] Lambda functions updated
- [ ] Environment variables configured
- [ ] IAM policies applied
- [ ] Monitoring configured
- [ ] Alerts configured

## Post-Deployment Validation

### Functional Testing

```bash
# Test user creation with PII
curl -X POST https://api.aquachain.com/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "email": "test@example.com",
    "name": "Test User",
    "phone": "+1234567890",
    "role": "consumer"
  }'

# Verify encryption in DynamoDB
aws dynamodb get-item \
  --table-name aquachain-prod-users \
  --key '{"user_id": {"S": "test-user"}}'

# Email field should be base64 encoded ciphertext
```

**Validation:**
- [ ] PII fields encrypted in storage
- [ ] SENSITIVE fields encrypted in storage
- [ ] INTERNAL fields not encrypted
- [ ] Decryption works correctly
- [ ] API responses contain decrypted data

### Performance Testing

```bash
# Run load test
artillery run load-test.yml

# Monitor KMS throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/KMS \
  --metric-name ThrottledRequests \
  --dimensions Name=KeyId,Value=$PII_KEY_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Validation:**
- [ ] Latency acceptable (<100ms added)
- [ ] No KMS throttling
- [ ] No errors under load
- [ ] Throughput maintained

### Security Testing

```bash
# Verify encryption at rest
aws dynamodb describe-table \
  --table-name aquachain-prod-users \
  --query 'Table.SSEDescription'

# Verify KMS key policies
aws kms get-key-policy \
  --key-id alias/aquachain-prod-pii-key \
  --policy-name default
```

**Validation:**
- [ ] Data encrypted at rest
- [ ] KMS key policies correct
- [ ] Access controls enforced
- [ ] Audit logging enabled

### Compliance Validation

**GDPR Compliance:**
- [ ] PII fields identified and encrypted
- [ ] Data subject rights supported
- [ ] Audit trail for PII access
- [ ] Encryption key rotation enabled
- [ ] Data retention policies applied

**Documentation:**
- [ ] Data classification documented
- [ ] Encryption procedures documented
- [ ] Key management procedures documented
- [ ] Incident response procedures updated

## Monitoring Setup

### CloudWatch Alarms

```bash
# Create alarm for KMS throttling
aws cloudwatch put-metric-alarm \
  --alarm-name aquachain-kms-throttling \
  --alarm-description "Alert on KMS throttling" \
  --metric-name ThrottledRequests \
  --namespace AWS/KMS \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold

# Create alarm for encryption errors
aws cloudwatch put-metric-alarm \
  --alarm-name aquachain-encryption-errors \
  --alarm-description "Alert on encryption errors" \
  --metric-name EncryptionErrors \
  --namespace AquaChain \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

**Alarms Configured:**
- [ ] KMS throttling alarm
- [ ] Encryption error alarm
- [ ] Decryption error alarm
- [ ] Key rotation alarm

### Logging

```bash
# Enable CloudTrail for KMS
aws cloudtrail create-trail \
  --name aquachain-kms-trail \
  --s3-bucket-name aquachain-cloudtrail-logs

aws cloudtrail start-logging --name aquachain-kms-trail
```

**Logging Enabled:**
- [ ] CloudTrail for KMS operations
- [ ] CloudWatch Logs for Lambda
- [ ] Structured logging for encryption operations
- [ ] Audit logging for PII access

## Rollback Plan

### If Issues Detected

1. **Disable Encryption (Emergency)**
   ```bash
   # Revert Lambda to previous version
   aws lambda update-function-configuration \
     --function-name user-management \
     --environment Variables="{ENCRYPTION_ENABLED=false}"
   ```

2. **Restore from Backup**
   ```bash
   # Restore DynamoDB table from backup
   aws dynamodb restore-table-from-backup \
     --target-table-name aquachain-prod-users \
     --backup-arn arn:aws:dynamodb:REGION:ACCOUNT:table/aquachain-prod-users/backup/BACKUP_ID
   ```

3. **Rollback CDK Stack**
   ```bash
   cd infrastructure/cdk
   cdk destroy DataClassificationStack
   ```

## Success Criteria

- ✅ All PII fields encrypted with PII KMS key
- ✅ All SENSITIVE fields encrypted with SENSITIVE KMS key
- ✅ INTERNAL and PUBLIC fields not encrypted
- ✅ Encryption/decryption transparent to application
- ✅ No performance degradation (< 100ms added latency)
- ✅ No errors in production
- ✅ GDPR compliance requirements met
- ✅ Audit logging operational
- ✅ Monitoring and alerts configured
- ✅ Documentation complete

## Support Contacts

- **Security Team**: security@aquachain.com
- **DevOps Team**: devops@aquachain.com
- **On-Call Engineer**: oncall@aquachain.com

## References

- Implementation Summary: `TASK_19_DATA_CLASSIFICATION_ENCRYPTION_SUMMARY.md`
- Integration Guide: `lambda/shared/DATA_ENCRYPTION_INTEGRATION_GUIDE.md`
- Quick Reference: `DATA_CLASSIFICATION_QUICK_REFERENCE.md`
- AWS KMS Documentation: https://docs.aws.amazon.com/kms/

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Environment**: [ ] Dev [ ] Staging [ ] Production  
**Status**: [ ] Success [ ] Failed [ ] Rolled Back
