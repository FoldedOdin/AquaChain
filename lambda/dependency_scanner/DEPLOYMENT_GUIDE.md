# Dependency Scanner - Quick Deployment Guide

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.11+ installed
- Access to AquaChain AWS account

## Step 1: Deploy Infrastructure

```bash
cd infrastructure/cdk

# Bootstrap CDK (if not already done)
cdk bootstrap

# Deploy the dependency scanner stack
cdk deploy DependencyScannerStack

# Confirm deployment when prompted
```

**Expected Output:**
```
✅  DependencyScannerStack

Outputs:
DependencyScannerStack.ResultsBucketName = aquachain-dependency-scans-123456789012
DependencyScannerStack.SourceBucketName = aquachain-source-snapshots-123456789012
DependencyScannerStack.AlertTopicArn = arn:aws:sns:us-east-1:123456789012:aquachain-dependency-alerts
DependencyScannerStack.ScannerFunctionName = aquachain-dependency-scanner
```

## Step 2: Configure SNS Email Alerts

```bash
# Subscribe your email to alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:REGION:ACCOUNT:aquachain-dependency-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm subscription via email
```

## Step 3: Upload Source Code Snapshots

```bash
# Get the source bucket name from CDK output
SOURCE_BUCKET="aquachain-source-snapshots-YOUR-ACCOUNT-ID"

# Upload frontend dependencies
aws s3 cp frontend/package.json s3://${SOURCE_BUCKET}/frontend/
aws s3 cp frontend/package-lock.json s3://${SOURCE_BUCKET}/frontend/

# Upload backend dependencies
aws s3 cp infrastructure/requirements.txt s3://${SOURCE_BUCKET}/infrastructure/
aws s3 cp lambda/ml_inference/requirements.txt s3://${SOURCE_BUCKET}/lambda/ml_inference/
aws s3 cp lambda/ml_training/requirements.txt s3://${SOURCE_BUCKET}/lambda/ml_training/
# ... upload other Lambda requirements.txt files as needed
```

## Step 4: Test the Scanner

Create a test event file `test-event.json`:

```json
{
  "scan_type": "all",
  "source_paths": {
    "npm": "s3://aquachain-source-snapshots-YOUR-ACCOUNT-ID/frontend/package.json",
    "python": [
      "s3://aquachain-source-snapshots-YOUR-ACCOUNT-ID/infrastructure/requirements.txt",
      "s3://aquachain-source-snapshots-YOUR-ACCOUNT-ID/lambda/ml_inference/requirements.txt"
    ]
  }
}
```

Invoke the Lambda function:

```bash
aws lambda invoke \
  --function-name aquachain-dependency-scanner \
  --payload file://test-event.json \
  response.json

# Check the response
cat response.json
```

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Dependency scan completed successfully\", \"summary\": {...}, \"action_required\": false}"
}
```

## Step 5: Verify Results

### Check S3 for Reports

```bash
# List scan reports
aws s3 ls s3://aquachain-dependency-scans-YOUR-ACCOUNT-ID/dependency-scans/

# Download latest report
aws s3 cp s3://aquachain-dependency-scans-YOUR-ACCOUNT-ID/dependency-scans/latest.json ./latest-report.json

# View report
cat latest-report.json | jq .
```

### Check CloudWatch Metrics

```bash
# Get vulnerability metrics
aws cloudwatch get-metric-statistics \
  --namespace AquaChain/Security \
  --metric-name Vulnerabilities_Total \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Maximum
```

### View CloudWatch Dashboard

Navigate to:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=AquaChain-Dependency-Security
```

## Step 6: Verify Weekly Schedule

```bash
# Check EventBridge rule
aws events describe-rule --name aquachain-weekly-dependency-scan

# List targets
aws events list-targets-by-rule --rule aquachain-weekly-dependency-scan
```

**Expected Output:**
```json
{
  "Name": "aquachain-weekly-dependency-scan",
  "Arn": "arn:aws:events:...",
  "ScheduleExpression": "cron(0 2 ? * MON *)",
  "State": "ENABLED",
  "Description": "Trigger dependency scan every week"
}
```

## Step 7: Monitor Logs

```bash
# Tail Lambda logs
aws logs tail /aws/lambda/aquachain-dependency-scanner --follow

# Or view in CloudWatch Console
# https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Faquachain-dependency-scanner
```

## Troubleshooting

### Issue: Lambda timeout

**Solution:** Increase timeout in CDK stack:
```python
timeout=Duration.minutes(15)  # Increase if needed
```

### Issue: npm audit fails

**Solution:** Ensure package-lock.json is uploaded:
```bash
aws s3 cp frontend/package-lock.json s3://${SOURCE_BUCKET}/frontend/
```

### Issue: No alerts received

**Solution:** Check SNS subscription:
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:REGION:ACCOUNT:aquachain-dependency-alerts
```

### Issue: Permission denied

**Solution:** Check Lambda IAM role has required permissions:
```bash
aws iam get-role-policy \
  --role-name DependencyScannerStack-ScannerFunctionRole... \
  --policy-name ...
```

## Rollback

If you need to remove the deployment:

```bash
cd infrastructure/cdk
cdk destroy DependencyScannerStack
```

**Warning:** This will delete:
- Lambda function
- S3 buckets (if empty)
- SNS topic
- EventBridge rule
- CloudWatch dashboard
- CloudWatch alarms

## Next Steps

1. ✅ Monitor first weekly scan (Monday 2 AM UTC)
2. ✅ Review scan reports and address vulnerabilities
3. ✅ Adjust alert thresholds if needed
4. ✅ Add additional email subscribers to SNS topic
5. ✅ Integrate with CI/CD pipeline

## Support

For issues or questions:
- Check [README.md](./README.md) for detailed documentation
- Review [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) for technical details
- Contact DevOps team

---

**Deployment Status:** Ready for Production  
**Estimated Deployment Time:** 10-15 minutes  
**Required Permissions:** Administrator or equivalent
