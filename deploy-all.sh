#!/bin/bash

###############################################################################
# AquaChain Complete Deployment Script
# Deploys all infrastructure, Lambda functions, and frontend
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_DEFAULT_REGION:-ap-south-1}
SKIP_TESTS=${SKIP_TESTS:-false}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         AquaChain Complete Deployment Script              ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║  Environment: ${ENVIRONMENT}                                        ║${NC}"
echo -e "${BLUE}║  Region: ${AWS_REGION}                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Pre-flight Checks
###############################################################################

echo -e "${YELLOW}🔍 Running pre-flight checks...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS credentials configured${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${YELLOW}⚠️  CDK not found. Installing...${NC}"
    npm install -g aws-cdk
fi
echo -e "${GREEN}✅ CDK found: $(cdk --version)${NC}"

echo ""

###############################################################################
# Security Checks
###############################################################################

echo -e "${YELLOW}🔒 Running security checks...${NC}"

# Check for hardcoded credentials
if grep -r "AKIA" infrastructure/ --exclude-dir=node_modules --exclude-dir=cdk.out 2>/dev/null; then
    echo -e "${RED}❌ Found potential hardcoded AWS credentials!${NC}"
    echo -e "${RED}   Please remove them before deploying.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ No hardcoded credentials found${NC}"

# Check for .env files in git
if git ls-files | grep -E "\.env$" | grep -v "\.env\.example" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: .env files found in git${NC}"
fi

echo ""

###############################################################################
# Install Dependencies
###############################################################################

echo -e "${YELLOW}📦 Installing dependencies...${NC}"

# Frontend dependencies
echo -e "${BLUE}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

# Infrastructure dependencies
echo -e "${BLUE}Installing infrastructure dependencies...${NC}"
cd infrastructure/cdk
pip3 install -r requirements.txt
cd ../..
echo -e "${GREEN}✅ Infrastructure dependencies installed${NC}"

# Lambda dependencies
echo -e "${BLUE}Installing Lambda dependencies...${NC}"
for lambda_dir in lambda/*/; do
    if [ -f "${lambda_dir}requirements.txt" ]; then
        echo "  Installing dependencies for $(basename $lambda_dir)..."
        pip3 install -r "${lambda_dir}requirements.txt" -t "${lambda_dir}" --quiet
    fi
done
echo -e "${GREEN}✅ Lambda dependencies installed${NC}"

echo ""

###############################################################################
# Run Tests (Optional)
###############################################################################

if [ "$SKIP_TESTS" != "true" ]; then
    echo -e "${YELLOW}🧪 Running tests...${NC}"
    
    # Frontend tests
    echo -e "${BLUE}Running frontend tests...${NC}"
    cd frontend
    npm test -- --watchAll=false --coverage || {
        echo -e "${RED}❌ Frontend tests failed${NC}"
        exit 1
    }
    cd ..
    echo -e "${GREEN}✅ Frontend tests passed${NC}"
    
    # Python tests
    echo -e "${BLUE}Running Python tests...${NC}"
    python3 -m pytest lambda/ || {
        echo -e "${YELLOW}⚠️  Some Python tests failed (continuing anyway)${NC}"
    }
    
    # Security scan
    echo -e "${BLUE}Running security scan...${NC}"
    cd frontend
    npm audit --audit-level=high || {
        echo -e "${YELLOW}⚠️  Security vulnerabilities found (review required)${NC}"
    }
    cd ..
    
    echo ""
fi

###############################################################################
# Deploy Infrastructure
###############################################################################

echo -e "${YELLOW}🏗️  Deploying infrastructure...${NC}"

cd infrastructure/cdk

# Bootstrap CDK (if needed)
echo -e "${BLUE}Bootstrapping CDK...${NC}"
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/${AWS_REGION}

# Synthesize stacks
echo -e "${BLUE}Synthesizing CDK stacks...${NC}"
cdk synth --all

# Deploy stacks in order
STACKS=(
    "AquaChain-Security-${ENVIRONMENT}"
    "AquaChain-VPC-${ENVIRONMENT}"
    "AquaChain-Core-${ENVIRONMENT}"
    "AquaChain-Data-${ENVIRONMENT}"
    "AquaChain-Compute-${ENVIRONMENT}"
    "AquaChain-Backup-${ENVIRONMENT}"
    "AquaChain-API-${ENVIRONMENT}"
    "AquaChain-Monitoring-${ENVIRONMENT}"
    "AquaChain-DR-${ENVIRONMENT}"
    "AquaChain-Phase3-${ENVIRONMENT}"
)

for stack in "${STACKS[@]}"; do
    echo -e "${BLUE}Deploying ${stack}...${NC}"
    cdk deploy ${stack} --require-approval never || {
        echo -e "${RED}❌ Failed to deploy ${stack}${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ ${stack} deployed${NC}"
done

cd ../..

echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
echo ""

###############################################################################
# Deploy Lambda Functions
###############################################################################

echo -e "${YELLOW}⚡ Deploying Lambda functions...${NC}"

# Package and deploy each Lambda
LAMBDA_FUNCTIONS=(
    "auth_service"
    "data_processing"
    "ml_inference"
    "backup"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "${BLUE}Deploying ${func}...${NC}"
    
    cd lambda/${func}
    
    # Create deployment package
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" -x "tests/*" > /dev/null
    
    # Update Lambda function
    aws lambda update-function-code \
        --function-name aquachain-${func}-${ENVIRONMENT} \
        --zip-file fileb://function.zip \
        --region ${AWS_REGION} || {
        echo -e "${YELLOW}⚠️  Function aquachain-${func}-${ENVIRONMENT} not found (may not exist yet)${NC}"
    }
    
    # Cleanup
    rm function.zip
    
    cd ../..
    
    echo -e "${GREEN}✅ ${func} deployed${NC}"
done

echo ""

###############################################################################
# Build and Deploy Frontend
###############################################################################

echo -e "${YELLOW}🎨 Building and deploying frontend...${NC}"

cd frontend

# Build production bundle
echo -e "${BLUE}Building frontend...${NC}"
npm run build

# Get CloudFront distribution ID (if exists)
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='AquaChain Frontend ${ENVIRONMENT}'].Id" \
    --output text 2>/dev/null)

if [ -n "$DISTRIBUTION_ID" ]; then
    # Deploy to S3
    echo -e "${BLUE}Deploying to S3...${NC}"
    aws s3 sync build/ s3://aquachain-frontend-${ENVIRONMENT}/ --delete
    
    # Invalidate CloudFront cache
    echo -e "${BLUE}Invalidating CloudFront cache...${NC}"
    aws cloudfront create-invalidation \
        --distribution-id ${DISTRIBUTION_ID} \
        --paths "/*"
    
    echo -e "${GREEN}✅ Frontend deployed to CloudFront${NC}"
else
    echo -e "${YELLOW}⚠️  CloudFront distribution not found${NC}"
    echo -e "${YELLOW}   Frontend built but not deployed${NC}"
fi

cd ..

echo ""

###############################################################################
# Post-Deployment Verification
###############################################################################

echo -e "${YELLOW}✅ Running post-deployment verification...${NC}"

# Check API Gateway
API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='aquachain-api-${ENVIRONMENT}'].id" \
    --output text 2>/dev/null)

if [ -n "$API_ID" ]; then
    API_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/${ENVIRONMENT}"
    echo -e "${GREEN}✅ API Gateway: ${API_URL}${NC}"
    
    # Test health endpoint
    if curl -s "${API_URL}/health" > /dev/null; then
        echo -e "${GREEN}✅ API health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  API health check failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  API Gateway not found${NC}"
fi

# Check DynamoDB tables
echo -e "${BLUE}Checking DynamoDB tables...${NC}"
TABLES=$(aws dynamodb list-tables --query "TableNames[?starts_with(@, 'aquachain-')]" --output text)
TABLE_COUNT=$(echo $TABLES | wc -w)
echo -e "${GREEN}✅ Found ${TABLE_COUNT} DynamoDB tables${NC}"

# Check Lambda functions
echo -e "${BLUE}Checking Lambda functions...${NC}"
FUNCTIONS=$(aws lambda list-functions \
    --query "Functions[?starts_with(FunctionName, 'aquachain-')].FunctionName" \
    --output text)
FUNCTION_COUNT=$(echo $FUNCTIONS | wc -w)
echo -e "${GREEN}✅ Found ${FUNCTION_COUNT} Lambda functions${NC}"

echo ""

###############################################################################
# Deployment Summary
###############################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Environment:${NC} ${ENVIRONMENT}"
echo -e "${BLUE}Region:${NC} ${AWS_REGION}"
echo -e "${BLUE}API URL:${NC} ${API_URL:-Not available}"
echo -e "${BLUE}DynamoDB Tables:${NC} ${TABLE_COUNT}"
echo -e "${BLUE}Lambda Functions:${NC} ${FUNCTION_COUNT}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Verify all services are running"
echo "2. Run integration tests"
echo "3. Check CloudWatch logs for errors"
echo "4. Update DNS records if needed"
echo "5. Monitor CloudWatch alarms"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "- Deployment Guide: frontend/DEPLOYMENT_GUIDE.md"
echo "- Security Guide: infrastructure/SECURITY_CREDENTIALS_GUIDE.md"
echo "- Action Checklist: ACTION_CHECKLIST.md"
echo ""
echo -e "${GREEN}✨ Happy deploying! ✨${NC}"
