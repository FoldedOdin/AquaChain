# Cleanup Failed Pipeline Stack
# This script manually deletes the stuck AquaChain-DeploymentPipeline-dev stack

Write-Host "=== Cleaning Up Failed Pipeline Stack ===" -ForegroundColor Cyan
Write-Host ""

$stackName = "AquaChain-DeploymentPipeline-dev"

Write-Host "Checking stack status..." -ForegroundColor Yellow
$stackStatus = aws cloudformation describe-stacks --stack-name $stackName --query "Stacks[0].StackStatus" --output text 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✓ Stack does not exist or already deleted" -ForegroundColor Green
    exit 0
}

Write-Host "Current status: $stackStatus" -ForegroundColor Yellow

if ($stackStatus -eq "ROLLBACK_FAILED") {
    Write-Host ""
    Write-Host "Stack is in ROLLBACK_FAILED state. Manual cleanup required." -ForegroundColor Red
    Write-Host ""
    Write-Host "Step 1: Delete the stuck CodeDeploy applications manually" -ForegroundColor Cyan
    
    # Try to delete CodeDeploy applications
    Write-Host "Attempting to delete CodeDeploy applications..." -ForegroundColor Yellow
    
    $lambdaApp = "aquachain-deploy-lambda-dev"
    $apiApp = "aquachain-deploy-api-dev"
    
    Write-Host "Deleting Lambda CodeDeploy app: $lambdaApp" -ForegroundColor Yellow
    aws deploy delete-application --application-name $lambdaApp 2>$null
    
    Write-Host "Deleting API CodeDeploy app: $apiApp" -ForegroundColor Yellow
    aws deploy delete-application --application-name $apiApp 2>$null
    
    Write-Host ""
    Write-Host "Step 2: Delete the stack with retain resources" -ForegroundColor Cyan
    Write-Host "Deleting stack: $stackName" -ForegroundColor Yellow
    
    # Delete stack and retain problematic resources
    aws cloudformation delete-stack --stack-name $stackName --retain-resources LambdaDeployApp4499EF7F ApiDeployApp2C0992BD
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stack deletion initiated" -ForegroundColor Green
        Write-Host ""
        Write-Host "Waiting for stack deletion to complete..." -ForegroundColor Yellow
        aws cloudformation wait stack-delete-complete --stack-name $stackName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Stack deleted successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠ Stack deletion may still be in progress. Check AWS Console." -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ Failed to delete stack" -ForegroundColor Red
        Write-Host ""
        Write-Host "Manual steps required:" -ForegroundColor Yellow
        Write-Host "1. Go to AWS CloudFormation Console" -ForegroundColor White
        Write-Host "2. Select stack: $stackName" -ForegroundColor White
        Write-Host "3. Click 'Delete' and select 'Retain' for failed resources" -ForegroundColor White
        Write-Host "4. Confirm deletion" -ForegroundColor White
    }
} else {
    Write-Host "Deleting stack: $stackName" -ForegroundColor Yellow
    aws cloudformation delete-stack --stack-name $stackName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stack deletion initiated" -ForegroundColor Green
        Write-Host "Waiting for completion..." -ForegroundColor Yellow
        aws cloudformation wait stack-delete-complete --stack-name $stackName
        Write-Host "✓ Stack deleted successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to delete stack" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
