# Test API Endpoints
# This script tests all critical API endpoints

$ErrorActionPreference = "Continue"

$API_BASE = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$REGION = "ap-south-1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AquaChain API Endpoint Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Path,
        [string]$Method = "GET",
        [string]$Token = $null
    )
    
    $url = "$API_BASE$Path"
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    if ($Token) {
        $headers["Authorization"] = "Bearer $Token"
    }
    
    try {
        $response = Invoke-WebRequest -Uri $url -Method $Method -Headers $headers -UseBasicParsing -ErrorAction Stop
        $status = $response.StatusCode
        $statusIcon = if ($status -eq 200 -or $status -eq 403) { "✅" } else { "⚠️" }
        Write-Host "$statusIcon $Path : $status" -ForegroundColor $(if ($status -eq 200 -or $status -eq 403) { "Green" } else { "Yellow" })
        return $status
    }
    catch {
        $status = $_.Exception.Response.StatusCode.value__
        $statusIcon = if ($status -eq 401) { "❌" } else { "⚠️" }
        Write-Host "$statusIcon $Path : $status" -ForegroundColor $(if ($status -eq 401) { "Red" } else { "Yellow" })
        return $status
    }
}

Write-Host "Testing endpoints WITHOUT authentication..." -ForegroundColor Yellow
Write-Host "(Should return 401 Unauthorized - this is correct!)" -ForegroundColor Gray
Write-Host ""

$endpoints = @(
    "/api/devices",
    "/dashboard/stats",
    "/water-quality/latest",
    "/alerts"
)

foreach ($endpoint in $endpoints) {
    Test-Endpoint -Path $endpoint
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ = Endpoint working correctly (200 or 403)" -ForegroundColor Green
Write-Host "❌ = Authentication required (401) - Expected without token!" -ForegroundColor Yellow
Write-Host "⚠️  = Other status - May need investigation" -ForegroundColor Yellow
Write-Host ""
Write-Host "To test WITH authentication:" -ForegroundColor Cyan
Write-Host "1. Log in to http://localhost:3000" -ForegroundColor White
Write-Host "2. Open browser console (F12)" -ForegroundColor White
Write-Host "3. Run the test script from TESTING_SCRIPT.md" -ForegroundColor White
Write-Host ""
Write-Host "Next: Follow TESTING_SCRIPT.md for complete testing" -ForegroundColor Yellow
Write-Host ""
