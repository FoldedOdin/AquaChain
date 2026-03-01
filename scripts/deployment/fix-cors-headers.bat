@echo off
REM Fix CORS headers in API Gateway Integration Responses
REM Remove quotes from Access-Control-Allow-Origin header value

echo ========================================
echo Fixing CORS Headers in API Gateway
echo ========================================
echo.

set API_ID=vtqjfznspc
set REGION=ap-south-1

echo API Gateway ID: %API_ID%
echo Region: %REGION%
echo.

REM Get all resources
echo Fetching API resources...
aws apigateway get-resources --rest-api-id %API_ID% --region %REGION% --output json > temp-resources.json

echo.
echo Fixing CORS headers for OPTIONS methods...
echo.

REM Note: We need to update each resource's OPTIONS method Integration Response
REM The issue is that the headers have quotes: '*' instead of *

REM List of resource IDs that have OPTIONS methods (from our earlier check)
set RESOURCES=011kmw 0yz9z0 1sz6gd 3j5bbl 42ge9a 4qguw7 6q69z515cl 85jbld akrzvl blsh9l dlok9v fqiwpd j6acmy m38eai m8vvc9 mhxb80 nakzvp pa29du qcab95 qs64be rowuku s60nz3 tme29l v4riy9 vjf3h6 vx0bur wjy00f xxo7os

echo Updating Integration Responses...
echo.

for %%R in (%RESOURCES%) do (
    echo Updating resource: %%R
    
    REM Update the Integration Response for OPTIONS method
    REM Remove quotes from header values
    aws apigateway update-integration-response ^
        --rest-api-id %API_ID% ^
        --resource-id %%R ^
        --http-method OPTIONS ^
        --status-code 204 ^
        --region %REGION% ^
        --patch-operations ^
            op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value=* ^
            op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Headers,value=Content-Type,Authorization,X-Amz-Date,X-Api-Key ^
            op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Methods,value=OPTIONS,GET,PUT,POST,DELETE,PATCH,HEAD ^
        2>nul
    
    if errorlevel 1 (
        echo   - Skipped ^(no OPTIONS method^)
    ) else (
        echo   - Updated successfully
    )
)

echo.
echo ========================================
echo Deploying API to dev stage...
echo ========================================
echo.

REM Create a new deployment
aws apigateway create-deployment ^
    --rest-api-id %API_ID% ^
    --stage-name dev ^
    --region %REGION% ^
    --description "Fix CORS headers - remove quotes from values"

if errorlevel 1 (
    echo ERROR: Failed to deploy API
    exit /b 1
)

echo.
echo ========================================
echo CORS Headers Fixed Successfully!
echo ========================================
echo.
echo API Endpoint: https://%API_ID%.execute-api.%REGION%.amazonaws.com/dev
echo.
echo Test with:
echo curl -X OPTIONS https://%API_ID%.execute-api.%REGION%.amazonaws.com/dev/api/v1/users -H "Origin: http://localhost:3000" -v
echo.

REM Cleanup
del temp-resources.json 2>nul

exit /b 0
