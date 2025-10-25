# Phase 3 Implementation Guide

## Overview

This guide provides comprehensive documentation for Phase 3 of the AquaChain water quality monitoring platform. Phase 3 implements ML model monitoring, IoT security enhancements, dependency management, and performance observability to achieve 80% production readiness.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Components](#components)
3. [Deployment Instructions](#deployment-instructions)
4. [Testing Procedures](#testing-procedures)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Operational Runbooks](#operational-runbooks)

---

## Architecture Overview

Phase 3 introduces seven major systems:

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 3 Components                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ ML Monitoring│    │ OTA Updates  │    │  Certificate │  │
│  │   System     │    │   System     │    │   Rotation   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┼────────────────────┘          │
│                              │                               │
│         ┌────────────────────┴────────────────────┐          │
│         │      CloudWatch Monitoring               │          │
│         │  ┌──────────┐  ┌──────────┐            │          │
│         │  │Dashboard │  │  Alarms  │            │          │
│         │  └──────────┘  └──────────┘            │          │
│         └──────────────────────────────────────────┘          │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Dependency  │    │     SBOM     │    │    Data      │  │
│  │   Scanner    │    │  Generator   │    │  Validator   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **ML Model Monitoring**: Real-time drift detection and automated retraining
- **Training Data Validation**: Quality checks for ML training data
- **OTA Firmware Updates**: Secure over-the-air updates for IoT devices
- **Certificate Rotation**: Automated zero-downtime certificate lifecycle management
- **Dependency Security**: Weekly vulnerability scanning for npm and Python packages
- **SBOM Generation**: Automated software bill of materials for compliance
- **Performance Dashboard**: Centralized CloudWatch monitoring

---

## Components

### 1. ML Model Monitoring System

**Location**: `lambda/ml_inference/model_performance_monitor.py`

**Purpose**: Track ML model performance and detect drift in real-time

**Key Features**:
- Async prediction logging to avoid latency impact
- Rolling window drift detection (last 1000 predictions)
- Configurable drift threshold (default: 15%)
- Automated retraining after 10 consecutive drift detections

**DynamoDB Table**: `ModelMetrics`
- Primary Key: `model_name`
- Sort Key: `timestamp`
- GSI: `drift_score-index` for querying high drift scores
- TTL: 90 days

**CloudWatch Alarms**:
- Drift score > 0.15 for 10 minutes
- Prediction latency > 500ms
- Error rate > 1%

**Documentation**: See `lambda/ml_inference/ML_MONITORING_IMPLEMENTATION.md`

---

### 2. Training Data Validation System

**Location**: `lambda/ml_training/training_data_validator.py`

**Purpose**: Validate training data quality before model training

**Key Features**:
- NaN and infinite value detection
- Feature range validation
- Label distribution checks (minimum 5% per class)
- Automated quality reports

**S3 Trigger**: Validates data on upload to training data bucket

**SNS Alerts**: Sends notifications for validation failures

**Documentation**: See `lambda/ml_training/IMPLEMENTATION_SUMMARY.md`

---

### 3. OTA Firmware Update System

**Location**: `lambda/iot_management/ota_update_manager.py`

**Purpose**: Securely distribute firmware updates to IoT devices

**Key Features**:
- AWS IoT code signing for firmware integrity
- Gradual rollout (10% → 50% → 100%)
- Automatic rollback on failure
- Device certificate verification

**IoT Jobs**: Manages firmware distribution and tracking

**ESP32 Integration**: See `iot-simulator/esp32-firmware/aquachain-device/ota_update.h`

**Documentation**: See `lambda/iot_management/OTA_IMPLEMENTATION_SUMMARY.md`

---

### 4. Certificate Rotation System

**Location**: `lambda/iot_management/certificate_rotation.py`

**Purpose**: Automate certificate lifecycle management

**Key Features**:
- Zero-downtime rotation strategy
- 30-day expiration warning
- 7-day critical alerts
- MQTT-based certificate provisioning

**DynamoDB Table**: `CertificateLifecycle`
- Primary Key: `device_id`
- Sort Key: `certificate_id`
- GSI: `expiration_date-index` for expiration queries
- GSI: `status-index` for status tracking

**EventBridge Schedule**: Daily checks for expiring certificates

**Documentation**: See `lambda/iot_management/CERTIFICATE_ROTATION_IMPLEMENTATION.md`

---

### 5. Dependency Security Management

**Location**: `lambda/dependency_scanner/dependency_scanner.py`

**Purpose**: Automated vulnerability scanning for dependencies

**Key Features**:
- npm audit integration for frontend
- pip-audit integration for backend
- Severity categorization (critical, high, medium, low)
- Weekly automated scans

**S3 Storage**: Vulnerability reports stored with versioning

**SNS Alerts**: Critical vulnerabilities trigger immediate notifications

**Documentation**: See `lambda/dependency_scanner/README.md`

---

### 6. SBOM Generation System

**Location**: `scripts/generate-sbom.py`

**Purpose**: Generate software bill of materials for compliance

**Key Features**:
- Syft for SBOM generation (SPDX format)
- Grype for vulnerability scanning
- CI/CD integration (GitHub Actions)
- S3 storage with versioning

**GitHub Workflows**:
- `.github/workflows/ci-cd-pipeline.yml` - On code push
- `.github/workflows/sbom-weekly.yml` - Weekly schedule

**Documentation**: See `DOCS/sbom-generation-guide.md`

---

### 7. Performance Monitoring Dashboard

**Location**: `infrastructure/cdk/stacks/performance_dashboard_stack.py`

**Purpose**: Centralized performance monitoring

**Metrics Tracked**:
- **API Gateway**: Response time (p50, p95, p99), error rate, throttling
- **Lambda**: Duration, errors, cold starts, concurrency
- **DynamoDB**: Read/write capacity, throttling, latency
- **IoT Core**: Connected devices, message rate, errors
- **ML Models**: Prediction latency, drift score, accuracy

**CloudWatch Alarms**:
- API response time > 1 second
- Lambda error rate > 1%
- DynamoDB throttling events
- IoT connection failures
- ML drift score > 0.15

**Documentation**: See `infrastructure/cdk/stacks/PERFORMANCE_DASHBOARD_GUIDE.md`

---

## Deployment Instructions

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **AWS CDK** installed (`npm install -g aws-cdk`)
3. **Python 3.9+** with boto3, aws-cdk-lib
4. **Node.js 16+** for frontend
5. **Docker** for Lambda layer builds

### Environment Setup

1. Configure infrastructure environment:
```bash
cd infrastructure
cp .env.example .env
# Edit .env with your AWS account details
```

2. Install dependencies:
```bash
# CDK dependencies
cd infrastructure/cdk
pip install -r requirements.txt

# Lambda dependencies
cd ../../lambda
for dir in */; do
  if [ -f "$dir/requirements.txt" ]; then
    pip install -r "$dir/requirements.txt" -t "$dir/"
  fi
done
```

### Deployment Steps

#### Option 1: Full Phase 3 Deployment

Deploy all Phase 3 components at once:

```bash
cd infrastructure/cdk
./deploy-phase3.sh
```

This script will:
1. Deploy Phase 3 infrastructure stack
2. Deploy ML monitoring components
3. Deploy IoT management components
4. Deploy dependency scanner
5. Deploy SBOM storage
6. Deploy performance dashboard
7. Run smoke tests

#### Option 2: Incremental Deployment

Deploy components individually:

```bash
cd infrastructure/cdk

# 1. Deploy infrastructure foundation
cdk deploy Phase3InfrastructureStack

# 2. Deploy ML monitoring
cdk deploy TrainingDataValidationStack

# 3. Deploy IoT security
cdk deploy IoTCodeSigningStack

# 4. Deploy dependency management
cdk deploy DependencyScannerStac
k

# 5. Deploy SBOM storage
cdk deploy SBOMStorageStack

# 6. Deploy performance dashboard
cdk deploy PerformanceDashboardStack
```

#### Option 3: Using deploy-all.sh

The main deployment script now includes Phase 3:

```bash
cd infrastructure/cdk
./deploy-all.sh --phase 3
```

### Post-Deployment Configuration

1. **Configure EventBridge Schedules**:
```bash
# Certificate rotation (daily)
aws events put-rule --name certificate-rotation-daily \
  --schedule-expression "cron(0 2 * * ? *)"

# Dependency scanning (weekly)
aws events put-rule --name dependency-scan-weekly \
  --schedule-expression "cron(0 3 ? * SUN *)"

# SBOM generation (weekly)
aws events put-rule --name sbom-generation-weekly \
  --schedule-expression "cron(0 4 ? * SUN *)"
```

2. **Set up SNS Subscriptions**:
```bash
# Subscribe to critical alerts
aws sns subscribe --topic-arn arn:aws:sns:REGION:ACCOUNT:critical-alerts \
  --protocol email --notification-endpoint your-email@example.com

# Subscribe to vulnerability alerts
aws sns subscribe --topic-arn arn:aws:sns:REGION:ACCOUNT:vulnerability-alerts \
  --protocol email --notification-endpoint security-team@example.com
```

3. **Configure IoT Code Signing**:
```bash
cd infrastructure/iot
python setup-code-signing.py
```

4. **Initialize SBOM Generation**:
```bash
cd scripts
python generate-sbom.py --all
```

### Verification

Run the Phase 3 test suite to verify deployment:

```bash
cd tests
python run_phase3_tests.py
```

Expected output:
```
✓ ML monitoring operational
✓ Data validation functional
✓ OTA updates configured
✓ Certificate rotation active
✓ Dependency scanner running
✓ SBOM generation working
✓ Performance dashboard accessible
```

---

## Testing Procedures

### Unit Tests

Test individual components:

```bash
# ML monitoring
cd lambda/ml_inference
python -m pytest test_model_performance_monitor.py -v

# Data validation
cd lambda/ml_training
python -m pytest test_training_data_validator.py -v

# OTA updates
cd lambda/iot_management
python -m pytest test_ota_integration.py -v

# Certificate rotation
cd lambda/iot_management
python -m pytest test_certificate_rotation.py -v

# Dependency scanner
cd lambda/dependency_scanner
python -m pytest test_dependency_scanner.py -v
```

### Integration Tests

Test end-to-end workflows:

```bash
cd tests/integration
python -m pytest test_phase3_e2e.py -v
```

Tests include:
- ML monitoring with live predictions
- OTA updates with test devices
- Certificate rotation workflow
- Dependency scanning and SBOM generation

### Performance Tests

Validate performance requirements:

```bash
cd tests/performance
python -m pytest test_phase3_performance.py -v
```

Tests include:
- ML monitoring latency (<50ms overhead)
- Certificate rotation speed (<5 minutes)
- SBOM generation time (<2 minutes)
- Dashboard query performance (<1 second)

### Security Tests

Validate security controls:

```bash
cd tests/security
python -m pytest test_phase3_security.py -v
```

Tests include:
- OTA firmware signature verification
- Certificate validation
- Vulnerability scanning accuracy
- IAM permission validation

### Smoke Tests

Quick validation after deployment:

```bash
cd tests
python run_phase3_tests.py --smoke
```

---

## Troubleshooting Guide

### ML Monitoring Issues

#### Problem: High drift scores detected

**Symptoms**: CloudWatch alarm triggered, drift score > 0.15

**Diagnosis**:
```bash
# Check recent predictions
aws dynamodb query --table-name ModelMetrics \
  --key-condition-expression "model_name = :mn" \
  --expression-attribute-values '{":mn":{"S":"water-quality-v1"}}' \
  --limit 100
```

**Solutions**:
1. Review recent data quality
2. Check for sensor calibration issues
3. Trigger manual retraining if needed:
```bash
aws lambda invoke --function-name ml-training-trigger \
  --payload '{"model_name":"water-quality-v1","reason":"manual"}' \
  response.json
```

#### Problem: Prediction latency high

**Symptoms**: Latency > 500ms

**Diagnosis**:
```bash
# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=ml-inference \
  --start-time 2025-10-24T00:00:00Z \
  --end-time 2025-10-24T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum
```

**Solutions**:
1. Increase Lambda memory allocation
2. Enable provisioned concurrency
3. Optimize model size
4. Check DynamoDB throttling

---

### OTA Update Issues

#### Problem: Firmware update fails

**Symptoms**: Device reports update failure, rollback triggered

**Diagnosis**:
```bash
# Check IoT job status
aws iot describe-job --job-id firmware-update-v2.0.0

# Check device logs
aws iot-data get-thing-shadow --thing-name device-001
```

**Solutions**:
1. Verify firmware signature:
```bash
aws signer get-signing-profile --profile-name aquachain-firmware
```

2. Check device connectivity:
```bash
aws iot describe-thing --thing-name device-001
```

3. Retry update with smaller device group:
```python
# Update rollout configuration
rollout_config = {
    "maximumPerMinute": 5,
    "exponentialRate": {
        "baseRatePerMinute": 10,
        "incrementFactor": 2,
        "rateIncreaseCriteria": {
            "numberOfSucceededThings": 10
        }
    }
}
```

#### Problem: Signature verification fails

**Symptoms**: Device rejects firmware, "Invalid signature" error

**Diagnosis**:
```bash
# Verify code signing configuration
aws signer list-signing-jobs --status Succeeded
```

**Solutions**:
1. Re-sign firmware:
```bash
cd infrastructure/iot
python setup-code-signing.py --resign firmware-v2.0.0.bin
```

2. Update device certificates if expired
3. Check device time synchronization (NTP)

---

### Certificate Rotation Issues

#### Problem: Certificate rotation fails

**Symptoms**: Device unreachable, rotation timeout

**Diagnosis**:
```bash
# Check certificate status
aws dynamodb get-item --table-name CertificateLifecycle \
  --key '{"device_id":{"S":"device-001"},"certificate_id":{"S":"cert-123"}}'

# Check device connection
aws iot describe-thing --thing-name device-001
```

**Solutions**:
1. Verify device is online:
```bash
aws iot-data get-thing-shadow --thing-name device-001 | \
  jq '.state.reported.connected'
```

2. Manually provision certificate:
```bash
cd iot-simulator
python provision-device.py --device-id device-001 --rotate
```

3. Extend old certificate validity temporarily:
```bash
aws iot update-certificate --certificate-id cert-123 \
  --new-status ACTIVE
```

#### Problem: Zero-downtime rotation causes brief disconnection

**Symptoms**: Device disconnects for 1-2 seconds during rotation

**Diagnosis**: Check device logs for connection events

**Solutions**:
1. Increase confirmation timeout in rotation Lambda
2. Implement connection retry logic on device
3. Use connection state machine for smoother transitions

---

### Dependency Scanner Issues

#### Problem: Scanner fails to run

**Symptoms**: EventBridge schedule triggers but no reports generated

**Diagnosis**:
```bash
# Check Lambda logs
aws logs tail /aws/lambda/dependency-scanner --follow

# Check S3 for reports
aws s3 ls s3://aquachain-vulnerability-reports/
```

**Solutions**:
1. Verify Lambda has npm and pip-audit installed:
```bash
# Update Lambda layer
cd lambda/dependency_scanner
./build-layer.sh
```

2. Check IAM permissions for S3 write access

3. Manually trigger scan:
```bash
aws lambda invoke --function-name dependency-scanner \
  --payload '{"scan_type":"all"}' \
  response.json
```

#### Problem: False positives in vulnerability reports

**Symptoms**: Known-safe packages flagged as vulnerable

**Diagnosis**: Review vulnerability report details

**Solutions**:
1. Add exceptions to scanner configuration:
```python
# In dependency_scanner.py
EXCEPTIONS = {
    "package-name": ["CVE-2021-12345"],  # Reason: Not applicable
}
```

2. Update vulnerability database:
```bash
npm audit fix
pip-audit --fix
```

---

### SBOM Generation Issues

#### Problem: SBOM generation fails

**Symptoms**: GitHub Action fails, no SBOM in S3

**Diagnosis**:
```bash
# Check GitHub Actions logs
gh run list --workflow=sbom-weekly.yml

# Check S3 bucket
aws s3 ls s3://aquachain-sbom-storage/
```

**Solutions**:
1. Verify Syft and Grype are installed:
```bash
syft version
grype version
```

2. Manually generate SBOM:
```bash
cd scripts
python generate-sbom.py --component frontend
```

3. Check S3 bucket permissions

#### Problem: SBOM contains incorrect dependencies

**Symptoms**: Missing or extra packages in SBOM

**Diagnosis**: Review SBOM content

**Solutions**:
1. Update Syft configuration:
```yaml
# .syft.yaml
exclude:
  - "**/node_modules/**"
  - "**/.venv/**"
```

2. Clean and rebuild:
```bash
rm -rf node_modules
npm install
python generate-sbom.py --clean
```

---

### Performance Dashboard Issues

#### Problem: Dashboard not loading

**Symptoms**: CloudWatch dashboard shows "No data"

**Diagnosis**:
```bash
# Check if metrics are being published
aws cloudwatch list-metrics --namespace AquaChain
```

**Solutions**:
1. Verify metric publishing in Lambda functions
2. Check CloudWatch Logs for errors
3. Redeploy dashboard stack:
```bash
cdk deploy PerformanceDashboardStack --force
```

#### Problem: Alarms not triggering

**Symptoms**: Performance issues but no alerts received

**Diagnosis**:
```bash
# Check alarm state
aws cloudwatch describe-alarms --alarm-names ml-drift-alarm

# Check SNS subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:REGION:ACCOUNT:critical-alerts
```

**Solutions**:
1. Verify SNS email subscription confirmed
2. Check alarm threshold configuration
3. Test alarm manually:
```bash
aws cloudwatch set-alarm-state --alarm-name ml-drift-alarm \
  --state-value ALARM --state-reason "Test"
```

---

## Operational Runbooks

### ML Model Retraining Procedure

**When to Use**: Drift detected, model performance degraded, new training data available

**Prerequisites**:
- Training data validated and available in S3
- SageMaker training job configured
- Model registry accessible

**Steps**:

1. **Trigger Retraining**:
```bash
aws lambda invoke --function-name ml-training-trigger \
  --payload '{
    "model_name": "water-quality-v1",
    "training_data_path": "s3://aquachain-training-data/2025-10-24/",
    "reason": "drift_detected"
  }' \
  response.json
```

2. **Monitor Training Progress**:
```bash
# Get training job name from response.json
TRAINING_JOB=$(cat response.json | jq -r '.training_job_name')

# Monitor status
aws sagemaker describe-training-job --training-job-name $TRAINING_JOB
```

3. **Validate New Model**:
```bash
# Run validation tests
cd tests/integration
python test_ml_model_validation.py --model-version v2
```

4. **Deploy New Model**:
```bash
# Update model version in inference Lambda
aws lambda update-function-configuration \
  --function-name ml-inference \
  --environment Variables={MODEL_VERSION=v2}
```

5. **Monitor Post-Deployment**:
```bash
# Watch drift scores for 24 hours
aws cloudwatch get-metric-statistics \
  --namespace AquaChain \
  --metric-name DriftScore \
  --dimensions Name=ModelVersion,Value=v2 \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average
```

6. **Rollback if Needed**:
```bash
# Revert to previous version
aws lambda update-function-configuration \
  --function-name ml-inference \
  --environment Variables={MODEL_VERSION=v1}
```

---

### OTA Update Rollout Procedure

**When to Use**: New firmware version available, security patches, feature updates

**Prerequisites**:
- Firmware tested in development
- Code signing profile configured
- Test devices available

**Steps**:

1. **Prepare Firmware**:
```bash
# Upload firmware to S3
aws s3 cp firmware-v2.0.0.bin s3://aquachain-firmware/

# Sign firmware
cd infrastructure/iot
python setup-code-signing.py --sign firmware-v2.0.0.bin
```

2. **Test with Pilot Devices** (10%):
```python
# Create test job
python -c "
from lambda.iot_management.ota_update_manager import OTAManager

manager = OTAManager()
job_id = manager.create_firmware_job(
    firmware_version='v2.0.0',
    device_group='pilot-devices',
    rollout_config={
        'maximumPerMinute': 2,
        'exponentialRate': {
            'baseRatePerMinute': 5,
            'incrementFactor': 1.5
        }
    }
)
print(f'Job ID: {job_id}')
"
```

3. **Monitor Pilot Rollout**:
```bash
# Check job status every 5 minutes
watch -n 300 'aws iot describe-job --job-id firmware-update-v2.0.0'

# Check for failures
aws iot list-job-executions --job-id firmware-update-v2.0.0 \
  --status FAILED
```

4. **Expand to 50% of Devices**:
```bash
# If pilot successful, expand rollout
aws iot update-job --job-id firmware-update-v2.0.0 \
  --job-executions-rollout-config '{
    "maximumPerMinute": 10,
    "exponentialRate": {
      "baseRatePerMinute": 20,
      "incrementFactor": 2
    }
  }'
```

5. **Full Rollout** (100%):
```bash
# After 50% success, complete rollout
aws iot update-job --job-id firmware-update-v2.0.0 \
  --job-executions-rollout-config '{
    "maximumPerMinute": 50
  }'
```

6. **Handle Failures**:
```bash
# If failure rate > 5%, pause and investigate
aws iot update-job --job-id firmware-update-v2.0.0 \
  --abort-config '{
    "criteriaList": [{
      "failureType": "FAILED",
      "action": "CANCEL",
      "thresholdPercentage": 5,
      "minNumberOfExecutedThings": 10
    }]
  }'

# Rollback failed devices
python -c "
from lambda.iot_management.ota_update_manager import OTAManager

manager = OTAManager()
failed_devices = manager.get_failed_devices('firmware-update-v2.0.0')
for device_id in failed_devices:
    manager.rollback_firmware(device_id, 'v1.9.0')
"
```

---

### Certificate Rotation Troubleshooting

**When to Use**: Certificate expiring soon, rotation failures, device connectivity issues

**Prerequisites**:
- Device online and connected
- Certificate lifecycle table accessible
- MQTT broker operational

**Steps**:

1. **Check Certificate Status**:
```bash
# List expiring certificates
aws dynamodb query --table-name CertificateLifecycle \
  --index-name expiration_date-index \
  --key-condition-expression "expiration_date < :date" \
  --expression-attribute-values '{":date":{"S":"2025-11-24"}}'
```

2. **Verify Device Connectivity**:
```bash
# Check device shadow
aws iot-data get-thing-shadow --thing-name device-001 | \
  jq '.state.reported'

# Check last connection time
aws iot describe-thing --thing-name device-001 | \
  jq '.attributes.lastConnected'
```

3. **Manual Certificate Rotation**:
```bash
# Trigger rotation for specific device
cd iot-simulator
python provision-device.py --device-id device-001 --rotate

# Or use Lambda directly
aws lambda invoke --function-name certificate-rotation \
  --payload '{"device_id":"device-001","force":true}' \
  response.json
```

4. **Monitor Rotation Progress**:
```bash
# Check rotation status
aws dynamodb get-item --table-name CertificateLifecycle \
  --key '{"device_id":{"S":"device-001"},"certificate_id":{"S":"new-cert-id"}}' | \
  jq '.Item.status.S'
```

5. **Handle Rotation Failure**:
```bash
# If device doesn't confirm new cert, extend old cert
aws iot update-certificate --certificate-id old-cert-id \
  --new-status ACTIVE

# Retry rotation with longer timeout
aws lambda update-function-configuration \
  --function-name certificate-rotation \
  --environment Variables={CONFIRMATION_TIMEOUT=600}

# Retry
aws lambda invoke --function-name certificate-rotation \
  --payload '{"device_id":"device-001","retry":true}' \
  response.json
```

6. **Verify Successful Rotation**:
```bash
# Check device is using new certificate
aws iot list-thing-principals --thing-name device-001

# Verify old certificate deactivated
aws iot describe-certificate --certificate-id old-cert-id | \
  jq '.certificateDescription.status'
```

---

### Dependency Update Procedure

**When to Use**: Critical vulnerabilities detected, weekly maintenance, major version updates

**Prerequisites**:
- Vulnerability report reviewed
- Test environment available
- Backup of current dependencies

**Steps**:

1. **Review Vulnerability Report**:
```bash
# Get latest report
aws s3 cp s3://aquachain-vulnerability-reports/latest.json ./

# Review critical vulnerabilities
cat latest.json | jq '.vulnerabilities[] | select(.severity=="critical")'
```

2. **Update Frontend Dependencies**:
```bash
cd frontend

# Backup current package-lock.json
cp package-lock.json package-lock.json.backup

# Update specific package
npm update axios

# Or update all packages
npm update

# Run tests
npm test

# Build and verify
npm run build
```

3. **Update Backend Dependencies**:
```bash
cd lambda

# For each Lambda function
for dir in */; do
  if [ -f "$dir/requirements.txt" ]; then
    cd "$dir"
    
    # Backup
    cp requirements.txt requirements.txt.backup
    
    # Update specific package
    pip install --upgrade boto3
    pip freeze > requirements.txt
    
    # Run tests
    python -m pytest
    
    cd ..
  fi
done
```

4. **Test in Development**:
```bash
# Deploy to dev environment
cd infrastructure/cdk
cdk deploy --all --context environment=dev

# Run integration tests
cd ../../tests
python run_phase3_tests.py --environment dev
```

5. **Deploy to Staging**:
```bash
# Deploy to staging
cd infrastructure/cdk
cdk deploy --all --context environment=staging

# Run smoke tests
cd ../../tests
python run_phase3_tests.py --smoke --environment staging
```

6. **Deploy to Production**:
```bash
# Deploy to production
cd infrastructure/cdk
cdk deploy --all --context environment=production

# Monitor for issues
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

7. **Rollback if Needed**:
```bash
# Restore previous dependencies
cd frontend
cp package-lock.json.backup package-lock.json
npm install

# Redeploy previous version
cd infrastructure/cdk
cdk deploy --all --context version=previous
```

---

## Performance Optimization

### ML Monitoring Optimization

**Reduce Latency**:
1. Enable Lambda provisioned concurrency
2. Increase Lambda memory (reduces CPU throttling)
3. Use DynamoDB batch writes for metrics
4. Implement metric caching with TTL

**Reduce Costs**:
1. Use DynamoDB on-demand pricing for variable workloads
2. Set appropriate TTL for metrics (90 days)
3. Use CloudWatch Logs Insights instead of storing all logs
4. Batch predictions when possible

### OTA Update Optimization

**Faster Rollouts**:
1. Increase rollout rate after successful pilot
2. Use parallel job execution
3. Optimize firmware size (compression)
4. Use CDN for firmware distribution

**Reduce Failures**:
1. Implement pre-update device health checks
2. Use staged rollouts (10% → 50% → 100%)
3. Implement automatic retry with exponential backoff
4. Monitor device battery levels before updates

### Certificate Rotation Optimization

**Reduce Rotation Time**:
1. Batch certificate generation
2. Use parallel MQTT provisioning
3. Implement certificate pre-generation
4. Optimize confirmation timeout

**Improve Reliability**:
1. Implement retry logic with exponential backoff
2. Use device queues for offline devices
3. Monitor device connectivity before rotation
4. Implement graceful degradation

---

## Security Best Practices

### ML Model Security

1. **Model Integrity**:
   - Sign model artifacts
   - Verify checksums before deployment
   - Use versioned S3 buckets

2. **Data Privacy**:
   - Encrypt training data at rest
   - Use VPC endpoints for S3 access
   - Implement data retention policies

3. **Access Control**:
   - Use IAM roles with least privilege
   - Enable CloudTrail logging
   - Implement MFA for model deployment

### IoT Security

1. **Device Authentication**:
   - Use X.509 certificates
   - Implement certificate pinning
   - Rotate certificates regularly

2. **Firmware Security**:
   - Sign all firmware images
   - Verify signatures on device
   - Use secure boot

3. **Communication Security**:
   - Use TLS 1.3 for MQTT
   - Implement message encryption
   - Use AWS IoT policies for authorization

### Dependency Security

1. **Vulnerability Management**:
   - Scan dependencies weekly
   - Prioritize critical vulnerabilities
   - Implement automated patching

2. **Supply Chain Security**:
   - Generate and maintain SBOM
   - Verify package signatures
   - Use private package registries

3. **Compliance**:
   - Track license compliance
   - Document security exceptions
   - Maintain audit trail

---

## Monitoring and Alerting

### Critical Alerts (Immediate Response)

- ML drift score > 0.20
- OTA update failure rate > 10%
- Certificate expiring in 24 hours
- Critical vulnerability detected
- API error rate > 5%

### Warning Alerts (Review within 24 hours)

- ML drift score > 0.15
- OTA update failure rate > 5%
- Certificate expiring in 7 days
- High severity vulnerability detected
- API latency > 1 second

### Info Alerts (Review weekly)

- ML model retrained
- OTA update completed
- Certificate rotated successfully
- Dependency scan completed
- SBOM generated

---

## Maintenance Schedule

### Daily

- Certificate expiration checks
- Performance dashboard review
- Error log review

### Weekly

- Dependency vulnerability scanning
- SBOM generation
- Performance optimization review
- Security audit log review

### Monthly

- ML model performance review
- OTA firmware planning
- Certificate lifecycle audit
- Dependency update planning

### Quarterly

- Full security audit
- Performance benchmarking
- Disaster recovery testing
- Documentation review

---

## Support and Resources

### Documentation

- **Phase 3 Requirements**: `.kiro/specs/phase-3-high-priority/requirements.md`
- **Phase 3 Design**: `.kiro/specs/phase-3-high-priority/design.md`
- **Phase 3 Tasks**: `.kiro/specs/phase-3-high-priority/tasks.md`
- **Test Guide**: `tests/PHASE3_TEST_GUIDE.md`
- **SBOM Guide**: `DOCS/sbom-generation-guide.md`

### Component Documentation

- ML Monitoring: `lambda/ml_inference/ML_MONITORING_IMPLEMENTATION.md`
- Data Validation: `lambda/ml_training/IMPLEMENTATION_SUMMARY.md`
- OTA Updates: `lambda/iot_management/OTA_IMPLEMENTATION_SUMMARY.md`
- Certificate Rotation: `lambda/iot_management/CERTIFICATE_ROTATION_IMPLEMENTATION.md`
- Dependency Scanner: `lambda/dependency_scanner/README.md`
- Performance Dashboard: `infrastructure/cdk/stacks/PERFORMANCE_DASHBOARD_GUIDE.md`

### AWS Resources

- CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=AquaChain-Performance
- IoT Core Console: https://console.aws.amazon.com/iot/home
- SageMaker Console: https://console.aws.amazon.com/sagemaker/home
- Lambda Console: https://console.aws.amazon.com/lambda/home

### Contact

- **DevOps Team**: devops@aquachain.example.com
- **Security Team**: security@aquachain.example.com
- **ML Team**: ml-team@aquachain.example.com
- **On-Call**: oncall@aquachain.example.com

---

## Appendix

### A. Environment Variables

**ML Monitoring**:
```bash
MODEL_VERSION=v1
DRIFT_THRESHOLD=0.15
METRICS_TABLE=ModelMetrics
RETRAINING_THRESHOLD=10
```

**OTA Updates**:
```bash
FIRMWARE_BUCKET=aquachain-firmware
CODE_SIGNING_PROFILE=aquachain-firmware
ROLLOUT_RATE=10
```

**Certificate Rotation**:
```bash
CERT_LIFECYCLE_TABLE=CertificateLifecycle
EXPIRATION_WARNING_DAYS=30
EXPIRATION_CRITICAL_DAYS=7
CONFIRMATION_TIMEOUT=300
```

**Dependency Scanner**:
```bash
REPORT_BUCKET=aquachain-vulnerability-reports
SCAN_SCHEDULE=weekly
ALERT_TOPIC=vulnerability-alerts
```

### B. IAM Policies

See `infrastructure/setup-iam-permissions.md` for detailed IAM policies.

### C. Cost Estimates

**Monthly Costs** (estimated for 100 devices):

- ML Monitoring: $50-100
- OTA Updates: $20-50
- Certificate Rotation: $10-20
- Dependency Scanner: $5-10
- SBOM Generation: $5-10
- Performance Dashboard: $10-20
- **Total**: $100-210/month

### D. Glossary

- **Drift**: Degradation in ML model performance over time
- **OTA**: Over-The-Air firmware updates
- **SBOM**: Software Bill of Materials
- **SPDX**: Software Package Data Exchange format
- **CVE**: Common Vulnerabilities and Exposures
- **TTL**: Time To Live (auto-expiration)
- **GSI**: Global Secondary Index (DynamoDB)

---

**Document Version**: 1.0  
**Last Updated**: October 25, 2025  
**Status**: Production Ready
