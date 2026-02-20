# Test the routing fix for profile update endpoints
# This verifies that /api/profile/verify-and-update no longer conflicts with /api/profile/update

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Profile Update Routing Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_URL = "https://api.aquachain.cloud"
$TEST_EMAIL = "karthikkpradeep123@gmail.com"
$TEST_PHONE = "+918547613649"

Write-Host "Test Configuration:" -ForegroundColor Yellow
Write-Host "  API URL: $API_URL" -ForegroundColor White
Write-Host "  Test Email: $TEST_EMAIL" -ForegroundColor White
Write-Host "  Test Phone: $TEST_PHONE" -ForegroundColor White
Write-Host ""

# Step 1: Request OTP
Write-Host "Step 1: Requesting OTP for profile update..." -ForegroundColor Yellow
Write-Host ""

$requestBody = @{
    email = $TEST_EMAIL
    updates = @{
        phone = $TEST_PHONE
    }
} | ConvertTo-Json

Write-Host "Request Body:" -ForegroundColor Cyan
Write-Host $requestBody -ForegroundColor White
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/profile/request-otp" `
        -Method POST `
        -ContentType "application/json" `
        -Body $requestBody `
        -ErrorAction Stop
    
    Write-Host "✓ OTP Request Successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor White
    Write-Host ""
    
    if ($response.devOtp) {
        Write-Host "Development OTP: $($response.devOtp)" -ForegroundColor Yellow
        Write-Host ""
        
        # Step 2: Verify OTP and update profile
        Write-Host "Step 2: Verifying OTP and updating profile..." -ForegroundColor Yellow
        Write-Host ""
        
        $verifyBody = @{
            otp = $response.devOtp
            updates = @{
                phone = $TEST_PHONE
            }
        } | ConvertTo-Json
        
        Write-Host "Verify Request Body:" -ForegroundColor Cyan
        Write-Host $verifyBody -ForegroundColor White
        Write-Host ""
        
        try {
            $verifyResponse = Invoke-RestMethod -Uri "$API_URL/api/profile/verify-and-update" `
                -Method PUT `
                -ContentType "application/json" `
                -Body $verifyBody `
                -ErrorAction Stop
            
            Write-Host "✓ Profile Update Successful!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Response:" -ForegroundColor Cyan
            Write-Host ($verifyResponse | ConvertTo-Json -Depth 5) -ForegroundColor White
            Write-Host ""
            
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "All Tests Passed!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "The routing fix is working correctly:" -ForegroundColor Green
            Write-Host "  ✓ /api/profile/request-otp generates OTP" -ForegroundColor White
            Write-Host "  ✓ /api/profile/verify-and-update verifies OTP and updates profile" -ForegroundColor White
            Write-Host "  ✓ No path routing conflicts detected" -ForegroundColor White
            
        } catch {
            Write-Host "✗ Profile Update Failed!" -ForegroundColor Red
            Write-Host ""
            Write-Host "Error Details:" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor White
            Write-Host ""
            
            if ($_.Exception.Response) {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                Write-Host "Response Body:" -ForegroundColor Red
                Write-Host $responseBody -ForegroundColor White
            }
        }
        
    } else {
        Write-Host "⚠ No development OTP in response" -ForegroundColor Yellow
        Write-Host "Check your email for the OTP code" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To complete the test manually:" -ForegroundColor Cyan
        Write-Host "  1. Check email: $TEST_EMAIL" -ForegroundColor White
        Write-Host "  2. Get the 6-digit OTP code" -ForegroundColor White
        Write-Host "  3. Run the verify command with the OTP" -ForegroundColor White
    }
    
} catch {
    Write-Host "✗ OTP Request Failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error Details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor White
    Write-Host ""
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body:" -ForegroundColor Red
        Write-Host $responseBody -ForegroundColor White
    }
}

Write-Host ""
Write-Host "CloudWatch Logs:" -ForegroundColor Cyan
Write-Host "  Check for 'DEBUG EVENT STRUCTURE' messages in:" -ForegroundColor White
Write-Host "  /aws/lambda/aquachain-function-user-management-dev" -ForegroundColor White
Write-Host ""
