# Contact Form Deployment Checklist

Use this checklist to ensure successful deployment of the contact form service.

## Pre-Deployment

### AWS Account Setup
- [ ] AWS account created and accessible
- [ ] AWS CLI installed and configured
- [ ] AWS credentials have necessary permissions:
  - [ ] Lambda (create, update, invoke)
  - [ ] DynamoDB (create table, read/write)
  - [ ] API Gateway (create, configure)
  - [ ] SES (send email, verify identities)
  - [ ] CloudWatch (logs, metrics)
  - [ ] IAM (create roles, policies)

### Development Environment
- [ ] Python 3.11+ installed
- [ ] Node.js 16+ installed
- [ ] AWS CDK installed (`npm install -g aws-cdk`)
- [ ] Git repository cloned
- [ ] All dependencies installed

### Email Configuration
- [ ] Decided on sender email address (e.g., noreply@aquachain.io)
- [ ] Decided on admin email address (e.g., admin@aquachain.io)
- [ ] Email addresses are accessible for verification

## Deployment Steps

### Step 1: Database Setup
- [ ] Run setup script: `python scripts/setup-contact-service.py`
- [ ] Verify DynamoDB table created: `aquachain-contact-submissions`
- [ ] Confirm table has correct schema:
  - [ ] Primary key: `submissionId`
  - [ ] GSI: `email-createdAt-index`
  - [ ] GSI: `inquiryType-createdAt-index`
  - [ ] GSI: `status-createdAt-index`
  - [ ] TTL enabled on `ttl` attribute

### Step 2: Email Service Setup
- [ ] Request SES email verification:
  ```bash
  aws ses verify-email-identity --email-address noreply@aquachain.io
  aws ses verify-email-identity --email-address admin@aquachain.io
  ```
- [ ] Check email inbox for verification emails
- [ ] Click verification links in both emails
- [ ] Verify email status:
  ```bash
  aws ses get-identity-verification-attributes \
    --identities noreply@aquachain.io admin@aquachain.io
  ```
- [ ] Both emails show `VerificationStatus: Success`

### Step 3: Lambda Function Deployment
- [ ] Navigate to CDK directory: `cd infrastructure/cdk`
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Bootstrap CDK (if first time):
  ```bash
  cdk bootstrap aws://ACCOUNT_ID/us-east-1
  ```
- [ ] Deploy stack: `cdk deploy ContactServiceStack`
- [ ] Deployment completes successfully
- [ ] Note the API URL from stack outputs

### Step 4: API Gateway Configuration
- [ ] API Gateway endpoint created
- [ ] CORS configured correctly
- [ ] POST /contact method exists
- [ ] Lambda integration configured
- [ ] API deployed to `prod` stage
- [ ] Copy API endpoint URL

### Step 5: Frontend Configuration
- [ ] Add API URL to `frontend/.env`:
  ```
  REACT_APP_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
  ```
- [ ] Verify environment variable is loaded
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] No build errors

## Testing

### Backend Testing
- [ ] Test Lambda function directly:
  ```bash
  aws lambda invoke \
    --function-name aquachain-contact-form-handler \
    --payload '{"httpMethod":"POST","body":"{\"name\":\"Test\",\"email\":\"test@example.com\",\"message\":\"Test message\",\"inquiryType\":\"general\"}"}' \
    response.json
  ```
- [ ] Check response.json for success message
- [ ] Verify submission in DynamoDB:
  ```bash
  aws dynamodb scan --table-name aquachain-contact-submissions --max-items 1
  ```

### API Testing
- [ ] Test API endpoint with curl:
  ```bash
  curl -X POST https://your-api-url/contact \
    -H "Content-Type: application/json" \
    -d '{"name":"Test User","email":"test@example.com","phone":"+1234567890","message":"This is a test message","inquiryType":"general"}'
  ```
- [ ] Receive 200 OK response
- [ ] Response contains `submissionId`

### Email Testing
- [ ] Submit test form
- [ ] User receives confirmation email
- [ ] Admin receives notification email
- [ ] Both emails formatted correctly (HTML)
- [ ] Plain text version works

### Frontend Testing
- [ ] Navigate to contact form on website
- [ ] Fill out form with test data
- [ ] Submit form
- [ ] See success message
- [ ] Form resets after submission
- [ ] Check for any console errors

### Admin Dashboard Testing
- [ ] Navigate to admin dashboard
- [ ] View contact submissions
- [ ] Filter by status works
- [ ] Click on submission to view details
- [ ] Update submission status
- [ ] Status updates successfully

## Monitoring Setup

### CloudWatch Logs
- [ ] Lambda logs are being created
- [ ] API Gateway logs are enabled
- [ ] Log retention set appropriately (30 days)
- [ ] Can view logs in CloudWatch console

### CloudWatch Metrics
- [ ] Lambda metrics visible:
  - [ ] Invocations
  - [ ] Errors
  - [ ] Duration
- [ ] API Gateway metrics visible:
  - [ ] Request count
  - [ ] 4xx errors
  - [ ] 5xx errors
- [ ] DynamoDB metrics visible:
  - [ ] Read/Write capacity
  - [ ] Item count

### CloudWatch Alarms (Optional but Recommended)
- [ ] Lambda error alarm created
- [ ] API Gateway 5xx error alarm created
- [ ] DynamoDB throttle alarm created
- [ ] SNS topic for alarm notifications

### X-Ray Tracing
- [ ] X-Ray enabled on Lambda
- [ ] Can view service map
- [ ] Can trace individual requests

## Security Verification

### IAM Permissions
- [ ] Lambda has minimal required permissions
- [ ] Lambda can write to DynamoDB
- [ ] Lambda can send emails via SES
- [ ] Lambda can write to CloudWatch Logs
- [ ] No overly permissive policies

### API Security
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled (100 req/s)
- [ ] Burst limit configured (200 req)
- [ ] HTTPS only (no HTTP)

### Data Security
- [ ] Input validation working
- [ ] No sensitive data in logs
- [ ] TTL configured for data cleanup
- [ ] Encryption at rest (DynamoDB default)
- [ ] Encryption in transit (HTTPS)

## Production Readiness

### SES Production Access
- [ ] Request sent for SES production access (if needed)
- [ ] Production access approved
- [ ] Can send to any email address
- [ ] Sending limits appropriate for expected volume

### Performance
- [ ] Lambda cold start time acceptable (<3s)
- [ ] Lambda warm execution time acceptable (<1s)
- [ ] API Gateway latency acceptable (<500ms)
- [ ] DynamoDB response time acceptable (<100ms)

### Scalability
- [ ] DynamoDB on-demand mode enabled
- [ ] Lambda concurrency limits reviewed
- [ ] API Gateway throttling configured
- [ ] Can handle expected traffic volume

### Cost Optimization
- [ ] Lambda memory size optimized (256MB)
- [ ] Lambda timeout appropriate (30s)
- [ ] DynamoDB on-demand for variable traffic
- [ ] CloudWatch log retention set (30 days)
- [ ] Estimated monthly cost acceptable

## Documentation

### Internal Documentation
- [ ] API endpoint documented
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Troubleshooting guide available

### User Documentation
- [ ] Contact form instructions (if needed)
- [ ] Privacy policy updated
- [ ] Terms of service updated

## Post-Deployment

### Immediate (First 24 Hours)
- [ ] Monitor CloudWatch logs for errors
- [ ] Check email delivery success rate
- [ ] Verify submissions are being stored
- [ ] Test from multiple devices/browsers
- [ ] Monitor API Gateway metrics

### Short-term (First Week)
- [ ] Review CloudWatch metrics
- [ ] Check for any error patterns
- [ ] Verify email deliverability
- [ ] Collect user feedback
- [ ] Optimize if needed

### Long-term (First Month)
- [ ] Review cost vs. estimates
- [ ] Analyze usage patterns
- [ ] Optimize Lambda memory/timeout
- [ ] Review and update documentation
- [ ] Plan for improvements

## Rollback Plan

### If Issues Occur
- [ ] Document the issue
- [ ] Check CloudWatch logs
- [ ] Verify SES email status
- [ ] Test API endpoint manually
- [ ] Check DynamoDB table

### Rollback Steps
1. [ ] Disable API Gateway endpoint (if critical)
2. [ ] Revert Lambda function to previous version
3. [ ] Check CloudFormation stack events
4. [ ] Restore from backup if needed
5. [ ] Document what went wrong

## Sign-off

### Deployment Team
- [ ] Backend developer sign-off
- [ ] Frontend developer sign-off
- [ ] DevOps engineer sign-off
- [ ] QA tester sign-off

### Stakeholders
- [ ] Product manager approval
- [ ] Security team approval
- [ ] Operations team notified

## Notes

**Deployment Date:** _______________

**Deployed By:** _______________

**API Endpoint:** _______________

**Issues Encountered:** 
_______________________________________________
_______________________________________________
_______________________________________________

**Resolution:** 
_______________________________________________
_______________________________________________
_______________________________________________

---

## Quick Reference

### Important URLs
- API Endpoint: `https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/contact`
- CloudWatch Logs: `/aws/lambda/aquachain-contact-form-handler`
- DynamoDB Table: `aquachain-contact-submissions`

### Important Commands
```bash
# View logs
aws logs tail /aws/lambda/aquachain-contact-form-handler --follow

# Query submissions
aws dynamodb scan --table-name aquachain-contact-submissions

# Check SES status
aws ses get-identity-verification-attributes --identities noreply@aquachain.io

# Test API
curl -X POST https://your-api-url/contact -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","message":"Test","inquiryType":"general"}'
```

### Support Contacts
- AWS Support: [AWS Console](https://console.aws.amazon.com/support)
- Documentation: `DOCS/CONTACT_FORM_SETUP.md`
- Emergency: Check CloudWatch logs first
