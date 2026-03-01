# Cleanup Manually Created Payment Endpoints
# This script removes payment endpoints that were created via AWS CLI
# so they can be properly managed by CDK

$ErrorActionPreference = "Stop"

$API_ID = "vtqjfznspc"
$REGION = "ap-south-1"
$STAGE = "dev"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Cleanup Manual Payment Endpoints" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Function to delete a resource and all its children
function Remove-ApiResource {
    param(
        [string]$ResourceId,
        [string]$Path
    )
    
    Write-Host "Deleting resource: $Path (ID: $ResourceId)" -ForegroundColor Yellow
    
    try {
        aws apigateway delete-resource `
            --rest-api-id $API_ID `
            --region $REGION `
            --resource-id $ResourceId 2>&1 | Out-Null
        
        Write-Host "  ✓ Deleted: $Path" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ✗ Failed to delete: $Path" -ForegroundColor Red
        Write-Host "    Error: $_" -ForegroundColor Red
        return $false
    }
}

# Get all resources
Write-Host "Fetching API Gateway resources..." -ForegroundColor Cyan
$resources = aws apigateway get-resources `
    --rest-api-id $API_ID `
    --region $REGION `
    --output json | ConvertFrom-Json

# Find payment-related resources
$paymentResources = $resources.items | Where-Object { $_.path -like '/api/payments*' } | Sort-Object -Property @{Expression={$_.path.Length}; Descending=$true}

if ($paymentResources.Count -eq 0) {
    Write-Host ""
    Write-Host "No payment endpoints found. They may have already been deleted." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "Found $($paymentResources.Count) payment-related resources:" -ForegroundColor Cyan
foreach ($resource in $paymentResources) {
    Write-Host "  - $($resource.path) (ID: $($resource.id))" -ForegroundColor White
}
Write-Host ""

# Confirm deletion
Write-Host "⚠️  WARNING: This will delete all payment endpoints!" -ForegroundColor Yellow
Write-Host "   They will be recreated by CDK deployment." -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Do you want to continue? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host ""
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "Deleting payment endpoints..." -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0
$failedCount = 0

# Delete resources (children first, then parent)
foreach ($resource in $paymentResources) {
    if (Remove-ApiResource -ResourceId $resource.id -Path $resource.path) {
        $deletedCount++
    } else {
        $failedCount++
    }
    Start-Sleep -Milliseconds 500  # Rate limiting
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Cleanup Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Deleted: $deletedCount resources" -ForegroundColor Green
Write-Host "  Failed:  $failedCount resources" -ForegroundColor $(if ($failedCount -gt 0) { "Red" } else { "Green" })
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if ($failedCount -eq 0) {
    Write-Host "✅ All payment endpoints deleted successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Deploy API stack via CDK:" -ForegroundColor White
    Write-Host "     cd infrastructure/cdk" -ForegroundColor Gray
    Write-Host "     cdk deploy AquaChain-API-dev --require-approval never --region ap-south-1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Verify endpoints are working:" -ForegroundColor White
    Write-Host "     cd scripts/testing" -ForegroundColor Gray
    Write-Host "     ./test-payment-endpoints-integration.ps1" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "⚠️  Some resources failed to delete." -ForegroundColor Yellow
    Write-Host "   You may need to delete them manually via AWS Console." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   AWS Console URL:" -ForegroundColor Cyan
    Write-Host "   https://ap-south-1.console.aws.amazon.com/apigateway/main/apis/$API_ID/resources" -ForegroundColor Gray
    Write-Host ""
}
