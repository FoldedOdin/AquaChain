# Fix Orders CORS - Complete Recreation
# This completely recreates the OPTIONS method with proper MOCK integration

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$RESOURCE_ID = "eqsswe"

Write-Host "Fixing Orders CORS..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Delete existing OPTIONS method completely
Write-Host "1. Removing existing OPTIONS method..." -ForegroundColor Yellow
aws apigateway delete-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --region $REGION 2>$null
Start-Sleep -Seconds 2

# Step 2: Create OPTIONS method with NO authorization
Write-Host "2. Creating OPTIONS method (no auth)..." -ForegroundColor Yellow
aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION

# Step 3: Add MOCK integration
Write-Host "3. Adding MOCK integration..." -ForegroundColor Yellow
aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' `
    --region $REGION

# Step 4: Add method response
Write-Host "4. Adding method response..." -ForegroundColor Yellow
aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false `
    --region $REGION

# Step 5: Add integration response with CORS headers
Write-Host "5. Adding integration response with CORS headers..." -ForegroundColor Yellow
aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters method.response.header.Access-Control-Allow-Headers="'Content-Type,Authorization,X-Amz-Date,X-Api-Key'",method.response.header.Access-Control-Allow-Methods="'GET,POST,PUT,DELETE,OPTIONS'",method.response.header.Access-Control-Allow-Origin="'*'" `
    --region $REGION

Write-Host "✅ OPTIONS method configured" -ForegroundColor Green
Write-Host ""

# Step 6: Deploy API
Write-Host "6. Deploying API..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Fixed orders CORS" `
    --region $REGION

Write-Host "✅ API deployed" -ForegroundColor Green
Write-Host ""

# Step 7: Wait and test
Write-Host "7. Waiting for deployment to propagate..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "8. Testing OPTIONS..." -ForegroundColor Yellow
$response = curl -X OPTIONS https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/orders -i 2>&1 | Select-String "HTTP/1.1"
Write-Host $response

if ($response -match "200") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ CORS Fixed Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Orders endpoint is now ready." -ForegroundColor White
    Write-Host "Try creating an order from your app." -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️  Still getting errors. May need manual fix in AWS Console." -ForegroundColor Yellow
    Write-Host "Go to: https://ap-south-1.console.aws.amazon.com/apigateway/main/apis/vtqjfznspc/resources/eqsswe?api=vtqjfznspc&region=ap-south-1" -ForegroundColor Gray
}
