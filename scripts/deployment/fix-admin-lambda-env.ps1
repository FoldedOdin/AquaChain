# Fix Admin Lambda Environment Variables
# This script updates the admin service Lambda with the correct Cognito User Pool ID

$ErrorActionPreference = "Stop"

Write-Host "=== Fixing Admin Lambda Environment Variables ===" -ForegroundColor Cyan

# Get User Pool ID
Write-Host "`nFetching Cognito User Pool ID..." -ForegroundColor Yellow
$userPools = aws cognito-idp list-user-pools --max-results 10 --output json | ConvertFrom-Json
$userPool = $userPools.UserPools | Where-Object { $_.Name -like "*aquachain*users*dev*" } | Select-Object -First 1

if (-not $userPool) {
    Write-Host "ERROR: Could not find AquaChain User Pool" -ForegroundColor Red
    exit 1
}

$userPoolId = $userPool.Id
Write-Host "Found User Pool ID: $userPoolId" -ForegroundColor Green

# Get User Pool Client ID
Write-Host "`nFetching User Pool Client ID..." -ForegroundColor Yellow
$clients = aws cognito-idp list-user-pool-clients --user-pool-id $userPoolId --max-results 10 --output json | ConvertFrom-Json
$client = $clients.UserPoolClients | Where-Object { $_.ClientName -like "*aquachain*web*" } | Select-Object -First 1

if (-not $client) {
    Write-Host "WARNING: Could not find User Pool Client" -ForegroundColor Yellow
    $clientId = ""
} else {
    $clientId = $client.ClientId
    Write-Host "Found Client ID: $clientId" -ForegroundColor Green
}

# Get current Lambda configuration
Write-Host "`nFetching current Lambda configuration..." -ForegroundColor Yellow
$functionName = "aquachain-function-admin-service-dev"
$currentConfig = aws lambda get-function-configuration --function-name $functionName --output json | ConvertFrom-Json

# Prepare updated environment variables
$envVars = @{}
if ($currentConfig.Environment.Variables) {
    $currentConfig.Environment.Variables.PSObject.Properties | ForEach-Object {
        $envVars[$_.Name] = $_.Value
    }
}

# Update with Cognito values
$envVars["USER_POOL_ID"] = $userPoolId
$envVars["COGNITO_USER_POOL_ID"] = $userPoolId
if ($clientId) {
    $envVars["COGNITO_CLIENT_ID"] = $clientId
}

# Convert to JSON format for AWS CLI
$envVarsJson = @{
    Variables = $envVars
} | ConvertTo-Json -Compress -Depth 10

Write-Host "`nUpdating Lambda environment variables..." -ForegroundColor Yellow
Write-Host "New environment variables:" -ForegroundColor Cyan
$envVars.GetEnumerator() | Sort-Object Name | ForEach-Object {
    if ($_.Name -like "*POOL*" -or $_.Name -like "*CLIENT*") {
        Write-Host "  $($_.Name) = $($_.Value)" -ForegroundColor White
    }
}

# Update Lambda function
aws lambda update-function-configuration `
    --function-name $functionName `
    --environment $envVarsJson `
    --output json | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Successfully updated Lambda environment variables" -ForegroundColor Green
    Write-Host "`nWaiting for Lambda to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host "✓ Lambda is ready" -ForegroundColor Green
} else {
    Write-Host "`n✗ Failed to update Lambda environment variables" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Fix Complete ===" -ForegroundColor Cyan
Write-Host "The admin dashboard should now be able to fetch users successfully." -ForegroundColor Green
