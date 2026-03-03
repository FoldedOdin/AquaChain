#!/bin/bash

# Deploy User Management Lambda Function
# This script packages and deploys the user_management Lambda function to AWS

set -e  # Exit on error

# Configuration
FUNCTION_NAME="AquaChain-Function-UserManagement-dev"
REGION="ap-south-1"
LAMBDA_DIR="lambda/user_management"

echo "🚀 Deploying User Management Lambda Function"
echo "=============================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if we're in the project root
if [ ! -d "$LAMBDA_DIR" ]; then
    echo "❌ Lambda directory not found. Please run this script from the project root."
    exit 1
fi

# Navigate to Lambda directory
cd "$LAMBDA_DIR"

echo "📦 Packaging Lambda function..."

# Create deployment package
if [ -f "function.zip" ]; then
    rm function.zip
fi

# Package the function with ALL dependencies
zip -r function.zip handler.py errors.py error_handler.py structured_logger.py audit_logger.py cors_utils.py cache_service.py user_utils.py 2>&1 | grep -v "adding:"

echo "✅ Package created: function.zip"
echo ""

# Get current function configuration
echo "🔍 Checking current Lambda configuration..."
CURRENT_RUNTIME=$(aws lambda get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query 'Runtime' \
    --output text 2>/dev/null || echo "not-found")

if [ "$CURRENT_RUNTIME" == "not-found" ]; then
    echo "❌ Lambda function '$FUNCTION_NAME' not found in region '$REGION'"
    echo "   Please create the function first using CDK or AWS Console"
    exit 1
fi

echo "✅ Function found: $FUNCTION_NAME (Runtime: $CURRENT_RUNTIME)"
echo ""

# Deploy to AWS Lambda
echo "🚀 Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://function.zip \
    --region "$REGION" \
    --output json > /dev/null

echo "✅ Code uploaded successfully"
echo ""

# Wait for function to be updated
echo "⏳ Waiting for function to be updated..."
aws lambda wait function-updated \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION"

echo "✅ Function updated successfully"
echo ""

# Get updated function info
echo "📊 Function Information:"
aws lambda get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query '{FunctionName:FunctionName,Runtime:Runtime,LastModified:LastModified,CodeSize:CodeSize,MemorySize:MemorySize,Timeout:Timeout}' \
    --output table

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🔍 Next Steps:"
echo "1. Test the email update functionality"
echo "2. Check CloudWatch logs: /aws/lambda/$FUNCTION_NAME"
echo "3. Monitor for any errors in the next 15 minutes"
echo ""
echo "📝 CloudWatch Logs:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION"
echo ""

# Cleanup
rm function.zip

cd - > /dev/null
