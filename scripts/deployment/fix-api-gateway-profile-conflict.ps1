# Fix API Gateway Profile Resource Conflict
# Removes duplicate /api/profile resource and redeploys API Gateway

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix API Gateway Profile Conflict" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$API_ID = "vtqjfznspc"
$PROFILE_RESOURCE_ID = "d8exti"
$STACK_NAME = "AquaChain-API-dev"

Write-Host "⚠️  WARNING: This will delete the existing /api/profile resource" -ForegroundColor Yellow
Write-Host "   The CDK will recreate it with proper configuration" -ForegroundColor Gray
Write-Host ""
Write-Host "Current state:" -ForegroundColor Yellow
Write-Host "  - API Gateway ID: $API_ID" -ForegroundColor Gray
Write-Host "  - Profile Resource ID: $PROFILE_RESOURCE_ID" -ForegroundColor Gray
Write-Host "  - Stack Status: UPDATE_ROLLBACK_COMPLETE" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Type 'DELETE' to proceed with removing the duplicate resource"

if ($confirm -ne "DELETE") {
    Write-Host "Cancelled" -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "[1/4] Checking for child resources..." -ForegroundColor Yellow

# Get all child resources of /api/profile
$childResources = aws apigateway get-resources `
    --rest-api-id $API_ID `
    --region $REGION `
    --query "items[?parentId=='$PROFILE_RESOURCE_ID'].{Id:id,Path:path}" `
    --output json | ConvertFrom-Json

if ($childResources.Count -gt 0) {
    Write-Host "  Found $($childResources.Count) child resources:" -ForegroundColor Gray
    foreach ($resource in $childResources) {
        Write-Host "    - $($resource.Path) (ID: $($resource.Id))" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  Deleting child resources first..." -ForegroundColor Yellow
    
    # Delete child resources in reverse order (deepest first)
    $sortedChildren = $childResources | Sort-Object -Property Path -Descending
    foreach ($resource in $sortedChildren) {
        Write-Host "    Deleting $($resource.Path)..." -ForegroundColor Gray
        aws apigateway delete-resource `
            --rest-api-id $API_ID `
            --resource-id $resource.Id `
            --region $REGION 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Deleted $($resource.Path)" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Failed to delete $($resource.Path)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  No child resources found" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/4] Deleting /api/profile resource..." -ForegroundColor Yellow

try {
    aws apigateway delete-resource `
        --rest-api-id $API_ID `
        --resource-id $PROFILE_RESOURCE_ID `
        --region $REGION 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Deleted /api/profile resource" -ForegroundColor Green
    } else {
        throw "Failed to delete resource"
    }
} catch {
    Write-Host "  ✗ ERROR: Failed to delete /api/profile resource" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] Verifying deletion..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

$checkResource = aws apigateway get-resources `
    --rest-api-id $API_ID `
    --region $REGION `
    --query "items[?pathPart=='profile'].id" `
    --output text 2>&1

if ([string]::IsNullOrWhiteSpace($checkResource)) {
    Write-Host "  ✓ Resource successfully deleted" -ForegroundColor Green
} else {
    Write-Host "  ✗ Resource still exists" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] Deploying API Gateway stack..." -ForegroundColor Yellow

Set-Location infrastructure/cdk

try {
    Write-Host "  - Synthesizing stack..." -ForegroundColor Gray
    cdk synth $STACK_NAME --no-version-reporting 2>&1 | Out-Null
    
    Write-Host "  - Deploying..." -ForegroundColor Gray
    cdk deploy $STACK_NAME --require-approval never --no-version-reporting
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ API Gateway deployed successfully" -ForegroundColor Green
    } else {
        throw "Deployment failed"
    }
} catch {
    Write-Host "  ✗ ERROR: Deployment failed" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Set-Location ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Duplicate /api/profile resource removed" -ForegroundColor Green
Write-Host "✓ API Gateway stack deployed" -ForegroundColor Green
Write-Host "✓ Payment endpoints now available" -ForegroundColor Green
Write-Host ""
Write-Host "Payment endpoints:" -ForegroundColor Yellow
Write-Host "  - POST /api/payments/create-razorpay-order" -ForegroundColor Gray
Write-Host "  - POST /api/payments/verify-payment" -ForegroundColor Gray
Write-Host "  - POST /api/payments/create-cod-payment" -ForegroundColor Gray
Write-Host "  - GET  /api/payments/payment-status" -ForegroundColor Gray
Write-Host ""
Write-Host "Profile endpoints (recreated):" -ForegroundColor Yellow
Write-Host "  - POST /api/profile/request-otp" -ForegroundColor Gray
Write-Host "  - PUT  /api/profile/verify-and-update" -ForegroundColor Gray
Write-Host ""
Write-Host "Next: Test payment flow in browser" -ForegroundColor Cyan
Write-Host ""
