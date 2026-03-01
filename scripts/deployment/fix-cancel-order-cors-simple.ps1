# Fix CORS for DELETE /api/orders/{orderId} endpoint
# Simplified version using JSON files

$API_ID = "vtqjfznspc"
$RESOURCE_ID = "x0imdx"  # /api/orders/{orderId}
$REGION = "ap-south-1"
$STAGE = "dev"

Write-Host "Configuring CORS for DELETE /api/orders/{orderId}..." -ForegroundColor Cyan

# Create temporary JSON files
$requestTemplates = @'
{
  "application/json": "{\"statusCode\": 200}"
}
'@

$responseParameters = @'
{
  "method.response.header.Access-Control-Allow-Headers": false,
  "method.response.header.Access-Control-Allow-Methods": false,
  "method.response.header.Access-Control-Allow-Origin": false
}
'@

$integrationResponseParams = @'
{
  "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization'",
  "method.response.header.Access-Control-Allow-Methods": "'DELETE,OPTIONS'",
  "method.response.header.Access-Control-Allow-Origin": "'*'"
}
'@

$requestTemplates | Out-File -FilePath "temp-request-templates.json" -Encoding utf8
$responseParameters | Out-File -FilePath "temp-response-params.json" -Encoding utf8
$integrationResponseParams | Out-File -FilePath "temp-integration-response.json" -Encoding utf8

try {
    # Step 1: Create OPTIONS method
    Write-Host "`nStep 1: Creating OPTIONS method..." -ForegroundColor Yellow
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION `
        --no-api-key-required 2>$null
    Write-Host "OPTIONS method created" -ForegroundColor Green

    # Step 2: Set up MOCK integration
    Write-Host "`nStep 2: Setting up MOCK integration..." -ForegroundColor Yellow
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates file://temp-request-templates.json `
        --region $REGION

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to configure MOCK integration"
    }
    Write-Host "MOCK integration configured" -ForegroundColor Green

    # Step 3: Delete existing method response and recreate
    Write-Host "`nStep 3: Setting up method response..." -ForegroundColor Yellow
    aws apigateway delete-method-response `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --status-code 200 `
        --region $REGION 2>$null
    
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters file://temp-response-params.json `
        --region $REGION

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to configure method response"
    }
    Write-Host "Method response configured" -ForegroundColor Green

    # Step 4: Delete existing integration response and recreate with CORS headers
    Write-Host "`nStep 4: Setting up integration response with CORS headers..." -ForegroundColor Yellow
    aws apigateway delete-integration-response `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --status-code 200 `
        --region $REGION 2>$null
    
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --resource-id $RESOURCE_ID `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters file://temp-integration-response.json `
        --region $REGION

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to configure integration response"
    }
    Write-Host "Integration response configured" -ForegroundColor Green

    # Step 5: Deploy API
    Write-Host "`nStep 5: Deploying API to dev stage..." -ForegroundColor Yellow
    aws apigateway create-deployment `
        --rest-api-id $API_ID `
        --stage-name $STAGE `
        --description "Fix CORS for order cancellation" `
        --region $REGION

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to deploy API"
    }

    Write-Host "`n=== CORS Configuration Complete ===" -ForegroundColor Green
    Write-Host "Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/api/orders/{orderId}" -ForegroundColor Cyan
    Write-Host "`nYou can now test order cancellation from the frontend!" -ForegroundColor Green

} catch {
    Write-Host "`nError: $_" -ForegroundColor Red
    exit 1
} finally {
    # Clean up temporary files
    Remove-Item -Path "temp-request-templates.json" -ErrorAction SilentlyContinue
    Remove-Item -Path "temp-response-params.json" -ErrorAction SilentlyContinue
    Remove-Item -Path "temp-integration-response.json" -ErrorAction SilentlyContinue
}
