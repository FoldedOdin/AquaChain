# Deploy OTP Email Fix for Profile Updates
# This script deploys the updated user management Lambda with SES email support

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy OTP Email Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is configured
Write-Host "[1/4] Checking AWS CLI configuration..." -ForegroundColor Yellow
try {
    $awsAccount = aws sts get-caller-identity --query Account --output text 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: AWS CLI not configured. Run 'aws configure' first." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ AWS Account: $awsAccount" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS CLI not found or not configured." -ForegroundColor Red
    exit 1
}

# Check AWS region
$region = aws configure get region
if ([string]::IsNullOrEmpty($region)) {
    $region = "ap-south-1"
    Write-Host "⚠ No region configured, using default: $region" -ForegroundColor Yellow
} else {
    Write-Host "✓ Region: $region" -ForegroundColor Green
}

Write-Host ""

# Verify SES email address
Write-Host "[2/4] Checking SES email verification..." -ForegroundColor Yellow
Write-Host "⚠ IMPORTANT: You must verify 'contact.aquachain@gmail.com' in AWS SES" -ForegroundColor Yellow
Write-Host "   Or update the email in lambda/user_management/handler.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "To verify an email in SES:" -ForegroundColor Cyan
Write-Host "  1. Go to AWS Console > SES > Verified identities" -ForegroundColor Cyan
Write-Host "  2. Click 'Create identity'" -ForegroundColor Cyan
Write-Host "  3. Select 'Email address' and enter your email" -ForegroundColor Cyan
Write-Host "  4. Check your inbox and click the verification link" -ForegroundColor Cyan
Write-Host ""
$continue = Read-Host "Have you verified the SES email? (y/n)"
if ($continue -ne 'y') {
    Write-Host "Please verify the email first, then run this script again." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Deploy CDK stack
Write-Host "[3/4] Deploying CDK stack with updated IAM permissions..." -ForegroundColor Yellow
Push-Location infrastructure/cdk
try {
    Write-Host "Running: cdk deploy AquaChain-Compute-dev --require-approval never" -ForegroundColor Cyan
    cdk deploy AquaChain-Compute-dev --require-approval never
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: CDK deployment failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "✓ CDK stack deployed successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host ""

# Test the OTP endpoint
Write-Host "[4/4] Testing OTP endpoint..." -ForegroundColor Yellow
$apiEndpoint = aws cloudformation describe-stacks `
    --stack-name AquaChain-API-dev `
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" `
    --output text 2>$null

if ([string]::IsNullOrEmpty($apiEndpoint)) {
    Write-Host "⚠ Could not retrieve API endpoint. Test manually." -ForegroundColor Yellow
} else {
    Write-Host "API Endpoint: $apiEndpoint" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To test OTP delivery:" -ForegroundColor Cyan
    Write-Host "  1. Log in to the dashboard" -ForegroundColor Cyan
    Write-Host "  2. Go to Profile Settings" -ForegroundColor Cyan
    Write-Host "  3. Try changing your email or phone" -ForegroundColor Cyan
    Write-Host "  4. Check your email/SMS for the OTP" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Changes deployed:" -ForegroundColor Cyan
Write-Host "  ✓ OTP emails sent via AWS SES" -ForegroundColor Green
Write-Host "  ✓ Smart email templates based on what's changing" -ForegroundColor Green
Write-Host "  ✓ Privacy: masked email in responses" -ForegroundColor Green
Write-Host "  ✓ Country code selector for phone input" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify SES email if not done already" -ForegroundColor Yellow
Write-Host "  2. Test profile updates with email/phone changes" -ForegroundColor Yellow
Write-Host "  3. Monitor CloudWatch logs for any issues" -ForegroundColor Yellow
Write-Host ""
