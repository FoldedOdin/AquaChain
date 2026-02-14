@echo off
REM AquaChain - Fix Compromised AWS Keys
REM This script helps you recover from compromised AWS access keys

echo ========================================
echo AWS Compromised Key Recovery
echo ========================================
echo.
echo CRITICAL: Your AWS access keys have been flagged as compromised!
echo.
echo Steps to fix:
echo 1. Go to AWS Console: https://console.aws.amazon.com/iam/home#/users/Karthik?section=security_credentials
echo 2. Delete ALL existing access keys
echo 3. Create a NEW access key
echo 4. Update your local AWS credentials file
echo 5. Detach the quarantine policy
echo.
echo Press any key to open AWS Console...
pause >nul
start https://console.aws.amazon.com/iam/home#/users/Karthik?section=security_credentials
echo.
echo After creating new keys, run this command to detach the quarantine policy:
echo aws iam detach-user-policy --user-name Karthik --policy-arn arn:aws:iam::aws:policy/AWSCompromisedKeyQuarantineV3
echo.
echo Then delete the old S3 bucket:
echo aws s3 rb s3://aquachain-bucket-audit-trail-758346259059-dev --force --region ap-south-1
echo.
pause
