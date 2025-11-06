# AWS Cost Analysis - AquaChain Infrastructure (in ₹ INR)

**Exchange Rate**: $1 USD = ₹83 INR (approximate)  
**Region**: ap-south-1 (Mumbai)  
**Environment**: Development

---

## Current Deployed Infrastructure Cost (20 Stacks)

### 1. **Compute Layer**

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **Lambda Functions (8)** | On-demand, ~1M invocations | $15-25 | ₹1,245 - ₹2,075 |
| **Lambda Layers (2)** | Storage only | $1-2 | ₹83 - ₹166 |
| **ElastiCache Redis** | cache.t3.micro (1 node) | $12-15 | ₹996 - ₹1,245 |
| **Subtotal** | | **$28-42** | **₹2,324 - ₹3,486** |

### 2. **Data Layer**

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **DynamoDB (5 tables)** | On-demand, ~1M reads/writes | $8-15 | ₹664 - ₹1,245 |
| **S3 Buckets (4)** | ~50 GB storage | $2-4 | ₹166 - ₹332 |
| **IoT Core** | ~100 devices, 1M messages | $5-8 | ₹415 - ₹664 |
| **Subtotal** | | **$15-27** | **₹1,245 - ₹2,241** |

### 3. **API & Networking**

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **API Gateway (REST)** | ~1M requests | $3.50 | ₹290 |
| **API Gateway (WebSocket)** | ~100K connections | $1-2 | ₹83 - ₹166 |
| **CloudFront** | ~10 GB transfer | $1-2 | ₹83 - ₹166 |
| **WAF** | 2 Web ACLs | $10-12 | ₹830 - ₹996 |
| **VPC** | NAT Gateway (if used) | $0-32 | ₹0 - ₹2,656 |
| **Subtotal** | | **$15.50-51.50** | **₹1,286 - ₹4,274** |

### 4. **Security & Compliance**

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **KMS Keys (3)** | 3 keys, ~10K operations | $3-5 | ₹249 - ₹415 |
| **Cognito** | ~1000 MAU (Monthly Active Users) | $0-5 | ₹0 - ₹415 |
| **Secrets Manager** | ~5 secrets | $2-3 | ₹166 - ₹249 |
| **Subtotal** | | **$5-13** | **₹415 - ₹1,079** |

### 5. **Monitoring & Logging**

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **CloudWatch Logs** | ~10 GB ingestion | $5-8 | ₹415 - ₹664 |
| **CloudWatch Dashboards** | 3 dashboards | $9 | ₹747 |
| **CloudWatch Alarms** | ~20 alarms | $2 | ₹166 |
| **X-Ray Tracing** | ~1M traces | $5-8 | ₹415 - ₹664 |
| **Subtotal** | | **$21-27** | **₹1,743 - ₹2,241** |

### 6. **Backup & DR**

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **AWS Backup** | ~50 GB backups | $2.50 | ₹207 |
| **S3 Glacier (DR)** | ~20 GB | $0.20 | ₹17 |
| **Subtotal** | | **$2.70** | **₹224** |

---

## 📊 Current Total Monthly Cost (20 Stacks Deployed)

| Category | USD | INR |
|----------|-----|-----|
| **Minimum (Low Usage)** | $87.20 | **₹7,237** |
| **Typical (Medium Usage)** | $125 | **₹10,375** |
| **Maximum (High Usage)** | $163.20 | **₹13,545** |

### **Estimated Average: ~$125/month = ₹10,375/month**

---

## 💰 Cost Impact of Deploying Remaining Stacks

### Option 1: Deploy LambdaPerformance Stack Only

#### Additional Costs:

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **Provisioned Concurrency** | 5 instances @ 1024 MB (Data Processing) | $35-45 | ₹2,905 - ₹3,735 |
| **Provisioned Concurrency** | 3 instances @ 2048 MB (ML Inference) | $25-35 | ₹2,075 - ₹2,905 |
| **Additional CloudWatch** | Metrics & alarms | $2-3 | ₹166 - ₹249 |
| **Total Additional** | | **$62-83** | **₹5,146 - ₹6,889** |

**New Total with LambdaPerformance:**
- **Minimum**: $149.20 = **₹12,383**
- **Typical**: $187 = **₹15,521**
- **Maximum**: $246.20 = **₹20,434**

**Cost Increase**: +50-70% (+₹5,146 - ₹6,889/month)

---

### Option 2: Deploy AuditLogging Stack Only

#### Additional Costs:

| Service | Configuration | Monthly Cost (USD) | Monthly Cost (INR) |
|---------|--------------|-------------------|-------------------|
| **Kinesis Firehose** | ~10 GB/month ingestion | $0.30 | ₹25 |
| **S3 Standard** | ~10 GB (first 90 days) | $0.23 | ₹19 |
| **S3 Glacier** | ~20 GB (after 1 year) | $0.08 | ₹7 |
| **S3 Deep Archive** | ~30 GB (after 2 years) | $0.03 | ₹2 |
| **KMS Operations** | Encryption/decryption | $1-2 | ₹83 - ₹166 |
| **Total Additional** | | **$1.64-2.64** | **₹136 - ₹219** |

**New Total with AuditLogging:**
- **Minimum**: $88.84 = **₹7,373**
- **Typical**: $127 = **₹10,541**
- **Maximum**: $165.84 = **₹13,764**

**Cost Increase**: +2% (+₹136 - ₹219/month)

---

### Option 3: Deploy Both Stacks

**Total Additional Cost**: $63.64 - $85.64 = **₹5,282 - ₹7,108/month**

**New Total with Both:**
- **Minimum**: $150.84 = **₹12,519**
- **Typical**: $189 = **₹15,687**
- **Maximum**: $248.84 = **₹20,653**

**Cost Increase**: +52-72% (+₹5,282 - ₹7,108/month)

---

## 📈 Cost Comparison Summary (Monthly)

| Scenario | USD | INR | % Increase |
|----------|-----|-----|------------|
| **Current (20 stacks)** | $125 | ₹10,375 | Baseline |
| **+ LambdaPerformance** | $187 | ₹15,521 | +50% |
| **+ AuditLogging** | $127 | ₹10,541 | +2% |
| **+ Both Stacks** | $189 | ₹15,687 | +52% |

---

## 💡 Cost Optimization Tips

### To Reduce Current Costs:

1. **Use Free Tier** (First 12 months):
   - Lambda: 1M free requests/month
   - DynamoDB: 25 GB storage free
   - CloudWatch: 10 custom metrics free
   - **Savings**: ~₹1,500-2,000/month

2. **Optimize Lambda Memory**:
   - Right-size memory allocation
   - **Savings**: ~₹500-800/month

3. **Use S3 Intelligent-Tiering**:
   - Auto-moves data to cheaper storage
   - **Savings**: ~₹200-400/month

4. **Reduce CloudWatch Log Retention**:
   - Change from 30 days to 7 days
   - **Savings**: ~₹300-500/month

5. **Remove NAT Gateway** (if not needed):
   - Use VPC endpoints instead
   - **Savings**: ~₹2,656/month

### Potential Total Savings: ₹5,156 - ₹6,356/month

---

## 🎯 Recommendations Based on Budget

### Budget: ₹5,000 - ₹8,000/month
- ✅ Keep current 20 stacks
- ❌ Skip LambdaPerformance
- ❌ Skip AuditLogging
- ✅ Apply cost optimizations above
- **Target**: ₹5,000 - ₹6,000/month

### Budget: ₹10,000 - ₹12,000/month
- ✅ Keep current 20 stacks
- ❌ Skip LambdaPerformance (too expensive)
- ✅ Deploy AuditLogging (cheap, good for compliance)
- **Target**: ₹10,500 - ₹11,000/month

### Budget: ₹15,000 - ₹20,000/month
- ✅ Keep current 20 stacks
- ✅ Deploy LambdaPerformance (better UX)
- ✅ Deploy AuditLogging (compliance)
- **Target**: ₹15,500 - ₹16,000/month

### Budget: Unlimited (Production)
- ✅ Deploy everything
- ✅ Enable all features
- ✅ Add monitoring and alerting
- **Target**: ₹20,000 - ₹25,000/month

---

## 📊 Annual Cost Projection

| Scenario | Monthly (INR) | Annual (INR) |
|----------|---------------|--------------|
| **Current (Optimized)** | ₹6,000 | ₹72,000 |
| **Current (Typical)** | ₹10,375 | ₹1,24,500 |
| **With LambdaPerformance** | ₹15,521 | ₹1,86,252 |
| **With Both Stacks** | ₹15,687 | ₹1,88,244 |

---

## ⚠️ Important Notes

1. **Free Tier**: First 12 months get significant discounts
2. **Usage-Based**: Costs scale with traffic (estimates assume low-medium usage)
3. **Development vs Production**: Dev costs are typically 30-50% of production
4. **Mumbai Region**: Slightly more expensive than US regions (~10-15%)

---

## 🎓 My Recommendation

**For Development/Learning:**
```
Current Setup: ₹10,375/month
Skip both optional stacks
Apply cost optimizations
Target: ₹6,000-8,000/month
```

**For Production (Non-Regulated):**
```
Current Setup: ₹10,375/month
+ AuditLogging: +₹200/month
Skip LambdaPerformance initially
Target: ₹10,500-11,000/month
Add LambdaPerformance later if needed
```

**For Production (Regulated/High-Traffic):**
```
Current Setup: ₹10,375/month
+ Both Stacks: +₹5,500/month
Target: ₹15,500-16,000/month
Worth it for compliance + performance
```

---

## 💰 Bottom Line

**Current Cost**: ~₹10,375/month (₹1,24,500/year)

**If you deploy LambdaPerformance**: +₹5,500/month = **₹15,875/month total**

**If you deploy AuditLogging**: +₹200/month = **₹10,575/month total**

**If you deploy both**: +₹5,700/month = **₹16,075/month total**

**My advice**: Start with current setup, add AuditLogging if needed for compliance, add LambdaPerformance only when you have real traffic and need the performance boost.
