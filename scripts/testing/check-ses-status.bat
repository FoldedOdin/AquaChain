@echo off
REM AquaChain - Check AWS SES Configuration and Status
REM This script verifies SES setup and helps troubleshoot email delivery issues

echo ========================================
echo AquaChain SES Status Check
echo ========================================
echo.

REM Check AWS CLI is installed
where aws >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found. Please install it first.
    echo Download from: https://aws.amazon.com/cli/
    exit /b 1
)

echo [1/6] Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS credentials not configured
    echo Run: aws configure
    exit /b 1
)
echo ✓ AWS credentials configured
echo.

echo [2/6] Checking sender email verification status...
aws ses get-identity-verification-attributes --identities contact.aquachain@gmail.com --region ap-south-1 --query "VerificationAttributes.\"contact.aquachain@gmail.com\".VerificationStatus" --output text
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to check email verification status
    exit /b 1
)
echo.

echo [3/6] Checking SES sending quota...
aws ses get-send-quota --region ap-south-1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to get SES quota
    exit /b 1
)
echo.

echo [4/6] Checking recent send statistics...
aws ses get-send-statistics --region ap-south-1 --query "SendDataPoints[-5:]"
echo.

echo [5/6] Listing all verified identities...
aws ses list-identities --region ap-south-1
echo.

echo [6/6] Testing email send capability...
echo Creating test email...

REM Create temporary JSON file for test email
echo { > %TEMP%\ses-test.json
echo   "Source": "contact.aquachain@gmail.com", >> %TEMP%\ses-test.json
echo   "Destination": { >> %TEMP%\ses-test.json
echo     "ToAddresses": ["contact.aquachain@gmail.com"] >> %TEMP%\ses-test.json
echo   }, >> %TEMP%\ses-test.json
echo   "Message": { >> %TEMP%\ses-test.json
echo     "Subject": { >> %TEMP%\ses-test.json
echo       "Data": "AquaChain SES Test", >> %TEMP%\ses-test.json
echo       "Charset": "UTF-8" >> %TEMP%\ses-test.json
echo     }, >> %TEMP%\ses-test.json
echo     "Body": { >> %TEMP%\ses-test.json
echo       "Text": { >> %TEMP%\ses-test.json
echo         "Data": "This is a test email from AquaChain SES configuration check.", >> %TEMP%\ses-test.json
echo         "Charset": "UTF-8" >> %TEMP%\ses-test.json
echo       } >> %TEMP%\ses-test.json
echo     } >> %TEMP%\ses-test.json
echo   } >> %TEMP%\ses-test.json
echo } >> %TEMP%\ses-test.json

echo Sending test email to contact.aquachain@gmail.com...
aws ses send-email --cli-input-json file://%TEMP%\ses-test.json --region ap-south-1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Test email sent successfully!
    echo Check contact.aquachain@gmail.com inbox
) else (
    echo ✗ Failed to send test email
)

REM Cleanup
del %TEMP%\ses-test.json >nul 2>&1

echo.
echo ========================================
echo SES Status Check Complete
echo ========================================
echo.
echo IMPORTANT NOTES:
echo - If sender email is not verified, run: aws ses verify-email-identity --email-address contact.aquachain@gmail.com --region ap-south-1
echo - If in sandbox mode (Max24HourSend = 200), you can only send to verified emails
echo - To send to any email, request production access: https://console.aws.amazon.com/ses/
echo - Check CloudWatch logs for Lambda errors: /aws/lambda/AquaChain-Function-UserManagement-dev
echo.

pause
