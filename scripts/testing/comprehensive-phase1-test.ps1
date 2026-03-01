# Comprehensive Phase 1 Testing Suite
# Tests backend, API Gateway, DynamoDB, and CloudWatch logs

$ErrorActionPreference = "Stop"

$API_BASE = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$REGION = "ap-south-1"
$LAMBDA_NAME = "aquachain-function-admin-service-dev"
$CONFIG_HISTORY_TABLE = "AquaChain-ConfigHistory"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Phase 1 Comprehensive Testing Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# SECTION 1: Pre-Flight Checks
# ============================================================
Write-Host "SECTION 1: Pre-Flight Checks" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""

# Check AWS CLI
Write-Host "[1/4] Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    Write-Host "  ✓ AWS CLI installed: $awsVersion" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ AWS CLI not found. Please install AWS CLI." -ForegroundColor Red
    exit 1
}

# Check Lambda function exists
Write-Host "[2/4] Checking Lambda function..." -ForegroundColor Yellow
try {
    $lambdaInfo = aws lambda get-function --function-name $LAMBDA_NAME --region $REGION 2>&1 | ConvertFrom-Json
    $lastModified = $lambdaInfo.Configuration.LastModified
    Write-Host "  ✓ Lambda function exists" -ForegroundColor Green
    Write-Host "    Last Modified: $lastModified" -ForegroundColor Gray
}
catch {
    Write-Host "  ✗ Lambda function not found" -ForegroundColor Red
    exit 1
}

# Check DynamoDB table exists
Write-Host "[3/4] Checking DynamoDB ConfigHistory table..." -ForegroundColor Yellow
try {
    $tableInfo = aws dynamodb describe-table --table-name $CONFIG_HISTORY_TABLE --region $REGION 2>&1 | ConvertFrom-Json
    $tableStatus = $tableInfo.Table.TableStatus
    $itemCount = $tableInfo.Table.ItemCount
    Write-Host "  ✓ ConfigHistory table exists" -ForegroundColor Green
    Write-Host "    Status: $tableStatus" -ForegroundColor Gray
    Write-Host "    Item Count: $itemCount" -ForegroundColor Gray
}
catch {
    Write-Host "  ✗ ConfigHistory table not found" -ForegroundColor Red
    exit 1
}

# Get JWT token
Write-Host "[4/4] Getting JWT token..." -ForegroundColor Yellow
Write-Host "  Please provide your admin JWT token:" -ForegroundColor Cyan
Write-Host "  (Get from browser localStorage: aquachain_token)" -ForegroundColor Gray
$token = Read-Host "  JWT Token"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "  ✗ Token is required" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Token received" -ForegroundColor Green

Write-Host ""

# ============================================================
# SECTION 2: Backend Endpoint Tests
# ============================================================
Write-Host "SECTION 2: Backend Endpoint Tests" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""

$testResults = @{
    validate = $false
    history = $false
    rollback = $false
    getCurrentConfig = $false
    updateConfig = $false
}

# Test 1: Get Current Configuration
Write-Host "[1/5] Testing GET /api/admin/system/configuration" -ForegroundColor Yellow
try {
    $currentConfig = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration" `
        -Method GET `
        -Headers @{
            "Authorization" = "Bearer $token"
        }
    
    Write-Host "  ✓ GET current config successful" -ForegroundColor Green
    Write-Host "    pH Min: $($currentConfig.alertThresholds.global.pH.min)" -ForegroundColor Gray
    Write-Host "    pH Max: $($currentConfig.alertThresholds.global.pH.max)" -ForegroundColor Gray
    $testResults.getCurrentConfig = $true
}
catch {
    Write-Host "  ✗ GET current config failed" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Validate Configuration (Valid)
Write-Host "[2/5] Testing POST /api/admin/system/configuration/validate (Valid)" -ForegroundColor Yellow

$validConfig = @{
    alertThresholds = @{
        global = @{
            pH = @{
                min = 6.5
                max = 8.5
            }
            turbidity = @{
                max = 5.0
            }
            tds = @{
                max = 500
            }
            temperature = @{
                min = 10.0
                max = 35.0
            }
        }
    }
    systemLimits = @{
        maxDevicesPerUser = 10
        dataRetentionDays = 90
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/validate" `
        -Method POST `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } `
        -Body $validConfig
    
    if ($response.valid -eq $true) {
        Write-Host "  ✓ Validation passed for valid config" -ForegroundColor Green
        $testResults.validate = $true
    }
    else {
        Write-Host "  ✗ Validation failed unexpectedly" -ForegroundColor Red
        Write-Host "    Errors: $($response.errors -join ', ')" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ✗ Validate endpoint failed" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Validate Configuration (Invalid)
Write-Host "[3/5] Testing POST /api/admin/system/configuration/validate (Invalid)" -ForegroundColor Yellow

$invalidConfig = @{
    alertThresholds = @{
        global = @{
            pH = @{
                min = 15.0  # Invalid: pH > 14
                max = 8.5
            }
        }
    }
    systemLimits = @{
        dataRetentionDays = 10  # Invalid: < 30 days
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/validate" `
        -Method POST `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } `
        -Body $invalidConfig
    
    if ($response.valid -eq $false) {
        Write-Host "  ✓ Validation correctly rejected invalid config" -ForegroundColor Green
        Write-Host "    Errors found: $($response.errors.Count)" -ForegroundColor Gray
        foreach ($error in $response.errors) {
            Write-Host "      - $error" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ✗ Validation should have failed but passed" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ✗ Validate endpoint failed" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: Get Configuration History
Write-Host "[4/5] Testing GET /api/admin/system/configuration/history" -ForegroundColor Yellow
try {
    $history = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/history?limit=10" `
        -Method GET `
        -Headers @{
            "Authorization" = "Bearer $token"
        }
    
    Write-Host "  ✓ History endpoint successful" -ForegroundColor Green
    Write-Host "    Versions found: $($history.versions.Count)" -ForegroundColor Gray
    
    if ($history.versions.Count -gt 0) {
        $latest = $history.versions[0]
        Write-Host "    Latest version: $($latest.version)" -ForegroundColor Gray
        Write-Host "    Updated by: $($latest.updatedBy)" -ForegroundColor Gray
        Write-Host "    Updated at: $($latest.updatedAt)" -ForegroundColor Gray
    }
    
    $testResults.history = $true
}
catch {
    Write-Host "  ✗ History endpoint failed" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 5: Rollback Configuration
Write-Host "[5/5] Testing POST /api/admin/system/configuration/rollback" -ForegroundColor Yellow

# First, check if we have any versions to rollback to
if ($testResults.history -and $history.versions.Count -gt 0) {
    $versionToRollback = $history.versions[0].version
    
    $rollbackPayload = @{
        version = $versionToRollback
    } | ConvertTo-Json
    
    Write-Host "  Note: Testing rollback to version: $versionToRollback" -ForegroundColor Gray
    Write-Host "  (This will actually rollback the config - use with caution!)" -ForegroundColor Yellow
    Write-Host "  Skip this test? (Y/N)" -ForegroundColor Cyan
    $skip = Read-Host "  "
    
    if ($skip -eq "Y" -or $skip -eq "y") {
        Write-Host "  ⊘ Rollback test skipped by user" -ForegroundColor Yellow
    }
    else {
        try {
            $response = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/rollback" `
                -Method POST `
                -Headers @{
                    "Authorization" = "Bearer $token"
                    "Content-Type" = "application/json"
                } `
                -Body $rollbackPayload
            
            Write-Host "  ✓ Rollback endpoint successful" -ForegroundColor Green
            Write-Host "    Rolled back to: $($response.version)" -ForegroundColor Gray
            $testResults.rollback = $true
        }
        catch {
            Write-Host "  ✗ Rollback endpoint failed" -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
else {
    Write-Host "  ⊘ No versions available for rollback test" -ForegroundColor Yellow
    Write-Host "    (Create a config change first to test rollback)" -ForegroundColor Gray
}

Write-Host ""

# ============================================================
# SECTION 3: DynamoDB Verification
# ============================================================
Write-Host "SECTION 3: DynamoDB Verification" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""

Write-Host "[1/2] Scanning ConfigHistory table..." -ForegroundColor Yellow
try {
    $scanResult = aws dynamodb scan --table-name $CONFIG_HISTORY_TABLE --region $REGION --max-items 5 2>&1 | ConvertFrom-Json
    $itemCount = $scanResult.Items.Count
    
    Write-Host "  ✓ ConfigHistory table accessible" -ForegroundColor Green
    Write-Host "    Items scanned: $itemCount" -ForegroundColor Gray
    
    if ($itemCount -gt 0) {
        Write-Host "    Sample version IDs:" -ForegroundColor Gray
        foreach ($item in $scanResult.Items) {
            $versionId = $item.SK.S
            $timestamp = $item.timestamp.S
            Write-Host "      - $versionId (at $timestamp)" -ForegroundColor Gray
        }
    }
}
catch {
    Write-Host "  ✗ Failed to scan ConfigHistory table" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

Write-Host "[2/2] Checking table metrics..." -ForegroundColor Yellow
try {
    $tableInfo = aws dynamodb describe-table --table-name $CONFIG_HISTORY_TABLE --region $REGION 2>&1 | ConvertFrom-Json
    
    Write-Host "  ✓ Table metrics retrieved" -ForegroundColor Green
    Write-Host "    Table Status: $($tableInfo.Table.TableStatus)" -ForegroundColor Gray
    Write-Host "    Item Count: $($tableInfo.Table.ItemCount)" -ForegroundColor Gray
    Write-Host "    Table Size: $($tableInfo.Table.TableSizeBytes) bytes" -ForegroundColor Gray
    Write-Host "    Billing Mode: $($tableInfo.Table.BillingModeSummary.BillingMode)" -ForegroundColor Gray
}
catch {
    Write-Host "  ✗ Failed to get table metrics" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# SECTION 4: CloudWatch Logs Check
# ============================================================
Write-Host "SECTION 4: CloudWatch Logs Check" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""

Write-Host "[1/2] Checking recent Lambda logs..." -ForegroundColor Yellow
try {
    $logGroup = "/aws/lambda/$LAMBDA_NAME"
    $endTime = [int][double]::Parse((Get-Date -UFormat %s)) * 1000
    $startTime = $endTime - (300000)  # Last 5 minutes
    
    $logs = aws logs filter-log-events `
        --log-group-name $logGroup `
        --start-time $startTime `
        --end-time $endTime `
        --region $REGION `
        --max-items 10 2>&1 | ConvertFrom-Json
    
    if ($logs.events.Count -gt 0) {
        Write-Host "  ✓ Recent logs found" -ForegroundColor Green
        Write-Host "    Log entries: $($logs.events.Count)" -ForegroundColor Gray
        Write-Host "    Recent messages:" -ForegroundColor Gray
        
        foreach ($event in $logs.events | Select-Object -First 5) {
            $message = $event.message.Substring(0, [Math]::Min(100, $event.message.Length))
            Write-Host "      $message..." -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ⊘ No recent logs found (last 5 minutes)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ✗ Failed to retrieve CloudWatch logs" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

Write-Host "[2/2] Searching for config-related log entries..." -ForegroundColor Yellow
try {
    $logs = aws logs filter-log-events `
        --log-group-name $logGroup `
        --filter-pattern "configuration" `
        --start-time $startTime `
        --end-time $endTime `
        --region $REGION `
        --max-items 5 2>&1 | ConvertFrom-Json
    
    if ($logs.events.Count -gt 0) {
        Write-Host "  ✓ Configuration-related logs found" -ForegroundColor Green
        Write-Host "    Entries: $($logs.events.Count)" -ForegroundColor Gray
    }
    else {
        Write-Host "  ⊘ No configuration-related logs in last 5 minutes" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ✗ Failed to search logs" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# SECTION 5: Test Summary
# ============================================================
Write-Host "SECTION 5: Test Summary" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""

$passedTests = ($testResults.Values | Where-Object { $_ -eq $true }).Count
$totalTests = $testResults.Count

Write-Host "Backend Endpoint Tests:" -ForegroundColor Yellow
Write-Host "  GET current config:  $(if ($testResults.getCurrentConfig) { '✓ PASS' } else { '✗ FAIL' })" -ForegroundColor $(if ($testResults.getCurrentConfig) { 'Green' } else { 'Red' })
Write-Host "  POST validate:       $(if ($testResults.validate) { '✓ PASS' } else { '✗ FAIL' })" -ForegroundColor $(if ($testResults.validate) { 'Green' } else { 'Red' })
Write-Host "  GET history:         $(if ($testResults.history) { '✓ PASS' } else { '✗ FAIL' })" -ForegroundColor $(if ($testResults.history) { 'Green' } else { 'Red' })
Write-Host "  POST rollback:       $(if ($testResults.rollback) { '✓ PASS' } else { '⊘ SKIP' })" -ForegroundColor $(if ($testResults.rollback) { 'Green' } else { 'Yellow' })
Write-Host ""
Write-Host "Score: $passedTests/$totalTests tests passed" -ForegroundColor $(if ($passedTests -eq $totalTests) { 'Green' } else { 'Yellow' })
Write-Host ""

# ============================================================
# SECTION 6: Next Steps
# ============================================================
Write-Host "SECTION 6: Next Steps" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Gray
Write-Host ""

if ($passedTests -ge 3) {
    Write-Host "✓ Backend is working well!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Recommended next steps:" -ForegroundColor Yellow
    Write-Host "  1. Deploy frontend build" -ForegroundColor White
    Write-Host "     cd frontend && npm run build" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Test end-to-end in browser" -ForegroundColor White
    Write-Host "     - Login as admin" -ForegroundColor Gray
    Write-Host "     - Navigate to System Configuration" -ForegroundColor Gray
    Write-Host "     - Make a change and verify confirmation modal" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Verify version history is created" -ForegroundColor White
    Write-Host "     - Check DynamoDB ConfigHistory table" -ForegroundColor Gray
    Write-Host "     - Check CloudWatch logs for audit entries" -ForegroundColor Gray
}
else {
    Write-Host "⚠ Some tests failed. Please review errors above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "  1. Check Lambda function logs in CloudWatch" -ForegroundColor White
    Write-Host "  2. Verify API Gateway deployment to 'dev' stage" -ForegroundColor White
    Write-Host "  3. Confirm IAM permissions for ConfigHistory table" -ForegroundColor White
    Write-Host "  4. Test endpoints manually with curl/Postman" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Testing Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
