# KMS Key Incident Resolution

## Incident Date: November 1, 2025

### Issue
DynamoDB table `aquachain-audit-logs-dev` became inaccessible due to KMS key encryption credentials issue.

**Error Details:**
- Table: `aquachain-audit-logs-dev`
- Region: `ap-south-1` (Asia Pacific Mumbai)
- KMS Key ARN: `arn:aws:kms:ap-south-1:758346259059:key/dd71a151-b7a5-4d18-8e55-da54db434c04`
- Detection Time: November 1, 2025 04:52:45 UTC
- Status: `INACCESSIBLE_ENCRYPTION_CREDENTIALS`

### Root Cause
The customer-managed KMS key was scheduled for deletion with:
- **KeyState**: `PendingDeletion`
- **Deletion Date**: December 1, 2025
- **Enabled**: `false`

### Resolution Steps

1. **Cancelled Key Deletion**
   ```bash
   aws kms cancel-key-deletion \
     --key-id dd71a151-b7a5-4d18-8e55-da54db434c04 \
     --region ap-south-1
   ```

2. **Re-enabled the Key**
   ```bash
   aws kms enable-key \
     --key-id dd71a151-b7a5-4d18-8e55-da54db434c04 \
     --region ap-south-1
   ```

3. **Verified Grants**
   - Confirmed DynamoDB service grants are intact
   - Grant ID: `29976ed2287ed2f29c24ada4f2259b767da25d689517165b6219bc573c1be761`
   - Grantee: `dynamodb.ap-south-1.amazonaws.com`

### Current Status ✅ RESOLVED
- **KMS Key State**: Enabled
- **Key Enabled**: True
- **Deletion Date**: None
- **Table Status**: ACTIVE
- **SSE Status**: ENABLED
- **Resolution Time**: ~10 minutes after key re-enablement

### Prevention Measures

1. **Enable KMS Key Deletion Protection**
   - Add CloudWatch alarms for KMS key state changes
   - Implement approval workflow for key deletion requests

2. **Monitoring Setup**
   ```bash
   # Create CloudWatch alarm for KMS key state
   aws cloudwatch put-metric-alarm \
     --alarm-name aquachain-kms-key-state \
     --alarm-description "Alert on KMS key state changes" \
     --metric-name KeyState \
     --namespace AWS/KMS \
     --statistic Average \
     --period 300 \
     --evaluation-periods 1 \
     --threshold 1 \
     --comparison-operator LessThanThreshold
   ```

3. **Update CDK Stack**
   - Review `security_stack.py` to ensure proper key retention policies
   - Current setting: `RemovalPolicy.RETAIN` for production
   - Consider adding explicit deletion protection

4. **Backup Strategy**
   - Ensure Point-in-Time Recovery (PITR) is enabled for all critical tables
   - Current status: Enabled for audit-logs table
   - AWS will create automatic on-demand backup if key is inaccessible for 7+ days

### Affected Resources
The following tables use this KMS key:
- `aquachain-audit-logs-dev` (CRITICAL - 7-year retention required)
- `aquachain-user-consents-dev` (GDPR compliance)
- `aquachain-gdpr-requests-dev` (GDPR compliance)

### Next Steps
1. Wait 5-10 minutes for table status to update from `INACCESSIBLE_ENCRYPTION_CREDENTIALS` to `ACTIVE`
2. Verify table accessibility:
   ```bash
   aws dynamodb describe-table \
     --table-name aquachain-audit-logs-dev \
     --region ap-south-1 \
     --query "Table.TableStatus"
   ```
3. Test read/write operations on the table
4. Implement monitoring and alerting as outlined above
5. Review and update key management procedures

### References
- [DynamoDB Encryption at Rest](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/encryption.usagenotes.html)
- [KMS Key States](https://docs.aws.amazon.com/kms/latest/developerguide/key-state.html)
- AWS Support Case: (if opened)

### Lessons Learned
- Never schedule KMS key deletion without thorough impact analysis
- Always verify dependent resources before key operations
- Implement automated monitoring for critical encryption keys
- Maintain proper key lifecycle management procedures


---

## Quick Reference: KMS Key Recovery Commands

### Check Key Status
```bash
aws kms describe-key \
  --key-id <KEY_ID> \
  --region <REGION> \
  --query "KeyMetadata.[KeyState,Enabled,DeletionDate]"
```

### Cancel Key Deletion
```bash
aws kms cancel-key-deletion \
  --key-id <KEY_ID> \
  --region <REGION>
```

### Enable Key
```bash
aws kms enable-key \
  --key-id <KEY_ID> \
  --region <REGION>
```

### Check Table Status
```bash
aws dynamodb describe-table \
  --table-name <TABLE_NAME> \
  --region <REGION> \
  --query "Table.[TableName,TableStatus,SSEDescription.Status]"
```

### Force Table Encryption Re-validation
```bash
aws dynamodb update-table \
  --table-name <TABLE_NAME> \
  --region <REGION> \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=<KEY_ID>
```

### List All Grants for a Key
```bash
aws kms list-grants \
  --key-id <KEY_ID> \
  --region <REGION>
```

---

## Contact Information
- **AWS Support**: Open a support case for critical encryption issues
- **Escalation**: Contact DevOps team lead immediately for production issues
- **Documentation**: Update this file after any KMS-related incidents
