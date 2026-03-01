# Deploy profile Lambda with GET support and configure API Gateway
$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Profile Lambda with GET support..." -ForegroundColor Cyan

# Step 1: Package and deploy Lambda
Write-Host "`n📦 Packaging Lambda function..." -ForegroundColor Cyan
cd lambda/user_management
if (Test-Path function.zip) { Remove-Item function.zip }
Compress-Archive -Path profile_update_simple.py -DestinationPath function.zip -Force
Write-Host "✅ Lambda packaged" -ForegroundColor Green

# Step 2: Update Lambda function
Write-Host "`n🔄 Updating Lambda function..." -ForegroundColor Cyan
aws lambda update-function-code `
    --function-name aquachain-profile-update-simple-dev `
    --zip-file fileb://function.zip `
    --region ap-south-1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to update Lambda function" -ForegroundColor Red
    cd ../..
    exit 1
}

Write-Host "✅ Lambda function updated" -ForegroundColor Green
cd ../..

# Step 3: Add GET method to API Gateway
Write-Host "`n🔧 Configuring API Gateway GET method..." -ForegroundColor Cyan

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$RESOURCE_ID = "c84ane"  # /api/profile/update resource

# Check if GET method exists
try {
    $existingMethod = aws apigateway get-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method GET `
        --region $REGION 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "⚠️  GET method already exists" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✅ No existing GET method found" -ForegroundColor Green
}

# Create GET method
Write-Host "`n🔧 Creating GET method..." -ForegroundColor Cyan
aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method GET `
    --authorization-type NONE `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Failed to create GET method (may already exist)" -ForegroundColor Yellow
}

# Set up Lambda integration for GET
Write-Host "`n🔧 Setting up Lambda integration for GET..." -ForegroundColor Cyan
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:211125763856:function:aquachain-profile-update-simple-dev"

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

# Step 4: Add Lambda permission for GET
Write-Host "`n🔐 Adding Lambda invoke permission for GET..." -ForegroundColor Cyan

try {
    aws lambda add-permission `
        --function-name aquachain-profile-update-simple-dev `
        --statement-id apigateway-profile-get-invoke `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn "arn:aws:execute-api:ap-south-1:211125763856:$API_ID/*/GET/api/profile/update" `
        --region $REGION 2>&1 | Out-Null
    
    Write-Host "✅ Lambda permission added" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Permission may already exist" -ForegroundColor Yellow
}

# Step 5: Deploy API Gateway
Write-Host "`n🚀 Deploying API Gateway changes..." -ForegroundColor Cyan
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Add GET support for profile endpoint" `
    --region $REGION | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy API Gateway" -ForegroundColor Red
    exit 1
}

Write-Host "✅ API Gateway deployed" -ForegroundColor Green

# Step 6: Test the GET endpoint
Write-Host "`n🧪 Testing GET endpoint..." -ForegroundColor Cyan
Write-Host "Please provide your JWT token to test:" -ForegroundColor Yellow
$token = Read-Host "Token"

if ($token) {
    try {
        $response = Invoke-WebRequest -Uri "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/profile/update" `
            -Method GET `
            -Headers @{
                "Authorization" = "Bearer $token"
                "Content-Type" = "application/json"
            } `
            -UseBasicParsing
        
        Write-Host "✅ GET request successful!" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Yellow
        $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "⚠️  Test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "📍 GET endpoint: https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/profile/update" -ForegroundColor Cyan
