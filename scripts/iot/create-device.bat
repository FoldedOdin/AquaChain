@echo off
REM Create a new IoT device (Thing) with certificates
REM Usage: create-device.bat ESP32-001

if "%1"=="" (
    echo Usage: create-device.bat DEVICE_ID
    echo Example: create-device.bat ESP32-001
    exit /b 1
)

set DEVICE_ID=%1
set THING_TYPE=aquachain-sensor-dev
set POLICY_NAME=aquachain-device-policy-dev
set REGION=ap-south-1

echo ========================================
echo Creating AquaChain IoT Device
echo ========================================
echo Device ID: %DEVICE_ID%
echo Thing Type: %THING_TYPE%
echo Policy: %POLICY_NAME%
echo.

REM Ensure certificates directory exists
if not exist certificates mkdir certificates

REM Step 1: Create Thing
echo Step 1: Creating Thing...
aws iot create-thing ^
    --thing-name %DEVICE_ID% ^
    --thing-type-name %THING_TYPE% ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create Thing
    exit /b 1
)
echo ✓ Thing created

REM Step 2: Create certificate
echo.
echo Step 2: Creating certificate...
aws iot create-keys-and-certificate ^
    --set-as-active ^
    --certificate-pem-outfile certificates\%DEVICE_ID%-cert.pem ^
    --public-key-outfile certificates\%DEVICE_ID%-public.key ^
    --private-key-outfile certificates\%DEVICE_ID%-private.key ^
    --region %REGION% > certificates\%DEVICE_ID%-cert-info.json

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create certificate
    exit /b 1
)
echo ✓ Certificate created

REM Extract certificate ARN using PowerShell for reliable JSON parsing
for /f "delims=" %%a in ('powershell -Command "(Get-Content certificates\%DEVICE_ID%-cert-info.json | ConvertFrom-Json).certificateArn"') do set CERT_ARN=%%a

echo Certificate ARN: %CERT_ARN%

if "%CERT_ARN%"=="" (
    echo Error: Failed to extract certificate ARN
    type certificates\%DEVICE_ID%-cert-info.json
    exit /b 1
)

REM Step 3: Attach policy to certificate
echo.
echo Step 3: Attaching policy to certificate...
aws iot attach-policy ^
    --policy-name %POLICY_NAME% ^
    --target %CERT_ARN% ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to attach policy
    exit /b 1
)
echo ✓ Policy attached

REM Step 4: Attach certificate to Thing
echo.
echo Step 4: Attaching certificate to Thing...
aws iot attach-thing-principal ^
    --thing-name %DEVICE_ID% ^
    --principal %CERT_ARN% ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to attach certificate to Thing
    exit /b 1
)
echo ✓ Certificate attached to Thing

REM Step 5: Add Thing to active group
echo.
echo Step 5: Adding Thing to active group...
aws iot add-thing-to-thing-group ^
    --thing-name %DEVICE_ID% ^
    --thing-group-name aquachain-active-dev ^
    --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo Warning: Failed to add to thing group (non-critical)
) else (
    echo ✓ Added to active group
)

REM Download root CA certificate if not exists
if not exist certificates\AmazonRootCA1.pem (
    echo.
    echo Step 6: Downloading Amazon Root CA...
    curl -o certificates\AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
    echo ✓ Root CA downloaded
)

echo.
echo ========================================
echo ✓ Device Created Successfully!
echo ========================================
echo.
echo Device ID: %DEVICE_ID%
echo Certificates saved in: certificates\
echo.
echo Files created:
echo   - %DEVICE_ID%-cert.pem (Device certificate)
echo   - %DEVICE_ID%-private.key (Private key)
echo   - %DEVICE_ID%-public.key (Public key)
echo   - AmazonRootCA1.pem (Root CA)
echo.
echo Next steps:
echo 1. Copy certificate contents to config.h
echo 2. Upload firmware to ESP32
echo 3. Register device in dashboard
echo.
pause
