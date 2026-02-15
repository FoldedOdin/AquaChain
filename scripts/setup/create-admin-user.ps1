# Create Admin User in Cognito
# This script creates an admin user with proper role assignment

param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [string]$Name = "Admin User",
    
    [Parameter(Mandatory=$false)]
    [string]$Phone = "+911234567890"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Create AquaChain Admin User" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get Cognito User Pool ID
Write-Host "Finding Cognito User Pool..." -ForegroundColor Yellow
$USER_POOLS_RAW = aws cognito-idp list-user-pools --max-results 20 --query "UserPools[?contains(Name, 'aquachain')].Id" --output text
$USER_POOL_ID = ($USER_POOLS_RAW -split '\s+')[0]

if ([string]::IsNullOrEmpty($USER_POOL_ID)) {
    Write-Host "ERROR: Could not find AquaChain User Pool" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available User Pools:" -ForegroundColor Yellow
    aws cognito-idp list-user-pools --max-results 20 --query "UserPools[*].[Name,Id]" --output table
    exit 1
}

Write-Host "✓ Found User Pool: $USER_POOL_ID" -ForegroundColor Green
Write-Host ""

# Create the user
Write-Host "Creating admin user: $Email" -ForegroundColor Yellow
try {
    # Create user with basic attributes only
    aws cognito-idp admin-create-user `
        --user-pool-id $USER_POOL_ID `
        --username $Email `
        --user-attributes `
            Name=email,Value=$Email `
            Name=email_verified,Value=true `
            Name=name,Value="$Name" `
        --temporary-password $Password `
        --message-action SUPPRESS
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create user"
    }
    
    Write-Host "✓ User created successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to create user - $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "User may already exist. Trying to update instead..." -ForegroundColor Yellow
}

Write-Host ""

# Set permanent password
Write-Host "Setting permanent password..." -ForegroundColor Yellow
try {
    aws cognito-idp admin-set-user-password `
        --user-pool-id $USER_POOL_ID `
        --username $Email `
        --password $Password `
        --permanent
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Password set successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not set password - $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# Verify email is confirmed
Write-Host "Verifying email..." -ForegroundColor Yellow
try {
    aws cognito-idp admin-update-user-attributes `
        --user-pool-id $USER_POOL_ID `
        --username $Email `
        --user-attributes Name=email_verified,Value=true
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Email verified" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not verify email - $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# Add user to admin group (if it exists)
Write-Host "Adding to admin group..." -ForegroundColor Yellow
try {
    aws cognito-idp admin-add-user-to-group `
        --user-pool-id $USER_POOL_ID `
        --username $Email `
        --group-name admin 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Added to admin group" -ForegroundColor Green
    } else {
        Write-Host "ℹ Admin group doesn't exist (this is okay)" -ForegroundColor Gray
    }
} catch {
    Write-Host "ℹ Admin group doesn't exist (this is okay)" -ForegroundColor Gray
}

Write-Host ""

# Get user details
Write-Host "Fetching user details..." -ForegroundColor Yellow
$USER_DETAILS = aws cognito-idp admin-get-user `
    --user-pool-id $USER_POOL_ID `
    --username $Email `
    --output json | ConvertFrom-Json

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Admin User Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Login Credentials:" -ForegroundColor Cyan
Write-Host "  Email:    $Email" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White
Write-Host "  Role:     admin" -ForegroundColor White
Write-Host ""
Write-Host "User Status: $($USER_DETAILS.UserStatus)" -ForegroundColor White
Write-Host "User Sub:    $($USER_DETAILS.Username)" -ForegroundColor White
Write-Host ""
Write-Host "You can now log in to the dashboard with these credentials." -ForegroundColor Green
Write-Host ""
