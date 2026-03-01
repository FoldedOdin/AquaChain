# Deploy Security Audit Integration
# This script integrates security audit logging with existing Lambda functions

Write-Host "Deploying Security Audit Integration..." -ForegroundColor Cyan

$ENVIRONMENT = "dev"
$REGION = "us-east-1"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# Step 1: Deploy Security Audit Stack
Write-Host "`n[1/5] Deploying Security Audit Stack..." -ForegroundColor Yellow
Set-Location infrastructure/cdk
cdk deploy AquaChain-SecurityAudit-$ENVIRONMENT --require-approval never

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Stack deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Security Audit Stack deployed" -ForegroundColor Green

# Step 2: Create Lambda Layer for Security Audit Logger
Write-Host "`n[2/5] Creating Lambda Layer..." -ForegroundColor Yellow
Set-Location ../../lambda/shared

# Create layer directory structure
New-Item -ItemType Directory -Force -Path python | Out-Null
Copy-Item security_audit_logger.py python/

# Create zip file
Compress-Archive -Path python -DestinationPath security-audit-layer.zip -Force

# Publish layer
$layerArn = aws lambda publish-layer-version `
    --layer-name aquachain-security-audit `
    --description "Security audit logging utilities" `
    --zip-file fileb://security-audit-layer.zip `
    --compatible-runtimes python3.11 `
    --query 'LayerVersionArn' `
    --output text

Write-Host "✓ Lambda Layer created: $layerArn" -ForegroundColor Green

# Cleanup
Remove-Item -Recurse -Force python
Remove-Item security-audit-layer.zip

# Step 3: Update Data Processing Lambda
Write-Host "`n[3/5] Updating Data Processing Lambda..." -ForegroundColor Yellow

# Add layer
aws lambda update-function-configuration `
    --function-name AquaChain-DataProcessing-$ENVIRONMENT `
    --layers $layerArn | Out-Null

# Add environment variable
$existingVars = aws lambda get-function-configuration `
    --function-name AquaChain-DataProcessing-$ENVIRONMENT `
    --query 'Environment.Variables' `
    --output json | ConvertFrom-Json

$existingVars | Add-Member -NotePropertyName "SECURITY_AUDIT_TABLE" -NotePropertyValue "AquaChain-SecurityAuditLogs-$ENVIRONMENT" -Force

$varsJson = $existingVars | ConvertTo-Json -Compress

aws lambda update-function-configuration `
    --function-name AquaChain-DataProcessing-$ENVIRONMENT `
    --environment "Variables=$varsJson" | Out-Null

Write-Host "✓ Data Processing Lambda updated" -ForegroundColor Green

# Step 4: Update Admin Service Lambda
Write-Host "`n[4/5] Updating Admin Service Lambda..." -ForegroundColor Yellow

# Add layer
aws lambda update-function-configuration `
    --function-name AquaChain-AdminService-$ENVIRONMENT `
    --layers $layerArn | Out-Null

# Add environment variable
$existingVars = aws lambda get-function-configuration `
    --function-name AquaChain-AdminService-$ENVIRONMENT `
    --query 'Environment.Variables' `
    --output json | ConvertFrom-Json

$existingVars | Add-Member -NotePropertyName "SECURITY_AUDIT_TABLE" -NotePropertyValue "AquaChain-SecurityAuditLogs-$ENVIRONMENT" -Force

$varsJson = $existingVars | ConvertTo-Json -Compress

aws lambda update-function-configuration `
    --function-name AquaChain-AdminService-$ENVIRONMENT `
    --environment "Variables=$varsJson" | Out-Null

Write-Host "✓ Admin Service Lambda updated" -ForegroundColor Green

# Step 5: Grant DynamoDB Permissions
Write-Host "`n[5/5] Granting DynamoDB Permissions..." -ForegroundColor Yellow

$policyDocument = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/AquaChain-SecurityAuditLogs-${ENVIRONMENT}",
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/AquaChain-SecurityAuditLogs-${ENVIRONMENT}/index/*"
      ]
    }
  ]
}
"@

# Update Data Processing Lambda role
$dataProcessingRole = aws lambda get-function-configuration `
    --function-name AquaChain-DataProcessing-$ENVIRONMENT `
    --query 'Role' `
    --output text | Split-Path -Leaf

aws iam put-role-policy `
    --role-name $dataProcessingRole `
    --policy-name SecurityAuditAccess `
    --policy-document $policyDocument | Out-Null

# Update Admin Service Lambda role
$adminServiceRole = aws lambda get-function-configuration `
    --function-name AquaChain-AdminService-$ENVIRONMENT `
    --query 'Role' `
    --output text | Split-Path -Leaf

aws iam put-role-policy `
    --role-name $adminServiceRole `
    --policy-name SecurityAuditAccess `
    --policy-document $policyDocument | Out-Null

Write-Host "✓ DynamoDB permissions granted" -ForegroundColor Green

# Verification
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nVerifying deployment..." -ForegroundColor Yellow

# Check table exists
$tableStatus = aws dynamodb describe-table `
    --table-name AquaChain-SecurityAuditLogs-$ENVIRONMENT `
    --query 'Table.TableStatus' `
    --output text 2>$null

if ($tableStatus -eq "ACTIVE") {
    Write-Host "✓ DynamoDB table is active" -ForegroundColor Green
} else {
    Write-Host "✗ DynamoDB table not found or not active" -ForegroundColor Red
}

# Check Lambda layer
$layers = aws lambda get-function-configuration `
    --function-name AquaChain-DataProcessing-$ENVIRONMENT `
    --query 'Layers[*].Arn' `
    --output text

if ($layers -match "aquachain-security-audit") {
    Write-Host "✓ Lambda layer attached" -ForegroundColor Green
} else {
    Write-Host "✗ Lambda layer not attached" -ForegroundColor Red
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Send a test IoT reading to verify audit logging"
Write-Host "  2. Make an admin API call to test admin action logging"
Write-Host "  3. Check the admin dashboard Security Audit Logs tab"
Write-Host "  4. Review CloudWatch logs for any errors"

Write-Host "`nTest Commands:" -ForegroundColor Cyan
Write-Host "  # View recent audit logs"
Write-Host "  aws dynamodb scan --table-name AquaChain-SecurityAuditLogs-$ENVIRONMENT --limit 10"
Write-Host ""
Write-Host "  # Check Lambda logs"
Write-Host "  aws logs tail /aws/lambda/AquaChain-DataProcessing-$ENVIRONMENT --follow"

Set-Location ../..
