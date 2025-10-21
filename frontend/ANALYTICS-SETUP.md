# Analytics Setup Guide

This guide explains how to configure analytics for the AquaChain frontend application.

## Quick Fix for Development

If you're getting AWS credential errors and just want to run the app locally, set this in your `.env.development`:

```bash
REACT_APP_ENABLE_ANALYTICS=false
```

This will disable analytics completely for development.

## Full Analytics Setup

### 1. AWS Pinpoint Setup

1. **Create AWS Pinpoint Application**:
   ```bash
   aws pinpoint create-app --create-application-request Name=AquaChain-Dev
   ```

2. **Get Application ID**:
   ```bash
   aws pinpoint get-apps
   ```

3. **Create IAM User for Analytics**:
   ```bash
   aws iam create-user --user-name aquachain-analytics-dev
   ```

4. **Attach Pinpoint Policy**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "mobiletargeting:PutEvents",
           "mobiletargeting:UpdateEndpoint",
           "mobiletargeting:GetEndpoint"
         ],
         "Resource": "arn:aws:mobiletargeting:*:*:apps/*"
       }
     ]
   }
   ```

5. **Create Access Keys**:
   ```bash
   aws iam create-access-key --user-name aquachain-analytics-dev
   ```

### 2. Environment Configuration

Update your `.env.development` file:

```bash
# Analytics Configuration
REACT_APP_PINPOINT_APPLICATION_ID=your-pinpoint-app-id
REACT_APP_AWS_ACCESS_KEY_ID=your-access-key-id
REACT_APP_AWS_SECRET_ACCESS_KEY=your-secret-access-key
REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX
REACT_APP_ENABLE_ANALYTICS=true
```

### 3. Google Analytics 4 Setup

1. **Create GA4 Property**:
   - Go to [Google Analytics](https://analytics.google.com)
   - Create new property for AquaChain
   - Get Measurement ID (starts with G-)

2. **Add to Environment**:
   ```bash
   REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX
   ```

## Security Best Practices

### For Production

**Never put AWS credentials in environment variables for production!**

Instead, use:

1. **AWS Cognito Identity Pools** (Recommended):
   ```typescript
   // Use temporary credentials via Cognito
   import { CognitoIdentityClient } from "@aws-sdk/client-cognito-identity";
   import { fromCognitoIdentityPool } from "@aws-sdk/credential-provider-cognito-identity";
   
   const credentials = fromCognitoIdentityPool({
     client: new CognitoIdentityClient({ region: "us-east-1" }),
     identityPoolId: "us-east-1:your-identity-pool-id"
   });
   ```

2. **IAM Roles for Web Identity**:
   - Configure OIDC provider
   - Use temporary credentials
   - No long-term keys in frontend

### For Development

Current setup with access keys is acceptable for local development only.

## Troubleshooting

### Common Issues

1. **"Credential is missing" Error**:
   - Check `.env.development` has correct AWS credentials
   - Verify credentials have Pinpoint permissions
   - Set `REACT_APP_ENABLE_ANALYTICS=false` to disable

2. **Pinpoint Application Not Found**:
   - Verify `REACT_APP_PINPOINT_APPLICATION_ID` is correct
   - Check AWS region matches `REACT_APP_AWS_REGION`

3. **CORS Errors**:
   - Pinpoint doesn't have CORS issues (server-side service)
   - Check if using correct region

### Debug Mode

Enable debug logging:

```bash
NODE_ENV=development
```

This will log all analytics events to console.

## Testing Analytics

### Manual Testing

1. **Open Browser DevTools**
2. **Go to Console tab**
3. **Look for analytics logs**:
   ```
   Analytics service initialized with Pinpoint
   Event tracked: { eventType: 'page_view', ... }
   Flushed 1 events to Pinpoint
   ```

### Automated Testing

Run analytics tests:

```bash
npm test -- --testNamePattern="analytics"
```

## Mock Mode

When credentials are missing, the service runs in mock mode:
- Events are logged to console (debug mode)
- No actual data sent to AWS
- App continues to function normally

This allows development without AWS setup.