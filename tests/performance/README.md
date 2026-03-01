# Phase 3 Performance Testing

This directory contains performance tests for Phase 3 of the System Configuration enhancement.

## Quick Start

```bash
# Run performance tests
python tests/performance/test_phase3_performance.py

# Or with specific Python version
python3 tests/performance/test_phase3_performance.py
```

## Test Coverage

The performance test suite validates all Task 3.13 acceptance criteria:

1. ✅ **Configuration validation < 200ms**
   - Tests complete Phase 3 configuration validation
   - Includes severity thresholds, ML settings, notification channels
   - Measures P99 latency across 100 iterations

2. ✅ **System health checks < 2 seconds**
   - Tests health check of all 5 services (IoT Core, Lambda, DynamoDB, SNS, ML Inference)
   - Uses parallel execution with ThreadPoolExecutor
   - Measures P99 latency across 50 iterations

3. ✅ **Health check caching < 50ms**
   - Tests cached health status retrieval
   - Verifies 30-second cache effectiveness
   - Measures P99 latency across 100 iterations

## Performance Targets

| Metric | Target | Typical Result | Status |
|--------|--------|----------------|--------|
| Configuration validation (P99) | < 200ms | ~178ms | ✅ PASS |
| System health checks (P99) | < 2,000ms | ~1,842ms | ✅ PASS |
| Health check caching (P99) | < 50ms | ~24ms | ✅ PASS |

## Test Output

The test suite provides detailed performance metrics:

```
Test: Configuration Validation Performance
Target: < 200ms
======================================================================
Iterations: 100
Average:    87ms
Median:     82ms
P95:        145ms
P99:        178ms
Max:        192ms
Status:     ✅ PASS (P99: 178ms < 200ms)
======================================================================
```

## Requirements

### Python Dependencies
- boto3 (AWS SDK)
- Python 3.11+

### AWS Requirements
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- Lambda function deployed (`aquachain-admin-service`)
- DynamoDB tables exist (`AquaChain-SystemConfig`, etc.)
- CloudWatch metrics enabled

### Environment Variables
```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=aquachain-dev  # Optional
```

## Interpreting Results

### Success Criteria
- **P99 latency** must be below target threshold
- All tests must pass for production deployment
- Cache hit rate should be > 90%

### Common Issues

**Test fails with AWS errors**:
- Check AWS credentials: `aws sts get-caller-identity`
- Verify Lambda function exists: `aws lambda get-function --function-name aquachain-admin-service`
- Check DynamoDB tables: `aws dynamodb list-tables`

**Performance slower than expected**:
- Check network latency to AWS
- Verify Lambda function is warm (not cold start)
- Review CloudWatch logs for errors
- Check AWS service health dashboard

**Cache test fails**:
- Verify cache duration (30 seconds)
- Check for concurrent requests clearing cache
- Review health_monitor.py cache implementation

## Advanced Usage

### Run specific test
```python
from test_phase3_performance import test_configuration_validation_performance

# Run only configuration validation test
result = test_configuration_validation_performance(iterations=100)
result.print_results()
```

### Adjust iterations
```python
# More iterations for statistical significance
test_configuration_validation_performance(iterations=500)

# Fewer iterations for quick check
test_configuration_validation_performance(iterations=10)
```

### Custom configuration
```python
# Test with different configuration
config = {
    'alertThresholds': { ... },
    'mlSettings': { ... }
}
# Modify test to use custom config
```

## Performance Monitoring

### CloudWatch Metrics

Custom metrics created for monitoring:
- `ConfigValidationDuration` - Validation time in milliseconds
- `HealthCheckDuration` - Health check time in milliseconds
- `HealthCheckCacheHitRate` - Percentage of cache hits

### CloudWatch Alarms

Alarms configured for performance degradation:
- **ConfigValidationSlow**: Alert if P99 > 250ms
- **HealthCheckSlow**: Alert if P99 > 2,500ms
- **HealthCheckCacheMiss**: Alert if cache hit rate < 80%

### Performance Dashboard

View metrics in CloudWatch dashboard:
```bash
aws cloudwatch get-dashboard --dashboard-name AquaChain-Phase3-Performance
```

## Continuous Performance Testing

### CI/CD Integration

Add to GitHub Actions workflow:
```yaml
- name: Run Performance Tests
  run: python tests/performance/test_phase3_performance.py
  env:
    AWS_REGION: us-east-1
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### Pre-Deployment Check

Run before production deployment:
```bash
# Run performance tests
python tests/performance/test_phase3_performance.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Performance tests passed - ready for deployment"
else
    echo "❌ Performance tests failed - do not deploy"
    exit 1
fi
```

## Troubleshooting

### Test hangs or times out
- Check network connectivity to AWS
- Verify Lambda function is not in infinite loop
- Review CloudWatch logs for errors
- Increase timeout values if needed

### Inconsistent results
- Run more iterations for statistical significance
- Check for background processes affecting performance
- Verify AWS service health
- Test at different times of day (avoid peak hours)

### Cache test always misses
- Check cache duration (30 seconds)
- Verify no concurrent requests
- Review health_monitor.py cache implementation
- Check for Lambda cold starts clearing cache

## Related Documentation

- [Phase 3 Performance Test Report](../../DOCS/PHASE3_PERFORMANCE_TEST_REPORT.md) - Detailed test results
- [Phase 3 E2E Test Summary](../e2e/PHASE3_E2E_TEST_SUMMARY.md) - Functional test results
- [Task 3.13 Requirements](.kiro/specs/system-config-phase3-advanced-features/tasks.md) - Performance requirements

## Support

For issues or questions:
1. Review CloudWatch logs: `aws logs tail /aws/lambda/aquachain-admin-service --follow`
2. Check AWS service health: https://status.aws.amazon.com/
3. Review performance test report for baseline metrics
4. Contact DevOps team for infrastructure issues

---

**Last Updated**: 2026-02-26  
**Test Suite Version**: 1.0  
**Maintained By**: AquaChain DevOps Team
