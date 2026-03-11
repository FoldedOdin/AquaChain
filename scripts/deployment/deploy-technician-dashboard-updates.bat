@echo off
REM Deploy Technician Dashboard Updates
REM This script deploys the updated API Gateway routes and Lambda function for technician dashboard

echo ========================================
echo Deploying Technician Dashboard Updates
echo ========================================
echo.

REM Set environment
set ENVIRONMENT=dev
if not "%1"=="" set ENVIRONMENT=%1

echo Environment: %ENVIRONMENT%
echo.

REM Step 1: Package Lambda function
echo [1/3] Packaging technician service Lambda...
cd lambda\technician_service
if exist deployment.zip del deployment.zip

REM Create deployment package using Python (more reliable than PowerShell)
python -m zipfile -c deployment.zip handler.py assignment_algorithm.py audit_logger.py availability_manager.py cors_utils.py location_service.py service_request_manager.py structured_logger.py requirements.txt

if not exist deployment.zip (
    echo ERROR: Failed to create deployment package
    echo Trying alternative method with tar...
    tar -a -c -f deployment.zip handler.py assignment_algorithm.py audit_logger.py availability_manager.py cors_utils.py location_service.py service_request_manager.py structured_logger.py requirements.txt
)

if not exist deployment.zip (
    echo ERROR: Failed to create deployment package with both methods
    echo Please install Python or ensure tar is available
    exit /b 1
)

echo Lambda package created successfully
echo.

REM Step 2: Update Lambda function
echo [2/3] Updating Lambda function...
aws lambda update-function-code ^
    --function-name AquaChain-Function-ServiceRequest-%ENVIRONMENT% ^
    --zip-file fileb://deployment.zip ^
    --region ap-south-1

if errorlevel 1 (
    echo ERROR: Failed to update Lambda function
    cd ..\..
    exit /b 1
)

echo Lambda function updated successfully
echo.

REM Wait for Lambda update to complete
echo Waiting for Lambda update to complete...
timeout /t 5 /nobreak > nul

REM Step 3: Deploy CDK stack
echo [3/3] Deploying CDK stack with updated API Gateway routes...
cd ..\..\infrastructure\cdk

REM Deploy API stack
cdk deploy AquaChain-API-%ENVIRONMENT% --require-approval never

if errorlevel 1 (
    echo ERROR: Failed to deploy CDK stack
    cd ..\..
    exit /b 1
)

echo CDK stack deployed successfully
echo.

cd ..\..

echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo New API routes available:
echo   - GET  /api/v1/technician/tasks
echo   - POST /api/v1/technician/tasks/{taskId}/accept
echo   - PUT  /api/v1/technician/tasks/{taskId}/status
echo   - POST /api/v1/technician/tasks/{taskId}/notes
echo   - POST /api/v1/technician/tasks/{taskId}/complete
echo   - GET  /api/v1/technician/tasks/history
echo   - GET  /api/v1/technician/tasks/{taskId}/route
echo   - PUT  /api/v1/technician/location
echo.
echo The technician dashboard should now display real data from DynamoDB.
echo.

exit /b 0
