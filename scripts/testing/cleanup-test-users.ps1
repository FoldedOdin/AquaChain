# Clean up all test consumer users and devices
# Use this to start fresh with registration testing

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$USER_POOL_ID = "ap-south-1_QUDl7hG8u"

Write-Host "=== Cleaning Up Test Data ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  WARNING: This will delete:" -ForegroundColor Yellow
Write-Host "  - All consumer users from Cognito" -ForegroundColor Yellow
Write-Host "  - All consumer users from DynamoDB" -ForegroundColor Yellow
Write-Host "  - All devices from DynamoDB" -ForegroundColor Yellow
Write-Host "  - All OTP records" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Are you sure? Type 'yes' to continue"

if ($confirm -ne 'yes') {
    Write-Host "Cancelled" -ForegroundColor Gray
    exit 0
}

Write-Host ""

# Step 1: List and delete consumer users from Cognito
Write-Host "Step 1: Removing consumer users from Cognito..." -ForegroundColor Yellow

$users = aws cognito-idp list-users-in-group `
    --user-pool-id $USER_POOL_ID `
    --group-name consumers `
    --region $REGION `
    --output json 2>$null | ConvertFrom-Json

if ($users -and $users.Users) {
    Write-Host "  Found $($users.Users.Count) consumer users" -ForegroundColor Cyan
    
    foreach ($user in $users.Users) {
        $username = $user.Username
        $email = ($user.Attributes | Where-Object { $_.Name -eq 'email' }).Value
        
        Write-Host "  Deleting: $email ($username)" -ForegroundColor Gray
        
        aws cognito-idp admin-delete-user `
            --user-pool-id $USER_POOL_ID `
            --username $username `
            --region $REGION 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Deleted from Cognito" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  No consumer users found in Cognito" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Delete consumer users from DynamoDB
Write-Host "Step 2: Removing consumer users from DynamoDB..." -ForegroundColor Yellow

$dynamoUsers = aws dynamodb scan `
    --table-name AquaChain-Users `
    --filter-expression "role = :role" `
    --expression-attribute-values '{":role":{"S":"consumer"}}' `
    --region $REGION `
    --output json 2>$null | ConvertFrom-Json

if ($dynamoUsers -and $dynamoUsers.Items) {
    Write-Host "  Found $($dynamoUsers.Items.Count) consumer users" -ForegroundColor Cyan
    
    foreach ($item in $dynamoUsers.Items) {
        $userId = $item.userId.S
        $email = $item.email.S
        
        Write-Host "  Deleting: $email ($userId)" -ForegroundColor Gray
        
        aws dynamodb delete-item `
            --table-name AquaChain-Users `
            --key "{\"userId\":{\"S\":\"$userId\"}}" `
            --region $REGION 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Deleted from DynamoDB" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  No consumer users found in DynamoDB" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Delete all devices
Write-Host "Step 3: Removing all devices..." -ForegroundColor Yellow

$devices = aws dynamodb scan `
    --table-name AquaChain-Devices `
    --region $REGION `
    --output json 2>$null | ConvertFrom-Json

if ($devices -and $devices.Items) {
    Write-Host "  Found $($devices.Items.Count) devices" -ForegroundColor Cyan
    
    foreach ($item in $devices.Items) {
        $deviceId = $item.deviceId.S
        
        Write-Host "  Deleting device: $deviceId" -ForegroundColor Gray
        
        aws dynamodb delete-item `
            --table-name AquaChain-Devices `
            --key "{\"deviceId\":{\"S\":\"$deviceId\"}}" `
            --region $REGION 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Deleted" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  No devices found" -ForegroundColor Gray
}

Write-Host ""

# Step 4: Clear OTP table
Write-Host "Step 4: Clearing OTP records..." -ForegroundColor Yellow

$otps = aws dynamodb scan `
    --table-name AquaChain-OTP `
    --region $REGION `
    --output json 2>$null | ConvertFrom-Json

if ($otps -and $otps.Items) {
    Write-Host "  Found $($otps.Items.Count) OTP records" -ForegroundColor Cyan
    
    foreach ($item in $otps.Items) {
        $email = $item.email.S
        
        Write-Host "  Deleting OTP for: $email" -ForegroundColor Gray
        
        aws dynamodb delete-item `
            --table-name AquaChain-OTP `
            --key "{\"email\":{\"S\":\"$email\"}}" `
            --region $REGION 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Deleted" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  No OTP records found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Cleanup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "System is now clean. You can:" -ForegroundColor Cyan
Write-Host "  1. Register a new user from the frontend" -ForegroundColor White
Write-Host "  2. Receive OTP via email" -ForegroundColor White
Write-Host "  3. Verify and log in" -ForegroundColor White
Write-Host ""
Write-Host "Note: Admin and technician users were NOT deleted" -ForegroundColor Gray
Write-Host ""
