# Check if notifications table exists and has correct GSI
$tableName = "aquachain-notifications"
$region = "ap-south-1"

Write-Host "Checking notifications table..." -ForegroundColor Cyan

# Check if table exists
$tableExists = aws dynamodb describe-table --table-name $tableName --region $region 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Table exists" -ForegroundColor Green
    
    # Check for GSI
    $gsiCheck = aws dynamodb describe-table --table-name $tableName --region $region --query "Table.GlobalSecondaryIndexes[?IndexName=='userId-createdAt-index'].IndexName" --output text
    
    if ($gsiCheck) {
        Write-Host "✓ GSI 'userId-createdAt-index' exists" -ForegroundColor Green
    } else {
        Write-Host "✗ GSI 'userId-createdAt-index' missing" -ForegroundColor Red
        Write-Host "Creating GSI..." -ForegroundColor Yellow
        
        aws dynamodb update-table `
            --table-name $tableName `
            --region $region `
            --attribute-definitions `
                AttributeName=userId,AttributeType=S `
                AttributeName=createdAt,AttributeType=S `
            --global-secondary-index-updates `
                "[{`"Create`":{`"IndexName`":`"userId-createdAt-index`",`"KeySchema`":[{`"AttributeName`":`"userId`",`"KeyType`":`"HASH`"},{`"AttributeName`":`"createdAt`",`"KeyType`":`"RANGE`"}],`"Projection`":{`"ProjectionType`":`"ALL`"},`"ProvisionedThroughput`":{`"ReadCapacityUnits`":5,`"WriteCapacityUnits`":5}}}]"
    }
} else {
    Write-Host "✗ Table does not exist" -ForegroundColor Red
    Write-Host "Creating table..." -ForegroundColor Yellow
    
    # Create table with GSI
    aws dynamodb create-table `
        --table-name $tableName `
        --region $region `
        --attribute-definitions `
            AttributeName=notificationId,AttributeType=S `
            AttributeName=userId,AttributeType=S `
            AttributeName=createdAt,AttributeType=S `
        --key-schema `
            AttributeName=notificationId,KeyType=HASH `
        --global-secondary-indexes `
            "IndexName=userId-createdAt-index,KeySchema=[{AttributeName=userId,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" `
        --provisioned-throughput `
            ReadCapacityUnits=5,WriteCapacityUnits=5 `
        --tags `
            Key=Project,Value=AquaChain `
            Key=Environment,Value=dev
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Table created successfully" -ForegroundColor Green
        Write-Host "Waiting for table to become active..." -ForegroundColor Yellow
        aws dynamodb wait table-exists --table-name $tableName --region $region
        Write-Host "✓ Table is active" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create table" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nNotifications table is ready!" -ForegroundColor Green
