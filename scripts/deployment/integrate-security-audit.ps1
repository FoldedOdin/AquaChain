# Integrate Security Audit Logging with Existing Lambda Functions
# This script deploys the security audit logger and updates Lambda functions

Write-Host "Integrating Security Audit Logging..." -ForegroundColor Cyan

$ENVIRONMENT = "dev"
$REGION = "us-east-1"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$TABLE_NAME = "AquaChain-SecurityAuditLogs-$ENVIRONMENT"

# Step 1: Create Lambda Layer
Write-Host "`n[1/4] Creating Lambda Layer for Security Audit Logger..." -ForegroundColor Yellow
Set-Location lambda/shared

# Create layer directory structure
if (Test-Path python) { Remove-Item -Recurse -Force python }
New-Item -ItemType Directory -Force -Path python | Out-Null
Copy-Item security_audit_logger.py python/

# Create zip file
if (Test-Path security-audit-layer.zip) { Remove-Item security-audit-layer.zip }
Compress-Archive -Path python -DestinationPath security-audit-layer.zip -Force

# Publish layer
Write-Host "Publishing Lambda layer..." -ForegroundColor Gray
$layerOutput = aws lambda publish-layer-version `
    --layer-name aquachain-security-audit `
    --description "Security audit logging utilities" `
    --zip-file fileb://security-audit-layer.zip `
    --compatible-runtimes python3.11 `
    --output json

$layerArn = ($layerOutput | ConvertFrom-Json).LayerVersionArn
Write-Host "✓ Lambda Layer created: $layerArn" -ForegroundColor Green

# Cleanup
Remove-Item -Recurse -Force python
Remove-Item security-audit-layer.zip

Set-Location ../..

# Step 2: Update Data Processing Lambda
Write-Host "`n[2/4] Updating Data Processing Lambda..." -ForegroundColor Yellow

# Get current function config
$dataProcessingFunc = "AquaChain-DataProcessing-$ENVIRONMENT"
Write-Host "Checking if $dataProcessingFunc exists..." -ForegroundColor Gray

$funcExists = aws lambda get-function --function-name $dataProcessingFunc 2>$null
if ($LASTEXITCODE -eq 0) {
    # Add layer
    Write-Host "Adding layer to $dataProcessingFunc..." -ForegroundColor Gray
    aws lambda update-function-configuration `
        --function-name $dataProcessingFunc `
        --layers $layerArn `
        --output json | Out-Null
    
    # Wait for update to complete
    Start-Sleep -Seconds 5
    
    # Add environment variable
    Write-Host "Adding environment variable..." -ForegroundColor Gray
    $currentEnv = aws lambda get-function-configuration `
        --function-name $dataProcessingFunc `
        --query 'Environment.Variables' `
        --output json
    
    if ($currentEnv) {
        $envVars = $currentEnv | ConvertFrom-Json
        $envVars | Add-Member -NotePropertyName "SECURITY_AUDIT_TABLE" -NotePropertyValue $TABLE_NAME -Force
        
        $envJson = ($envVars | ConvertTo-Json -Compress).Replace('"', '\"')
        
        aws lambda update-function-configuration `
            --function-name $dataProcessingFunc `
            --environment "Variables=$envJson" `
            --output json | Out-Null
    }
    
    Write-Host "✓ Data Processing Lambda updated" -ForegroundColor Green
} else {
    Write-Host "⚠ $dataProcessingFunc not found, skipping..." -ForegroundColor Yellow
}

# Step 3: Update Admin Service Lambda
Write-Host "`n[3/4] Updating Admin Service Lambda..." -ForegroundColor Yellow

$adminServiceFunc = "AquaChain-AdminService-$ENVIRONMENT"
Write-Host "Checking if $adminServiceFunc exists..." -ForegroundColor Gray

$funcExists = aws lambda get-function --function-name $adminServiceFunc 2>$null
if ($LASTEXITCODE -eq 0) {
    # Add layer
    Write-Host "Adding layer to $adminServiceFunc..." -ForegroundColor Gray
    aws lambda update-function-configuration `
        --function-name $adminServiceFunc `
        --layers $layerArn `
        --output json | Out-Null
    
    # Wait for update to complete
    Start-Sleep -Seconds 5
    
    # Add environment variable
    Write-Host "Adding environment variable..." -ForegroundColor Gray
    $currentEnv = aws lambda get-function-configuration `
        --function-name $adminServiceFunc `
        --query 'Environment.Variables' `
        --output json
    
    if ($currentEnv) {
        $envVars = $currentEnv | ConvertFrom-Json
        $envVars | Add-Member -NotePropertyName "SECURITY_AUDIT_TABLE" -NotePropertyValue $TABLE_NAME -Force
        
        $envJson = ($envVars | ConvertTo-Json -Compress).Replace('"', '\"')
        
        aws lambda update-function-configuration `
            --function-name $adminServiceFunc `
            --environment "Variables=$envJson" `
            --output json | Out-Null
    }
    
    Write-Host "✓ Admin Service Lambda updated" -ForegroundColor Green
} else {
    Write-Host "⚠ $adminServiceFunc not found, skipping..." -ForegroundColor Yellow
}

# Step 4: Grant DynamoDB Permissions
Write-Host "`n[4/4] Granting DynamoDB Permissions..." -ForegroundColor Yellow

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
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${TABLE_NAME}",
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${TABLE_NAME}/index/*"
      ]
    }
  ]
}
"@

# Update Data Processing Lambda role
if (aws lambda get-function --function-name "AquaChain-DataProcessing-$ENVIRONMENT" 2>$null) {
    $dataProcessingRole = (aws lambda get-function-configuration `
        --function-name "AquaChain-DataProcessing-$ENVIRONMENT" `
        --query 'Role' `
        --output text) -replace '.*/', ''
    
    Write-Host "Updating IAM policy for $dataProcessingRole..." -ForegroundColor Gray
    $policyDocument | Out-File -FilePath policy.json -Encoding utf8
    
    aws iam put-role-policy `
        --role-name $dataProcessingRole `
        --policy-name SecurityAuditAccess `
        --policy-document file://policy.json | Out-Null
    
    Remove-Item policy.json
    Write-Host "✓ Permissions granted to Data Processing Lambda" -ForegroundColor Green
}

# Update Admin Service Lambda role
if (aws lambda get-function --function-name "AquaChain-AdminService-$ENVIRONMENT" 2>$null) {
    $adminServiceRole = (aws lambda get-function-configuration `
        --function-name "AquaChain-AdminService-$ENVIRONMENT" `
        --query 'Role' `
        --output text) -replace '.*/', ''
    
    Write-Host "Updating IAM policy for $adminServiceRole..." -ForegroundColor Gray
    $policyDocument | Out-File -FilePath policy.json -Encoding utf8
    
    aws iam put-role-policy `
        --role-name $adminServiceRole `
        --policy-name SecurityAuditAccess `
        --policy-document file://policy.json | Out-Null
    
    Remove-Item policy.json
    Write-Host "✓ Permissions granted to Admin Service Lambda" -ForegroundColor Green
}

# Verification
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "Integration Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nVerifying deployment..." -ForegroundColor Yellow

# Check table exists
$tableStatus = aws dynamodb describe-table `
    --table-name $TABLE_NAME `
    --query 'Table.TableStatus' `
    --output text 2>$null

if ($tableStatus -eq "ACTIVE") {
    Write-Host "✓ DynamoDB table is active" -ForegroundColor Green
} else {
    Write-Host "✗ DynamoDB table not found or not active" -ForegroundColor Red
}

# Check Lambda layer
if (aws lambda get-function --function-name "AquaChain-DataProcessing-$ENVIRONMENT" 2>$null) {
    $layers = aws lambda get-function-configuration `
        --function-name "AquaChain-DataProcessing-$ENVIRONMENT" `
        --query 'Layers[*].Arn' `
        --output text

    if ($layers -match "aquachain-security-audit") {
        Write-Host "✓ Lambda layer attached to Data Processing" -ForegroundColor Green
    } else {
        Write-Host "✗ Lambda layer not attached to Data Processing" -ForegroundColor Red
    }
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Redeploy your Lambda functions to pick up the code changes"
Write-Host "  2. Send a test IoT reading to verify audit logging"
Write-Host "  3. Make an admin API call to test admin action logging"
Write-Host "  4. Check the Security Audit Logs table for entries"

Write-Host "`nTest Commands:" -ForegroundColor Cyan
Write-Host "  # View recent audit logs"
Write-Host "  aws dynamodb scan --table-name $TABLE_NAME --limit 10 --query 'Items[*].[deviceId.S,timestamp.S,anomalyType.S,wqi.N]' --output table"
Write-Host ""
Write-Host "  # Check Lambda logs for audit logging"
Write-Host "  aws logs tail /aws/lambda/AquaChain-DataProcessing-$ENVIRONMENT --follow --filter-pattern 'Security audit'"
