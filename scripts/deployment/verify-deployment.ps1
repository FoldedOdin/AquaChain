# Verify AquaChain Deployment Status
# Checks what's deployed and what's missing

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev'
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AquaChain Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host ""

# Check CloudFormation Stacks
Write-Host "Checking CloudFormation Stacks..." -ForegroundColor Yellow
$stacks = aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?contains(StackName, 'AquaChain')].{Name:StackName,Status:StackStatus}" --output json | ConvertFrom-Json

if ($stacks.Count -eq 0) {
    Write-Host "✗ No AquaChain stacks found!" -ForegroundColor Red
} else {
    Write-Host "✓ Found $($stacks.Count) stack(s):" -ForegroundColor Green
    foreach ($stack in $stacks) {
        Write-Host "  - $($stack.Name): $($stack.Status)" -ForegroundColor Gray
    }
}

Write-Host ""

# Check DynamoDB Tables
Write-Host "Checking DynamoDB Tables..." -ForegroundColor Yellow
$requiredTables = @(
    "AquaChain-Users-$Environment",
    "AquaChain-Devices-$Environment",
    "AquaChain-Readings-$Environment",
    "AquaChain-Alerts-$Environment",
    "AquaChain-ServiceRequests-$Environment"
)

$existingTables = aws dynamodb list-tables --query "TableNames" --output json | ConvertFrom-Json
$missingTables = @()

foreach ($table in $requiredTables) {
    if ($existingTables -contains $table) {
        Write-Host "✓ $table exists" -ForegroundColor Green
    } else {
        Write-Host "✗ $table MISSING" -ForegroundColor Red
        $missingTables += $table
    }
}

Write-Host ""

# Check Lambda Functions
Write-Host "Checking Lambda Functions..." -ForegroundColor Yellow
$functions = aws lambda list-functions --query "Functions[?contains(FunctionName, 'AquaChain')].FunctionName" --output json | ConvertFrom-Json

if ($functions.Count -eq 0) {
    Write-Host "✗ No AquaChain Lambda functions found!" -ForegroundColor Red
} else {
    Write-Host "✓ Found $($functions.Count) Lambda function(s)" -ForegroundColor Green
    foreach ($func in $functions | Select-Object -First 5) {
        Write-Host "  - $func" -ForegroundColor Gray
    }
    if ($functions.Count -gt 5) {
        Write-Host "  ... and $($functions.Count - 5) more" -ForegroundColor Gray
    }
}

Write-Host ""

# Check API Gateway
Write-Host "Checking API Gateway..." -ForegroundColor Yellow
$apis = aws apigateway get-rest-apis --query "items[?contains(name, 'AquaChain')].{Name:name,Id:id}" --output json | ConvertFrom-Json

if ($apis.Count -eq 0) {
    Write-Host "✗ No AquaChain API Gateway found!" -ForegroundColor Red
} else {
    Write-Host "✓ Found API Gateway:" -ForegroundColor Green
    foreach ($api in $apis) {
        Write-Host "  - $($api.Name) (ID: $($api.Id))" -ForegroundColor Gray
        
        # Get API endpoint
        $endpoint = "https://$($api.Id).execute-api.ap-south-1.amazonaws.com/$Environment"
        Write-Host "    Endpoint: $endpoint" -ForegroundColor Cyan
    }
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($missingTables.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  MISSING COMPONENTS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "DynamoDB Tables Missing:" -ForegroundColor Red
    foreach ($table in $missingTables) {
        Write-Host "  - $table" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "To fix, deploy the data stack:" -ForegroundColor Yellow
    Write-Host "  cd infrastructure/cdk" -ForegroundColor White
    Write-Host "  cdk deploy AquaChain-Data-$Environment" -ForegroundColor White
    Write-Host ""
    Write-Host "Or deploy all stacks:" -ForegroundColor Yellow
    Write-Host "  cdk deploy --all" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✓ All core components deployed!" -ForegroundColor Green
}

Write-Host ""
