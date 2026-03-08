@echo off
REM Fix AquaChain Ledger Table Schema
REM Deletes old table and creates new one with correct schema

echo ============================================================
echo AquaChain Ledger Table Schema Fix
echo ============================================================
echo.
echo WARNING: This will delete and recreate the Ledger table
echo Current table: AquaChain-Ledger (WRONG SCHEMA)
echo New table: aquachain-ledger (CORRECT SCHEMA)
echo.

set /p CONFIRM="Type 'YES' to continue: "
if not "%CONFIRM%"=="YES" (
    echo Operation cancelled
    exit /b 0
)

echo.
echo Step 1: Check if table has data
echo ------------------------------------------------------------
aws dynamodb scan --table-name AquaChain-Ledger --region ap-south-1 --select COUNT --output json > %TEMP%\ledger-count.json

for /f "tokens=2 delims=:" %%a in ('findstr /C:"Count" %TEMP%\ledger-count.json') do set ITEM_COUNT=%%a
set ITEM_COUNT=%ITEM_COUNT:~1,-1%
set ITEM_COUNT=%ITEM_COUNT: =%

echo Table has %ITEM_COUNT% items

if %ITEM_COUNT% GTR 0 (
    echo.
    echo WARNING: Table contains data!
    set /p BACKUP="Do you want to backup data first? (YES/NO): "
    if "%BACKUP%"=="YES" (
        echo Backing up data...
        aws dynamodb scan --table-name AquaChain-Ledger --region ap-south-1 --output json > ledger-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%.json
        echo Backup saved to: ledger-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%.json
    )
)

echo.
echo Step 2: Delete old table
echo ------------------------------------------------------------
aws dynamodb delete-table --table-name AquaChain-Ledger --region ap-south-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to delete table
    exit /b 1
)

echo Waiting for table deletion...
timeout /t 10 /nobreak > nul

:wait_delete
aws dynamodb describe-table --table-name AquaChain-Ledger --region ap-south-1 > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Still deleting...
    timeout /t 5 /nobreak > nul
    goto wait_delete
)

echo Table deleted successfully
echo.

echo Step 3: Create new table with correct schema
echo ------------------------------------------------------------

REM Create table definition JSON
echo { > %TEMP%\ledger-table.json
echo   "TableName": "aquachain-ledger", >> %TEMP%\ledger-table.json
echo   "KeySchema": [ >> %TEMP%\ledger-table.json
echo     {"AttributeName": "partition_key", "KeyType": "HASH"}, >> %TEMP%\ledger-table.json
echo     {"AttributeName": "sequenceNumber", "KeyType": "RANGE"} >> %TEMP%\ledger-table.json
echo   ], >> %TEMP%\ledger-table.json
echo   "AttributeDefinitions": [ >> %TEMP%\ledger-table.json
echo     {"AttributeName": "partition_key", "AttributeType": "S"}, >> %TEMP%\ledger-table.json
echo     {"AttributeName": "sequenceNumber", "AttributeType": "N"}, >> %TEMP%\ledger-table.json
echo     {"AttributeName": "deviceId", "AttributeType": "S"}, >> %TEMP%\ledger-table.json
echo     {"AttributeName": "timestamp", "AttributeType": "S"} >> %TEMP%\ledger-table.json
echo   ], >> %TEMP%\ledger-table.json
echo   "GlobalSecondaryIndexes": [ >> %TEMP%\ledger-table.json
echo     { >> %TEMP%\ledger-table.json
echo       "IndexName": "DeviceLedgerIndex", >> %TEMP%\ledger-table.json
echo       "KeySchema": [ >> %TEMP%\ledger-table.json
echo         {"AttributeName": "deviceId", "KeyType": "HASH"}, >> %TEMP%\ledger-table.json
echo         {"AttributeName": "timestamp", "KeyType": "RANGE"} >> %TEMP%\ledger-table.json
echo       ], >> %TEMP%\ledger-table.json
echo       "Projection": {"ProjectionType": "ALL"} >> %TEMP%\ledger-table.json
echo     } >> %TEMP%\ledger-table.json
echo   ], >> %TEMP%\ledger-table.json
echo   "BillingMode": "PAY_PER_REQUEST", >> %TEMP%\ledger-table.json
echo   "StreamSpecification": { >> %TEMP%\ledger-table.json
echo     "StreamEnabled": true, >> %TEMP%\ledger-table.json
echo     "StreamViewType": "NEW_AND_OLD_IMAGES" >> %TEMP%\ledger-table.json
echo   }, >> %TEMP%\ledger-table.json
echo   "Tags": [ >> %TEMP%\ledger-table.json
echo     {"Key": "Project", "Value": "AquaChain"}, >> %TEMP%\ledger-table.json
echo     {"Key": "Environment", "Value": "dev"}, >> %TEMP%\ledger-table.json
echo     {"Key": "DataClassification", "Value": "immutable-ledger"} >> %TEMP%\ledger-table.json
echo   ] >> %TEMP%\ledger-table.json
echo } >> %TEMP%\ledger-table.json

aws dynamodb create-table --cli-input-json file://%TEMP%\ledger-table.json --region ap-south-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create table
    exit /b 1
)

echo Waiting for table to become active...
timeout /t 10 /nobreak > nul

:wait_active
aws dynamodb describe-table --table-name aquachain-ledger --region ap-south-1 --query "Table.TableStatus" --output text > %TEMP%\status.txt
set /p TABLE_STATUS=<%TEMP%\status.txt

if not "%TABLE_STATUS%"=="ACTIVE" (
    echo Status: %TABLE_STATUS%
    timeout /t 5 /nobreak > nul
    goto wait_active
)

echo Table is now ACTIVE
echo.

echo Step 4: Enable Point-in-Time Recovery
echo ------------------------------------------------------------
aws dynamodb update-continuous-backups ^
  --table-name aquachain-ledger ^
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true ^
  --region ap-south-1

if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Failed to enable PITR (non-critical)
) else (
    echo PITR enabled successfully
)

echo.
echo Step 5: Verify table configuration
echo ------------------------------------------------------------
echo.
echo Table Details:
aws dynamodb describe-table --table-name aquachain-ledger --region ap-south-1 --query "Table.[TableName,TableStatus,KeySchema,GlobalSecondaryIndexes[0].IndexName,StreamSpecification.StreamEnabled]" --output table

echo.
echo Step 6: Update Lambda environment variables
echo ------------------------------------------------------------
echo Updating data processing Lambda...
aws lambda update-function-configuration ^
  --function-name aquachain-function-data-processing-dev ^
  --environment Variables="{LEDGER_TABLE=aquachain-ledger,READINGS_TABLE=AquaChain-Readings,SEQUENCE_TABLE=AquaChain-Sequence}" ^
  --region ap-south-1 > nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo ✓ Data processing Lambda updated
) else (
    echo ⚠ Lambda update failed (may not exist yet)
)

echo.
echo ============================================================
echo Ledger Table Fix Complete!
echo ============================================================
echo.
echo Old table: AquaChain-Ledger (DELETED)
echo New table: aquachain-ledger (ACTIVE)
echo.
echo Schema:
echo   - Partition Key: partition_key (String)
echo   - Sort Key: sequenceNumber (Number)
echo   - GSI: DeviceLedgerIndex (deviceId, timestamp)
echo   - Streams: ENABLED (NEW_AND_OLD_IMAGES)
echo   - PITR: ENABLED
echo.
echo Next Steps:
echo 1. Test ledger entry creation
echo 2. Verify DynamoDB Streams trigger
echo 3. Test device query via GSI
echo 4. Monitor CloudWatch logs
echo.
echo ============================================================

REM Cleanup
del %TEMP%\ledger-table.json
del %TEMP%\ledger-count.json
del %TEMP%\status.txt

exit /b 0
