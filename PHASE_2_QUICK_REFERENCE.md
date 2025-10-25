# Phase 2 Quick Reference Guide

**Quick access to Phase 2 implementations**

---

## 🔐 IoT Security

### Device Policy
**Location:** `infrastructure/cdk/stacks/iot_security_stack.py`

**Key Features:**
- Device can only connect as itself (ClientId = ThingName)
- Restricted to own topics only
- Explicit deny for wildcards

**Deploy:**
```bash
cdk deploy AquaChain-IoTSecurity-dev
```

**Enable Logging:**
```bash
aws iot set-v2-logging-options \
  --role-arn <role-arn> \
  --default-log-level INFO
```

---

## 🤖 ML Model Versioning

### Model Manager
**Location:** `lambda/ml_inference/model_version_manager.py`

**Quick Start:**
```python
from model_version_manager import ModelVersionManager

manager = ModelVersionManager(
    s3_bucket='aquachain-ml-models-dev-123456789',
    dynamodb_table='aquachain-model-registry-dev'
)

# Register model
manager.register_model('wqi_predictor', 'v1.0.0', model, metrics)

# A/B test
manager.setup_ab_test('wqi_predictor', 'v1.0.0', 'v2.0.0', 0.5)

# Promote
manager.promote_to_active('wqi_predictor', 'v2.0.0')

# Rollback
manager.rollback_to_version('wqi_predictor', 'v1.0.0')
```

**Deploy:**
```bash
cdk deploy AquaChain-MLRegistry-dev
```

---

## 🚦 API Throttling

### Usage Tiers
**Location:** `infrastructure/cdk/stacks/api_throttling_stack.py`

| Tier | Rate | Burst | Quota |
|------|------|-------|-------|
| Free | 10/s | 20 | 1K/day |
| Standard | 100/s | 200 | 10K/day |
| Premium | 1K/s | 2K | 100K/day |
| Internal | 10K/s | 20K | Unlimited |

**Deploy:**
```bash
cdk deploy AquaChain-APIThrottling-dev
```

**Get API Key:**
```bash
aws apigateway get-api-key --api-key <key-id> --include-value
```

---

## 🌐 CloudFront CDN

### Distribution
**Location:** `infrastructure/cdk/stacks/cloudfront_stack.py`

**Features:**
- Global CDN
- WAF protection
- Rate limiting: 2000 req/5min
- Security headers
- SSL/TLS

**Deploy:**
```bash
# Build frontend first
cd frontend && npm run build

# Deploy
cd ../infrastructure/cdk
cdk deploy AquaChain-CloudFront-dev
```

**Invalidate Cache:**
```bash
aws cloudfront create-invalidation \
  --distribution-id <id> \
  --paths "/*"
```

---

## 📊 Monitoring

### Key Metrics

**IoT:**
- `AWS/IoT` → `Connect.AuthError`
- `AWS/IoT` → `PublishIn.ClientError`

**API:**
- `AWS/ApiGateway` → `4XXError`
- `AWS/ApiGateway` → `Latency`

**CloudFront:**
- `AWS/CloudFront` → `Requests`
- `AWS/CloudFront` → `4xxErrorRate`

---

## 🧪 Testing

### IoT Security
```bash
# Valid connection
mosquitto_pub \
  --cafile root-CA.crt \
  --cert device.crt \
  --key device.key \
  -h <endpoint> \
  -p 8883 \
  -t "aquachain/DEV-001/data" \
  -m '{"temp": 25.5}'
```

### API Throttling
```bash
# Test rate limit
for i in {1..150}; do
  curl -H "x-api-key: <key>" https://<api>/devices
  sleep 0.05
done
```

### CloudFront
```bash
# Check headers
curl -I https://<distribution>/ | grep -E "(Strict-Transport|X-Frame)"
```

---

## 🔧 Troubleshooting

### IoT Issues
```bash
# Check policy
aws iot get-policy --policy-name aquachain-device-policy-dev

# Check certificate
aws iot describe-certificate --certificate-id <id>
```

### CloudFront Issues
```bash
# Check distribution
aws cloudfront get-distribution --id <id>

# View logs
aws s3 ls s3://aquachain-cloudfront-logs-dev-<account>/
```

### API Issues
```bash
# Check usage plan
aws apigateway get-usage-plan --usage-plan-id <id>

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --start-time 2025-10-24T00:00:00Z \
  --end-time 2025-10-24T23:59:59Z \
  --period 300 \
  --statistics Sum
```

---

## 📁 File Locations

### New Files
- `infrastructure/cdk/stacks/iot_security_stack.py`
- `infrastructure/cdk/stacks/ml_model_registry_stack.py`
- `infrastructure/cdk/stacks/api_throttling_stack.py`
- `infrastructure/cdk/stacks/cloudfront_stack.py`
- `lambda/ml_inference/model_version_manager.py`

### Updated Files
- `infrastructure/cdk/app.py` (integrated all new stacks)

### Documentation
- `PHASE_2_IMPLEMENTATION.md` (comprehensive guide)
- `PHASE_2_QUICK_REFERENCE.md` (this file)
- `IMPLEMENTATION_PROGRESS.md` (updated progress)

---

## ✅ Completion Checklist

- [x] IoT security policies deployed
- [x] ML model registry created
- [x] API throttling configured
- [x] CloudFront distribution deployed
- [x] All stacks integrated in CDK app
- [x] Documentation created
- [x] Testing procedures documented
- [x] Monitoring configured
- [x] Troubleshooting guides written

---

**Phase 2 Status:** ✅ Complete  
**Next:** Phase 3 - Performance & Code Quality
