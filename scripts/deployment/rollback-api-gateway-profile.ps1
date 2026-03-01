# Rollback API Gateway Profile Resources
# Restores profile endpoints from backup if deployment fails

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rollback API Gateway Profile Resources" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$API_ID = "vtqjfznspc"
$BACKUP_DIR = "backups/api-gateway"

Write-Host "⚠️  WARNING: This will attempt to restore profile endpoints from backup" -ForegroundColor Yellow
Write-Host ""

# Find most recent backup
$backupFiles = Get-ChildItem -Path $BACKUP_DIR -Filter "profile-resources-backup-*.json" | Sort-Object LastWriteTime -Descending

if ($backupFiles.Count -eq 0) {
    Write-Host "✗ ERROR: No backup files found in $BACKUP_DIR" -ForegroundColor Red
    exit 1
}

$latestBackup = $backupFiles[0]
$timestamp = $latestBackup.Name -replace 'profile-resources-backup-', '' -replace '.json', ''

Write-Host "Found backup from: $timestamp" -ForegroundColor Green
Write-Host "  - Resources: $BACKUP_DIR/profile-resources-backup-$timestamp.json" -ForegroundColor Gray
Write-Host "  - Methods: $BACKUP_DIR/profile-methods-backup-$timestamp.json" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Type 'ROLLBACK' to restore from this backup"

if ($confirm -ne "ROLLBACK") {
    Write-Host "Cancelled" -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "⚠️  IMPORTANT: Rollback Limitations" -ForegroundColor Yellow
Write-Host ""
Write-Host "API Gateway resources cannot be restored with exact same IDs." -ForegroundColor Yellow
Write-Host "This script will:" -ForegroundColor Gray
Write-Host "  1. Show you what was backed up" -ForegroundColor Gray
Write-Host "  2. Provide manual restoration commands" -ForegroundColor Gray
Write-Host "  3. Recommend using CDK to fix the issue properly" -ForegroundColor Gray
Write-Host ""

# Load backup
$resourcesBackup = Get-Content "$BACKUP_DIR/profile-resources-backup-$timestamp.json" | ConvertFrom-Json
$methodsBackup = Get-Content "$BACKUP_DIR/profile-methods-backup-$timestamp.json" | ConvertFrom-Json

Write-Host "[BACKUP CONTENTS]" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resources that were deleted:" -ForegroundColor Yellow
foreach ($resource in $resourcesBackup) {
    Write-Host "  - $($resource.path) (ID: $($resource.id))" -ForegroundColor Gray
    if ($resource.resourceMethods) {
        foreach ($method in $resource.resourceMethods.PSObject.Properties.Name) {
            Write-Host "    └─ $method" -ForegroundColor DarkGray
        }
    }
}

Write-Host ""
Write-Host "[RECOMMENDED ACTION]" -ForegroundColor Cyan
Write-Host ""
Write-Host "The best way to restore functionality is to:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Fix the CDK deployment issue that caused the rollback" -ForegroundColor Gray
Write-Host "2. Run the deployment again with the fix" -ForegroundColor Gray
Write-Host "3. CDK will recreate the resources properly" -ForegroundColor Gray
Write-Host ""
Write-Host "OR" -ForegroundColor Yellow
Write-Host ""
Write-Host "If you need immediate restoration, manually recreate via AWS Console:" -ForegroundColor Gray
Write-Host ""
Write-Host "AWS Console Steps:" -ForegroundColor Cyan
Write-Host "1. Go to API Gateway console" -ForegroundColor Gray
Write-Host "2. Select API: aquachain-api-rest-dev (ID: $API_ID)" -ForegroundColor Gray
Write-Host "3. Find /api resource" -ForegroundColor Gray
Write-Host "4. Create child resource 'profile'" -ForegroundColor Gray
Write-Host "5. Under /api/profile, create:" -ForegroundColor Gray
Write-Host "   - Child resource 'request-otp' with POST method" -ForegroundColor Gray
Write-Host "   - Child resource 'verify-and-update' with PUT method" -ForegroundColor Gray
Write-Host "   - Child resource 'update' with GET and PUT methods" -ForegroundColor Gray
Write-Host "6. For each method:" -ForegroundColor Gray
Write-Host "   - Integration type: Lambda Function" -ForegroundColor Gray
Write-Host "   - Lambda: aquachain-function-user-management-dev" -ForegroundColor Gray
Write-Host "   - Use Lambda Proxy integration: Yes" -ForegroundColor Gray
Write-Host "   - Authorizer: AquaChainAuthorizer (Cognito)" -ForegroundColor Gray
Write-Host "7. Enable CORS for each resource" -ForegroundColor Gray
Write-Host "8. Deploy to 'dev' stage" -ForegroundColor Gray
Write-Host ""

Write-Host "[MANUAL RESTORATION COMMANDS]" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you prefer AWS CLI (requires finding parent resource ID first):" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Get /api resource ID" -ForegroundColor Gray
Write-Host 'aws apigateway get-resources --rest-api-id vtqjfznspc --region ap-south-1 --query "items[?path=='"'"'/api'"'"'].id" --output text' -ForegroundColor DarkGray
Write-Host ""
Write-Host "# Create /api/profile (replace <API_RESOURCE_ID>)" -ForegroundColor Gray
Write-Host 'aws apigateway create-resource --rest-api-id vtqjfznspc --parent-id <API_RESOURCE_ID> --path-part profile --region ap-south-1' -ForegroundColor DarkGray
Write-Host ""
Write-Host "# Then create child resources and methods..." -ForegroundColor Gray
Write-Host "(This is complex - AWS Console is easier)" -ForegroundColor DarkGray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backup Information Displayed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup files preserved at:" -ForegroundColor Green
Write-Host "  $BACKUP_DIR/profile-*-$timestamp.json" -ForegroundColor Gray
Write-Host ""
Write-Host "Recommendation: Fix CDK and redeploy rather than manual restoration" -ForegroundColor Yellow
Write-Host ""
