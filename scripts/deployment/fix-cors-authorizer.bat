@echo off
REM Fix CORS by removing authorizer from OPTIONS methods
REM This script removes Cognito authorizer from OPTIONS requests

echo ========================================
echo Fix CORS - Remove Authorizer from OPTIONS
echo ========================================
echo.

set API_ID=vtqjfznspc
set REGION=ap-south-1

echo Getting API resources...
echo.

REM Get all resources
aws apigateway get-resources --rest-api-id %API_ID% --region %REGION% > resources.json

echo.
echo Resources saved to resources.json
echo.
echo You need to manually update each OPTIONS method to remove the authorizer.
echo.
echo Alternative: Redeploy the API with correct CDK configuration
echo.

pause
