# Compliance Reporting Quick Reference

## Overview

Automated compliance reporting system that generates monthly reports, detects violations, and sends alerts.

## Key Features

- 📊 **Monthly Reports**: Automated generation on 1st of each month
- 🚨 **Violation Detection**: Real-time detection with 5 compliance rules
- 📧 **Alerts**: SNS notifications within 15 minutes
- 📈 **Dashboard**: View reports and metrics in UI
- 🔒 **Secure Storage**: Encrypted S3 with lifecycle policies

## Quick Commands

### View Compliance Dashboard

```
Navigate to: /compliance
```

### Generate Manual Report

```bash
curl -X POST https://api.aquachain.com/compliance/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"year": 2025, "month": 10}'
```

### List Recent Reports

```bash
curl https://api.aquachain.com/compliance/reports?limit=12 \
  -H "Authorization: Bearer $TOKEN"
```

### Get Specific Report

```bash
curl https://api.aquachain.com/compliance/reports/2025/10 \
  -H "Authorization: Bearer $TOKEN"
```

## Compliance Rules

| Rule | Threshold | Severity | Description |
|------|-----------|----------|-------------|
| GDPR Export SLA | 48 hours | HIGH | Data exports must complete within 48h |
| GDPR Deletion SLA | 30 days | HIGH | Data deletions must complete within 30d |
| Audit Log Retention | 7 years | MEDIUM | Audit logs must be retained for 7 years |
| Failed Login Threshold | 100/month | MEDIUM | Alert on excessive failed logins |
| Data Access Anomaly | 3x average | HIGH | Detect unusual access patterns |

## Report Sections

1. **Data Access**: Access patterns, unique users, resource usage
2. **Data Retention**: Retention compliance, inactive devices
3. **Security Controls**: Authentication, encryption, monitoring
4. **GDPR Requests**: Request metrics, SLA compliance
5. **Audit Summary**: Total logs, action types, retention status

## Alert Response

When violation detected:

1. ✅ **Immediate**: SNS notification sent
2. ✅ **Within 15 min**: CloudWatch alarm triggers
3. 📋 **Action Required**:
   - Review violation details
   - Investigate root cause
   - Implement corrective actions
   - Document remediation

## File Locations

```
lambda/compliance_service/
├── report_generator.py          # Report generation logic
├── violation_detector.py        # Violation detection rules
├── scheduled_report_handler.py  # Monthly Lambda handler
├── api_handler.py              # REST API endpoints
└── README.md                   # Detailed documentation

infrastructure/cdk/stacks/
└── compliance_reporting_stack.py  # CDK infrastructure

frontend/src/
├── pages/ComplianceDashboard.tsx  # Dashboard UI
└── services/complianceService.ts  # API client
```

## Environment Variables

```bash
COMPLIANCE_REPORTS_BUCKET=aquachain-compliance-reports-{account}
AUDIT_LOGS_TABLE=AuditLogs
GDPR_REQUESTS_TABLE=GDPRRequests
DEVICES_TABLE=Devices
USERS_TABLE=Users
COMPLIANCE_ALERTS_TOPIC_ARN=arn:aws:sns:region:account:compliance-alerts
```

## Deployment

```bash
# Deploy infrastructure
cd infrastructure/cdk
cdk deploy ComplianceReportingStack

# Confirm SNS subscription
# Check email and click confirmation link
```

## Monitoring

### CloudWatch Logs
```
/aws/lambda/compliance-report-generator
```

### CloudWatch Metrics
```
Namespace: AquaChain/Compliance
Metric: ComplianceViolations
Dimensions: ReportPeriod, Severity
```

### S3 Reports
```
s3://compliance-reports-bucket/compliance-reports/YYYY/MM/
```

## Troubleshooting

### Reports Not Generating

```bash
# Check EventBridge rule
aws events describe-rule --name compliance-monthly-report

# Check Lambda logs
aws logs tail /aws/lambda/compliance-report-generator --follow

# Verify permissions
aws iam get-role --role-name compliance-report-generator
```

### Alerts Not Sending

```bash
# Check SNS topic
aws sns list-subscriptions-by-topic --topic-arn $TOPIC_ARN

# Check CloudWatch alarms
aws cloudwatch describe-alarms --alarm-names compliance-violations

# Test SNS
aws sns publish --topic-arn $TOPIC_ARN --message "Test alert"
```

### Missing Data

```bash
# Check DynamoDB tables
aws dynamodb describe-table --table-name AuditLogs
aws dynamodb describe-table --table-name GDPRRequests

# Verify Lambda permissions
aws lambda get-policy --function-name compliance-report-generator
```

## Testing

### Test Report Generation

```python
from report_generator import ComplianceReportGenerator

generator = ComplianceReportGenerator()
report = generator.generate_monthly_report(2025, 10)
print(f"Status: {report['compliance_status']}")
print(f"Violations: {len(report['violations'])}")
```

### Test Violation Detection

```python
from violation_detector import ComplianceViolationDetector

detector = ComplianceViolationDetector()
violations = detector.check_violations(report)

for v in violations:
    print(f"{v['severity']}: {v['rule_name']}")
```

### Test API

```bash
# Health check
curl https://api.aquachain.com/compliance/metrics/summary

# Generate test report
curl -X POST https://api.aquachain.com/compliance/reports/generate \
  -d '{"year": 2025, "month": 10}'
```

## Security Checklist

- ✅ KMS encryption enabled
- ✅ S3 bucket blocks public access
- ✅ IAM roles follow least privilege
- ✅ HTTPS enforced for all requests
- ✅ Audit logs are immutable
- ✅ Reports are versioned
- ✅ SNS messages encrypted

## Compliance Checklist

- ✅ GDPR: Data subject request tracking
- ✅ SOC 2: Audit logging and monitoring
- ✅ ISO 27001: Security controls verification
- ✅ HIPAA: Audit trail and retention (if applicable)

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review README documentation
3. Contact DevOps team
4. Escalate to compliance officer

## Resources

- **Full Documentation**: `lambda/compliance_service/README.md`
- **Implementation Summary**: `TASK_20_COMPLIANCE_REPORTING_IMPLEMENTATION.md`
- **CDK Stack**: `infrastructure/cdk/stacks/compliance_reporting_stack.py`
- **Dashboard**: `frontend/src/pages/ComplianceDashboard.tsx`
