# Compliance Service

The Compliance Service provides automated compliance reporting and monitoring for the AquaChain system.

## Features

- **Automated Monthly Reports**: Generate comprehensive compliance reports on the 1st of each month
- **Violation Detection**: Automatically detect and alert on compliance violations
- **GDPR Metrics**: Track GDPR data subject requests and SLA compliance
- **Audit Log Analysis**: Analyze audit logs for data access patterns and security events
- **Real-time Alerts**: Send SNS notifications when violations are detected (within 15 minutes)
- **Dashboard UI**: View compliance status, violations, and metrics in the frontend

## Components

### 1. Report Generator (`report_generator.py`)

Generates comprehensive monthly compliance reports including:
- Data access patterns from audit logs
- Data retention compliance status
- Security controls verification
- GDPR requests metrics and SLA compliance
- Audit log statistics

### 2. Violation Detector (`violation_detector.py`)

Detects compliance violations based on predefined rules:
- **GDPR Export SLA**: Exports must complete within 48 hours
- **GDPR Deletion SLA**: Deletions must complete within 30 days
- **Audit Log Retention**: Logs must be retained for 7 years
- **Failed Login Threshold**: Alert on excessive failed login attempts
- **Data Access Anomaly**: Detect unusual data access patterns

### 3. Scheduled Report Handler (`scheduled_report_handler.py`)

Lambda function triggered monthly by EventBridge to:
- Generate compliance report for previous month
- Check for violations
- Save report to S3
- Send alerts if violations detected

### 4. API Handler (`api_handler.py`)

REST API endpoints for compliance data:
- `GET /compliance/reports` - List recent reports
- `GET /compliance/reports/{year}/{month}` - Get specific report
- `POST /compliance/reports/generate` - Manually trigger report generation
- `GET /compliance/metrics/summary` - Get compliance metrics summary

## Infrastructure

### S3 Bucket

Compliance reports are stored in S3 with:
- KMS encryption
- Versioning enabled
- Lifecycle policies for cost optimization:
  - 90 days: Transition to Infrequent Access
  - 365 days: Transition to Glacier
  - 5 years: Transition to Deep Archive
  - 7 years: Expire old versions

### EventBridge Schedule

Monthly report generation is triggered by EventBridge:
- Schedule: 1st day of each month at 2:00 AM UTC
- Cron expression: `cron(0 2 1 * ? *)`

### SNS Topic

Compliance alerts are sent via SNS to:
- Compliance team email
- CloudWatch alarms

### CloudWatch Alarms

Two alarms monitor compliance violations:
1. **General Violations Alarm**: Triggers on any violation
2. **High Severity Alarm**: Triggers on HIGH or CRITICAL violations

## Usage

### View Compliance Dashboard

Navigate to `/compliance` in the frontend to view:
- Recent compliance reports
- Compliance status (COMPLIANT/NON_COMPLIANT)
- Violations with severity levels
- GDPR request metrics
- Audit log statistics
- Data access metrics

### Manual Report Generation

Trigger manual report generation via API:

```bash
curl -X POST https://api.aquachain.com/compliance/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "month": 10}'
```

### Download Report

Download a specific report:

```bash
curl https://api.aquachain.com/compliance/reports/2025/10 \
  -H "Authorization: Bearer $TOKEN" \
  -o compliance-report-2025-10.json
```

## Compliance Rules

### GDPR Export SLA
- **Threshold**: 48 hours
- **Severity**: HIGH
- **Description**: GDPR data export requests must complete within 48 hours

### GDPR Deletion SLA
- **Threshold**: 30 days
- **Severity**: HIGH
- **Description**: GDPR data deletion requests must complete within 30 days

### Audit Log Retention
- **Threshold**: 7 years
- **Severity**: MEDIUM
- **Description**: Audit logs must be retained for 7 years

### Failed Login Threshold
- **Threshold**: 100 attempts per month
- **Severity**: MEDIUM
- **Description**: Excessive failed login attempts may indicate security issue

### Data Access Anomaly
- **Threshold**: 3x average access
- **Severity**: HIGH
- **Description**: Unusual data access patterns detected

## Alert Response

When a compliance violation is detected:

1. **Immediate**: SNS notification sent to compliance team
2. **Within 15 minutes**: CloudWatch alarm triggers
3. **Action Required**:
   - Review violation details in the report
   - Investigate root cause
   - Implement corrective actions
   - Document remediation steps

## Environment Variables

Required environment variables:

```bash
COMPLIANCE_REPORTS_BUCKET=aquachain-compliance-reports-123456789
AUDIT_LOGS_TABLE=AuditLogs
GDPR_REQUESTS_TABLE=GDPRRequests
DEVICES_TABLE=Devices
USERS_TABLE=Users
COMPLIANCE_ALERTS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:compliance-alerts
```

## Testing

Test report generation locally:

```python
from report_generator import ComplianceReportGenerator

generator = ComplianceReportGenerator()
report = generator.generate_monthly_report(2025, 10)
print(json.dumps(report, indent=2))
```

Test violation detection:

```python
from violation_detector import ComplianceViolationDetector

detector = ComplianceViolationDetector()
violations = detector.check_violations(report)
print(f"Found {len(violations)} violations")
```

## Deployment

Deploy the compliance service:

```bash
cd infrastructure/cdk
cdk deploy ComplianceReportingStack
```

This will create:
- S3 bucket for reports
- Lambda function for report generation
- EventBridge schedule for monthly execution
- SNS topic for alerts
- CloudWatch alarms for violations

## Monitoring

Monitor compliance service health:

1. **CloudWatch Logs**: Check Lambda execution logs
2. **CloudWatch Metrics**: Monitor `AquaChain/Compliance` namespace
3. **S3 Bucket**: Verify reports are being generated
4. **SNS Topic**: Confirm alert delivery

## Troubleshooting

### Reports Not Generating

Check:
- EventBridge rule is enabled
- Lambda function has correct permissions
- Environment variables are set correctly

### Alerts Not Sending

Check:
- SNS topic subscription is confirmed
- Lambda has publish permissions to SNS
- CloudWatch alarms are configured correctly

### Missing Data in Reports

Check:
- DynamoDB tables have data
- Lambda has read permissions to tables
- GSIs are created for efficient querying

## Security

- All reports encrypted with KMS
- S3 bucket blocks public access
- IAM roles follow least privilege principle
- Audit logs are immutable (S3 Object Lock)
- Sensitive data is encrypted at rest

## Compliance

This service helps meet:
- **GDPR**: Data subject request tracking and SLA monitoring
- **SOC 2**: Audit logging and access monitoring
- **ISO 27001**: Security controls verification
- **HIPAA**: Audit trail and data retention (if applicable)
