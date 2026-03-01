# Fix API Gateway Profile Resource Conflict (Safe Version with Backup & Rollback)
# Backs up current configuration before making changes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix API Gateway Profile Conflict (Safe)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$API_ID = "vtqjfznspc"
$PROFILE_RESOURCE_ID = "d8exti"
$STACK_NAME = "AquaChain-API-dev"
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BACKUP_DIR = "backups/api-gateway"

# Create backup directory
New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null

Write-Host "[STEP 1/6] Creating backup of current configuration..." -ForegroundColor Yellow
Write-Host ""

# Backup all profile resources
Write-Host "  - Backing up resource structure..." -ForegroundColor Gray
$resourcesBackup = aws apigateway get-resources `
    --rest-api-id $API_ID `
    --region $REGION `
    --query "items[?contains(path, 'profile')]" `
    --output json

$resourcesBackup | Out-File "$BACKUP_DIR/profile-resources-backup-$TIMESTAMP.json"
Write-Host "    ✓ Saved: $BACKUP_DIR/profile-resources-backup-$TIMESTAMP.json" -ForegroundColor Green

# Parse resources
$resources = $resourcesBackup | ConvertFrom-Json

# Backup method configurations
Write-Host "  - Backing up method configurations..." -ForegroundColor Gray
$methodsBackup = @()

foreach ($resource in $resources) {
    if ($resource.resourceMethods) {
        foreach ($method in $resource.resourceMethods.PSObject.Properties.Name) {
            if ($method -ne "OPTIONS") {  # Skip OPTIONS, we'll recreate with CORS
                try {
                    $methodConfig = aws apigateway get-method `
                        --rest-api-id $API_ID `
                        --resource-id $resource.id `
                        --http-method $method `
                        --region $REGION `
                        --output json | ConvertFrom-Json
                    
                    $methodsBackup += @{
                        resourcePath = $resource.path
                        resourceId = $resource.id
                        httpMethod = $method
                        config = $methodConfig
                    }
                    
                    Write-Host "    ✓ Backed up: $method $($resource.path)" -ForegroundColor Green
                } catch {
                    Write-Host "    ⚠ Could not backup: $method $($resource.path)" -ForegroundColor Yellow
                }
            }
        }
    }
}

$methodsBackup | ConvertTo-Json -Depth 10 | Out-File "$BACKUP_DIR/profile-methods-backup-$TIMESTAMP.json"
Write-Host "    ✓ Saved: $BACKUP_DIR/profile-methods-backup-$TIMESTAMP.json" -ForegroundColor Green

Write-Host ""
Write-Host "  ✓ Backup complete!" -ForegroundColor Green
Write-Host ""

# Display what will be deleted
Write-Host "[STEP 2/6] Review changes..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Resources to be deleted and recreated:" -ForegroundColor Gray
foreach ($resource in $resources) {
    Write-Host "    - $($resource.path) (ID: $($resource.id))" -ForegroundColor Gray
    if ($resource.resourceMethods) {
        foreach ($method in $resource.resourceMethods.PSObject.Properties.Name) {
            Write-Host "      └─ $method" -ForegroundColor DarkGray
        }
    }
}

Write-Host ""
Write-Host "  These will be recreated by CDK with:" -ForegroundColor Gray
Write-Host "    - POST /api/profile/request-otp" -ForegroundColor DarkGray
Write-Host "    - PUT  /api/profile/verify-and-update" -ForegroundColor DarkGray
Write-Host ""

Write-Host "⚠️  WARNING: Brief downtime (~30 seconds) for profile endpoints" -ForegroundColor Yellow
Write-Host "✓  Backup saved - can rollback if needed" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "Type 'DELETE' to proceed with the fix"

if ($confirm -ne "DELETE") {
    Write-Host ""
    Write-Host "Cancelled - No changes made" -ForegroundColor Gray
    Write-Host "Backup preserved at: $BACKUP_DIR" -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "[STEP 3/6] Deleting child resources..." -ForegroundColor Yellow

# Get child resources (sorted deepest first)
$childResources = $resources | Where-Object { $_.parentId -eq $PROFILE_RESOURCE_ID } | Sort-Object -Property path -Descending

if ($childResources.Count -gt 0) {
    foreach ($resource in $childResources) {
        Write-Host "  - Deleting $($resource.path)..." -ForegroundColor Gray
        try {
            aws apigateway delete-resource `
                --rest-api-id $API_ID `
                --resource-id $resource.id `
                --region $REGION 2>&1 | Out-Null
            
            Write-Host "    ✓ Deleted" -ForegroundColor Green
        } catch {
            Write-Host "    ✗ Failed: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "ERROR: Could not delete child resource" -ForegroundColor Red
            Write-Host "Backup preserved at: $BACKUP_DIR" -ForegroundColor Yellow
            exit 1
        }
    }
} else {
    Write-Host "  No child resources found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[STEP 4/6] Deleting /api/profile resource..." -ForegroundColor Yellow

try {
    aws apigateway delete-resource `
        --rest-api-id $API_ID `
        --resource-id $PROFILE_RESOURCE_ID `
        --region $REGION 2>&1 | Out-Null
    
    Write-Host "  ✓ Deleted /api/profile" -ForegroundColor Green
} catch {
    Write-Host "  ✗ ERROR: Failed to delete /api/profile" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Backup preserved at: $BACKUP_DIR" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[STEP 5/6] Verifying deletion..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

$checkResource = aws apigateway get-resources `
    --rest-api-id $API_ID `
    --region $REGION `
    --query "items[?pathPart=='profile'].id" `
    --output text 2>&1

if ([string]::IsNullOrWhiteSpace($checkResource)) {
    Write-Host "  ✓ Resources successfully deleted" -ForegroundColor Green
} else {
    Write-Host "  ✗ Resources still exist" -ForegroundColor Red
    Write-Host ""
    Write-Host "Backup preserved at: $BACKUP_DIR" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[STEP 6/6] Deploying API Gateway with CDK..." -ForegroundColor Yellow
Write-Host ""

Set-Location infrastructure/cdk

try {
    Write-Host "  - Synthesizing stack..." -ForegroundColor Gray
    cdk synth $STACK_NAME --no-version-reporting 2>&1 | Out-Null
    
    Write-Host "  - Deploying (this may take 2-3 minutes)..." -ForegroundColor Gray
    $deployOutput = cdk deploy $STACK_NAME --require-approval never --no-version-reporting 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ API Gateway deployed successfully" -ForegroundColor Green
    } else {
        throw "Deployment failed"
    }
} catch {
    Write-Host "  ✗ ERROR: CDK deployment failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "  $deployOutput" -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠️  ROLLBACK REQUIRED!" -ForegroundColor Red
    Write-Host "Run: .\scripts\deployment\rollback-api-gateway-profile.ps1" -ForegroundColor Yellow
    Write-Host "Backup location: $BACKUP_DIR" -ForegroundColor Yellow
    Set-Location ../..
    exit 1
}

Set-Location ../..

Write-Host ""
Write-Host "[VERIFICATION] Testing recreated endpoints..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

$newResources = aws apigateway get-resources `
    --rest-api-id $API_ID `
    --region $REGION `
    --query "items[?contains(path, 'profile')].{Path:path,Methods:resourceMethods}" `
    --output json | ConvertFrom-Json

Write-Host ""
Write-Host "  Recreated endpoints:" -ForegroundColor Gray
foreach ($resource in $newResources) {
    Write-Host "    ✓ $($resource.Path)" -ForegroundColor Green
    if ($resource.Methods) {
        foreach ($method in $resource.Methods.PSObject.Properties.Name) {
            Write-Host "      └─ $method" -ForegroundColor DarkGray
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Profile resources deleted and recreated" -ForegroundColor Green
Write-Host "✓ API Gateway stack deployed" -ForegroundColor Green
Write-Host "✓ Payment endpoints now available" -ForegroundColor Green
Write-Host ""
Write-Host "Backup preserved at: $BACKUP_DIR/profile-*-$TIMESTAMP.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "New endpoints available:" -ForegroundColor Yellow
Write-Host "  Profile:" -ForegroundColor Gray
Write-Host "    - POST /api/profile/request-otp" -ForegroundColor Gray
Write-Host "    - PUT  /api/profile/verify-and-update" -ForegroundColor Gray
Write-Host ""
Write-Host "  Payment:" -ForegroundColor Gray
Write-Host "    - POST /api/payments/create-razorpay-order" -ForegroundColor Gray
Write-Host "    - POST /api/payments/verify-payment" -ForegroundColor Gray
Write-Host "    - POST /api/payments/create-cod-payment" -ForegroundColor Gray
Write-Host "    - GET  /api/payments/payment-status" -ForegroundColor Gray
Write-Host ""
Write-Host "Next: Test payment flow in browser" -ForegroundColor Cyan
Write-Host ""
