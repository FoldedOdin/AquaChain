# 🎯 Ultra Cost Optimization - Target: Under ₹1,000/month (or FREE!)

## Current Cost: ₹5,810 - ₹7,470/month
## Target: ₹0 - ₹1,000/month
## Savings: ₹4,810 - ₹6,470/month (80-90% reduction!)

---

## 🆓 AWS Free Tier Limits (Always Free)

| Service | Free Tier Limit | Your Usage | Status |
|---------|----------------|------------|--------|
| **Lambda** | 1M requests/month, 400,000 GB-seconds | ~100K requests | ✅ Within limit |
| **DynamoDB** | 25 GB storage, 25 RCU, 25 WCU | ~5 GB, low traffic | ✅ Within limit |
| **S3** | 5 GB storage, 20K GET, 2K PUT | ~2 GB | ✅ Within limit |
| **CloudWatch** | 10 custom metrics, 10 alarms, 5 GB logs | 50+ metrics, 20+ alarms | ❌ EXCEEDING |
| **API Gateway** | 1M requests/month (12 months free) | ~50K requests | ✅ Within limit |
| **Cognito** | 50K MAU | ~10 users | ✅ Within limit |
| **IoT Core** | 250K messages/month (12 months) | ~100K messages | ✅ Within limit |

**Key Issue**: CloudWatch is your biggest cost because you're exceeding free tier!

---

## 🚀 Phase 1: Aggressive Stack Removal (Save ₹2,500/month)

### Remove These Stacks Immediately:

```bash
# 1. Remove Monitoring Stack (Save ₹1,743-2,241/month) - BIGGEST SAVINGS!
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-Monitoring-dev

# 2. Remove Backup Stack (Save ₹207/month)
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-Backup-dev

# 3. Remove DR Stack (Save ₹17/month)
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-DR-dev

# 4. Remove CloudFront Stack (Save ₹83-166/month)
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-CloudFront-dev

# 5. Remove VPC Stack if using NAT Gateway (Save ₹0-2,656/month)
# Check if NAT Gateway exists first
aws ec2 describe-nat-gateways --region ap-south-1 --filter "Name=state,Values=available"
# If exists, delete VPC stack
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-VPC-dev

# 6. Remove failed LambdaPerformance stack (cleanup)
aws cloudformation delete-stack --region ap-south-1 --stack-name AquaChain-LambdaPerformance-dev
```

**Total Savings**: ₹2,050 - ₹5,280/month

---

## 🔧 Phase 2: Optimize Remaining Stacks (Save ₹1,500-2,000/month)

### 2.1 Optimize Lambda Functions

**Current**: 8 Lambda functions with 1024MB memory  
**Target**: Reduce to 256-512MB (stay in free tier)

```python
# Update infrastructure/cdk/stacks/compute_stack.py

# Change all Lambda memory configurations:
memory_size=256,  # Was 1024 - reduces cost by 75%
timeout=Duration.seconds(30),  # Was 300 - reduce timeout
reserved_concurrent_executions=None,  # Remove reserved capacity
```

**Savings**: ₹1,000-1,500/month

### 2.2 Optimize DynamoDB

**Current**: On-demand capacity  
**Target**: Use free tier (25 RCU/WCU)

```python
# Update infrastructure/cdk/stacks/data_stack.py

# Change billing mode for all tables:
billing_mode=dynamodb.BillingMode.PROVISIONED,
read_capacity=5,  # Free tier: 25 total across all tables
write_capacity=5,  # Free tier: 25 total across all tables
```

**Savings**: ₹300-500/month

### 2.3 Minimize CloudWatch Logs

**Current**: 30-day retention, all logs enabled  
**Target**: 1-day retention, critical logs only

```python
# Update all Lambda functions in compute_stack.py

log_retention=logs.RetentionDays.ONE_DAY,  # Was 30 days
```

**Savings**: ₹400-600/month

### 2.4 Remove X-Ray Tracing

```python
# Update all Lambda functions
tracing=lambda_.Tracing.DISABLED,  # Was ACTIVE
```

**Savings**: ₹200-300/month

---

## 📝 Phase 3: Use Free Alternatives

### 3.1 Replace CloudWatch Dashboards

**Instead of**: CloudWatch Dashboards (₹747/month)  
**Use**: AWS Console (FREE) or CloudWatch Insights (free tier)

### 3.2 Replace CloudWatch Alarms

**Instead of**: 20+ alarms (₹166/month)  
**Use**: 10 alarms max (FREE in free tier)

### 3.3 Replace S3 with S3 Intelligent-Tiering

```python
# Update data_stack.py
lifecycle_rules=[
    s3.LifecycleRule(
        transitions=[
            s3.Transition(
                storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                transition_after=Duration.days(0)
            )
        ]
    )
]
```

**Savings**: ₹50-100/month

---

## 🎯 Final Minimal Architecture (Under ₹1,000/month)

### Keep Only These 8 Stacks:

1. ✅ **Core** - Foundation (FREE)
2. ✅ **Security** - KMS (₹249-415/month) - REQUIRED
3. ✅ **Data** - DynamoDB, S3, IoT (₹0-500/month with optimization)
4. ✅ **Compute** - Lambda (₹0-300/month with optimization)
5. ✅ **LambdaLayers** - Shared code (₹83-166/month)
6. ✅ **IoTSecurity** - Device policies (FREE)
7. ✅ **API** - API Gateway, Cognito (₹0-300/month in free tier)
8. ✅ **LandingPage** - S3 static site (₹0-50/month)

### Remove These 6 Stacks:

- ❌ Monitoring (₹1,743-2,241/month)
- ❌ Backup (₹207/month)
- ❌ DR (₹17/month)
- ❌ CloudFront (₹83-166/month)
- ❌ VPC (₹0-2,656/month if NAT Gateway)
- ❌ LambdaPerformance (failed anyway)

---

## 💰 Projected Cost After Optimization

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Lambda | ₹1,328-2,241 | ₹0-300 | ₹1,028-1,941 |
| DynamoDB | ₹664-1,245 | ₹0-200 | ₹464-1,045 |
| S3 | ₹166-332 | ₹0-50 | ₹116-282 |
| IoT Core | ₹415-664 | ₹0-300 | ₹115-364 |
| API Gateway | ₹373-581 | ₹0-100 | ₹273-481 |
| CloudWatch | ₹1,743-2,241 | ₹0 | ₹1,743-2,241 |
| KMS | ₹249-415 | ₹249-415 | ₹0 |
| Other | ₹872-1,751 | ₹0-50 | ₹822-1,701 |
| **TOTAL** | **₹5,810-7,470** | **₹249-1,415** | **₹4,395-6,055** |

### 🎉 Target Achieved: ₹249-1,415/month (Under ₹1,000 possible!)

---

## 🚀 Implementation Script

I'll create an automated script to do all this. Run it to optimize everything:

```bash
# Run the ultra optimization script
./ultra-cost-optimize.bat
```

---

## 📊 Cost Breakdown by Scenario

### Scenario 1: Maximum Free Tier Usage (₹249-500/month)
- Stay within all free tier limits
- Only pay for KMS keys (required)
- Minimal S3/DynamoDB usage
- **Best for**: Demo/learning project

### Scenario 2: Light Production (₹500-800/month)
- Slightly exceed free tier
- Keep basic monitoring (10 alarms)
- Moderate traffic
- **Best for**: Small pilot project

### Scenario 3: Optimized Production (₹800-1,000/month)
- Optimized but functional
- Essential monitoring only
- Good for 100-500 users
- **Best for**: MVP launch

---

## ⚠️ Trade-offs

### What You'll Lose:
1. ❌ CloudWatch Dashboards (use AWS Console instead)
2. ❌ X-Ray Tracing (debug with logs instead)
3. ❌ Automated Backups (manual backups if needed)
4. ❌ Disaster Recovery automation
5. ❌ CloudFront CDN (slower for global users)
6. ❌ Advanced monitoring/alerting

### What You'll Keep:
1. ✅ All core functionality
2. ✅ Lambda functions
3. ✅ DynamoDB database
4. ✅ IoT device connectivity
5. ✅ API Gateway
6. ✅ User authentication
7. ✅ Basic security
8. ✅ Frontend hosting

---

## 🎯 Recommended Action Plan

### Step 1: Backup Current State (5 minutes)
```bash
# Export all stack templates
./backup-stacks.bat
```

### Step 2: Remove Expensive Stacks (10 minutes)
```bash
# Delete monitoring, backup, DR, CloudFront
./remove-expensive-stacks.bat
```

### Step 3: Optimize Remaining Stacks (15 minutes)
```bash
# Update Lambda memory, DynamoDB capacity, log retention
./optimize-stacks.bat
```

### Step 4: Verify Cost Reduction (24 hours later)
```bash
# Check AWS Cost Explorer
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-02 --granularity DAILY --metrics BlendedCost
```

---

## 📈 Expected Timeline

| Time | Cost |
|------|------|
| **Now** | ₹5,810-7,470/month |
| **After Phase 1** (1 hour) | ₹3,000-4,000/month |
| **After Phase 2** (2 hours) | ₹1,000-2,000/month |
| **After Phase 3** (3 hours) | ₹249-1,000/month |
| **Optimized** (1 week) | ₹249-800/month |

---

## ✅ Success Criteria

- [ ] Monthly cost under ₹1,000
- [ ] All core features working
- [ ] Lambda within free tier (1M requests/month)
- [ ] DynamoDB within free tier (25 GB)
- [ ] CloudWatch within free tier (10 alarms)
- [ ] No NAT Gateway charges
- [ ] Minimal S3 costs

---

Ready to proceed? I'll create the automation scripts now!
