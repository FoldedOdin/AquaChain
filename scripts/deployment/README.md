# Deployment Scripts

Automation scripts for deploying AquaChain infrastructure to AWS.

## Quick Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy-all.bat` | Deploy all stacks (Windows) | `deploy-all.bat` |
| `deploy-all.ps1` | Deploy all stacks (PowerShell) | `deploy-all.ps1 -Environment dev` |
| `deploy-all.sh` | Deploy all stacks (Linux/Mac) | `./deploy-all.sh dev` |
| `destroy-all-stacks.bat` | Destroy all stacks (Windows) | `destroy-all-stacks.bat` |
| `destroy-all-stacks.sh` | Destroy all stacks (Linux/Mac) | `./destroy-all-stacks.sh` |
| `rollback.py` | Rollback deployment | `python rollback.py --stack StackName` |

## Deployment Workflow

### 1. Development Environment

```bash
# Build Lambda packages
python scripts/core/build-lambda-packages.py

# Deploy to dev
scripts\deployment\deploy-all.bat

# Verify deployment
python scripts/testing/production_readiness_validation.py --environment dev
```

### 2. Staging Environment

```bash
# Deploy to staging
scripts\deployment\deploy-all.ps1 -Environment staging

# Run comprehensive tests
scripts\testing\run-comprehensive-test.bat staging

# Verify all endpoints
python scripts/testing/production_readiness_validation.py --environment staging
```

### 3. Production Environment

```bash
# Deploy to production (requires approval)
scripts\deployment\deploy-all.ps1 -Environment prod

# Monitor deployment
# Check CloudWatch dashboards
# Review X-Ray traces

# Verify critical paths
python scripts/testing/production_readiness_validation.py --environment prod
```

## Script Details

### deploy-all.bat / deploy-all.ps1 / deploy-all.sh

Deploys all CDK stacks to AWS.

**What it does:**
1. Validates AWS credentials
2. Synthesizes CDK stacks
3. Deploys infrastructure in correct order
4. Outputs API endpoints and resource ARNs

**Options:**
```bash
# PowerShell
.\deploy-all.ps1 -Environment dev
.\deploy-all.ps1 -Environment staging
.\deploy-all.ps1 -Environment prod

# Bash
./deploy-all.sh dev
./deploy-all.sh staging
./deploy-all.sh prod
```

**Duration:** 10-15 minutes for full deployment

**Prerequisites:**
- AWS CLI configured
- CDK bootstrapped in target account/region
- Appropriate IAM permissions

### destroy-all-stacks.bat / destroy-all-stacks.sh

Destroys all CDK stacks (use with caution!).

**What it does:**
1. Lists all AquaChain stacks
2. Confirms destruction
3. Deletes stacks in reverse dependency order
4. Cleans up resources

**Usage:**
```bash
# Windows
scripts\deployment\destroy-all-stacks.bat

# Linux/Mac
./scripts/deployment/destroy-all-stacks.sh
```

**⚠️ WARNING:** This is destructive and irreversible!
- All data will be lost
- DynamoDB tables will be deleted
- S3 buckets will be emptied and deleted
- Lambda functions will be removed

**Safety:**
- Requires manual confirmation
- Only use in dev/staging environments
- Never run in production without backup

### rollback.py

Rolls back a specific stack to previous version.

**Usage:**
```bash
# Rollback specific stack
python scripts/deployment/rollback.py --stack AquaChain-API-dev

# Rollback to specific version
python scripts/deployment/rollback.py --stack AquaChain-API-dev --version 2

# Dry run (preview changes)
python scripts/deployment/rollback.py --stack AquaChain-API-dev --dry-run
```

**When to use:**
- Deployment introduced bugs
- Performance degradation detected
- Security issue discovered
- Need to revert to known-good state

**How it works:**
1. Retrieves previous stack template from CloudFormation
2. Validates rollback is safe
3. Updates stack with previous template
4. Monitors rollback progress
5. Verifies rollback success

## Deployment Checklist

### Pre-Deployment
- [ ] Code reviewed and approved
- [ ] Tests passing (unit, integration, E2E)
- [ ] Security scan passed
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] On-call engineer notified

### During Deployment
- [ ] Monitor CloudWatch logs
- [ ] Check X-Ray traces
- [ ] Verify API endpoints responding
- [ ] Test critical user flows
- [ ] Monitor error rates

### Post-Deployment
- [ ] Run smoke tests
- [ ] Verify all features working
- [ ] Check performance metrics
- [ ] Review CloudWatch alarms
- [ ] Update deployment log

## Troubleshooting

### Deployment Fails

**Issue: CDK bootstrap not found**
```bash
# Solution: Bootstrap CDK
cdk bootstrap aws://ACCOUNT-ID/REGION
```

**Issue: Insufficient permissions**
```bash
# Solution: Check IAM permissions
aws sts get-caller-identity
# Ensure user has CloudFormation, Lambda, DynamoDB, etc. permissions
```

**Issue: Stack already exists**
```bash
# Solution: Update existing stack or destroy first
cdk deploy --force
# Or
cdk destroy StackName
```

### Rollback Fails

**Issue: Stack in UPDATE_ROLLBACK_FAILED state**
```bash
# Solution: Continue rollback
aws cloudformation continue-update-rollback --stack-name StackName
```

**Issue: Resource deletion failed**
```bash
# Solution: Manually delete resource, then retry
# Check CloudFormation console for details
```

## Best Practices

1. **Always deploy to dev first** - Test changes before staging/prod
2. **Use blue-green deployments** - For zero-downtime updates
3. **Monitor during deployment** - Watch CloudWatch and X-Ray
4. **Have rollback plan** - Know how to revert quickly
5. **Tag all resources** - Use consistent tagging strategy
6. **Document changes** - Update deployment log
7. **Test rollback** - Verify rollback works before production

## Deployment Strategies

### Blue-Green Deployment
1. Deploy new version (green) alongside current (blue)
2. Run smoke tests on green
3. Switch traffic to green
4. Monitor for issues
5. Keep blue for quick rollback

### Canary Deployment
1. Deploy to 10% of traffic
2. Monitor for 1 hour
3. Increase to 50% if stable
4. Monitor for 1 hour
5. Increase to 100% if stable

### Rolling Deployment
1. Deploy to one Lambda function at a time
2. Verify each function works
3. Continue to next function
4. Rollback if any function fails

## Emergency Procedures

### Critical Bug in Production

1. **Immediate rollback**
   ```bash
   python scripts/deployment/rollback.py --stack AquaChain-API-prod
   ```

2. **Verify rollback success**
   ```bash
   python scripts/testing/production_readiness_validation.py --environment prod
   ```

3. **Notify stakeholders**
   - Post in Slack #incidents channel
   - Update status page
   - Notify on-call engineer

4. **Root cause analysis**
   - Review CloudWatch logs
   - Check X-Ray traces
   - Identify what changed

5. **Fix and redeploy**
   - Fix bug in dev
   - Test thoroughly
   - Deploy to staging
   - Deploy to production with monitoring

## Support

For deployment issues:
- Check CloudFormation console for stack events
- Review CloudWatch logs for errors
- Check X-Ray for distributed tracing
- Contact DevOps team for assistance
