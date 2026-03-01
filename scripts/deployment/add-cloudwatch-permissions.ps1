# Add CloudWatch Permissions to Lambda Role
# This script adds the required CloudWatch permissions for metrics queries

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Add CloudWatch Permissions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ROLE_NAME = "aquachain-lambda-admin-service-role"
$POLICY_NAME = "CloudWatchMetricsRead"
$REGION = "ap-south-1"

Write-Host "Step 1: Create CloudWatch policy document..." -ForegroundColor Yellow

# Create policy document
$policyDocument = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "cloudwatch:GetMetricStatistics"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 10

# Save to temp file
$policyFile = "cloudwatch-policy.json"
$policyDocument | Out-File -FilePath $policyFile -Encoding utf8

Write-Host "  ✓ Policy document created" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Attach policy to Lambda role..." -ForegroundColor Yellow

# Check if role exists
$roleExists = aws iam get-role --role-name $ROLE_NAME --region $REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Role '$ROLE_NAME' not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available roles:" -ForegroundColor Yellow
    aws iam list-roles --query "Roles[?contains(RoleName, 'aquachain')].RoleName" --output table
    Write-Host ""
    Write-Host "Please update the ROLE_NAME variable in this script with the correct role name." -ForegroundColor Yellow
    Remove-Item $policyFile -ErrorAction SilentlyContinue
    exit 1
}

# Attach inline policy to role
aws iam put-role-policy `
    --role-name $ROLE_NAME `
    --policy-name $POLICY_NAME `
    --policy-document file://$policyFile `
    --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to attach policy" -ForegroundColor Red
    Remove-Item $policyFile -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "  ✓ Policy attached successfully" -ForegroundColor Green
Write-Host ""

# Clean up temp file
Remove-Item $policyFile -ErrorAction SilentlyContinue

Write-Host "Step 3: Verify policy attachment..." -ForegroundColor Yellow

# Get role policy
$policy = aws iam get-role-policy `
    --role-name $ROLE_NAME `
    --policy-name $POLICY_NAME `
    --region $REGION `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Policy verified" -ForegroundColor Green
    Write-Host ""
    Write-Host "Policy Details:" -ForegroundColor Cyan
    Write-Host "  Role: $ROLE_NAME" -ForegroundColor White
    Write-Host "  Policy: $POLICY_NAME" -ForegroundColor White
    Write-Host "  Permissions: cloudwatch:GetMetricStatistics" -ForegroundColor White
} else {
    Write-Host "  ⚠ Could not verify policy (but it may have been attached)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "CloudWatch Permissions Added!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
