# Dependency Scanner - Quick Reference Card

## 🚀 Quick Start

### Deploy
```bash
cd infrastructure/cdk
cdk deploy DependencyScannerStack
```

### Configure Alerts
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:REGION:ACCOUNT:aquachain-dependency-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### Manual Scan
```bash
aws lambda invoke \
  --function-name aquachain-dependency-scanner \
  --payload '{"scan_type":"all","source_paths":{...}}' \
  response.json
```

## 📊 Key Metrics

| Metric | Location | Threshold |
|--------|----------|-----------|
| Critical Vulnerabilities | CloudWatch | 0 |
| High Vulnerabilities | CloudWatch | 5 |
| Scan Duration | Lambda Logs | <5 min |
| Alert Latency | SNS | <1 min |

## 🔍 Common Commands

### View Latest Report
```bash
aws s3 cp s3://aquachain-dependency-scans-{account}/dependency-scans/latest.json - | jq .
```

### Check Scan Schedule
```bash
aws events describe-rule --name aquachain-weekly-dependency-scan
```

### View Logs
```bash
aws logs tail /aws/lambda/aquachain-dependency-scanner --follow
```

### Get Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AquaChain/Security \
  --metric-name Vulnerabilities_Total \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Maximum
```

## 🎯 Alert Thresholds

| Severity | Threshold | Action |
|----------|-----------|--------|
| Critical | 0 | Immediate alert |
| High | 5 | Alert if exceeded |
| Moderate | - | Report only |
| Low | - | Report only |

## 📅 Schedule

- **Frequency:** Weekly
- **Day:** Monday
- **Time:** 2:00 AM UTC
- **Duration:** ~2-3 minutes

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Timeout | Check Lambda logs, increase timeout if needed |
| No alerts | Verify SNS subscription confirmed |
| npm audit fails | Ensure package-lock.json uploaded |
| pip-audit fails | Check requirements.txt format |

## 📁 Important Locations

| Resource | Location |
|----------|----------|
| Reports | `s3://aquachain-dependency-scans-{account}/dependency-scans/` |
| Source Code | `s3://aquachain-source-snapshots-{account}/` |
| Dashboard | CloudWatch → Dashboards → AquaChain-Dependency-Security |
| Logs | CloudWatch → Log Groups → /aws/lambda/aquachain-dependency-scanner |

## 🔐 IAM Permissions Required

- `s3:GetObject` - Read source code
- `s3:PutObject` - Write reports
- `sns:Publish` - Send alerts
- `cloudwatch:PutMetricData` - Publish metrics
- `logs:CreateLogGroup` - Create log groups
- `logs:CreateLogStream` - Create log streams
- `logs:PutLogEvents` - Write logs

## 📞 Support

- **Documentation:** [README.md](./README.md)
- **Deployment:** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Technical Details:** [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

## ⚡ Quick Tips

1. Always check `latest.json` for most recent scan results
2. Subscribe multiple emails to SNS for redundancy
3. Review reports weekly even if no alerts
4. Keep source snapshots up to date
5. Monitor CloudWatch dashboard for trends

---

**Last Updated:** October 25, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
