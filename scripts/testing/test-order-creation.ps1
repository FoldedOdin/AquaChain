# Test order creation with correct payload structure
$token = (Get-Content frontend\.env.local | Select-String "REACT_APP_TEST_TOKEN").ToString().Split("=")[1].Trim()

$orderPayload = @{
    consumerId = "test-user-123"
    deviceType = "basic"
    serviceType = "installation"
    paymentMethod = "COD"
    deliveryAddress = @{
        street = "123 Test Street"
        city = "Mumbai"
        state = "Maharashtra"
        pincode = "400001"
        country = "India"
        landmark = "Near Test Mall"
    }
    contactInfo = @{
        name = "Test User"
        phone = "+919876543210"
        email = "test@example.com"
    }
    amount = 5499
    specialInstructions = "Please call before delivery"
} | ConvertTo-Json -Depth 10

Write-Host "Testing order creation..." -ForegroundColor Cyan
Write-Host "Payload:" -ForegroundColor Yellow
Write-Host $orderPayload

$response = Invoke-WebRequest `
    -Uri "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/orders" `
    -Method POST `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    } `
    -Body $orderPayload `
    -UseBasicParsing

Write-Host "`nResponse Status: $($response.StatusCode)" -ForegroundColor Green
Write-Host "Response Body:" -ForegroundColor Yellow
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
