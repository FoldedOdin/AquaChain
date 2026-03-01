# Deploy Security Audit Stack
# This script deploys the enhanced security audit infrastructure

Write-Host "Deploying Security Audit Stack..." -ForegroundColor Cyan

# Set environment
$env:CDK_DEFAULT_ACCOUNT = (aws sts get-caller-identity --query Account --output text)
$env:CDK_DEFAULT_REGION = "us-east-1"

# Navigate to CDK directory
Set-Location infrastructure/cdk

# Install dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Synthesize CloudFormation template
Write-Host "`nSynthesizing CloudFormation template..." -ForegroundColor Yellow
cdk synth AquaChain-SecurityAudit-dev

# Deploy stack
Write-Host "`nDeploying Security Audit Stack..." -ForegroundColor Yellow
cdk deploy AquaChain-SecurityAudit-dev --require-approval never

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Security Audit Stack deployed successfully!" -ForegroundColor Green
    
    # Populate test data
    Write-Host "`nPopulating test data..." -ForegroundColor Yellow
    Set-Location ../../scripts/testing
    python populate-security-audit-logs.py
    
    Write-Host "`n✓ Deployment complete!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Test the API endpoints"
    Write-Host "  2. Verify data in DynamoDB tables"
    Write-Host "  3. Check CloudWatch logs for any errors"
} else {
    Write-Host "`n✗ Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
}

# Return to root directory
Set-Location ../..
