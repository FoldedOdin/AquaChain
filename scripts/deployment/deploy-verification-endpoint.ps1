# Deploy verification status endpoint

$REGION = "ap-south-1"
$API_ID = "vtqjfznspc"
$USER_POOL_ID = "ap-south-1_QUDl7hG8u"

Write-Host "Deploying verification status endpoint..." -ForegroundColor Cyan

# Create Lambda function
Write-Host "Creating Lambda function..." -ForegroundColor Yellow

# Package Lambda
if (Test-Path lambda/auth_service/function.zip) {
    Remove-Item lambda/auth_service/function.zip
}

Compress-Archive -Path lambda/auth_service/verification_status.py -DestinationPath lambda/auth_service/function.zip -Force

# Create or update Lambda function
$functionExists = aws lambda get-function --function-name aquachain-verification-status-dev --region $REGION 2>&1

if ($functionExists -like "*ResourceNotFoundException*") {
    Write-Host "Creating new Lambda function..." -ForegroundColor Yellow
    
    aws lambda create-function `
        --function-name aquachain-verification-status-dev `
        --runtime python3.11 `
        --role arn:aws:iam::758346259059:role/aquachain-lambda-execution-role `
        --handler verification_status.lambda_handler `
        --zip-file fileb://lambda/auth_service/function.zip `
        --timeout 30 `
        --memory-size 256 `
        --environment "Variables={COGNITO_USER_POOL_ID=$USER_POOL_ID,REGION=$REGION}" `
        --region $REGION
} else {
    Write-Host "Updating existing Lambda function..." -ForegroundColor Yellow
    
    aws lambda update-function-code `
        --function-name aquachain-verification-status-dev `
        --zip-file fileb://lambda/auth_service/function.zip `
        --region $REGION
    
    aws lambda update-function-configuration `
        --function-name aquachain-verification-status-dev `
        --environment "Variables={COGNITO_USER_POOL_ID=$USER_POOL_ID,REGION=$REGION}" `
        --region $REGION
}

Write-Host "Waiting for Lambda to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Get API Gateway root resource
$rootId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text

# Create /api resource if it doesn't exist
$apiResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api'].id" --output text

if ([string]::IsNullOrWhiteSpace($apiResourceId)) {
    Write-Host "Creating /api resource..." -ForegroundColor Yellow
    $apiResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $rootId `
        --path-part api `
        --region $REGION `
        --query 'id' --output text
}

# Create /api/auth resource
$authResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/auth'].id" --output text

if ([string]::IsNullOrWhiteSpace($authResourceId)) {
    Write-Host "Creating /api/auth resource..." -ForegroundColor Yellow
    $authResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResourceId `
        --path-part auth `
        --region $REGION `
        --query 'id' --output text
}

# Create /api/auth/verification-status resource
$verificationResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/auth/verification-status'].id" --output text

if ([string]::IsNullOrWhiteSpace($verificationResourceId)) {
    Write-Host "Creating /api/auth/verification-status resource..." -ForegroundColor Yellow
    $verificationResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $authResourceId `
        --path-part verification-status `
        --region $REGION `
        --query 'id' --output text
}

# Create /api/auth/verification-status/{email} resource
$emailResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/auth/verification-status/{email}'].id" --output text

if ([string]::IsNullOrWhiteSpace($emailResourceId)) {
    Write-Host "Creating /api/auth/verification-status/{email} resource..." -ForegroundColor Yellow
    $emailResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $verificationResourceId `
        --path-part '{email}' `
        --region $REGION `
        --query 'id' --output text
}

# Add OPTIONS method for CORS
Write-Host "Adding OPTIONS method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $emailResourceId `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION 2>$null

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $emailResourceId `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{"application/json":"{\"statusCode\": 200}"}' `
    --region $REGION 2>$null

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $emailResourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
    --region $REGION 2>$null

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $emailResourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'GET,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
    --region $REGION 2>$null

# Add GET method
Write-Host "Adding GET method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $emailResourceId `
    --http-method GET `
    --authorization-type NONE `
    --region $REGION 2>$null

# Get Lambda ARN
$lambdaArn = "arn:aws:lambda:$REGION:758346259059:function:aquachain-verification-status-dev"

# Add Lambda integration
aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $emailResourceId `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$lambdaArn/invocations" `
    --region $REGION

# Add Lambda permission
aws lambda add-permission `
    --function-name aquachain-verification-status-dev `
    --statement-id apigateway-verification-status `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:$REGION:758346259059:$API_ID/*/*/api/auth/verification-status/*" `
    --region $REGION 2>$null

# Deploy API
Write-Host "Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --region $REGION

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/auth/verification-status/{email}" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test with:" -ForegroundColor Yellow
Write-Host "curl https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/auth/verification-status/test@example.com" -ForegroundColor Cyan
