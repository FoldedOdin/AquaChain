# Cost Reduction Guide - Reduce from ₹10,375 to ₹3,000-5,000/month

## 🎯 Target: Reduce cost by 50-70%

**Current**: ₹10,375/month  
**Target**: ₹3,000-5,000/month  
**Savings**: ₹5,375-7,375/month

---

## 🚀 Quick Wins (Do These First)

### 1. Remove Redis Cache Stack (Save ₹996/month)

**Why**: You don't need caching for a demo project. DynamoDB is fast enough.

```bash
cd infrastructure/cdk

# Delete the cache stack
cdk destroy AquaChain-Cache-dev --force

# Confirm deletion
aws cloudformation describe-stacks --region ap-south-1 --stack-name AquaChain-Cache-dev
```

**Savings**: ₹996/month ✅

---

### 2. Remove Performance Dashboard (Save ₹498/month)

**Why**: You already have basic monitoring. Extra dashboards are overkill.

```bash
# Delete performance dashboard
cdk destroy AquaChain-PerformanceDashboard-dev --force
```

**Savings**: ₹498/month ✅

---

### 3. Remove API Throttling Stack (Save ₹166/month)

**Why**: No real traffic to throttle in a demo project.

```bash
# Delete API throttling
cdk destroy AquaChain-APIThrottling-dev --force
```

**Savings**: ₹166/month ✅

---

### 4. Remove Phase3 Stack (Save ₹830/month)

**Why**: Advanced ML monitoring features you don't need yet.

```bash
# Delete Phase3 infrastructure
cdk destroy AquaChain-Phase3-dev --force
```

**Savings**: ₹830/month ✅

---

### 5. Remove ML Registry Stack (Save ₹415/month)

**Why**: Model versioning is overkill for a project.

```bash
# Delete ML registry
cdk destroy AquaChain-MLRegistry-dev --force
```

**Savings**: ₹415/month ✅

---

### 6. Remove GDPR Compliance Stack (Save ₹249/month)

**Why**: Not needed for academic project.

```bash
# Delete GDPR compliance
cdk destroy AquaChain-GDPRCompliance-dev --force
```

**Savings**: ₹249/month ✅

---

### 7. Remove Data Classification Stack (Save ₹249/month)

**Why**: Basic encryption is enough.

```bash
# Delete data classification
cdk destroy AquaChain-DataClassification-dev --force
```

**Savings**: ₹249/month ✅

---

## 📊 After Quick Wins

**Original Cost**: ₹10,375/month  
**After Removing 7 Stacks**: ₹10,375 - ₹3,403 = **₹6,972/month**

**Stacks Remaining**: 13 (down from 20)  
**Savings So Far**: ₹3,403/month (33% reduction) ✅

---

## 🔧 Advanced Optimizations (Optional)

### 8. Reduce CloudWatch Log Retention (Save ₹564/month)

**Current**: 30 days retention  
**Optimized**: 3 days retention

```bash
# Edit each Lambda function's log retention
# In infrastructure/cdk/stacks/compute_stack.py

# Find all instances of:
log_retention=logs.RetentionDays.ONE_MONTH

# Replace with:
log_retention=logs.RetentionDays.THREE_DAYS

# Redeploy
cdk deploy AquaChain-Compute-dev --require-approval never
```

**Savings**: ₹564/month ✅

---

### 9. Disable X-Ray Tracing (Save ₹664/month)

**Why**: Only needed for debugging production issues.

```bash
# In infrastructure/cdk/stacks/compute_stack.py

# Find all instances of:
tracing=lambda_.Tracing.ACTIVE

# Replace with:
tracing=lambda_.Tracing.DISABLED

# Redeploy
cdk deploy AquaChain-Compute-dev --require-approval never
```

**Savings**: ₹664/month ✅

---

### 10. Remove Disaster Recovery Stack (Save ₹415/month)

**Why**: Not critical for a demo project.

```bash
# Delete DR stack
cdk destroy AquaChain-DR-dev --force
```

**Savings**: ₹415/month ✅

---

### 11. Remove Backup Stack (Save ₹207/month)

**Why**: You can manually backup if needed.

```bash
# Delete backup stack
cdk destroy AquaChain-Backup-dev --force
```

**Savings**: ₹207/month ✅

---

### 12. Simplify Monitoring Stack (Save ₹498/month)

**Current**: 3 dashboards + many alarms  
**Optimized**: 1 dashboard + essential alarms

```bash
# Edit infrastructure/cdk/stacks/monitoring_stack.py
# Comment out extra dashboards and non-critical alarms

# Or just remove the monitoring stack entirely
cdk destroy AquaChain-Monitoring-dev --force

# You'll still have basic CloudWatch metrics
```

**Savings**: ₹498/month ✅

---

## 📊 Final Cost Breakdown

### Option 1: Conservative (Keep Core Features)

**Remove**: 7 stacks (Cache, PerformanceDashboard, APIThrottling, Phase3, MLRegistry, GDPR, DataClassification)

```
Original Cost:           ₹10,375
After Removals:          -₹3,403
Final Cost:              ₹6,972/month
Savings:                 33%
```

**Stacks Remaining**: 13

- ✅ Core, VPC, Security, Data, Compute, LambdaLayers
- ✅ API, LandingPage, CloudFront
- ✅ Monitoring, IoTSecurity, Backup, DR

---

### Option 2: Aggressive (Maximum Savings)

**Remove**: 12 stacks + optimizations

```
Original Cost:           ₹10,375
Remove 12 stacks:        -₹5,753
Reduce log retention:    -₹564
Disable X-Ray:           -₹664
Final Cost:              ₹3,394/month
Savings:                 67%
```

**Stacks Remaining**: 8 (Minimal but functional)

- ✅ Core, Security, Data, Compute
- ✅ API, LandingPage, CloudFront
- ✅ Basic Monitoring

---

### Option 3: Ultra-Minimal (For Very Tight Budget)

**Keep Only Essential**: 6 stacks

```
Original Cost:           ₹10,375
Keep only 6 stacks:      ₹2,500-3,000/month
Savings:                 71-76%
```

**Stacks Remaining**: 6

- ✅ Core
- ✅ Security (minimal)
- ✅ Data
- ✅ Compute
- ✅ API
- ✅ LandingPage

---

## 🎯 My Recommended Approach

### Step 1: Quick Wins (Do Now)

```bash
# Remove these 7 stacks (saves ₹3,403/month)
cdk destroy AquaChain-Cache-dev --force
cdk destroy AquaChain-PerformanceDashboard-dev --force
cdk destroy AquaChain-APIThrottling-dev --force
cdk destroy AquaChain-Phase3-dev --force
cdk destroy AquaChain-MLRegistry-dev --force
cdk destroy AquaChain-GDPRCompliance-dev --force
cdk destroy AquaChain-DataClassification-dev --force
```

**New Cost**: ₹6,972/month (33% savings)

---

### Step 2: If Still Too Expensive

```bash
# Remove these 3 more stacks (saves ₹1,120/month)
cdk destroy AquaChain-DR-dev --force
cdk destroy AquaChain-Backup-dev --force
cdk destroy AquaChain-Monitoring-dev --force
```

**New Cost**: ₹5,852/month (44% savings)

---

### Step 3: If Need Even More Savings

```bash
# Disable X-Ray and reduce logs (saves ₹1,228/month)
# Edit compute_stack.py as shown above
# Then redeploy
cdk deploy AquaChain-Compute-dev --require-approval never
```

**New Cost**: ₹4,624/month (55% savings)

---

## 📋 Complete Removal Script

Save this as `reduce-costs.bat`:

```batch
@echo off
echo ========================================
echo AquaChain Cost Reduction Script
echo ========================================
echo.
echo This will remove 7 non-essential stacks
echo Estimated savings: ₹3,403/month
echo.
pause

cd infrastructure\cdk

echo [1/7] Removing Cache stack...
call cdk destroy AquaChain-Cache-dev --force

echo [2/7] Removing PerformanceDashboard stack...
call cdk destroy AquaChain-PerformanceDashboard-dev --force

echo [3/7] Removing APIThrottling stack...
call cdk destroy AquaChain-APIThrottling-dev --force

echo [4/7] Removing Phase3 stack...
call cdk destroy AquaChain-Phase3-dev --force

echo [5/7] Removing MLRegistry stack...
call cdk destroy AquaChain-MLRegistry-dev --force

echo [6/7] Removing GDPRCompliance stack...
call cdk destroy AquaChain-GDPRCompliance-dev --force

echo [7/7] Removing DataClassification stack...
call cdk destroy AquaChain-DataClassification-dev --force

echo.
echo ========================================
echo Cost Reduction Complete!
echo ========================================
echo.
echo Removed: 7 stacks
echo Savings: ₹3,403/month
echo New cost: ~₹6,972/month
echo.
echo Remaining stacks: 13
echo - Core infrastructure
echo - API and Frontend
echo - Basic monitoring
echo - Security and backup
echo.

cd ..\..
```

---

## ⚠️ What You'll Lose vs Keep

### ❌ What You'll Lose (Not Important for Demo)

- Redis caching (DynamoDB is fast enough)
- Advanced performance dashboards (basic monitoring remains)
- API throttling (no real traffic anyway)
- ML model versioning (not using it)
- GDPR compliance features (not needed)
- Advanced data classification (basic encryption remains)

### ✅ What You'll Keep (Important for Demo)

- ✅ Full API functionality
- ✅ Frontend website
- ✅ Lambda functions (all 8)
- ✅ DynamoDB database
- ✅ IoT device connectivity
- ✅ User authentication (Cognito)
- ✅ Security (KMS encryption)
- ✅ Basic monitoring
- ✅ Backup and DR (optional)

---

## 💰 Cost Comparison

| Scenario                         | Monthly | 3 Months | 6 Months |
| -------------------------------- | ------- | -------- | -------- |
| **Current (20 stacks)**          | ₹10,375 | ₹31,125  | ₹62,250  |
| **After Quick Wins (13 stacks)** | ₹6,972  | ₹20,916  | ₹41,832  |
| **Aggressive (8 stacks)**        | ₹3,394  | ₹10,182  | ₹20,364  |
| **Ultra-Minimal (6 stacks)**     | ₹2,500  | ₹7,500   | ₹15,000  |

---

## 🎓 For Your Project

**My Recommendation**: Go with **Option 1 (Conservative)**

**Why?**

- Still looks impressive (13 stacks)
- Saves 33% (₹3,403/month)
- Keeps all core functionality
- Easy to do (just delete 7 stacks)

**3-Month Project Cost**: ₹20,916 (vs ₹31,125 originally)  
**Savings**: ₹10,209 💰

---

## 🚀 Execute Now

Run these commands to save ₹3,403/month immediately:

```bash
cd infrastructure/cdk

cdk destroy AquaChain-Cache-dev AquaChain-PerformanceDashboard-dev AquaChain-APIThrottling-dev AquaChain-Phase3-dev AquaChain-MLRegistry-dev AquaChain-GDPRCompliance-dev AquaChain-DataClassification-dev --force
```

**Done!** You just reduced your cost by 33% while keeping all essential features! 🎉
