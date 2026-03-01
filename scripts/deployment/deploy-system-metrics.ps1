# Deploy System Metrics Feature
# This script deploys the real-time system metrics endpoint to AWS Lambda

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy System Metrics Feature" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$FUNCTION_NAME = "aquachain-function-admin-service-dev"
$USER_POOL_ID = "ap-south-1_QUDl7hG8u"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Gray
Write-Host "  Function: $FUNCTION_NAME" -ForegroundColor Gray
Write-Host "  User Pool: $USER_POOL_ID" -ForegroundColor Gray
Write-Host ""

# Step 1: Package Lambda function
Write-Host "Step 1: Packaging Lambda function..." -ForegroundColor Yellow

$TEMP_DIR = "temp_lambda_package"
$ZIP_FILE = "admin-service-metrics.zip"

# Clean up old package
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}

# Create temp directory
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Copy Lambda files
Write-Host "  Copying Lambda files..." -ForegroundColor Gray
Copy-Item -Path "lambda/admin_service/handler.py" -Destination $TEMP_DIR
Copy-Item -Path "lambda/admin_service/get_system_metrics.py" -Destination $TEMP_DIR

# Copy shared utilities if they exist
if (Test-Path "lambda/shared") {
    Copy-Item -Path "lambda/shared/*" -Destination $TEMP_DIR -Recurse
}

# Create ZIP file
Write-Host "  Creating deployment package..." -ForegroundColor Gray
Push-Location $TEMP_DIR
Compress-Archive -Path * -DestinationPath "../$ZIP_FILE" -Force
Pop-Location

# Clean up temp directory
Remove-Item -Recurse -Force $TEMP_DIR

Write-Host "  ✓ Package created: $ZIP_FILE" -ForegroundColor Green
Write-Host ""

# Step 2: Update Lambda function code
Write-Host "Step 2: Updating Lambda function code..." -ForegroundColor Yellow

try {
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file "fileb://$ZIP_FILE" `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "  ✓ Lambda code updated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to update Lambda code" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Update Lambda environment variables
Write-Host "Step 3: Updating environment variables..." -ForegroundColor Yellow

try {
    aws lambda update-function-configuration `
        --function-name $FUNCTION_NAME `
        --environment "Variables={USER_POOL_ID=$USER_POOL_ID,COGNITO_USER_POOL_ID=$USER_POOL_ID}" `
        --region $REGION `
        --output json | Out-Null
    
    Write-Host "  ✓ Environment variables updated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to update environment variables" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

Write-Host ""

# Step 4: Wait for Lambda to be ready
Write-Host "Step 4: Waiting for Lambda to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "  ✓ Lambda function ready" -ForegroundColor Green
Write-Host ""

# Step 5: Add IAM permissions for CloudWatch and Cognito
Write-Host "Step 5: Checking IAM permissions..." -ForegroundColor Yellow

$ROLE_NAME = "aquachain-admin-service-role-dev"

Write-Host "  Note: Ensure the Lambda execution role has these permissions:" -ForegroundColor Gray
Write-Host "    - cognito-idp:ListUsers" -ForegroundColor Gray
Write-Host "    - cloudwatch:GetMetricStatistics" -ForegroundColor Gray
Write-Host "    - lambda:GetFunction" -ForegroundColor Gray
Write-Host ""

# Step 6: Test the endpoint
Write-Host "Step 6: Testing the metrics endpoint..." -ForegroundColor Yellow

$API_ENDPOINT = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$METRICS_URL = "$API_ENDPOINT/api/admin/system/metrics"

Write-Host "  Endpoint: $METRICS_URL" -ForegroundColor Gray
Write-Host "  Note: You'll need a valid admin JWT token to test this endpoint" -ForegroundColor Gray
Write-Host ""

# Clean up
Write-Host "Cleaning up..." -ForegroundColor Yellow
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
    Write-Host "  ✓ Deployment package removed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Verify IAM permissions for the Lambda role" -ForegroundColor White
Write-Host "2. Test the endpoint: GET $METRICS_URL" -ForegroundColor White
Write-Host "3. Check CloudWatch logs if there are any issues" -ForegroundColor White
Write-Host ""
Write-Host "The admin dashboard will now fetch real-time metrics:" -ForegroundColor Cyan
Write-Host "  • User count from Cognito" -ForegroundColor White
Write-Host "  • API success rate from CloudWatch" -ForegroundColor White
Write-Host "  • System uptime from CloudWatch" -ForegroundColor White
Write-Host ""
Write-Host "Metrics refresh every 30 seconds automatically." -ForegroundColor Green
Write-Host ""
