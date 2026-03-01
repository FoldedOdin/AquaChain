# Test order cancellation endpoint
# This script tests the DELETE /api/orders/{orderId} endpoint with CORS

$API_ENDPOINT = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$TOKEN = $env:AQUACHAIN_TOKEN

if (-not $TOKEN) {
    Write-Host "Error: AQUACHAIN_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host "Please set it with: `$env:AQUACHAIN_TOKEN = 'your-token-here'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Testing Order Cancellation Endpoint" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Test 1: OPTIONS request (CORS preflight)
Write-Host "Test 1: OPTIONS request (CORS preflight)" -ForegroundColor Yellow
try {
    $optionsResponse = Invoke-WebRequest `
        -Uri "$API_ENDPOINT/api/orders/test-order-id" `
        -Method OPTIONS `
        -Headers @{
            "Origin" = "http://localhost:3000"
            "Access-Control-Request-Method" = "DELETE"
            "Access-Control-Request-Headers" = "Content-Type,Authorization"
        } `
        -UseBasicParsing

    Write-Host "Status Code: $($optionsResponse.StatusCode)" -ForegroundColor Green
    Write-Host "CORS Headers:" -ForegroundColor Cyan
    $optionsResponse.Headers.GetEnumerator() | Where-Object { $_.Key -like "Access-Control-*" } | ForEach-Object {
        Write-Host "  $($_.Key): $($_.Value)" -ForegroundColor White
    }
    Write-Host ""
} catch {
    Write-Host "OPTIONS request failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 2: Fetch orders to get a real order ID
Write-Host "Test 2: Fetching orders to get a cancellable order ID" -ForegroundColor Yellow
try {
    $ordersResponse = Invoke-RestMethod `
        -Uri "$API_ENDPOINT/api/orders/history" `
        -Method GET `
        -Headers @{
            "Authorization" = "Bearer $TOKEN"
            "Content-Type" = "application/json"
        }

    $cancellableOrders = $ordersResponse.orders | Where-Object { 
        $_.status -eq "ORDER_PLACED" -or $_.status -eq "pending" 
    }

    if ($cancellableOrders.Count -gt 0) {
        $testOrderId = $cancellableOrders[0].orderId
        Write-Host "Found cancellable order: $testOrderId" -ForegroundColor Green
        Write-Host "Status: $($cancellableOrders[0].status)" -ForegroundColor Cyan
        Write-Host ""

        # Test 3: Attempt to cancel the order (with confirmation)
        Write-Host "Test 3: Testing DELETE request" -ForegroundColor Yellow
        $confirm = Read-Host "Do you want to actually cancel order $testOrderId? (yes/no)"
        
        if ($confirm -eq "yes") {
            try {
                $deleteResponse = Invoke-RestMethod `
                    -Uri "$API_ENDPOINT/api/orders/$testOrderId" `
                    -Method DELETE `
                    -Headers @{
                        "Authorization" = "Bearer $TOKEN"
                        "Content-Type" = "application/json"
                    }

                Write-Host "Order cancelled successfully!" -ForegroundColor Green
                Write-Host "Response: $($deleteResponse | ConvertTo-Json -Depth 3)" -ForegroundColor White
            } catch {
                Write-Host "DELETE request failed: $($_.Exception.Message)" -ForegroundColor Red
                if ($_.Exception.Response) {
                    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                    $responseBody = $reader.ReadToEnd()
                    Write-Host "Response body: $responseBody" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "Skipping actual cancellation (dry run)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No cancellable orders found (all orders are already processed or cancelled)" -ForegroundColor Yellow
        Write-Host "Total orders: $($ordersResponse.orders.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "Failed to fetch orders: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n====================================`n" -ForegroundColor Cyan
Write-Host "Testing complete!" -ForegroundColor Green
Write-Host "`nNote: You can also test from the frontend at http://localhost:3000" -ForegroundColor Cyan
