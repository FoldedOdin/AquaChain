@echo off
REM Test AquaChain Backend Deployment Status
REM This script verifies the AWS backend is deployed and accessible

echo ========================================
echo AquaChain Backend Deployment Test
echo ========================================
echo.

set API_URL=https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev
set REGION=ap-south-1

echo [1/4] Testing API Gateway connectivity...
echo.
curl -s %API_URL%/api/v1/users
echo.
echo.

echo ========================================
echo [2/4] Checking deployed Lambda functions...
echo.
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'aquachain')].FunctionName" --output table --region %REGION%
echo.

echo ========================================
echo [3/4] Checking Cognito User Pool...
echo.
aws cognito-idp describe-user-pool --user-pool-id ap-south-1_QUDl7hG8u --query "UserPool.{Name:Name,Status:Status,Id:Id}" --output table --region %REGION%
echo.

echo ========================================
echo [4/4] Checking DynamoDB Tables...
echo.
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'AquaChain') || starts_with(@, 'aquachain')]" --output table --region %REGION%
echo.

echo ========================================
echo Deployment Status Summary
echo ========================================
echo.
echo API Gateway URL: %API_URL%
echo Region: %REGION%
echo.
echo IMPORTANT: All API endpoints require Cognito authentication.
echo The "Missing Authentication Token" message means the API is working!
echo.
echo Next steps:
echo 1. Create a test user: scripts\setup\create-test-user.bat
echo 2. Start the frontend: cd frontend ^&^& npm start
echo 3. Sign in with your test user credentials
echo 4. Test the full application flow
echo.

pause
