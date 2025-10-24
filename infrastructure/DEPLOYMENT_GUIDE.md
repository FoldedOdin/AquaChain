# AquaChain Infrastructure Deployment Guide

This guide walks you through deploying the complete AquaChain infrastructure to AWS.

## Prerequisites

### 1. Install Required Tools

#### AWS CLI
```bash
# Windows (using installer)
# Download from: https://aws.amazon.com/cli/

# macOS
brew install awscli

# Linux
sudo apt install awscli
# or
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

#### Node.js and CDK
```bash
# Install Node.js (if not already installed)
# Download from: https://nodejs.org/

# Install AWS CDK
npm install -g aws-cdk
```

#### Python 3.11+
```bash
# Windows: Download from python.org
# macOS: brew install python
# Linux: sudo apt install python3 python3-pip python3-venv
```

### 2. Configure AWS Credentials

#### Option A: Automated Setup (Recommended)
```bash
# Navigate to infrastructure directory
cd infrastructure

# Run the setup script
python setup-aws-env.py

# This will:
# 1. Check AWS CLI installation
# 2. Guide you through credential setup
# 3. Create .env file with your configuration
```

#### Option B: Manual Setup
```bash
# Configure AWS CLI with your credentials
aws configure

# You'll need:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region (us-east-1)
# - Default output format (json)
```

#### Option C: Environment Variables
Create `.env` file in the infrastructure directory:
```bash
AWS_ACCOUNT_ID=123456789012
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
CDK_DEFAULT_ACCOUNT=123456789012
CDK_DEFAULT_REGION=us-east-1
```

### 3. Verify Setup

```bash
# Check AWS identity
aws sts get-caller-identity

# Check CDK version
cdk --version

# Check Python version
python --version
```

## Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# Navigate to infrastructure directory
cd infrastructure

# Run the deployment script
python deploy-infrastructure.py dev

# This will:
# 1. Check prerequisites
# 2. Set up Python environment
# 3. Bootstrap CDK
# 4. Deploy all stacks
# 5. Generate frontend configuration
```

### Option 2: Manual Deployment

```bash
# Navigate to CDK directory
cd infrastructure/cdk

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all --context environment=dev
```

## Deployment Environments

### Development Environment
```bash
python deploy-infrastructure.py dev
```
- **Purpose**: Development and testing
- **Resources**: Minimal, cost-optimized
- **Data retention**: 7 days
- **No cross-account replication**

### Staging Environment
```bash
python deploy-infrastructure.py staging
```
- **Purpose**: Pre-production testing
- **Resources**: Production-like but smaller
- **Data retention**: 30 days
- **Cross-region backup enabled**

### Production Environment
```bash
python deploy-infrastructure.py prod
```
- **Purpose**: Live production system
- **Resources**: Full scale, high availability
- **Data retention**: 7 years (compliance)
- **Full disaster recovery setup**

## Infrastructure Components

The deployment creates the following AWS resources:

### 1. Security Stack
- **KMS Keys**: Data encryption, audit trail, ledger signing
- **IAM Roles**: Service roles with least privilege
- **Security Groups**: Network access control

### 2. Core Stack
- **VPC**: Network infrastructure (if needed)
- **Networking**: Subnets, route tables, gateways

### 3. Data Stack
- **DynamoDB Tables**:
  - `aquachain-readings`: Sensor data storage
  - `aquachain-ledger`: Immutable audit ledger
  - `aquachain-users`: User profiles
  - `aquachain-service-requests`: Technician requests
- **S3 Buckets**:
  - Data lake bucket (encrypted)
  - Audit trail bucket (Object Lock enabled)
- **IoT Core**: Device management and messaging

### 4. Compute Stack
- **Lambda Functions**:
  - Data processing
  - User management
  - Service requests
  - Audit processing
  - WebSocket handling
- **SageMaker**: ML model endpoints (if configured)

### 5. API Stack
- **API Gateway**: REST API with authentication
- **WebSocket API**: Real-time communication
- **Cognito**: User authentication and authorization
- **WAF**: API protection and rate limiting

### 6. Monitoring Stack
- **CloudWatch**: Metrics, logs, and alarms
- **X-Ray**: Distributed tracing
- **SNS**: Alert notifications

### 7. Disaster Recovery Stack
- **Backup**: Automated backups
- **Cross-region replication**: Data redundancy
- **Failover automation**: RTO/RPO compliance

### 8. Landing Page Stack
- **CloudFront**: CDN for static assets
- **S3**: Static website hosting
- **Route 53**: DNS management

## Post-Deployment Steps

### 1. Verify Deployment

```bash
# Check stack status
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Get API endpoints
aws cloudformation describe-stacks --stack-name AquaChain-API-dev --query 'Stacks[0].Outputs'
```

### 2. Configure Frontend

The deployment script automatically creates frontend configuration, but you can also do it manually:

```bash
# Navigate to frontend directory
cd frontend

# Get AWS configuration
npm run get-aws-config dev

# Switch to AWS mode
npm run switch-to-aws

# Start the app
npm start
```

### 3. Create Test Users

#### Option A: AWS Console
1. Go to AWS Console → Cognito → User Pools
2. Select your AquaChain user pool
3. Users tab → Create user
4. Set email and temporary password

#### Option B: AWS CLI
```bash
# Get User Pool ID from stack outputs
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name AquaChain-API-dev --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)

# Create a consumer user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username consumer@test.com \
  --user-attributes Name=email,Value=consumer@test.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username consumer@test.com \
  --password Password123! \
  --permanent

# Add user to consumer group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username consumer@test.com \
  --group-name consumers
```

### 4. Test the System

```bash
# Test API endpoint
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/api/v1/health

# Test authentication in your app
# Login with: consumer@test.com / Password123!
```

## Cost Optimization

### Development Environment
- **Estimated monthly cost**: $50-100
- Uses pay-per-request pricing
- Minimal reserved capacity
- Short data retention

### Production Environment
- **Estimated monthly cost**: $500-2000 (depends on usage)
- Provisioned capacity for predictable workloads
- Long-term data retention
- Full disaster recovery

### Cost Reduction Tips
1. **Use development environment** for testing
2. **Delete unused stacks** when not needed
3. **Monitor usage** with AWS Cost Explorer
4. **Set up billing alerts**

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Failed
```bash
# Error: CDK not bootstrapped
# Solution: Bootstrap manually
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

#### 2. Stack Deployment Failed
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name AquaChain-Security-dev

# Common causes:
# - Insufficient IAM permissions
# - Resource limits exceeded
# - Name conflicts
```

#### 3. Resource Already Exists
```bash
# If resources exist from previous deployment
# Option 1: Delete existing stack
aws cloudformation delete-stack --stack-name STACK-NAME

# Option 2: Import existing resources (advanced)
# Use CDK import functionality
```

#### 4. Permission Denied
```bash
# Check IAM permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR-USERNAME

# Required permissions:
# - CloudFormation full access
# - IAM role creation
# - Service-specific permissions (DynamoDB, S3, Lambda, etc.)
```

### Getting Help

1. **Check CloudWatch Logs** for Lambda function errors
2. **Review CloudFormation Events** for deployment issues
3. **Verify IAM Permissions** for your AWS user
4. **Check AWS Service Limits** in your account

## Cleanup

### Delete Development Environment
```bash
# Delete all stacks (in reverse order)
cdk destroy --all --context environment=dev

# Or use AWS CLI
aws cloudformation delete-stack --stack-name AquaChain-LandingPage-dev
aws cloudformation delete-stack --stack-name AquaChain-DR-dev
aws cloudformation delete-stack --stack-name AquaChain-Monitoring-dev
aws cloudformation delete-stack --stack-name AquaChain-API-dev
aws cloudformation delete-stack --stack-name AquaChain-Compute-dev
aws cloudformation delete-stack --stack-name AquaChain-Data-dev
aws cloudformation delete-stack --stack-name AquaChain-Core-dev
aws cloudformation delete-stack --stack-name AquaChain-Security-dev
```

### Partial Cleanup
```bash
# Delete specific stack
cdk destroy AquaChain-API-dev --context environment=dev
```

## Next Steps

After successful deployment:

1. **Configure monitoring alerts**
2. **Set up CI/CD pipeline** for automated deployments
3. **Configure custom domain** and SSL certificates
4. **Set up backup and disaster recovery testing**
5. **Implement security scanning** and compliance checks

Your AquaChain infrastructure is now ready for production use! 🚀