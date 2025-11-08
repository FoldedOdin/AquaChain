# 💰 Cost Optimization Summary - Get Under ₹1,000/month

## 🎯 Goal: Maximum Cost Efficiency (Target: ₹0-1,000/month)

**Current Cost**: ₹5,810 - ₹7,470/month ($70-90 USD)  
**Target Cost**: ₹0 - ₹1,000/month ($0-12 USD)  
**Potential Savings**: ₹4,810 - ₹6,470/month (80-90% reduction!)

---

## 📊 Current Situation (14 Stacks Deployed)

### Cost Breakdown:

| Service | Current Cost (INR/month) | % of Total |
|---------|-------------------------|------------|
| CloudWatch Monitoring | ₹1,743 - ₹2,241 | 30-32% 🔴 |
| Lambda Functions | ₹1,328 - ₹2,241 | 23-32% 🔴 |
| DynamoDB | ₹664 - ₹1,245 | 11-18% 🟡 |
| IoT Core | ₹415 - ₹664 | 7-9% 🟡 |
| API Gateway | ₹373 - ₹581 | 6-8% 🟢 |
| KMS | ₹249 - ₹415 | 4-6% 🟢 |
| Other | ₹1,038 - ₹1,083 | 15-18% 🟡 |

🔴 = Major cost driver  
🟡 = Moderate cost  
🟢 = Acceptable cost

---

## 🚀 3-Phase Optimization Plan

### Phase 1: Remove Expensive Stacks (Save ₹2,050-5,280/month)

**Action**: Delete non-essential stacks

```bash
# Run this script:
ultra-cost-optimize.bat
```

**Stacks to Remove**:
1. ❌ **Monitoring Stack** → Save ₹1,743-2,241/month (BIGGEST SAVINGS!)
2. ❌ **Backup Stack** → Save ₹207/month
3. ❌ **DR Stack** → Save ₹17/month
4. ❌ **CloudFront Stack** → Save ₹83-166/month
5. ❌ **VPC Stack** (if NAT Gateway) → Save ₹0-2,656/month
6. ❌ **LambdaPerformance** (failed) → Cleanup

**Time**: 10 minutes  
**Savings**: ₹2,050-5,280/month

---

### Phase 2: Optimize Lambda & DynamoDB (Save ₹2,000-3,500/month)

**Action**: Reduce resource allocation to stay in free tier

```bash
# Run this script:
python optimize-lambda-memory.py
cd infrastructure/cdk
cdk deploy --all
```

**Optimizations**:

| Resource | Before | After | Savings |
|----------|--------|-------|---------|
| Lambda Memory | 1024 MB | 256 MB | ₹1,000-1,500/month |
| Lambda Timeout | 300s | 30s | ₹200-300/month |
| DynamoDB Mode | On-demand | Provisioned (5/5) | ₹300-500/month |
| CloudWatch Logs | 30 days | 1 day | ₹400-600/month |
| X-Ray Tracing | Enabled | Disabled | ₹200-300/month |

**Time**: 15 minutes  
**Savings**: ₹2,100-3,200/month

---

### Phase 3: Maximize Free Tier Usage (Save ₹500-1,000/month)

**Action**: Stay within AWS Free Tier limits

**AWS Free Tier Limits**:

| Service | Free Tier | Your Usage | Status |
|---------|-----------|------------|--------|
| Lambda | 1M requests/month | ~100K | ✅ Within |
| DynamoDB | 25 GB, 25 RCU/WCU | ~5 GB, low | ✅ Within |
| S3 | 5 GB storage | ~2 GB | ✅ Within |
| CloudWatch | 10 metrics, 10 alarms | 50+, 20+ | ❌ OVER |
| API Gateway | 1M requests/month | ~50K | ✅ Within |
| IoT Core | 250K messages/month | ~100K | ✅ Within |

**Actions**:
- ✅ Reduce CloudWatch alarms from 20+ to 10 (FREE)
- ✅ Remove custom metrics (use default only)
- ✅ Use 1-day log retention
- ✅ Disable X-Ray tracing

**Time**: 5 minutes  
**Savings**: ₹500-1,000/month

---

## 💰 Final Cost Projection

### After Full Optimization:

| Component | Optimized Cost (INR/month) |
|-----------|---------------------------|
| Lambda (256MB, 1M requests) | ₹0 (Free Tier) |
| DynamoDB (5 RCU/WCU) | ₹0 (Free Tier) |
| S3 (2 GB) | ₹0 (Free Tier) |
| IoT Core (100K messages) | ₹0 (Free Tier) |
| API Gateway (50K requests) | ₹0 (Free Tier) |
| CloudWatch (10 alarms, 1d logs) | ₹0-300 |
| KMS (3 keys) | ₹249-415 |
| Cognito (10 users) | ₹0 (Free Tier) |
| **TOTAL** | **₹249-715/month** |

### 🎉 Target Achieved: Under ₹1,000/month!

---

## 📋 Implementation Checklist

### Step 1: Backup (5 minutes)
- [ ] Export current stack templates
- [ ] Document current configuration
- [ ] Take note of important resources

### Step 2: Remove Expensive Stacks (10 minutes)
- [ ] Run `ultra-cost-optimize.bat`
- [ ] Wait for stack deletions (5-10 minutes)
- [ ] Verify deletions in AWS Console

### Step 3: Optimize Remaining Stacks (15 minutes)
- [ ] Run `python optimize-lambda-memory.py`
- [ ] Review changes in CDK files
- [ ] Deploy: `cd infrastructure/cdk && cdk deploy --all`
- [ ] Wait for deployment (10-15 minutes)

### Step 4: Verify Free Tier Usage (5 minutes)
- [ ] Run `check-free-tier-usage.bat`
- [ ] Check AWS Free Tier dashboard
- [ ] Ensure all services within limits

### Step 5: Monitor Costs (24 hours later)
- [ ] Check AWS Cost Explorer
- [ ] Verify cost reduction
- [ ] Adjust if needed

---

## ⚠️ Trade-offs & Limitations

### What You'll Lose:
1. ❌ CloudWatch Dashboards (use AWS Console instead)
2. ❌ X-Ray Distributed Tracing (use logs for debugging)
3. ❌ Automated Backups (manual backups if needed)
4. ❌ Disaster Recovery automation
5. ❌ CloudFront CDN (direct S3/API access, slower for global users)
6. ❌ Advanced monitoring (only basic alarms)
7. ❌ Long log retention (1 day instead of 30 days)

### What You'll Keep:
1. ✅ All core functionality
2. ✅ Lambda functions (8 functions)
3. ✅ DynamoDB database (5 tables)
4. ✅ IoT device connectivity
5. ✅ API Gateway (REST + WebSocket)
6. ✅ User authentication (Cognito)
7. ✅ Basic security (KMS, IAM)
8. ✅ Frontend hosting (S3)
9. ✅ Basic monitoring (10 alarms)

### Performance Impact:
- Lambda: 256MB is sufficient for most operations (may be 10-20% slower)
- DynamoDB: Provisioned capacity is fine for low traffic
- Logs: 1-day retention means you need to check logs daily
- No CDN: Slightly slower for users far from ap-south-1 region

---

## 📈 Cost Comparison

| Scenario | Stacks | Monthly Cost (INR) | Use Case |
|----------|--------|-------------------|----------|
| **Current** | 14 | ₹5,810-7,470 | Full featured |
| **After Phase 1** | 8 | ₹3,000-4,000 | Reduced monitoring |
| **After Phase 2** | 8 | ₹1,000-2,000 | Optimized resources |
| **After Phase 3** | 8 | **₹249-715** | **Maximum efficiency** ✅ |
| **If all 22 deployed** | 22 | ₹10,375-13,545 | Enterprise (not recommended) |

---

## 🎯 Recommended Configuration

### Minimal Production Setup (₹249-715/month):

**Keep These 8 Stacks**:
1. ✅ Core - Foundation
2. ✅ Security - KMS, IAM
3. ✅ Data - DynamoDB, S3, IoT
4. ✅ Compute - Lambda (256MB)
5. ✅ LambdaLayers - Shared code
6. ✅ IoTSecurity - Device policies
7. ✅ API - API Gateway, Cognito
8. ✅ LandingPage - Frontend

**Configuration**:
- Lambda: 256MB memory, 30s timeout
- DynamoDB: Provisioned 5 RCU/5 WCU per table
- CloudWatch: 10 alarms, 1-day log retention
- X-Ray: Disabled
- No NAT Gateway
- No CloudFront CDN

**Good For**:
- Demo/portfolio project
- Learning/development
- Small pilot (< 100 users)
- MVP testing
- Academic project

---

## 🚀 Quick Start

### Option 1: Automated (Recommended)
```bash
# Run the ultra optimization script
ultra-cost-optimize.bat

# Wait for completion, then deploy optimized stacks
cd infrastructure/cdk
cdk deploy --all
```

### Option 2: Manual
```bash
# 1. Delete expensive stacks
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-Monitoring-dev
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-Backup-dev
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-DR-dev
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-CloudFront-dev

# 2. Optimize Lambda
python optimize-lambda-memory.py

# 3. Deploy
cd infrastructure/cdk
cdk deploy --all
```

---

## 📊 Monitoring Your Costs

### Daily:
- Check CloudWatch logs (1-day retention)
- Monitor Lambda invocations
- Review any errors

### Weekly:
- Check AWS Free Tier dashboard
- Review Cost Explorer
- Verify all services within limits

### Monthly:
- Review total costs
- Adjust if exceeding ₹1,000
- Optimize further if needed

---

## ✅ Success Criteria

After optimization, you should have:

- [ ] Monthly cost under ₹1,000 (ideally ₹249-715)
- [ ] All core features working
- [ ] Lambda within free tier (< 1M requests/month)
- [ ] DynamoDB within free tier (< 25 GB, < 25 RCU/WCU)
- [ ] CloudWatch within free tier (≤ 10 alarms)
- [ ] S3 within free tier (< 5 GB)
- [ ] IoT within free tier (< 250K messages/month)
- [ ] No unexpected charges

---

## 🆘 Troubleshooting

### If costs are still high:

1. **Check for NAT Gateway**:
   ```bash
   aws ec2 describe-nat-gateways --region ap-south-1
   ```
   If found, delete VPC stack (saves ₹2,656/month)

2. **Check CloudWatch logs**:
   - Reduce retention to 1 day
   - Delete old log groups
   - Disable verbose logging

3. **Check Lambda memory**:
   - Ensure all functions use 256MB
   - Check actual memory usage in CloudWatch

4. **Check DynamoDB**:
   - Verify provisioned capacity (not on-demand)
   - Ensure 5 RCU/5 WCU per table

5. **Check for orphaned resources**:
   ```bash
   # List all resources
   aws resourcegroupstaggingapi get-resources --region ap-south-1
   ```

---

## 📞 Need Help?

- **Cost issues**: Check AWS Cost Explorer
- **Free tier**: https://console.aws.amazon.com/billing/home#/freetier
- **Optimization**: Run `check-free-tier-usage.bat`
- **Questions**: Review ULTRA_COST_OPTIMIZATION.md

---

**Ready to optimize?** Run `ultra-cost-optimize.bat` now!

**Target**: ₹249-715/month (under ₹1,000) ✅  
**Savings**: ₹4,810-6,470/month (80-90% reduction) 🎉
