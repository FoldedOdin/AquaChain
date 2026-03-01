# Test Authentication Flow
# This script helps diagnose 401 authentication errors

Write-Host "=== AquaChain Authentication Flow Test ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_ENDPOINT = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
$USER_POOL_ID = "ap-south-1_QUDl7hG8u"
$CLIENT_ID = "692o9a3pjudl1vudfgqpr5nuln"
$REGION = "ap-south-1"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  API Endpoint: $API_ENDPOINT"
Write-Host "  User Pool ID: $USER_POOL_ID"
Write-Host "  Client ID: $CLIENT_ID"
Write-Host "  Region: $REGION"
Write-Host ""

# Step 1: Check if user is logged in (get token from browser localStorage)
Write-Host "Step 1: Token Check" -ForegroundColor Green
Write-Host "  Please check your browser's localStorage for 'aquachain_token'"
Write-Host "  Open DevTools > Application > Local Storage > http://localhost:3000"
Write-Host ""
Write-Host "  Enter your token (or press Enter to skip): " -NoNewline
$token = Read-Host

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "  No token provided. Please log in first." -ForegroundColor Red
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Open http://localhost:3000 in your browser"
    Write-Host "  2. Log in with your credentials"
    Write-Host "  3. Open DevTools (F12)"
    Write-Host "  4. Go to Application > Local Storage"
    Write-Host "  5. Copy the value of 'aquachain_token'"
    Write-Host "  6. Run this script again and paste the token"
    exit 1
}

Write-Host "  Token received (length: $($token.Length) chars)" -ForegroundColor Green
Write-Host ""

# Step 2: Decode JWT token (basic check)
Write-Host "Step 2: Token Analysis" -ForegroundColor Green
try {
    $parts = $token.Split('.')
    if ($parts.Length -ne 3) {
        Write-Host "  ERROR: Invalid JWT format (expected 3 parts, got $($parts.Length))" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Token format: Valid JWT (3 parts)" -ForegroundColor Green
    
    # Decode payload (base64url)
    $payload = $parts[1]
    # Add padding if needed
    while ($payload.Length % 4 -ne 0) {
        $payload += "="
    }
    $payload = $payload.Replace('-', '+').Replace('_', '/')
    $payloadJson = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload))
    $payloadObj = $payloadJson | ConvertFrom-Json
    
    Write-Host "  Token Type: $($payloadObj.token_use)" -ForegroundColor Cyan
    Write-Host "  Issuer: $($payloadObj.iss)" -ForegroundColor Cyan
    Write-Host "  Client ID: $($payloadObj.client_id)" -ForegroundColor Cyan
    Write-Host "  Username: $($payloadObj.username)" -ForegroundColor Cyan
    Write-Host "  Expiration: $(Get-Date -UnixTimeSeconds $payloadObj.exp)" -ForegroundColor Cyan
    
    # Check if token is expired
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($now -gt $payloadObj.exp) {
        Write-Host "  WARNING: Token is EXPIRED!" -ForegroundColor Red
        Write-Host "  Please log in again to get a fresh token." -ForegroundColor Yellow
        exit 1
    } else {
        $remaining = $payloadObj.exp - $now
        Write-Host "  Token valid for: $([math]::Floor($remaining / 60)) minutes" -ForegroundColor Green
    }
    
    # Check token type
    if ($payloadObj.token_use -ne "id") {
        Write-Host "  WARNING: Token type is '$($payloadObj.token_use)' but API Gateway expects 'id' token" -ForegroundColor Yellow
        Write-Host "  This might be the cause of 401 errors!" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ERROR: Failed to decode token: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Test API endpoints
Write-Host "Step 3: API Endpoint Tests" -ForegroundColor Green
Write-Host ""

$endpoints = @(
    @{ Path = "/dashboard/stats"; Method = "GET"; Description = "Dashboard Stats" },
    @{ Path = "/water-quality/latest"; Method = "GET"; Description = "Latest Water Quality" },
    @{ Path = "/api/devices"; Method = "GET"; Description = "Device List" },
    @{ Path = "/alerts?limit=20"; Method = "GET"; Description = "Alerts" },
    @{ Path = "/api/notifications"; Method = "GET"; Description = "Notifications" }
)

$successCount = 0
$failCount = 0

foreach ($endpoint in $endpoints) {
    $url = "$API_ENDPOINT$($endpoint.Path)"
    Write-Host "  Testing: $($endpoint.Description)" -NoNewline
    
    try {
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-WebRequest -Uri $url -Method $endpoint.Method -Headers $headers -ErrorAction Stop
        
        Write-Host " - " -NoNewline
        Write-Host "SUCCESS ($($response.StatusCode))" -ForegroundColor Green
        $successCount++
        
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host " - " -NoNewline
        
        if ($statusCode -eq 401) {
            Write-Host "FAILED (401 Unauthorized)" -ForegroundColor Red
            Write-Host "    This is the authentication error!" -ForegroundColor Yellow
        } elseif ($statusCode -eq 403) {
            Write-Host "FAILED (403 Forbidden)" -ForegroundColor Red
            Write-Host "    Token is valid but user lacks permissions" -ForegroundColor Yellow
        } elseif ($statusCode -eq 404) {
            Write-Host "FAILED (404 Not Found)" -ForegroundColor Yellow
            Write-Host "    Endpoint doesn't exist" -ForegroundColor Yellow
        } else {
            Write-Host "FAILED ($statusCode)" -ForegroundColor Red
        }
        
        $failCount++
    }
}

Write-Host ""
Write-Host "Results: $successCount passed, $failCount failed" -ForegroundColor Cyan
Write-Host ""

# Step 4: Diagnosis and recommendations
Write-Host "Step 4: Diagnosis" -ForegroundColor Green
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "  All tests passed! Authentication is working correctly." -ForegroundColor Green
} else {
    Write-Host "  Authentication issues detected. Possible causes:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Token Type Mismatch:" -ForegroundColor Cyan
    Write-Host "     - API Gateway expects ID token, but you might be sending Access token"
    Write-Host "     - Check AuthContext.tsx getAuthToken() method"
    Write-Host "     - Should use: session.tokens?.idToken (not accessToken)"
    Write-Host ""
    Write-Host "  2. Cognito Authorizer Configuration:" -ForegroundColor Cyan
    Write-Host "     - Verify API Gateway authorizer is configured correctly"
    Write-Host "     - Check: AWS Console > API Gateway > Authorizers"
    Write-Host "     - User Pool ID should match: $USER_POOL_ID"
    Write-Host ""
    Write-Host "  3. Token Source Configuration:" -ForegroundColor Cyan
    Write-Host "     - API Gateway looks for token in 'Authorization' header"
    Write-Host "     - Format should be: 'Bearer <token>'"
    Write-Host "     - Verify all services use this format"
    Write-Host ""
    Write-Host "  4. CORS Configuration:" -ForegroundColor Cyan
    Write-Host "     - Ensure CORS allows Authorization header"
    Write-Host "     - Check API Gateway CORS settings"
    Write-Host ""
}

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
