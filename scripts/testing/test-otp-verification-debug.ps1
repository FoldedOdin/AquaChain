# Test OTP Verification with Debug Logging
# This script tests the OTP verification endpoint and checks CloudWatch logs

$API_ENDPOINT = $env:REACT_APP_API_ENDPOINT
if (-not $API_ENDPOINT) {
    $API_ENDPOINT = "https://api.aquachain.cloud"
}

$TEST_EMAIL = "karthikkpradeep123@gmail.com"
$TOKEN = (Get-Content "$env:USERPROFILE\.aquachain\token.txt" -ErrorAction SilentlyContinue)

if (-not $TOKEN) {
    Write-Host "❌ No token found. Please login first." -ForegroundColor Red
    exit 1
}

Write-Host "🧪 Testing OTP Verification Flow with Debug Logging" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Request OTP
Write-Host "📧 Step 1: Requesting OTP..." -ForegroundColor Yellow
$otpRequest = @{
    email = $TEST_EMAIL
    changes = @{
        firstName = "Karthik"
        lastName = "Pradeep"
        email = $TEST_EMAIL
        phone = "+919876543210"
        address = @{
            country = "India"
            pincode = "560001"
            flatHouse = "Test House"
            areaStreet = "Test Street"
            landmark = "Test Landmark"
            city = "Bangalore"
            state = "Karnataka"
            formatted = "Test House, Test Street, Test Landmark, Bangalore, Karnataka, 560001, India"
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_ENDPOINT/api/profile/request-otp" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $TOKEN"
        } `
        -Body $otpRequest
    
    Write-Host "✅ OTP requested successfully" -ForegroundColor Green
    
    if ($response.devOtp) {
        $OTP = $response.devOtp
        Write-Host "🔑 Dev OTP: $OTP" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  No dev OTP in response. Check your email." -ForegroundColor Yellow
        $OTP = Read-Host "Enter OTP from email"
    }
} catch {
    Write-Host "❌ Failed to request OTP: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔐 Step 2: Verifying OTP (this will trigger debug logs)..." -ForegroundColor Yellow

$verifyRequest = @{
    otp = $OTP
    updates = @{
        firstName = "Karthik"
        lastName = "Pradeep"
        email = $TEST_EMAIL
        phone = "+919876543210"
        address = @{
            country = "India"
            pincode = "560001"
            flatHouse = "Test House"
            areaStreet = "Test Street"
            landmark = "Test Landmark"
            city = "Bangalore"
            state = "Karnataka"
            formatted = "Test House, Test Street, Test Landmark, Bangalore, Karnataka, 560001, India"
        }
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_ENDPOINT/api/profile/verify-and-update" `
        -Method PUT `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $TOKEN"
        } `
        -Body $verifyRequest
    
    Write-Host "✅ OTP verified successfully!" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 5)" -ForegroundColor Gray
} catch {
    Write-Host "❌ OTP verification failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Now checking CloudWatch logs for debug information..." -ForegroundColor Yellow
    Write-Host ""
    
    # Wait a moment for logs to be written
    Start-Sleep -Seconds 3
    
    # Get recent logs
    Write-Host "Fetching logs from /aws/lambda/aquachain-function-user-management-dev..." -ForegroundColor Gray
    $logStreams = aws logs describe-log-streams `
        --log-group-name "/aws/lambda/aquachain-function-user-management-dev" `
        --order-by LastEventTime `
        --descending `
        --max-items 1 | ConvertFrom-Json
    
    if ($logStreams.logStreams) {
        $latestStream = $logStreams.logStreams[0].logStreamName
        Write-Host "Latest log stream: $latestStream" -ForegroundColor Gray
        Write-Host ""
        
        $logs = aws logs get-log-events `
            --log-group-name "/aws/lambda/aquachain-function-user-management-dev" `
            --log-stream-name $latestStream `
            --limit 50 | ConvertFrom-Json
        
        Write-Host "=== DEBUG LOGS ===" -ForegroundColor Cyan
        foreach ($event in $logs.events) {
            $message = $event.message
            if ($message -match "DEBUG|Event|headers|requestContext|email") {
                Write-Host $message -ForegroundColor White
            }
        }
    }
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "✅ Test complete. Check logs above for event structure." -ForegroundColor Green
