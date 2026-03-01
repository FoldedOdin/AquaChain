# Import Existing DynamoDB Tables into CDK
# This script imports existing tables into CloudFormation management

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Import Existing Tables to CDK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$STACK_NAME = "AquaChain-Data-dev"

# Tables to import (legacy names)
$TABLES = @(
    @{LogicalId="ReadingsTable"; TableName="AquaChain-Readings"},
    @{LogicalId="LedgerTable"; TableName="AquaChain-Ledger"},
    @{LogicalId="SequenceTable"; TableName="AquaChain-Sequence"},
    @{LogicalId="UsersTable"; TableName="AquaChain-Users"},
    @{LogicalId="ServiceRequestsTable"; TableName="AquaChain-ServiceRequests"},
    @{LogicalId="DevicesTable"; TableName="AquaChain-Devices"},
    @{LogicalId="AuditLogsTable"; TableName="AquaChain-AuditLogs"},
    @{LogicalId="SystemConfigTable"; TableName="AquaChain-SystemConfig"}
)

Write-Host "[1/4] Verifying tables exist..." -ForegroundColor Yellow
Write-Host ""

$allExist = $true
foreach ($table in $TABLES) {
    $exists = aws dynamodb describe-table --table-name $table.TableName --region $REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $($table.TableName)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($table.TableName) NOT FOUND" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "ERROR: Some tables don't exist" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] Creating import resources file..." -ForegroundColor Yellow

# Create resources-to-import.txt file
$importFile = "infrastructure/cdk/resources-to-import.txt"
$importContent = ""

foreach ($table in $TABLES) {
    $arn = "arn:aws:dynamodb:${REGION}:758346259059:table/$($table.TableName)"
    $importContent += "$($table.LogicalId)|$arn`n"
}

$importContent | Out-File -FilePath $importFile -Encoding UTF8 -NoNewline
Write-Host "  ✓ Created: $importFile" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Generating CDK template..." -ForegroundColor Yellow

Set-Location infrastructure/cdk

try {
    cdk synth $STACK_NAME --no-version-reporting 2>&1 | Out-Null
    Write-Host "  ✓ Template generated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ ERROR: Failed to synthesize template" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Write-Host ""
Write-Host "[4/4] Creating import changeset..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  NOTE: CDK doesn't support resource import via 'cdk deploy'" -ForegroundColor Yellow
Write-Host "  We need to use CloudFormation directly" -ForegroundColor Yellow
Write-Host ""

# Get the template path
$templatePath = "cdk.out/$STACK_NAME.template.json"

if (-not (Test-Path $templatePath)) {
    Write-Host "  ✗ ERROR: Template not found at $templatePath" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Write-Host "  Creating changeset with resource imports..." -ForegroundColor Gray

# Create resources-to-import JSON for CloudFormation
$resourcesToImport = @()
foreach ($table in $TABLES) {
    $resourcesToImport += @{
        ResourceType = "AWS::DynamoDB::Table"
        LogicalResourceId = $table.LogicalId
        ResourceIdentifier = @{
            TableName = $table.TableName
        }
    }
}

$resourcesToImportJson = $resourcesToImport | ConvertTo-Json -Depth 10
$resourcesToImportJson | Out-File -FilePath "resources-to-import.json" -Encoding UTF8

try {
    aws cloudformation create-change-set `
        --stack-name $STACK_NAME `
        --change-set-name import-existing-tables `
        --change-set-type IMPORT `
        --resources-to-import file://resources-to-import.json `
        --template-body file://$templatePath `
        --capabilities CAPABILITY_IAM `
        --region $REGION 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Changeset created" -ForegroundColor Green
    } else {
        throw "Failed to create changeset"
    }
} catch {
    Write-Host "  ✗ ERROR: Failed to create import changeset" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Write-Host ""
Write-Host "  Waiting for changeset to be ready..." -ForegroundColor Gray

Start-Sleep -Seconds 5

$changesetStatus = aws cloudformation describe-change-set `
    --stack-name $STACK_NAME `
    --change-set-name import-existing-tables `
    --region $REGION `
    --query "Status" `
    --output text 2>&1

Write-Host "  Changeset status: $changesetStatus" -ForegroundColor Gray

if ($changesetStatus -eq "CREATE_COMPLETE") {
    Write-Host "  ✓ Changeset ready to execute" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Execute with:" -ForegroundColor Yellow
    Write-Host "  aws cloudformation execute-change-set --stack-name $STACK_NAME --change-set-name import-existing-tables --region $REGION" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Changeset status: $changesetStatus" -ForegroundColor Yellow
    Write-Host "  Check AWS Console for details" -ForegroundColor Gray
}

Set-Location ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Import Preparation Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the changeset in AWS Console" -ForegroundColor Gray
Write-Host "2. Execute the changeset to import tables" -ForegroundColor Gray
Write-Host "3. Deploy API Gateway stack" -ForegroundColor Gray
Write-Host ""
Write-Host "Execute changeset:" -ForegroundColor Cyan
Write-Host "aws cloudformation execute-change-set --stack-name $STACK_NAME --change-set-name import-existing-tables --region $REGION" -ForegroundColor Gray
Write-Host ""
