# Create Notifications DynamoDB Table
# This script creates the notifications table with proper indexes

$region = "ap-south-1"
$tableName = "aquachain-notifications"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating Notifications Table" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if table already exists
$tableExists = aws dynamodb describe-table --table-name $tableName --region $region 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Table $tableName already exists" -ForegroundColor Yellow
    exit 0
}

Write-Host "Creating table $tableName..." -ForegroundColor Yellow

# Create table with GSI
$tableDefinition = @"
{
    "TableName": "$tableName",
    "KeySchema": [
        {
            "AttributeName": "notificationId",
            "KeyType": "HASH"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "notificationId",
            "AttributeType": "S"
        },
        {
            "AttributeName": "userId",
            "AttributeType": "S"
        },
        {
            "AttributeName": "createdAt",
            "AttributeType": "S"
        }
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "userId-createdAt-index",
            "KeySchema": [
                {
                    "AttributeName": "userId",
                    "KeyType": "HASH"
                },
                {
                    "AttributeName": "createdAt",
                    "KeyType": "RANGE"
                }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        }
    ],
    "BillingMode": "PROVISIONED",
    "ProvisionedThroughput": {
        "ReadCapacityUnits": 5,
        "WriteCapacityUnits": 5
    },
    "StreamSpecification": {
        "StreamEnabled": false
    },
    "SSESpecification": {
        "Enabled": true,
        "SSEType": "KMS"
    },
    "Tags": [
        {
            "Key": "Project",
            "Value": "AquaChain"
        },
        {
            "Key": "Environment",
            "Value": "dev"
        }
    ]
}
"@

# Create the table
$tableDefinition | aws dynamodb create-table --region $region --cli-input-json file:///dev/stdin

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Table created successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for table to become active..." -ForegroundColor Yellow
    
    aws dynamodb wait table-exists --table-name $tableName --region $region
    
    Write-Host "  ✓ Table is now active" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to create table" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Notifications Table Created" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Table Details:" -ForegroundColor Cyan
Write-Host "  Name: $tableName" -ForegroundColor White
Write-Host "  Primary Key: notificationId (String)" -ForegroundColor White
Write-Host "  GSI: userId-createdAt-index" -ForegroundColor White
Write-Host "  Billing: Provisioned 5 RCU 5 WCU" -ForegroundColor White
Write-Host "  Encryption: KMS" -ForegroundColor White
