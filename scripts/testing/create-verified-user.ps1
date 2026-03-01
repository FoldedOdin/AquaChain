# Create and verify a user manually for testing
# This bypasses the registration flow since auth endpoints aren't deployed

$EMAIL = "karthikkpradeep123@gmail.com"
$PASSWORD = "Test@123456"
$USER_POOL_ID = "ap-south-1_QUDl7hG8u"
$REGION = "ap-south-1"

Write-Host "Creating user in Cognito..." -ForegroundColor Cyan

# Create user in Cognito
$createResult = aws cognito-idp admin-create-user `
    --user-pool-id $USER_POOL_ID `
    --username $EMAIL `
    --user-attributes Name=email,Value=$EMAIL Name=email_verified,Value=true `
    --message-action SUPPRESS `
    --region $REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    if ($createResult -like "*UsernameExistsException*") {
        Write-Host "User already exists, continuing..." -ForegroundColor Yellow
    } else {
        Write-Host "Error creating user: $createResult" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "User created in Cognito" -ForegroundColor Green
}

# Set permanent password
Write-Host "Setting password..." -ForegroundColor Cyan
aws cognito-idp admin-set-user-password `
    --user-pool-id $USER_POOL_ID `
    --username $EMAIL `
    --password $PASSWORD `
    --permanent `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Password set" -ForegroundColor Green
} else {
    Write-Host "Failed to set password" -ForegroundColor Red
}

# Get user sub (userId)
$userInfo = aws cognito-idp admin-get-user `
    --user-pool-id $USER_POOL_ID `
    --username $EMAIL `
    --region $REGION `
    --output json | ConvertFrom-Json

$userId = ($userInfo.UserAttributes | Where-Object { $_.Name -eq "sub" }).Value

Write-Host "User ID: $userId" -ForegroundColor Cyan

# Create DynamoDB record
Write-Host "Creating DynamoDB record..." -ForegroundColor Cyan

$item = @{
    userId = @{ S = $userId }
    email = @{ S = $EMAIL }
    role = @{ S = "consumer" }
    profile = @{
        M = @{
            firstName = @{ S = "Karthik" }
            lastName = @{ S = "Pradeep" }
            phone = @{ S = "+919876543210" }
            address = @{ M = @{} }
        }
    }
    deviceIds = @{ L = @() }
    preferences = @{
        M = @{
            notifications = @{
                M = @{
                    push = @{ BOOL = $true }
                    sms = @{ BOOL = $true }
                    email = @{ BOOL = $true }
                }
            }
            theme = @{ S = "auto" }
            language = @{ S = "en" }
        }
    }
    createdAt = @{ S = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ") }
    updatedAt = @{ S = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ") }
} | ConvertTo-Json -Depth 10 -Compress

$item | Out-File -FilePath user-item.json -Encoding utf8

aws dynamodb put-item `
    --table-name AquaChain-Users `
    --item file://user-item.json `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "DynamoDB record created" -ForegroundColor Green
    Remove-Item user-item.json
} else {
    Write-Host "Failed to create DynamoDB record" -ForegroundColor Red
    Remove-Item user-item.json
    exit 1
}

Write-Host ""
Write-Host "=== User Created Successfully ===" -ForegroundColor Green
Write-Host "Email: $EMAIL" -ForegroundColor Cyan
Write-Host "Password: $PASSWORD" -ForegroundColor Cyan
Write-Host "User ID: $userId" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now log in with these credentials!" -ForegroundColor Green
