# Setup SES Email for OTP Delivery
# Verifies sender email address in AWS SES

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$SENDER_EMAIL = "noreply@aquachain.com"

Write-Host "=== Setting Up SES Email ===" -ForegroundColor Cyan
Write-Host ""

# Check if email is already verified
Write-Host "Checking verification status..." -ForegroundColor Yellow

$verificationStatus = aws ses get-identity-verification-attributes `
    --identities $SENDER_EMAIL `
    --region $REGION `
    --query "VerificationAttributes.""$SENDER_EMAIL"".VerificationStatus" `
    --output text 2>$null

if ($verificationStatus -eq "Success") {
    Write-Host "✓ Email already verified: $SENDER_EMAIL" -ForegroundColor Green
    Write-Host ""
    Write-Host "You're all set! The registration flow can send emails." -ForegroundColor Green
    exit 0
}

# Verify email address
Write-Host "Sending verification email to: $SENDER_EMAIL" -ForegroundColor Cyan

aws ses verify-email-identity `
    --email-address $SENDER_EMAIL `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Verification email sent" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== Next Steps ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Check the inbox for: $SENDER_EMAIL" -ForegroundColor White
    Write-Host "2. Click the verification link in the email from AWS" -ForegroundColor White
    Write-Host "3. Run this script again to confirm verification" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: The verification link expires in 24 hours" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To check status manually:" -ForegroundColor Cyan
    Write-Host "aws ses get-identity-verification-attributes --identities $SENDER_EMAIL --region $REGION" -ForegroundColor Gray
} else {
    Write-Host "✗ Failed to send verification email" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "- AWS CLI not configured correctly" -ForegroundColor White
    Write-Host "- Insufficient IAM permissions (need ses:VerifyEmailIdentity)" -ForegroundColor White
    Write-Host "- Invalid email address format" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "=== SES Sandbox Mode ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your SES account is currently in SANDBOX mode, which means:" -ForegroundColor Cyan
Write-Host "- You can only send emails to verified addresses" -ForegroundColor White
Write-Host "- Maximum 200 emails per 24 hours" -ForegroundColor White
Write-Host "- Maximum 1 email per second" -ForegroundColor White
Write-Host ""
Write-Host "For production use, request production access:" -ForegroundColor Yellow
Write-Host "1. Go to AWS Console > SES > Account Dashboard" -ForegroundColor White
Write-Host "2. Click 'Request production access'" -ForegroundColor White
Write-Host "3. Fill out the form with your use case" -ForegroundColor White
Write-Host "4. Wait for AWS approval (usually 24-48 hours)" -ForegroundColor White
Write-Host ""
