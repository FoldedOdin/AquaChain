# Fix CORS for PUT /api/profile/update endpoint
# Add PUT to Access-Control-Allow-Methods

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$RESOURCE_ID = "c84ane"  # /api/profile/update

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix Profile Update CORS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Updating CORS headers for /api/profile/update..." -ForegroundColor Yellow

# Update integration response to include PUT method
$integrationResponseParams = @{
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
}
$integrationResponseParams | ConvertTo-Json -Compress | Out-File -FilePath "temp-cors-params.json" -Encoding utf8

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $RESOURCE_ID `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters file://temp-cors-params.json `
    --region $REGION | Out-Null

Remove-Item "temp-cors-params.json" -Force

Write-Host "✓ CORS headers updated" -ForegroundColor Green

# Deploy changes
Write-Host ""
Write-Host "Deploying to dev stage..." -ForegroundColor Yellow

$deployment = aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Fix CORS for PUT /api/profile/update" `
    --region $REGION | ConvertFrom-Json

Write-Host "✓ Deployed (ID: $($deployment.id))" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ CORS Fix Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Profile update should now work without CORS errors." -ForegroundColor Cyan
