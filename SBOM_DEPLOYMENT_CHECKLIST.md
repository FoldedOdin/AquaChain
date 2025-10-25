# SBOM Deployment Checklist

## Pre-Deployment

### 1. Install Required Tools

- [ ] Install Syft
  ```bash
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
  syft version
  ```

- [ ] Install Grype
  ```bash
  curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
  grype version
  ```

- [ ] Verify Python 3.11+
  ```bash
  python --version
  ```

- [ ] Verify Node.js 18+
  ```bash
  node --version
  ```

### 2. Test Locally

- [ ] Generate SBOM locally
  ```bash
  python scripts/generate-sbom.py
  ```

- [ ] Verify output in `sbom-artifacts/`
  ```bash
  ls -la sbom-artifacts/
  ```

- [ ] Generate vulnerability reports
  ```bash
  python scripts/vulnerability-report-generator.py
  ```

- [ ] Test SBOM comparison
  ```bash
  # Generate two SBOMs at different times
  python scripts/generate-sbom.py
  # Make a change, then generate again
  python scripts/compare-sboms.py sbom-artifacts/sbom-complete-*.json
  ```

---

## Infrastructure Deployment

### 3. Deploy SBOM Storage Stack

- [ ] Navigate to CDK directory
  ```bash
  cd infrastructure/cdk
  ```

- [ ] Install CDK dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Synthesize stack
  ```bash
  cdk synth SBOMStorageStack
  ```

- [ ] Deploy stack
  ```bash
  cdk deploy SBOMStorageStack
  ```

- [ ] Verify stack deployment
  ```bash
  aws cloudformation describe-stacks --stack-name SBOMStorageStack
  ```

- [ ] Note the outputs:
  - [ ] SBOM Bucket Name
  - [ ] SBOM Topic ARN
  - [ ] CI/CD Policy ARN

### 4. Configure S3 Bucket

- [ ] Verify bucket exists
  ```bash
  aws s3 ls | grep aquachain-sbom
  ```

- [ ] Check versioning enabled
  ```bash
  aws s3api get-bucket-versioning --bucket aquachain-sbom-<account-id>
  ```

- [ ] Verify encryption
  ```bash
  aws s3api get-bucket-encryption --bucket aquachain-sbom-<account-id>
  ```

- [ ] Check lifecycle policies
  ```bash
  aws s3api get-bucket-lifecycle-configuration --bucket aquachain-sbom-<account-id>
  ```

---

## CI/CD Configuration

### 5. Configure GitHub Secrets

- [ ] Add `AWS_ACCESS_KEY_ID`
  - Go to GitHub repo → Settings → Secrets and variables → Actions
  - New repository secret
  - Name: `AWS_ACCESS_KEY_ID`
  - Value: Your AWS access key

- [ ] Add `AWS_SECRET_ACCESS_KEY`
  - Name: `AWS_SECRET_ACCESS_KEY`
  - Value: Your AWS secret key

- [ ] Add `AWS_ACCOUNT_ID`
  - Name: `AWS_ACCOUNT_ID`
  - Value: Your AWS account ID (12 digits)

- [ ] Verify secrets are set
  - Check in Settings → Secrets and variables → Actions

### 6. Test CI/CD Workflows

- [ ] Create test branch
  ```bash
  git checkout -b test-sbom-generation
  ```

- [ ] Make a small change
  ```bash
  echo "# Test" >> README.md
  git add README.md
  git commit -m "Test SBOM generation"
  ```

- [ ] Push to GitHub
  ```bash
  git push origin test-sbom-generation
  ```

- [ ] Create Pull Request

- [ ] Verify workflow runs
  - Go to Actions tab
  - Check "AquaChain CI/CD Pipeline" workflow
  - Verify "Generate SBOM" job runs successfully

- [ ] Check PR comment
  - Verify vulnerability summary comment appears on PR

- [ ] Download artifacts
  - Go to workflow run
  - Download "sbom-artifacts"
  - Verify contents

### 7. Test Weekly Workflow

- [ ] Manually trigger weekly workflow
  - Go to Actions tab
  - Select "Weekly SBOM Generation"
  - Click "Run workflow"
  - Select branch: main
  - Click "Run workflow"

- [ ] Verify workflow completes

- [ ] Check S3 upload
  ```bash
  aws s3 ls s3://aquachain-sbom-<account-id>/latest/
  aws s3 ls s3://aquachain-sbom-<account-id>/weekly/
  ```

---

## Notifications

### 8. Configure SNS Subscriptions

- [ ] Subscribe email to SNS topic
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:<account-id>:aquachain-sbom-notifications \
    --protocol email \
    --notification-endpoint security@aquachain.io
  ```

- [ ] Confirm subscription
  - Check email inbox
  - Click confirmation link

- [ ] Test notification
  ```bash
  aws sns publish \
    --topic-arn arn:aws:sns:us-east-1:<account-id>:aquachain-sbom-notifications \
    --subject "Test SBOM Notification" \
    --message "This is a test notification"
  ```

- [ ] Verify email received

### 9. Configure Slack Notifications (Optional)

- [ ] Create Slack webhook URL
  - Go to Slack → Apps → Incoming Webhooks
  - Create new webhook
  - Copy webhook URL

- [ ] Add to GitHub secrets
  - Name: `SLACK_WEBHOOK_URL`
  - Value: Your Slack webhook URL

- [ ] Update workflow to use Slack
  - Uncomment Slack notification steps in workflows

---

## Monitoring

### 10. Set Up CloudWatch Monitoring

- [ ] Create CloudWatch dashboard
  ```bash
  aws cloudwatch put-dashboard \
    --dashboard-name AquaChain-SBOM \
    --dashboard-body file://sbom-dashboard.json
  ```

- [ ] Set up alarms for Lambda function
  ```bash
  aws cloudwatch put-metric-alarm \
    --alarm-name sbom-comparison-errors \
    --alarm-description "Alert on SBOM comparison errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --dimensions Name=FunctionName,Value=aquachain-sbom-comparison
  ```

- [ ] Verify alarms
  ```bash
  aws cloudwatch describe-alarms --alarm-names sbom-comparison-errors
  ```

### 11. Configure Log Retention

- [ ] Set Lambda log retention
  ```bash
  aws logs put-retention-policy \
    --log-group-name /aws/lambda/aquachain-sbom-comparison \
    --retention-in-days 90
  ```

- [ ] Verify retention policy
  ```bash
  aws logs describe-log-groups \
    --log-group-name-prefix /aws/lambda/aquachain-sbom-comparison
  ```

---

## Validation

### 12. End-to-End Testing

- [ ] Generate SBOM manually
  ```bash
  python scripts/generate-sbom.py
  ```

- [ ] Upload to S3
  ```bash
  TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
  aws s3 sync sbom-artifacts/ s3://aquachain-sbom-<account-id>/${TIMESTAMP}/
  ```

- [ ] Verify Lambda triggered
  ```bash
  aws logs tail /aws/lambda/aquachain-sbom-comparison --follow
  ```

- [ ] Check comparison report created
  ```bash
  aws s3 ls s3://aquachain-sbom-<account-id>/${TIMESTAMP}/ | grep comparison
  ```

- [ ] Verify SNS notification sent (if changes detected)

### 13. Security Validation

- [ ] Verify bucket encryption
  ```bash
  aws s3api head-object \
    --bucket aquachain-sbom-<account-id> \
    --key latest/sbom-complete-*.json
  ```

- [ ] Check IAM permissions
  ```bash
  aws iam get-policy-version \
    --policy-arn arn:aws:iam::<account-id>:policy/AquaChain-SBOM-Upload-Policy \
    --version-id v1
  ```

- [ ] Verify public access blocked
  ```bash
  aws s3api get-public-access-block \
    --bucket aquachain-sbom-<account-id>
  ```

- [ ] Test unauthorized access (should fail)
  ```bash
  # Try to access without credentials
  curl https://aquachain-sbom-<account-id>.s3.amazonaws.com/latest/sbom-complete-*.json
  # Should return Access Denied
  ```

---

## Documentation

### 14. Update Documentation

- [ ] Review `DOCS/sbom-generation-guide.md`
- [ ] Update with actual bucket names and ARNs
- [ ] Add team-specific contact information
- [ ] Update troubleshooting section with any issues encountered

### 15. Team Training

- [ ] Schedule training session for team
- [ ] Walk through SBOM generation process
- [ ] Demonstrate vulnerability report interpretation
- [ ] Show how to access SBOMs from S3
- [ ] Explain CI/CD integration

---

## Post-Deployment

### 16. Monitor First Week

- [ ] Day 1: Check CI/CD runs on all pushes
- [ ] Day 2: Review vulnerability reports
- [ ] Day 3: Verify S3 storage and lifecycle
- [ ] Day 4: Check SNS notifications
- [ ] Day 5: Review CloudWatch metrics
- [ ] Day 6: Test SBOM comparison
- [ ] Day 7: Verify weekly workflow runs

### 17. Establish Processes

- [ ] Define vulnerability response process
  - Critical: Immediate response
  - High: Within 24 hours
  - Medium: Within 1 week
  - Low: Next sprint

- [ ] Assign SBOM review responsibilities
  - Weekly review: Security team
  - Monthly audit: Compliance team
  - Quarterly report: Management

- [ ] Create runbooks
  - [ ] How to respond to critical vulnerabilities
  - [ ] How to investigate SBOM changes
  - [ ] How to manually generate SBOMs
  - [ ] How to troubleshoot failures

---

## Rollback Plan

### 18. Prepare Rollback Procedure

- [ ] Document current state
  ```bash
  aws cloudformation describe-stacks --stack-name SBOMStorageStack > sbom-stack-backup.json
  ```

- [ ] Backup current workflows
  ```bash
  cp .github/workflows/ci-cd-pipeline.yml .github/workflows/ci-cd-pipeline.yml.backup
  cp .github/workflows/sbom-weekly.yml .github/workflows/sbom-weekly.yml.backup
  ```

- [ ] Test rollback procedure
  - [ ] Disable workflows
  - [ ] Delete stack (in test environment)
  - [ ] Restore from backup
  - [ ] Verify functionality

---

## Sign-Off

### 19. Stakeholder Approval

- [ ] Security team approval
  - [ ] Reviewed vulnerability scanning
  - [ ] Approved encryption and access controls
  - [ ] Verified compliance requirements

- [ ] DevOps team approval
  - [ ] Tested CI/CD integration
  - [ ] Verified monitoring and alerts
  - [ ] Approved operational procedures

- [ ] Compliance team approval
  - [ ] Verified EO 14028 compliance
  - [ ] Confirmed NTIA minimum elements
  - [ ] Approved audit trail

- [ ] Management approval
  - [ ] Reviewed implementation summary
  - [ ] Approved budget and resources
  - [ ] Signed off on deployment

---

## Completion

### 20. Final Steps

- [ ] Mark task as complete in project tracker
- [ ] Update project documentation
- [ ] Announce deployment to team
- [ ] Schedule post-deployment review (1 month)
- [ ] Archive deployment artifacts

---

## Success Criteria

All items must be checked before considering deployment complete:

- [ ] All infrastructure deployed successfully
- [ ] CI/CD workflows running without errors
- [ ] SBOMs being generated and uploaded to S3
- [ ] Vulnerability scanning operational
- [ ] Notifications configured and tested
- [ ] Monitoring and alerting in place
- [ ] Documentation complete and reviewed
- [ ] Team trained on new processes
- [ ] Stakeholder sign-off obtained

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Reviewed By:** _________________

**Approved By:** _________________

---

## Notes

Use this section to document any issues, deviations, or special considerations during deployment:

```
[Add notes here]
```

---

**Status:** Ready for Deployment  
**Version:** 1.0  
**Last Updated:** October 25, 2025
