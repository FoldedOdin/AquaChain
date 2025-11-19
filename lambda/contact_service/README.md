# Contact Form Service

Complete backend service for handling contact form submissions with email notifications and database storage.

## Features

- ✅ **Form Validation**: Server-side validation of all form fields
- ✅ **Database Storage**: Stores submissions in DynamoDB with TTL
- ✅ **Email Notifications**: Sends confirmation to users and notifications to admins
- ✅ **CORS Support**: Configured for frontend integration
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Security**: Input sanitization and validation

## Architecture

```
Frontend Form → API Gateway → Lambda Function → DynamoDB
                                    ↓
                                AWS SES (Email)
```

## Components

### 1. Lambda Function (`handler.py`)
- Handles POST requests to `/contact` endpoint
- Validates form data
- Stores submissions in DynamoDB
- Sends email notifications via SES

### 2. DynamoDB Table (`aquachain-contact-submissions`)
- **Partition Key**: `submissionId` (UUID)
- **GSIs**:
  - `email-createdAt-index`: Query by email
  - `inquiryType-createdAt-index`: Query by inquiry type
  - `status-createdAt-index`: Query by status
- **TTL**: Automatic cleanup after 1 year

### 3. Email Service (AWS SES)
- Sends confirmation email to user
- Sends notification email to admin
- HTML and plain text formats

## Deployment

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS SES** configured and verified
3. **Python 3.11** or later
4. **AWS CDK** installed

### Step 1: Verify SES Email Addresses

```bash
# Verify sender email addresses in AWS SES
aws ses verify-email-identity --email-address noreply@aquachain.io
aws ses verify-email-identity --email-address admin@aquachain.io
```

Check your email inbox for verification links.

### Step 2: Create DynamoDB Table

```bash
# Run the setup script
python scripts/setup-contact-service.py
```

Or manually:

```bash
python infrastructure/dynamodb/contact_table.py
```

### Step 3: Deploy Lambda Function

Using CDK:

```bash
cd infrastructure/cdk
cdk deploy ContactServiceStack
```

Or using AWS CLI:

```bash
# Package Lambda function
cd lambda/contact_service
zip -r function.zip handler.py

# Create Lambda function
aws lambda create-function \
  --function-name aquachain-contact-form-handler \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    CONTACT_TABLE_NAME=aquachain-contact-submissions,
    ADMIN_EMAIL=admin@aquachain.io,
    FROM_EMAIL=noreply@aquachain.io
  }"
```

### Step 4: Configure API Gateway

The CDK stack automatically creates an API Gateway endpoint. After deployment, note the API URL from the stack outputs.

### Step 5: Update Frontend Configuration

Add the API URL to your frontend `.env` file:

```bash
# frontend/.env
REACT_APP_API_URL=https://your-api-gateway-id.execute-api.us-east-1.amazonaws.com/prod
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CONTACT_TABLE_NAME` | DynamoDB table name | `aquachain-contact-submissions` |
| `ADMIN_EMAIL` | Email to receive notifications | `admin@aquachain.io` |
| `FROM_EMAIL` | Sender email address | `noreply@aquachain.io` |
| `AWS_REGION` | AWS region | `us-east-1` |

## API Endpoint

### POST /contact

Submit a contact form.

**Request Body:**

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
  "submissionId": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response (Error):**

```json
{
  "error": "Missing required field: email"
}
```

## Inquiry Types

- `technician`: Technician application inquiries
- `general`: General questions about AquaChain
- `support`: Technical support requests

## Email Templates

### User Confirmation Email

Sent to the user who submitted the form:
- Confirms receipt of inquiry
- Includes submission details
- Provides submission ID for reference

### Admin Notification Email

Sent to admin team:
- Contains all form details
- Includes contact information
- Shows inquiry type and message

## Database Schema

### Contact Submission Item

```json
{
  "submissionId": "uuid",
  "name": "string",
  "email": "string",
  "phone": "string (optional)",
  "message": "string",
  "inquiryType": "technician|general|support",
  "status": "pending|contacted|resolved",
  "createdAt": "ISO 8601 timestamp",
  "updatedAt": "ISO 8601 timestamp",
  "source": "web_form",
  "ttl": "unix timestamp (1 year from creation)"
}
```

## Monitoring

### CloudWatch Metrics

- Lambda invocations
- Lambda errors
- Lambda duration
- API Gateway requests
- API Gateway 4xx/5xx errors

### CloudWatch Logs

- Lambda execution logs
- API Gateway access logs
- Email delivery status

## Security

### Input Validation

- Server-side validation of all fields
- Email format validation
- Message length validation
- Inquiry type whitelist

### Data Protection

- HTTPS only
- CORS configured for specific origins
- Input sanitization
- No sensitive data in logs

### Rate Limiting

- API Gateway throttling: 100 requests/second
- Burst limit: 200 requests

## Testing

### Local Testing

```bash
# Test Lambda function locally
python -c "
import json
from handler import lambda_handler

event = {
    'httpMethod': 'POST',
    'body': json.dumps({
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'message': 'This is a test message',
        'inquiryType': 'general'
    })
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

### API Testing

```bash
# Test API endpoint
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

## Troubleshooting

### Email Not Sending

1. Check SES email verification status
2. Verify Lambda has SES permissions
3. Check CloudWatch logs for errors
4. Ensure you're not in SES sandbox mode

### Lambda Timeout

1. Increase Lambda timeout (current: 30s)
2. Check DynamoDB table exists
3. Verify network connectivity

### CORS Errors

1. Verify API Gateway CORS configuration
2. Check allowed origins
3. Ensure preflight OPTIONS requests work

## Cost Estimation

### Monthly Costs (1000 submissions)

- **Lambda**: ~$0.20
- **DynamoDB**: ~$0.25 (on-demand)
- **SES**: ~$0.10 (2000 emails)
- **API Gateway**: ~$3.50
- **Total**: ~$4.05/month

## Support

For issues or questions:
- Email: support@aquachain.io
- Documentation: https://docs.aquachain.io
- GitHub Issues: https://github.com/aquachain/issues
