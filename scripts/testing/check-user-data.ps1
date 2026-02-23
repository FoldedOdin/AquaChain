# Check User Data in DynamoDB
# This script queries DynamoDB to see the actual data structure for a user

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Check User Data in DynamoDB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TABLE_NAME = "AquaChain-Users"
$REGION = "ap-south-1"
$EMAIL = "karthikkpradeep123@gmail.com"  # Update this to the actual user email

Write-Host "Searching for user with email: $EMAIL" -ForegroundColor Yellow
Write-Host ""

try {
    # Scan table for user by email (since we don't have the userId)
    Write-Host "Querying DynamoDB..." -ForegroundColor White
    
    $result = aws dynamodb scan `
        --table-name $TABLE_NAME `
        --filter-expression "email = :email" `
        --expression-attribute-values '{":email":{"S":"'$EMAIL'"}}' `
        --region $REGION | ConvertFrom-Json
    
    if ($result.Items.Count -eq 0) {
        Write-Host "❌ User not found in DynamoDB" -ForegroundColor Red
        Write-Host ""
        Write-Host "Possible reasons:" -ForegroundColor Yellow
        Write-Host "1. Email address is incorrect" -ForegroundColor White
        Write-Host "2. User was not properly created during registration" -ForegroundColor White
        Write-Host "3. Table name is incorrect" -ForegroundColor White
        exit 1
    }
    
    Write-Host "✓ User found!" -ForegroundColor Green
    Write-Host ""
    
    # Parse the DynamoDB item
    $item = $result.Items[0]
    
    Write-Host "User Data Structure:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Gray
    
    # Extract key fields
    $userId = if ($item.userId.S) { $item.userId.S } else { "N/A" }
    $email = if ($item.email.S) { $item.email.S } else { "N/A" }
    $role = if ($item.role.S) { $item.role.S } else { "N/A" }
    
    Write-Host "userId: $userId" -ForegroundColor White
    Write-Host "email: $email" -ForegroundColor White
    Write-Host "role: $role" -ForegroundColor White
    Write-Host ""
    
    # Check profile structure
    if ($item.profile) {
        Write-Host "profile: (nested object)" -ForegroundColor Yellow
        
        if ($item.profile.M) {
            $profile = $item.profile.M
            
            if ($profile.firstName) {
                Write-Host "  firstName: $($profile.firstName.S)" -ForegroundColor White
            }
            if ($profile.lastName) {
                Write-Host "  lastName: $($profile.lastName.S)" -ForegroundColor White
            }
            if ($profile.phone) {
                Write-Host "  phone: $($profile.phone.S)" -ForegroundColor Green
            } else {
                Write-Host "  phone: NOT SET ❌" -ForegroundColor Red
            }
            if ($profile.address) {
                Write-Host "  address: (object)" -ForegroundColor White
            }
        }
    } else {
        Write-Host "profile: NOT FOUND ❌" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Full Item (JSON):" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Gray
    $result.Items[0] | ConvertTo-Json -Depth 10
    Write-Host "========================================" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "Analysis:" -ForegroundColor Cyan
    
    if ($item.profile.M.phone) {
        Write-Host "✓ Phone number IS present in DynamoDB at profile.phone" -ForegroundColor Green
        Write-Host "  Value: $($item.profile.M.phone.S)" -ForegroundColor White
        Write-Host ""
        Write-Host "The issue is likely:" -ForegroundColor Yellow
        Write-Host "1. Lambda is not returning the data correctly" -ForegroundColor White
        Write-Host "2. Frontend is not parsing the response correctly" -ForegroundColor White
        Write-Host "3. API Gateway is returning 502 before Lambda completes" -ForegroundColor White
    } else {
        Write-Host "❌ Phone number is NOT in DynamoDB" -ForegroundColor Red
        Write-Host ""
        Write-Host "The phone number needs to be added to the database." -ForegroundColor Yellow
        Write-Host "You can update it using the AWS Console or CLI." -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Error querying DynamoDB" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you have:" -ForegroundColor Yellow
    Write-Host "1. AWS CLI configured with correct credentials" -ForegroundColor White
    Write-Host "2. Permissions to read from DynamoDB" -ForegroundColor White
    Write-Host "3. Correct table name and region" -ForegroundColor White
}

Write-Host ""
