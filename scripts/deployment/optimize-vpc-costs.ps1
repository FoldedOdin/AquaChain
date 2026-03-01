# VPC Cost Optimization Deployment Script
# Reduces VPC costs for dev environment while maintaining production redundancy

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev',
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VPC Cost Optimization Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate environment
if ($Environment -eq 'prod') {
    Write-Host "WARNING: You are about to modify PRODUCTION infrastructure!" -ForegroundColor Yellow
    Write-Host "Production will maintain 2 NAT Gateways and all VPC endpoints for reliability." -ForegroundColor Yellow
    $confirmation = Read-Host "Type 'CONFIRM-PROD' to proceed"
    if ($confirmation -ne 'CONFIRM-PROD') {
        Write-Host "Deployment cancelled." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Environment: $Environment" -ForegroundColor Green
Write-Host ""

# Display cost savings
Write-Host "Expected Cost Changes:" -ForegroundColor Cyan
if ($Environment -eq 'dev') {
    Write-Host "  - NAT Gateways: 2 -> 1 (saves ~`$35/month)" -ForegroundColor Green
    Write-Host "  - CloudWatch Logs Endpoint: Removed (saves ~`$7.30/month)" -ForegroundColor Green
    Write-Host "  - Secrets Manager Endpoint: Kept (security critical)" -ForegroundColor Yellow
    Write-Host "  - KMS Endpoint: Kept (security critical)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Total Monthly Savings: ~`$42/month" -ForegroundColor Green
} else {
    Write-Host "  - No changes for $Environment (maintains redundancy)" -ForegroundColor Yellow
    Write-Host "  - 2 NAT Gateways: Kept for high availability" -ForegroundColor Yellow
    Write-Host "  - All VPC Endpoints: Kept for performance" -ForegroundColor Yellow
}
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Navigate to CDK directory
$cdkPath = Join-Path $PSScriptRoot "..\..\infrastructure\cdk"
if (-not (Test-Path $cdkPath)) {
    Write-Host "ERROR: CDK directory not found at $cdkPath" -ForegroundColor Red
    exit 1
}

Set-Location $cdkPath

# Check if CDK is installed
Write-Host "Checking CDK installation..." -ForegroundColor Cyan
try {
    $cdkVersion = cdk --version
    Write-Host "  CDK Version: $cdkVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS CDK not found. Install with: npm install -g aws-cdk" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Cyan
try {
    $awsIdentity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "  Account: $($awsIdentity.Account)" -ForegroundColor Green
    Write-Host "  User: $($awsIdentity.Arn)" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS credentials not configured" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Show what will be deployed
Write-Host "Stack to be updated:" -ForegroundColor Cyan
Write-Host "  AquaChain-VPC-$Environment" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
    Write-Host "Running CDK diff to show changes..." -ForegroundColor Cyan
    cdk diff "AquaChain-VPC-$Environment"
    Write-Host ""
    Write-Host "DRY RUN COMPLETE - No changes were made" -ForegroundColor Yellow
    exit 0
}

# Confirm deployment
Write-Host "This will update the VPC stack with cost optimizations." -ForegroundColor Yellow
$confirm = Read-Host "Proceed with deployment? (yes/no)"
if ($confirm -ne 'yes') {
    Write-Host "Deployment cancelled." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Deploying VPC stack..." -ForegroundColor Cyan

# Deploy the stack
try {
    cdk deploy "AquaChain-VPC-$Environment" --require-approval never
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    if ($Environment -eq 'dev') {
        Write-Host "Cost Optimizations Applied:" -ForegroundColor Green
        Write-Host "  ✓ NAT Gateways reduced to 1" -ForegroundColor Green
        Write-Host "  ✓ CloudWatch Logs endpoint removed" -ForegroundColor Green
        Write-Host "  ✓ Estimated savings: ~`$42/month" -ForegroundColor Green
        Write-Host ""
        Write-Host "Note: It may take 5-10 minutes for the old NAT Gateway to be deleted." -ForegroundColor Yellow
        Write-Host "Monitor costs in AWS Cost Explorer after 24 hours." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Deployment Failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check AWS credentials and permissions" -ForegroundColor Yellow
    Write-Host "  2. Verify the VPC stack exists: cdk list" -ForegroundColor Yellow
    Write-Host "  3. Check for resource dependencies" -ForegroundColor Yellow
    Write-Host "  4. Review CloudFormation console for detailed errors" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Verify Lambda functions can still access AWS services" -ForegroundColor White
Write-Host "  2. Check CloudWatch logs are being delivered" -ForegroundColor White
Write-Host "  3. Monitor VPC costs in Cost Explorer after 24 hours" -ForegroundColor White
Write-Host "  4. Review VPC Flow Logs for any connectivity issues" -ForegroundColor White
Write-Host ""
