# Test API directly to see exact response
Write-Host "Testing /api/devices endpoint directly..." -ForegroundColor Cyan
Write-Host ""

# Get token
$token = Read-Host "Enter your auth token from browser localStorage"

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
    } -UseBasicParsing
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Headers:" -ForegroundColor Cyan
    $response.Headers | Format-Table
    Write-Host ""
    Write-Host "Raw Response Body:" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    Write-Host $response.Content
    Write-Host ""
    Write-Host "Parsed JSON:" -ForegroundColor Cyan
    Write-Host "============" -ForegroundColor Cyan
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Yellow
    }
}
