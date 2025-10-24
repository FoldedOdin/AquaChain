# AquaChain AWS Infrastructure Setup Guide

This guide helps you connect your AquaChain frontend to the deployed AWS infrastructure instead of the local development server.

## Prerequisites

1. **AWS CLI installed and configured**

   ```bash
   # Install AWS CLI
   # Windows: Download from https://aws.amazon.com/cli/
   # macOS: brew install awscli
   # Linux: sudo apt install awscli

   # Configure credentials
   aws configure
   ```

2. **CDK stacks deployed**
   - Your AquaChain CDK stacks should be deployed to AWS
   - Stack names should follow the pattern: `AquaChain-{Component}-{Environment}`

## Quick Setup

### Option 1: Automatic Configuration (Recommended)

```bash
# 1. Get your deployed AWS endpoints
npm run get-aws-config dev  # or 'prod' for production

# 2. Switch to AWS mode
npm run switch-to-aws

# 3. Start the app
npm start
```

### Option 2: Manual Configuration

1. **Get your AWS resource IDs from the AWS Console:**
   - Go to CloudFormation → Find your AquaChain stacks → Outputs tab
   - Copy the values for:
     - RestAPIEndpoint
     - WebSocketAPIEndpoint
     - UserPoolId
     - UserPoolClientId

2. **Update `.env.production`:**

   ```bash
   REACT_APP_AWS_REGION=us-east-1
   REACT_APP_USER_POOL_ID=us-east-1_XXXXXXXXX
   REACT_APP_USER_POOL_CLIENT_ID=your_actual_client_id
   REACT_APP_IDENTITY_POOL_ID=us-east-1:your-identity-pool-id
   REACT_APP_API_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com/dev
   REACT_APP_WEBSOCKET_ENDPOINT=wss://your-ws-api-id.execute-api.us-east-1.amazonaws.com/dev
   ```

3. **Switch to AWS mode:**
   ```bash
   npm run switch-to-aws
   npm start
   ```

## Available Scripts

| Script                         | Description                                |
| ------------------------------ | ------------------------------------------ |
| `npm run get-aws-config [env]` | Fetch deployed AWS endpoints automatically |
| `npm run switch-to-aws`        | Switch to AWS infrastructure mode          |
| `npm run switch-to-dev`        | Switch back to local development mode      |
| `npm run start:aws`            | Switch to AWS and start the app            |

## Authentication Differences

### Development Mode (Local Dev Server)

- Uses in-memory user storage
- Auto-creates test accounts
- Email verification simulated (2 seconds)
- Test credentials work immediately

### AWS Mode (Production Infrastructure)

- Uses AWS Cognito for authentication
- Real email verification required
- Users must be created through:
  - Cognito console
  - Signup flow (if enabled)
  - Admin invitation

## Creating Users in AWS Cognito

### Option 1: AWS Console

1. Go to AWS Console → Cognito → User Pools
2. Select your AquaChain user pool
3. Users tab → Create user
4. Set temporary password and require password change

### Option 2: AWS CLI

```bash
# Create a user
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username consumer@test.com \
  --user-attributes Name=email,Value=consumer@test.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username consumer@test.com \
  --password Password123! \
  --permanent
```

### Option 3: Signup Flow

If your Cognito is configured to allow self-registration:

1. Use the signup form in your app
2. Check email for verification code
3. Complete verification process

## User Roles and Groups

The system supports three user roles:

- **Consumer**: Monitor water quality data
- **Technician**: Service devices and handle requests
- **Admin**: Full system access

### Assigning Roles in Cognito

```bash
# Add user to a group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username consumer@test.com \
  --group-name consumers
```

## API Endpoints

When connected to AWS, your app will use:

### REST API

- **Base URL**: `https://your-api-id.execute-api.region.amazonaws.com/stage`
- **Authentication**: Cognito JWT tokens
- **Endpoints**:
  - `GET /api/v1/readings/{deviceId}` - Get device readings
  - `GET /api/v1/readings/{deviceId}/history` - Get historical data
  - `POST /api/v1/service-requests` - Create service request
  - `GET /api/v1/audit/hash-chain` - Get audit trail

### WebSocket API

- **URL**: `wss://your-ws-api-id.execute-api.region.amazonaws.com/stage`
- **Real-time updates**: Device status, alerts, notifications

## Troubleshooting

### Common Issues

1. **"User does not exist" error**
   - Create user in Cognito console
   - Verify email address is correct
   - Check user pool ID in configuration

2. **"Access denied" errors**
   - Verify user is in correct Cognito group
   - Check API Gateway authorizer configuration
   - Ensure JWT token is valid

3. **CORS errors**
   - Verify your domain is in Cognito callback URLs
   - Check API Gateway CORS configuration
   - Ensure proper headers are sent

4. **Configuration not loading**
   - Restart React app after changing .env files
   - Check .env.local takes precedence over .env.development
   - Verify environment variables start with REACT*APP*

### Debugging Steps

1. **Check current configuration:**

   ```javascript
   // In browser console
   console.log('API Endpoint:', process.env.REACT_APP_API_ENDPOINT);
   console.log('User Pool:', process.env.REACT_APP_USER_POOL_ID);
   ```

2. **Verify AWS resources:**

   ```bash
   # Check if stacks exist
   aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

   # Get stack outputs
   aws cloudformation describe-stacks --stack-name AquaChain-API-dev
   ```

3. **Test API connectivity:**
   ```bash
   # Test API endpoint
   curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/api/v1/health
   ```

## Switching Between Modes

### Development Mode

```bash
npm run switch-to-dev
npm run start:full  # Starts both dev server and React app
```

### AWS Mode

```bash
npm run switch-to-aws
npm start  # Uses AWS infrastructure
```

## Security Considerations

### Development Mode

- Uses test reCAPTCHA keys
- No real email verification
- In-memory data storage
- Suitable for development only

### AWS Mode

- Production reCAPTCHA keys required
- Real email verification via SES
- Encrypted data storage in DynamoDB/S3
- WAF protection enabled
- Audit trail and compliance features

## Next Steps

1. **Deploy your CDK stacks** if not already done
2. **Run the configuration script** to get endpoints
3. **Create test users** in Cognito
4. **Test the authentication flow**
5. **Configure additional services** (Pinpoint, reCAPTCHA, etc.)

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your AWS permissions
3. Review CloudWatch logs for API errors
4. Check Cognito user pool configuration

Your AquaChain app is now ready to use the full AWS infrastructure! 🚀
