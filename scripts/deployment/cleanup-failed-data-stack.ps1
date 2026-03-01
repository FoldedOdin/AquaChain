# Cleanup Failed Data Stack
# Deletes the AquaChain-Data-dev stack that's in UPDATE_ROLLBACK_COMPLETE state

Write-Host "=== Cleaning Up Failed Data Stack ===" -ForegroundColor Cyan
Write-Host ""

$stackName = "AquaChain-Data-dev"
$region = "ap-south-1"

Write-Host "Checking stack status..." -ForegroundColor Yellow
$stackStatus = aws cloudformation describe-stacks --stack-name $stackName --region $region --query "Stacks[0].StackStatus" --output text 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✓ Stack does not exist" -ForegroundColor Green
    exit 0
}

Write-Host "Current status: $stackStatus" -ForegroundColor Yellow
Write-Host ""

if ($stackStatus -eq "UPDATE_ROLLBACK_COMPLETE") {
    Write-Host "Stack is in UPDATE_ROLLBACK_COMPLETE state. Deleting..." -ForegroundColor Yellow
    
    aws cloudformation delete-stack --stack-name $stackName --region $region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stack deletion initiated" -ForegroundColor Green
        Write-Host ""
        Write-Host "Waiting for deletion to complete (this may take a few minutes)..." -ForegroundColor Yellow
        
        aws cloudformation wait stack-delete-complete --stack-name $stackName --region $region
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Stack deleted successfully!" -ForegroundColor Green
        } else {
            Write-Host "⚠ Stack deletion may still be in progress. Check AWS Console." -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ Failed to delete stack" -ForegroundColor Red
    }
} else {
    Write-Host "Stack is in $stackStatus state." -ForegroundColor Yellow
    Write-Host "Attempting to delete anyway..." -ForegroundColor Yellow
    
    aws cloudformation delete-stack --stack-name $stackName --region $region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stack deletion initiated" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to delete stack" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
