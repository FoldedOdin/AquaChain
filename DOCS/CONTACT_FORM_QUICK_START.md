# Contact Form - Quick Start Guide

Get the contact form up and running in 5 minutes.

## 🚀 Quick Deploy

### Step 1: Setup (2 minutes)

```bash
# Run automated setup
python scripts/setup-contact-service.py
```

### Step 2: Verify Emails (1 minute)

```bash
# Verify sender emails in AWS SES
aws ses verify-email-identity --email-address noreply@aquachain.io
aws ses verify-email-identity --email-address admin@aquachain.io
```

**Check your email** and click the verification links.

### Step 3: Deploy (2 minutes)

```bash
# Deploy infrastructure
cd infrastructure/cdk
cdk deploy ContactServiceStack
```

**Copy the API URL** from the output.

### Step 4: Configure Frontend (30 seconds)

```bash
# Add to frontend/.env
echo "REACT_APP_API_URL=YOUR_API_URL_HERE" >> frontend/.env
```

### Step 5: Test (30 seconds)

```bash
# Test the endpoint
curl -X POST YOUR_API_URL/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "Test message",
    "inquiryType": "general"
  }'
```

## ✅ What You Get

- ✅ **Backend API** - Serverless Lambda function
- ✅ **Database** - DynamoDB table with auto-cleanup
- ✅ **Email Service** - Automated notifications via SES
- ✅ **Frontend Integration** - React form component
- ✅ **Admin Dashboard** - View and manage submissions

## 📁 Files Created

```
lambda/contact_service/
├── handler.py              # Lambda function
├── requirements.txt        # Dependencies
└── README.md              # Detailed docs

infrastructure/
├── dynamodb/contact_table.py    # Table definition
└── cdk/stacks/contact_service_stack.py  # CDK stack

frontend/src/
├── services/contactService.ts   # API client
└── components/
    ├── LandingPage/ContactForm.tsx      # Form component
    └── Admin/ContactSubmissions.tsx     # Admin view

scripts/
└── setup-contact-service.py    # Setup automation

DOCS/
├── CONTACT_FORM_SETUP.md       # Full guide
└── CONTACT_FORM_QUICK_START.md # This file
```

## 🔧 Configuration

### Environment Variables

**Lambda Function:**
```
CONTACT_TABLE_NAME=aquachain-contact-submissions
ADMIN_EMAIL=admin@aquachain.io
FROM_EMAIL=noreply@aquachain.io
AWS_REGION=us-east-1
```

**Frontend:**
```
REACT_APP_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

## 📊 Monitoring

### View Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/aquachain-contact-form-handler --follow

# API Gateway logs
aws logs tail /aws/apigateway/ContactFormApi --follow
```

### View Submissions

```bash
# Query DynamoDB
aws dynamodb scan --table-name aquachain-contact-submissions --max-items 10
```

## 🐛 Troubleshooting

### Emails Not Sending?

```bash
# Check SES verification
aws ses get-identity-verification-attributes \
  --identities noreply@aquachain.io admin@aquachain.io
```

### CORS Errors?

Update API Gateway CORS in `contact_service_stack.py`:
```python
allow_origins=['https://yourdomain.com']
```

### Lambda Timeout?

```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name aquachain-contact-form-handler \
  --timeout 60
```

## 💰 Cost

**~$4/month** for 1,000 submissions:
- Lambda: $0.20
- DynamoDB: $0.25
- SES: $0.10
- API Gateway: $3.50

## 📚 Full Documentation

See `DOCS/CONTACT_FORM_SETUP.md` for:
- Detailed setup instructions
- Security best practices
- Advanced configuration
- Monitoring and alerts
- Cost optimization

## 🎯 Next Steps

1. ✅ Test form submission
2. ✅ Verify email delivery
3. ✅ Add to admin dashboard
4. ✅ Set up CloudWatch alarms
5. ✅ Request SES production access

## 📞 Support

- **Docs:** `lambda/contact_service/README.md`
- **Issues:** Check CloudWatch logs
- **Email:** support@aquachain.io
