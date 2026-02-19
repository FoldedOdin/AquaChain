# Complete SES Email Setup for AquaChain
# Verifies sender and recipient emails for development

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$SENDER_EMAIL = "noreply@aquachain.com"

Write-Host "=== AquaChain SES Email Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check current SES status
Write-Host "Step 1: Checking SES account status..." -ForegroundColor Yellow

$accountStatus = aws sesv2 get-account --region $REGION --output json 2>$null | ConvertFrom-Json

if ($accountStatus) {
    $productionAccess = $accountStatus.ProductionAccessEnabled
    $sendingEnabled = $accountStatus.SendingEnabled
    
    Write-Host "  Production Access: $productionAccess" -ForegroundColor $(if ($productionAccess) { "Green" } else { "Yellow" })
    Write-Host "  Sending Enabled: $sendingEnabled" -ForegroundColor $(if ($sendingEnabled) { "Green" } else { "Red" })
    
    if (-not $productionAccess) {
        Write-Host ""
        Write-Host "  ⚠️  SES is in SANDBOX mode" -ForegroundColor Yellow
        Write-Host "  You can only send to verified email addresses" -ForegroundColor Yellow
        Write-Host "  Limit: 200 emails/day, 1 email/second" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Could not retrieve SES account status" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Verify sender email
Write-Host "Step 2: Setting up sender email..." -ForegroundColor Yellow
Write-Host "  Sender: $SENDER_EMAIL" -ForegroundColor Cyan

$senderStatus = aws sesv2 get-email-identity --email-identity $SENDER_EMAIL --region $REGION --output json 2>$null | ConvertFrom-Json

if ($senderStatus) {
    $verified = $senderStatus.VerifiedForSendingStatus
    Write-Host "  Status: $($senderStatus.IdentityType) - Verified: $verified" -ForegroundColor $(if ($verified) { "Green" } else { "Yellow" })
    
    if (-not $verified) {
        Write-Host "  ⚠️  Sender email not verified yet" -ForegroundColor Yellow
        Write-Host "  Check inbox for verification email" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Sending verification email to: $SENDER_EMAIL" -ForegroundColor Cyan
    
    aws sesv2 create-email-identity --email-identity $SENDER_EMAIL --region $REGION 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Verification email sent" -ForegroundColor Green
        Write-Host "  Check inbox: $SENDER_EMAIL" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ Failed to send verification email" -ForegroundColor Red
    }
}

Write-Host ""

# Step 3: Verify recipient email (for testing)
Write-Host "Step 3: Setting up recipient email for testing..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  In SANDBOX mode, you must verify recipient emails too." -ForegroundColor Cyan
Write-Host "  Enter the email address you want to test with:" -ForegroundColor Cyan
Write-Host "  (Press Enter to skip)" -ForegroundColor Gray
Write-Host ""

$recipientEmail = Read-Host "  Recipient email"

if ($recipientEmail) {
    Write-Host ""
    Write-Host "  Checking $recipientEmail..." -ForegroundColor Cyan
    
    $recipientStatus = aws sesv2 get-email-identity --email-identity $recipientEmail --region $REGION --output json 2>$null | ConvertFrom-Json
    
    if ($recipientStatus) {
        $verified = $recipientStatus.VerifiedForSendingStatus
        Write-Host "  Status: Verified: $verified" -ForegroundColor $(if ($verified) { "Green" } else { "Yellow" })
        
        if (-not $verified) {
            Write-Host "  ⚠️  Recipient email not verified yet" -ForegroundColor Yellow
            Write-Host "  Check inbox for verification email" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Sending verification email to: $recipientEmail" -ForegroundColor Cyan
        
        aws sesv2 create-email-identity --email-identity $recipientEmail --region $REGION 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Verification email sent" -ForegroundColor Green
            Write-Host "  Check inbox: $recipientEmail" -ForegroundColor Yellow
        } else {
            Write-Host "  ✗ Failed to send verification email" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "=== Setup Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Check email inboxes for verification links" -ForegroundColor White
Write-Host "   - $SENDER_EMAIL" -ForegroundColor Gray
if ($recipientEmail) {
    Write-Host "   - $recipientEmail" -ForegroundColor Gray
}
Write-Host ""
Write-Host "2. Click verification links in emails" -ForegroundColor White
Write-Host "   (Links expire in 24 hours)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Run this script again to verify status:" -ForegroundColor White
Write-Host "   .\scripts\setup\setup-ses-complete.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test registration with verified email" -ForegroundColor White
Write-Host ""

# Step 4: List all verified identities
Write-Host "=== Currently Verified Identities ===" -ForegroundColor Cyan
Write-Host ""

$identities = aws sesv2 list-email-identities --region $REGION --output json 2>$null | ConvertFrom-Json

if ($identities -and $identities.EmailIdentities) {
    $verifiedCount = 0
    foreach ($identity in $identities.EmailIdentities) {
        $details = aws sesv2 get-email-identity --email-identity $identity.IdentityName --region $REGION --output json 2>$null | ConvertFrom-Json
        
        if ($details.VerifiedForSendingStatus) {
            Write-Host "  ✓ $($identity.IdentityName)" -ForegroundColor Green
            $verifiedCount++
        } else {
            Write-Host "  ⏳ $($identity.IdentityName) (pending verification)" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Total verified: $verifiedCount" -ForegroundColor Cyan
} else {
    Write-Host "  No identities found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Production Access ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "To send emails to ANY address (not just verified ones):" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to AWS Console > Amazon SES" -ForegroundColor White
Write-Host "2. Click 'Get started' or 'Account dashboard'" -ForegroundColor White
Write-Host "3. Click 'Request production access'" -ForegroundColor White
Write-Host "4. Fill out the form:" -ForegroundColor White
Write-Host "   - Use case: Transactional emails (OTP verification)" -ForegroundColor Gray
Write-Host "   - Website URL: Your domain" -ForegroundColor Gray
Write-Host "   - Expected volume: Your estimate" -ForegroundColor Gray
Write-Host "5. Submit and wait for approval (24-48 hours)" -ForegroundColor White
Write-Host ""
Write-Host "Or use AWS CLI:" -ForegroundColor Cyan
Write-Host "  aws sesv2 put-account-details --region $REGION \" -ForegroundColor Gray
Write-Host "    --production-access-enabled \" -ForegroundColor Gray
Write-Host "    --mail-type TRANSACTIONAL \" -ForegroundColor Gray
Write-Host "    --website-url https://aquachain.com \" -ForegroundColor Gray
Write-Host "    --use-case-description 'OTP verification emails for water monitoring system'" -ForegroundColor Gray
Write-Host ""
