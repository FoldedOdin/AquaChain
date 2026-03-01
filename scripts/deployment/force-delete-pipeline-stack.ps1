# Force Delete Pipeline Stack
# This script uses AWS CLI to force delete the stuck stack

Write-Host "=== Force Deleting Pipeline Stack ===" -ForegroundColor Cyan
Write-Host ""

$stackName = "AquaChain-DeploymentPipeline-dev"
$region = "ap-south-1"

Write-Host "Attempting to delete stack: $stackName" -ForegroundColor Yellow
Write-Host ""

# Try direct delete first
Write-Host "Method 1: Direct delete..." -ForegroundColor Cyan
aws cloudformation delete-stack --stack-name $stackName --region $region 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Delete initiated successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for deletion to complete (this may take a few minutes)..." -ForegroundColor Yellow
    
    # Wait for deletion
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 10
        $attempt++
        
        $status = aws cloudformation describe-stacks --stack-name $stackName --region $region --query "Stacks[0].StackStatus" --output text 2>$null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✓ Stack deleted successfully!" -ForegroundColor Green
            break
        }
        
        Write-Host "  Status: $status (attempt $attempt/$maxAttempts)" -ForegroundColor Gray
        
        if ($status -eq "DELETE_COMPLETE") {
            Write-Host "✓ Stack deleted successfully!" -ForegroundColor Green
            break
        }
        
        if ($status -eq "DELETE_FAILED") {
            Write-Host "✗ Delete failed" -ForegroundColor Red
            break
        }
    }
} else {
    Write-Host "✗ Direct delete failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Manual Cleanup Instructions ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If the stack is still stuck, follow these steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Open AWS Console: https://ap-south-1.console.aws.amazon.com/cloudformation" -ForegroundColor White
Write-Host "2. Find stack: $stackName" -ForegroundColor White
Write-Host "3. Click 'Delete'" -ForegroundColor White
Write-Host "4. If prompted, check 'Retain resources' for any failed resources" -ForegroundColor White
Write-Host "5. Confirm deletion" -ForegroundColor White
Write-Host ""
Write-Host "The stack should be deleted within 5-10 minutes." -ForegroundColor Gray
Write-Host ""
