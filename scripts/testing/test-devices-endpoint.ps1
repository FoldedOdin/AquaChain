# Test the /api/devices endpoint with authentication

Write-Host "Testing /api/devices endpoint..." -ForegroundColor Cyan
Write-Host ""

# You need to get your token from the browser
Write-Host "To get your token:" -ForegroundColor Yellow
Write-Host "1. Open browser console (F12)" -ForegroundColor White
Write-Host "2. Run: localStorage.getItem('aquachain_token')" -ForegroundColor White
Write-Host "3. Copy the token and paste it below" -ForegroundColor White
Write-Host ""

$token = Read-Host "Enter your auth token"

if (-not $token) {
    Write-Host "No token provided. Exiting." -ForegroundColor Red
    exit
}

$url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices"

Write-Host "Calling: $url" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -Method GET -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Yellow
    }
}
