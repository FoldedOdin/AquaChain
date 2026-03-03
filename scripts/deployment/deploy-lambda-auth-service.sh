#!/bin/bash
# Deploy Auth Service Lambda with Google OAuth Support
# This script packages and deploys the auth service Lambda function

echo "========================================"
echo "Deploying Auth Service Lambda Function"
echo "========================================"
echo ""

# Configuration
FUNCTION_NAME="aquachain-function-auth-service-dev"
LAMBDA_DIR="lambda/auth_service"
PACKAGE_DIR="$LAMBDA_DIR/package"
ZIP_FILE="$LAMBDA_DIR/function.zip"

echo "Step 1: Cleaning previous build..."
rm -f "$ZIP_FILE"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

echo "Step 2: Installing dependencies..."
pip install -r "$LAMBDA_DIR/requirements.txt" -t "$PACKAGE_DIR" --upgrade

echo "Step 3: Copying Lambda function files..."
cp "$LAMBDA_DIR/handler.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/google_oauth_handler.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/auth_utils.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/recaptcha_verifier.py" "$PACKAGE_DIR/"

echo "Step 4: Copying shared utilities..."
cp lambda/shared/*.py "$PACKAGE_DIR/"

echo "Step 5: Creating deployment package..."
cd "$PACKAGE_DIR"
zip -r ../function.zip . -q
cd ../../..

echo "Step 6: Deploying to AWS Lambda..."
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file "fileb://$ZIP_FILE" \
  --region ap-south-1

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Deployment Successful!"
    echo "========================================"
    echo "Function: $FUNCTION_NAME"
    echo "Region: ap-south-1"
    echo ""
    echo "Waiting for function to be active..."
    aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region ap-south-1
    
    echo ""
    echo "Verifying deployment..."
    aws lambda get-function --function-name "$FUNCTION_NAME" --region ap-south-1 --query "Configuration.[FunctionName,LastModified,CodeSize,State]" --output table
    
    echo ""
    echo "========================================"
    echo "Next Steps:"
    echo "========================================"
    echo "1. Configure Google OAuth credentials in Google Cloud Console"
    echo "2. Store Google Client Secret in AWS Secrets Manager"
    echo "3. Update Lambda environment variables with Secret ARN"
    echo "4. Test the /api/auth/google/callback endpoint"
    echo "5. Verify user creation in DynamoDB"
    echo ""
    echo "See DOCS/guides/GOOGLE_OAUTH_SETUP_GUIDE.md for details"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "Deployment Failed!"
    echo "========================================"
    echo "Please check the error message above"
    echo ""
    exit 1
fi

echo ""
echo "Cleaning up..."
rm -rf "$PACKAGE_DIR"

echo "Done!"
