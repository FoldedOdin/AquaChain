# Setup API Gateway Route for Google OAuth Callback
# This script creates the /api/auth/google/callback route and connects it to Lambda

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API Gateway Google OAuth Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-auth-service-dev"
$AUTH_RESOURCE_ID = "wzt9ff"  # /api/auth
$ACCOUNT_ID = "758346259059"

Write-Host "Step 1: Creating /api/auth/google resource..." -ForegroundColor Yellow

# Create /api/auth/google resource
$googleResource = aws apigateway create-resource `
  --rest-api-id $API_ID `
  --parent-id $AUTH_RESOURCE_ID `
  --path-part "google" `
  --region $REGION | ConvertFrom-Json

$GOOGLE_RESOURCE_ID = $googleResource.id
Write-Host "Created resource: /api/auth/google (ID: $GOOGLE_RESOURCE_ID)" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Creating /api/auth/google/callback resource..." -ForegroundColor Yellow

# Create /api/auth/google/callback resource
$callbackResource = aws apigateway create-resource `
  --rest-api-id $API_ID `
  --parent-id $GOOGLE_RESOURCE_ID `
  --path-part "callback" `
  --region $REGION | ConvertFrom-Json

$CALLBACK_RESOURCE_ID = $callbackResource.id
Write-Host "Created resource: /api/auth/google/callback (ID: $CALLBACK_RESOURCE_ID)" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Creating POST method on /api/auth/google/callback..." -ForegroundColor Yellow

# Create POST method
aws apigateway put-method `
  --rest-api-id $API_ID `
  --resource-id $CALLBACK_RESOURCE_ID `
  --http-method POST `
  --authorization-type NONE `
  --region $REGION | Out-Null

Write-Host "Created POST method" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Creating Lambda integration..." -ForegroundColor Yellow

# Create Lambda integration
aws apigateway put-integration `
  --rest-api-id $API_ID `
  --resource-id $CALLBACK_RESOURCE_ID `
  --http-method POST `
  --type AWS_PROXY `
  --integration-http-method POST `
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" `
  --region $REGION | Out-Null

Write-Host "Created Lambda integration" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Granting API Gateway permission to invoke Lambda..." -ForegroundColor Yellow

# Grant API Gateway permission to invoke Lambda
$sourceArn = "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/POST/api/auth/google/callback"

try {
    aws lambda add-permission `
      --function-name aquachain-function-auth-service-dev `
      --statement-id apigateway-google-oauth-callback `
      --action lambda:InvokeFunction `
      --principal apigateway.amazonaws.com `
      --source-arn $sourceArn `
      --region $REGION 2>&1 | Out-Null
    Write-Host "Permission granted successfully" -ForegroundColor Green
} catch {
    Write-Host "Permission may already exist (this is OK)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 6: Enabling CORS on /api/auth/google/callback..." -ForegroundColor Yellow

# Create OPTIONS method for CORS
aws apigateway put-method `
  --rest-api-id $API_ID `
  --resource-id $CALLBACK_RESOURCE_ID `
  --http-method OPTIONS `
  --authorization-type NONE `
  --region $REGION | Out-Null

# Create MOCK integration for OPTIONS
aws apigateway put-integration `
  --rest-api-id $API_ID `
  --resource-id $CALLBACK_RESOURCE_ID `
  --http-method OPTIONS `
  --type MOCK `
  --request-templates '{"application/json":"{\"statusCode\": 200}"}' `
  --region $REGION | Out-Null

# Create method response for OPTIONS
aws apigateway put-method-response `
  --rest-api-id $API_ID `
  --resource-id $CALLBACK_RESOURCE_ID `
  --http-method OPTIONS `
  --status-code 200 `
  --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
  --region $REGION | Out-Null

# Create integration response for OPTIONS
aws apigateway put-integration-response `
  --rest-api-id $API_ID `
  --resource-id $CALLBACK_RESOURCE_ID `
  --http-method OPTIONS `
  --status-code 200 `
  --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
  --region $REGION | Out-Null

Write-Host "CORS enabled" -ForegroundColor Green
Write-Host ""

Write-Host "Step 7: Deploying API Gateway changes..." -ForegroundColor Yellow

# Deploy to dev stage
aws apigateway create-deployment `
  --rest-api-id $API_ID `
  --stage-name dev `
  --description "Added Google OAuth callback endpoint" `
  --region $REGION | Out-Null

Write-Host "Deployed to dev stage" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Endpoint:" -ForegroundColor White
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/api/auth/google/callback" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Update frontend .env.local:" -ForegroundColor White
Write-Host "   REACT_APP_API_ENDPOINT=https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test the OAuth flow:" -ForegroundColor White
Write-Host "   - Click 'Continue with Google'" -ForegroundColor Gray
Write-Host "   - Authenticate with Google" -ForegroundColor Gray
Write-Host "   - Should redirect back and log you in" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Check CloudWatch Logs if issues:" -ForegroundColor White
Write-Host "   aws logs tail /aws/lambda/aquachain-function-auth-service-dev --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test the endpoint directly:" -ForegroundColor White
Write-Host "   curl -X POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/api/auth/google/callback \" -ForegroundColor Gray
Write-Host "     -H 'Content-Type: application/json' \" -ForegroundColor Gray
Write-Host "     -d '{\"code\":\"test\",\"redirectUri\":\"http://localhost:3000/auth/google/callback\",\"clientId\":\"test\"}'" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
