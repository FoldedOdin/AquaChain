# ✅ Ready to Deploy: API Gateway Profile Fix

**Created:** February 23, 2026  
**Status:** All backups complete, ready for deployment

---

## 📦 What's Been Prepared

### 1. Backup Created ✅
- **Location:** `backups/api-gateway/`
- **Timestamp:** 2026-02-23_05-08-13
- **Files:**
  - `profile-resources-backup-2026-02-23_05-08-13.json` (4 resources)
  - `profile-methods-backup-2026-02-23_05-08-13.json` (4 methods)

### 2. Deployment Script Ready ✅
- **Script:** `scripts/deployment/fix-api-gateway-profile-conflict-safe.ps1`
- **Features:**
  - Full backup before changes
  - Step-by-step verification
  - Automatic rollback on failure
  - Detailed progress reporting

### 3. Rollback Script Ready ✅
- **Script:** `scripts/deployment/rollback-api-gateway-profile.ps1`
- **Purpose:** Manual restoration if needed
- **Includes:** AWS Console and CLI instructions

### 4. Documentation Complete ✅
- **Guide:** `DOCS/deployment/API_GATEWAY_PROFILE_FIX.md`
- **Contents:**
  - Problem explanation
  - Step-by-step deployment
  - Troubleshooting guide
  - Post-deployment checklist

---

## 🎯 What Will Happen

### Current State
```
/api/profile (ID: d8exti) - DUPLICATE, BLOCKING UPDATES
├── /api/profile/request-otp (POST)
├── /api/profile/verify-and-update (PUT)
└── /api/profile/update (GET, PUT)
```

### After Deployment
```
/api/profile - CDK-MANAGED, UPDATES ENABLED
├── /api/profile/request-otp (POST)
└── /api/profile/verify-and-update (PUT)

/api/payments - NEW, PAYMENT INTEGRATION ENABLED
├── /api/payments/create-razorpay-order (POST)
├── /api/payments/verify-payment (POST)
├── /api/payments/create-cod-payment (POST)
└── /api/payments/payment-status (GET)
```

**Note:** `/api/profile/update` will be removed (not in CDK code). If needed, it can be added to CDK.

---

## 🚀 Deployment Command

```powershell
.\scripts\deployment\fix-api-gateway-profile-conflict-safe.ps1
```

**You will be prompted:**
1. Review what will be deleted
2. Type 'DELETE' to confirm
3. Script handles the rest automatically

**Expected duration:** 2-3 minutes

---

## ⚠️ Important Notes

### Downtime
- **Duration:** ~30 seconds
- **Affected:** Profile endpoints only
- **Impact:** Users updating profile during this window may see errors
- **Recommendation:** Deploy during low-traffic period

### What's Safe
- ✅ Full backup created
- ✅ Rollback script available
- ✅ CDK will recreate endpoints
- ✅ Same Lambda integrations
- ✅ Same authentication
- ✅ Payment Lambda already deployed

### What Changes
- ❌ `/api/profile/update` endpoint will be removed (not in CDK)
- ✅ `/api/profile/request-otp` recreated
- ✅ `/api/profile/verify-and-update` recreated
- ✅ `/api/payments/*` endpoints added (NEW)

---

## 📋 Pre-Deployment Checklist

- [x] Backup created
- [x] Deployment script tested (dry-run)
- [x] Rollback script ready
- [x] Documentation complete
- [ ] Low-traffic window identified
- [ ] Team notified of brief downtime
- [ ] Monitoring dashboard open

---

## 🔄 If Something Goes Wrong

### Option 1: Automatic Rollback
The script will detect failures and preserve backups. Check error message and fix CDK code, then redeploy.

### Option 2: Manual Rollback
```powershell
.\scripts\deployment\rollback-api-gateway-profile.ps1
```

This will show you:
- What was backed up
- Manual restoration commands
- AWS Console instructions

### Option 3: Contact Support
- Backup location: `backups/api-gateway/`
- Timestamp: 2026-02-23_05-08-13
- All configurations preserved

---

## ✅ Post-Deployment Verification

### 1. Check Endpoints Exist
```bash
aws apigateway get-resources --rest-api-id vtqjfznspc --region ap-south-1 --query "items[?contains(path, 'profile') || contains(path, 'payment')].path"
```

**Expected:**
- /api/profile
- /api/profile/request-otp
- /api/profile/verify-and-update
- /api/payments
- /api/payments/create-razorpay-order
- /api/payments/verify-payment
- /api/payments/create-cod-payment
- /api/payments/payment-status

### 2. Test Profile Endpoint
```bash
curl -X POST https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/profile/request-otp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected:** 200 OK with OTP sent

### 3. Test Payment Endpoint
```bash
curl -X POST https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/payments/create-razorpay-order \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000, "currency": "INR"}'
```

**Expected:** 200 OK with Razorpay order details

### 4. Check CloudWatch Logs
```bash
aws logs tail /aws/lambda/aquachain-function-user-management-dev --follow --region ap-south-1
aws logs tail /aws/lambda/aquachain-function-payment-service-dev --follow --region ap-south-1
```

**Expected:** No errors, successful invocations

---

## 🎉 Success Criteria

- [ ] API Gateway stack status: `UPDATE_COMPLETE`
- [ ] Profile endpoints accessible
- [ ] Payment endpoints accessible
- [ ] CORS working (no preflight errors)
- [ ] Authentication working
- [ ] Lambda logs show successful requests
- [ ] Frontend can make API calls
- [ ] No 403/404/502 errors

---

## 📞 Need Help?

**Documentation:**
- Full guide: `DOCS/deployment/API_GATEWAY_PROFILE_FIX.md`
- Project summary: `DOCS/PROJECT_WORK_SUMMARY_FEB_2026.md`

**Backup Location:**
- `backups/api-gateway/profile-resources-backup-2026-02-23_05-08-13.json`
- `backups/api-gateway/profile-methods-backup-2026-02-23_05-08-13.json`

**Scripts:**
- Deploy: `scripts/deployment/fix-api-gateway-profile-conflict-safe.ps1`
- Rollback: `scripts/deployment/rollback-api-gateway-profile.ps1`

---

## 🚦 Ready to Proceed

Everything is prepared and backed up. When you're ready:

```powershell
.\scripts\deployment\fix-api-gateway-profile-conflict-safe.ps1
```

Type `DELETE` when prompted, and the script will handle the rest.

**Good luck! 🚀**

