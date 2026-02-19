# Test OTP Registration Flow
# Tests the complete registration workflow end-to-end

$ErrorActionPreference = "Stop"

$API_BASE = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$TEST_EMAIL = "test.user.$(Get-Random -Minimum 1000 -Maximum 9999)@example.com"
$TEST_PASSWORD = "TestPass123!"

Write-Host "=== Testing OTP Registration Flow ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test Email: $TEST_EMAIL" -ForegroundColor Yellow
Write-Host ""

# Test 1: Register new user
Write-Host "Test 1: Register new user" -ForegroundColor Yellow
Write-Host "POST $API_BASE/api/auth/register" -ForegroundColor Gray

$registerBody = @{
    email = $TEST_EMAIL
    password = $TEST_PASSWORD
    firstName = "Test"
    lastName = "User"
    phone = "+919876543210"
    role = "consumer"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/auth/register" `
        -Method POST `
        -Body $registerBody `
        -ContentType "application/json"
    
    Write-Host "✓ Registration successful" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
    
    $userId = $response.userId
    Write-Host "User ID: $userId" -ForegroundColor Cyan
} catch {
    Write-Host "✗ Registration failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Try to register same email again (should fail)
Write-Host "Test 2: Duplicate registration (should fail)" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/auth/register" `
        -Method POST `
        -Body $registerBody `
        -ContentType "application/json"
    
    Write-Host "✗ Should have failed with 409 Conflict" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "✓ Correctly rejected duplicate registration" -ForegroundColor Green
    } else {
        Write-Host "✗ Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 3: Request new OTP
Write-Host "Test 3: Request new OTP" -ForegroundColor Yellow
Write-Host "POST $API_BASE/api/auth/request-otp" -ForegroundColor Gray

$otpRequestBody = @{
    email = $TEST_EMAIL
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/auth/request-otp" `
        -Method POST `
        -Body $otpRequestBody `
        -ContentType "application/json"
    
    Write-Host "✓ OTP request successful" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
} catch {
    Write-Host "✗ OTP request failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""

# Test 4: Verify with wrong OTP (should fail)
Write-Host "Test 4: Verify with wrong OTP (should fail)" -ForegroundColor Yellow

$wrongOtpBody = @{
    email = $TEST_EMAIL
    otp = "000000"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/auth/verify-otp" `
        -Method POST `
        -Body $wrongOtpBody `
        -ContentType "application/json"
    
    Write-Host "✗ Should have failed with invalid OTP" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✓ Correctly rejected invalid OTP" -ForegroundColor Green
    } else {
        Write-Host "✗ Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Manual OTP verification step
Write-Host "=== Manual Verification Required ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "To complete the test:" -ForegroundColor Cyan
Write-Host "1. Check CloudWatch logs for the OTP:" -ForegroundColor White
Write-Host "   aws logs tail /aws/lambda/aquachain-register-dev --follow --region ap-south-1" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or check your email inbox for: $TEST_EMAIL" -ForegroundColor White
Write-Host ""
Write-Host "3. Run the verification command:" -ForegroundColor White
Write-Host "   `$otpCode = Read-Host 'Enter OTP'" -ForegroundColor Gray
Write-Host "   `$verifyBody = @{email='$TEST_EMAIL'; otp=`$otpCode} | ConvertTo-Json" -ForegroundColor Gray
Write-Host "   Invoke-RestMethod -Uri '$API_BASE/api/auth/verify-otp' -Method POST -Body `$verifyBody -ContentType 'application/json'" -ForegroundColor Gray
Write-Host ""

# Test 5: Check verification status
Write-Host "Test 5: Check verification status (before OTP verification)" -ForegroundColor Yellow
Write-Host "GET $API_BASE/api/auth/verification-status/$TEST_EMAIL" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$API_BASE/api/auth/verification-status/$TEST_EMAIL" `
        -Method GET
    
    Write-Host "✓ Status check successful" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
    
    if ($response.verified -eq $false) {
        Write-Host "✓ User correctly marked as unverified" -ForegroundColor Green
    } else {
        Write-Host "✗ User should be unverified at this point" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Status check failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Test Email: $TEST_EMAIL" -ForegroundColor Yellow
Write-Host "Test Password: $TEST_PASSWORD" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Get OTP from CloudWatch logs or email" -ForegroundColor White
Write-Host "2. Verify OTP using the command above" -ForegroundColor White
Write-Host "3. Try logging in with the credentials" -ForegroundColor White
Write-Host ""
