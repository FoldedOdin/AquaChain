# Complete Google OAuth Lambda Setup Script
# This script configures the Lambda function with Google OAuth credentials

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Google OAuth Lambda Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:758346259059:secret:aquachain/google-oauth/client-secret-dev-vyX2NP"
$FUNCTION_NAME = "aquachain-function-auth-service-dev"
$REGION = "ap-south-1"
$ROLE_NAME = "aquachain-role-data-processing-dev"

Write-Host "Step 1: Checking if Lambda function exists..." -ForegroundColor Yellow
try {
    $function = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Function does not exist"
    }
    Write-Host "Function already exists." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Function does not exist. Creating new Lambda function..." -ForegroundColor Yellow
    
    # Get the role ARN
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query "Role.Arn" --output text
    
    # Create a minimal deployment package
    Write-Host "Creating minimal deployment package..." -ForegroundColor Yellow
    $tempDir = "temp_package"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    
    @"
import json
def lambda_handler(event, context):
    return {'statusCode': 200, 'body': json.dumps('Hello')}
"@ | Out-File -FilePath "$tempDir\handler.py" -Encoding UTF8
    
    Compress-Archive -Path "$tempDir\*" -DestinationPath "temp.zip" -Force
    
    Write-Host "Creating Lambda function..." -ForegroundColor Yellow
    aws lambda create-function `
      --function-name $FUNCTION_NAME `
      --runtime python3.11 `
      --role $ROLE_ARN `
      --handler handler.lambda_handler `
      --zip-file fileb://temp.zip `
      --timeout 30 `
      --memory-size 512 `
      --region $REGION `
      --description "AquaChain Auth Service with Google OAuth support"
    
    # Cleanup
    Remove-Item "temp.zip" -Force
    Remove-Item $tempDir -Recurse -Force
    
    Write-Host "Waiting for function to be active..." -ForegroundColor Yellow
    aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION
    Write-Host "Function created successfully!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "Step 2: Adding Google OAuth Secret ARN to Lambda environment..." -ForegroundColor Yellow
aws lambda update-function-configuration `
  --function-name $FUNCTION_NAME `
  --environment "Variables={GOOGLE_CLIENT_SECRET_ARN=$SECRET_ARN,USERS_TABLE=AquaChain-Users,COGNITO_USER_POOL_ID=ap-south-1_QUDl7hG8u,COGNITO_CLIENT_ID=692o9a3pjudl1vudfgqpr5nuln,REGION=ap-south-1,ENVIRONMENT=dev}" `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to update Lambda configuration!" -ForegroundColor Red
    exit 1
}

Write-Host "Waiting for configuration update..." -ForegroundColor Yellow
aws lambda wait function-updated --function-name $FUNCTION_NAME --region $REGION
Write-Host ""

Write-Host "Step 3: Granting Lambda permission to read the secret..." -ForegroundColor Yellow
Write-Host "Creating IAM policy for Secrets Manager access..." -ForegroundColor Yellow

# Create policy document
$policyDoc = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "$SECRET_ARN"
    }
  ]
}
"@

$policyDoc | Out-File -FilePath "policy.json" -Encoding UTF8

# Attach policy to Lambda role
aws iam put-role-policy `
  --role-name $ROLE_NAME `
  --policy-name GoogleOAuthSecretsAccess `
  --policy-document file://policy.json

if ($LASTEXITCODE -eq 0) {
    Write-Host "IAM policy attached successfully!" -ForegroundColor Green
} else {
    Write-Host "Warning: Failed to attach IAM policy. You may need to do this manually." -ForegroundColor Yellow
}

# Cleanup
Remove-Item "policy.json" -Force

Write-Host ""
Write-Host "Step 4: Verifying configuration..." -ForegroundColor Yellow
$envVar = aws lambda get-function-configuration `
  --function-name $FUNCTION_NAME `
  --region $REGION `
  --query "Environment.Variables.GOOGLE_CLIENT_SECRET_ARN" `
  --output text

Write-Host "Environment variable set to: $envVar" -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Verifying secret access..." -ForegroundColor Yellow
Write-Host "Testing if secret exists..." -ForegroundColor Yellow
$secret = aws secretsmanager get-secret-value `
  --secret-id $SECRET_ARN `
  --region $REGION `
  --query "SecretString" `
  --output text

if ($secret) {
    Write-Host "Secret retrieved successfully!" -ForegroundColor Green
    Write-Host "Secret contains: $(($secret | ConvertFrom-Json | Select-Object -Property client_id).client_id)" -ForegroundColor Green
} else {
    Write-Host "Warning: Could not retrieve secret!" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lambda Function: $FUNCTION_NAME" -ForegroundColor White
Write-Host "Secret ARN: $SECRET_ARN" -ForegroundColor White
Write-Host "Region: $REGION" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Deploy the actual Lambda code:" -ForegroundColor White
Write-Host "   .\scripts\deployment\deploy-lambda-auth-service.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Configure API Gateway to route /api/auth/google/callback" -ForegroundColor White
Write-Host "   to this Lambda function" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test the OAuth flow:" -ForegroundColor White
Write-Host "   - Click 'Continue with Google' in your app" -ForegroundColor Gray
Write-Host "   - Authenticate with Google" -ForegroundColor Gray
Write-Host "   - Verify callback works" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Check CloudWatch Logs for any errors:" -ForegroundColor White
Write-Host "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
