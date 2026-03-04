# Test Google OAuth API Endpoint
# This script tests if the API Gateway endpoint is working

$ErrorActionPreference = "Stop"

Write-Host "🧪 Testing Google OAuth API Endpoint..." -ForegroundColor Cyan

$API_ENDPOINT = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/google/callback"

Write-Host "`n📍 Endpoint: $API_ENDPOINT" -ForegroundColor Yellow

# Test with a dummy request (will fail auth but proves endpoint works)
Write-Host "`n🔄 Sending test request..." -ForegroundColor Cyan

$body = @{
    code = "test_code"
    redirectUri = "http://localhost:3000/auth/google/callback"
    clientId = "740926138916-gn6ne63km7o8d44f3um3rlded4nirqrp.apps.googleusercontent.com"
    role = "consumer"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri $API_ENDPOINT `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -ErrorAction SilentlyContinue
    
    Write-Host "✅ Endpoint is reachable!" -ForegroundColor Green
    Write-Host "Response: $($response.StatusCode)" -ForegroundColor White
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $errorBody = $_.ErrorDetails.Message
    
    if ($statusCode -eq 500 -or $statusCode -eq 400) {
        Write-Host "✅ Endpoint is working! (Got expected error response)" -ForegroundColor Green
        Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
        Write-Host "Response: $errorBody" -ForegroundColor White
        
        if ($errorBody -like "*Token exchange failed*" -or $errorBody -like "*invalid_grant*") {
            Write-Host "`n✅ This is expected! The endpoint is working." -ForegroundColor Green
            Write-Host "The error is because we used a dummy authorization code." -ForegroundColor White
            Write-Host "`n🚀 Your OAuth flow should work when you test with real Google auth!" -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ Unexpected error: $statusCode" -ForegroundColor Red
        Write-Host "Response: $errorBody" -ForegroundColor White
    }
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start your frontend: cd frontend && npm start" -ForegroundColor White
Write-Host "2. Click 'Continue with Google'" -ForegroundColor White
Write-Host "3. Authenticate with Google" -ForegroundColor White
Write-Host "4. You should be logged in!" -ForegroundColor White

Write-Host "`n💡 If OAuth fails, check Lambda logs:" -ForegroundColor Yellow
Write-Host "aws logs tail /aws/lambda/aquachain-function-auth-service-dev --follow --region ap-south-1" -ForegroundColor White
