# Add GET method to /api/profile/update endpoint
$ErrorActionPreference = "Stop"

Write-Host "🔧 Adding GET method to /api/profile/update..." -ForegroundColor Cyan

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$RESOURCE_ID = "c84ane"  # /api/profile/update
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:211125763856:function:aquachain-function-user-management-dev"

# Step 1: Create GET method
Write-Host "`n📝 Creating GET method..." -ForegroundColor Cyan
try {
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method GET `
        --authorization-type NONE `
        --region $REGION | Out-Null
    Write-Host "✅ GET method created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  GET method may already exist" -ForegroundColor Yellow
}

# Step 2: Set up Lambda integration
Write-Host "`n🔗 Setting up Lambda integration..." -ForegroundColor Cyan
aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method GET `
    --type AWS_PROXY `
    --integration-http-method POST `
    --uri "arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set up Lambda integration" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda integration configured" -ForegroundColor Green

# Step 3: Add Lambda permission
Write-Host "`n🔐 Adding Lambda invoke permission..." -ForegroundColor Cyan
try {
    aws lambda add-permission `
        --function-name aquachain-function-user-management-dev `
        --statement-id apigateway-profile-get-2026 `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn "arn:aws:execute-api:$REGION:211125763856:$API_ID/*/GET/api/profile/update" `
        --region $REGION 2>&1 | Out-Null
    Write-Host "✅ Lambda permission added" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Permission may already exist" -ForegroundColor Yellow
}

# Step 4: Deploy changes
Write-Host "`n🚀 Deploying API Gateway..." -ForegroundColor Cyan
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Add GET method for profile endpoint" `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Deployed successfully" -ForegroundColor Green

Write-Host "`n✅ GET method added to /api/profile/update" -ForegroundColor Green
Write-Host "🔄 Please refresh your browser to test" -ForegroundColor Cyan
