# Fix CORS for /api/auth/register endpoint
# This script ensures OPTIONS method returns 200 with proper CORS headers

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$STAGE = "dev"

Write-Host "Fixing CORS for /api/auth/register endpoint..." -ForegroundColor Cyan

# Get all resources
Write-Host "`nFetching API resources..." -ForegroundColor Yellow
$resources = aws apigateway get-resources --rest-api-id $API_ID --region $REGION | ConvertFrom-Json

# Find the register resource
$registerResource = $resources.items | Where-Object { $_.path -eq "/api/auth/register" }

if (-not $registerResource) {
    Write-Host "ERROR: /api/auth/register resource not found!" -ForegroundColor Red
    exit 1
}

$resourceId = $registerResource.id
Write-Host "Found register resource: $resourceId" -ForegroundColor Green

# Check if OPTIONS method exists
Write-Host "`nChecking OPTIONS method..." -ForegroundColor Yellow
try {
    $optionsMethod = aws apigateway get-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --region $REGION 2>$null | ConvertFrom-Json
    
    Write-Host "OPTIONS method exists, will update it" -ForegroundColor Yellow
    
    # Delete existing OPTIONS method
    aws apigateway delete-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --region $REGION | Out-Null
    
    Write-Host "Deleted existing OPTIONS method" -ForegroundColor Yellow
} catch {
    Write-Host "OPTIONS method doesn't exist, will create it" -ForegroundColor Yellow
}

# Create OPTIONS method with MOCK integration
Write-Host "`nCreating OPTIONS method..." -ForegroundColor Yellow

# 1. Create the method
aws apigateway put-method `
    --rest-api-id $API_ID `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --authorization-type NONE `
    --region $REGION | Out-Null

Write-Host "Created OPTIONS method" -ForegroundColor Green

# 2. Create MOCK integration
$requestTemplates = @{
    "application/json" = '{"statusCode": 200}'
} | ConvertTo-Json -Compress

aws apigateway put-integration `
    --rest-api-id $API_ID `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --type MOCK `
    --request-templates $requestTemplates `
    --region $REGION | Out-Null

Write-Host "Created MOCK integration" -ForegroundColor Green

# 3. Create method response
$methodResponseParams = @{
    "method.response.header.Access-Control-Allow-Headers" = $false
    "method.response.header.Access-Control-Allow-Methods" = $false
    "method.response.header.Access-Control-Allow-Origin" = $false
} | ConvertTo-Json -Compress

aws apigateway put-method-response `
    --rest-api-id $API_ID `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters $methodResponseParams `
    --region $REGION | Out-Null

Write-Host "Created method response" -ForegroundColor Green

# 4. Create integration response with CORS headers
$integrationResponseParams = @{
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
} | ConvertTo-Json -Compress

aws apigateway put-integration-response `
    --rest-api-id $API_ID `
    --resource-id $resourceId `
    --http-method OPTIONS `
    --status-code 200 `
    --response-parameters $integrationResponseParams `
    --region $REGION | Out-Null

Write-Host "Created integration response with CORS headers" -ForegroundColor Green

# Deploy the changes
Write-Host "`nDeploying changes to $STAGE stage..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name $STAGE `
    --description "Fix CORS for register endpoint" `
    --region $REGION | Out-Null

Write-Host "`n✓ CORS configuration fixed successfully!" -ForegroundColor Green
Write-Host "`nEndpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/api/auth/register" -ForegroundColor Cyan
Write-Host "`nTest with:" -ForegroundColor Yellow
Write-Host "curl -X OPTIONS https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/api/auth/register -v" -ForegroundColor White
