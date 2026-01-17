# OTP Configuration Guide

## Overview

The authentication system supports two modes:

1. **Local Development Mode** - Uses hardcoded OTP (no AWS Cognito needed)
2. **AWS Production Mode** - Uses real Cognito OTP via email

This is controlled by environment variables.

---

## Local Development Mode

### Configuration

**File:** `frontend/.env.local`

```env
# Enable mock authentication
REACT_APP_USE_MOCK_AUTH=true

# Hardcoded OTP code for local development
REACT_APP_LOCAL_OTP_CODE=123456
```

### How It Works

1. User signs up with email/password
2. Verification modal appears
3. **Instead of sending email**, system shows: "Use code 123456"
4. User enters `123456`
5. Account is verified ✅

### Benefits

- ✅ No AWS Cognito needed
- ✅ No email service required
- ✅ Instant verification
- ✅ Works offline
- ✅ Zero cost

### Usage

```bash
cd frontend
npm start

# Sign up with any email
# When prompted, enter: 123456
```

---

## AWS Production Mode

### Configuration

**File:** `frontend/.env.production`

```env
# Disable mock authentication
REACT_APP_USE_MOCK_AUTH=false

# AWS Cognito configuration
REACT_APP_AWS_REGION=ap-south-1
REACT_APP_USER_POOL_ID=ap-south-1_YourPoolId
REACT_APP_USER_POOL_CLIENT_ID=your_client_id
```

### How It Works

1. User signs up with email/password
2. AWS Cognito sends real OTP via email
3. User checks email for 6-digit code
4. User enters code from email
5. Account is verified ✅

### Benefits

- ✅ Real email verification
- ✅ Secure OTP generation
- ✅ Production-ready
- ✅ Prevents fake signups

### Usage

```bash
cd frontend
npm run build
# Deploy to AWS

# Sign up with real email
# Check email for OTP code
```

---

## Environment Files

### `.env.local` (Local Development)

```env
# Local mode - hardcoded OTP
REACT_APP_USE_MOCK_AUTH=true
REACT_APP_LOCAL_OTP_CODE=123456
REACT_APP_API_ENDPOINT=http://localhost:3001
REACT_APP_ENABLE_ANALYTICS=false
```

**When to use:** Daily development, testing, no AWS needed

### `.env.production` (AWS Deployment)

```env
# AWS mode - real Cognito OTP
REACT_APP_USE_MOCK_AUTH=false
REACT_APP_AWS_REGION=ap-south-1
REACT_APP_USER_POOL_ID=ap-south-1_YourPoolId
REACT_APP_USER_POOL_CLIENT_ID=your_client_id
REACT_APP_API_ENDPOINT=https://your-api.amazonaws.com
REACT_APP_ENABLE_ANALYTICS=true
```

**When to use:** Production deployment, demos, real users

---

## Switching Between Modes

### Switch to Local Mode

```bash
# Edit frontend/.env.local
REACT_APP_USE_MOCK_AUTH=true
REACT_APP_LOCAL_OTP_CODE=123456

# Restart dev server
npm start
```

### Switch to AWS Mode

```bash
# Edit frontend/.env.production
REACT_APP_USE_MOCK_AUTH=false

# Add your AWS Cognito details
REACT_APP_USER_POOL_ID=ap-south-1_YourPoolId
REACT_APP_USER_POOL_CLIENT_ID=your_client_id

# Build and deploy
npm run build
```

---

## Customizing the OTP Code

### Change the Hardcoded OTP

**File:** `frontend/.env.local`

```env
# Use any 6-digit code
REACT_APP_LOCAL_OTP_CODE=999999

# Or use a memorable code
REACT_APP_LOCAL_OTP_CODE=111111
```

**Note:** Code must be exactly 6 digits.

---

## How It Works Internally

### authService.ts

```typescript
async confirmSignUp(email: string, confirmationCode: string): Promise<void> {
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';
  const localOtpCode = process.env.REACT_APP_LOCAL_OTP_CODE || '123456';

  if (useMockAuth) {
    // Local mode - validate against hardcoded OTP
    if (confirmationCode === localOtpCode) {
      console.log('✅ OTP verified');
      return;
    } else {
      throw new Error('Invalid code');
    }
  }

  // AWS mode - use real Cognito
  await amplifyAuth.confirmSignUp({
    username: email,
    confirmationCode
  });
}
```

### EmailVerificationModal.tsx

```typescript
<p className="text-sm text-gray-600 text-center mb-6">
  {process.env.REACT_APP_USE_MOCK_AUTH === 'true' ? (
    <>
      <span className="badge">LOCAL DEV MODE</span>
      Use code <strong>123456</strong> to verify
    </>
  ) : (
    <>
      We've sent a code to your email
    </>
  )}
</p>
```

---

## Testing

### Test Local Mode

```bash
# 1. Start dev server
npm start

# 2. Sign up
Email: test@example.com
Password: Test123!

# 3. Enter OTP
Code: 123456

# 4. Should verify successfully ✅
```

### Test AWS Mode

```bash
# 1. Deploy to AWS
npm run build
# Deploy to S3/CloudFront

# 2. Sign up with real email
Email: your-real-email@gmail.com
Password: Test123!

# 3. Check email for OTP
# 4. Enter code from email
# 5. Should verify successfully ✅
```

---

## Troubleshooting

### "Invalid verification code" in Local Mode

**Problem:** Entered wrong code

**Solution:** Use the code from `.env.local`:
```env
REACT_APP_LOCAL_OTP_CODE=123456
```

### OTP not showing in Local Mode

**Problem:** Environment variable not loaded

**Solution:**
```bash
# 1. Check .env.local exists
ls frontend/.env.local

# 2. Restart dev server
npm start

# 3. Check console for OTP hint
```

### Real email not received in AWS Mode

**Problem:** Cognito not configured or email service issue

**Solution:**
1. Check AWS Cognito User Pool settings
2. Verify email service is enabled
3. Check spam folder
4. Try resending code

---

## Security Considerations

### Local Development

- ✅ Hardcoded OTP is fine (not production)
- ✅ Only works in development environment
- ✅ Not exposed to users
- ✅ Speeds up development

### Production

- ⚠️ Never use hardcoded OTP in production
- ⚠️ Always set `REACT_APP_USE_MOCK_AUTH=false`
- ⚠️ Use real AWS Cognito
- ⚠️ Validate environment before deployment

---

## Deployment Checklist

### Before Deploying to AWS

- [ ] Set `REACT_APP_USE_MOCK_AUTH=false` in `.env.production`
- [ ] Add real AWS Cognito credentials
- [ ] Test signup flow with real email
- [ ] Verify OTP email is received
- [ ] Test verification with real code
- [ ] Remove any hardcoded test credentials

### Before Local Development

- [ ] Set `REACT_APP_USE_MOCK_AUTH=true` in `.env.local`
- [ ] Set `REACT_APP_LOCAL_OTP_CODE=123456`
- [ ] Restart dev server
- [ ] Test signup with hardcoded OTP
- [ ] Verify console shows OTP hint

---

## Summary

| Mode | OTP Source | Email Sent? | Cost | Use Case |
|------|------------|-------------|------|----------|
| **Local** | Hardcoded `123456` | ❌ No | ₹0 | Development |
| **AWS** | Real Cognito | ✅ Yes | ₹100-200/mo | Production |

**Recommendation:** Use local mode for development, AWS mode for production.

---

## Quick Reference

### Local Development
```bash
# .env.local
REACT_APP_USE_MOCK_AUTH=true
REACT_APP_LOCAL_OTP_CODE=123456

# Start
npm start

# OTP to use
123456
```

### AWS Production
```bash
# .env.production
REACT_APP_USE_MOCK_AUTH=false
REACT_APP_USER_POOL_ID=ap-south-1_YourPoolId

# Deploy
npm run build

# OTP to use
Check email
```

---

**Last Updated:** November 2, 2025  
**Version:** 1.0.0
