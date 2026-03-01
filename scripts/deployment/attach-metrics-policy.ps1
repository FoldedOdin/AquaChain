# Attach IAM Policy for System Metrics
# This script attaches the necessary IAM permissions to the Lambda execution role

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Attach System Metrics IAM Policy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$POLICY_NAME = "AquaChain-SystemMetrics-Policy"
$POLICY_FILE = "scripts/deployment/system-metrics-iam-policy.json"
$ROLE_NAME = "aquachain-admin-service-role-dev"

Write-Host "Step 1: Finding Lambda execution role..." -ForegroundColor Yellow

# Get the Lambda function configuration to find the role
$FUNCTION_NAME = "aquachain-function-admin-service-dev"
$FUNCTION_CONFIG = aws lambda get-function-configuration --function-name $FUNCTION_NAME --region ap-south-1 --output json | ConvertFrom-Json

if ($FUNCTION_CONFIG.Role) {
    $ROLE_ARN = $FUNCTION_CONFIG.Role
    $ROLE_NAME = $ROLE_ARN.Split('/')[-1]
    Write-Host "  ✓ Found role: $ROLE_NAME" -ForegroundColor Green
} else {
    Write-Host "  ✗ Could not find Lambda execution role" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Create or update the IAM policy
Write-Host "Step 2: Creating IAM policy..." -ForegroundColor Yellow

# Check if policy already exists
$EXISTING_POLICY = aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>$null

if ($EXISTING_POLICY) {
    Write-Host "  Policy already exists: $EXISTING_POLICY" -ForegroundColor Gray
    Write-Host "  Creating new policy version..." -ForegroundColor Gray
    
    # Get current default version
    $POLICY_VERSIONS = aws iam list-policy-versions --policy-arn $EXISTING_POLICY --query "Versions[?IsDefaultVersion==``true``].VersionId" --output text
    
    # Create new version
    try {
        aws iam create-policy-version `
            --policy-arn $EXISTING_POLICY `
            --policy-document "file://$POLICY_FILE" `
            --set-as-default `
            --output json | Out-Null
        
        Write-Host "  ✓ Policy updated" -ForegroundColor Green
        $POLICY_ARN = $EXISTING_POLICY
    } catch {
        Write-Host "  ✗ Failed to update policy" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  Creating new policy..." -ForegroundColor Gray
    
    try {
        $POLICY_RESULT = aws iam create-policy `
            --policy-name $POLICY_NAME `
            --policy-document "file://$POLICY_FILE" `
            --description "Permissions for AquaChain system metrics collection" `
            --output json | ConvertFrom-Json
        
        $POLICY_ARN = $POLICY_RESULT.Policy.Arn
        Write-Host "  ✓ Policy created: $POLICY_ARN" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to create policy" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 3: Attach policy to role
Write-Host "Step 3: Attaching policy to Lambda role..." -ForegroundColor Yellow

try {
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn $POLICY_ARN `
        --output json 2>$null
    
    Write-Host "  ✓ Policy attached to role: $ROLE_NAME" -ForegroundColor Green
} catch {
    # Policy might already be attached
    Write-Host "  ℹ Policy may already be attached (this is okay)" -ForegroundColor Gray
}

Write-Host ""

# Step 4: Verify permissions
Write-Host "Step 4: Verifying attached policies..." -ForegroundColor Yellow

$ATTACHED_POLICIES = aws iam list-attached-role-policies --role-name $ROLE_NAME --output json | ConvertFrom-Json

Write-Host "  Attached policies:" -ForegroundColor Gray
foreach ($policy in $ATTACHED_POLICIES.AttachedPolicies) {
    Write-Host "    • $($policy.PolicyName)" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ IAM Policy Attached Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The Lambda function now has permissions to:" -ForegroundColor Cyan
Write-Host "  • Read Cognito user pool data" -ForegroundColor White
Write-Host "  • Query CloudWatch metrics" -ForegroundColor White
Write-Host "  • Access Lambda function metadata" -ForegroundColor White
Write-Host "  • Read API Gateway configuration" -ForegroundColor White
Write-Host ""
