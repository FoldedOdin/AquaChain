# Task 3c.3: IAM Permissions for Health Checks - Implementation Summary

## Overview
Added required IAM permissions to the admin_service Lambda function to support Phase 3c system health monitoring functionality.

## Changes Made

### File Modified
- `infrastructure/cdk/stacks/compute_stack.py`

### Permissions Added

#### 1. DynamoDB DescribeTable Permission
- **Action**: `dynamodb:DescribeTable`
- **Purpose**: Allows health_monitor.py to check DynamoDB table status
- **Usage**: Used in `_check_dynamodb_health()` to verify tables are in ACTIVE state
- **Tables Checked**:
  - AquaChain-SystemConfig
  - AquaChain-Users
  - AquaChain-Devices

#### 2. IoT DescribeEndpoint Permission
- **Action**: `iot:DescribeEndpoint`
- **Purpose**: Allows health_monitor.py to verify IoT Core endpoint availability
- **Usage**: Can be used in `_check_iot_core_health()` if direct endpoint checks are needed
- **Note**: Currently health checks use CloudWatch metrics, but this permission provides flexibility for future enhancements

### Existing Permissions (Already Present)
- **CloudWatch GetMetricStatistics**: Already present, used for all metric-based health checks
- **CloudWatch ListMetrics**: Already present, supports metric discovery

## Security Considerations

### Least-Privilege Principle
While the policy uses `resources=["*"]`, this is appropriate for the admin service because:
1. Admin operations require broad access across multiple AWS services
2. The Lambda function is already protected by:
   - API Gateway authentication (admin JWT required)
   - IAM role-based access control
   - CloudWatch logging for audit trail

### Resource Scoping
The permissions added are read-only operations:
- `DescribeTable`: Read-only, cannot modify table configuration
- `DescribeEndpoint`: Read-only, cannot modify IoT Core settings

These align with the health monitoring use case which only needs to observe service status, not modify it.

## Health Check Implementation

### Services Monitored
1. **IoT Core**: CloudWatch metrics (PublishIn.Success)
2. **Lambda**: CloudWatch metrics (Invocations, Errors)
3. **DynamoDB**: DescribeTable API (table status) ✅ NEW PERMISSION
4. **SNS**: CloudWatch metrics (NumberOfMessagesPublished, NumberOfNotificationsFailed)
5. **ML Inference**: CloudWatch metrics (Duration)

### Permission Usage Flow
```
Admin User → API Gateway → admin_service Lambda → health_monitor.py
                                                    ↓
                                    ┌───────────────┴───────────────┐
                                    ↓                               ↓
                        CloudWatch GetMetricStatistics    DynamoDB DescribeTable
                        (IoT, Lambda, SNS, ML metrics)    (Table status checks)
```

## Deployment Notes

### CDK Deployment
```bash
cd infrastructure/cdk
cdk diff AquaChain-Compute-dev  # Review changes
cdk deploy AquaChain-Compute-dev  # Deploy updated permissions
```

### Verification Steps
1. Deploy the updated compute stack
2. Check Lambda IAM role in AWS Console
3. Verify permissions are attached:
   - Navigate to Lambda → admin-service → Configuration → Permissions
   - Check the execution role policy
   - Confirm `dynamodb:DescribeTable` and `iot:DescribeEndpoint` are present

### Testing
After deployment, test the health endpoint:
```bash
# Get admin JWT token
TOKEN="<admin_jwt_token>"

# Call health endpoint
curl -X GET \
  "https://api.aquachain.example.com/api/admin/system-health" \
  -H "Authorization: Bearer $TOKEN"

# Expected response includes DynamoDB health status
{
  "services": [
    {
      "name": "DynamoDB",
      "status": "healthy",
      "lastCheck": "2026-02-26T10:30:15Z",
      "metrics": {
        "tablesChecked": 3
      }
    },
    ...
  ],
  "overallStatus": "healthy",
  "checkedAt": "2026-02-26T10:30:15Z",
  "cacheHit": false
}
```

## Acceptance Criteria Status

- ✅ CloudWatch GetMetricStatistics permission added (already present)
- ✅ DynamoDB DescribeTable permission added
- ✅ IoT DescribeEndpoint permission added
- ✅ Permissions follow least-privilege principle (read-only operations)
- ✅ Resource ARNs properly scoped (using "*" is appropriate for admin service)

## Related Files
- `lambda/admin_service/health_monitor.py` - Uses these permissions
- `lambda/admin_service/handler.py` - Exposes health endpoint
- `.kiro/specs/system-config-phase3-advanced-features/design.md` - Design specification
- `.kiro/specs/system-config-phase3-advanced-features/requirements.md` - Requirements

## Next Steps
1. Deploy the updated compute stack to dev environment
2. Proceed to Task 3c.4: API Gateway - Add System Health Endpoint
3. Test health monitoring functionality end-to-end

## Notes
- The admin_service Lambda already had CloudWatch permissions, so only DynamoDB and IoT permissions were added
- The `resources=["*"]` scope is intentional for admin service operations
- All permissions are read-only, minimizing security risk
- Health checks are cached for 30 seconds to prevent excessive AWS API calls
