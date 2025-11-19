# Contact Form Setup Guide

Complete guide to set up and deploy the AquaChain contact form service.

## Overview

The contact form service provides:
- Backend API endpoint for form submissions
- DynamoDB storage for contact data
- Automated email notifications via AWS SES
- Frontend integration with React

## Quick Start

### 1. Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.11+
- Node.js 16+
- AWS CDK installed (`npm install -g aws-cdk`)

### 2. One-Command Setup

```bash
# Run the automated setup script
python scripts/setup-contact-service.py
```

This script will:
- Create DynamoDB table
- Verify SES email configuration
- Provide deployment instructions

### 3. Deploy Infrastructure

```bash
# Navigate to CDK directory
cd infrastructure/cdk

# Install dependencies
pip install -r requirements.txt

# Deploy the contact service stack
cdk deploy ContactServiceStack
```

### 4. Configure Frontend

After deployment, update your frontend environment:

```bash
# frontend/.env
REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod
```

Replace `YOUR_API_ID` with the actual API Gateway ID from the CDK output.

### 5. Verify SES Emails

**Important**: AWS SES requires email verification before sending emails.

```bash
# Verify sender email
aws ses verify-email-identity --email-address noreply@aquachain.io

# Verify admin email
aws ses verify-email-identity --email-address admin@aquachain.io
```

Check your email inbox for verification links and click them.

### 6. Test the Form

```bash
# Test the API endpoint
curl -X POST https://YOUR_API_URL/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "+1234567890",
    "message": "This is a test message for the contact form",
    "inquiryType": "general"
  }'
```

Expected response:
```json
{
  "message": "Contact form submitted successfully",
  "submissionId": "uuid-here"
}
```

## Detailed Setup

### AWS SES Configuration

#### Option 1: Sandbox Mode (Testing)

In sandbox mode, you can only send emails to verified addresses.

1. Verify both sender and recipient emails:
```bash
aws ses verify-email-identity --email-address noreply@aquachain.io
aws ses verify-email-identity --email-address admin@aquachain.io
aws ses verify-email-identity --email-address your-test-email@example.com
```

#### Option 2: Production Mode

To send emails to any address:

1. Request production access:
```bash
# Go to AWS Console → SES → Account Dashboard
# Click "Request production access"
# Fill out the form with your use case
```

2. Verify your domain (recommended):
```bash
# Add DNS records provided by SES
# Verify domain ownership
```

### DynamoDB Table Details

The contact submissions table includes:

**Primary Key:**
- `submissionId` (String) - UUID

**Global Secondary Indexes:**
- `email-createdAt-index` - Query by email
- `inquiryType-createdAt-index` - Query by inquiry type
- `status-createdAt-index` - Query by status

**TTL:**
- Automatic deletion after 1 year

### Lambda Function Configuration

**Runtime:** Python 3.11  
**Memory:** 256 MB  
**Timeout:** 30 seconds  
**Tracing:** AWS X-Ray enabled

**Environment Variables:**
```
CONTACT_TABLE_NAME=aquachain-contact-submissions
ADMIN_EMAIL=admin@aquachain.io
FROM_EMAIL=noreply@aquachain.io
AWS_REGION=us-east-1
```

**IAM Permissions:**
- DynamoDB: Read/Write on contact table
- SES: SendEmail, SendRawEmail
- CloudWatch: Logs and metrics
- X-Ray: Tracing

### API Gateway Configuration

**Endpoint:** POST /contact  
**CORS:** Enabled for all origins (configure for production)  
**Throttling:**
- Rate limit: 100 requests/second
- Burst limit: 200 requests

**Stage:** prod  
**Logging:** INFO level  
**Metrics:** Enabled

## Frontend Integration

### 1. Install Dependencies

The contact service is already integrated in the frontend. No additional dependencies needed.

### 2. Environment Configuration

Create or update `frontend/.env`:

```env
# API Configuration
REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod

# Optional: Enable debug logging
REACT_APP_DEBUG=false
```

### 3. Usage in Components

The ContactForm component is already configured:

```tsx
import ContactSection from './components/LandingPage/ContactSection';

// In your landing page
<ContactSection />
```

The form automatically:
- Validates input
- Submits to backend API
- Shows success/error messages
- Resets after successful submission

## Monitoring and Maintenance

### CloudWatch Dashboards

Monitor your contact form service:

1. **Lambda Metrics:**
   - Invocations
   - Errors
   - Duration
   - Throttles

2. **API Gateway Metrics:**
   - Request count
   - 4xx errors
   - 5xx errors
   - Latency

3. **DynamoDB Metrics:**
   - Read/Write capacity
   - Throttled requests
   - Item count

### CloudWatch Alarms

Set up alarms for:

```bash
# Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name contact-form-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold

# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name contact-form-api-errors \
  --alarm-description "Alert on API errors" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### Viewing Submissions

Query DynamoDB to view submissions:

```bash
# Get all submissions
aws dynamodb scan \
  --table-name aquachain-contact-submissions \
  --max-items 10

# Query by email
aws dynamodb query \
  --table-name aquachain-contact-submissions \
  --index-name email-createdAt-index \
  --key-condition-expression "email = :email" \
  --expression-attribute-values '{":email":{"S":"user@example.com"}}'

# Query by inquiry type
aws dynamodb query \
  --table-name aquachain-contact-submissions \
  --index-name inquiryType-createdAt-index \
  --key-condition-expression "inquiryType = :type" \
  --expression-attribute-values '{":type":{"S":"technician"}}'
```

## Security Best Practices

### 1. CORS Configuration

For production, restrict CORS to your domain:

```python
# In contact_service_stack.py
default_cors_preflight_options=apigateway.CorsOptions(
    allow_origins=['https://aquachain.io', 'https://www.aquachain.io'],
    allow_methods=['POST', 'OPTIONS'],
    allow_headers=['Content-Type']
)
```

### 2. Rate Limiting

Implement additional rate limiting:

```python
# Add API key requirement
api_key = api.add_api_key('ContactFormApiKey')
plan = api.add_usage_plan('ContactFormUsagePlan',
    throttle=apigateway.ThrottleSettings(
        rate_limit=10,
        burst_limit=20
    )
)
plan.add_api_key(api_key)
```

### 3. Input Validation

Server-side validation is already implemented:
- Email format validation
- Message length limits
- Inquiry type whitelist
- Input sanitization

### 4. Data Retention

TTL is configured for 1 year. Adjust if needed:

```python
# In contact_table.py
# Change TTL duration (in seconds)
ttl_seconds = 365 * 24 * 60 * 60  # 1 year
```

## Troubleshooting

### Issue: Emails Not Sending

**Symptoms:** Form submits successfully but no emails received

**Solutions:**
1. Check SES email verification:
```bash
aws ses get-identity-verification-attributes \
  --identities noreply@aquachain.io admin@aquachain.io
```

2. Check Lambda logs:
```bash
aws logs tail /aws/lambda/aquachain-contact-form-handler --follow
```

3. Verify SES sending limits:
```bash
aws ses get-send-quota
```

### Issue: CORS Errors

**Symptoms:** Browser console shows CORS errors

**Solutions:**
1. Verify API Gateway CORS configuration
2. Check allowed origins in CDK stack
3. Ensure OPTIONS method is configured
4. Clear browser cache

### Issue: Lambda Timeout

**Symptoms:** 504 Gateway Timeout errors

**Solutions:**
1. Increase Lambda timeout:
```bash
aws lambda update-function-configuration \
  --function-name aquachain-contact-form-handler \
  --timeout 60
```

2. Check DynamoDB table exists and is accessible
3. Verify network connectivity

### Issue: DynamoDB Throttling

**Symptoms:** 500 errors during high traffic

**Solutions:**
1. Table is already on-demand mode (auto-scaling)
2. Check for hot partitions
3. Review access patterns

## Cost Optimization

### Estimated Monthly Costs

Based on 1,000 submissions per month:

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 1,000 invocations × 30s | $0.20 |
| DynamoDB | On-demand, 1,000 writes | $0.25 |
| SES | 2,000 emails (user + admin) | $0.10 |
| API Gateway | 1,000 requests | $3.50 |
| **Total** | | **~$4.05** |

### Cost Reduction Tips

1. **Use SES in bulk:** Batch notifications if possible
2. **Optimize Lambda:** Reduce memory if not needed
3. **Cache responses:** Use API Gateway caching for GET requests
4. **Clean old data:** TTL automatically removes old submissions

## Updating the Service

### Update Lambda Code

```bash
# Make changes to lambda/contact_service/handler.py
cd infrastructure/cdk
cdk deploy ContactServiceStack
```

### Update DynamoDB Schema

```bash
# Add new GSI
python infrastructure/dynamodb/contact_table.py
```

### Update Frontend

```bash
# Make changes to frontend/src/services/contactService.ts
cd frontend
npm run build
```

## Support and Resources

- **Documentation:** `lambda/contact_service/README.md`
- **API Reference:** See Lambda handler docstrings
- **AWS SES Docs:** https://docs.aws.amazon.com/ses/
- **AWS Lambda Docs:** https://docs.aws.amazon.com/lambda/

## Next Steps

After setup:

1. ✅ Test form submission
2. ✅ Verify email delivery
3. ✅ Set up CloudWatch alarms
4. ✅ Configure production CORS
5. ✅ Request SES production access
6. ✅ Set up monitoring dashboard
7. ✅ Document admin procedures

## Admin Dashboard Integration

To view submissions in the admin dashboard, add a new component:

```tsx
// frontend/src/components/Admin/ContactSubmissions.tsx
// Query the DynamoDB table via API
// Display submissions in a table
// Allow status updates (pending → contacted → resolved)
```

This is optional but recommended for managing inquiries.
