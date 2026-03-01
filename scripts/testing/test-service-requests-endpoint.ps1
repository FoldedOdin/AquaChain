# Test Service Requests Endpoint
# Tests the GET /api/v1/service-requests endpoint

Write-Host "=== Testing Service Requests Endpoint ===" -ForegroundColor Cyan
Write-Host ""

# Get auth token from localStorage (you'll need to provide this)
Write-Host "Note: You need a valid Cognito JWT token to test this endpoint" -ForegroundColor Yellow
Write-Host "Get it from your browser's localStorage: aquachain_token or authToken" -ForegroundColor Yellow
Write-Host ""

$token = Read-Host "Enter your JWT token (or press Enter to skip auth test)"

$apiEndpoint = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$url = "$apiEndpoint/api/v1/service-requests?status=assigned,in_progress"

Write-Host "Testing: $url" -ForegroundColor Cyan
Write-Host ""

if ($token) {
    Write-Host "Testing with authentication..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } -UseBasicParsing
        
        Write-Host "✓ Success!" -ForegroundColor Green
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Gray
        Write-Host "Response:" -ForegroundColor Gray
        $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "✗ Request failed" -ForegroundColor Red
        Write-Host "Status Code: $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 401) {
            Write-Host "  → Token is invalid or expired" -ForegroundColor Yellow
        }
        elseif ($statusCode -eq 403) {
            Write-Host "  → Access denied - check user role" -ForegroundColor Yellow
        }
        elseif ($statusCode -eq 404) {
            Write-Host "  → No service requests found (this is OK if database is empty)" -ForegroundColor Yellow
        }
        elseif ($statusCode -eq 502) {
            Write-Host "  → Lambda error - check CloudWatch logs" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Error details:" -ForegroundColor Gray
        Write-Host $_.Exception.Message
    }
} else {
    Write-Host "Skipping authenticated test" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Checking Lambda Logs ===" -ForegroundColor Cyan
Write-Host ""

$logs = aws logs tail /aws/lambda/aquachain-function-service-request-dev `
    --since 2m `
    --format short `
    --region ap-south-1 2>&1 | Select-String -Pattern "ERROR|Processing|list_service_requests" | Select-Object -Last 10

if ($logs) {
    Write-Host "Recent log entries:" -ForegroundColor Gray
    $logs | ForEach-Object { 
        if ($_ -like "*ERROR*") {
            Write-Host "  $_" -ForegroundColor Red
        } else {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "No recent log entries found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Green
