# Profile Edit with OTP Verification - Guide

## Overview

The Profile Edit feature allows users to update their personal information with enhanced security. Changes to sensitive fields (email and phone) require OTP verification to ensure account security.

## Features

### Editable Fields

| Field | Required | Verification Required | Description |
|-------|----------|----------------------|-------------|
| **First Name** | ✅ Yes | ❌ No | User's first name |
| **Last Name** | ✅ Yes | ❌ No | User's last name |
| **Email** | ✅ Yes | ✅ Yes (if changed) | Primary email address |
| **Phone** | ❌ Optional | ✅ Yes (if changed) | Contact phone number |
| **Address** | ❌ Optional | ❌ No | Physical address |

### Security Features

#### OTP Verification
- **When Required**: Email or phone number changes
- **OTP Length**: 6 digits
- **Validity**: 5 minutes
- **Max Attempts**: 3 attempts per OTP
- **Delivery**: Sent to current email address

#### Non-Sensitive Updates
- Name and address changes don't require OTP
- Updates are immediate
- Still require authentication

## User Flow

### 1. Access Profile Settings

```
Dashboard → Settings Icon → Profile Information → Edit Profile Button
```

### 2. Edit Profile Form

Users can update any of the following:
- First Name
- Last Name
- Email Address (requires verification)
- Phone Number (requires verification)
- Address

### 3. Verification Flow

#### Scenario A: Non-Sensitive Changes Only
```
1. User updates name/address
2. Clicks "Save Changes"
3. Profile updated immediately
4. Success message shown
5. Dashboard refreshes
```

#### Scenario B: Sensitive Changes (Email/Phone)
```
1. User updates email or phone
2. Warning shown: "Verification Required"
3. Clicks "Save Changes"
4. OTP sent to current email
5. OTP verification screen shown
6. User enters 6-digit code
7. Clicks "Verify & Update"
8. Profile updated after verification
9. Success message shown
10. Dashboard refreshes
```

## Technical Implementation

### Frontend Components

#### EditProfileModal Component
**Location**: `frontend/src/components/Dashboard/EditProfileModal.tsx`

**Features**:
- Multi-step form (form → OTP → success/error)
- Real-time validation
- OTP input with auto-focus
- Resend OTP with cooldown timer
- Loading states
- Error handling
- Responsive design

**Props**:
```typescript
interface EditProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentProfile: {
    firstName?: string;
    lastName?: string;
    email: string;
    phone?: string;
    address?: string;
  };
  onProfileUpdated: () => void;
}
```

**State Management**:
```typescript
// Form state
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const [email, setEmail] = useState('');
const [phone, setPhone] = useState('');
const [address, setAddress] = useState('');

// OTP state
const [otp, setOtp] = useState(['', '', '', '', '', '']);
const [otpError, setOtpError] = useState('');
const [resendTimer, setResendTimer] = useState(0);

// Flow state
const [step, setStep] = useState<'form' | 'otp' | 'success' | 'error'>('form');
const [requiresOTP, setRequiresOTP] = useState(false);
```

### Backend API Endpoints

#### 1. Request OTP
**Endpoint**: `POST /api/profile/request-otp`

**Request**:
```json
{
  "email": "user@example.com",
  "changes": {
    "firstName": "John",
    "lastName": "Doe",
    "email": "newemail@example.com",
    "phone": "+1234567890",
    "address": "123 Main St"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "OTP sent to your email",
  "devOtp": "123456"  // Only in development
}
```

#### 2. Verify OTP and Update
**Endpoint**: `PUT /api/profile/verify-and-update`

**Request**:
```json
{
  "otp": "123456",
  "updates": {
    "firstName": "John",
    "lastName": "Doe",
    "email": "newemail@example.com",
    "phone": "+1234567890",
    "address": "123 Main St"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "userId": "user_123",
    "email": "newemail@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1234567890",
    "address": "123 Main St",
    "role": "consumer"
  }
}
```

#### 3. Update Without OTP
**Endpoint**: `PUT /api/profile/update`

**Request**:
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "address": "123 Main St"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": { ... }
}
```

### OTP Management

#### Storage
```javascript
const pendingOTPs = new Map();

// Structure
{
  "user@example.com": {
    otp: "123456",
    changes: { ... },
    expiresAt: 1699999999999,
    attempts: 0
  }
}
```

#### Validation Rules
- **Expiration**: 5 minutes from generation
- **Max Attempts**: 3 failed attempts
- **Rate Limiting**: 60-second cooldown between requests
- **Auto-cleanup**: Expired OTPs removed on verification

#### Security Measures
1. **OTP Generation**: Cryptographically secure random 6-digit code
2. **Time-based Expiration**: 5-minute validity window
3. **Attempt Limiting**: Max 3 verification attempts
4. **Rate Limiting**: 60-second cooldown between OTP requests
5. **Single Use**: OTP deleted after successful verification
6. **Email Verification**: OTP sent to current email only

## User Interface

### Edit Profile Modal

```
┌─────────────────────────────────────────────────────────┐
│  Edit Profile                                      [X]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Update your profile information. Changes to email or   │
│  phone will require verification.                       │
│                                                          │
│  First Name *          Last Name *                      │
│  [John_________]       [Doe__________]                  │
│                                                          │
│  Email Address * (Requires verification)                │
│  [john.doe@example.com_____________________]            │
│                                                          │
│  Phone Number (Requires verification)                   │
│  [+1 (555) 123-4567________________________]            │
│                                                          │
│  Address                                                 │
│  [123 Main St, City, State, ZIP____________]            │
│  [_________________________________________]            │
│                                                          │
│  ⚠️ Verification Required                               │
│  You're changing sensitive information. We'll send a    │
│  verification code to your current email address.       │
│                                                          │
│  [Cancel]                        [Save Changes]         │
└─────────────────────────────────────────────────────────┘
```

### OTP Verification Screen

```
┌─────────────────────────────────────────────────────────┐
│  Verify Your Identity                              [X]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                    🛡️                                    │
│                                                          │
│           Enter Verification Code                        │
│                                                          │
│  We've sent a 6-digit code to user@example.com         │
│                                                          │
│         [1] [2] [3] [4] [5] [6]                        │
│                                                          │
│         Resend code in 45s                              │
│                                                          │
│  ℹ️ Why do I need to verify?                            │
│  You're changing sensitive information (email or phone).│
│  We need to verify it's really you for security.       │
│                                                          │
│  [Back]                          [Verify & Update]      │
└─────────────────────────────────────────────────────────┘
```

### Success Screen

```
┌─────────────────────────────────────────────────────────┐
│  Edit Profile                                      [X]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                    ✓                                     │
│                                                          │
│         Profile Updated Successfully!                    │
│                                                          │
│  Your profile information has been updated.             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Error Handling

### Common Errors

#### Invalid OTP
```json
{
  "success": false,
  "error": "Invalid OTP. Please try again.",
  "attemptsRemaining": 2
}
```

#### Expired OTP
```json
{
  "success": false,
  "error": "OTP expired. Please request a new one."
}
```

#### Too Many Attempts
```json
{
  "success": false,
  "error": "Too many failed attempts. Please request a new OTP."
}
```

#### Rate Limit
```json
{
  "success": false,
  "error": "Please wait before requesting another OTP."
}
```

## Development Testing

### Test Scenarios

#### 1. Update Name Only (No OTP)
```javascript
// Should update immediately without OTP
{
  firstName: "Jane",
  lastName: "Smith"
}
```

#### 2. Update Email (Requires OTP)
```javascript
// Should trigger OTP flow
{
  email: "newemail@example.com"
}
```

#### 3. Update Phone (Requires OTP)
```javascript
// Should trigger OTP flow
{
  phone: "+1987654321"
}
```

#### 4. Update Multiple Fields
```javascript
// Should trigger OTP if email/phone changed
{
  firstName: "Jane",
  lastName: "Smith",
  email: "newemail@example.com",
  phone: "+1987654321",
  address: "456 Oak Ave"
}
```

### Development OTP

In development mode, the OTP is logged to console:
```
📧 OTP for user@example.com: 123456
💡 Use this OTP to verify profile changes
```

## Production Deployment

### Email Service Integration

For production, integrate with an email service:

```javascript
// Example with AWS SES
const AWS = require('aws-sdk');
const ses = new AWS.SES({ region: 'us-east-1' });

async function sendOTP(email, otp) {
  const params = {
    Source: 'noreply@aquachain.com',
    Destination: { ToAddresses: [email] },
    Message: {
      Subject: { Data: 'AquaChain - Verification Code' },
      Body: {
        Html: {
          Data: `
            <h2>Verification Code</h2>
            <p>Your verification code is: <strong>${otp}</strong></p>
            <p>This code will expire in 5 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
          `
        }
      }
    }
  };
  
  await ses.sendEmail(params).promise();
}
```

### Database Updates

For production, update user records in database:

```python
# Lambda function example
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('AquaChain-Users')

def update_user_profile(user_id, updates):
    users_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET firstName = :fn, lastName = :ln, email = :em, phone = :ph, address = :ad, updatedAt = :ua',
        ExpressionAttributeValues={
            ':fn': updates['firstName'],
            ':ln': updates['lastName'],
            ':em': updates['email'],
            ':ph': updates.get('phone', ''),
            ':ad': updates.get('address', ''),
            ':ua': datetime.utcnow().isoformat()
        }
    )
```

## Security Best Practices

### 1. OTP Security
- ✅ Use cryptographically secure random generation
- ✅ Set short expiration time (5 minutes)
- ✅ Limit verification attempts (3 max)
- ✅ Implement rate limiting
- ✅ Delete OTP after use

### 2. Email Changes
- ✅ Send OTP to current email (not new email)
- ✅ Verify ownership before change
- ✅ Send confirmation to both old and new email
- ✅ Log email change events

### 3. Authentication
- ✅ Require valid JWT token
- ✅ Verify token signature
- ✅ Check token expiration
- ✅ Validate user ownership

### 4. Input Validation
- ✅ Sanitize all inputs
- ✅ Validate email format
- ✅ Validate phone format
- ✅ Limit field lengths
- ✅ Prevent XSS attacks

## Troubleshooting

### OTP Not Received
1. Check spam/junk folder
2. Verify email address is correct
3. Wait 60 seconds before requesting new OTP
4. Check email service logs

### OTP Invalid
1. Ensure all 6 digits entered
2. Check OTP hasn't expired (5 min)
3. Verify no typos in code
4. Request new OTP if needed

### Profile Not Updating
1. Check authentication token
2. Verify all required fields filled
3. Check network connection
4. Review browser console for errors

### Email Change Issues
1. Verify OTP sent to current email
2. Check new email format is valid
3. Ensure new email not already in use
4. Confirm OTP verification successful

## Related Documentation

- [Authentication Guide](./AUTHENTICATION_GUIDE.md)
- [Security Best Practices](./SECURITY_GUIDE.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [User Management](./USER_MANAGEMENT.md)

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [GitHub Issues](https://github.com/aquachain/issues)
- Contact support: support@aquachain.com

---

**Last Updated**: November 6, 2025
**Version**: 1.0
**Status**: Production Ready
