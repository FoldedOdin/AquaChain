# AWS Account Migration Guide

Complete guide for switching AquaChain to a different AWS account.

---

## 📋 Overview

This guide covers how to migrate AquaChain from one AWS account to another, or set up the project with new AWS credentials.

**Time Required:** 30-45 minutes  
**Difficulty:** Intermediate  
**Prerequisites:** AWS account with admin access

---

## 🎯 When to Use This Guide

- ✅ Switching to a different AWS account
- ✅ Setting up project for a new team member
- ✅ Moving from development to production account
- ✅ Rotating AWS credentials for security
- ✅ Setting up in a different AWS region

---

## 🔄 Migration Process

### Step 1: Configure AWS CLI

Update AWS CLI with new account credentials.

**Windows:**
```bash
aws configure
```

**You'll be prompted for:**
```
AWS Access Key ID [None]: AKIA****************
AWS Secret Access Key [None]: ****************************************
Default region name [None]: us-east-1
Default output format [None]: json
```

**Verify the configuration:**
```bash
# Check current AWS account
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AIDA****************",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

**Save your new Account ID** - you'll need it in the next steps!

---

### Step 2: Update Environment Files

Update AWS account information in environment files.

#### 2.1 Infrastructure Environment File

**File:** `infrastructure/.env`

```bash
# Update these values
AWS_ACCOUNT_ID=123456789012          # Your new account ID
AWS_REGION=us-east-1                 # Your preferred region
CDK_DEFAULT_ACCOUNT=123456789012     # Same as AWS_ACCOUNT_ID
CDK_DEFAULT_REGION=us-east-1         # Same as AWS_REGION

# Optional: Update environment name
ENVIRONMENT=dev
```

**How to get your Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

#### 2.2 CDK Environment File

**File:** `infrastructure/cdk/.env`

```bash
# Update these values
CDK_DEFAULT_ACCOUNT=123456789012
CDK_DEFAULT_REGION=us-east-1
ENVIRONMENT=dev
```

#### 2.3 IoT Simulator Environment File (Optional)

**File:** `iot-simulator/.env`

```bash
# AWS Configuration
AWS_REGION=us-east-1

# Optional: Explicit credentials (not recommended)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key

# IoT Endpoint (will be generated after deployment)
AWS_IOT_ENDPOINT=your-iot-endpoint.iot.us-east-1.amazonaws.com
```

**Note:** IoT endpoint will be generated after deployment. Leave blank for now.

---

### Step 3: Bootstrap CDK in New Account

CDK requires bootstrapping in each AWS account/region combination.

```bash
# Navigate to CDK directory
cd infrastructure/cdk

# Bootstrap CDK (replace with your account ID and region)
cdk bootstrap aws://123456789012/us-east-1

# Expected output:
# ⏳ Bootstrapping environment aws://123456789012/us-east-1...
# ✅ Environment aws://123456789012/us-east-1 bootstrapped
```

**What this does:**
- Creates CDKToolkit CloudFormation stack
- Creates S3 bucket for CDK assets
- Creates IAM roles for CDK deployments
- Sets up ECR repository for Docker images

**Verify bootstrap:**
```bash
aws cloudformation describe-stacks --stack-name CDKToolkit --query "Stacks[0].StackStatus"

# Expected output: "CREATE_COMPLETE"
```

---

### Step 4: Clean CDK Context

Remove old account information from CDK context.

```bash
# Still in infrastructure/cdk directory

# Windows
del cdk.context.json

# Linux/Mac
rm cdk.context.json
```

**Why this is important:**
- CDK caches account-specific information
- Old context can cause deployment failures
- Fresh context ensures clean deployment

---

### Step 5: Deploy Infrastructure

Deploy AquaChain infrastructure to the new account.

#### Option A: Minimal Deployment (Recommended)

**Cost:** ~₹1,600-2,800/month (~$20-35/month)

```bash
# Navigate to deployment scripts
cd scripts/deployment

# Run minimal deployment
deploy-minimal.bat

# Or on Linux/Mac
./deploy-minimal.sh
```

**Deploys 7 essential stacks:**
1. Security Stack (KMS, IAM)
2. Core Stack (Foundation)
3. Data Stack (DynamoDB, S3, IoT)
4. LambdaLayers Stack
5. Compute Stack (Lambda functions)
6. API Stack (API Gateway, Cognito)
7. IoTSecurity Stack

**Time:** 15-20 minutes

#### Option B: Full Deployment

**Cost:** ~₹12,000-16,000/month (~$150-200/month)

```bash
cd scripts/deployment
deploy-all.bat

# Or on Linux/Mac
./deploy-all.sh
```

**Deploys 22 stacks** including monitoring, backup, DR, CloudFront, etc.

**Time:** 30-45 minutes

---

### Step 6: Update Frontend Configuration

After deployment, update frontend with new AWS resource IDs.

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Automatically fetch and update AWS configuration
npm run get-aws-config
```

**What this does:**
- Fetches Cognito User Pool ID
- Fetches API Gateway URL
- Fetches IoT endpoint
- Updates frontend `.env` files automatically

**Verify the update:**
```bash
# Check frontend/.env.local
cat frontend/.env.local

# Should contain:
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=us-east-1_XXXXXXXXX
REACT_APP_USER_POOL_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
REACT_APP_API_URL=https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev
REACT_APP_IOT_ENDPOINT=XXXXXXXXXXXXXX.iot.us-east-1.amazonaws.com
```

---

### Step 7: Test the Migration

Verify everything works in the new account.

#### 7.1 Test AWS Resources

```bash
# Check deployed stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Check API Gateway
aws apigateway get-rest-apis --query "items[?name=='aquachain-api-dev'].id"

# Check Cognito User Pool
aws cognito-idp list-user-pools --max-results 10

# Check DynamoDB tables
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'aquachain-')]"

# Check Lambda functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aquachain-')]"
```

#### 7.2 Test Frontend Locally

```bash
cd frontend

# Start development server
npm start

# Access at http://localhost:3000
```

**Test these features:**
- ✅ User registration
- ✅ User login
- ✅ Dashboard loads
- ✅ API calls work
- ✅ No console errors

#### 7.3 Create Test User

```bash
# Get User Pool ID
aws cognito-idp list-user-pools --max-results 10 --query "UserPools[?Name=='aquachain-pool-users-dev'].Id" --output text

# Create test user (replace USER_POOL_ID)
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username test@example.com \
  --password MySecurePass123! \
  --permanent
```

---

## 📁 Files to Update - Quick Reference

### Must Update Manually:
```
infrastructure/.env                    # AWS_ACCOUNT_ID, AWS_REGION
infrastructure/cdk/.env                # CDK_DEFAULT_ACCOUNT, CDK_DEFAULT_REGION
```

### Auto-Generated After Deployment:
```
frontend/.env.local                    # Generated by npm run get-aws-config
frontend/.env.development              # Generated by npm run get-aws-config
frontend/.env.production               # Generated by npm run get-aws-config
iot-simulator/.env                     # IoT endpoint (manual or script)
```

### Must Delete:
```
infrastructure/cdk/cdk.context.json    # Delete before deployment
```

---

## 🔒 Security Best Practices

### 1. Credential Management

**DO:**
- ✅ Use AWS CLI profiles for multiple accounts
- ✅ Rotate credentials regularly (every 90 days)
- ✅ Use IAM roles in production
- ✅ Enable MFA on AWS account
- ✅ Use least-privilege IAM policies

**DON'T:**
- ❌ Commit `.env` files with real credentials
- ❌ Share AWS access keys via email/chat
- ❌ Use root account credentials
- ❌ Hardcode credentials in code
- ❌ Store credentials in git history

### 2. Multiple AWS Accounts

Use AWS CLI profiles for managing multiple accounts:

```bash
# Configure multiple profiles
aws configure --profile personal
aws configure --profile work
aws configure --profile production

# Use specific profile
aws --profile personal sts get-caller-identity
aws --profile work s3 ls

# Set default profile
set AWS_PROFILE=work           # Windows
export AWS_PROFILE=work        # Linux/Mac

# Verify current profile
aws sts get-caller-identity
```

### 3. Environment Variables

Set AWS credentials via environment variables (more secure):

```bash
# Windows
set AWS_ACCESS_KEY_ID=AKIA****************
set AWS_SECRET_ACCESS_KEY=****************************************
set AWS_DEFAULT_REGION=us-east-1

# Linux/Mac
export AWS_ACCESS_KEY_ID=AKIA****************
export AWS_SECRET_ACCESS_KEY=****************************************
export AWS_DEFAULT_REGION=us-east-1
```

---

## 🚨 Troubleshooting

### Issue 1: "Unable to resolve AWS account"

**Error:**
```
Unable to resolve AWS account to use. It must be either configured when you define your CDK Stack, or through the environment
```

**Solution:**
```bash
# Update infrastructure/.env with correct AWS_ACCOUNT_ID
# Then re-run deployment
cd scripts/deployment
deploy-minimal.bat
```

---

### Issue 2: "CDK bootstrap required"

**Error:**
```
This stack uses assets, so the toolkit stack must be deployed to the environment
```

**Solution:**
```bash
cd infrastructure/cdk
cdk bootstrap aws://YOUR-ACCOUNT-ID/YOUR-REGION
```

---

### Issue 3: "Access Denied" errors

**Error:**
```
User: arn:aws:iam::123456789012:user/username is not authorized to perform: cloudformation:CreateStack
```

**Solution:**
Ensure your IAM user has sufficient permissions:

**Required IAM Policies:**
- AdministratorAccess (for full deployment)
- Or custom policy with:
  - CloudFormation full access
  - IAM role creation
  - Lambda, API Gateway, DynamoDB, S3, Cognito, IoT access
  - KMS key management

**Check current permissions:**
```bash
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR-USERNAME
```

---

### Issue 4: "Stack already exists"

**Error:**
```
Stack [AquaChain-Core-dev] already exists
```

**Solution:**
```bash
# Delete existing stacks first
cd scripts/maintenance
delete-everything.bat

# Wait for deletion to complete (5-10 minutes)
aws cloudformation wait stack-delete-complete --stack-name AquaChain-Core-dev

# Then redeploy
cd ../deployment
deploy-minimal.bat
```

---

### Issue 5: "Region mismatch"

**Error:**
```
Stack is in region us-west-2 but CLI is configured for us-east-1
```

**Solution:**
```bash
# Update AWS CLI region
aws configure set region us-east-1

# Or use --region flag
aws cloudformation list-stacks --region us-east-1

# Update all .env files with consistent region
```

---

## 📊 Cost Estimation

### After Migration Costs

| Deployment Type | Monthly Cost (USD) | Monthly Cost (INR) |
|----------------|-------------------|-------------------|
| **Minimal (7 stacks)** | $20-35 | ₹1,600-2,800 |
| **Full (22 stacks)** | $150-200 | ₹12,000-16,000 |
| **Deleted (0 stacks)** | $0-1 | ₹0-80 |

**Cost Breakdown (Minimal):**
- Lambda (256MB): $2-5
- DynamoDB (on-demand): $10-15
- S3 Storage: $1-3
- API Gateway: $0-5
- Cognito: $0 (free tier)
- KMS: $3-5
- IoT Core: $0-3
- Other: $1-2

**Free Tier Eligible:**
- Lambda: 1M requests/month
- DynamoDB: 25GB storage
- S3: 5GB storage
- API Gateway: 1M requests/month
- Cognito: 50,000 MAUs

---

## ✅ Migration Checklist

Use this checklist to ensure complete migration:

### Pre-Migration
- [ ] Backup existing data (if migrating from old account)
- [ ] Document current AWS resources
- [ ] Export Cognito users (if needed)
- [ ] Export DynamoDB data (if needed)
- [ ] Note down custom configurations

### AWS Configuration
- [ ] Run `aws configure` with new credentials
- [ ] Verify with `aws sts get-caller-identity`
- [ ] Save new Account ID

### Environment Files
- [ ] Update `infrastructure/.env` (AWS_ACCOUNT_ID)
- [ ] Update `infrastructure/cdk/.env` (CDK_DEFAULT_ACCOUNT)
- [ ] Update `iot-simulator/.env` (AWS_REGION)

### CDK Setup
- [ ] Run `cdk bootstrap` in new account
- [ ] Delete `cdk.context.json`
- [ ] Verify CDKToolkit stack created

### Deployment
- [ ] Choose deployment type (minimal or full)
- [ ] Run deployment script
- [ ] Wait for completion (15-45 minutes)
- [ ] Verify all stacks deployed successfully

### Frontend Configuration
- [ ] Run `npm run get-aws-config`
- [ ] Verify `.env.local` updated
- [ ] Test frontend locally

### Testing
- [ ] Create test user in Cognito
- [ ] Test user login
- [ ] Test API endpoints
- [ ] Test IoT device connection (if applicable)
- [ ] Verify data persistence

### Post-Migration
- [ ] Set up AWS Budget alerts
- [ ] Configure CloudWatch alarms
- [ ] Update documentation
- [ ] Notify team members
- [ ] Delete old account resources (if applicable)

---

## 🔄 Rollback Plan

If migration fails, you can rollback:

### Option 1: Delete New Deployment
```bash
cd scripts/maintenance
delete-everything.bat
```

### Option 2: Revert AWS CLI Configuration
```bash
# Reconfigure with old credentials
aws configure

# Or switch to old profile
set AWS_PROFILE=old-account
```

### Option 3: Restore from Backup
```bash
# Restore DynamoDB tables
aws dynamodb restore-table-from-backup \
  --target-table-name aquachain-users-dev \
  --backup-arn arn:aws:dynamodb:region:account:table/aquachain-users-dev/backup/01234567890123-abcdefgh

# Restore S3 data
aws s3 sync s3://old-bucket s3://new-bucket
```

---

## 📞 Support

If you encounter issues during migration:

1. **Check AWS CloudFormation Console**
   - View stack events for error details
   - Check failed resource creation

2. **Review CloudWatch Logs**
   - Lambda function logs
   - API Gateway logs

3. **Verify IAM Permissions**
   - Ensure sufficient permissions
   - Check trust relationships

4. **Consult Documentation**
   - [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
   - [AWS CLI Documentation](https://docs.aws.amazon.com/cli/)
   - [PROJECT_REPORT.md](../PROJECT_REPORT.md)

---

## 📚 Related Documentation

- [Setup Guide](SETUP_GUIDE.md) - Initial project setup
- [Deployment Guide](../infrastructure/DEPLOYMENT_GUIDE.md) - Detailed deployment instructions
- [Cost Optimization Guide](cost-optimization/README.md) - Cost reduction strategies
- [Security Guide](../infrastructure/SECURITY_CREDENTIALS_GUIDE.md) - Security best practices
- [Troubleshooting Guide](QUICK_FIX_GUIDE.md) - Common issues and solutions

---

**Last Updated:** November 8, 2025  
**Version:** 1.0  
**Status:** ✅ Complete and Tested
