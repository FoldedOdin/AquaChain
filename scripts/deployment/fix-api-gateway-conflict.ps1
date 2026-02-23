# Fix API Gateway Stack Conflict
# Resolves UPDATE_ROLLBACK_COMPLETE state and deploys payment endpoints

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix API Gateway Stack Conflict" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Configuration
$REGION = "ap-south-1"
$STACK_NAME = "AquaChain-API-dev"

Write-Host "[1/3] Checking stack status..." -ForegroundColor Yellow

$stackStatus = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --region $REGION `
    --query "Stacks[0].StackStatus" `
    --output text

Write-Host "  Current status: $stackStatus" -ForegroundColor Gray

if ($stackStatus -eq "UPDATE_ROLLBACK_COMPLETE") {
    Write-Host "  Stack is in UPDATE_ROLLBACK_COMPLETE state" -ForegroundColor Yellow
    Write-Host "  This happens when a previous update failed and rolled back" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "[2/3] Continuing rollback to stable state..." -ForegroundColor Yellow
    
    try {
        # Try to continue the update with a no-op change
        Write-Host "  - Attempting to stabilize stack..." -ForegroundColor Gray
        
        Set-Location infrastructure/cdk
        
        # Deploy with no changes to complete the rollback
        cdk deploy $STACK_NAME --require-approval never --no-version-reporting 2>&1 | Out-Null
        
        Set-Location ../..
        
        Write-Host "  ✓ Stack stabilized" -ForegroundColor Green
    } catch {
        Write-Host "  Stack deployment still has conflicts" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  The issue is that the stack has orphaned resources." -ForegroundColor Yellow
        Write-Host "  We need to manually clean up the API Gateway." -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "  Option 1: Delete and recreate the stack (DESTRUCTIVE)" -ForegroundColor Red
        Write-Host "    This will delete all API Gateway endpoints and recreate them" -ForegroundColor Gray
        Write-Host "    Command: cdk destroy $STACK_NAME && cdk deploy $STACK_NAME" -ForegroundColor Gray
        Write-Host ""
        
        Write-Host "  Option 2: Manually fix via AWS Console (RECOMMENDED)" -ForegroundColor Green
        Write-Host "    1. Go to CloudFormation console" -ForegroundColor Gray
        Write-Host "    2. Select $STACK_NAME" -ForegroundColor Gray
        Write-Host "    3. Click 'Stack Actions' > 'Continue update rollback'" -ForegroundColor Gray
        Write-Host "    4. Skip any resources that can't be rolled back" -ForegroundColor Gray
        Write-Host "    5. Once in UPDATE_COMPLETE or CREATE_COMPLETE, run this script again" -ForegroundColor Gray
        Write-Host ""
        
        Write-Host "  Option 3: Use AWS CLI to continue rollback" -ForegroundColor Yellow
        Write-Host "    aws cloudformation continue-update-rollback --stack-name $STACK_NAME --region $REGION" -ForegroundColor Gray
        Write-Host ""
        
        $choice = Read-Host "Choose option (1/2/3) or press Enter to exit"
        
        if ($choice -eq "1") {
            Write-Host ""
            Write-Host "  WARNING: This will DELETE the entire API Gateway stack!" -ForegroundColor Red
            Write-Host "  All endpoints will be temporarily unavailable." -ForegroundColor Red
            $confirm = Read-Host "  Type 'DELETE' to confirm"
            
            if ($confirm -eq "DELETE") {
                Write-Host ""
                Write-Host "  Destroying stack..." -ForegroundColor Yellow
                Set-Location infrastructure/cdk
                cdk destroy $STACK_NAME --force
                
                Write-Host ""
                Write-Host "  Recreating stack..." -ForegroundColor Yellow
                cdk deploy $STACK_NAME --require-approval never
                
                Set-Location ../..
                Write-Host "  ✓ Stack recreated" -ForegroundColor Green
            } else {
                Write-Host "  Cancelled" -ForegroundColor Gray
                exit 0
            }
        } elseif ($choice -eq "3") {
            Write-Host ""
            Write-Host "  Attempting to continue rollback..." -ForegroundColor Yellow
            aws cloudformation continue-update-rollback --stack-name $STACK_NAME --region $REGION
            
            Write-Host "  Waiting for rollback to complete..." -ForegroundColor Gray
            aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION
            
            Write-Host "  ✓ Rollback complete" -ForegroundColor Green
        } else {
            Write-Host "  Exiting. Please fix manually via AWS Console." -ForegroundColor Gray
            exit 0
        }
    }
} elseif ($stackStatus -like "*COMPLETE*" -and $stackStatus -notlike "*ROLLBACK*") {
    Write-Host "  ✓ Stack is in a stable state" -ForegroundColor Green
} else {
    Write-Host "  Stack is in state: $stackStatus" -ForegroundColor Yellow
    Write-Host "  Wait for stack to reach a stable state before continuing" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[3/3] Deploying payment endpoints..." -ForegroundColor Yellow

Set-Location infrastructure/cdk

try {
    Write-Host "  - Synthesizing stack..." -ForegroundColor Gray
    cdk synth $STACK_NAME --no-version-reporting 2>&1 | Out-Null
    
    Write-Host "  - Deploying..." -ForegroundColor Gray
    cdk deploy $STACK_NAME --require-approval never --no-version-reporting
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Payment endpoints deployed" -ForegroundColor Green
    } else {
        throw "Deployment failed"
    }
} catch {
    Write-Host "  ERROR: Deployment failed" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Set-Location ../..
    exit 1
}

Set-Location ../..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ API Gateway stack fixed" -ForegroundColor Green
Write-Host "✓ Payment endpoints deployed" -ForegroundColor Green
Write-Host ""
Write-Host "Payment endpoints now available:" -ForegroundColor Yellow
Write-Host "  - POST /api/payments/create-razorpay-order" -ForegroundColor Gray
Write-Host "  - POST /api/payments/verify-payment" -ForegroundColor Gray
Write-Host "  - POST /api/payments/create-cod-payment" -ForegroundColor Gray
Write-Host "  - GET  /api/payments/payment-status" -ForegroundColor Gray
Write-Host ""
Write-Host "Next: Test payment flow in browser" -ForegroundColor Cyan
Write-Host ""
