# Phase 2 Implementation Guide

**Date:** October 24, 2025  
**Status:** In Progress  
**Focus:** High-Priority Infrastructure & ML Systems

---

## Overview

Phase 2 builds on the critical security fixes from Phase 1 and implements high-priority infrastructure improvements, ML model versioning, and enhanced IoT security.

### Completed in Phase 2

1. ✅ **IoT Security Hardening**
   - Enhanced device policies with strict access controls
   - Device can only connect as itself (ClientId = ThingName)
   - Explicit deny for wildcard topics
   - Shadow operations restricted to own device
   - IoT logging enabled
   - Security monitoring with CloudWatch alarms

2. ✅ **ML Model Versioning System**
   - Complete model registry with DynamoDB + S3
   - A/B testing support with traffic splitting
   - Model rollback capabilities
   - Checksum verification for model integrity
   - Model caching with TTL
   - Performance metrics tracking

3. ✅ **API Gateway Throttling**
   - Tiered usage plans (Free, Standard, Premium, Internal)
   - Rate limiting per tier
   - Daily quotas
   - CloudWatch alarms for throttling events
   - API key management

4. ✅ **CloudFront Distribution**
   - Global CDN for frontend
   - WAF integration with managed rule sets
   - Rate limiting (2000 req/5min)
   - Security headers (HSTS, XSS, Frame Options)
   - S3 origin with OAI
   - SSL/TLS with ACM
   - Error page handling for SPA

5. ✅ **Enhanced CDK Stack Integration**
   - All new stacks integrated into main app
   - Proper dependency chain
   - VPC, Backup, and new security stacks included

---

## New Infrastructure Components

### 1. IoT Security Stack

**File:** `infrastructure/cdk/stacks/iot_security_stack.py`

**Features:**
- Strict device policies with condition-based access
- IoT Core logging to CloudWatch
- Security monitoring alarms:
  - Connection failures
  - Authentication failures
  - Publish failures
- Fleet indexing support

**Key Security Improvements:**
```python
# Device can only connect as itself
"Condition": {
    "StringEquals": {
        "iot:Connection.Thing.ThingName": "${iot:ClientId}"
    }
}

# Explicit deny for wildcard access
{
    "Effect": "Deny",
    "Action": ["iot:Publish", "iot:Subscribe", "iot:Receive"],
    "Resource": ["arn:aws:iot:*:*:topic/*"],
    "Condition": {
        "StringNotEquals": {
            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
        }
    }
}
```

**Deployment:**
```bash
cd infrastructure/cdk
cdk deploy AquaChain-IoTSecurity-dev
```

**Post-Deployment:**
```bash
# Enable IoT logging
aws iot set-v2-logging-options \
  --role-arn <IoTLoggingRoleArn from outputs> \
  --default-log-level INFO

# Enable fleet indexing
aws iot update-indexing-configuration \
  --thing-indexing-configuration thingIndexingMode=REGISTRY_AND_SHADOW
```

---

### 2. ML Model Registry Stack

**Files:**
- `infrastructure/cdk/stacks/ml_model_registry_stack.py`
- `lambda/ml_inference/model_version_manager.py`

**Features:**
- S3 bucket for model storage with versioning
- DynamoDB table for model metadata
- Model lifecycle management (active, testing, deprecated, archived)
- A/B testing with traffic splitting
- Rollback support
- Checksum verification
- Model caching

**Usage Example:**
```python
from model_version_manager import ModelVersionManager

# Initialize
manager = ModelVersionManager(
    s3_bucket='aquachain-ml-models-dev-123456789',
    dynamodb_table='aquachain-model-registry-dev'
)

# Register new model
metadata = manager.register_model(
    model_name='wqi_predictor',
    version='v2.0.0',
    model_object=trained_model,
    metrics={'rmse': 0.15, 'r2': 0.92},
    description='Improved WQI prediction with additional features'
)

# Setup A/B test (50/50 split)
manager.setup_ab_test(
    model_name='wqi_predictor',
    version_a='v1.0.0',
    version_b='v2.0.0',
    traffic_split=0.5
)

# Get model for request (handles A/B routing)
model, metadata = manager.get_model_for_request(
    model_name='wqi_predictor',
    request_id='unique-request-id'
)

# Promote to active after testing
manager.promote_to_active('wqi_predictor', 'v2.0.0')

# Rollback if needed
manager.rollback_to_version('wqi_predictor', 'v1.0.0')
```

**Deployment:**
```bash
cd infrastructure/cdk
cdk deploy AquaChain-MLRegistry-dev
```

---

### 3. API Throttling Stack

**File:** `infrastructure/cdk/stacks/api_throttling_stack.py`

**Usage Tiers:**

| Tier | Rate Limit | Burst | Daily Quota | Use Case |
|------|------------|-------|-------------|----------|
| Free | 10 req/s | 20 | 1,000 | Trial users |
| Standard | 100 req/s | 200 | 10,000 | Regular users |
| Premium | 1,000 req/s | 2,000 | 100,000 | High-volume users |
| Internal | 10,000 req/s | 20,000 | Unlimited | Internal services |

**CloudWatch Alarms:**
- 4XX errors > 50 in 5 minutes
- Throttling events > 100 in 5 minutes
- Latency > 1 second

**Deployment:**
```bash
cd infrastructure/cdk
cdk deploy AquaChain-APIThrottling-dev
```

**Retrieve API Keys:**
```bash
# Get API key value
aws apigateway get-api-key \
  --api-key <key-id-from-outputs> \
  --include-value
```

---

### 4. CloudFront Distribution Stack

**File:** `infrastructure/cdk/stacks/cloudfront_stack.py`

**Features:**
- Global CDN with edge locations
- WAF with managed rule sets:
  - Rate limiting (2000 req/5min per IP)
  - Common Rule Set (OWASP Top 10)
  - Known Bad Inputs protection
- Security headers:
  - Strict-Transport-Security (HSTS)
  - X-Content-Type-Options
  - X-Frame-Options: DENY
  - X-XSS-Protection
  - Referrer-Policy
- S3 origin with Origin Access Identity
- SSL/TLS with ACM certificate
- SPA error handling (403/404 → index.html)
- CloudFront access logging
- Brotli and Gzip compression

**Deployment:**
```bash
# Build frontend first
cd frontend
npm run build

# Deploy CloudFront stack
cd ../infrastructure/cdk
cdk deploy AquaChain-CloudFront-dev
```

**Custom Domain Setup (Optional):**
```typescript
// In config
{
  domain_name: 'app.aquachain.com',
  hosted_zone_id: 'Z1234567890ABC'
}
```

**Invalidate Cache:**
```bash
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/*"
```

---

## Updated CDK App Structure

**File:** `infrastructure/cdk/app.py`

**Stack Dependency Chain:**
```
Security Stack
    ↓
Core Stack
    ↓
Data Stack → Backup Stack
    ↓
Compute Stack
    ↓
API Stack → API Throttling Stack
    ↓
Monitoring Stack

Independent:
- VPC Stack
- CloudFront Stack
- IoT Security Stack
- ML Model Registry Stack
- Landing Page Stack
- DR Stack
```

---

## Deployment Instructions

### Full Deployment

```bash
cd infrastructure/cdk

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all --require-approval never

# Or deploy specific stacks
cdk deploy AquaChain-IoTSecurity-dev
cdk deploy AquaChain-MLRegistry-dev
cdk deploy AquaChain-APIThrottling-dev
cdk deploy AquaChain-CloudFront-dev
```

### Incremental Deployment

```bash
# Deploy only Phase 2 stacks
cdk deploy \
  AquaChain-IoTSecurity-dev \
  AquaChain-MLRegistry-dev \
  AquaChain-APIThrottling-dev \
  AquaChain-CloudFront-dev
```

---

## Testing

### 1. IoT Security Testing

```bash
# Test device connection with correct credentials
mosquitto_pub \
  --cafile root-CA.crt \
  --cert device.crt \
  --key device.key \
  -h <iot-endpoint> \
  -p 8883 \
  -t "aquachain/DEV-001/data" \
  -m '{"temperature": 25.5}'

# Test policy violation (should fail)
mosquitto_pub \
  --cafile root-CA.crt \
  --cert device.crt \
  --key device.key \
  -h <iot-endpoint> \
  -p 8883 \
  -t "aquachain/OTHER-DEVICE/data" \
  -m '{"temperature": 25.5}'
```

### 2. ML Model Versioning Testing

```python
# Test model registration and A/B testing
from model_version_manager import ModelVersionManager

manager = ModelVersionManager(
    s3_bucket='aquachain-ml-models-dev-123456789',
    dynamodb_table='aquachain-model-registry-dev'
)

# Register two versions
manager.register_model('test_model', 'v1.0.0', model_v1, {'accuracy': 0.85})
manager.register_model('test_model', 'v2.0.0', model_v2, {'accuracy': 0.90})

# Setup A/B test
manager.setup_ab_test('test_model', 'v1.0.0', 'v2.0.0', 0.5)

# Test routing consistency
for i in range(100):
    model, metadata = manager.get_model_for_request('test_model', f'request-{i}')
    print(f"Request {i}: {metadata.version}")
```

### 3. API Throttling Testing

```bash
# Test rate limiting
for i in {1..150}; do
  curl -H "x-api-key: <api-key>" \
    https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/devices
  sleep 0.05
done

# Should see 429 responses after exceeding rate limit
```

### 4. CloudFront Testing

```bash
# Test CloudFront distribution
curl -I https://<distribution-domain>/

# Check security headers
curl -I https://<distribution-domain>/ | grep -E "(Strict-Transport|X-Frame|X-Content)"

# Test WAF rate limiting
for i in {1..2500}; do
  curl https://<distribution-domain>/
done
# Should get blocked after 2000 requests in 5 minutes
```

---

## Monitoring

### CloudWatch Dashboards

Create custom dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name AquaChain-Phase2 \
  --dashboard-body file://phase2-dashboard.json
```

### Key Metrics to Monitor

**IoT Security:**
- `AWS/IoT` → `Connect.AuthError`
- `AWS/IoT` → `Connect.ClientError`
- `AWS/IoT` → `PublishIn.ClientError`

**API Throttling:**
- `AWS/ApiGateway` → `4XXError`
- `AWS/ApiGateway` → `Count` (throttled requests)
- `AWS/ApiGateway` → `Latency`

**CloudFront:**
- `AWS/CloudFront` → `Requests`
- `AWS/CloudFront` → `BytesDownloaded`
- `AWS/CloudFront` → `4xxErrorRate`
- `AWS/CloudFront` → `5xxErrorRate`

**ML Models:**
- Custom metrics in DynamoDB
- Model load times
- Prediction latencies
- A/B test traffic distribution

---

## Cost Optimization

### Estimated Monthly Costs (Development)

| Service | Usage | Cost |
|---------|-------|------|
| IoT Core | 100 devices, 1M messages | $8 |
| CloudFront | 100GB transfer, 1M requests | $12 |
| API Gateway | 1M requests | $3.50 |
| DynamoDB (Model Registry) | 1GB storage, 100K reads | $1 |
| S3 (Models) | 10GB storage | $0.23 |
| CloudWatch Logs | 5GB ingestion | $2.50 |
| **Total** | | **~$27/month** |

### Cost Optimization Tips

1. **CloudFront:** Use Price Class 100 (US, Canada, Europe only)
2. **S3:** Enable Intelligent-Tiering for model storage
3. **DynamoDB:** Use on-demand billing for variable workloads
4. **API Gateway:** Use HTTP API instead of REST API where possible
5. **CloudWatch:** Set appropriate log retention periods

---

## Security Checklist

- [x] IoT device policies enforce ClientId = ThingName
- [x] Explicit deny for wildcard topic access
- [x] IoT logging enabled
- [x] CloudFront WAF with rate limiting
- [x] API Gateway throttling configured
- [x] Model checksum verification
- [x] S3 buckets block public access
- [x] DynamoDB point-in-time recovery enabled
- [x] Security headers on CloudFront
- [x] CloudWatch alarms for security events

---

## Troubleshooting

### IoT Connection Issues

```bash
# Check device policy
aws iot get-policy --policy-name aquachain-device-policy-dev

# Check thing attachment
aws iot list-thing-principals --thing-name DEV-001

# Check certificate status
aws iot describe-certificate --certificate-id <cert-id>
```

### CloudFront Issues

```bash
# Check distribution status
aws cloudfront get-distribution --id <distribution-id>

# Check WAF rules
aws wafv2 get-web-acl --scope CLOUDFRONT --id <web-acl-id>

# View CloudFront logs
aws s3 ls s3://aquachain-cloudfront-logs-dev-<account>/cloudfront/
```

### API Throttling Issues

```bash
# Check usage plan
aws apigateway get-usage-plan --usage-plan-id <plan-id>

# Check API key
aws apigateway get-api-key --api-key <key-id> --include-value

# View throttling metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=AquaChain \
  --start-time 2025-10-24T00:00:00Z \
  --end-time 2025-10-24T23:59:59Z \
  --period 300 \
  --statistics Sum
```

---

## Next Steps (Phase 3)

1. **Performance Optimization**
   - Lambda cold start reduction
   - Database query optimization
   - React component optimization

2. **Code Quality**
   - Type annotations
   - Unit test coverage to 80%
   - Dashboard refactoring

3. **ML Enhancements**
   - Model performance monitoring
   - Automated retraining triggers
   - Feature store implementation

4. **Compliance**
   - GDPR features
   - Audit logging
   - Data classification

---

## Resources

- [IoT Security Best Practices](https://docs.aws.amazon.com/iot/latest/developerguide/security-best-practices.html)
- [CloudFront Security](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/security.html)
- [API Gateway Throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)
- [ML Model Versioning](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html)

---

**Status:** Phase 2 Complete ✅  
**Next Review:** October 25, 2025
