# 🚀 AquaChain Project Setup Guide

**Get the AquaChain project up and running in 30 minutes**

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Node.js 18+** - [Download](https://nodejs.org)
- ✅ **Python 3.11+** - [Download](https://python.org)
- ✅ **AWS CLI** - [Install Guide](https://aws.amazon.com/cli/)
- ✅ **AWS Account** with admin access
- ✅ **Git** installed

---

## Quick Start (3 Options)

### Option 1: Full Stack Deployment (Recommended)
```bash
# 1. Install all dependencies
npm install
cd frontend && npm install && cd ..
pip install -r requirements-dev.txt

# 2. Configure AWS credentials
aws configure

# 3. Deploy everything
./deploy-all.sh
```

### Option 2: Frontend Only (Development)
```bash
# 1. Install frontend dependencies
cd frontend
npm install

# 2. Configure environment
cp .env.example .env.development
# Edit .env.development with your settings

# 3. Start development server
npm start
```

### Option 3: Infrastructure Only
```bash
# 1. Install CDK dependencies
cd infrastructure/cdk
pip install -r requirements.txt

# 2. Bootstrap CDK (first time only)
cdk bootstrap

# 3. Deploy infrastructure
cdk deploy --all
```

---

## Detailed Setup Steps

### Step 1: Clone and Install Dependencies

```bash
# Clone repository (if not already done)
git clone <repository-url>
cd AquaChain-Final

# Install root dependencies
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install Python dependencies
pip install -r requirements-dev.txt
pip install boto3 aws-cdk-lib constructs
```

### Step 2: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)

# Verify configuration
aws sts get-caller-identity
```

### Step 3: Set Up Environment Variables

**Frontend (.env.development):**
```bash
cd frontend
cp .env.example .env.development
```

Edit `frontend/.env.development`:
```env
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=<your-cognito-user-pool-id>
REACT_APP_USER_POOL_CLIENT_ID=<your-cognito-client-id>
REACT_APP_API_ENDPOINT=<your-api-gateway-url>
REACT_APP_WEBSOCKET_ENDPOINT=<your-websocket-url>
REACT_APP_IOT_ENDPOINT=<your-iot-endpoint>
```

**Infrastructure (.env):**
```bash
cd infrastructure
cp .env.example .env
```

Edit `infrastructure/.env`:
```env
AWS_REGION=us-east-1
ENVIRONMENT=dev
PROJECT_NAME=aquachain
```


### Step 4: Deploy Infrastructure

**Option A: Deploy Everything (Recommended)**
```bash
# From project root
./deploy-all.sh
```

**Option B: Deploy with CDK**
```bash
cd infrastructure/cdk

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Deploy all stacks
cdk deploy --all

# Or deploy specific stacks
cdk deploy AquaChainSecurityStack
cdk deploy AquaChainDataStack
cdk deploy AquaChainComputeStack
cdk deploy AquaChainAPIStack
```

**Option C: Deploy Specific Components**
```bash
cd infrastructure/cdk

# Deploy Phase 2 features only
cdk deploy AquaChain-IoTSecurity-dev
cdk deploy AquaChain-MLRegistry-dev
cdk deploy AquaChain-APIThrottling-dev
cdk deploy AquaChain-CloudFront-dev
```

### Step 5: Get Deployment Outputs

After deployment, get the outputs:
```bash
# Get Cognito User Pool ID
aws cognito-idp list-user-pools --max-results 10

# Get API Gateway URL
aws apigateway get-rest-apis

# Get IoT Endpoint
aws iot describe-endpoint --endpoint-type iot:Data-ATS
```

Update your frontend `.env.development` with these values.

### Step 6: Start Frontend Development Server

```bash
cd frontend

# Start development server
npm start

# Application will open at http://localhost:3000
```

### Step 7: Create Test User

```bash
# Create a test user in Cognito
aws cognito-idp admin-create-user \
  --user-pool-id <your-user-pool-id> \
  --username testuser@example.com \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password TempPass123!

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id <your-user-pool-id> \
  --username testuser@example.com \
  --password YourPassword123! \
  --permanent
```

---

## Component-Specific Setup

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Run linting
npm run lint
```

### Backend/Lambda Development

```bash
cd lambda

# Install dependencies for a specific function
cd data_processing
pip install -r requirements.txt

# Run tests
pytest

# Package for deployment
zip -r function.zip .
```

### IoT Simulator

```bash
cd iot-simulator

# Install dependencies
pip install -r requirements.txt

# Provision a device
python provision-device-multi-user.py provision \
  --device-id AquaChain-Device-001 \
  --user-id <cognito-user-sub> \
  --region us-east-1

# Run simulator
python simulator.py
```

---

## Verification Steps

### 1. Check Infrastructure Deployment

```bash
# Check CDK stacks
cd infrastructure/cdk
cdk list

# Check deployed stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE

# Run validation script
python infrastructure/check-deployment.py
```

### 2. Test API Endpoints

```bash
# Get API Gateway URL
API_URL=$(aws apigateway get-rest-apis --query 'items[?name==`AquaChain-API`].id' --output text)
echo "https://${API_URL}.execute-api.us-east-1.amazonaws.com/prod"

# Test health endpoint
curl https://${API_URL}.execute-api.us-east-1.amazonaws.com/prod/health
```

### 3. Test Frontend

```bash
cd frontend

# Run all tests
npm test

# Run specific test suites
npm run test:a11y
npm run test:security
npm run test:performance
```

### 4. Test IoT Connection

```bash
cd iot-simulator

# Test device connection
python test_device_connection.py --device-id AquaChain-Device-001
```

---

## Common Issues & Solutions

### Issue 1: CDK Bootstrap Failed

**Error:** "Need to perform AWS calls for account..."

**Solution:**
```bash
# Bootstrap with explicit account and region
cdk bootstrap aws://123456789012/us-east-1
```

### Issue 2: Frontend Can't Connect to API

**Error:** "Network Error" or CORS issues

**Solution:**
1. Check API Gateway URL in `.env.development`
2. Verify CORS is enabled in API Gateway
3. Check Cognito configuration

```bash
# Get correct API URL
aws apigateway get-rest-apis --query 'items[?name==`AquaChain-API`].[id,name]' --output table
```

### Issue 3: Authentication Fails

**Error:** "User does not exist" or "Incorrect username or password"

**Solution:**
```bash
# Verify user exists
aws cognito-idp admin-get-user \
  --user-pool-id <pool-id> \
  --username testuser@example.com

# Reset password if needed
aws cognito-idp admin-set-user-password \
  --user-pool-id <pool-id> \
  --username testuser@example.com \
  --password NewPassword123! \
  --permanent
```

### Issue 4: Lambda Function Errors

**Error:** "Function not found" or timeout

**Solution:**
```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `AquaChain`)].[FunctionName,Runtime]' --output table

# Check function logs
aws logs tail /aws/lambda/AquaChain-DataProcessing --follow

# Update function code
cd lambda/data_processing
zip -r function.zip .
aws lambda update-function-code \
  --function-name AquaChain-DataProcessing \
  --zip-file fileb://function.zip
```

### Issue 5: IoT Device Can't Connect

**Error:** "Connection refused" or certificate errors

**Solution:**
```bash
# Check IoT endpoint
aws iot describe-endpoint --endpoint-type iot:Data-ATS

# Verify device certificate
aws iot list-certificates

# Check device policy
aws iot get-policy --policy-name AquaChain-Device-Policy
```

---

## Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull origin main

# 2. Install any new dependencies
npm install
cd frontend && npm install && cd ..
pip install -r requirements-dev.txt

# 3. Start development servers
# Terminal 1: Frontend
cd frontend && npm start

# Terminal 2: Backend (if testing locally)
cd lambda/data_processing && python -m pytest --watch

# Terminal 3: IoT Simulator (if needed)
cd iot-simulator && python simulator.py
```

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes

# 3. Run tests
npm test
pytest

# 4. Commit changes
git add .
git commit -m "Description of changes"

# 5. Push and create PR
git push origin feature/your-feature-name
```

### Deploying Changes

```bash
# Deploy infrastructure changes
cd infrastructure/cdk
cdk deploy --all

# Deploy Lambda changes
cd lambda/your-function
./deploy.sh

# Deploy frontend changes
cd frontend
npm run build
# Deploy to S3/CloudFront
```

---

## Testing

### Run All Tests

```bash
# Frontend tests
cd frontend
npm test

# Backend tests
pytest

# Integration tests
python tests/integration/test_data_pipeline.py

# End-to-end tests
npm run test:e2e
```

### Specific Test Suites

```bash
# Frontend
npm run test:a11y          # Accessibility tests
npm run test:security      # Security tests
npm run test:performance   # Performance tests

# Backend
pytest tests/unit/         # Unit tests
pytest tests/integration/  # Integration tests
pytest tests/security/     # Security tests
```

---

## Monitoring & Debugging

### View Logs

```bash
# CloudWatch Logs
aws logs tail /aws/lambda/AquaChain-DataProcessing --follow

# API Gateway logs
aws logs tail /aws/apigateway/AquaChain-API --follow

# Frontend logs (browser console)
# Open browser DevTools (F12)
```

### Check Metrics

```bash
# Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=AquaChain-DataProcessing \
  --start-time 2025-10-27T00:00:00Z \
  --end-time 2025-10-27T23:59:59Z \
  --period 3600 \
  --statistics Sum

# API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=AquaChain-API \
  --start-time 2025-10-27T00:00:00Z \
  --end-time 2025-10-27T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Rollback plan ready

### Deploy to Production

```bash
# 1. Set environment to production
export ENVIRONMENT=production

# 2. Deploy infrastructure
cd infrastructure/cdk
cdk deploy --all --require-approval never

# 3. Deploy frontend
cd frontend
npm run build
aws s3 sync build/ s3://aquachain-frontend-production/

# 4. Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/*"

# 5. Run smoke tests
npm run test:smoke
```

---

## Useful Commands

### AWS CLI

```bash
# List all resources
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=AquaChain

# Check costs
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# List Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `AquaChain`)]'

# List DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `aquachain`)]'
```

### CDK Commands

```bash
# List stacks
cdk list

# Show differences
cdk diff

# Synthesize CloudFormation
cdk synth

# Deploy specific stack
cdk deploy AquaChainDataStack

# Destroy stack (careful!)
cdk destroy AquaChainDataStack
```

---

## Next Steps

1. ✅ Complete setup following this guide
2. 📖 Read [PROJECT_REPORT.md](PROJECT_REPORT.md) for comprehensive documentation
3. 🔐 Review [Security Quick Start](SECURITY_QUICK_START.md)
4. 🚀 Check [README_START_HERE.md](README_START_HERE.md) for navigation
5. 📊 Monitor your deployment with CloudWatch

---

## Support

**Need help?**
- 📖 Check [PROJECT_REPORT.md](PROJECT_REPORT.md)
- 🗺️ Navigate with [README_START_HERE.md](README_START_HERE.md)
- 🔍 Search documentation in `/DOCS` directory
- 💬 Contact team via Slack: #aquachain-infrastructure

---

**Project Status:** Production-Ready  
**Last Updated:** October 27, 2025  
**Setup Time:** ~30 minutes

