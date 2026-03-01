# Fix CORS OPTIONS responses for payment endpoints
# This script properly configures CORS for payment endpoints

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$STAGE = "dev"

Write-Host "Fixing CORS for Payment Endpoints..." -ForegroundColor Cyan

# Get payment endpoint resource IDs
$endpoints = @(
    @{Path = "create-razorpay-order"; Id = "q0fyeu"},
    @{Path = "verify-payment"; Id = "k8vet9"},
    @{Path = "create-cod-payment"; Id = "og3cat"},
    @{Path = "payment-status"; Id = "sf1wkp"}
)

foreach ($endpoint in $endpoints) {
    $resourceId = $endpoint.Id
    $pathName = $endpoint.Path
    
    Write-Host "`nFixing CORS for /$pathName..." -ForegroundColor Yellow
    
    # Delete existing OPTIONS method if it exists
    try {
        aws apigateway delete-method `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $resourceId `
            --http-method "OPTIONS" 2>$null
        Write-Host "Deleted existing OPTIONS method" -ForegroundColor Yellow
    } catch {
        # Method doesn't exist, continue
    }
    
    # Create OPTIONS method
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --region $REGION `
        --resource-id $resourceId `
        --http-method "OPTIONS" `
        --authorization-type "NONE" | Out-Null
    
    # Create mock integration
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --region $REGION `
        --resource-id $resourceId `
        --http-method "OPTIONS" `
        --type "MOCK" `
        --request-templates '{\"application/json\":\"{\\\"statusCode\\\": 200}\"}' | Out-Null
    
    # Create method response
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --region $REGION `
        --resource-id $resourceId `
        --http-method "OPTIONS" `
        --status-code "200" `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":false,\"method.response.header.Access-Control-Allow-Methods\":false,\"method.response.header.Access-Control-Allow-Origin\":false}' | Out-Null
    
    # Create integration response with proper CORS headers
    $responseParams = @{
        "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
        "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
        "method.response.header.Access-Control-Allow-Origin" = "'*'"
    } | ConvertTo-Json -Compress
    
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --region $REGION `
        --resource-id $resourceId `
        --http-method "OPTIONS" `
        --status-code "200" `
        --response-parameters $responseParams | Out-Null
    
    Write-Host "Fixed CORS for /$pathName" -ForegroundColor Green
}

# Deploy API
Write-Host "`nDeploying API to $STAGE stage..." -ForegroundColor Cyan
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --region $REGION `
    --stage-name $STAGE `
    --description "CORS fix for payment endpoints - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-Null

Write-Host "`n✅ CORS fixed for all payment endpoints!" -ForegroundColor Green
