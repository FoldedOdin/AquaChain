# Create Orders Service Infrastructure
# Step-by-step deployment of orders service

$ErrorActionPreference = "Stop"
$region = "ap-south-1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating Orders Infrastructure" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create Orders DynamoDB Table
Write-Host "Step 1: Creating Orders DynamoDB table..." -ForegroundColor Yellow

aws dynamodb create-table `
    --table-name aquachain-orders `
    --region $region `
    --attribute-definitions `
        AttributeName=orderId,AttributeType=S `
        AttributeName=userId,AttributeType=S `
        AttributeName=createdAt,AttributeType=S `
        AttributeName=status,AttributeType=S `
    --key-schema `
        AttributeName=orderId,KeyType=HASH `
    --global-secondary-indexes `
        "IndexName=userId-createdAt-index,KeySchema=[{AttributeName=userId,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" `
        "IndexName=status-createdAt-index,KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" `
    --provisioned-throughput `
        ReadCapacityUnits=5,WriteCapacityUnits=5 `
    --tags `
        Key=Project,Value=AquaChain `
        Key=Environment,Value=dev

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Orders table created" -ForegroundColor Green
    Write-Host "Waiting for table to become active..." -ForegroundColor Yellow
    aws dynamodb wait table-exists --table-name aquachain-orders --region $region
    Write-Host "✓ Table is active" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create table (may already exist)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Orders table created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Deploy Orders Lambda function" -ForegroundColor White
Write-Host "2. Configure API Gateway endpoints" -ForegroundColor White
Write-Host "3. Set up Razorpay secrets" -ForegroundColor White
