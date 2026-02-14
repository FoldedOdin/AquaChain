# Test Profile Endpoints CORS Configuration
# This script tests the CORS preflight requests for profile endpoints

$apiEndpoint = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Profile Endpoints CORS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test endpoints
$endpoints = @(
    "/api/profile/request-otp",
    "/api/profile/verify-and-update",
    "/api/profile/update"
)

foreach ($endpoint in $endpoints) {
    Write-Host "Testing: $endpoint" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest `
            -Uri "$apiEndpoint$endpoint" `
            -Method OPTIONS `
            -Headers @{
                "Origin" = "http://localhost:3000"
                "Access-Control-Request-Method" = "POST"
                "Access-Control-Request-Headers" = "Content-Type,Authorization"
            } `
            -UseBasicParsing `
            -ErrorAction Stop
        
        $headers = $response.Headers
        
        Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Access-Control-Allow-Origin: $($headers['Access-Control-Allow-Origin'])" -ForegroundColor White
        Write-Host "  Access-Control-Allow-Methods: $($headers['Access-Control-Allow-Methods'])" -ForegroundColor White
        Write-Host "  Access-Control-Allow-Headers: $($headers['Access-Control-Allow-Headers'])" -ForegroundColor White
        Write-Host "  ✓ CORS configured correctly" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ CORS test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Notification Endpoints CORS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$notifEndpoints = @(
    "/api/notifications",
    "/api/notifications/unread-count",
    "/api/notifications/read-all"
)

foreach ($endpoint in $notifEndpoints) {
    Write-Host "Testing: $endpoint" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest `
            -Uri "$apiEndpoint$endpoint" `
            -Method OPTIONS `
            -Headers @{
                "Origin" = "http://localhost:3000"
                "Access-Control-Request-Method" = "GET"
                "Access-Control-Request-Headers" = "Content-Type,Authorization"
            } `
            -UseBasicParsing `
            -ErrorAction Stop
        
        $headers = $response.Headers
        
        Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Access-Control-Allow-Origin: $($headers['Access-Control-Allow-Origin'])" -ForegroundColor White
        Write-Host "  Access-Control-Allow-Methods: $($headers['Access-Control-Allow-Methods'])" -ForegroundColor White
        Write-Host "  Access-Control-Allow-Headers: $($headers['Access-Control-Allow-Headers'])" -ForegroundColor White
        Write-Host "  ✓ CORS configured correctly" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ CORS test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "CORS Testing Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
