# Update SES sender email to contact.aquachain@gmail.com for all Lambda functions
# This script updates the SES_SENDER_EMAIL environment variable

$NEW_EMAIL = "contact.aquachain@gmail.com"
$REGION = "ap-south-1"

Write-Host "Updating sender email to: $NEW_EMAIL" -ForegroundColor Cyan

# List of Lambda functions that send emails
$lambdaFunctions = @(
    "aquachain-register-dev",
    "aquachain-request-otp-dev",
    "aquachain-verify-otp-dev"
)

Write-Host "`nChecking SES verification status..." -ForegroundColor Yellow
$verification = aws ses get-identity-verification-attributes --identities $NEW_EMAIL --region $REGION | ConvertFrom-Json

$status = $verification.VerificationAttributes.$NEW_EMAIL.VerificationStatus

if ($status -ne "Success") {
    Write-Host "ERROR: Email $NEW_EMAIL is not verified in SES!" -ForegroundColor Red
    Write-Host "Current status: $status" -ForegroundColor Yellow
    Write-Host "`nPlease verify the email first:" -ForegroundColor Yellow
    Write-Host "1. Check inbox at $NEW_EMAIL" -ForegroundColor White
    Write-Host "2. Click the verification link from AWS SES" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host "✓ Email verified successfully!" -ForegroundColor Green

# Update each Lambda function
foreach ($functionName in $lambdaFunctions) {
    Write-Host "`nUpdating $functionName..." -ForegroundColor Yellow
    
    # Get current environment variables
    $currentEnv = aws lambda get-function-configuration `
        --function-name $functionName `
        --region $REGION `
        --query "Environment.Variables" `
        --output json | ConvertFrom-Json
    
    if (-not $currentEnv) {
        Write-Host "  ⚠ Function not found, skipping..." -ForegroundColor Yellow
        continue
    }
    
    # Update SES_SENDER_EMAIL
    $currentEnv | Add-Member -NotePropertyName "SES_SENDER_EMAIL" -NotePropertyValue $NEW_EMAIL -Force
    
    # Convert back to JSON
    $envJson = $currentEnv | ConvertTo-Json -Compress
    
    # Update Lambda function
    aws lambda update-function-configuration `
        --function-name $functionName `
        --environment "Variables=$envJson" `
        --region $REGION | Out-Null
    
    Write-Host "  ✓ Updated successfully" -ForegroundColor Green
}

Write-Host "`n✓ All Lambda functions updated!" -ForegroundColor Green
Write-Host "`nSender email changed from vinodakash03@gmail.com to $NEW_EMAIL" -ForegroundColor Cyan
Write-Host "`nAll OTP and registration emails will now be sent from: $NEW_EMAIL" -ForegroundColor White
