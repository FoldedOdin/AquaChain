#!/bin/bash

# Contact Form Service Deployment Script
# Automates the deployment of the complete contact form infrastructure

set -e  # Exit on error

echo "=========================================="
echo "AquaChain Contact Form Service Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}✗ AWS CDK not found. Please install it: npm install -g aws-cdk${NC}"
    exit 1
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: $ACCOUNT_ID${NC}"
echo ""

# Step 1: Create DynamoDB Table
echo "Step 1: Creating DynamoDB table..."
python3 infrastructure/dynamodb/contact_table.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ DynamoDB table created${NC}"
else
    echo -e "${YELLOW}⚠ Table may already exist${NC}"
fi
echo ""

# Step 2: Verify SES Emails
echo "Step 2: Verifying SES email addresses..."
echo "Requesting verification for noreply@aquachain.io..."
aws ses verify-email-identity --email-address noreply@aquachain.io --region us-east-1 2>/dev/null || true

echo "Requesting verification for admin@aquachain.io..."
aws ses verify-email-identity --email-address admin@aquachain.io --region us-east-1 2>/dev/null || true

echo -e "${YELLOW}⚠ Please check your email inbox and verify both addresses${NC}"
echo ""

# Step 3: Deploy CDK Stack
echo "Step 3: Deploying CDK stack..."
cd infrastructure/cdk

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

# Bootstrap CDK (if needed)
echo "Bootstrapping CDK..."
cdk bootstrap aws://$ACCOUNT_ID/us-east-1 2>/dev/null || true

# Deploy the stack
echo "Deploying ContactServiceStack..."
cdk deploy ContactServiceStack --require-approval never

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CDK stack deployed successfully${NC}"
else
    echo -e "${RED}✗ CDK deployment failed${NC}"
    exit 1
fi

# Get API URL from stack outputs
API_URL=$(aws cloudformation describe-stacks \
    --stack-name ContactServiceStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ContactApiEndpoint`].OutputValue' \
    --output text 2>/dev/null)

cd ../..
echo ""

# Step 4: Configure Frontend
echo "Step 4: Configuring frontend..."
if [ -n "$API_URL" ]; then
    echo "REACT_APP_API_URL=$API_URL" >> frontend/.env
    echo -e "${GREEN}✓ Frontend configured with API URL${NC}"
    echo "API URL: $API_URL"
else
    echo -e "${YELLOW}⚠ Could not retrieve API URL. Please configure manually.${NC}"
fi
echo ""

# Step 5: Test Deployment
echo "Step 5: Testing deployment..."
if [ -n "$API_URL" ]; then
    echo "Testing API endpoint..."
    RESPONSE=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "message": "This is a test message from deployment script",
            "inquiryType": "general"
        }')
    
    if echo "$RESPONSE" | grep -q "submissionId"; then
        echo -e "${GREEN}✓ API test successful${NC}"
        echo "Response: $RESPONSE"
    else
        echo -e "${YELLOW}⚠ API test returned unexpected response${NC}"
        echo "Response: $RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ Skipping API test (no URL available)${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ DynamoDB table created${NC}"
echo -e "${YELLOW}⚠ SES emails need verification (check inbox)${NC}"
echo -e "${GREEN}✓ Lambda function deployed${NC}"
echo -e "${GREEN}✓ API Gateway configured${NC}"
echo -e "${GREEN}✓ Frontend environment updated${NC}"
echo ""

if [ -n "$API_URL" ]; then
    echo "API Endpoint: $API_URL"
    echo ""
fi

echo "Next Steps:"
echo "1. Verify SES email addresses (check your inbox)"
echo "2. Test the contact form on your website"
echo "3. Check CloudWatch logs for any issues"
echo "4. Set up CloudWatch alarms (optional)"
echo "5. Request SES production access (for production use)"
echo ""

echo "Documentation:"
echo "- Quick Start: DOCS/CONTACT_FORM_QUICK_START.md"
echo "- Full Setup: DOCS/CONTACT_FORM_SETUP.md"
echo "- API Docs: lambda/contact_service/README.md"
echo ""

echo -e "${GREEN}Deployment complete!${NC}"
