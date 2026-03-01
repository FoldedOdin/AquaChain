# Complete fix and test for profile update endpoint
# This script will:
# 1. Get a fresh token
# 2. Test the Lambda function directly
# 3. Test via API Gateway
# 4. Show detailed error logs

Write-Host "=== Profile Update Complete Fix and Test ===" -ForegroundColor Cyan

# Step 1: Get fresh token
Write-Host "`n[1/4] Getting fresh authentication token..." -ForegroundColor Yellow

$authResult = aws cognito-idp initiate-auth `
    --client-id 692o9a3pjudl1vudfgqpr5nuln `
    --auth-flow USER_PASSWORD_AUTH `
    --auth-parameters USERNAME=karthikkpradeep123@gmail.com,PASSWORD=Hu8hyxf1TPf3cwl@ `
    --region ap-south-1 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to get token from Cognito" -ForegroundColor Red
    Write-Host $authResult
    exit 1
}

$auth = $authResult | ConvertFrom-Json
$token = $auth.AuthenticationResult.IdToken

Write-Host "✓ Got token (length: $($token.Length))" -ForegroundColor Green

# Step 2: Test Lambda directly
Write-Host "`n[2/4] Testing Lambda function directly..." -ForegroundColor Yellow

$testEvent = @{
    httpMethod = "PUT"
    path = "/api/profile/update"
    headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    }
    body = '{"firstName":"Karthik","lastName":"Pradeep","phone":"+919876543210"}'
    requestContext = @{
        identity = @{
            sourceIp = "127.0.0.1"
        }
    }
} | ConvertTo-Json -Depth 10 -Compress

$testEvent | Out-File -FilePath temp-test-event.json -Encoding utf8

aws lambda invoke `
    --function-name aquachain-function-user-management-dev `
    --payload file://temp-test-event.json `
    --region ap-south-1 `
    --cli-binary-format raw-in-base64-out `
    temp-lambda-response.json | Out-Null

$lambdaResponse = Get-Content temp-lambda-response.json | ConvertFrom-Json

Write-Host "Lambda Response:" -ForegroundColor Cyan
$lambdaResponse | ConvertTo-Json -Depth 5

if ($lambdaResponse.statusCode -eq 200) {
    Write-Host "✓ Lambda function works!" -ForegroundColor Green
} else {
    Write-Host "✗ Lambda returned error: $($lambdaResponse.statusCode)" -ForegroundColor Red
    
    # Get logs
    Write-Host "`nFetching Lambda logs..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    $logStream = aws logs describe-log-streams `
        --log-group-name /aws/lambda/aquachain-function-user-management-dev `
        --region ap-south-1 `
        --order-by LastEventTime `
        --descending `
        --max-items 1 `
        --query "logStreams[0].logStreamName" `
        --output text
    
    if ($logStream -and $logStream -ne "None") {
        Write-Host "Log stream: $logStream" -ForegroundColor Gray
        
        aws logs get-log-events `
            --log-group-name /aws/lambda/aquachain-function-user-management-dev `
            --log-stream-name $logStream `
            --region ap-south-1 `
            --limit 20 `
            --query "events[*].message" `
            --output text | Select-Object -Last 15
    }
}

# Step 3: Test via API Gateway
Write-Host "`n[3/4] Testing via API Gateway..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    firstName = "Karthik"
    lastName = "Pradeep"
    phone = "+919876543210"
} | ConvertTo-Json

try {
    $apiResponse = Invoke-RestMethod `
        -Uri "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/profile/update" `
        -Method PUT `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "✓ API Gateway test successful!" -ForegroundColor Green
    Write-Host "`nAPI Response:" -ForegroundColor Cyan
    $apiResponse | ConvertTo-Json -Depth 5
    
} catch {
    Write-Host "✗ API Gateway test failed" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        Write-Host "Error: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}

# Step 4: Verify in DynamoDB
Write-Host "`n[4/4] Verifying profile in DynamoDB..." -ForegroundColor Yellow

$user = aws dynamodb scan `
    --table-name AquaChain-Users `
    --filter-expression "email = :email" `
    --expression-attribute-values '{":email":{"S":"karthikkpradeep123@gmail.com"}}' `
    --region ap-south-1 | ConvertFrom-Json

if ($user.Items.Count -gt 0) {
    $profile = $user.Items[0].profile.M
    Write-Host "Current profile in DynamoDB:" -ForegroundColor Cyan
    Write-Host "  First Name: $($profile.firstName.S)" -ForegroundColor White
    Write-Host "  Last Name: $($profile.lastName.S)" -ForegroundColor White
    Write-Host "  Phone: $($profile.phone.S)" -ForegroundColor White
}

# Cleanup
Remove-Item temp-test-event.json, temp-lambda-response.json -ErrorAction SilentlyContinue

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
