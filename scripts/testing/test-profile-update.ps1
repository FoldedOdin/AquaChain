# Test profile update endpoint
# Tests the fixed /api/profile/update endpoint

$API_URL = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"

Write-Host "Testing Profile Update Endpoint" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# You'll need to replace this with a valid JWT token from your login
$TOKEN = Read-Host "Enter your JWT token (from browser localStorage or login response)"

if ([string]::IsNullOrWhiteSpace($TOKEN)) {
    Write-Host "Error: Token is required" -ForegroundColor Red
    exit 1
}

# Test profile update
Write-Host "Testing profile update..." -ForegroundColor Yellow

$updateBody = @{
    profile = @{
        firstName = "Updated"
        lastName = "Name"
        phone = "+1234567890"
    }
    preferences = @{
        theme = "dark"
        notifications = @{
            email = $true
            push = $true
            sms = $false
        }
    }
} | ConvertTo-Json -Depth 10

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $TOKEN"
}

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/profile/update" -Method PUT -Headers $headers -Body $updateBody
    Write-Host "✓ Profile update successful!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "✗ Profile update failed" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        Write-Host "Details:" -ForegroundColor Yellow
        $_.ErrorDetails.Message
    }
}

Write-Host ""
Write-Host "Test complete!" -ForegroundColor Cyan
