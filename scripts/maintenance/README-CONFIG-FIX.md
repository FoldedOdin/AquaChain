# System Configuration Threshold Fix

## Overview

This directory contains scripts to fix incorrect threshold values in the AquaChain system configuration stored in DynamoDB.

## Problem

The current system configuration has backwards threshold values:
- **TDS**: Critical Max (500) > Warning Max (400) ❌
- **Temperature**: Thresholds don't follow the required pattern ❌

This causes validation errors when trying to update the configuration through the UI.

## Solution

The `fix-system-config-thresholds.py` script updates the configuration with scientifically correct values:

### Correct Threshold Values

**Turbidity (0-100 NTU):**
- Critical Max: 4 NTU (triggers SMS alert)
- Warning Max: 8 NTU (triggers email alert)

**TDS (0-5000 ppm):**
- Critical Max: 300 ppm (triggers SMS alert)
- Warning Max: 450 ppm (triggers email alert)

**Temperature (-10°C to 100°C):**
- Warning Min: 0°C (outer lower bound)
- Critical Min: 10°C (inner lower bound)
- Critical Max: 40°C (inner upper bound)
- Warning Max: 50°C (outer upper bound)

## Prerequisites

1. **AWS Credentials**: Ensure you have AWS credentials configured
   ```bash
   aws configure
   ```

2. **Python 3**: Python 3.7+ with boto3 installed
   ```bash
   pip install boto3
   ```

3. **IAM Permissions**: Your AWS user/role needs:
   - `dynamodb:GetItem` on `AquaChain-SystemConfig`
   - `dynamodb:PutItem` on `AquaChain-SystemConfig`
   - `dynamodb:PutItem` on `AquaChain-ConfigHistory`

## Usage

### Step 1: Run the Fix Script

```bash
cd /path/to/aquachain
python scripts/maintenance/fix-system-config-thresholds.py --environment dev --region ap-south-1
```

The script will:
1. ✅ Create a backup of the current configuration
2. ✅ Show current vs. new threshold values
3. ✅ Validate the new configuration
4. ⚠️  Ask for confirmation
5. ✅ Update the configuration in DynamoDB
6. ✅ Log the change to the audit history

### Step 2: Verify the Changes

After running the script, verify the changes in the admin dashboard:
1. Log in as an admin user
2. Navigate to System Configuration
3. Check that the threshold values are correct

### Step 3: Test the System

1. Verify that the configuration can be saved through the UI
2. Check that alerts are triggered at the correct thresholds
3. Monitor for any issues with existing devices

## Rollback

If you need to restore the previous configuration:

```bash
python scripts/maintenance/restore-config-backup.py config-backup-YYYYMMDD-HHMMSS.json --region ap-south-1
```

The backup file name is shown when you run the fix script.

## Safety Features

### Automatic Backup
- Creates a timestamped backup before making changes
- Backup file: `config-backup-YYYYMMDD-HHMMSS.json`

### Validation
- Validates new configuration against backend rules
- Checks all threshold relationships
- Ensures values are within scientific ranges

### Audit Logging
- Logs changes to `AquaChain-ConfigHistory` table
- Tracks who made the change and when
- Stores full configuration snapshot

### Version Control
- Creates a new version ID for the configuration
- Links to previous version for rollback
- Maintains complete version history

## Troubleshooting

### Error: "No authentication token found"
```bash
aws configure
# Enter your AWS Access Key ID and Secret Access Key
```

### Error: "Failed to connect to AWS"
Check your AWS credentials and region:
```bash
aws sts get-caller-identity
aws dynamodb list-tables --region ap-south-1
```

### Error: "No system configuration found in database"
The configuration table might be empty. Check if the table exists:
```bash
aws dynamodb describe-table --table-name AquaChain-SystemConfig --region ap-south-1
```

### Error: "Validation failed"
The script validates the new configuration before applying it. If validation fails, the configuration is not updated. Check the error messages for details.

## Files

- `fix-system-config-thresholds.py` - Main script to fix thresholds
- `restore-config-backup.py` - Script to restore from backup
- `README-CONFIG-FIX.md` - This documentation

## Impact

⚠️ **System-Wide Impact**: Changes affect ALL devices and users immediately.

After updating:
- All devices will use the new thresholds for alert generation
- Existing alerts may be re-evaluated
- Users may receive new alerts if readings exceed new thresholds

## Support

If you encounter issues:
1. Check the backup file is created before making changes
2. Review the validation errors if the script fails
3. Use the restore script to rollback if needed
4. Contact the development team for assistance

## Example Output

```
================================================================================
🔧 AquaChain - Fix System Configuration Thresholds
================================================================================

Environment: dev
Region: ap-south-1
Config Table: AquaChain-SystemConfig
History Table: AquaChain-ConfigHistory

✅ Connected to DynamoDB

================================================================================
STEP 1: Backing up current configuration
================================================================================
✅ Backup saved to: config-backup-20260227-143022.json

================================================================================
STEP 2: Current threshold values
================================================================================

📊 Turbidity:
  Current Critical Max: 5 NTU
  Current Warning Max:  4 NTU

📊 TDS:
  Current Critical Max: 500 ppm
  Current Warning Max:  400 ppm

📊 Temperature:
  Current Warning Min:  0.5°C
  Current Critical Min: 0.0°C
  Current Critical Max: 40.0°C
  Current Warning Max:  39.5°C

================================================================================
STEP 3: New threshold values (scientifically correct)
================================================================================

📊 Turbidity:
  New Critical Max: 4 NTU
  New Warning Max:  8 NTU

📊 TDS:
  New Critical Max: 300 ppm
  New Warning Max:  450 ppm

📊 Temperature:
  New Warning Min:  0°C
  New Critical Min: 10°C
  New Critical Max: 40°C
  New Warning Max:  50°C

================================================================================
STEP 4: Validating new configuration
================================================================================
✅ Validation passed - configuration is correct

================================================================================
⚠️  CONFIRMATION REQUIRED
================================================================================

This will update the system configuration in DynamoDB.
All devices and users will be affected immediately.

Backup file: config-backup-20260227-143022.json

To restore from backup, run:
  python scripts/maintenance/restore-config-backup.py config-backup-20260227-143022.json

Do you want to proceed? (yes/no): yes

================================================================================
STEP 5: Updating configuration
================================================================================
✅ Version history saved: v_2026-02-27T14:30:22.123456
✅ Configuration updated successfully

================================================================================
✅ SUCCESS
================================================================================

System configuration has been updated successfully!
Backup saved to: config-backup-20260227-143022.json

The new thresholds are now active for all devices and users.
```
