# Phase 4 Compliance Reporting Runbook

## Overview

This runbook provides operational procedures for generating, reviewing, and managing compliance reports in the AquaChain IoT water quality monitoring system. It is designed for compliance officers, auditors, and system administrators.

## Table of Contents

1. [Report Types](#report-types)
2. [Automated Report Generation](#automated-report-generation)
3. [Manual Report Generation](#manual-report-generation)
4. [Report Review Procedures](#report-review-procedures)
5. [Violation Detection and Response](#violation-detection-and-response)
6. [Report Distribution](#report-distribution)
7. [Troubleshooting](#troubleshooting)
8. [Emergency Procedures](#emergency-procedures)

---

## Report Types

### Monthly Compliance Reports

Generated automatically on the 1st of each month, covering the previous month's activities.

#### Data Access Report

**Purpose**: Track all access to personal data for GDPR Article 30 compliance.

**Contents**:
- Total data access events
- Access by user role
- Access by data type
- Unusual access patterns
- Failed access attempts

**Location**: `s3://aquachain-compliance-reports/monthly/YYYY-MM/data-access-report.json`

#### Data Retention Report

**Purpose**: Verify data retention policies are being enforced.

**Contents**:
- Data types and retention periods
- Records approaching retention limit
- Records deleted per retention policy
- Exceptions to retention policy

**Location**: `s3://aquachain-compliance-reports/monthly/YYYY-MM/data-retention-report.json`

#### Security Controls Report

**Purpose**: Verify security controls are functioning correctly.

**Contents**:
- Encryption status (data at rest and in transit)
- Authentication events (successful and failed)
- Authorization violations
- Security incidents
- Vulnerability scan results

**Location**: `s3://aquachain-compliance-reports/monthly/YYYY-MM/security-controls-report.json`

#### GDPR Requests Report

**Purpose**: Track GDPR data subject requests and response times.

**Contents**:
- Total requests by type (export, deletion, rectification)
- Average response time
- Requests exceeding SLA
- Request status breakdown
- Completion rate

**Location**: `s3://aquachain-compliance-reports/monthly/YYYY-MM/gdpr-requests-report.json`

### Quarterly Compliance Reports

Generated automatically on the 1st of January, April, July, and October.

#### Comprehensive Compliance Report

**Purpose**: Provide executive summary of compliance posture.

**Contents**:
- Summary of monthly reports
- Compliance metrics trends
- Risk assessment
- Recommendations for improvement
- Regulatory changes impact

**Location**: `s3://aquachain-compliance-reports/quarterly/YYYY-QN/comprehensive-report.pdf`

### Ad-Hoc Reports

Generated on-demand for specific investigations or audits.

#### Audit Trail Report

**Purpose**: Provide complete audit trail for specific user or time period.

**Contents**:
- All actions by specified user
- All actions on specified resource
- All actions in specified time range
- Detailed event information

#### Incident Investigation Report

**Purpose**: Document security incident investigation.

**Contents**:
- Incident timeline
- Affected users and data
- Root cause analysis
- Remediation actions
- Lessons learned

---

## Automated Report Generation

### Monthly Report Schedule

**Trigger**: EventBridge rule runs on 1st of each month at 02:00 UTC

**Lambda Function**: `compliance-report-generator`

**Process Flow**:

```
1. EventBridge triggers Lambda
2. Lambda queries audit logs for previous month
3. Lambda generates all monthly reports
4. Lambda uploads reports to S3
5. Lambda sends notification to compliance team
6. Lambda updates compliance dashboard
```

### Monitoring Automated Reports

**Check Report Generation Status**:

```bash
# List recent reports
aws s3 ls s3://aquachain-compliance-reports/monthly/ --recursive | tail -20

# Check Lambda execution logs
aws logs tail /aws/lambda/compliance-report-generator --since 1h

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AquaChain/Compliance \
  --metric-name ReportGenerationSuccess \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### Verifying Report Completeness

**Checklist**:

- [ ] Data Access Report exists
- [ ] Data Retention Report exists
- [ ] Security Controls Report exists
- [ ] GDPR Requests Report exists
- [ ] All reports have valid JSON structure
- [ ] Reports contain data for correct time period
- [ ] Report file sizes are reasonable (not empty or truncated)
- [ ] Notification email was sent

**Verification Script**:

```python
# scripts/verify-compliance-reports.py

import boto3
import json
from datetime import datetime, timedelta

s3 = boto3.client('s3')
bucket = 'aquachain-compliance-reports'

def verify_monthly_reports(year, month):
    """Verify all monthly reports exist and are valid"""
    
    report_types = [
        'data-access-report.json',
        'data-retention-report.json',
        'security-controls-report.json',
        'gdpr-requests-report.json'
    ]
    
    prefix = f'monthly/{year}-{month:02d}/'
    
    for report_type in report_types:
        key = f'{prefix}{report_type}'
        
        try:
            # Check if report exists
            response = s3.head_object(Bucket=bucket, Key=key)
            print(f'✓ {report_type} exists ({response["ContentLength"]} bytes)')
            
            # Validate JSON structure
            obj = s3.get_object(Bucket=bucket, Key=key)
            data = json.loads(obj['Body'].read())
            
            # Check required fields
            assert 'report_date' in data
            assert 'report_type' in data
            assert 'data' in data
            
            print(f'✓ {report_type} is valid')
            
        except Exception as e:
            print(f'✗ {report_type} failed: {str(e)}')
            return False
    
    return True

# Usage
if __name__ == '__main__':
    last_month = datetime.now() - timedelta(days=30)
    success = verify_monthly_reports(last_month.year, last_month.month)
    
    if success:
        print('\n✓ All reports verified successfully')
    else:
        print('\n✗ Report verification failed')
        exit(1)
```

---

## Manual Report Generation

### When to Generate Manual Reports

- Automated report generation failed
- Ad-hoc audit request
- Incident investigation
- Regulatory inquiry
- Executive request

### Generating Reports via CLI

**Data Access Report**:

```bash
# Invoke Lambda function manually
aws lambda invoke \
  --function-name compliance-report-generator \
  --payload '{"report_type": "data_access", "start_date": "2025-10-01", "end_date": "2025-10-31"}' \
  response.json

# Check response
cat response.json
```

**GDPR Requests Report**:

```bash
aws lambda invoke \
  --function-name compliance-report-generator \
  --payload '{"report_type": "gdpr_requests", "start_date": "2025-10-01", "end_date": "2025-10-31"}' \
  response.json
```

**Custom Audit Trail Report**:

```bash
# Generate report for specific user
aws lambda invoke \
  --function-name compliance-report-generator \
  --payload '{"report_type": "audit_trail", "user_id": "user-123", "start_date": "2025-10-01", "end_date": "2025-10-31"}' \
  response.json
```

### Generating Reports via UI

**Steps**:

1. Navigate to Compliance Dashboard
2. Click "Generate Report" button
3. Select report type from dropdown
4. Enter date range
5. Click "Generate"
6. Wait for completion notification
7. Download report from dashboard

**UI Location**: `/admin/compliance/reports`

### Generating Reports via API

**Endpoint**: `POST /api/compliance/reports`

**Request**:

```json
{
  "report_type": "data_access",
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "format": "json"
}
```

**Response**:

```json
{
  "report_id": "report-abc123",
  "status": "generating",
  "estimated_completion": "2025-10-25T10:35:00Z"
}
```

**Check Status**:

```bash
curl -X GET https://api.aquachain.com/api/compliance/reports/report-abc123 \
  -H "Authorization: Bearer $TOKEN"
```

**Download Report**:

```bash
curl -X GET https://api.aquachain.com/api/compliance/reports/report-abc123/download \
  -H "Authorization: Bearer $TOKEN" \
  -o report.json
```

---

## Report Review Procedures

### Monthly Review Process

**Timeline**: Complete within 5 business days of report generation

**Responsible**: Compliance Officer

**Steps**:

1. **Verify Report Completeness**
   - [ ] All required reports generated
   - [ ] No errors in report generation
   - [ ] Data covers correct time period

2. **Review Data Access Report**
   - [ ] Total access events within expected range
   - [ ] No unusual access patterns detected
   - [ ] Failed access attempts are reasonable
   - [ ] All access is properly authorized

3. **Review Data Retention Report**
   - [ ] Retention policies are being enforced
   - [ ] No overdue deletions
   - [ ] Exceptions are documented and justified

4. **Review Security Controls Report**
   - [ ] All data is encrypted
   - [ ] No security incidents or all incidents resolved
   - [ ] Authentication success rate is acceptable
   - [ ] No critical vulnerabilities

5. **Review GDPR Requests Report**
   - [ ] All requests completed within SLA
   - [ ] No overdue requests
   - [ ] Response times are acceptable
   - [ ] Completion rate is 100%

6. **Document Findings**
   - Create summary document
   - Note any issues or concerns
   - Recommend corrective actions
   - Update compliance dashboard

7. **Escalate Issues**
   - Report violations to management
   - Create remediation tickets
   - Schedule follow-up review

### Review Checklist Template

```markdown
# Compliance Report Review - [Month Year]

**Reviewer**: [Name]
**Date**: [Date]
**Reports Reviewed**: [List of reports]

## Data Access Report
- Total Events: [Number]
- Unusual Patterns: [Yes/No - Details]
- Failed Attempts: [Number - Acceptable/Concerning]
- Issues Found: [None/List]

## Data Retention Report
- Policies Enforced: [Yes/No]
- Overdue Deletions: [Number]
- Exceptions: [Number - Justified/Unjustified]
- Issues Found: [None/List]

## Security Controls Report
- Encryption Status: [All Encrypted/Issues]
- Security Incidents: [Number - All Resolved/Pending]
- Authentication: [Success Rate %]
- Vulnerabilities: [None/List]
- Issues Found: [None/List]

## GDPR Requests Report
- Total Requests: [Number]
- Within SLA: [Number/%]
- Overdue: [Number]
- Completion Rate: [%]
- Issues Found: [None/List]

## Overall Assessment
- Compliance Status: [Compliant/Non-Compliant]
- Risk Level: [Low/Medium/High]
- Action Items: [List]

## Recommendations
[List of recommendations]

## Sign-off
Reviewed by: [Name]
Date: [Date]
Signature: [Signature]
```

---

## Violation Detection and Response

### Automated Violation Detection

**Violation Types**:

| Violation | Detection Rule | Severity | Response Time |
|-----------|----------------|----------|---------------|
| Overdue GDPR request | Request age > 30 days | High | 15 minutes |
| Unauthorized data access | Access without permission | Critical | Immediate |
| Retention policy violation | Data past retention period | Medium | 24 hours |
| Encryption failure | Unencrypted PII detected | Critical | Immediate |
| Excessive failed logins | >10 failures in 5 minutes | Medium | 15 minutes |

### Violation Alert Process

**Flow**:

```
1. Violation detected by Lambda function
2. SNS notification sent to compliance team
3. Ticket created in issue tracking system
4. Compliance officer investigates
5. Remediation actions taken
6. Violation resolved and documented
7. Follow-up review scheduled
```

### Responding to Violations

#### Overdue GDPR Request

**Immediate Actions**:
1. Check request status in GDPRRequests table
2. Identify cause of delay
3. Prioritize request processing
4. Notify user of delay and new timeline
5. Escalate to management if needed

**Investigation**:
```bash
# Check request details
aws dynamodb get-item \
  --table-name GDPRRequests \
  --key '{"request_id": {"S": "req-123"}}'

# Check processing logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/gdpr-export-handler \
  --filter-pattern "req-123"
```

#### Unauthorized Data Access

**Immediate Actions**:
1. Identify user and resource accessed
2. Verify if access was truly unauthorized
3. Revoke user access if necessary
4. Notify security team
5. Document incident

**Investigation**:
```bash
# Query audit logs
aws dynamodb query \
  --table-name AuditLogs \
  --index-name action_type-timestamp-index \
  --key-condition-expression "action_type = :type" \
  --expression-attribute-values '{":type": {"S": "UNAUTHORIZED_ACCESS"}}'
```

#### Retention Policy Violation

**Immediate Actions**:
1. Identify data past retention period
2. Verify retention policy is correct
3. Schedule immediate deletion
4. Document exception if deletion cannot occur
5. Update retention monitoring

**Remediation**:
```python
# scripts/cleanup-overdue-data.py

import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SensorReadings')

# Find records past retention period (e.g., 2 years)
retention_date = datetime.now() - timedelta(days=730)

# Scan for old records
response = table.scan(
    FilterExpression='timestamp < :retention_date',
    ExpressionAttributeValues={
        ':retention_date': retention_date.isoformat()
    }
)

# Delete old records
for item in response['Items']:
    table.delete_item(
        Key={
            'device_id': item['device_id'],
            'timestamp': item['timestamp']
        }
    )
    print(f"Deleted record: {item['device_id']} - {item['timestamp']}")
```

---

## Report Distribution

### Distribution Lists

**Monthly Reports**:
- Compliance Officer (primary)
- Chief Information Security Officer
- Data Protection Officer
- Legal Team

**Quarterly Reports**:
- Executive Team
- Board of Directors
- External Auditors (if applicable)

**Incident Reports**:
- Incident Response Team
- Security Team
- Legal Team
- Management (as appropriate)

### Distribution Methods

**Email Notification**:

```python
# lambda/compliance_service/report_notifier.py

import boto3

ses = boto3.client('ses')

def send_report_notification(report_type, report_url, recipients):
    """Send email notification with report link"""
    
    subject = f'Compliance Report Available: {report_type}'
    
    body = f"""
    A new compliance report is available for review:
    
    Report Type: {report_type}
    Generated: {datetime.now().isoformat()}
    
    Download: {report_url}
    
    Please review within 5 business days.
    
    AquaChain Compliance System
    """
    
    ses.send_email(
        Source='compliance@aquachain.com',
        Destination={'ToAddresses': recipients},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body}}
        }
    )
```

**Dashboard Access**:

Reports are automatically displayed in the Compliance Dashboard at `/admin/compliance/reports`.

**Secure File Transfer**:

For external auditors, use secure file transfer:

```bash
# Generate presigned URL (valid for 7 days)
aws s3 presign s3://aquachain-compliance-reports/monthly/2025-10/data-access-report.json \
  --expires-in 604800
```

---

## Troubleshooting

### Report Generation Failures

**Symptom**: Monthly reports not generated

**Diagnosis**:

```bash
# Check Lambda execution
aws logs tail /aws/lambda/compliance-report-generator --since 1h

# Check EventBridge rule
aws events describe-rule --name MonthlyComplianceReports

# Check Lambda permissions
aws lambda get-policy --function-name compliance-report-generator
```

**Common Causes**:
- Lambda timeout (increase timeout to 5 minutes)
- Insufficient IAM permissions
- DynamoDB throttling
- S3 bucket permissions

**Resolution**:
1. Review CloudWatch logs for errors
2. Fix identified issue
3. Manually trigger report generation
4. Verify report completeness

### Missing Data in Reports

**Symptom**: Reports show incomplete or missing data

**Diagnosis**:

```bash
# Check audit log count
aws dynamodb scan \
  --table-name AuditLogs \
  --select COUNT

# Check date range in report
aws s3 cp s3://aquachain-compliance-reports/monthly/2025-10/data-access-report.json - | jq '.date_range'
```

**Common Causes**:
- Audit logging not functioning
- Incorrect date range in query
- DynamoDB TTL deleted records prematurely
- Query pagination issues

**Resolution**:
1. Verify audit logging is working
2. Check S3 archives for missing data
3. Regenerate report with correct parameters
4. Update report generation logic if needed

### Report Access Issues

**Symptom**: Users cannot access reports

**Diagnosis**:

```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket aquachain-compliance-reports

# Check IAM user permissions
aws iam get-user-policy --user-name compliance-officer --policy-name ComplianceReportAccess
```

**Resolution**:
1. Verify user has correct IAM permissions
2. Check S3 bucket policy allows access
3. Generate new presigned URL if expired
4. Verify user is in correct IAM group

---

## Emergency Procedures

### Regulatory Inquiry

**Scenario**: Regulator requests compliance documentation

**Immediate Actions** (within 1 hour):
1. Notify legal team
2. Identify requested time period
3. Generate all relevant reports
4. Review reports for completeness
5. Prepare summary document

**Documentation to Provide**:
- Monthly compliance reports for requested period
- Audit trail for specific incidents
- Data retention policies
- Security controls documentation
- GDPR request logs
- Incident reports (if applicable)

**Process**:

```bash
# Generate comprehensive report package
./scripts/generate-regulatory-package.sh \
  --start-date 2025-01-01 \
  --end-date 2025-10-31 \
  --output regulatory-package-2025.zip
```

### Data Breach Notification

**Scenario**: Data breach requires compliance reporting

**Immediate Actions** (within 1 hour):
1. Activate incident response team
2. Generate incident investigation report
3. Identify affected users and data
4. Document timeline of events
5. Prepare breach notification

**Required Reports**:
- Incident investigation report
- Affected users list
- Data types compromised
- Audit trail of breach
- Remediation actions taken

**Notification Timeline**:
- Supervisory authority: Within 72 hours
- Affected users: Without undue delay
- Internal stakeholders: Immediately

### System Outage

**Scenario**: Compliance reporting system is unavailable

**Immediate Actions**:
1. Switch to manual reporting procedures
2. Document outage in incident log
3. Notify compliance team
4. Generate reports manually when system recovers
5. Verify no data loss occurred

**Manual Reporting**:

```bash
# Query audit logs directly from DynamoDB
aws dynamodb scan --table-name AuditLogs > audit-logs-backup.json

# Query GDPR requests
aws dynamodb scan --table-name GDPRRequests > gdpr-requests-backup.json

# Generate manual report from backups
python scripts/generate-manual-report.py \
  --audit-logs audit-logs-backup.json \
  --gdpr-requests gdpr-requests-backup.json \
  --output manual-report.json
```

---

## Appendix

### Report Schema Reference

**Data Access Report Schema**:

```json
{
  "report_date": "2025-10-31T23:59:59Z",
  "report_type": "data_access",
  "period": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-10-31T23:59:59Z"
  },
  "data": {
    "total_access_events": 15420,
    "access_by_role": {
      "admin": 234,
      "technician": 5678,
      "consumer": 9508
    },
    "access_by_data_type": {
      "user_profile": 1234,
      "device_data": 8765,
      "sensor_readings": 5421
    },
    "failed_access_attempts": 47,
    "unusual_patterns": []
  }
}
```

### Contact Information

**Compliance Team**:
- Email: compliance@aquachain.com
- Phone: [Phone Number]
- On-call: [On-call Number]

**Technical Support**:
- Email: support@aquachain.com
- Slack: #compliance-tech-support

**Escalation**:
- Level 1: Compliance Officer
- Level 2: Chief Information Security Officer
- Level 3: Chief Legal Officer
- Level 4: Chief Executive Officer

---

**Document Version**: 1.0  
**Last Updated**: Phase 4 Implementation  
**Owner**: Compliance Team  
**Review Cycle**: Quarterly  
**Next Review**: [Date]
