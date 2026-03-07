# AquaChain Comprehensive System Testing Suite

## Overview

The Comprehensive System Testing Suite is an all-in-one testing solution that performs in-depth analysis across all AquaChain components and generates detailed reports with actionable recommendations.

## Features

### Test Categories

1. **Unit Tests**
   - Python backend unit tests (pytest)
   - Frontend unit tests (Jest)
   - Code coverage analysis

2. **API Tests**
   - Health check endpoints
   - Authentication and authorization
   - Rate limiting validation
   - CORS configuration

3. **Database Tests**
   - DynamoDB table existence
   - Table capacity and configuration
   - TTL settings for GDPR compliance

4. **IoT Tests**
   - AWS IoT Core connectivity
   - MQTT message validation
   - Sensor reading range checks

5. **Security Tests**
   - Hardcoded secrets detection
   - IAM least privilege validation
   - Encryption verification

6. **Performance Tests**
   - API latency measurement (p50, p95, p99)
   - Lambda cold start analysis
   - Throughput testing

7. **Compliance Tests**
   - GDPR data retention policies
   - Audit logging verification
   - Data export capabilities

8. **Integration Tests**
   - End-to-end device flow
   - Multi-service interactions
   - Data pipeline validation

## Installation

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- Node.js 18+ (for frontend tests)
- Access to target AWS environment

### Install Dependencies

```bash
# Python dependencies
pip install boto3 requests pytest

# Frontend dependencies (if running frontend tests)
cd frontend
npm install
```

## Usage

### Quick Start

**Windows (Batch):**
```batch
scripts\testing\run-comprehensive-test.bat dev
```

**Windows (PowerShell):**
```powershell
.\scripts\testing\run-comprehensive-test.ps1 -Environment dev
```

**Python Direct:**
```bash
python scripts/testing/comprehensive-system-test.py --environment dev --output-dir ./reports
```

### Command-Line Options

```
--environment {dev|staging|prod}
    Target environment for testing (default: dev)

--output-dir PATH
    Directory for test reports (default: ./reports)
```

### Examples

```bash
# Test development environment
python scripts/testing/comprehensive-system-test.py --environment dev

# Test staging with custom output directory
python scripts/testing/comprehensive-system-test.py --environment staging --output-dir ./test-results

# Test production (requires production AWS credentials)
python scripts/testing/comprehensive-system-test.py --environment prod
```

## Report Formats

### JSON Report

Structured JSON report with complete test results, metrics, and metadata.

**Location:** `./reports/test-report-{environment}-{timestamp}.json`

**Structure:**
```json
{
  "environment": "dev",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": "2024-01-15T10:35:00Z",
  "total_duration_seconds": 300.5,
  "total_tests": 15,
  "passed": 12,
  "failed": 1,
  "skipped": 1,
  "warnings": 1,
  "results": [...],
  "system_info": {...},
  "coverage_summary": {...},
  "performance_metrics": {...},
  "recommendations": [...]
}
```

### HTML Report

Interactive HTML report with visual summaries and detailed test results.

**Location:** `./reports/test-report-{environment}-{timestamp}.html`

**Features:**
- Color-coded test results
- Summary statistics dashboard
- Categorized test results
- Actionable recommendations
- Performance metrics visualization

## Test Result Interpretation

### Status Codes

- ✓ **PASSED**: Test completed successfully, no issues detected
- ✗ **FAILED**: Test failed, immediate attention required
- ⚠ **WARNING**: Test passed with concerns, review recommended
- ○ **SKIPPED**: Test skipped (not applicable or requires specific conditions)

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Performance Benchmarks

### Expected Latencies

| Metric | Target | Warning Threshold |
|--------|--------|-------------------|
| API P95 Latency | <500ms | >500ms |
| API P99 Latency | <1000ms | >1000ms |
| Lambda Cold Start | <2000ms | >3000ms |
| DynamoDB Query | <100ms | >200ms |

### Coverage Targets

| Component | Minimum Coverage |
|-----------|------------------|
| Python Backend | 80% |
| Frontend | 70% |
| Critical Paths | 95% |

## Troubleshooting

### Common Issues

**Issue: "AWS credentials not configured"**
```bash
# Solution: Configure AWS CLI
aws configure
```

**Issue: "Python module not found"**
```bash
# Solution: Install missing dependencies
pip install -r requirements.txt
```

**Issue: "API endpoint unreachable"**
- Verify the environment is deployed
- Check VPN/network connectivity
- Confirm API Gateway is running

**Issue: "DynamoDB table not found"**
- Ensure CDK stacks are deployed
- Verify table naming convention matches environment
- Check AWS region configuration

### Debug Mode

Enable verbose logging:
```bash
export LOG_LEVEL=DEBUG
python scripts/testing/comprehensive-system-test.py --environment dev
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Comprehensive System Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install boto3 requests pytest
      
      - name: Run comprehensive tests
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python scripts/testing/comprehensive-system-test.py --environment dev
      
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: reports/
```

## Extending the Test Suite

### Adding New Tests

1. Create a new test method in `ComprehensiveSystemTester` class:

```python
def test_my_new_feature(self):
    """Test description"""
    start = time.time()
    try:
        # Test logic here
        result = perform_test()
        duration = (time.time() - start) * 1000
        
        self._record_result(
            "My New Feature Test",
            TestCategory.INTEGRATION,
            TestStatus.PASSED if result else TestStatus.FAILED,
            duration,
            "Test message",
            {"details": "additional info"}
        )
    except Exception as e:
        self._record_result(
            "My New Feature Test",
            TestCategory.INTEGRATION,
            TestStatus.FAILED,
            (time.time() - start) * 1000,
            f"Exception: {str(e)}",
            {"error": str(e)}
        )
```

2. Add the test method to `run_all_tests()`:

```python
test_methods = [
    # ... existing tests
    self.test_my_new_feature,
]
```

### Adding New Test Categories

1. Add to `TestCategory` enum:

```python
class TestCategory(Enum):
    # ... existing categories
    MY_CATEGORY = "My Category Tests"
```

2. Create tests using the new category:

```python
self._record_result(
    "Test Name",
    TestCategory.MY_CATEGORY,
    TestStatus.PASSED,
    duration,
    "Message"
)
```

## Best Practices

1. **Run tests regularly**: Execute comprehensive tests before deployments
2. **Review warnings**: Don't ignore WARNING status - investigate and resolve
3. **Monitor trends**: Track test duration and performance metrics over time
4. **Update thresholds**: Adjust performance benchmarks as system evolves
5. **Document failures**: Add context to failed tests for future reference

## Support

For issues or questions:
- Check the troubleshooting section above
- Review test logs in `./reports/` directory
- Consult AquaChain documentation in `DOCS/`
- Contact the engineering team

## Version History

- **v1.0** (March 2026): Initial comprehensive test suite
  - 15+ test categories
  - JSON and HTML reporting
  - Performance benchmarking
  - Security scanning
  - GDPR compliance checks
