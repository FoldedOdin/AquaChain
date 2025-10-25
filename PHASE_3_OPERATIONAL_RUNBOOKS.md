# Phase 3 Operational Runbooks

## Overview

This document provides step-by-step operational procedures for managing Phase 3 components of the AquaChain platform. These runbooks are designed for DevOps engineers, ML engineers, and security teams.

## Table of Contents

1. [ML Model Retraining Procedure](#ml-model-retraining-procedure)
2. [OTA Update Rollout Procedure](#ota-update-rollout-procedure)
3. [Certificate Rotation Troubleshooting](#certificate-rotation-troubleshooting)
4. [Dependency Update Procedure](#dependency-update-procedure)
5. [Emergency Response Procedures](#emergency-response-procedures)
6. [Monitoring and Alerting](#monitoring-and-alerting)

---

## ML Model Retraining Procedure

### Purpose
Retrain ML models when drift is detected or new training data is available.

### Prerequisites
- Training data validated and available in S3
- SageMaker training job configured
- Model registry accessible
- Appropriate IAM permissions

### When to Use
- Drift score exceeds 0.15 for 10 consecutive predictions
- Model performance degrades below acceptable threshold
- New training data available (monthly or quarterly)
- Seasonal adjustments needed

### Procedure

#### Step 1: Validate Training Data

```bash
# Check if training data exists
aws s3 ls s3://aquachain-training-data/$(date +%Y-%m-%d)/

# Verify data quality report
aws s3 cp s3://aquachain-training-data/$(date +%Y-%m-%d)/quality-report.json ./
cat quality-report.json | jq '.validation_status'
```

**Expected Output**: `"PASSED"`

**If Failed**: Review quality report and fix data issues before proceeding.


#### Step 2: Trigger Retraining

```bash
# Trigger retraining via Lambda
aws lambda invoke \
  --function-name aquachain-ml-training-trigger-dev \
  --payload '{
    "model_name": "water-quality-v1",
    "training_data_path": "s3://aquachain-training-data/2025-10-25/",
    "reason": "drift_detected",
    "hyperparameters": {
      "learning_rate": 0.001,
      "epochs": 100,
      "batch_size": 32
    }
  }' \
  response.json

# Get training job name
TRAINING_JOB=$(cat response.json | jq -r '.training_job_name')
echo "Training Job: $TRAINING_JOB"
```

**Expected Output**: Training job name (e.g., `water-quality-v1-2025-10-25-123456`)

#### Step 3: Monitor Training Progress

```bash
# Check training status
aws sagemaker describe-training-job --training-job-name $TRAINING_JOB

# Watch training metrics
watch -n 60 'aws sagemaker describe-training-job --training-job-name '$TRAINING_JOB' | jq ".TrainingJobStatus"'

# View training logs
aws logs tail /aws/sagemaker/TrainingJobs --follow --filter-pattern $TRAINING_JOB
```

**Expected Duration**: 30-60 minutes depending on data size

**Status Progression**: `InProgress` → `Completed`

#### Step 4: Validate New Model

```bash
# Run validation tests
cd tests/integration
python test_ml_model_validation.py --model-version v2 --training-job $TRAINING_JOB

# Check validation metrics
aws s3 cp s3://aquachain-model-artifacts/${TRAINING_JOB}/validation-metrics.json ./
cat validation-metrics.json | jq '.accuracy, .precision, .recall'
```

**Acceptance Criteria**:
- Accuracy > 0.85
- Precision > 0.80
- Recall > 0.80
- No significant performance degradation

#### Step 5: Deploy New Model

```bash
# Update model version in inference Lambda
aws lambda update-function-configuration \
  --function-name aquachain-ml-inference-dev \
  --environment Variables="{
    MODEL_VERSION=v2,
    MODEL_PATH=s3://aquachain-model-artifacts/${TRAINING_JOB}/model.tar.gz,
    DRIFT_THRESHOLD=0.15
  }"

# Wait for update to complete
aws lambda wait function-updated \
  --function-name aquachain-ml-inference-dev

# Verify deployment
aws lambda get-function-configuration \
  --function-name aquachain-ml-inference-dev | jq '.Environment.Variables.MODEL_VERSION'
```

**Expected Output**: `"v2"`

#### Step 6: Monitor Post-Deployment

```bash
# Monitor drift scores for 24 hours
aws cloudwatch get-metric-statistics \
  --namespace AquaChain \
  --metric-name DriftScore \
  --dimensions Name=ModelVersion,Value=v2 \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum

# Monitor prediction latency
aws cloudwatch get-metric-statistics \
  --namespace AquaChain \
  --metric-name PredictionLatency \
  --dimensions Name=ModelVersion,Value=v2 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,p95
```

**Success Criteria**:
- Drift score < 0.10 for 24 hours
- Prediction latency < 200ms (p95)
- Error rate < 0.5%

#### Step 7: Rollback if Needed

```bash
# If new model performs poorly, rollback to previous version
aws lambda update-function-configuration \
  --function-name aquachain-ml-inference-dev \
  --environment Variables="{
    MODEL_VERSION=v1,
    MODEL_PATH=s3://aquachain-model-artifacts/previous/model.tar.gz,
    DRIFT_THRESHOLD=0.15
  }"

# Verify rollback
aws lambda get-function-configuration \
  --function-name aquachain-ml-inference-dev | jq '.Environment.Variables.MODEL_VERSION'

# Send notification
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:ml-alerts \
  --subject "Model Rollback Performed" \
  --message "Model v2 rolled back to v1 due to performance issues"
```

### Troubleshooting

**Issue**: Training job fails with "InsufficientCapacity"
- **Solution**: Retry with smaller instance type or different availability zone

**Issue**: Validation metrics below threshold
- **Solution**: Review training data quality, adjust hyperparameters, collect more data

**Issue**: High latency after deployment
- **Solution**: Increase Lambda memory, enable provisioned concurrency, optimize model size

---

## OTA Update Rollout Procedure

### Purpose
Deploy firmware updates to IoT devices securely and reliably.

### Prerequisites
- Firmware tested in development environment
- Code signing profile configured
- Test devices available for pilot rollout
- Rollback plan prepared

### When to Use
- Security patches available
- New features ready for deployment
- Bug fixes needed
- Performance improvements

### Procedure

#### Step 1: Prepare Firmware

```bash
# Upload firmware to S3
aws s3 cp firmware-v2.0.0.bin s3://aquachain-firmware/v2.0.0/firmware.bin

# Sign firmware
cd infrastructure/iot
python setup-code-signing.py --sign v2.0.0

# Verify signature
aws signer describe-signing-job --job-id $(cat signing-job-id.txt)
```

**Expected Output**: `status: "Succeeded"`

#### Step 2: Create Pilot Rollout (10% of devices)

```python
# Create pilot job
python3 << EOF
from lambda.iot_management.ota_update_manager import OTAManager

manager = OTAManager()
job_id = manager.create_firmware_job(
    firmware_version='v2.0.0',
    device_group='pilot-devices',  # 10% of fleet
    rollout_config={
        'maximumPerMinute': 2,
        'exponentialRate': {
            'baseRatePerMinute': 5,
            'incrementFactor': 1.5,
            'rateIncreaseCriteria': {
                'numberOfSucceededThings': 5
            }
        }
    }
)
print(f'Pilot Job ID: {job_id}')
EOF
```

**Expected Output**: Job ID (e.g., `firmware-update-v2.0.0-pilot`)

#### Step 3: Monitor Pilot Rollout

```bash
# Check job status every 5 minutes
JOB_ID="firmware-update-v2.0.0-pilot"

watch -n 300 'aws iot describe-job --job-id '$JOB_ID' | jq ".job.jobProcessDetails"'

# Check for failures
aws iot list-job-executions \
  --job-id $JOB_ID \
  --status FAILED | jq '.jobExecutions'

# Get success rate
SUCCESS=$(aws iot list-job-executions --job-id $JOB_ID --status SUCCEEDED | jq '.jobExecutions | length')
TOTAL=$(aws iot list-job-executions --job-id $JOB_ID | jq '.jobExecutions | length')
echo "Success Rate: $(($SUCCESS * 100 / $TOTAL))%"
```

**Success Criteria**:
- Success rate > 95%
- No critical errors reported
- Device connectivity maintained
- Average update time < 5 minutes

#### Step 4: Expand to 50% of Devices

```bash
# If pilot successful, expand rollout
aws iot update-job \
  --job-id firmware-update-v2.0.0 \
  --job-executions-rollout-config '{
    "maximumPerMinute": 10,
    "exponentialRate": {
      "baseRatePerMinute": 20,
      "incrementFactor": 2,
      "rateIncreaseCriteria": {
        "numberOfSucceededThings": 50
      }
    }
  }'

# Monitor expanded rollout
watch -n 300 'aws iot describe-job --job-id firmware-update-v2.0.0 | jq ".job.jobProcessDetails"'
```

**Monitor for**: 2-4 hours depending on fleet size

#### Step 5: Complete Full Rollout (100%)

```bash
# After 50% success, complete rollout
aws iot update-job \
  --job-id firmware-update-v2.0.0 \
  --job-executions-rollout-config '{
    "maximumPerMinute": 50
  }'

# Monitor completion
watch -n 600 'aws iot describe-job --job-id firmware-update-v2.0.0 | jq ".job.jobProcessDetails"'
```

#### Step 6: Handle Failures

```bash
# If failure rate > 5%, pause and investigate
aws iot update-job \
  --job-id firmware-update-v2.0.0 \
  --abort-config '{
    "criteriaList": [{
      "failureType": "FAILED",
      "action": "CANCEL",
      "thresholdPercentage": 5,
      "minNumberOfExecutedThings": 10
    }]
  }'

# Get failed devices
aws iot list-job-executions \
  --job-id firmware-update-v2.0.0 \
  --status FAILED \
  --query 'jobExecutions[*].thingArn' \
  --output text > failed-devices.txt

# Rollback failed devices
while read device_arn; do
  DEVICE_ID=$(echo $device_arn | cut -d'/' -f2)
  python3 -c "
from lambda.iot_management.ota_update_manager import OTAManager
manager = OTAManager()
manager.rollback_firmware('$DEVICE_ID', 'v1.9.0')
"
done < failed-devices.txt
```

#### Step 7: Verify Deployment

```bash
# Check firmware versions across fleet
aws iot search-index \
  --query-string "shadow.reported.firmware_version:v2.0.0" \
  --max-results 1000 | jq '.things | length'

# Verify device health
aws cloudwatch get-metric-statistics \
  --namespace AquaChain/IoT \
  --metric-name DeviceHealth \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Troubleshooting

**Issue**: Signature verification fails on device
- **Solution**: Check device time synchronization (NTP), verify code signing profile, re-sign firmware

**Issue**: Device becomes unresponsive after update
- **Solution**: Trigger automatic rollback, investigate device logs, check power supply

**Issue**: Update download fails
- **Solution**: Check S3 bucket permissions, verify device internet connectivity, retry with smaller chunks

---

## Certificate Rotation Troubleshooting

### Purpose
Diagnose and resolve certificate rotation issues to maintain device connectivity.

### Prerequisites
- Device online and connected
- Certificate lifecycle table accessible
- MQTT broker operational
- Appropriate IAM permissions

### When to Use
- Certificate expiring within 30 days
- Rotation failures detected
- Device connectivity issues
- Manual rotation required

### Procedure

#### Step 1: Check Certificate Status

```bash
# List expiring certificates
aws dynamodb query \
  --table-name aquachain-certificate-lifecycle-dev \
  --index-name expiration_date-index \
  --key-condition-expression "expiration_date < :date" \
  --expression-attribute-values '{":date":{"S":"2025-11-25"}}' \
  --projection-expression "device_id, certificate_id, expiration_date, #status" \
  --expression-attribute-names '{"#status":"status"}' | jq '.Items'

# Check specific device certificate
DEVICE_ID="device-001"
aws dynamodb query \
  --table-name aquachain-certificate-lifecycle-dev \
  --key-condition-expression "device_id = :did" \
  --expression-attribute-values '{":did":{"S":"'$DEVICE_ID'"}}' | jq '.Items'
```

#### Step 2: Verify Device Connectivity

```bash
# Check device shadow
aws iot-data get-thing-shadow \
  --thing-name $DEVICE_ID \
  --output text | jq '.state.reported'

# Check last connection time
aws iot describe-thing \
  --thing-name $DEVICE_ID | jq '.attributes.lastConnected'

# Check device connectivity status
aws iot search-index \
  --query-string "thingName:$DEVICE_ID AND connectivity.connected:true"
```

**Expected**: Device should be online and connected

#### Step 3: Manual Certificate Rotation

```bash
# Trigger rotation for specific device
cd iot-simulator
python provision-device.py --device-id $DEVICE_ID --rotate

# Or use Lambda directly
aws lambda invoke \
  --function-name aquachain-cert-rotation-dev \
  --payload '{"device_id":"'$DEVICE_ID'","force":true}' \
  response.json

# Check response
cat response.json | jq '.'
```

#### Step 4: Monitor Rotation Progress

```bash
# Check rotation status
aws dynamodb get-item \
  --table-name aquachain-certificate-lifecycle-dev \
  --key '{"device_id":{"S":"'$DEVICE_ID'"},"certificate_id":{"S":"new-cert-id"}}' | \
  jq '.Item.status.S'

# Watch for confirmation
watch -n 30 'aws dynamodb get-item --table-name aquachain-certificate-lifecycle-dev --key '"'"'{"device_id":{"S":"'$DEVICE_ID'"},"certificate_id":{"S":"new-cert-id"}}'"'"' | jq ".Item.status.S"'
```

**Expected Status Progression**: `rotating` → `active`

#### Step 5: Handle Rotation Failure

```bash
# If device doesn't confirm new cert, extend old cert
OLD_CERT_ID=$(aws iot list-thing-principals --thing-name $DEVICE_ID | jq -r '.principals[0]' | cut -d'/' -f2)

aws iot update-certificate \
  --certificate-id $OLD_CERT_ID \
  --new-status ACTIVE

# Retry rotation with longer timeout
aws lambda update-function-configuration \
  --function-name aquachain-cert-rotation-dev \
  --environment Variables="{CONFIRMATION_TIMEOUT=600}"

# Retry
aws lambda invoke \
  --function-name aquachain-cert-rotation-dev \
  --payload '{"device_id":"'$DEVICE_ID'","retry":true}' \
  response.json
```

#### Step 6: Verify Successful Rotation

```bash
# Check device is using new certificate
aws iot list-thing-principals --thing-name $DEVICE_ID

# Verify old certificate deactivated
aws iot describe-certificate --certificate-id $OLD_CERT_ID | jq '.certificateDescription.status'

# Test device connectivity
aws iot-data publish \
  --topic "test/$DEVICE_ID" \
  --payload '{"test":"connectivity"}' \
  --qos 1
```

**Expected**: Device responds to test message

### Troubleshooting

**Issue**: Device unreachable during rotation
- **Solution**: Queue rotation for next connection, extend old certificate validity, check device power

**Issue**: Confirmation timeout
- **Solution**: Increase timeout, check MQTT connectivity, verify device firmware supports rotation

**Issue**: Both certificates active
- **Solution**: Manually deactivate old certificate after verifying new one works

---

## Dependency Update Procedure

### Purpose
Update dependencies to address vulnerabilities and maintain security.

### Prerequisites
- Vulnerability report reviewed
- Test environment available
- Backup of current dependencies
- Rollback plan prepared

### When to Use
- Critical vulnerabilities detected
- Weekly maintenance window
- Major version updates available
- Security patches released

### Procedure

#### Step 1: Review Vulnerability Report

```bash
# Get latest report
aws s3 cp s3://aquachain-vulnerability-reports/latest.json ./

# Review critical vulnerabilities
cat latest.json | jq '.vulnerabilities[] | select(.severity=="critical")'

# Count vulnerabilities by severity
cat latest.json | jq '.vulnerabilities | group_by(.severity) | map({severity: .[0].severity, count: length})'
```

#### Step 2: Update Frontend Dependencies

```bash
cd frontend

# Backup current package-lock.json
cp package-lock.json package-lock.json.backup.$(date +%Y%m%d)

# Update specific package
npm update axios

# Or update all packages
npm update

# Check for breaking changes
npm outdated

# Run tests
npm test -- --watchAll=false

# Build and verify
npm run build
```

**Acceptance Criteria**:
- All tests pass
- Build succeeds
- No console errors
- Application functions correctly

#### Step 3: Update Backend Dependencies

```bash
cd lambda

# For each Lambda function
for dir in */; do
  if [ -f "$dir/requirements.txt" ]; then
    cd "$dir"
    
    # Backup
    cp requirements.txt requirements.txt.backup.$(date +%Y%m%d)
    
    # Update specific package
    pip install --upgrade boto3
    pip freeze > requirements.txt
    
    # Run tests
    python -m pytest
    
    cd ..
  fi
done
```

#### Step 4: Test in Development

```bash
# Deploy to dev environment
cd infrastructure/cdk
cdk deploy --all --context environment=dev

# Run integration tests
cd ../../tests
python run_phase3_tests.py --environment dev

# Monitor for errors
aws logs tail /aws/lambda/aquachain-ml-inference-dev --follow --since 5m
```

**Monitor for**: 1-2 hours

#### Step 5: Deploy to Staging

```bash
# Deploy to staging
cd infrastructure/cdk
cdk deploy --all --context environment=staging

# Run smoke tests
cd ../../tests
python run_phase3_tests.py --smoke --environment staging

# Performance testing
python -m pytest tests/performance/ --environment staging
```

**Acceptance Criteria**:
- All smoke tests pass
- Performance within acceptable range
- No critical errors in logs

#### Step 6: Deploy to Production

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

# Monitor API Gateway
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Monitor for**: 24 hours

#### Step 7: Rollback if Needed

```bash
# Restore previous dependencies
cd frontend
cp package-lock.json.backup.YYYYMMDD package-lock.json
npm install

cd ../lambda
for dir in */; do
  if [ -f "$dir/requirements.txt.backup.YYYYMMDD" ]; then
    cp "$dir/requirements.txt.backup.YYYYMMDD" "$dir/requirements.txt"
    pip install -r "$dir/requirements.txt" -t "$dir/" --upgrade
  fi
done

# Redeploy previous version
cd infrastructure/cdk
cdk deploy --all --context version=previous

# Verify rollback
aws lambda get-function-configuration \
  --function-name aquachain-ml-inference-production | jq '.LastModified'
```

### Troubleshooting

**Issue**: Tests fail after update
- **Solution**: Review breaking changes, update test code, check compatibility matrix

**Issue**: Performance degradation
- **Solution**: Profile application, check for memory leaks, optimize hot paths

**Issue**: Dependency conflicts
- **Solution**: Use dependency resolution tools, update conflicting packages together, consider alternatives

---

## Emergency Response Procedures

### Critical Alert: ML Drift Score > 0.20

**Severity**: HIGH  
**Response Time**: 15 minutes

```bash
# 1. Check current drift score
aws cloudwatch get-metric-statistics \
  --namespace AquaChain \
  --metric-name DriftScore \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum

# 2. Review recent predictions
aws dynamodb query \
  --table-name aquachain-model-metrics-dev \
  --key-condition-expression "model_name = :mn" \
  --expression-attribute-values '{":mn":{"S":"water-quality-v1"}}' \
  --limit 100 \
  --scan-index-forward false

# 3. Check data quality
aws s3 cp s3://aquachain-training-data/latest/quality-report.json ./
cat quality-report.json | jq '.validation_status'

# 4. Trigger immediate retraining
aws lambda invoke \
  --function-name aquachain-ml-training-trigger-dev \
  --payload '{"model_name":"water-quality-v1","reason":"critical_drift","priority":"high"}' \
  response.json

# 5. Notify team
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:critical-alerts \
  --subject "CRITICAL: ML Drift Detected" \
  --message "Drift score exceeded 0.20. Retraining initiated."
```

### Critical Alert: OTA Update Failure Rate > 10%

**Severity**: HIGH  
**Response Time**: 30 minutes

```bash
# 1. Pause rollout immediately
JOB_ID="firmware-update-v2.0.0"
aws iot cancel-job --job-id $JOB_ID --force

# 2. Get failed devices
aws iot list-job-executions \
  --job-id $JOB_ID \
  --status FAILED \
  --query 'jobExecutions[*].[thingArn,statusDetails]' \
  --output table

# 3. Rollback all devices
python3 << EOF
from lambda.iot_management.ota_update_manager import OTAManager
manager = OTAManager()
manager.rollback_all_devices('$JOB_ID', 'v1.9.0')
EOF

# 4. Investigate root cause
aws logs filter-log-events \
  --log-group-name /aws/iot/jobs \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '2 hours ago' +%s)000

# 5. Notify team
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:critical-alerts \
  --subject "CRITICAL: OTA Update Failure" \
  --message "OTA update paused due to high failure rate. Rollback initiated."
```

### Critical Alert: Certificate Expiring in 24 Hours

**Severity**: CRITICAL  
**Response Time**: Immediate

```bash
# 1. Identify expiring certificates
aws dynamodb query \
  --table-name aquachain-certificate-lifecycle-dev \
  --index-name expiration_date-index \
  --key-condition-expression "expiration_date < :date" \
  --expression-attribute-values '{":date":{"S":"'$(date -u -d '24 hours' +%Y-%m-%d)'"}}' \
  --projection-expression "device_id, certificate_id"

# 2. Trigger immediate rotation for all
while read device_id; do
  aws lambda invoke \
    --function-name aquachain-cert-rotation-dev \
    --payload '{"device_id":"'$device_id'","force":true,"priority":"critical"}' \
    response-$device_id.json &
done < expiring-devices.txt

wait

# 3. Monitor rotation progress
watch -n 30 'aws dynamodb query --table-name aquachain-certificate-lifecycle-dev --index-name status-index --key-condition-expression "#status = :s" --expression-attribute-names '"'"'{"#status":"status"}'"'"' --expression-attribute-values '"'"'{":s":{"S":"rotating"}}'"'"' | jq ".Items | length"'

# 4. Escalate if needed
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:critical-alerts \
  --subject "CRITICAL: Certificate Expiration Imminent" \
  --message "Emergency certificate rotation in progress for $(wc -l < expiring-devices.txt) devices."
```

---

## Monitoring and Alerting

### Daily Checks

```bash
# Check system health
aws cloudwatch get-dashboard \
  --dashboard-name AquaChain-Performance-dev | jq '.DashboardBody' | jq -r '.' | jq '.widgets[].properties.metrics'

# Review error logs
aws logs tail /aws/lambda/aquachain-ml-inference-dev --since 24h --filter-pattern "ERROR"

# Check certificate expiration
aws dynamodb query \
  --table-name aquachain-certificate-lifecycle-dev \
  --index-name expiration_date-index \
  --key-condition-expression "expiration_date < :date" \
  --expression-attribute-values '{":date":{"S":"'$(date -u -d '30 days' +%Y-%m-%d)'"}}' | jq '.Items | length'
```

### Weekly Checks

```bash
# Run dependency scan
aws lambda invoke \
  --function-name aquachain-dependency-scanner-dev \
  --payload '{"scan_type":"all"}' \
  response.json

# Generate SBOM
cd scripts
python generate-sbom.py --all

# Review performance trends
aws cloudwatch get-metric-statistics \
  --namespace AquaChain \
  --metric-name PredictionLatency \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum
```

### Monthly Checks

```bash
# Review ML model performance
aws dynamodb query \
  --table-name aquachain-model-metrics-dev \
  --key-condition-expression "model_name = :mn AND #ts BETWEEN :start AND :end" \
  --expression-attribute-names '{"#ts":"timestamp"}' \
  --expression-attribute-values '{
    ":mn":{"S":"water-quality-v1"},
    ":start":{"S":"'$(date -u -d '30 days ago' +%Y-%m-%d)'"},
    ":end":{"S":"'$(date -u +%Y-%m-%d)'"}
  }' | jq '.Items | map(.drift_score.N | tonumber) | add/length'

# Review OTA update history
aws iot list-jobs --max-results 100 | jq '.jobs[] | select(.status=="COMPLETED")'

# Certificate rotation audit
aws dynamodb scan \
  --table-name aquachain-certificate-lifecycle-dev \
  --filter-expression "attribute_exists(rotation_history)" | jq '.Items | length'
```

---

## Appendix

### Contact Information

- **DevOps Team**: devops@aquachain.example.com
- **Security Team**: security@aquachain.example.com
- **ML Team**: ml-team@aquachain.example.com
- **On-Call**: oncall@aquachain.example.com

### Useful Links

- CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=AquaChain-Performance
- IoT Core Console: https://console.aws.amazon.com/iot/home
- SageMaker Console: https://console.aws.amazon.com/sagemaker/home
- Lambda Console: https://console.aws.amazon.com/lambda/home

### Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| Critical | Immediate | On-Call → Team Lead → Director |
| High | 15 minutes | On-Call → Team Lead |
| Medium | 1 hour | On-Call |
| Low | 4 hours | Team Member |

---

**Document Version**: 1.0  
**Last Updated**: October 25, 2025  
**Next Review**: November 25, 2025
