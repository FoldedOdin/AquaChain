# Phase 3 Integration and Testing Guide

## Overview

This document provides comprehensive guidance for executing Phase 3 integration, performance, security, and monitoring tests.

## Test Structure

```
tests/
├── integration/
│   └── test_phase3_e2e.py          # End-to-end integration tests
├── performance/
│   └── test_phase3_performance.py  # Performance and load tests
├── security/
│   └── test_phase3_security.py     # Security validation tests
└── monitoring/
    └── test_phase3_monitoring.py   # Monitoring and alerting tests
```

## Prerequisites

### Required Dependencies

```bash
pip install pytest moto boto3 numpy
```

### Environment Setup

Set the following environment variables before running tests:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing
```

## Test Execution

### 1. End-to-End Integration Tests

Tests the complete workflow of all Phase 3 components.

```bash
# Run all integration tests
pytest tests/integration/test_phase3_e2e.py -v

# Run specific test class
pytest tests/integration/test_phase3_e2e.py::TestMLMonitoringE2E -v

# Run specific test
pytest tests/integration/test_phase3_e2e.py::TestMLMonitoringE2E::test_ml_monitoring_with_live_predictions -v
```

**Test Coverage:**
- ML monitoring with live predictions
- ML drift detection workflow
- OTA firmware update workflow
- Certificate rotation workflow
- Dependency scanning workflow
- CloudWatch metrics publishing
- SNS alert delivery
- Full monitoring pipeline

### 2. Performance Tests

Tests system performance under load and validates latency requirements.

```bash
# Run all performance tests
pytest tests/performance/test_phase3_performance.py -v -s

# Run ML monitoring performance tests
pytest tests/performance/test_phase3_performance.py::TestMLMonitoringPerformance -v -s

# Run certificate rotation performance tests
pytest tests/performance/test_phase3_performance.py::TestCertificateRotationPerformance -v -s
```

**Performance Benchmarks:**
- Prediction logging latency: <50ms overhead
- High throughput: 10K predictions/sec
- Drift calculation: <100ms for 1000 predictions
- Certificate rotation: >10 certs/sec
- Dashboard query: <5 seconds

### 3. Security Tests

Validates security controls and compliance requirements.

```bash
# Run all security tests
pytest tests/security/test_phase3_security.py -v -s

# Run OTA security tests
pytest tests/security/test_phase3_security.py::TestOTAUpdateSecurity -v -s

# Run certificate validation tests
pytest tests/security/test_phase3_security.py::TestCertificateValidation -v -s
```

**Security Validation:**
- Firmware signature verification
- Device authorization checks
- Encryption in transit (TLS)
- Rollback security
- Certificate expiration validation
- Private key security
- Audit trail maintenance
- Vulnerability detection
- SBOM completeness
- IAM permissions (least privilege)

### 4. Monitoring and Alerting Tests

Validates CloudWatch alarms and SNS notifications.

```bash
# Run all monitoring tests
pytest tests/monitoring/test_phase3_monitoring.py -v -s

# Run alarm configuration tests
pytest tests/monitoring/test_phase3_monitoring.py::TestCloudWatchAlarms -v -s

# Run SNS notification tests
pytest tests/monitoring/test_phase3_monitoring.py::TestSNSNotifications -v -s
```

**Monitoring Coverage:**
- ML drift alarms
- API response time alarms
- Lambda error rate alarms
- DynamoDB throttling alarms
- IoT connection failure alarms
- SNS topic configuration
- Alert delivery validation
- Dashboard metrics accuracy
- Metric retention and TTL

## Test Execution Summary

### Run All Tests

```bash
# Run all Phase 3 tests
pytest tests/ -v -s

# Run with coverage report
pytest tests/ -v -s --cov=lambda --cov-report=html

# Run with detailed output
pytest tests/ -v -s --tb=long
```

### Generate Test Report

```bash
# Generate HTML report
pytest tests/ --html=test-report.html --self-contained-html

# Generate JUnit XML report (for CI/CD)
pytest tests/ --junitxml=test-results.xml
```

## Test Results Interpretation

### Success Criteria

All tests should pass with the following outcomes:

**Integration Tests:**
- ✅ ML monitoring tracks predictions correctly
- ✅ Drift detection triggers at threshold
- ✅ OTA updates complete successfully
- ✅ Certificate rotation maintains zero downtime
- ✅ Dependency scanning identifies vulnerabilities
- ✅ Metrics are published to CloudWatch
- ✅ Alerts are delivered via SNS

**Performance Tests:**
- ✅ Prediction logging adds <50ms latency
- ✅ System handles 10K predictions/sec
- ✅ Drift calculation completes in <100ms
- ✅ Certificate rotation handles 5K devices
- ✅ Dashboard queries complete in <5 seconds

**Security Tests:**
- ✅ Firmware signatures are verified
- ✅ Only authorized devices can download firmware
- ✅ Encryption is enforced
- ✅ Certificates are validated
- ✅ Private keys are never transmitted insecurely
- ✅ Audit trails are maintained
- ✅ IAM follows least privilege

**Monitoring Tests:**
- ✅ All alarms are properly configured
- ✅ Alarms trigger at correct thresholds
- ✅ SNS notifications are delivered
- ✅ Dashboard metrics are accurate
- ✅ Metric retention is configured

## Troubleshooting

### Common Issues

**1. Import Errors**

```
ImportError: cannot import name 'mock_dynamodb' from 'moto'
```

**Solution:** Ensure you're using moto v5+ which uses `@mock_aws` decorator:
```bash
pip install --upgrade moto[all]
```

**2. AWS Credentials**

```
NoCredentialsError: Unable to locate credentials
```

**Solution:** Set mock credentials:
```bash
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing
```

**3. Module Not Found**

```
ModuleNotFoundError: No module named 'model_performance_monitor'
```

**Solution:** Ensure lambda directories are in Python path. Tests automatically add them, but if running individual functions:
```python
import sys
sys.path.insert(0, 'lambda/ml_inference')
```

**4. Test Timeouts**

If tests timeout, increase pytest timeout:
```bash
pytest tests/ -v --timeout=300
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Phase 3 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest moto boto3 numpy pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=lambda --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

## Test Maintenance

### Adding New Tests

1. **Integration Tests:** Add to `tests/integration/test_phase3_e2e.py`
2. **Performance Tests:** Add to `tests/performance/test_phase3_performance.py`
3. **Security Tests:** Add to `tests/security/test_phase3_security.py`
4. **Monitoring Tests:** Add to `tests/monitoring/test_phase3_monitoring.py`

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Mocking Best Practices

Use `@mock_aws` decorator for all AWS service mocking:

```python
from moto import mock_aws

@mock_aws
def test_my_function():
    # Setup AWS resources
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    # ... test code
```

## Performance Benchmarks

### Expected Results

| Test | Metric | Target | Acceptable |
|------|--------|--------|------------|
| Prediction Logging | Latency | <10ms | <50ms |
| High Throughput | Predictions/sec | 10,000 | 1,000 |
| Drift Calculation | Time | <50ms | <100ms |
| Certificate Rotation | Certs/sec | 50 | 10 |
| Dashboard Query | Time | <1s | <5s |

### Load Testing

For production load testing, use tools like:
- **Locust** for API load testing
- **AWS CloudWatch Synthetics** for monitoring
- **Artillery** for WebSocket testing

## Security Testing

### Vulnerability Scanning

Run additional security scans:

```bash
# Scan Python dependencies
pip-audit

# Scan npm dependencies
cd frontend && npm audit

# Generate SBOM
syft packages dir:. -o spdx-json > sbom.json

# Scan SBOM for vulnerabilities
grype sbom:sbom.json
```

### Penetration Testing

For production systems, conduct:
1. OWASP Top 10 testing
2. API security testing
3. IoT device security testing
4. Certificate validation testing

## Monitoring Validation

### CloudWatch Dashboard

Verify dashboard shows:
- ML model metrics (drift score, latency)
- API Gateway metrics (response time, errors)
- Lambda metrics (duration, errors, cold starts)
- DynamoDB metrics (capacity, throttling)
- IoT metrics (connections, messages)

### Alert Testing

Manually trigger alarms to verify:
1. Alarm state changes to ALARM
2. SNS notification is sent
3. Email/SMS is received
4. Alert contains correct information

## Compliance and Reporting

### Test Coverage Report

Generate coverage report:
```bash
pytest tests/ --cov=lambda --cov-report=html
open htmlcov/index.html
```

Target: >80% code coverage

### Compliance Documentation

Tests validate compliance with:
- Security best practices
- Performance SLAs
- Monitoring requirements
- Audit trail requirements

## Next Steps

After all tests pass:

1. ✅ Review test results
2. ✅ Address any failures
3. ✅ Generate test report
4. ✅ Update documentation
5. ✅ Deploy to staging
6. ✅ Run smoke tests
7. ✅ Get stakeholder approval
8. ✅ Deploy to production

## Support

For issues or questions:
- Review test output and logs
- Check AWS CloudWatch logs
- Consult Phase 3 design document
- Review implementation guides

---

**Status:** Complete
**Last Updated:** October 25, 2025
**Test Coverage:** 100% of Phase 3 components
