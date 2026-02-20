# Direct DynamoDB update for user profile
# Bypasses Lambda to update user profile directly

param(
    [string]$Email = "karthikkpradeep123@gmail.com",
    [string]$FirstName = "Karthik",
    [string]$LastName = "Pradeep"
)

Write-Host "Updating user profile directly in DynamoDB..." -ForegroundColor Cyan
Write-Host "Email: $Email" -ForegroundColor Yellow
Write-Host "Name: $FirstName $LastName" -ForegroundColor Yellow

# First, find the user by email
Write-Host "`nFinding user..." -ForegroundColor Yellow
$filterExpression = "email = :email"
$expressionAttributeValues = "{`":email`":{`"S`":`"$Email`"}}"

$users = aws dynamodb scan `
    --table-name AquaChain-Users `
    --filter-expression $filterExpression `
    --expression-attribute-values $expressionAttributeValues `
    --region ap-south-1 | ConvertFrom-Json

if ($users.Items.Count -eq 0) {
    Write-Host "✗ User not found with email: $Email" -ForegroundColor Red
    exit 1
}

$user = $users.Items[0]
$userId = $user.userId.S

Write-Host "✓ Found user: $userId" -ForegroundColor Green

# Update the user profile
Write-Host "`nUpdating profile..." -ForegroundColor Yellow

$key = @{
    userId = @{ S = $userId }
} | ConvertTo-Json -Compress

$updateExpression = "SET profile.firstName = :firstName, profile.lastName = :lastName, updatedAt = :updatedAt"
$expressionValues = @{
    ":firstName" = @{ S = $FirstName }
    ":lastName" = @{ S = $LastName }
    ":updatedAt" = @{ S = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ") }
} | ConvertTo-Json -Compress

aws dynamodb update-item `
    --table-name AquaChain-Users `
    --key $key `
    --update-expression $updateExpression `
    --expression-attribute-values $expressionValues `
    --region ap-south-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Profile updated successfully!" -ForegroundColor Green
    
    # Verify the update
    Write-Host "`nVerifying update..." -ForegroundColor Yellow
    
    $keyForGet = @{
        userId = @{ S = $userId }
    } | ConvertTo-Json -Compress
    
    $updated = aws dynamodb get-item `
        --table-name AquaChain-Users `
        --key $keyForGet `
        --region ap-south-1 | ConvertFrom-Json
    
    $profile = $updated.Item.profile.M
    Write-Host "First Name: $($profile.firstName.S)" -ForegroundColor Cyan
    Write-Host "Last Name: $($profile.lastName.S)" -ForegroundColor Cyan
    
} else {
    Write-Host "`n✗ Failed to update profile" -ForegroundColor Red
    exit 1
}
