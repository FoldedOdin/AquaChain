# Debug script for profile update 502 error
# Tests the /api/profile/update endpoint and logs detailed response

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Profile Update 502 Debug Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_URL = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$EMAIL = "karthikpradep@gmail.com"  # Replace with actual email

# Get auth token (you'll need to provide this)
Write-Host "Please provide your JWT token:" -ForegroundColor Yellow
$TOKEN = Read-Host

if (-not $TOKEN) {
    Write-Host "❌ Token is required" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Write-Host "`n1. Testing GET /api/profile/update..." -ForegroundColor Cyan
try {
    $getResponse = Invoke-WebRequest -Uri "$API_URL/api/profile/update" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    
    Write-Host "✓ GET request successful" -ForegroundColor Green
    Write-Host "Status Code: $($getResponse.StatusCode)" -ForegroundColor White
    Write-Host "Response Body:" -ForegroundColor White
    $getResponse.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
    # Parse the response to check phone number
    $profileData = ($getResponse.Content | ConvertFrom-Json)
    if ($profileData.profile) {
        Write-Host "`nProfile structure:" -ForegroundColor Yellow
        Write-Host "  - profile.phone: $($profileData.profile.profile.phone)" -ForegroundColor White
        Write-Host "  - profile.firstName: $($profileData.profile.profile.firstName)" -ForegroundColor White
        Write-Host "  - profile.lastName: $($profileData.profile.profile.lastName)" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ GET request failed" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n2. Testing PUT /api/profile/update..." -ForegroundColor Cyan

$updateBody = @{
    updates = @{
        firstName = "Karthik"
        lastName = "K Pradep"
        phone = "+919876543210"
    }
} | ConvertTo-Json

Write-Host "Request Body:" -ForegroundColor White
Write-Host $updateBody -ForegroundColor Gray

try {
    $putResponse = Invoke-WebRequest -Uri "$API_URL/api/profile/update" `
        -Method PUT `
        -Headers $headers `
        -Body $updateBody `
        -UseBasicParsing
    
    Write-Host "✓ PUT request successful" -ForegroundColor Green
    Write-Host "Status Code: $($putResponse.StatusCode)" -ForegroundColor White
    Write-Host "Response Body:" -ForegroundColor White
    $putResponse.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "❌ PUT request failed" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Debug Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
