# AquaChain Contact Form Service

Complete serverless contact form implementation with backend API, database storage, and email notifications.

## 🎯 Features

✅ **Backend API Endpoint**
- AWS Lambda function with Python 3.11
- API Gateway REST endpoint
- Form validation and error handling
- CORS support for frontend integration

✅ **Email Service Integration**
- AWS SES for email delivery
- User confirmation emails (HTML + text)
- Admin notification emails
- Automatic retry on failure

✅ **Database Storage**
- DynamoDB table with on-demand billing
- Global Secondary Indexes for querying
- TTL for automatic cleanup (1 year)
- Admin dashboard for viewing submissions

## 🚀 Quick Start

### Prerequisites

- AWS Account
- AWS CLI configured
- Python 3.11+
- Node.js 16+
- AWS CDK (`npm install -g aws-cdk`)

### Deploy in 5 Minutes

```bash
# 1. Run automated setup
python scripts/setup-contact-service.py

# 2. Verify SES emails (check your inbox)
aws ses verify-email-identity --email-address noreply@aquachain.io
aws ses verify-email-identity --email-address admin@aquachain.io

# 3. Deploy infrastructure
cd infrastructure/cdk
cdk deploy ContactServiceStack

# 4. Configure frontend
echo "REACT_APP_API_URL=<YOUR_API_URL>" >> frontend/.env

# 5. Test
curl -X POST <YOUR_API_URL>/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","message":"Test","inquiryType":"general"}'
```

Or use the automated deployment script:

```bash
chmod +x scripts/deploy-contact-service.sh
./scripts/deploy-contact-service.sh
```

## 📁 Project Structure

```
lambda/contact_service/
├── handler.py              # Lambda function
├── requirements.txt        # Python dependencies
├── README.md              # API documentation
└── __init__.py            # Package info

infrastructure/
├── dynamodb/
│   └── contact_table.py   # DynamoDB table definition
└── cdk/stacks/
    └── contact_service_stack.py  # CDK infrastructure

frontend/src/
├── services/
│   └── contactService.ts  # API client
└── components/
    ├── LandingPage/
    │   ├── ContactForm.tsx       # Form component
    │   └── ContactSection.tsx    # Section wrapper
    └── Admin/
        └── ContactSubmissions.tsx # Admin dashboard

scripts/
├── setup-contact-service.py      # Setup automation
└── deploy-contact-service.sh     # Deployment script

DOCS/
├── CONTACT_FORM_SETUP.md         # Complete setup guide
├── CONTACT_FORM_QUICK_START.md   # Quick start guide
└── CONTACT_FORM_IMPLEMENTATION_SUMMARY.md  # Implementation details
```

## 🏗️ Architecture

```
┌──────────────┐
│   Frontend   │  React Contact Form
│  (React.js)  │
└──────┬───────┘
       │ HTTPS POST
       ▼
┌──────────────┐
│ API Gateway  │  REST API Endpoint
│ POST /contact│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Lambda    │  Python 3.11 Handler
│   Function   │  - Validate input
│              │  - Store in DB
│              │  - Send emails
└──┬────────┬──┘
   │        │
   ▼        ▼
┌─────┐  ┌─────┐
│ DDB │  │ SES │  Storage & Email
└─────┘  └─────┘
```

## 📊 API Specification

### POST /contact

Submit a contact form.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "message": "I'm interested in becoming a technician",
  "inquiryType": "technician"
}
```

**Response (Success):**
```json
{
  "message": "Contact form submitted successfully",
  "submissionId": "uuid"
}
```

**Inquiry Types:**
- `technician` - Technician application
- `general` - General inquiry
- `support` - Technical support

## 💾 Database Schema

### Contact Submissions Table

**Table Name:** `aquachain-contact-submissions`

**Primary Key:**
- `submissionId` (String) - UUID

**Attributes:**
- `name` - User's full name
- `email` - User's email address
- `phone` - Phone number (optional)
- `message` - User's message
- `inquiryType` - Type of inquiry
- `status` - pending | contacted | resolved
- `createdAt` - Submission timestamp
- `updatedAt` - Last update timestamp
- `source` - web_form
- `ttl` - Auto-deletion timestamp

**Global Secondary Indexes:**
1. `email-createdAt-index` - Query by email
2. `inquiryType-createdAt-index` - Query by type
3. `status-createdAt-index` - Query by status

## 📧 Email Templates

### User Confirmation
- Personalized greeting
- Submission details
- Expected response time
- Contact information

### Admin Notification
- Contact details
- Full message
- Inquiry type
- Submission metadata

## 🔒 Security

- ✅ Server-side input validation
- ✅ HTTPS only
- ✅ CORS configuration
- ✅ Input sanitization
- ✅ Rate limiting (100 req/s)
- ✅ IAM least privilege
- ✅ No sensitive data in logs

## 📈 Monitoring

### CloudWatch Metrics
- Lambda invocations, errors, duration
- API Gateway requests, errors, latency
- DynamoDB read/write capacity

### CloudWatch Logs
- Lambda execution logs
- API Gateway access logs
- Email delivery status

### X-Ray Tracing
- End-to-end request tracing
- Performance analysis
- Error tracking

## 💰 Cost Estimate

**~$4.55/month** for 1,000 submissions:

| Service | Cost |
|---------|------|
| Lambda | $0.20 |
| DynamoDB | $0.25 |
| SES | $0.10 |
| API Gateway | $3.50 |
| CloudWatch | $0.50 |

## 🧪 Testing

### Test API Endpoint

```bash
curl -X POST https://your-api-url/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "+1234567890",
    "message": "This is a test message",
    "inquiryType": "general"
  }'
```

### View Submissions

```bash
# Query DynamoDB
aws dynamodb scan \
  --table-name aquachain-contact-submissions \
  --max-items 10
```

### Check Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/aquachain-contact-form-handler --follow
```

## 🐛 Troubleshooting

### Emails Not Sending?

```bash
# Check SES verification
aws ses get-identity-verification-attributes \
  --identities noreply@aquachain.io admin@aquachain.io
```

### CORS Errors?

Update allowed origins in `contact_service_stack.py`

### Lambda Timeout?

```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name aquachain-contact-form-handler \
  --timeout 60
```

## 📚 Documentation

- **Quick Start:** `DOCS/CONTACT_FORM_QUICK_START.md`
- **Full Setup:** `DOCS/CONTACT_FORM_SETUP.md`
- **API Docs:** `lambda/contact_service/README.md`
- **Implementation:** `DOCS/CONTACT_FORM_IMPLEMENTATION_SUMMARY.md`

## 🎯 Next Steps

### Immediate
1. ✅ Deploy infrastructure
2. ✅ Verify SES emails
3. ✅ Test form submission

### Short-term
1. Set up CloudWatch alarms
2. Request SES production access
3. Configure production CORS
4. Add to admin dashboard

### Long-term
1. Add spam protection
2. Implement per-IP rate limiting
3. Add file attachments
4. Create custom email templates

## 🤝 Contributing

This is part of the AquaChain project. For issues or improvements:

1. Check CloudWatch logs
2. Review documentation
3. Test locally first
4. Update tests

## 📞 Support

- **Documentation:** See files listed above
- **AWS Issues:** Check CloudWatch logs
- **Code Issues:** Review Lambda handler
- **Email Issues:** Check SES console

## 📝 License

Part of AquaChain Technologies project.

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** November 19, 2025
