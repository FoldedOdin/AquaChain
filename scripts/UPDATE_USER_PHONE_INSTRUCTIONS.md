# Update User Phone Number - Instructions

This guide explains how to manually add a phone number to a user in the AquaChain DynamoDB database.

## Prerequisites

1. **AWS Credentials**: Make sure your AWS credentials are configured
   - Run `aws configure` if not already done
   - Or ensure environment variables are set: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

2. **Python 3.x**: Installed and available in PATH

3. **boto3**: Python AWS SDK (will be installed automatically if missing)

## Quick Start

### Option 1: Using the Batch Script (Windows)

1. Open the script file: `scripts/update_user_phone.py`
2. Update these values at the top:
   ```python
   USER_EMAIL = 'karthikpradeep2005@gmail.com'  # User's email
   PHONE_NUMBER = '+919876543210'  # New phone number (with country code)
   ```

3. Run the batch script:
   ```bash
   scripts\update-user-phone.bat
   ```

4. Confirm when prompted

### Option 2: Using Python Directly

1. Edit `scripts/update_user_phone.py` and set:
   - `USER_EMAIL`: The email of the user (Karthik K Pradeep)
   - `PHONE_NUMBER`: The phone number to add (format: +91XXXXXXXXXX)

2. Run the script:
   ```bash
   python scripts/update_user_phone.py
   ```

3. Type `yes` when prompted to confirm

## Phone Number Format

**Important**: Use international format with country code:
- ✅ Correct: `+919876543210`
- ❌ Wrong: `9876543210`
- ❌ Wrong: `+91 98765 43210`

## What the Script Does

1. Connects to DynamoDB table `AquaChain-Users` in `ap-south-1` region
2. Searches for the user by email
3. Displays current user information
4. Asks for confirmation
5. Updates the `profile.phone` field
6. Updates the `updatedAt` timestamp
7. Shows the updated user details

## Verification

After running the script, you can verify the update by:

1. **Check the script output**: It will show the updated phone number
2. **Login to the application**: The user should now be able to place orders without the warning
3. **Check DynamoDB**: Use AWS Console to view the user record

## Troubleshooting

### Error: "User not found"
- Double-check the email address in the script
- Verify the user exists in DynamoDB using AWS Console

### Error: "Access Denied"
- Ensure your AWS credentials have DynamoDB write permissions
- Check IAM policy includes `dynamodb:UpdateItem` and `dynamodb:Scan`

### Error: "Table not found"
- Verify the table name is correct: `AquaChain-Users`
- Check you're using the correct AWS region: `ap-south-1`

### Error: "boto3 not found"
- Install boto3: `pip install boto3`

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit AWS credentials** to version control
2. **Use IAM roles** with least-privilege permissions
3. **Audit all manual database changes** for compliance
4. **Backup data** before making manual changes
5. **Log all manual updates** for audit trail

## Alternative: Using AWS Console

If you prefer using the AWS Console:

1. Go to DynamoDB in AWS Console
2. Select table: `AquaChain-Users`
3. Find the user by email using "Scan" with filter
4. Click "Edit item"
5. Navigate to `profile` → `phone`
6. Add the phone number
7. Update `updatedAt` to current timestamp
8. Save changes

## Support

If you encounter issues:
1. Check the error message in the script output
2. Verify AWS credentials and permissions
3. Check DynamoDB table exists and is accessible
4. Review CloudWatch logs for Lambda functions if needed

---

**Last Updated**: 2024
**Script Version**: 1.0
**Maintainer**: AquaChain Development Team
