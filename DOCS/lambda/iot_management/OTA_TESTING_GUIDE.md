# OTA Firmware Update Testing Guide

## Overview

This guide covers testing the complete OTA (Over-The-Air) firmware update system for AquaChain IoT devices.

## Test Environment Setup

### Prerequisites

1. AWS Account with IoT Core enabled
2. Test ESP32 device(s)
3. Python 3.9+ for running tests
4. AWS CLI configured

### Install Test Dependencies

```bash
cd lambda/iot_management
pip install -r requirements-test.txt
```

## Unit Tests

### Running Unit Tests

```bash
# Run all tests
pytest test_ota_integration.py -v

# Run with coverage
pytest test_ota_integration.py --cov=ota_update_manager --cov-report=html

# Run specific test
pytest test_ota_integration.py::test_firmware_signing -v
```

### Test Coverage

The unit tests cover:
- ✅ Firmware signing workflow
- ✅ IoT Job creation
- ✅ Update progress tracking
- ✅ Device status handling
- ✅ Firmware rollback
- ✅ Automatic rollback on failure
- ✅ Job document templates

## Integration Tests

### Test 1: Successful Firmware Update

**Objective:** Verify complete firmware update workflow

**Steps:**

1. **Prepare Firmware**
   ```bash
   # Create test firmware
   echo "TEST_FIRMWARE_v2.0.0" > test-firmware-v2.0.0.bin
   
   # Upload to S3
   aws s3 cp test-firmware-v2.0.0.bin s3://aquachain-firmware-{account-id}/unsigned/
   ```

2. **Sign Firmware**
   ```bash
   # Invoke Lambda to sign firmware
   aws lambda invoke \
     --function-name aquachain-ota-manager \
     --payload '{"action":"sign_firmware","firmware_key":"unsigned/test-firmware-v2.0.0.bin","version":"2.0.0"}' \
     response.json
   
   cat response.json
   ```

3. **Create Update Job**
   ```bash
   # Create firmware update job
   aws lambda invoke \
     --function-name aquachain-ota-manager \
     --payload '{"action":"create_firmware_job","firmware_version":"2.0.0","signed_firmware_key":"signed/2.0.0/test-firmware-v2.0.0.bin","target_devices":["test-device-001"]}' \
     response.json
   
   # Note the job_id from response
   JOB_ID=$(cat response.json | jq -r '.body' | jq -r '.job_id')
   echo "Job ID: $JOB_ID"
   ```

4. **Monitor Progress**
   ```bash
   # Track update progress
   aws lambda invoke \
     --function-name aquachain-ota-manager \
     --payload "{\"action\":\"track_progress\",\"job_id\":\"$JOB_ID\"}" \
     response.json
   
   cat response.json
   ```

5. **Verify Device Update**
   ```bash
   # Check device firmware version
   aws dynamodb get-item \
     --table-name aquachain-devices \
     --key '{"device_id":{"S":"test-device-001"}}'
   ```

**Expected Results:**
- Firmware signed successfully
- Job created with status IN_PROGRESS
- Device downloads and installs firmware
- Device reports success status
- Device firmware_version updated to 2.0.0
- Previous version stored in previous_firmware_version

---

### Test 2: Firmware Update with Rollback

**Objective:** Test rollback mechanism when update fails

**Steps:**

1. **Create Invalid Firmware**
   ```bash
   # Create firmware with wrong checksum
   echo "INVALID_FIRMWARE" > invalid-firmware.bin
   aws s3 cp invalid-firmware.bin s3://aquachain-firmware-{account-id}/signed/3.0.0/
   ```

2. **Trigger Update**
   ```bash
   # Create job with invalid firmware
   aws lambda invoke \
     --function-name aquachain-ota-manager \
     --payload '{"action":"create_firmware_job","firmware_version":"3.0.0","signed_firmware_key":"signed/3.0.0/invalid-firmware.bin","target_devices":["test-device-001"]}' \
     response.json
   ```

3. **Simulate Failure**
   ```bash
   # Device will report failure due to checksum mismatch
   # Automatic rollback should be triggered
   ```

4. **Verify Rollback**
   ```bash
   # Check device firmware version (should be previous version)
   aws dynamodb get-item \
     --table-name aquachain-devices \
     --key '{"device_id":{"S":"test-device-001"}}'
   ```

**Expected Results:**
- Update fails on device
- Automatic rollback triggered
- Device reverts to previous firmware version
- Alert sent via SNS

---

### Test 3: Gradual Rollout

**Objective:** Test gradual rollout to multiple devices

**Steps:**

1. **Create Multiple Test Devices**
   ```bash
   # Register 10 test devices
   for i in {1..10}; do
     aws iot create-thing --thing-name "test-device-$(printf "%03d" $i)"
   done
   ```

2. **Create Update Job for All Devices**
   ```bash
   DEVICES='["test-device-001","test-device-002","test-device-003","test-device-004","test-device-005","test-device-006","test-device-007","test-device-008","test-device-009","test-device-010"]'
   
   aws lambda invoke \
     --function-name aquachain-ota-manager \
     --payload "{\"action\":\"create_firmware_job\",\"firmware_version\":\"2.0.0\",\"signed_firmware_key\":\"signed/2.0.0/firmware.bin\",\"target_devices\":$DEVICES}" \
     response.json
   ```

3. **Monitor Rollout Progress**
   ```bash
   # Check progress every minute
   JOB_ID=$(cat response.json | jq -r '.body' | jq -r '.job_id')
   
   while true; do
     aws lambda invoke \
       --function-name aquachain-ota-manager \
       --payload "{\"action\":\"track_progress\",\"job_id\":\"$JOB_ID\"}" \
       response.json
     
     cat response.json | jq '.body | fromjson'
     sleep 60
   done
   ```

**Expected Results:**
- Job starts with initial rollout (10% = 1 device)
- After success, increases to 50% (5 devices)
- Finally updates remaining devices (100%)
- If failures exceed threshold, job is cancelled

---

### Test 4: Manual Rollback

**Objective:** Test manual rollback to specific version

**Steps:**

1. **Trigger Manual Rollback**
   ```bash
   aws lambda invoke \
     --function-name aquachain-ota-manager \
     --payload '{"action":"rollback","device_id":"test-device-001","target_version":"1.0.0"}' \
     response.json
   
   cat response.json
   ```

2. **Verify Rollback Job Created**
   ```bash
   # Check IoT Jobs
   aws iot list-jobs --status IN_PROGRESS
   ```

3. **Monitor Device**
   ```bash
   # Device should download and install previous version
   # Check device logs via serial monitor
   ```

**Expected Results:**
- Rollback job created
- Device downloads previous firmware
- Device installs and reboots
- Device reports rollback success
- Alert sent via SNS

---

## Device-Side Testing

### ESP32 Firmware Testing

1. **Flash Test Firmware**
   ```bash
   cd iot-simulator/esp32-firmware/aquachain-device
   
   # Update config.h with test device credentials
   # Build and flash
   pio run --target upload
   
   # Monitor serial output
   pio device monitor
   ```

2. **Test OTA Update Reception**
   - Device should subscribe to job topics
   - Receive job notifications
   - Download firmware from presigned URL
   - Verify checksum
   - Install firmware
   - Report status

3. **Test Signature Verification**
   - Device verifies firmware signature
   - Rejects unsigned firmware
   - Rejects firmware with invalid signature

4. **Test Dual Partition Rollback**
   - Device boots from partition A
   - Updates to partition B
   - If update fails, boots back to partition A
   - Previous firmware still functional

---

## Performance Testing

### Load Test: Multiple Devices

**Objective:** Test system with 100+ devices

```bash
# Create 100 test devices
for i in {1..100}; do
  aws iot create-thing --thing-name "load-test-device-$(printf "%03d" $i)"
done

# Create update job for all devices
# Monitor system performance
# Check CloudWatch metrics
```

**Metrics to Monitor:**
- Lambda execution time
- DynamoDB read/write capacity
- S3 download bandwidth
- IoT Core message rate
- Job completion time

---

## Security Testing

### Test 1: Unsigned Firmware Rejection

**Objective:** Verify devices reject unsigned firmware

**Steps:**
1. Upload unsigned firmware
2. Create job without signing
3. Device should reject firmware

**Expected:** Device reports signature verification failure

### Test 2: Checksum Verification

**Objective:** Verify checksum validation

**Steps:**
1. Modify firmware after signing
2. Device downloads firmware
3. Checksum verification fails

**Expected:** Device rejects firmware, triggers rollback

### Test 3: Certificate Validation

**Objective:** Verify device certificate validation

**Steps:**
1. Attempt update with expired certificate
2. Attempt update with revoked certificate

**Expected:** Update rejected, alert sent

---

## Troubleshooting

### Common Issues

1. **Job Not Starting**
   - Check device is online
   - Verify device subscribed to job topics
   - Check IAM permissions

2. **Download Fails**
   - Verify presigned URL not expired
   - Check S3 bucket permissions
   - Verify network connectivity

3. **Checksum Mismatch**
   - Verify firmware not corrupted
   - Check signing process
   - Verify hash algorithm matches

4. **Rollback Fails**
   - Check previous partition exists
   - Verify previous firmware valid
   - Check device storage

### Debug Commands

```bash
# Check job status
aws iot describe-job --job-id <job-id>

# List job executions
aws iot list-job-executions-for-job --job-id <job-id>

# Get device shadow
aws iot-data get-thing-shadow --thing-name <device-id> shadow.json

# Check CloudWatch logs
aws logs tail /aws/lambda/aquachain-ota-manager --follow
```

---

## Test Checklist

- [ ] Unit tests pass
- [ ] Firmware signing works
- [ ] Job creation successful
- [ ] Device receives job notification
- [ ] Firmware download completes
- [ ] Checksum verification passes
- [ ] Firmware installation succeeds
- [ ] Device reboots successfully
- [ ] Status reported correctly
- [ ] Gradual rollout works
- [ ] Automatic rollback on failure
- [ ] Manual rollback works
- [ ] Signature verification works
- [ ] Certificate validation works
- [ ] Performance acceptable (100+ devices)
- [ ] Alerts sent correctly
- [ ] CloudWatch metrics accurate

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: OTA Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd lambda/iot_management
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          cd lambda/iot_management
          pytest test_ota_integration.py -v --cov
```

---

## Success Criteria

OTA system is production-ready when:

1. ✅ All unit tests pass
2. ✅ All integration tests pass
3. ✅ 99% success rate with test devices
4. ✅ Rollback works 100% of time
5. ✅ No security vulnerabilities
6. ✅ Performance meets requirements (<5 min for 100 devices)
7. ✅ Monitoring and alerts functional
8. ✅ Documentation complete

---

**Last Updated:** October 25, 2025
