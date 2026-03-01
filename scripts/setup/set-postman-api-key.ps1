# Set Postman API Key as environment variable
# Replace YOUR_API_KEY_HERE with your actual Postman API key

$apiKey = Read-Host "Enter your Postman API Key" -AsSecureString
$apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey))

# Set for current session
$env:POSTMAN_API_KEY = $apiKeyPlain

# Set permanently for user
[System.Environment]::SetEnvironmentVariable('POSTMAN_API_KEY', $apiKeyPlain, 'User')

Write-Host "✓ POSTMAN_API_KEY set successfully!" -ForegroundColor Green
Write-Host "✓ Restart Kiro for changes to take effect" -ForegroundColor Yellow
