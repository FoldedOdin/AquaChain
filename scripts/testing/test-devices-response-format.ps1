# Test the /api/devices endpoint response format
# Verifies that the response matches frontend expectations

Write-Host "Testing /api/devices endpoint response format..." -ForegroundColor Cyan
Write-Host ""

# Get token from user
Write-Host "To get your auth token:" -ForegroundColor Yellow
Write-Host "1. Open browser console (F12)" -ForegroundColor White
Write-Host "2. Go to Application tab > Local Storage" -ForegroundColor White
Write-Host "3. Copy the value of 'aquachain_token'" -ForegroundColor White
Write-Host ""

$token = Read-Host "Enter your auth token (or press Enter to skip)"

if (-not $token) {
    Write-Host ""
    Write-Host "No token provided. Testing without authentication..." -ForegroundColor Yellow
    Write-Host "Note: This will likely return 401 Unauthorized" -ForegroundColor Yellow
    Write-Host ""
}

$url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/devices"

Write-Host "Calling: $url" -ForegroundColor Gray
Write-Host ""

try {
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    if ($token) {
        $headers["Authorization"] = "Bearer $token"
    }
    
    $response = Invoke-WebRequest -Uri $url -Method GET -Headers $headers
    
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    
    # Parse JSON response
    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "Response structure:" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    
    # Check if response has 'success' field
    if ($null -ne $jsonResponse.success) {
        Write-Host "✓ Has 'success' field: $($jsonResponse.success)" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing 'success' field" -ForegroundColor Red
    }
    
    # Check if response has 'data' field
    if ($null -ne $jsonResponse.data) {
        Write-Host "✓ Has 'data' field" -ForegroundColor Green
        
        if ($jsonResponse.data -is [array]) {
            Write-Host "✓ 'data' is an array with $($jsonResponse.data.Count) items" -ForegroundColor Green
            
            if ($jsonResponse.data.Count -gt 0) {
                Write-Host ""
                Write-Host "First device:" -ForegroundColor Cyan
                $jsonResponse.data[0] | ConvertTo-Json -Depth 3
            }
        } else {
            Write-Host "✗ 'data' is not an array" -ForegroundColor Red
        }
    } else {
        Write-Host "✗ Missing 'data' field" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Full response:" -ForegroundColor Cyan
    Write-Host "==============" -ForegroundColor Cyan
    $jsonResponse | ConvertTo-Json -Depth 5
    
    Write-Host ""
    Write-Host "✓ Response format is correct!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend should now be able to parse this response." -ForegroundColor Cyan
    
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host ""
        Write-Host "Response Body:" -ForegroundColor Yellow
        Write-Host $responseBody
    }
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Refresh your dashboard in the browser (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "2. Open browser console (F12)" -ForegroundColor White
Write-Host "3. Look for device data in the Network tab" -ForegroundColor White
Write-Host "4. Devices should now appear in the dashboard!" -ForegroundColor White
