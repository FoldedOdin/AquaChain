# AWS Account Migration - Quick Reference

Quick reference for switching AWS accounts. See [AWS_ACCOUNT_MIGRATION_GUIDE.md](AWS_ACCOUNT_MIGRATION_GUIDE.md) for detailed instructions.

---

## 🚀 Quick Steps

### 1. Configure AWS CLI
```bash
aws configure
# Enter: Access Key, Secret Key, Region, Output format

# Verify
aws sts get-caller-identity
```

### 2. Update Environment Files
```bash
# infrastructure/.env
AWS_ACCOUNT_ID=<new-account-id>
AWS_REGION=us-east-1

# infrastructure/cdk/.env
CDK_DEFAULT_ACCOUNT=<new-account-id>
CDK_DEFAULT_REGION=us-east-1
```

### 3. Bootstrap CDK
```bash
cd infrastructure/cdk
cdk bootstrap aws://<ACCOUNT-ID>/<REGION>
del cdk.context.json
```

### 4. Deploy
```bash
cd scripts/deployment
deploy-minimal.bat  # ~₹1,600-2,800/month
# or
deploy-all.bat      # ~₹12,000-16,000/month
```

### 5. Update Frontend
```bash
cd frontend
npm run get-aws-config
npm start
```

---

## ✅ Checklist

- [ ] `aws configure` with new credentials
- [ ] Update `infrastructure/.env`
- [ ] Update `infrastructure/cdk/.env`
- [ ] `cdk bootstrap` in new account
- [ ] Delete `cdk.context.json`
- [ ] Run deployment script
- [ ] `npm run get-aws-config`
- [ ] Test locally

---

## 📁 Files to Update

| File | What to Update |
|------|---------------|
| `infrastructure/.env` | AWS_ACCOUNT_ID, AWS_REGION |
| `infrastructure/cdk/.env` | CDK_DEFAULT_ACCOUNT, CDK_DEFAULT_REGION |
| `infrastructure/cdk/cdk.context.json` | **DELETE THIS FILE** |

**Auto-generated after deployment:**
- `frontend/.env.local`
- `frontend/.env.development`
- `frontend/.env.production`

---

## 💰 Cost After Migration

| Deployment | Monthly Cost |
|-----------|--------------|
| Minimal (7 stacks) | ₹1,600-2,800 |
| Full (22 stacks) | ₹12,000-16,000 |
| Deleted (0 stacks) | ₹0-80 |

---

## 🔧 Common Issues

### "Unable to resolve AWS account"
→ Update `AWS_ACCOUNT_ID` in `infrastructure/.env`

### "CDK bootstrap required"
→ Run `cdk bootstrap aws://ACCOUNT-ID/REGION`

### "Access Denied"
→ Check IAM permissions (need AdministratorAccess or equivalent)

### "Stack already exists"
→ Run `scripts/maintenance/delete-everything.bat` first

---

**Full Guide:** [AWS_ACCOUNT_MIGRATION_GUIDE.md](AWS_ACCOUNT_MIGRATION_GUIDE.md)
