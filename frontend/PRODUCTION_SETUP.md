# AquaChain Production Setup Guide

## Overview

This guide covers setting up AquaChain for production deployment with real AWS services, authentication, and analytics.

## Development vs Production

### Development (Current Setup)
- ✅ Mock authentication with in-memory storage
- ✅ Auto email verification (2 seconds)
- ✅ Local development server on port 3002
- ✅ Test reCAPTCHA keys
- ✅ Mock analytics service
- ✅ No real AWS credentials required

### Production Requirements
- 🔧 Real AWS Cognito User Pool
- 🔧 Real email service (AWS SES)
- 🔧 Production reCAPTCHA keys
- 🔧 Real AWS Pinpoint/GA4 analytics
- 🔧 Production backend server
- 🔧 HTTPS and security headers

## Production Environment Setup

### 1. AWS Cognito Configuration

#### Create User Pool
```bash
# Using AWS CLI
aws cognito-idp create-user-pool \
  --pool-name "AquaChain-Users" \
  --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}" \
  --auto-verified-attributes email \
  --email-configuration "SourceArn=arn:aws:ses:region:account:identity/noreply@yourdomain.com"
```

#### Create User Pool Client
```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id us-east-1_XXXXXXXXX \
  --client-name "AquaChain-Web-Client" \
  --generate-secret false \
  --explicit-auth-flows ADMIN_NO_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH
```

### 2. Environment Variables

#### Production (.env.production)
```bash
# AWS Configuration
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=us-east-1_XXXXXXXXX
REACT_APP_USER_POOL_CLIENT_ID=your_client_id
REACT_APP_IDENTITY_POOL_ID=us-east-1:your-identity-pool-id

# API Configuration
REACT_APP_API_ENDPOINT=https://api.yourdomain.com
REACT_APP_WEBSOCKET_ENDPOINT=wss://websocket.yourdomain.com

# Analytics Configuration
REACT_APP_PINPOINT_APPLICATION_ID=your-pinpoint-app-id
REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX

# Security Configuration
REACT_APP_RECAPTCHA_SITE_KEY=your_production_recaptcha_key

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_MOCK_DATA=false
```

### 3. Backend Server Setup

#### Production Backend Structure
```
backend/
├── server.js              # Main server file
├── routes/
│   ├── auth.js            # Authentication routes
│   ├── analytics.js       # Analytics endpoints
│   └── rum.js             # RUM data collection
├── middleware/
│   ├── auth.js            # JWT verification
│   ├── cors.js            # CORS configuration
│   └── security.js        # Security headers
├── services/
│   ├── cognito.js         # AWS Cognito integration
│   ├── pinpoint.js        # Analytics service
│   └── ses.js             # Email service
└── config/
    ├── aws.js             # AWS configuration
    └── database.js        # Database connection
```

#### Sample Production Server (server.js)
```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { CognitoIdentityProviderClient } = require('@aws-sdk/client-cognito-identity-provider');

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'nonce-{nonce}'", "https://www.google.com/recaptcha/"],
      styleSrc: ["'self'", "'nonce-{nonce}'", "https://fonts.googleapis.com"],
      imgSrc: ["'self'", "data:", "https://*.amazonaws.com"],
      connectSrc: ["'self'", "https://*.amazonaws.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      frameSrc: ["https://www.google.com/recaptcha/"],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
      frameAncestors: ["'none'"]
    }
  }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// CORS configuration
app.use(cors({
  origin: process.env.FRONTEND_URL || 'https://yourdomain.com',
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/analytics', require('./routes/analytics'));
app.use('/api/rum', require('./routes/rum'));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    service: 'aquachain-production-server'
  });
});

app.listen(PORT, () => {
  console.log(`AquaChain Production Server running on port ${PORT}`);
});
```

### 4. AWS Services Configuration

#### Pinpoint Analytics
```javascript
// services/pinpoint.js
const { PinpointClient, PutEventsCommand } = require('@aws-sdk/client-pinpoint');

const pinpointClient = new PinpointClient({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

async function trackEvent(applicationId, event) {
  const command = new PutEventsCommand({
    ApplicationId: applicationId,
    EventsRequest: {
      BatchItem: {
        [event.userId]: {
          Endpoint: {},
          Events: {
            [event.eventId]: {
              EventType: event.eventType,
              Timestamp: event.timestamp,
              Attributes: event.attributes,
              Metrics: event.metrics
            }
          }
        }
      }
    }
  });

  return await pinpointClient.send(command);
}

module.exports = { trackEvent };
```

#### SES Email Service
```javascript
// services/ses.js
const { SESClient, SendEmailCommand } = require('@aws-sdk/client-ses');

const sesClient = new SESClient({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

async function sendVerificationEmail(email, verificationLink) {
  const command = new SendEmailCommand({
    Source: 'noreply@yourdomain.com',
    Destination: {
      ToAddresses: [email]
    },
    Message: {
      Subject: {
        Data: 'Verify your AquaChain account'
      },
      Body: {
        Html: {
          Data: `
            <h2>Welcome to AquaChain!</h2>
            <p>Please click the link below to verify your email address:</p>
            <a href="${verificationLink}">Verify Email</a>
            <p>If you didn't create an account, please ignore this email.</p>
          `
        }
      }
    }
  });

  return await sesClient.send(command);
}

module.exports = { sendVerificationEmail };
```

### 5. Deployment Options

#### Option A: AWS Amplify
```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting

# Deploy
amplify publish
```

#### Option B: Docker Deployment
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000

# Start the app
CMD ["npm", "start"]
```

#### Option C: Traditional Server
```bash
# Build the app
npm run build

# Copy build files to web server
cp -r build/* /var/www/html/

# Configure nginx/apache to serve the files
```

### 6. Security Checklist

#### Frontend Security
- ✅ Content Security Policy headers
- ✅ HTTPS enforcement
- ✅ Input sanitization
- ✅ XSS protection
- ✅ CSRF tokens
- ✅ Rate limiting

#### Backend Security
- ✅ JWT token validation
- ✅ API rate limiting
- ✅ Input validation
- ✅ SQL injection prevention
- ✅ CORS configuration
- ✅ Security headers

### 7. Monitoring and Analytics

#### CloudWatch Integration
```javascript
// Add to your backend
const { CloudWatchClient, PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');

async function logMetric(metricName, value, unit = 'Count') {
  const command = new PutMetricDataCommand({
    Namespace: 'AquaChain/Application',
    MetricData: [{
      MetricName: metricName,
      Value: value,
      Unit: unit,
      Timestamp: new Date()
    }]
  });

  await cloudWatchClient.send(command);
}
```

### 8. Database Integration

#### RDS Setup (Optional)
```javascript
// config/database.js
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  ssl: process.env.NODE_ENV === 'production'
});

module.exports = pool;
```

## Migration from Development

### 1. Update Environment Variables
Replace development values with production values in `.env.production`

### 2. Update AuthService
The `authService.ts` already has conditional logic for development vs production:
```typescript
// In development, use the dev server
if (process.env.NODE_ENV === 'development') {
  // Use development server
} else {
  // Use AWS Amplify for production
}
```

### 3. Build and Deploy
```bash
# Build for production
npm run build

# Deploy to your chosen platform
```

## Testing Production Setup

### 1. Local Production Test
```bash
# Build the app
npm run build

# Serve the built files
npx serve -s build -l 3000
```

### 2. End-to-End Testing
- Test signup with real email
- Verify email verification works
- Test login flow
- Verify analytics tracking
- Test all user flows

## Support and Troubleshooting

### Common Issues
1. **CORS errors**: Check backend CORS configuration
2. **Authentication failures**: Verify Cognito configuration
3. **Email not sending**: Check SES configuration and domain verification
4. **Analytics not tracking**: Verify Pinpoint/GA4 setup

### Debug Mode
Enable debug logging in production (temporarily):
```bash
REACT_APP_DEBUG_MODE=true
```

This comprehensive guide covers the complete production setup for AquaChain, ensuring a smooth transition from development to production deployment.