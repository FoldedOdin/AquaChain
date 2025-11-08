# 📊 Cost & Free Tier Monitoring Checklist

## ✅ Completed Today (November 1, 2025)

- ✅ Deployed 20 stacks successfully
- ✅ Optimized costs (57-68% reduction)
- ✅ DynamoDB changed to PROVISIONED mode
- ✅ Deleted expensive stacks (Monitoring, Backup, CloudFront, DR)
- ✅ Verified all infrastructure working
- ✅ DR stack cleaned up

---

## 📅 Tomorrow (November 2, 2025)

### 1. Check AWS Costs (5 minutes)

**Go to AWS Console:**
1. Open: https://console.aws.amazon.com/cost-management/home
2. Click "Cost Explorer"
3. View: "Daily costs"
4. Compare: November 1 vs October 31

**What to look for:**
- ✅ Cost should be lower than yesterday
- ✅ Should see ~₹80-120/day (₹2,500-3,500/month)
- ⚠️ If higher than ₹150/day, investigate

**Screenshot it!** Save for your records.

---

### 2. Check Free Tier Usage (5 minutes)

**Go to AWS Console:**
1. Open: https://console.aws.amazon.com/billing/home#/freetier
2. Review all services
3. Check for any warnings

**What to look for:**
- ✅ DynamoDB: Should show "Provisioned" usage
- ✅ Lambda: Should be under 1M requests
- ✅ S3: Should be under 5 GB
- ⚠️ Any service showing >80% usage

---

### 3. Check DynamoDB Throttling (2 minutes)

**Go to AWS Console:**
1. Open: https://console.aws.amazon.com/dynamodb
2. Click on any table
3. Go to "Metrics" tab
4. Look for "Throttled Requests"

**What to look for:**
- ✅ Throttled Requests: Should be 0
- ⚠️ If >0, may need to increase capacity

---

## 📅 This Week (November 2-8, 2025)

### Daily Quick Check (2 minutes/day)

**Run this command:**
```bash
test-everything.bat
```

**Or check manually:**
```bash
# Check stacks are healthy
aws cloudformation describe-stacks --region ap-south-1 --query "Stacks[?contains(StackName, 'AquaChain')].{Name:StackName, Status:StackStatus}" --output table
```

**What to look for:**
- ✅ All stacks: CREATE_COMPLETE or UPDATE_COMPLETE
- ⚠️ Any ROLLBACK or FAILED status

---

### Weekly Review (Friday, November 8)

**1. Cost Review (10 minutes)**
- Total costs for the week
- Compare to expected (₹2,500-3,500/month = ₹580-815/week)
- Identify any unexpected charges

**2. Free Tier Review (5 minutes)**
- Check all services still within limits
- Review any warnings

**3. Performance Check (5 minutes)**
- Test your application
- Check CloudWatch logs for errors
- Verify DynamoDB not throttling

---

## 📅 Monthly (December 1, 2025)

### Full Cost Analysis (30 minutes)

**1. Review November Costs**
- Total monthly cost
- Compare to target (₹2,500-3,500)
- Breakdown by service

**2. Optimization Opportunities**
- Any services costing more than expected?
- Any unused resources?
- Can optimize further?

**3. Free Tier Status**
- Still within limits?
- Any services approaching limits?
- Plan for when free tier expires (if applicable)

**4. Update Documentation**
- Update PROJECT_REPORT.md with actual costs
- Document any issues encountered
- Note any optimizations made

---

## 🚨 Alert Thresholds

### Immediate Action Required If:

**Costs:**
- ⚠️ Daily cost > ₹200 (₹6,000/month)
- 🚨 Daily cost > ₹300 (₹9,000/month)

**Free Tier:**
- ⚠️ Any service > 80% of free tier
- 🚨 Any service > 95% of free tier

**Performance:**
- ⚠️ DynamoDB throttling > 10 requests/day
- 🚨 Lambda errors > 5% of invocations
- 🚨 Any stack in FAILED state

---

## 📊 Expected Metrics

### Daily Costs (Target)
- **Minimum**: ₹80/day (₹2,400/month)
- **Average**: ₹100/day (₹3,000/month)
- **Maximum**: ₹120/day (₹3,600/month)

### Free Tier Usage (Target)
- **Lambda**: < 100K requests/month (10% of limit)
- **DynamoDB**: 25 RCU/25 WCU (at limit, but FREE)
- **S3**: < 2 GB (40% of limit)
- **API Gateway**: < 50K requests/month (5% of limit)
- **IoT Core**: < 100K messages/month (40% of limit)

### Performance (Target)
- **DynamoDB Throttling**: 0 requests
- **Lambda Errors**: < 1%
- **API Response Time**: < 500ms
- **Stack Status**: All CREATE_COMPLETE

---

## 🔧 Quick Commands

### Check Costs
```bash
# Today's costs
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-02 --granularity DAILY --metrics BlendedCost --region us-east-1
```

### Check Free Tier
```bash
check-free-tier-usage.bat
```

### Check Infrastructure
```bash
test-everything.bat
```

### Check DynamoDB
```bash
aws dynamodb describe-table --region ap-south-1 --table-name AquaChain-Readings-dev --query "Table.{BillingMode:BillingModeSummary.BillingMode, Read:ProvisionedThroughput.ReadCapacityUnits, Write:ProvisionedThroughput.WriteCapacityUnits}"
```

---

## 📝 Monitoring Log

### November 1, 2025
- ✅ Initial optimization completed
- ✅ Cost reduced from ₹5,810-7,470 to ₹2,500-3,500
- ✅ DynamoDB optimized to PROVISIONED
- ✅ All infrastructure tested and working
- ✅ DR stack deleted successfully

### November 2, 2025
- [ ] Check daily costs
- [ ] Check free tier usage
- [ ] Verify DynamoDB not throttling
- [ ] Test application

### November 8, 2025 (Weekly Review)
- [ ] Review week's costs
- [ ] Check free tier status
- [ ] Performance check
- [ ] Document any issues

### December 1, 2025 (Monthly Review)
- [ ] Full cost analysis
- [ ] Optimization review
- [ ] Update documentation
- [ ] Plan for next month

---

## 🎯 Success Criteria

**You're doing great if:**
- ✅ Daily costs: ₹80-120
- ✅ All services within free tier
- ✅ No DynamoDB throttling
- ✅ All stacks healthy
- ✅ Application working

**Need attention if:**
- ⚠️ Daily costs > ₹150
- ⚠️ Any service > 80% free tier
- ⚠️ DynamoDB throttling > 0
- ⚠️ Any errors in logs

**Urgent action if:**
- 🚨 Daily costs > ₹300
- 🚨 Any service > 95% free tier
- 🚨 Stack failures
- 🚨 Application down

---

## 📞 Resources

**AWS Console Links:**
- Cost Explorer: https://console.aws.amazon.com/cost-management/home
- Free Tier: https://console.aws.amazon.com/billing/home#/freetier
- CloudFormation: https://ap-south-1.console.aws.amazon.com/cloudformation/home
- DynamoDB: https://ap-south-1.console.aws.amazon.com/dynamodb/home

**Documentation:**
- OPTIMIZATION_COMPLETE.md - Full optimization results
- COST_OPTIMIZATION_SUMMARY.md - Optimization guide
- PROJECT_REPORT.md - Complete technical documentation

**Scripts:**
- test-everything.bat - Test all infrastructure
- check-free-tier-usage.bat - Check free tier usage

---

**Last Updated**: November 1, 2025  
**Next Review**: November 2, 2025  
**Status**: ✅ Monitoring Active
