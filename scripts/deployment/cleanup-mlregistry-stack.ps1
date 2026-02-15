# Cleanup ML Registry Stack
# Deletes changesets and stack that's stuck in REVIEW_IN_PROGRESS

Write-Host "=== Cleaning Up ML Registry Stack ===" -ForegroundColor Cyan
Write-Host ""

$stackName = "AquaChain-MLRegistry-dev"
$region = "ap-south-1"

Write-Host "Step 1: Deleting any pending changesets..." -ForegroundColor Yellow

# List and delete all changesets for this stack
$changesets = aws cloudformation list-change-sets --stack-name $stackName --region $region --query "Summaries[].ChangeSetName" --output text 2>$null

if ($LASTEXITCODE -eq 0 -and $changesets) {
    $changesetList = $changesets -split "`t"
    foreach ($changeset in $changesetList) {
        if ($changeset) {
            Write-Host "  Deleting changeset: $changeset" -ForegroundColor Gray
            aws cloudformation delete-change-set --change-set-name $changeset --stack-name $stackName --region $region 2>$null
        }
    }
    Write-Host "✓ Changesets deleted" -ForegroundColor Green
} else {
    Write-Host "  No changesets found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 2: Checking if stack exists..." -ForegroundColor Yellow

$stackStatus = aws cloudformation describe-stacks --stack-name $stackName --region $region --query "Stacks[0].StackStatus" --output text 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "✓ Stack does not exist" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
    exit 0
}

Write-Host "  Current status: $stackStatus" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 3: Deleting stack..." -ForegroundColor Yellow

aws cloudformation delete-stack --stack-name $stackName --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Stack deletion initiated" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for deletion to complete..." -ForegroundColor Yellow
    
    # Wait for deletion with timeout
    $maxWait = 300  # 5 minutes
    $waited = 0
    $interval = 10
    
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds $interval
        $waited += $interval
        
        $status = aws cloudformation describe-stacks --stack-name $stackName --region $region --query "Stacks[0].StackStatus" --output text 2>$null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✓ Stack deleted successfully!" -ForegroundColor Green
            break
        }
        
        Write-Host "  Status: $status (waited $waited seconds)" -ForegroundColor Gray
        
        if ($status -eq "DELETE_FAILED") {
            Write-Host "✗ Stack deletion failed" -ForegroundColor Red
            Write-Host ""
            Write-Host "You may need to manually delete this stack from the AWS Console:" -ForegroundColor Yellow
            Write-Host "https://ap-south-1.console.aws.amazon.com/cloudformation" -ForegroundColor White
            break
        }
    }
    
    if ($waited -ge $maxWait) {
        Write-Host "⚠ Deletion is taking longer than expected" -ForegroundColor Yellow
        Write-Host "Check AWS Console for status" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Failed to initiate stack deletion" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
