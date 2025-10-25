# Dependency Security Scanner

Automated vulnerability scanning for npm and Python dependencies in the AquaChain platform.

## Overview

The Dependency Security Scanner is a Lambda function that automatically scans project dependencies for known security vulnerabilities using:
- **npm audit** for JavaScript/Node.js dependencies
- **pip-audit** for Python dependencies

The scanner runs on a weekly schedule and sends alerts when critical or high-severity vulnerabilities are detected.

## Features

- ✅ Automated weekly scanning via EventBridge
- ✅ npm audit integration for frontend dependencies
- ✅ pip-audit integration for backend/Lambda dependencies
- ✅ Severity categorization (Critical, High, Moderate, Low)
- ✅ Actionable recommendations for fixes
- ✅ SNS alerts for critical vulnerabilities
- ✅ CloudWatch metrics and dashboard
- ✅ S3 storage for scan reports with versioning
- ✅ Comprehensive error handling and retry logic

## Architecture

```
┌─────────────────────────────────────────────────┐
│    EventBridge Schedule (Weekly)                │
│    └─ Every Monday at 2 AM UTC                  │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│    Dependency Scanner Lambda                    │
│    ├─ Download source files from S3             │
│    ├─ Run npm audit                             │
│    ├─ Run pip-audit                             │
│    ├─ Generate report                           │
│    └─ Send alerts if needed                     │
└────────────┬────────────────────────────────────┘
             │
             ├──────────────────┬──────────────────┐
             ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│ S3: Reports      │  │ SNS: Alerts  │  │ CloudWatch   │
│ (Versioned)      │  │              │  │ Metrics      │
└──────────────────┘  └──────────────┘  └──────────────┘
```

## Requirements

### Python Dependencies
```
boto3>=1.26.0
pip-audit>=2.6.0
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALERT_TOPIC_ARN` | SNS topic ARN for alerts | Required |
| `RESULTS_BUCKET` | S3 bucket for scan reports | `aquachain-security-scans` |
| `SOURCE_BUCKET` | S3 bucket for source code | `aquachain-source-code` |
| `CRITICAL_THRESHOLD` | Alert threshold for critical vulns | `0` |
| `HIGH_THRESHOLD` | Alert threshold for high vulns | `5` |

## Usage

### Lambda Event Format

```json
{
  "scan_type": "all",
  "source_paths": {
    "npm": "s3://bucket/path/to/package.json",
    "python": [
      "s3://bucket/path/to/requirements.txt",
      "s3://bucket/path/to/another/requirements.txt"
    ]
  }
}
```

### Scan Types

- `all` - Scan both npm and Python dependencies
- `npm` - Scan only npm dependencies
- `python` - Scan only Python dependencies

### Manual Invocation

```bash
aws lambda invoke \
  --function-name aquachain-dependency-scanner \
  --payload '{"scan_type": "all", "source_paths": {...}}' \
  response.json
```

## Report Format

### Report Structure

```json
{
  "timestamp": "2025-10-25T00:00:00Z",
  "summary": {
    "total_vulnerabilities": 5,
    "critical": 1,
    "high": 2,
    "moderate": 2,
    "low": 0
  },
  "scans": {
    "npm": {
      "status": "success",
      "total": 3,
      "by_severity": {
        "critical": 1,
        "high": 1,
        "moderate": 1,
        "low": 0
      },
      "recommendations": [
        "Run 'npm audit fix' to automatically fix 2 vulnerabilities",
        "1 fixes require major version updates"
      ],
      "details": [...]
    },
    "python": {
      "status": "success",
      "total": 2,
      "by_severity": {
        "critical": 0,
        "high": 1,
        "moderate": 1,
        "low": 0
      },
      "recommendations": [
        "Update requests to version 2.28.0 to fix 1 vulnerability(ies)"
      ],
      "details": [...]
    }
  },
  "overall_recommendations": [
    "IMMEDIATE ACTION REQUIRED: Critical or high severity vulnerabilities detected",
    "Total of 5 vulnerabilities found across all dependencies"
  ],
  "action_required": true
}
```

### Report Storage

Reports are stored in S3 with the following structure:
```
s3://aquachain-security-scans/
├── dependency-scans/
│   ├── report-20251025-020000.json
│   ├── report-20251101-020000.json
│   └── latest.json  (always points to most recent)
```

## Alerts

### Alert Conditions

Alerts are sent via SNS when:
- Any critical vulnerabilities are detected (threshold: 0)
- More than 5 high-severity vulnerabilities are detected
- Scanner function errors occur

### Alert Format

```json
{
  "timestamp": "2025-10-25T00:00:00Z",
  "severity": "CRITICAL",
  "summary": {
    "total_vulnerabilities": 5,
    "critical": 1,
    "high": 2,
    "moderate": 2,
    "low": 0
  },
  "recommendations": [
    "IMMEDIATE ACTION REQUIRED: Critical or high severity vulnerabilities detected"
  ],
  "action_required": "Review and update dependencies immediately",
  "report_location": "s3://aquachain-security-scans/dependency-scans/"
}
```

## CloudWatch Metrics

The scanner publishes the following metrics to the `AquaChain/Security` namespace:

| Metric | Description | Unit |
|--------|-------------|------|
| `Vulnerabilities_Critical` | Count of critical vulnerabilities | Count |
| `Vulnerabilities_High` | Count of high vulnerabilities | Count |
| `Vulnerabilities_Moderate` | Count of moderate vulnerabilities | Count |
| `Vulnerabilities_Low` | Count of low vulnerabilities | Count |
| `Vulnerabilities_Total` | Total vulnerability count | Count |

## Dashboard

A CloudWatch dashboard is automatically created with:
- Vulnerability trends over time
- Total vulnerability count
- Scanner function performance metrics
- Error rates and duration

Access the dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Dependency-Security
```

## Testing

### Run Unit Tests

```bash
cd lambda/dependency_scanner
python -m pytest test_dependency_scanner.py -v
```

### Test Coverage

```bash
python -m pytest test_dependency_scanner.py --cov=dependency_scanner --cov-report=html
```

### Test Categories

- **Scanner initialization** - Verify proper setup
- **npm audit integration** - Test npm vulnerability scanning
- **pip-audit integration** - Test Python vulnerability scanning
- **Report generation** - Test report formatting
- **Alert sending** - Test SNS notifications
- **Error handling** - Test failure scenarios

## Deployment

### Using CDK

```bash
cd infrastructure/cdk
cdk deploy DependencyScannerStack
```

### Manual Deployment

1. Package Lambda function:
```bash
cd lambda/dependency_scanner
pip install -r requirements.txt -t .
zip -r function.zip .
```

2. Upload to Lambda:
```bash
aws lambda update-function-code \
  --function-name aquachain-dependency-scanner \
  --zip-file fileb://function.zip
```

## Troubleshooting

### Common Issues

#### npm audit fails
- **Cause**: Missing package-lock.json
- **Solution**: Ensure package-lock.json is uploaded to S3 alongside package.json

#### pip-audit not found
- **Cause**: pip-audit not installed in Lambda environment
- **Solution**: The function auto-installs pip-audit on first run

#### Timeout errors
- **Cause**: Large dependency trees take time to scan
- **Solution**: Increase Lambda timeout (current: 15 minutes)

#### No alerts received
- **Cause**: SNS topic not configured or no subscriptions
- **Solution**: Add email subscription to SNS topic

### Logs

View Lambda logs in CloudWatch:
```bash
aws logs tail /aws/lambda/aquachain-dependency-scanner --follow
```

## Security Considerations

- ✅ All reports are encrypted at rest in S3
- ✅ Lambda function has minimal IAM permissions
- ✅ Source code is stored in separate S3 bucket
- ✅ SNS topics use encryption in transit
- ✅ CloudWatch metrics are namespaced

## Maintenance

### Weekly Tasks
- Review scan reports in S3
- Address critical and high vulnerabilities
- Update dependencies as recommended

### Monthly Tasks
- Review CloudWatch dashboard trends
- Adjust alert thresholds if needed
- Clean up old reports (automatic via lifecycle policy)

### Quarterly Tasks
- Review and update scanner configuration
- Test alert notifications
- Audit IAM permissions

## Integration with CI/CD

The scanner can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Upload dependencies to S3
  run: |
    aws s3 cp package.json s3://aquachain-source-snapshots/frontend/
    aws s3 cp package-lock.json s3://aquachain-source-snapshots/frontend/

- name: Trigger dependency scan
  run: |
    aws lambda invoke \
      --function-name aquachain-dependency-scanner \
      --payload '{"scan_type": "npm", "source_paths": {"npm": "s3://aquachain-source-snapshots/frontend/package.json"}}' \
      response.json
```

## Related Documentation

- [Phase 3 Requirements](../../.kiro/specs/phase-3-high-priority/requirements.md)
- [Phase 3 Design](../../.kiro/specs/phase-3-high-priority/design.md)
- [SBOM Generation](../../scripts/generate-sbom.py)
- [Security Best Practices](../../SECURITY_QUICK_START.md)

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review S3 reports for details
3. Consult the troubleshooting section
4. Contact the DevOps team

## License

Copyright © 2025 AquaChain. All rights reserved.
