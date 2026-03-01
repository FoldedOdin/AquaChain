# Deploy Complete OTP Registration Flow
# Creates Lambda functions, DynamoDB table, and API Gateway endpoints

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$USER_POOL_ID = "ap-south-1_QUDl7hG8u"
$API_ID = "vtqjfznspc"
$STAGE = "dev"
$OTP_TABLE_NAME = "AquaChain-OTP"
$USERS_TABLE_NAME = "AquaChain-Users"
$SES_SENDER_EMAIL = "noreply@aquachain.com"

Write-Host "=== Deploying OTP Registration Flow ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create DynamoDB table for OTP storage
Write-Host "Step 1: Creating DynamoDB OTP table..." -ForegroundColor Yellow

$tableExists = aws dynamodb describe-table --table-name $OTP_TABLE_NAME --region $REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating OTP table..." -ForegroundColor Cyan
    
    aws dynamodb create-table `
        --table-name $OTP_TABLE_NAME `
        --attribute-definitions AttributeName=email,AttributeType=S `
        --key-schema AttributeName=email,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ OTP table created" -ForegroundColor Green
        
        # Wait for table to be active
        Write-Host "Waiting for table to be active..." -ForegroundColor Cyan
        aws dynamodb wait table-exists --table-name $OTP_TABLE_NAME --region $REGION
        Write-Host "✓ Table is active" -ForegroundColor Green
        
        # Enable TTL
        Write-Host "Enabling TTL on expiresAt attribute..." -ForegroundColor Cyan
        aws dynamodb update-time-to-live `
            --table-name $OTP_TABLE_NAME `
            --time-to-live-specification "Enabled=true,AttributeName=expiresAt" `
            --region $REGION
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ TTL enabled" -ForegroundColor Green
        }
    } else {
        Write-Host "✗ Failed to create OTP table" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ OTP table already exists" -ForegroundColor Green
}

Write-Host ""

# Step 2: Create Lambda execution role (if not exists)
Write-Host "Step 2: Setting up IAM role..." -ForegroundColor Yellow

$ROLE_NAME = "aquachain-registration-lambda-role"
$roleExists = aws iam get-role --role-name $ROLE_NAME 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Lambda execution role..." -ForegroundColor Cyan
    
    $trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
    
    $trustPolicy | Out-File -FilePath trust-policy.json -Encoding utf8
    
    aws iam create-role `
        --role-name $ROLE_NAME `
        --assume-role-policy-document file://trust-policy.json
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    # Create inline policy for Cognito, DynamoDB, and SES
    $inlinePolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminSetUserPassword",
        "cognito-idp:AdminGetUser",
        "cognito-idp:AdminUpdateUserAttributes",
        "cognito-idp:AdminEnableUser",
        "cognito-idp:AdminDisableUser",
        "cognito-idp:AdminAddUserToGroup"
      ],
      "Resource": "arn:aws:cognito-idp:${REGION}:*:userpool/${USER_POOL_ID}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:${REGION}:*:table/${OTP_TABLE_NAME}",
        "arn:aws:dynamodb:${REGION}:*:table/${USERS_TABLE_NAME}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
"@
    
    $inlinePolicy | Out-File -FilePath inline-policy.json -Encoding utf8
    
    aws iam put-role-policy `
        --role-name $ROLE_NAME `
        --policy-name "RegistrationServicePolicy" `
        --policy-document file://inline-policy.json
    
    Remove-Item trust-policy.json, inline-policy.json
    
    Write-Host "✓ IAM role created" -ForegroundColor Green
    Write-Host "Waiting 10 seconds for IAM propagation..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
} else {
    Write-Host "✓ IAM role already exists" -ForegroundColor Green
}

$ROLE_ARN = (aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
Write-Host "Role ARN: $ROLE_ARN" -ForegroundColor Cyan
Write-Host ""

# Step 3: Package and deploy Lambda functions
Write-Host "Step 3: Deploying Lambda functions..." -ForegroundColor Yellow

$functions = @(
    @{
        Name = "aquachain-register-dev"
        Handler = "register.lambda_handler"
        File = "lambda/auth_service/register.py"
        ZipName = "register-function.zip"
    },
    @{
        Name = "aquachain-request-otp-dev"
        Handler = "request_otp.lambda_handler"
        File = "lambda/auth_service/request_otp.py"
        ZipName = "request-otp-function.zip"
    },
    @{
        Name = "aquachain-verify-otp-dev"
        Handler = "verify_otp.lambda_handler"
        File = "lambda/auth_service/verify_otp.py"
        ZipName = "verify-otp-function.zip"
    }
)

foreach ($func in $functions) {
    Write-Host "Deploying $($func.Name)..." -ForegroundColor Cyan
    
    # Create deployment package
    if (Test-Path $func.ZipName) {
        Remove-Item $func.ZipName
    }
    
    Compress-Archive -Path $func.File -DestinationPath $func.ZipName
    
    # Check if function exists
    $functionExists = aws lambda get-function --function-name $func.Name --region $REGION 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        # Create function
        aws lambda create-function `
            --function-name $func.Name `
            --runtime python3.11 `
            --role $ROLE_ARN `
            --handler $func.Handler `
            --zip-file "fileb://$($func.ZipName)" `
            --timeout 30 `
            --memory-size 256 `
            --environment "Variables={COGNITO_USER_POOL_ID=$USER_POOL_ID,REGION=$REGION,OTP_TABLE_NAME=$OTP_TABLE_NAME,USERS_TABLE_NAME=$USERS_TABLE_NAME,SES_SENDER_EMAIL=$SES_SENDER_EMAIL}" `
            --region $REGION
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $($func.Name) created" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to create $($func.Name)" -ForegroundColor Red
        }
    } else {
        # Update function code
        aws lambda update-function-code `
            --function-name $func.Name `
            --zip-file "fileb://$($func.ZipName)" `
            --region $REGION
        
        # Update environment variables
        aws lambda update-function-configuration `
            --function-name $func.Name `
            --environment "Variables={COGNITO_USER_POOL_ID=$USER_POOL_ID,REGION=$REGION,OTP_TABLE_NAME=$OTP_TABLE_NAME,USERS_TABLE_NAME=$USERS_TABLE_NAME,SES_SENDER_EMAIL=$SES_SENDER_EMAIL}" `
            --region $REGION
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $($func.Name) updated" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to update $($func.Name)" -ForegroundColor Red
        }
    }
    
    # Clean up zip file
    Remove-Item $func.ZipName
}

Write-Host ""

# Step 4: Add API Gateway permissions
Write-Host "Step 4: Adding API Gateway permissions..." -ForegroundColor Yellow

foreach ($func in $functions) {
    $statementId = "$($func.Name)-apigateway-permission"
    
    # Remove existing permission if it exists
    aws lambda remove-permission `
        --function-name $func.Name `
        --statement-id $statementId `
        --region $REGION 2>$null
    
    # Add permission
    $ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
    aws lambda add-permission `
        --function-name $func.Name `
        --statement-id $statementId `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*" `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Permission added for $($func.Name)" -ForegroundColor Green
    }
}

Write-Host ""

# Step 5: Create API Gateway resources and methods
Write-Host "Step 5: Creating API Gateway endpoints..." -ForegroundColor Yellow

# Get root resource ID
$ROOT_ID = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/`].id' --output text

# Get or create /api resource
$apiResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/api`].id' --output text

if ([string]::IsNullOrEmpty($apiResourceId)) {
    Write-Host "Creating /api resource..." -ForegroundColor Cyan
    $apiResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $ROOT_ID `
        --path-part "api" `
        --region $REGION `
        --query 'id' --output text
}

# Get or create /api/auth resource
$authResourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/api/auth`].id' --output text

if ([string]::IsNullOrEmpty($authResourceId)) {
    Write-Host "Creating /api/auth resource..." -ForegroundColor Cyan
    $authResourceId = aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $apiResourceId `
        --path-part "auth" `
        --region $REGION `
        --query 'id' --output text
}

# Create endpoints
$endpoints = @(
    @{
        Path = "register"
        FunctionName = "aquachain-register-dev"
        ResourceId = $null
    },
    @{
        Path = "request-otp"
        FunctionName = "aquachain-request-otp-dev"
        ResourceId = $null
    },
    @{
        Path = "verify-otp"
        FunctionName = "aquachain-verify-otp-dev"
        ResourceId = $null
    }
)

foreach ($endpoint in $endpoints) {
    Write-Host "Creating /api/auth/$($endpoint.Path) endpoint..." -ForegroundColor Cyan
    
    # Get or create resource
    $resourceId = aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path==``/api/auth/$($endpoint.Path)``].id" --output text
    
    if ([string]::IsNullOrEmpty($resourceId)) {
        $resourceId = aws apigateway create-resource `
            --rest-api-id $API_ID `
            --parent-id $authResourceId `
            --path-part $endpoint.Path `
            --region $REGION `
            --query 'id' --output text
    }
    
    $endpoint.ResourceId = $resourceId
    
    # Get Lambda ARN
    $lambdaArn = aws lambda get-function --function-name $endpoint.FunctionName --region $REGION --query 'Configuration.FunctionArn' --output text
    $lambdaUri = "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
    
    # Create OPTIONS method
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION 2>$null
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' `
        --region $REGION 2>$null
    
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
        --region $REGION 2>$null
    
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,Authorization'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        --region $REGION 2>$null
    
    # Create POST method
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method POST `
        --authorization-type NONE `
        --region $REGION 2>$null
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method POST `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri $lambdaUri `
        --region $REGION 2>$null
    
    Write-Host "✓ /api/auth/$($endpoint.Path) created" -ForegroundColor Green
}

Write-Host ""

# Step 6: Deploy API
Write-Host "Step 6: Deploying API..." -ForegroundColor Yellow

aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name $STAGE `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ API deployed" -ForegroundColor Green
} else {
    Write-Host "✗ API deployment failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Cyan
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/api/auth/register" -ForegroundColor White
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/api/auth/request-otp" -ForegroundColor White
Write-Host "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/api/auth/verify-otp" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify SES sender email: $SES_SENDER_EMAIL" -ForegroundColor White
Write-Host "2. Test registration flow with test script" -ForegroundColor White
Write-Host "3. Update frontend to use new endpoints" -ForegroundColor White
Write-Host ""
