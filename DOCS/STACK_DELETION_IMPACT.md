# Stack Deletion Impact Guide

**⚠️ CRITICAL:** Understanding what breaks when you delete AWS CloudFormation stacks.

---

## 🎯 Quick Answer

**Q: Will Cognito work if I delete all stacks?**  
**A: NO. Cognito User Pool will be deleted and authentication will completely stop working.**

---

## 📊 Current Deployed Stacks

Your current deployment (ap-south-1):

| Stack Name | Contains | Critical? |
|------------|----------|-----------|
| **AquaChain-Security-dev** | KMS keys, IAM roles | 🔴 CRITICAL |
| **AquaChain-Data-dev** | DynamoDB tables, S3 buckets | 🔴 CRITICAL |
| **AquaChain-API-dev** | **Cognito User Pool**, API Gateway | 🔴 CRITICAL |
| **AquaChain-Compute-dev** | Lambda functions | 🔴 CRITICAL |
| **AquaChain-LambdaLayers-dev** | Shared Lambda code | 🟡 Important |
| **AquaChain-VPC-dev** | Network infrastructure | 🟡 Important |
| **AquaChain-Core-dev** | Foundation resources | 🟡 Important |
| **AquaChain-IoTSecurity-dev** | IoT policies | 🟢 Optional |
| **AquaChain-LandingPage-dev** | Static website | 🟢 Optional |

---

## 🔴 CRITICAL: What Breaks When You Delete Stacks

### 1. Delete API Stack → Authentication FAILS

**Stack:** `AquaChain-API-dev`

**Contains:**
- ✅ Cognito User Pool: `ap-south-1_KkQZlYidJ`
- ✅ Cognito User Pool Client
- ✅ API Gateway REST API
- ✅ API Gateway Authorizer

**If Deleted:**
```
❌ Cannot login (no Cognito User Pool)
❌ Cannot register new users
❌ All existing user sessions invalidated
❌ All JWT tokens become invalid
❌ API calls fail (no authorizer)
❌ Frontend authentication completely broken
```

**Impact:** **100% - Complete system failure**

---

### 2. Delete Data Stack → All Data LOST

**Stack:** `AquaChain-Data-dev`

**Contains:**
- ✅ DynamoDB tables (12 tables)
  - Readings, Devices, Users, Alerts
  - Audit logs, Ledger, Service requests
- ✅ S3 buckets
  - Data lake, Audit trail, ML models
- ✅ IoT Core resources

**If Deleted:**
```
❌ All sensor readings lost
❌ All user profiles lost
❌ All device registrations lost
❌ All alerts lost
❌ All audit logs lost
❌ IoT devices cannot connect
❌ ML models unavailable
```

**Impact:** **100% - Complete data loss**

**⚠️ WARNING:** Some tables have `RemovalPolicy.RETAIN` but most are set to `DESTROY` in dev environment!

---

### 3. Delete Security Stack → Encryption FAILS

**Stack:** `AquaChain-Security-dev`

**Contains:**
- ✅ KMS encryption keys (3 keys)
  - Data encryption key
  - Ledger signing key
  - IoT device key
- ✅ IAM roles (10+ roles)
- ✅ SNS topics for alerts

**If Deleted:**
```
❌ Cannot decrypt existing data
❌ DynamoDB tables become inaccessible (like the recent incident!)
❌ Lambda functions cannot assume roles
❌ S3 buckets cannot be accessed
❌ Alerts cannot be sent
```

**Impact:** **100% - System cannot function**

---

### 4. Delete Compute Stack → No Backend Processing

**Stack:** `AquaChain-Compute-dev`

**Contains:**
- ✅ Lambda functions (30+ functions)
  - Data processing
  - ML inference
  - Alert detection
  - User management
  - Device management

**If Deleted:**
```
❌ No data processing
❌ No ML predictions
❌ No alert generation
❌ No API endpoints work
❌ No real-time updates
```

**Impact:** **100% - No backend functionality**

---

## 💡 What You CAN Delete Safely

### Safe to Delete (Minimal Impact)

| Stack | Impact | Can Recreate? |
|-------|--------|---------------|
| **LandingPage** | Static website only | ✅ Yes, easily |
| **IoTSecurity** | Enhanced IoT policies | ✅ Yes, if needed |

### Risky but Recoverable

| Stack | Impact | Recovery |
|-------|--------|----------|
| **LambdaLayers** | Functions won't deploy | Redeploy layers |
| **VPC** | Network isolation lost | Redeploy VPC |
| **Core** | Foundation missing | Redeploy foundation |

---

## 🎯 Deletion Scenarios

### Scenario 1: Delete Everything

```bash
# This will destroy EVERYTHING
./scripts/delete-everything.bat
```

**Result:**
- ❌ All data permanently lost
- ❌ All users deleted
- ❌ All configurations gone
- ❌ System completely non-functional
- ✅ AWS cost: $0/month

**Recovery:** Full redeployment + data migration from backups (if available)

---

### Scenario 2: Delete Non-Critical Stacks Only

**Safe to delete:**
```bash
aws cloudformation delete-stack --stack-name AquaChain-LandingPage-dev --region ap-south-1
aws cloudformation delete-stack --stack-name AquaChain-IoTSecurity-dev --region ap-south-1
```

**Result:**
- ✅ Core system still works
- ✅ Authentication works
- ✅ Data preserved
- ✅ APIs functional
- ✅ Saves ~$5-10/month

---

### Scenario 3: Keep Only Essential Stacks

**Keep these for minimal functionality:**
1. **Security Stack** - Encryption keys, IAM roles
2. **Data Stack** - DynamoDB, S3
3. **API Stack** - Cognito, API Gateway
4. **Compute Stack** - Lambda functions

**Delete these:**
- LandingPage
- IoTSecurity
- VPC (if not using private subnets)
- Core (if not needed)

**Result:**
- ✅ System works
- ✅ Authentication works
- ✅ Data preserved
- ✅ Saves ~$10-15/month

---

## 🔄 Cognito Specific Impact

### Current Cognito Configuration

```
User Pool ID: ap-south-1_KkQZlYidJ
Stack: AquaChain-API-dev
Region: ap-south-1
```

### If API Stack is Deleted

**Immediate Impact:**
```javascript
// Frontend login attempt
await Auth.signIn(email, password);
// Error: User pool ap-south-1_KkQZlYidJ does not exist

// API call with JWT
fetch('/api/devices', {
  headers: { Authorization: `Bearer ${token}` }
});
// Error: 401 Unauthorized - Invalid token
```

**User Experience:**
1. User tries to login → Error: "Authentication service unavailable"
2. Existing logged-in users → Automatically logged out
3. API calls → All fail with 401 Unauthorized
4. Frontend → Shows "Please login" but login doesn't work

### Recovery Options

**Option 1: Redeploy API Stack**
```bash
cd infrastructure/cdk
cdk deploy AquaChain-API-dev
```
- ✅ Creates new Cognito User Pool
- ❌ All users must re-register
- ❌ New User Pool ID (frontend config must update)

**Option 2: Export Users Before Deletion**
```bash
# Export users (if you plan to delete)
aws cognito-idp list-users \
  --user-pool-id ap-south-1_KkQZlYidJ \
  --region ap-south-1 > users-backup.json
```

**Option 3: Use Cognito Backup/Restore**
- Not natively supported by AWS
- Requires custom migration scripts

---

## 💰 Cost vs Functionality Trade-off

### Current Monthly Cost: ~$50-60

| Keep All Stacks | Keep Essential Only | Delete Everything |
|-----------------|---------------------|-------------------|
| $50-60/month | $30-40/month | $0/month |
| ✅ Full functionality | ✅ Core features work | ❌ Nothing works |
| ✅ All features | ⚠️ Limited features | ❌ Must redeploy |
| ✅ Production-ready | ✅ Dev-ready | ❌ Local dev only |

---

## 🛡️ Data Protection

### Tables with RETAIN Policy (Production)

In production, these tables are protected:
- Ledger table (immutable audit trail)
- Audit logs table (compliance)

### Tables with DESTROY Policy (Dev)

In dev environment, these are deleted:
- All other tables

**⚠️ WARNING:** Your current deployment is in **dev** mode, so most data will be **permanently deleted** when stacks are removed!

---

## 📋 Pre-Deletion Checklist

Before deleting any stack:

### 1. Backup Critical Data
```bash
# Export DynamoDB tables
aws dynamodb create-backup \
  --table-name aquachain-audit-logs-dev \
  --backup-name pre-deletion-backup \
  --region ap-south-1

# Export Cognito users
aws cognito-idp list-users \
  --user-pool-id ap-south-1_KkQZlYidJ \
  --region ap-south-1 > cognito-users-backup.json

# Download S3 data
aws s3 sync s3://aquachain-data-dev-758346259059 ./s3-backup/
```

### 2. Document Configuration
```bash
# Save stack outputs
aws cloudformation describe-stacks \
  --stack-name AquaChain-API-dev \
  --region ap-south-1 > api-stack-config.json
```

### 3. Update Frontend Config
```bash
# If you're deleting and redeploying, frontend will need new endpoints
cd frontend
npm run get-aws-config
```

### 4. Notify Users
- Inform users of downtime
- Export user data if required (GDPR)
- Plan migration timeline

---

## 🚀 Recommended Approach

### For Cost Optimization (Keep System Working)

**Option A: Optimize Without Deletion**
```bash
# Use the cost optimization script
./scripts/ultra-cost-optimize.bat
```
- ✅ Reduces costs by 57-68%
- ✅ System keeps working
- ✅ No data loss
- ✅ No downtime

**Option B: Delete Non-Essential Stacks**
```bash
# Delete only safe stacks
aws cloudformation delete-stack --stack-name AquaChain-LandingPage-dev
```
- ✅ Saves $5-10/month
- ✅ Core system works
- ✅ No data loss

### For Complete Shutdown

**If you want $0 cost:**
```bash
# 1. Backup everything first!
# 2. Delete all stacks
./scripts/delete-everything.bat
# 3. Use local development only
cd frontend && npm start
```

---

## ✅ Summary

### Will Cognito Work After Stack Deletion?

| Scenario | Cognito Works? | Why? |
|----------|----------------|------|
| Delete API Stack | ❌ NO | Cognito User Pool is deleted |
| Delete Data Stack | ✅ YES | Cognito is in API Stack |
| Delete Security Stack | ⚠️ PARTIAL | Cognito exists but IAM roles missing |
| Delete Compute Stack | ✅ YES | Cognito is in API Stack |
| Delete ALL Stacks | ❌ NO | Everything deleted |

### Key Takeaways

1. **Cognito is in API Stack** - Delete API Stack = No authentication
2. **All stacks are interconnected** - Deleting one breaks others
3. **Dev environment = Data loss** - Most tables have DESTROY policy
4. **Backup before deletion** - No native Cognito backup/restore
5. **Consider cost optimization** - Instead of deletion

### Recommendation

**Don't delete stacks if you want the system to work!**

Instead:
- ✅ Use cost optimization scripts
- ✅ Delete only non-essential stacks
- ✅ Use local development for testing
- ✅ Deploy to AWS only when needed

**Cost:** Optimize to $30-40/month instead of $0 with broken system.

---

**Last Updated:** November 1, 2025  
**Current Deployment:** 9 stacks in ap-south-1  
**Cognito User Pool:** ap-south-1_KkQZlYidJ (in AquaChain-API-dev)
