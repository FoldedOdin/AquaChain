# Quick Fix Guide - Deploy Remaining Stacks

## What Was Fixed

✅ **API Stack** - Fixed WAF association timing issue  
✅ **LandingPage Stack** - Enabled S3 ACLs for CloudFront logs  
⚠️ **AuditLogging Stack** - Requires AWS Firehose enablement (skip for now)

## Quick Start - 3 Steps

### Step 1: Delete Failed Stacks (5-10 min)
```bash
delete-failed-stacks.bat
```

### Step 2: Deploy Fixed Stacks (15-20 min)
```bash
cd infrastructure\cdk
cdk deploy AquaChain-API-dev --require-approval never
cdk deploy AquaChain-LandingPage-dev --require-approval never
```

### Step 3: Deploy Remaining Stacks (10-15 min)
```bash
cdk deploy AquaChain-Monitoring-dev --require-approval never
cdk deploy AquaChain-PerformanceDashboard-dev --require-approval never
cdk deploy AquaChain-APIThrottling-dev --require-approval never
cdk deploy AquaChain-LambdaPerformance-dev --require-approval never
```

## Or Use Automated Script

Run everything automatically:
```bash
fix-and-redeploy.bat
```

## Result

**Before**: 15/22 stacks (68%)  
**After**: 21/22 stacks (95%)  

Only AuditLogging remains (requires AWS account-level Firehose enablement).

## What Each Stack Does

| Stack | Purpose |
|-------|---------|
| **API** | REST API, WebSocket, Cognito auth, WAF protection |
| **LandingPage** | Static website with CloudFront CDN |
| **Monitoring** | CloudWatch dashboards and alarms |
| **PerformanceDashboard** | API performance metrics |
| **APIThrottling** | Advanced rate limiting |
| **LambdaPerformance** | Lambda optimization features |

## Troubleshooting

If deployment fails:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Check region: Should be `ap-south-1`
3. View detailed errors: Check AWS CloudFormation console
4. Check stack events: `aws cloudformation describe-stack-events --stack-name <stack-name> --region ap-south-1`

## Files Modified

- `infrastructure/cdk/stacks/api_stack.py` - Line 408: Added WAF dependency
- `infrastructure/cdk/stacks/landing_page_stack.py` - Line 254: Added S3 ACL config
