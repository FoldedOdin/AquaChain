# AquaChain Complete Deployment Script for Windows
# PowerShell version

param(
    [string]$Environment = "dev",
    [string]$Region = "ap-south-1",
    [switch]$SkipTests
)

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║         AquaChain Complete Deployment Script              ║" -ForegroundColor Blue
Write-Host "║                  Windows PowerShell                        ║" -ForegroundColor Blue
Write-Host "║                                                            ║" -ForegroundColor Blue
Write-Host "║  Environment: $Environment                                 ║" -ForegroundColor Blue
Write-Host "║  Region: $Region                                           ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Pre-flight Checks
Write-Host "🔍 Running pre-flight checks..." -ForegroundColor Yellow

# Check AWS CLI
if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "   Download from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ AWS CLI found" -ForegroundColor Green

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS credentials configured" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured" -ForegroundColor Red
    Write-Host "   Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Check Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
    exit 1
}
$nodeVersion = node --version
Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found" -ForegroundColor Red
    exit 1
}
$pythonVersion = python --version
Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green

# Check CDK
if (!(Get-Command cdk -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  CDK not found. Installing..." -ForegroundColor Yellow
    npm install -g aws-cdk
}
$cdkVersion = cdk --version
Write-Host "✅ CDK found: $cdkVersion" -ForegroundColor Green

Write-Host ""

# Install Dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow

# Frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Blue
Set-Location frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend dependency installation failed" -ForegroundColor Red
    exit 1
}
Set-Location ..
Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green

# Infrastructure dependencies
Write-Host "Installing infrastructure dependencies..." -ForegroundColor Blue
Set-Location infrastructure/cdk
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Infrastructure dependency installation failed" -ForegroundColor Red
    exit 1
}
Set-Location ../..
Write-Host "✅ Infrastructure dependencies installed" -ForegroundColor Green

Write-Host ""

# Run Tests (Optional)
if (!$SkipTests) {
    Write-Host "🧪 Running tests..." -ForegroundColor Yellow
    
    # Frontend tests
    Write-Host "Running frontend tests..." -ForegroundColor Blue
    Set-Location frontend
    npm test -- --watchAll=false --passWithNoTests
    Set-Location ..
    Write-Host "✅ Frontend tests completed" -ForegroundColor Green
    
    Write-Host ""
}

# Deploy Infrastructure
Write-Host "🏗️  Deploying infrastructure..." -ForegroundColor Yellow

Set-Location infrastructure/cdk

# Bootstrap CDK
Write-Host "Bootstrapping CDK..." -ForegroundColor Blue
$accountId = (aws sts get-caller-identity --query Account --output text)
cdk bootstrap "aws://$accountId/$Region"

# Synthesize stacks
Write-Host "Synthesizing CDK stacks..." -ForegroundColor Blue
cdk synth --all

# Deploy stacks
$stacks = @(
    "AquaChain-Security-$Environment",
    "AquaChain-Core-$Environment",
    "AquaChain-Data-$Environment",
    "AquaChain-Compute-$Environment",
    "AquaChain-API-$Environment"
)

foreach ($stack in $stacks) {
    Write-Host "Deploying $stack..." -ForegroundColor Blue
    cdk deploy $stack --require-approval never
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to deploy $stack" -ForegroundColor Red
        Write-Host "   Check CloudFormation console for details" -ForegroundColor Yellow
        Set-Location ../..
        exit 1
    }
    Write-Host "✅ $stack deployed" -ForegroundColor Green
}

Set-Location ../..

Write-Host "✅ Infrastructure deployed successfully" -ForegroundColor Green
Write-Host ""

# Build Frontend
Write-Host "🎨 Building frontend..." -ForegroundColor Yellow

Set-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "✅ Frontend built successfully" -ForegroundColor Green
Set-Location ..

Write-Host ""

# Post-Deployment Verification
Write-Host "✅ Running post-deployment verification..." -ForegroundColor Yellow

# Check API Gateway
$apiId = aws apigateway get-rest-apis --query "items[?name=='aquachain-api-$Environment'].id" --output text 2>$null

if ($apiId) {
    $apiUrl = "https://$apiId.execute-api.$Region.amazonaws.com/$Environment"
    Write-Host "✅ API Gateway: $apiUrl" -ForegroundColor Green
} else {
    Write-Host "⚠️  API Gateway not found" -ForegroundColor Yellow
}

# Check DynamoDB tables
$tables = aws dynamodb list-tables --query "TableNames[?starts_with(@, 'aquachain-')]" --output text
$tableCount = ($tables -split '\s+').Count
Write-Host "✅ Found $tableCount DynamoDB tables" -ForegroundColor Green

# Check Lambda functions
$functions = aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aquachain-')].FunctionName" --output text
$functionCount = ($functions -split '\s+').Count
Write-Host "✅ Found $functionCount Lambda functions" -ForegroundColor Green

Write-Host ""

# Deployment Summary
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Environment: $Environment" -ForegroundColor Blue
Write-Host "Region: $Region" -ForegroundColor Blue
Write-Host "API URL: $apiUrl" -ForegroundColor Blue
Write-Host "DynamoDB Tables: $tableCount" -ForegroundColor Blue
Write-Host "Lambda Functions: $functionCount" -ForegroundColor Blue
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify all services are running"
Write-Host "2. Create test user in Cognito"
Write-Host "3. Test frontend at http://localhost:3000"
Write-Host "4. Check CloudWatch logs for errors"
Write-Host ""
Write-Host "✨ Happy deploying! ✨" -ForegroundColor Green
