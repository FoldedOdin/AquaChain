# Phase 1 Endpoint Testing Script
# Tests the new configuration endpoints

$ErrorActionPreference = "Stop"

$API_BASE = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Phase 1 Endpoint Testing" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Get JWT token from user
Write-Host "Please provide your admin JWT token:" -ForegroundColor Yellow
Write-Host "(You can get this from browser localStorage: aquachain_token)" -ForegroundColor Gray
$token = Read-Host "JWT Token"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Error: Token is required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Testing endpoints..." -ForegroundColor Green
Write-Host ""

# Test 1: Validate Endpoint
Write-Host "Test 1: Validate Configuration Endpoint" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

$validatePayload = @{
    alertThresholds = @{
        global = @{
            pH = @{
                min = 6.5
                max = 8.5
            }
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/validate" `
        -Method POST `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } `
        -Body $validatePayload
    
    Write-Host "✓ Validate endpoint working" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Validate endpoint failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: History Endpoint
Write-Host "Test 2: Configuration History Endpoint" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/history?limit=10" `
        -Method GET `
        -Headers @{
            "Authorization" = "Bearer $token"
        }
    
    Write-Host "✓ History endpoint working" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ History endpoint failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Rollback Endpoint (will fail with "version not found" but that's expected)
Write-Host "Test 3: Rollback Configuration Endpoint" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

$rollbackPayload = @{
    version = "v_2026-02-26T14:00:00.000Z"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/admin/system/configuration/rollback" `
        -Method POST `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } `
        -Body $rollbackPayload
    
    Write-Host "✓ Rollback endpoint working" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
}
catch {
    $errorMessage = $_.Exception.Message
    if ($errorMessage -like "*404*" -or $errorMessage -like "*not found*") {
        Write-Host "✓ Rollback endpoint working (version not found is expected)" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Rollback endpoint failed" -ForegroundColor Red
        Write-Host "  Error: $errorMessage" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. If all tests passed, deploy frontend" -ForegroundColor White
Write-Host "2. cd frontend && npm run build" -ForegroundColor Gray
Write-Host "3. Deploy build to your hosting" -ForegroundColor White
Write-Host ""
