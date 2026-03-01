# Test to understand the token format stored in frontend

Write-Host "Checking token format..." -ForegroundColor Cyan

# Check if .env.local has a token
if (Test-Path "frontend/.env.local") {
    Write-Host "`nChecking frontend/.env.local..." -ForegroundColor Yellow
    $envContent = Get-Content "frontend/.env.local"
    $tokenLine = $envContent | Select-String "TOKEN"
    if ($tokenLine) {
        Write-Host "Found token-related lines:" -ForegroundColor Green
        $tokenLine
    } else {
        Write-Host "No TOKEN found in .env.local" -ForegroundColor Red
    }
}

# Get a real token from Cognito for the test user
Write-Host "`nGetting fresh token from Cognito..." -ForegroundColor Yellow

$authResult = aws cognito-idp initiate-auth `
    --client-id 692o9a3pjudl1vudfgqpr5nuln `
    --auth-flow USER_PASSWORD_AUTH `
    --auth-parameters USERNAME=karthikkpradeep123@gmail.com,PASSWORD=Hu8hyxf1TPf3cwl@ `
    --region ap-south-1 | ConvertFrom-Json

if ($authResult.AuthenticationResult) {
    $idToken = $authResult.AuthenticationResult.IdToken
    
    Write-Host "`n✓ Got ID Token!" -ForegroundColor Green
    Write-Host "Token length: $($idToken.Length) characters" -ForegroundColor Cyan
    Write-Host "Token preview: $($idToken.Substring(0, [Math]::Min(50, $idToken.Length)))..." -ForegroundColor Gray
    
    # Decode the token to see what's inside
    Write-Host "`nDecoding token payload..." -ForegroundColor Yellow
    $parts = $idToken.Split('.')
    if ($parts.Length -eq 3) {
        $payload = $parts[1]
        # Add padding
        $payload += '=' * (4 - $payload.Length % 4)
        $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload))
        $tokenData = $decoded | ConvertFrom-Json
        
        Write-Host "`nToken contains:" -ForegroundColor Cyan
        Write-Host "  Email: $($tokenData.email)" -ForegroundColor White
        Write-Host "  Sub (User ID): $($tokenData.sub)" -ForegroundColor White
        Write-Host "  Token Use: $($tokenData.token_use)" -ForegroundColor White
        Write-Host "  Expiration: $($tokenData.exp)" -ForegroundColor White
    }
    
    # Save token to a file for testing
    $idToken | Out-File -FilePath "test-token.txt" -Encoding utf8 -NoNewline
    Write-Host "`n✓ Token saved to test-token.txt" -ForegroundColor Green
    
} else {
    Write-Host "`n✗ Failed to get token" -ForegroundColor Red
    Write-Host "Error: $($authResult | ConvertTo-Json)" -ForegroundColor Red
}
