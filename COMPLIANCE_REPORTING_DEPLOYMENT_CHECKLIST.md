# Compliance Reporting Deployment Checklist

## Pre-Deployment

### 1. Environment Configuration

- [ ] Set `COMPLIANCE_REPORTS_BUCKET` environment variable
- [ ] Set `AUDIT_LOGS_TABLE` environment variable
- [ ] Set `GDPR_REQUESTS_TABLE` environment variable
- [ ] Set `DEVICES_TABLE` environment variable
- [ ] Set `USERS_TABLE` environment variable
- [ ] Configure compliance team email address in CDK config
- [ ] Verify KMS key exists and is accessible

### 2. Dependencies

- [ ] Verify DynamoDB tables exist:
  - AuditLogs
  - GDPRRequests
  - Devices
  - Users
- [ ] Verify audit logging is operational
- [ ] Verify GDPR service is operational
- [ ] Ensure boto3 is available in Lambda runtime

### 3. Code Review

- [ ] Review `report_generator.py` for correctness
- [ ] Review `violation_detector.py` rules
- [ ] Review `scheduled_report_handler.py` logic
- [ ] Review `api_handler.py` endpoints
- [ ] Review `compliance_reporting_stack.py` infrastructure
- [ ] Review frontend `ComplianceDashboard.tsx`
- [ ] Review frontend `complianceService.ts`

## Deployment Steps

### 1. Deploy Infrastructure

```bash
cd infrastructure/cdk
cdk synth ComplianceReportingStack
cdk deploy ComplianceReportingStack
```

Expected outputs:
- S3 bucket name
- Lambda function ARN
- SNS topic ARN
- EventBridge rule name
- CloudWatch alarm names

### 2. Verify Infrastructure

- [ ] S3 bucket created with encryption
- [ ] Lambda function deployed successfully
- [ ] EventBridge rule is enabled
- [ ] SNS topic created
- [ ] CloudWatch alarms created
- [ ] IAM roles and policies created

### 3. Configure SNS Subscriptions

- [ ] Check compliance team email for subscription confirmation
- [ ] Click confirmation link in email
- [ ] Verify subscription status in AWS Console
- [ ] Test SNS topic with manual message

### 4. Test Lambda Function

```bash
# Invoke Lambda manually
aws lambda invoke \
  --function-name compliance-report-generator \
  --payload '{"year": 2025, "month": 10}' \
  response.json

# Check response
cat response.json
```

- [ ] Lambda executes without errors
- [ ] Report is generated in S3
- [ ] CloudWatch logs show successful execution

### 5. Verify S3 Report Storage

```bash
# List reports in S3
aws s3 ls s3://compliance-reports-bucket/compliance-reports/ --recursive

# Download a report
aws s3 cp s3://compliance-reports-bucket/compliance-reports/2025/10/report.json ./
```

- [ ] Report file exists in S3
- [ ] Report is encrypted
- [ ] Report contains all expected sections
- [ ] JSON is valid and parseable

### 6. Test Violation Detection

- [ ] Create test data with violations
- [ ] Generate report manually
- [ ] Verify violations are detected
- [ ] Verify SNS alert is sent
- [ ] Verify CloudWatch alarm triggers
- [ ] Verify CloudWatch metrics are published

### 7. Deploy Frontend

```bash
cd frontend
npm run build
# Deploy to your hosting service
```

- [ ] Frontend builds successfully
- [ ] ComplianceDashboard route is accessible
- [ ] Dashboard loads without errors
- [ ] Reports are displayed correctly

### 8. Test API Endpoints

```bash
# Test list reports
curl https://api.aquachain.com/compliance/reports \
  -H "Authorization: Bearer $TOKEN"

# Test get specific report
curl https://api.aquachain.com/compliance/reports/2025/10 \
  -H "Authorization: Bearer $TOKEN"

# Test generate report
curl -X POST https://api.aquachain.com/compliance/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"year": 2025, "month": 10}'

# Test metrics summary
curl https://api.aquachain.com/compliance/metrics/summary \
  -H "Authorization: Bearer $TOKEN"
```

- [ ] All endpoints return 200 OK
- [ ] Response data is correct
- [ ] CORS headers are present
- [ ] Authentication is enforced

## Post-Deployment

### 1. Monitoring Setup

- [ ] Configure CloudWatch dashboard for compliance metrics
- [ ] Set up log retention policies
- [ ] Configure CloudWatch Insights queries
- [ ] Set up custom metrics and alarms

### 2. Documentation

- [ ] Update team documentation with new endpoints
- [ ] Document compliance dashboard usage
- [ ] Create runbook for violation response
- [ ] Document deployment procedures

### 3. Training

- [ ] Train compliance team on dashboard usage
- [ ] Train DevOps team on troubleshooting
- [ ] Train administrators on manual report generation
- [ ] Document escalation procedures

### 4. Validation

- [ ] Wait for first scheduled report (1st of next month)
- [ ] Verify report is generated automatically
- [ ] Verify email notification is received
- [ ] Review report for accuracy

### 5. Security Review

- [ ] Verify S3 bucket is not publicly accessible
- [ ] Verify IAM roles follow least privilege
- [ ] Verify encryption is enabled everywhere
- [ ] Verify audit logging is comprehensive
- [ ] Review access logs

## Rollback Plan

If issues occur:

### 1. Disable Scheduled Reports

```bash
aws events disable-rule --name compliance-monthly-report
```

### 2. Revert Infrastructure

```bash
cd infrastructure/cdk
cdk destroy ComplianceReportingStack
```

### 3. Restore Previous State

- [ ] Remove Lambda function
- [ ] Delete S3 bucket (if safe)
- [ ] Remove SNS topic
- [ ] Remove CloudWatch alarms
- [ ] Remove EventBridge rule

## Troubleshooting

### Lambda Execution Failures

1. Check CloudWatch logs
2. Verify environment variables
3. Check IAM permissions
4. Verify DynamoDB table access
5. Check S3 bucket permissions

### Reports Not Generating

1. Check EventBridge rule is enabled
2. Verify Lambda function exists
3. Check Lambda execution role
4. Review CloudWatch logs for errors
5. Test manual invocation

### Alerts Not Sending

1. Verify SNS subscription is confirmed
2. Check SNS topic permissions
3. Test SNS with manual message
4. Review CloudWatch alarm configuration
5. Check Lambda SNS publish permissions

### Dashboard Not Loading

1. Check API endpoints are accessible
2. Verify CORS configuration
3. Check authentication tokens
4. Review browser console for errors
5. Verify S3 bucket has reports

## Success Criteria

- ✅ Infrastructure deployed successfully
- ✅ Lambda function executes without errors
- ✅ Reports are generated and stored in S3
- ✅ Violations are detected correctly
- ✅ Alerts are sent when violations occur
- ✅ Dashboard displays reports correctly
- ✅ API endpoints are functional
- ✅ Scheduled execution works
- ✅ Security controls are in place
- ✅ Documentation is complete

## Sign-Off

- [ ] DevOps Team Lead: _______________
- [ ] Compliance Officer: _______________
- [ ] Security Team: _______________
- [ ] Product Owner: _______________

Date: _______________

## Notes

Add any deployment notes, issues encountered, or special configurations here:

---

---

---
