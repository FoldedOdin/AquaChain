# Phase 3 Staging Deployment Guide

## Overview

This document provides step-by-step instructions for deploying Phase 3 components to the staging environment, validating functionality, and obtaining stakeholder approval.

## Prerequisites

- [ ] All Phase 3 development complete
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Documentation complete
- [ ] AWS credentials configured for staging account
- [ ] Stakeholders notified of deployment window

## Deployment Checklist

### Pre-Deployment

- [ ] Review deployment plan with team
- [ ] Backup current staging environment
- [ ] Verify rollback procedures
- [ ] Schedule deployment window (low-traffic period)
- [ ] Notify stakeholders of deployment

### Deployment Steps

#### Step 1: Environment Preparation

```bash
# Set environment variables
export AWS_DEFAULT_REGION=us-east-1
export ENVIRONMENT=staging
export AWS_PROFILE=aquachain-staging

# Verify AWS credentials
aws sts get-caller-identity

# Expected output: Staging account ID
```

**Verification**: Confirm correct AWS account

#### Step 2: Deploy Infrastructure Foundation

```bash
cd infrastructure/cdk

# Deploy Phase 3 infrastructure stack
./phase-3-deploy.sh staging infrastructure

# Verify deployment
aws cloudformation describe-stacks \
  --stack-name AquaChain-Phase3-staging \
  --query 'Stacks[0].StackStatus'
```

**Expected Output**: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

**Verification Checklist**:
- [ ] ModelMetrics DynamoDB table created
- [ ] CertificateLifecycle DynamoDB table created
- [ ] EventBridge schedules configured
- [ ] SNS topics created
- [ ] IAM roles and policies created

#### Step 3: Deploy ML Monitoring System

```bash
# Deploy ML monitoring components
./phase-3-deploy.sh staging ml-monitoring

# Verify Lambda function
aws lambda get-function \
  --function-name aquachain-ml-inference-staging \
  --query 'Configuration.LastModified'
```

**Verification Checklist**:
- [ ] ML inference Lambda updated with monitoring code
- [ ] ModelPerformanceTracker integrated
- [ ] CloudWatch metrics publishing
- [ ] Drift detection alarms configured

#### Step 4: Deploy Training Data Validation

```bash
# Deploy data validation
./phase-3-deploy.sh staging data-validation

# Verify S3 trigger
aws lambda get-function-event-invoke-config \
  --function-name aquachain-data-validator-staging
```

**Verification Checklist**:
- [ ] Data validation Lambda deployed
- [ ] S3 event trigger configured
- [ ] SNS alert topic configured
- [ ] Validation rules active

#### Step 5: Deploy OTA Update System

```bash
# Deploy OTA components
./phase-3-deploy.sh staging ota-updates

# Verify code signing profile
aws signer get-signing-profile \
  --profile-name aquachain-firmware-staging
```

**Verification Checklist**:
- [ ] OTA manager Lambda deployed
- [ ] Code signing profile configured
- [ ] Firmware S3 bucket created
- [ ] IoT Jobs configured
- [ ] Rollback mechanism tested

#### Step 6: Deploy Certificate Rotation

```bash
# Deploy certificate rotation
./phase-3-deploy.sh staging certificate-rotation

# Verify EventBridge schedule
aws events describe-rule \
  --name aquachain-cert-rotation-daily-staging
```

**Verification Checklist**:
- [ ] Certificate rotation Lambda deployed
- [ ] Daily schedule configured
- [ ] MQTT provisioning tested
- [ ] Zero-downtime rotation verified

#### Step 7: Deploy Dependency Scanner

```bash
# Deploy dependency scanner
./phase-3-deploy.sh staging dependency-scanner

# Verify weekly schedule
aws events describe-rule \
  --name aquachain-dependency-scan-weekly-staging
```

**Verification Checklist**:
- [ ] Dependency scanner Lambda deployed
- [ ] Weekly schedule configured
- [ ] S3 reports bucket created
- [ ] SNS alerts configured

#### Step 8: Deploy SBOM Generator

```bash
# Deploy SBOM storage
./phase-3-deploy.sh staging sbom

# Generate initial SBOM
cd ../../scripts
python generate-sbom.py --all --environment staging
```

**Verification Checklist**:
- [ ] SBOM storage bucket created
- [ ] Syft and Grype configured
- [ ] GitHub Actions workflow updated
- [ ] Initial SBOM generated

#### Step 9: Deploy Performance Dashboard

```bash
# Deploy dashboard
cd ../infrastructure/cdk
./phase-3-deploy.sh staging dashboard

# Get dashboard URL
echo "Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Performance-staging"
```

**Verification Checklist**:
- [ ] CloudWatch dashboard created
- [ ] All metrics displaying
- [ ] Alarms configured
- [ ] Dashboard accessible

### Post-Deployment Validation

#### Smoke Tests

```bash
cd ../../tests

# Run Phase 3 smoke tests
python run_phase3_tests.py --smoke --environment staging

# Expected: All tests pass
```

**Test Coverage**:
- [ ] ML monitoring operational
- [ ] Data validation functional
- [ ] OTA updates configured
- [ ] Certificate rotation active
- [ ] Dependency scanner running
- [ ] SBOM generation working
- [ ] Performance dashboard accessible

#### Integration Tests

```bash
# Run full integration test suite
python run_phase3_tests.py --environment staging

# Expected: All tests pass (may take 15-30 minutes)
```

**Test Coverage**:
- [ ] End-to-end ML monitoring workflow
- [ ] OTA update with test devices
- [ ] Certificate rotation workflow
- [ ] Dependency scanning and reporting
- [ ] SBOM generation and vulnerability scanning

#### Performance Tests

```bash
# Run performance tests
python -m pytest tests/performance/test_phase3_performance.py --environment staging

# Expected: All performance metrics within acceptable range
```

**Performance Criteria**:
- [ ] ML monitoring latency < 50ms
- [ ] Prediction throughput > 1000/sec
- [ ] Certificate rotation < 5 minutes
- [ ] SBOM generation < 2 minutes
- [ ] Dashboard load time < 1 second

#### Security Tests

```bash
# Run security tests
python -m pytest tests/security/test_phase3_security.py --environment staging

# Expected: All security controls validated
```

**Security Criteria**:
- [ ] Firmware signature verification working
- [ ] Certificate validation functional
- [ ] IAM permissions least-privilege
- [ ] Data encryption at rest
- [ ] TLS encryption in transit

### Functional Validation

#### ML Monitoring Validation

```bash
# Trigger test predictions
aws lambda invoke \
  --function-name aquachain-ml-inference-staging \
  --payload '{"sensor_data":{"pH":7.2,"temperature":25.5,"turbidity":2.1}}' \
  response.json

# Check metrics logged
aws dynamodb query \
  --table-name aquachain-model-metrics-staging \
  --key-condition-expression "model_name = :mn" \
  --expression-attribute-values '{":mn":{"S":"water-quality-v1"}}' \
  --limit 10 \
  --scan-index-forward false

# Verify CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AquaChain \
  --metric-name PredictionLatency \
  --dimensions Name=Environment,Value=staging \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

**Validation Checklist**:
- [ ] Predictions logged to DynamoDB
- [ ] Drift score calculated
- [ ] CloudWatch metrics published
- [ ] Latency within acceptable range

#### OTA Update Validation

```bash
# Create test firmware update job
python3 << EOF
from lambda.iot_management.ota_update_manager import OTAManager

manager = OTAManager(environment='staging')
job_id = manager.create_firmware_job(
    firmware_version='v2.0.0-test',
    device_group='test-devices',
    rollout_config={'maximumPerMinute': 1}
)
print(f'Test Job ID: {job_id}')
EOF

# Monitor job progress
aws iot describe-job --job-id <job_id>

# Verify signature
aws signer describe-signing-job --job-id <signing_job_id>
```

**Validation Checklist**:
- [ ] Firmware signed successfully
- [ ] IoT Job created
- [ ] Test device received update
- [ ] Signature verified on device
- [ ] Update applied successfully

#### Certificate Rotation Validation

```bash
# Trigger test rotation
aws lambda invoke \
  --function-name aquachain-cert-rotation-staging \
  --payload '{"device_id":"test-device-001","force":true}' \
  response.json

# Monitor rotation
aws dynamodb get-item \
  --table-name aquachain-certificate-lifecycle-staging \
  --key '{"device_id":{"S":"test-device-001"},"certificate_id":{"S":"<new_cert_id>"}}'

# Verify device connectivity
aws iot-data get-thing-shadow --thing-name test-device-001
```

**Validation Checklist**:
- [ ] New certificate generated
- [ ] Certificate provisioned to device
- [ ] Device confirmed new certificate
- [ ] Old certificate deactivated
- [ ] Zero downtime maintained

#### Dependency Scanner Validation

```bash
# Trigger manual scan
aws lambda invoke \
  --function-name aquachain-dependency-scanner-staging \
  --payload '{"scan_type":"all"}' \
  response.json

# Check report generated
aws s3 ls s3://aquachain-vulnerability-reports-staging/

# Download and review report
aws s3 cp s3://aquachain-vulnerability-reports-staging/latest.json ./
cat latest.json | jq '.vulnerabilities | length'
```

**Validation Checklist**:
- [ ] npm audit completed
- [ ] pip-audit completed
- [ ] Report generated
- [ ] Vulnerabilities categorized
- [ ] Alerts sent for critical issues

#### SBOM Validation

```bash
# Verify SBOM generated
aws s3 ls s3://aquachain-sbom-storage-staging/

# Download and validate SBOM
aws s3 cp s3://aquachain-sbom-storage-staging/sbom-frontend-latest.json ./
cat sbom-frontend-latest.json | jq '.artifacts | length'

# Run Grype scan
grype sbom:sbom-frontend-latest.json -o json
```

**Validation Checklist**:
- [ ] SBOM generated for all components
- [ ] SPDX format validated
- [ ] All dependencies included
- [ ] Vulnerability scan completed
- [ ] Results stored in S3

#### Performance Dashboard Validation

```bash
# Access dashboard
echo "Dashboard URL: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Performance-staging"

# Verify metrics displaying
aws cloudwatch get-dashboard \
  --dashboard-name AquaChain-Performance-staging | jq '.DashboardBody' | jq -r '.'

# Test alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix aquachain-staging
```

**Validation Checklist**:
- [ ] Dashboard loads successfully
- [ ] All widgets displaying data
- [ ] Metrics updating in real-time
- [ ] Alarms configured correctly
- [ ] Alert notifications working

### Stakeholder Approval

#### Prepare Demonstration

1. **ML Monitoring Demo**:
   - Show real-time drift detection
   - Demonstrate automated retraining trigger
   - Review CloudWatch metrics

2. **OTA Update Demo**:
   - Show firmware signing process
   - Demonstrate gradual rollout
   - Show rollback capability

3. **Certificate Rotation Demo**:
   - Show zero-downtime rotation
   - Demonstrate expiration monitoring
   - Review rotation history

4. **Security Demo**:
   - Show dependency vulnerability scanning
   - Demonstrate SBOM generation
   - Review security alerts

5. **Performance Dashboard Demo**:
   - Walk through dashboard widgets
   - Show alarm configuration
   - Demonstrate metric queries

#### Approval Checklist

- [ ] All functional requirements met
- [ ] All non-functional requirements met
- [ ] Performance within acceptable range
- [ ] Security controls validated
- [ ] Documentation complete
- [ ] Training materials prepared
- [ ] Stakeholder sign-off obtained

#### Sign-off Form

```
Phase 3 Staging Deployment Approval

Environment: Staging
Deployment Date: October 25, 2025
Deployed By: [Name]

Components Deployed:
✓ ML Monitoring System
✓ Training Data Validation
✓ OTA Update System
✓ Certificate Rotation
✓ Dependency Scanner
✓ SBOM Generator
✓ Performance Dashboard

Test Results:
✓ Smoke Tests: PASSED
✓ Integration Tests: PASSED
✓ Performance Tests: PASSED
✓ Security Tests: PASSED

Stakeholder Approval:
[ ] Product Owner: _________________ Date: _______
[ ] Technical Lead: ________________ Date: _______
[ ] Security Lead: _________________ Date: _______
[ ] DevOps Lead: __________________ Date: _______

Approved for Production: [ ] YES  [ ] NO

Comments:
_________________________________________________
_________________________________________________
_________________________________________________
```

### Rollback Procedure

If issues are discovered during validation:

```bash
# Rollback infrastructure
cd infrastructure/cdk
cdk destroy AquaChain-Phase3-staging --force

# Restore previous Lambda versions
aws lambda update-function-code \
  --function-name aquachain-ml-inference-staging \
  --s3-bucket aquachain-lambda-artifacts \
  --s3-key ml-inference-previous.zip

# Notify stakeholders
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:deployment-alerts \
  --subject "Phase 3 Staging Rollback" \
  --message "Phase 3 deployment rolled back due to validation issues."
```

### Post-Approval Actions

- [ ] Document any issues encountered
- [ ] Update deployment procedures based on lessons learned
- [ ] Schedule production deployment
- [ ] Prepare production deployment plan
- [ ] Update monitoring and alerting
- [ ] Train operations team

## Deployment Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Pre-Deployment | 1 hour | Environment prep, backups |
| Infrastructure | 30 minutes | Deploy foundation stacks |
| Components | 2 hours | Deploy all Phase 3 components |
| Smoke Tests | 30 minutes | Quick validation |
| Integration Tests | 1 hour | Full test suite |
| Performance Tests | 30 minutes | Load and stress testing |
| Security Tests | 30 minutes | Security validation |
| Functional Validation | 2 hours | Manual testing |
| Stakeholder Demo | 1 hour | Demonstration and approval |
| **Total** | **8-9 hours** | Full deployment and validation |

## Success Criteria

Phase 3 staging deployment is successful when:

- [ ] All infrastructure deployed without errors
- [ ] All Lambda functions operational
- [ ] All smoke tests passing
- [ ] All integration tests passing
- [ ] All performance tests passing
- [ ] All security tests passing
- [ ] All functional validation complete
- [ ] Performance dashboard operational
- [ ] Stakeholder approval obtained
- [ ] Documentation complete
- [ ] No critical issues identified

## Known Issues and Workarounds

### Issue 1: EventBridge Schedule Delay
**Description**: EventBridge schedules may take up to 5 minutes to activate  
**Workaround**: Wait 5 minutes after deployment before testing scheduled functions  
**Status**: Expected behavior

### Issue 2: CloudWatch Metrics Delay
**Description**: Metrics may take 1-2 minutes to appear in dashboard  
**Workaround**: Refresh dashboard after 2 minutes  
**Status**: Expected behavior

### Issue 3: Certificate Rotation Timeout
**Description**: First rotation may timeout if device is offline  
**Workaround**: Ensure test devices are online before testing  
**Status**: Expected behavior

## Contact Information

**Deployment Lead**: devops@aquachain.example.com  
**Technical Support**: support@aquachain.example.com  
**On-Call**: oncall@aquachain.example.com  
**Emergency**: +1-555-0100

## References

- [Phase 3 Implementation Guide](PHASE_3_IMPLEMENTATION_GUIDE.md)
- [Phase 3 Operational Runbooks](PHASE_3_OPERATIONAL_RUNBOOKS.md)
- [Phase 3 Requirements](.kiro/specs/phase-3-high-priority/requirements.md)
- [Phase 3 Design](.kiro/specs/phase-3-high-priority/design.md)
- [Phase 3 Test Guide](tests/PHASE3_TEST_GUIDE.md)

---

**Document Version**: 1.0  
**Last Updated**: October 25, 2025  
**Next Review**: After production deployment
