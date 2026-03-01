# Create DynamoDB Tables Manually
# This script creates all required DynamoDB tables when CDK deployment fails

Write-Host "=== AquaChain DynamoDB Manual Setup ===" -ForegroundColor Cyan
Write-Host ""

$region = "ap-south-1"
$tables = @()

# Function to create table
function Create-DynamoDBTable {
    param(
        [string]$TableName,
        [string]$PartitionKey,
        [string]$PartitionKeyType,
        [string]$SortKey = $null,
        [string]$SortKeyType = $null
    )
    
    Write-Host "Creating table: $TableName" -ForegroundColor Yellow
    
    $keySchema = @(
        @{
            AttributeName = $PartitionKey
            KeyType = "HASH"
        }
    )
    
    $attributeDefinitions = @(
        @{
            AttributeName = $PartitionKey
            AttributeType = $PartitionKeyType
        }
    )
    
    if ($SortKey) {
        $keySchema += @{
            AttributeName = $SortKey
            KeyType = "RANGE"
        }
        $attributeDefinitions += @{
            AttributeName = $SortKey
            AttributeType = $SortKeyType
        }
    }
    
    $keySchemaJson = $keySchema | ConvertTo-Json -Compress
    $attributeDefsJson = $attributeDefinitions | ConvertTo-Json -Compress
    
    aws dynamodb create-table `
        --table-name $TableName `
        --key-schema $keySchemaJson `
        --attribute-definitions $attributeDefsJson `
        --billing-mode PAY_PER_REQUEST `
        --region $region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Table created: $TableName" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ✗ Failed to create: $TableName" -ForegroundColor Red
        return $false
    }
}

# Function to create GSI
function Create-GSI {
    param(
        [string]$TableName,
        [string]$IndexName,
        [string]$PartitionKey,
        [string]$PartitionKeyType,
        [string]$SortKey = $null,
        [string]$SortKeyType = $null
    )
    
    Write-Host "  Creating GSI: $IndexName on $TableName" -ForegroundColor Gray
    
    # Wait for table to be active
    Start-Sleep -Seconds 5
    
    $keySchema = @(
        @{
            AttributeName = $PartitionKey
            KeyType = "HASH"
        }
    )
    
    $attributeDefinitions = @(
        @{
            AttributeName = $PartitionKey
            AttributeType = $PartitionKeyType
        }
    )
    
    if ($SortKey) {
        $keySchema += @{
            AttributeName = $SortKey
            KeyType = "RANGE"
        }
        $attributeDefinitions += @{
            AttributeName = $SortKey
            AttributeType = $SortKeyType
        }
    }
    
    $keySchemaJson = $keySchema | ConvertTo-Json -Compress
    $attributeDefsJson = $attributeDefinitions | ConvertTo-Json -Compress
    
    $gsiSpec = @{
        IndexName = $IndexName
        KeySchema = $keySchema
        Projection = @{
            ProjectionType = "ALL"
        }
    } | ConvertTo-Json -Depth 10 -Compress
    
    aws dynamodb update-table `
        --table-name $TableName `
        --attribute-definitions $attributeDefsJson `
        --global-secondary-index-updates "[{`"Create`":$gsiSpec}]" `
        --region $region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ GSI created: $IndexName" -ForegroundColor Green
    } else {
        Write-Host "    ⚠ GSI may already exist or failed: $IndexName" -ForegroundColor Yellow
    }
}

Write-Host "This script will create 8 DynamoDB tables for AquaChain" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tables to create:" -ForegroundColor Yellow
Write-Host "  1. AquaChain-Readings" -ForegroundColor White
Write-Host "  2. AquaChain-Ledger" -ForegroundColor White
Write-Host "  3. AquaChain-Sequence" -ForegroundColor White
Write-Host "  4. AquaChain-Users" -ForegroundColor White
Write-Host "  5. AquaChain-ServiceRequests" -ForegroundColor White
Write-Host "  6. AquaChain-Devices" -ForegroundColor White
Write-Host "  7. AquaChain-AuditLogs" -ForegroundColor White
Write-Host "  8. AquaChain-SystemConfig" -ForegroundColor White
Write-Host ""

$response = Read-Host "Do you want to proceed? (y/n)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Creating tables..." -ForegroundColor Cyan
Write-Host ""

# 1. Readings Table
if (Create-DynamoDBTable -TableName "AquaChain-Readings" -PartitionKey "deviceId_month" -PartitionKeyType "S" -SortKey "timestamp" -SortKeyType "S") {
    Create-GSI -TableName "AquaChain-Readings" -IndexName "DeviceIndex" -PartitionKey "deviceId" -PartitionKeyType "S" -SortKey "timestamp" -SortKeyType "S"
    Start-Sleep -Seconds 10
    Create-GSI -TableName "AquaChain-Readings" -IndexName "device_id-metric_type-index" -PartitionKey "deviceId" -PartitionKeyType "S" -SortKey "metric_type" -SortKeyType "S"
}

Write-Host ""

# 2. Ledger Table
Create-DynamoDBTable -TableName "AquaChain-Ledger" -PartitionKey "ledgerId" -PartitionKeyType "S" -SortKey "sequence" -SortKeyType "N"

Write-Host ""

# 3. Sequence Table
Create-DynamoDBTable -TableName "AquaChain-Sequence" -PartitionKey "sequenceName" -PartitionKeyType "S"

Write-Host ""

# 4. Users Table
if (Create-DynamoDBTable -TableName "AquaChain-Users" -PartitionKey "userId" -PartitionKeyType "S") {
    Create-GSI -TableName "AquaChain-Users" -IndexName "EmailIndex" -PartitionKey "email" -PartitionKeyType "S"
    Start-Sleep -Seconds 10
    Create-GSI -TableName "AquaChain-Users" -IndexName "RoleIndex" -PartitionKey "role" -PartitionKeyType "S" -SortKey "createdAt" -SortKeyType "S"
}

Write-Host ""

# 5. Service Requests Table
if (Create-DynamoDBTable -TableName "AquaChain-ServiceRequests" -PartitionKey "requestId" -PartitionKeyType "S") {
    Create-GSI -TableName "AquaChain-ServiceRequests" -IndexName "TechnicianIndex" -PartitionKey "technicianId" -PartitionKeyType "S" -SortKey "createdAt" -SortKeyType "S"
    Start-Sleep -Seconds 10
    Create-GSI -TableName "AquaChain-ServiceRequests" -IndexName "StatusIndex" -PartitionKey "status" -PartitionKeyType "S" -SortKey "createdAt" -SortKeyType "S"
}

Write-Host ""

# 6. Devices Table
if (Create-DynamoDBTable -TableName "AquaChain-Devices" -PartitionKey "deviceId" -PartitionKeyType "S") {
    Create-GSI -TableName "AquaChain-Devices" -IndexName "UserIndex" -PartitionKey "userId" -PartitionKeyType "S" -SortKey "createdAt" -SortKeyType "S"
    Start-Sleep -Seconds 10
    Create-GSI -TableName "AquaChain-Devices" -IndexName "StatusIndex" -PartitionKey "status" -PartitionKeyType "S" -SortKey "lastSeen" -SortKeyType "S"
}

Write-Host ""

# 7. Audit Logs Table
if (Create-DynamoDBTable -TableName "AquaChain-AuditLogs" -PartitionKey "userId_date" -PartitionKeyType "S" -SortKey "timestamp" -SortKeyType "S") {
    Create-GSI -TableName "AquaChain-AuditLogs" -IndexName "ActionIndex" -PartitionKey "action" -PartitionKeyType "S" -SortKey "timestamp" -SortKeyType "S"
    Start-Sleep -Seconds 10
    Create-GSI -TableName "AquaChain-AuditLogs" -IndexName "ResourceIndex" -PartitionKey "resourceType" -PartitionKeyType "S" -SortKey "timestamp" -SortKeyType "S"
}

Write-Host ""

# 8. System Config Table
Create-DynamoDBTable -TableName "AquaChain-SystemConfig" -PartitionKey "configKey" -PartitionKeyType "S"

Write-Host ""
Write-Host "=== Table Creation Complete ===" -ForegroundColor Cyan
Write-Host ""

# Verify tables
Write-Host "Verifying tables..." -ForegroundColor Yellow
$existingTables = aws dynamodb list-tables --region $region --query "TableNames[?contains(@, 'AquaChain')]" --output json | ConvertFrom-Json

Write-Host ""
Write-Host "Found $($existingTables.Count) AquaChain tables:" -ForegroundColor Green
$existingTables | ForEach-Object {
    Write-Host "  ✓ $_" -ForegroundColor White
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for all GSIs to finish creating" -ForegroundColor White
Write-Host "2. Test your application at http://localhost:3000" -ForegroundColor White
Write-Host "3. Check CloudWatch logs if you encounter errors" -ForegroundColor White
Write-Host ""
