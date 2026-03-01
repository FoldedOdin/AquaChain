# API Gateway Configuration Update Script
# Adds new routes for System Configuration Phase 1
# Date: February 26, 2026

$ErrorActionPreference = "Stop"

# Configuration
$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$LAMBDA_ARN = "arn:aws:lambda:ap-south-1:758346259059:function:aquachain-function-admin-service-dev"
$CONFIG_RESOURCE_ID = "fqiwpd"  # /api/admin/system/configuration

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "API Gateway Configuration Update" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API ID: $API_ID" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "Parent Resource: /api/admin/system/configuration" -ForegroundColor Yellow
Write-Host ""

# Function to create resource
function Create-ApiResource {
    param(
        [string]$ParentId,
        [string]$PathPart,
        [string]$Description
    )
    
    Write-Host "Creating resource: $PathPart..." -ForegroundColor Green
    
    try {
        $result = aws apigateway create-resource `
            --rest-api-id $API_ID `
            --parent-id $ParentId `
            --path-part $PathPart `
            --region $REGION `
            --output json | ConvertFrom-Json
        
        Write-Host "  ✓ Resource created: $($result.id)" -ForegroundColor Green
        return $result.id
    }
    catch {
        Write-Host "  ✗ Failed to create resource: $_" -ForegroundColor Red
        throw
    }
}

# Function to add method
function Add-ApiMethod {
    param(
        [string]$ResourceId,
        [string]$HttpMethod,
        [string]$Description
    )
    
    Write-Host "  Adding $HttpMethod method..." -ForegroundColor Cyan
    
    try {
        aws apigateway put-method `
            --rest-api-id $API_ID `
            --resource-id $ResourceId `
            --http-method $HttpMethod `
            --authorization-type "COGNITO_USER_POOLS" `
            --authorizer-id "xxxxxx" `
            --region $REGION `
            --output json | Out-Null
        
        Write-Host "    ✓ Method added" -ForegroundColor Green
    }
    catch {
        Write-Host "    ✗ Failed to add method: $_" -ForegroundColor Red
        throw
    }
}

# Function to add Lambda integration
function Add-LambdaIntegration {
    param(
        [string]$ResourceId,
        [string]$HttpMethod
    )
    
    Write-Host "  Adding Lambda integration..." -ForegroundColor Cyan
    
    try {
        aws apigateway put-integration `
            --rest-api-id $API_ID `
            --resource-id $ResourceId `
            --http-method $HttpMethod `
            --type AWS_PROXY `
            --integration-http-method POST `
            --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" `
            --region $REGION `
            --output json | Out-Null
        
        Write-Host "    ✓ Integration added" -ForegroundColor Green
    }
    catch {
        Write-Host "    ✗ Failed to add integration: $_" -ForegroundColor Red
        throw
    }
}

# Function to enable CORS
function Enable-Cors {
    param(
        [string]$ResourceId
    )
    
    Write-Host "  Enabling CORS..." -ForegroundColor Cyan
    
    try {
        # Add OPTIONS method
        aws apigateway put-method `
            --rest-api-id $API_ID `
            --resource-id $ResourceId `
            --http-method OPTIONS `
            --authorization-type NONE `
            --region $REGION `
            --output json | Out-Null
        
        # Add mock integration for OPTIONS
        aws apigateway put-integration `
            --rest-api-id $API_ID `
            --resource-id $ResourceId `
            --http-method OPTIONS `
            --type MOCK `
            --request-templates '{"application/json":"{\"statusCode\": 200}"}' `
            --region $REGION `
            --output json | Out-Null
        
        # Add integration response
        aws apigateway put-integration-response `
            --rest-api-id $API_ID `
            --resource-id $ResourceId `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters '{
                "method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,Authorization'"'"'",
                "method.response.header.Access-Control-Allow-Methods": "'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'",
                "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"
            }' `
            --region $REGION `
            --output json | Out-Null
        
        # Add method response
        aws apigateway put-method-response `
            --rest-api-id $API_ID `
            --resource-id $ResourceId `
            --http-method OPTIONS `
            --status-code 200 `
            --response-parameters '{
                "method.response.header.Access-Control-Allow-Headers": true,
                "method.response.header.Access-Control-Allow-Methods": true,
                "method.response.header.Access-Control-Allow-Origin": true
            }' `
            --region $REGION `
            --output json | Out-Null
        
        Write-Host "    ✓ CORS enabled" -ForegroundColor Green
    }
    catch {
        Write-Host "    ✗ Failed to enable CORS: $_" -ForegroundColor Red
        throw
    }
}

# Main execution
try {
    Write-Host "Step 1: Creating /history resource" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    $historyResourceId = Create-ApiResource -ParentId $CONFIG_RESOURCE_ID -PathPart "history" -Description "Configuration history endpoint"
    Add-ApiMethod -ResourceId $historyResourceId -HttpMethod "GET" -Description "Get configuration history"
    Add-LambdaIntegration -ResourceId $historyResourceId -HttpMethod "GET"
    Enable-Cors -ResourceId $historyResourceId
    Write-Host ""
    
    Write-Host "Step 2: Creating /validate resource" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    $validateResourceId = Create-ApiResource -ParentId $CONFIG_RESOURCE_ID -PathPart "validate" -Description "Validate configuration endpoint"
    Add-ApiMethod -ResourceId $validateResourceId -HttpMethod "POST" -Description "Validate configuration"
    Add-LambdaIntegration -ResourceId $validateResourceId -HttpMethod "POST"
    Enable-Cors -ResourceId $validateResourceId
    Write-Host ""
    
    Write-Host "Step 3: Creating /rollback resource" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    $rollbackResourceId = Create-ApiResource -ParentId $CONFIG_RESOURCE_ID -PathPart "rollback" -Description "Rollback configuration endpoint"
    Add-ApiMethod -ResourceId $rollbackResourceId -HttpMethod "POST" -Description "Rollback configuration"
    Add-LambdaIntegration -ResourceId $rollbackResourceId -HttpMethod "POST"
    Enable-Cors -ResourceId $rollbackResourceId
    Write-Host ""
    
    Write-Host "Step 4: Deploying API Gateway" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "Deploying to dev stage..." -ForegroundColor Cyan
    
    $deployment = aws apigateway create-deployment `
        --rest-api-id $API_ID `
        --stage-name dev `
        --description "Phase 1: System Config Security & Audit features" `
        --region $REGION `
        --output json | ConvertFrom-Json
    
    Write-Host "  ✓ Deployment ID: $($deployment.id)" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✓ API Gateway configuration completed successfully!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "New endpoints available:" -ForegroundColor Yellow
    Write-Host "  GET  https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/admin/system/configuration/history" -ForegroundColor Cyan
    Write-Host "  POST https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/admin/system/configuration/validate" -ForegroundColor Cyan
    Write-Host "  POST https://$API_ID.execute-api.$REGION.amazonaws.com/dev/api/admin/system/configuration/rollback" -ForegroundColor Cyan
    Write-Host ""
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "✗ API Gateway configuration failed!" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Rollback: Resources may have been partially created." -ForegroundColor Yellow
    Write-Host "Check API Gateway console to verify state." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
