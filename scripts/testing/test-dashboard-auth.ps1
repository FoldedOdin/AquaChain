# Test dashboard API authentication
$ErrorActionPreference = "Stop"

Write-Host "🔍 Testing Dashboard API Authentication..." -ForegroundColor Cyan

# Get token from user
Write-Host "`n📝 Please provide your JWT token from localStorage:" -ForegroundColor Yellow
Write-Host "(Open browser console and run: localStorage.getItem('aquachain_token'))" -ForegroundColor Gray
$token = Read-Host "Token"

if (-not $token) {
    Write-Host "❌ No token provided" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Token received (length: $($token.Length))" -ForegroundColor Green

# Test endpoints
$endpoints = @(
    @{url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/dashboard/stats"; name = "Dashboard Stats"},
    @{url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices"; name = "Devices"}
)

foreach ($endpoint in $endpoints) {
    Write-Host "`n🧪 Testing: $($endpoint.name)" -ForegroundColor Cyan
    Write-Host "URL: $($endpoint.url)" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $endpoint.url `
            -Method GET `
            -Headers @{
                "Authorization" = "Bearer $token"
                "Content-Type" = "application/json"
            } `
            -UseBasicParsing
        
        Write-Host "✅ Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Yellow
        $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        }
    }
}

Write-Host "`n✅ Test complete" -ForegroundColor Green
