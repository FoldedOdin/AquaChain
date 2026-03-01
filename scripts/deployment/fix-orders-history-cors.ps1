# Fix CORS for /api/orders/history endpoint

$apiId = "vtqjfznspc"
$region = "ap-south-1"
$resourceId = "7hx5ie"

Write-Host "Fixing CORS for /api/orders/history..." -ForegroundColor Cyan

# Step 1: Delete existing OPTIONS method
Write-Host "`n1. Removing existing OPTIONS method..." -ForegroundColor Yellow
aws apigateway delete-method `
    --rest-api-id $apiId `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --region $region 2>$null

# Step 2: Create OPTIONS method with NONE authorization
Write-Host "`n2. Creating OPTIONS method..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $apiId `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $region

# Step 3: Create MOCK integration
Write-Host "`n3. Creating MOCK integration..." -ForegroundColor Yellow
aws apigateway put-integration `
    --rest-api-id $apiId `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates "application/json={statusCode:200}" `
    --region $region

# Step 4: Create method response
Write-Host "`n4. Creating method response..." -ForegroundColor Yellow
aws apigateway put-method-response `
    --rest-api-id $apiId `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
    --region $region

# Step 5: Create integration response with CORS headers
Write-Host "`n5. Creating integration response with CORS headers..." -ForegroundColor Yellow
aws apigateway put-integration-response `
    --rest-api-id $apiId `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters "method.response.header.Access-Control-Allow-Headers='Content-Type,Authorization',method.response.header.Access-Control-Allow-Methods='GET,OPTIONS',method.response.header.Access-Control-Allow-Origin='*'" `
    --region $region

# Step 6: Deploy API
Write-Host "`n6. Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $apiId `
    --stage-name dev `
    --region $region

Write-Host "`n✅ CORS configuration complete!" -ForegroundColor Green
Write-Host "Please wait 10-15 seconds for deployment to propagate, then refresh your page." -ForegroundColor Cyan
