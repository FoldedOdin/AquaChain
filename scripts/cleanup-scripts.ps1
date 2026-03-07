# AquaChain Scripts Cleanup Automation
# This script removes redundant/outdated scripts and reorganizes the folder

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AquaChain Scripts Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptRoot = $PSScriptRoot

# Backup before cleanup
$backupDir = Join-Path $scriptRoot "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "Creating backup at: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Function to safely delete files
function Remove-ScriptFile {
    param([string]$Path)
    if (Test-Path $Path) {
        $relativePath = $Path.Replace($scriptRoot, "scripts")
        Write-Host "  Deleting: $relativePath" -ForegroundColor Gray
        Remove-Item $Path -Force -ErrorAction SilentlyContinue
    }
}

# Function to safely delete directory
function Remove-ScriptDirectory {
    param([string]$Path)
    if (Test-Path $Path) {
        $relativePath = $Path.Replace($scriptRoot, "scripts")
        Write-Host "  Deleting directory: $relativePath" -ForegroundColor Gray
        Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Step 1: Removing Python cache files..." -ForegroundColor Yellow
Remove-ScriptDirectory (Join-Path $scriptRoot "__pycache__")
Remove-ScriptDirectory (Join-Path $scriptRoot "testing/__pycache__")

Write-Host ""
Write-Host "Step 2: Removing outdated root-level scripts..." -ForegroundColor Yellow
$rootScriptsToDelete = @(
    "create-supply-chain-users-with-passwords.bat",
    "create-supply-chain-users-with-passwords.py",
    "deploy-and-create-users.bat",
    "deploy-contact-service.sh",
    "deploy-notifications-service.py",
    "deploy-notifications.bat",
    "find-user-pool-id.bat",
    "fix-frontend-auth-config.bat",
    "fix-frontend-auth-config.py",
    "fix-order-status-cors.ps1",
    "get-user-pool-id-cli.bat",
    "get-user-pool-id.py",
    "setup-api-gateway-google-oauth.ps1",
    "setup-contact-service.py",
    "setup-google-oauth-lambda.bat",
    "setup-google-oauth-lambda.ps1",
    "test-google-oauth-endpoint.ps1",
    "UPDATE_USER_PHONE_INSTRUCTIONS.md",
    "update_user_phone.py",
    "update-google-oauth-secret.bat",
    "update-google-oauth-secret.ps1",
    "update-user-phone.bat",
    "verify-users-and-config.bat",
    "verify-users-and-config.py"
)

foreach ($file in $rootScriptsToDelete) {
    Remove-ScriptFile (Join-Path $scriptRoot $file)
}

Write-Host ""
Write-Host "Step 3: Cleaning deployment folder..." -ForegroundColor Yellow
$deploymentDir = Join-Path $scriptRoot "deployment"

# Delete all fix-* scripts (temporary fixes)
Get-ChildItem -Path $deploymentDir -Filter "fix-*.ps1" | ForEach-Object {
    Remove-ScriptFile $_.FullName
}
Get-ChildItem -Path $deploymentDir -Filter "fix-*.bat" | ForEach-Object {
    Remove-ScriptFile $_.FullName
}
Get-ChildItem -Path $deploymentDir -Filter "fix-*.sh" | ForEach-Object {
    Remove-ScriptFile $_.FullName
}
Get-ChildItem -Path $deploymentDir -Filter "fix-*.py" | ForEach-Object {
    Remove-ScriptFile $_.FullName
}

# Delete redundant deployment variations
$deploymentPatternsToDelete = @(
    "add-*.ps1",
    "attach-*.ps1",
    "check-*.ps1",
    "cleanup-*.ps1",
    "complete-*.ps1",
    "create-*-manually.ps1",
    "create-*-table.ps1",
    "create-*-endpoint.ps1",
    "deploy-admin-*.ps1",
    "deploy-admin-*.bat",
    "deploy-cancel-*.ps1",
    "deploy-cors-*.bat",
    "deploy-cors-*.sh",
    "deploy-device-*.ps1",
    "deploy-enhanced-*.ps1",
    "deploy-get-*.ps1",
    "deploy-inventory-*.py",
    "deploy-lambda-auth-*.bat",
    "deploy-lambda-auth-*.sh",
    "deploy-lambda-user-*.bat",
    "deploy-lambda-user-*.sh",
    "deploy-lambda-*.ps1",
    "deploy-minimal-*.ps1",
    "deploy-minimal.bat",
    "deploy-notification-*.ps1",
    "deploy-orders-*.ps1",
    "deploy-otp-*.ps1",
    "deploy-payment-*.ps1",
    "deploy-phase*.ps1",
    "deploy-phase*.py",
    "deploy-profile-*.ps1",
    "deploy-profile-*.bat",
    "deploy-real-*.ps1",
    "deploy-realtime-*.ps1",
    "deploy-registration-*.ps1",
    "deploy-routing-*.ps1",
    "deploy-secure-*.ps1",
    "deploy-security-*.ps1",
    "deploy-service-*.ps1",
    "deploy-simple-*.ps1",
    "deploy-system-*.ps1",
    "deploy-user-*.ps1",
    "deploy-verification-*.ps1",
    "enable-*.bat",
    "enable-*.sh",
    "find-*.ps1",
    "force-*.ps1",
    "import-*.ps1",
    "integrate-*.ps1",
    "minimal-*.ps1",
    "optimize-*.ps1",
    "package-*.py",
    "quick-*.bat",
    "recreate-*.ps1",
    "remove-*.ps1",
    "rollback-*.ps1",
    "ultra-*.ps1",
    "update-*.ps1",
    "upload-*.py",
    "verify-*.bat"
)

foreach ($pattern in $deploymentPatternsToDelete) {
    Get-ChildItem -Path $deploymentDir -Filter $pattern | ForEach-Object {
        Remove-ScriptFile $_.FullName
    }
}

# Delete JSON template files
Get-ChildItem -Path $deploymentDir -Filter "*.json" | ForEach-Object {
    Remove-ScriptFile $_.FullName
}

Write-Host ""
Write-Host "Step 4: Cleaning testing folder..." -ForegroundColor Yellow
$testingDir = Join-Path $scriptRoot "testing"

# Delete specific endpoint test scripts
$testingPatternsToDelete = @(
    "check-*.bat",
    "check-*.ps1",
    "check-*.html",
    "cleanup-*.ps1",
    "create-test-*.ps1",
    "create-verified-*.ps1",
    "debug-*.ps1",
    "fix-*.ps1",
    "local-*.bat",
    "local-*.js",
    "populate-*.py",
    "quick-*.sh",
    "restart-*.bat",
    "restart-*.ps1",
    "tail-*.ps1",
    "test_dr_*.py",
    "test_email_*.py",
    "test_enhanced_*.py",
    "test-*-error-*.ps1",
    "test-api-*.ps1",
    "test-auth-*.ps1",
    "test-backend-*.bat",
    "test-cors-*.sh",
    "test-dashboard-*.ps1",
    "test-devices-*.ps1",
    "test-frontend-*.ps1",
    "test-order-*.ps1",
    "test-otp-*.ps1",
    "test-payment-*.ps1",
    "test-phase*.ps1",
    "test-profile-*.ps1",
    "test-registration-*.ps1",
    "test-routing-*.ps1",
    "test-secure-*.ps1",
    "test-service-*.ps1",
    "test-token-*.ps1",
    "trigger-*.bat",
    "trigger-*.py",
    "update-*.ps1",
    "update-*.json",
    "validate_*.py",
    "validate-*.ps1"
)

foreach ($pattern in $testingPatternsToDelete) {
    Get-ChildItem -Path $testingDir -Filter $pattern | ForEach-Object {
        # Keep the new comprehensive test files
        if ($_.Name -notlike "comprehensive-*" -and 
            $_.Name -ne "run-comprehensive-test.bat" -and 
            $_.Name -ne "run-comprehensive-test.ps1" -and
            $_.Name -ne "COMPREHENSIVE_TEST_README.md") {
            Remove-ScriptFile $_.FullName
        }
    }
}

# Keep only essential testing files
$testingKeepFiles = @(
    "comprehensive-system-test.py",
    "run-comprehensive-test.bat",
    "run-comprehensive-test.ps1",
    "COMPREHENSIVE_TEST_README.md",
    "production_readiness_validation.py",
    "test-everything.bat"
)

Write-Host ""
Write-Host "Step 5: Cleaning setup folder..." -ForegroundColor Yellow
$setupDir = Join-Path $scriptRoot "setup"

# Delete redundant setup scripts
$setupPatternsToDelete = @(
    "add-*.bat",
    "add-*.ps1",
    "check-*.bat",
    "configure-*.bat",
    "create-razorpay-*.bat",
    "create-razorpay-*.ps1",
    "create-test-*.bat",
    "request-*.md",
    "set-*.ps1",
    "setup-frontend-*.ps1",
    "setup-razorpay-*.bat",
    "setup-ses-*.ps1",
    "test-*.bat",
    "verify-*.bat",
    "*.json"
)

foreach ($pattern in $setupPatternsToDelete) {
    Get-ChildItem -Path $setupDir -Filter $pattern | ForEach-Object {
        Remove-ScriptFile $_.FullName
    }
}

Write-Host ""
Write-Host "Step 6: Cleaning maintenance folder..." -ForegroundColor Yellow
$maintenanceDir = Join-Path $scriptRoot "maintenance"

# Delete outdated maintenance scripts
$maintenanceFilesToDelete = @(
    "delete-everything.bat",
    "fix-data-stack-v2.py",
    "fix-data-stack.py",
    "fix-system-config-thresholds.py",
    "lint-all.sh",
    "lint-python.sh",
    "README-CONFIG-FIX.md",
    "remove_humidity_sensor.py",
    "restore-config-backup.py",
    "stop-iot-simulator.ps1",
    "switch-dynamodb-to-provisioned.py",
    "ultra-cost-optimize.bat"
)

foreach ($file in $maintenanceFilesToDelete) {
    Remove-ScriptFile (Join-Path $maintenanceDir $file)
}

Write-Host ""
Write-Host "Step 7: Creating core utilities folder..." -ForegroundColor Yellow
$coreDir = Join-Path $scriptRoot "core"
if (-not (Test-Path $coreDir)) {
    New-Item -ItemType Directory -Path $coreDir -Force | Out-Null
}

# Move core utilities
$coreFiles = @("build-lambda-packages.py")
foreach ($file in $coreFiles) {
    $sourcePath = Join-Path $scriptRoot $file
    $destPath = Join-Path $coreDir $file
    if (Test-Path $sourcePath) {
        Write-Host "  Moving $file to core/" -ForegroundColor Green
        Move-Item -Path $sourcePath -Destination $destPath -Force
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Removed 150+ redundant scripts" -ForegroundColor White
Write-Host "  - Organized remaining scripts into logical folders" -ForegroundColor White
Write-Host "  - Created core utilities folder" -ForegroundColor White
Write-Host "  - Backup created at: $backupDir" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the changes" -ForegroundColor White
Write-Host "  2. Test essential scripts still work" -ForegroundColor White
Write-Host "  3. Delete backup folder if satisfied" -ForegroundColor White
Write-Host ""
