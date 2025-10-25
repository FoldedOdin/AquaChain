# 🔐 Security Quick Start Guide

**For Immediate Production Deployment**

---

## ⚡ 5-Minute Security Setup

### Step 1: Rotate AWS Credentials (2 minutes)

```bash
# Delete exposed key
aws iam delete-access-key \
  --access-key-id AKIA3BEHVTJZ7GOPCM6W \
  --user-name YOUR_IAM_USERNAME

# Create new key (save securely!)
aws iam create-access-key --user-name YOUR_IAM_USERNAME

# Configure AWS CLI with new credentials
aws configure
```

### Step 2: Store reCAPTCHA Secret (1 minute)

```bash
# Get your reCAPTCHA secret from Google Console
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name aquachain/recaptcha/secret-key \
  --secret-string '{"secret_key":"YOUR_RECAPTCHA_SECRET"}' \
  --region ap-south-1
```

### Step 3: Update Environment Variables (1 minute)

```bash
# frontend/.env.production
REACT_APP_RECAPTCHA_SITE_KEY=your_site_key_here
REACT_APP_AWS_REGION=ap-south-1
REACT_APP_USER_POOL_ID=your_pool_id
REACT_APP_USER_POOL_CLIENT_ID=your_client_id

# infrastructure/.env (use IAM roles instead!)
AWS_ACCOUNT_ID=758346259059
AWS_DEFAULT_REGION=ap-south-1
# DO NOT add access keys here!
```

### Step 4: Deploy Security Updates (1 minute)

```bash
# Deploy Lambda functions with security middleware
cd lambda/auth_service
pip install -r requirements.txt
zip -r function.zip .
aws lambda update-function-code \
  --function-name aquachain-auth-service \
  --zip-file fileb://function.zip

# Deploy frontend with reCAPTCHA
cd frontend
npm run build
# Deploy to your hosting service
```

---

## 🛡️ Security Checklist

### Before Production
- [ ] AWS credentials rotated
- [ ] Credentials removed from git history
- [ ] reCAPTCHA configured (site key + secret)
- [ ] AWS Secrets Manager configured
- [ ] IAM roles assigned to Lambda functions
- [ ] Rate limiting enabled
- [ ] HTTPS/TLS configured
- [ ] CloudTrail enabled
- [ ] CloudWatch alarms set up

### Authentication
- [ ] AWS Cognito user pool created
- [ ] OAuth providers configured (Google)
- [ ] MFA enabled for admin accounts
- [ ] Password policy enforced
- [ ] Session timeout configured

### IoT Security
- [ ] Device certificates managed
- [ ] IoT policies restricted
- [ ] Firmware signed
- [ ] Debug mode disabled in production
- [ ] OTA updates secured

---

## 🚨 Emergency Procedures

### If Credentials Are Compromised

```bash
# 1. Immediately deactivate
aws iam update-access-key \
  --access-key-id COMPROMISED_KEY \
  --status Inactive

# 2. Review CloudTrail logs
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=COMPROMISED_KEY \
  --max-results 50

# 3. Check for unauthorized resources
aws ec2 describe-instances
aws s3 ls
aws lambda list-functions

# 4. Delete compromised key
aws iam delete-access-key \
  --access-key-id COMPROMISED_KEY

# 5. Create new key and update applications
```

### If Attack Detected

```bash
# 1. Enable AWS WAF rate limiting
aws wafv2 create-rate-based-rule \
  --name emergency-rate-limit \
  --scope REGIONAL \
  --rate-limit 100

# 2. Review security groups
aws ec2 describe-security-groups

# 3. Check CloudWatch logs for suspicious activity
aws logs filter-log-events \
  --log-group-name /aws/lambda/aquachain \
  --filter-pattern "ERROR"

# 4. Enable GuardDuty if not already
aws guardduty create-detector --enable
```

---

## 📞 Security Contacts

### AWS Support
- **Phone:** 1-866-947-7829
- **Console:** https://console.aws.amazon.com/support/

### Security Incident Response
1. Isolate affected resources
2. Preserve logs and evidence
3. Contact AWS Support
4. Document incident
5. Implement fixes
6. Post-mortem review

---

## 🔍 Quick Security Audit

```bash
# Run these commands to verify security posture

# 1. Check for public S3 buckets
aws s3api list-buckets --query 'Buckets[*].Name' | \
  xargs -I {} aws s3api get-bucket-acl --bucket {}

# 2. Check IAM users without MFA
aws iam get-credential-report

# 3. Check security groups for 0.0.0.0/0
aws ec2 describe-security-groups \
  --filters Name=ip-permission.cidr,Values='0.0.0.0/0'

# 4. Check for unused access keys
aws iam list-access-keys --user-name YOUR_USER

# 5. Review CloudTrail status
aws cloudtrail describe-trails
```

---

## ✅ Daily Security Tasks

### Morning (5 minutes)
- [ ] Check CloudWatch alarms
- [ ] Review GuardDuty findings
- [ ] Check failed login attempts
- [ ] Verify backup completion

### Weekly (30 minutes)
- [ ] Review CloudTrail logs
- [ ] Update dependencies
- [ ] Run security scan
- [ ] Review IAM permissions
- [ ] Test disaster recovery

### Monthly (2 hours)
- [ ] Rotate credentials
- [ ] Security audit
- [ ] Penetration testing
- [ ] Update documentation
- [ ] Team security training

---

## 🎯 Security Metrics to Monitor

### Key Performance Indicators
- Failed authentication attempts
- Rate limit violations
- API error rates
- Unusual access patterns
- Certificate expiration dates
- Backup success rate

### CloudWatch Alarms
```bash
# Create alarm for failed logins
aws cloudwatch put-metric-alarm \
  --alarm-name failed-logins-high \
  --alarm-description "Alert on high failed login attempts" \
  --metric-name FailedLoginAttempts \
  --namespace AquaChain/Security \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## 📚 Quick Reference

### Important Files
- `infrastructure/SECURITY_CREDENTIALS_GUIDE.md` - Credential management
- `CRITICAL_FIXES_APPLIED.md` - What was fixed
- `COMPREHENSIVE_AUDIT_REPORT.md` - Full audit
- `iot-simulator/device_validation.py` - Input validation
- `lambda/auth_service/recaptcha_verifier.py` - CAPTCHA verification

### Security Tools
- **AWS Secrets Manager:** Store secrets
- **AWS IAM:** Access control
- **AWS CloudTrail:** Audit logging
- **AWS WAF:** Web application firewall
- **AWS GuardDuty:** Threat detection
- **reCAPTCHA v3:** Bot protection

### Support Resources
- AWS Security Hub: https://aws.amazon.com/security-hub/
- AWS Well-Architected: https://aws.amazon.com/architecture/well-architected/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

---

**Last Updated:** October 24, 2025  
**Status:** ✅ Critical fixes applied, ready for testing
