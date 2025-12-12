# Google OAuth Setup Guide

## Overview
This guide explains how to set up "Continue with Google" authentication for your application.

## Prerequisites
- Google Cloud Console account
- Your application running on localhost:3000 (development)
- Production domain (for production deployment)

---

## Step 1: Create Google OAuth Credentials

### 1.1 Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Create a new project or select existing project
3. Name it: "AquaChain IoT Platform" (or your preferred name)

### 1.2 Enable Google+ API
1. Go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click "Enable"

### 1.3 Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type
3. Fill in the required information:
   - **App name:** AquaChain IoT Platform
   - **User support email:** Your email
   - **Developer contact:** Your email
4. Add scopes:
   - `email`
   - `profile`
   - `openid`
5. Add test users (for development):
   - Add your test email addresses
6. Save and continue

### 1.4 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client ID"
3. Select "Web application"
4. Configure:
   - **Name:** AquaChain Web Client
   - **Authorized JavaScript origins:**
     - `http://localhost:3000` (development)
     - `https://yourdomain.com` (production)
   - **Authorized redirect URIs:**
     - `http://localhost:3000/auth/google/callback` (development)
     - `https://yourdomain.com/auth/google/callback` (production)
5. Click "Create"
6. **IMPORTANT:** Copy your Client ID and Client Secret

---

## Step 2: Environment Configuration

### 2.1 Create Environment File
Create `.env` file in your project root:

```env
# Google OAuth Configuration
REACT_APP_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
REACT_APP_GOOGLE_CLIENT_SECRET=your-client-secret-here

# OAuth Redirect URIs
REACT_APP_OAUTH_REDIRECT_URI=http://localhost:3000/auth/google/callback
REACT_APP_BASE_URL=http://localhost:3000

# For production, use:
# REACT_APP_OAUTH_REDIRECT_URI=https://yourdomain.com/auth/google/callback
# REACT_APP_BASE_URL=https://yourdomain.com
```

### 2.2 Add to .gitignore
Make sure `.env` is in your `.gitignore`:
```
.env
.env.local
.env.production
```

---

## Step 3: Implementation Files

The following files have been created/updated:

### 3.1 OAuth Configuration
- `frontend/src/config/googleOAuth.ts` - OAuth configuration
- `frontend/src/contexts/GoogleAuthContext.tsx` - Auth context provider
- `frontend/src/components/Auth/GoogleCallbackHandler.tsx` - Callback handler

### 3.2 Updated Components
- `frontend/src/components/LandingPage/GoogleOAuthButton.tsx` - Button component
- `frontend/src/services/authService.ts` - Auth service with Google OAuth

---

## Step 4: Integration

### 4.1 Wrap App with Auth Provider
Update `frontend/src/App.tsx`:

```typescript
import { GoogleAuthProvider } from './contexts/GoogleAuthContext';

function App() {
  return (
    <GoogleAuthProvider>
      {/* Your existing app components */}
    </GoogleAuthProvider>
  );
}
```

### 4.2 Add Callback Route
Add route in your router:

```typescript
<Route path="/auth/google/callback" element={<GoogleCallbackHandler />} />
```

---

## Step 5: Testing

### 5.1 Development Testing
1. Start your dev server: `npm start`
2. Navigate to login page
3. Click "Continue with Google"
4. Should redirect to Google sign-in
5. After signing in, should redirect back to your app
6. User should be authenticated

### 5.2 Test Users
During development (before verification), only test users added in Google Console can sign in.

### 5.3 Debugging
Check browser console for:
- OAuth configuration logs
- Redirect URLs
- Token exchange logs
- Error messages

---

## Step 6: Backend Integration

### 6.1 Update Dev Server
The dev server (`frontend/src/dev-server.js`) has been updated with:
- `/api/auth/google/callback` endpoint
- Token verification
- User creation/lookup
- Session management

### 6.2 Verify Backend Endpoint
Test the callback endpoint:
```bash
curl -X POST http://localhost:3002/api/auth/google/callback \
  -H "Content-Type: application/json" \
  -d '{"code":"test-code","state":"test-state"}'
```

---

## Step 7: Production Deployment

### 7.1 Update OAuth Credentials
1. Go back to Google Cloud Console
2. Add production URLs to authorized origins and redirect URIs
3. Update environment variables for production

### 7.2 Verify OAuth Consent Screen
1. Submit app for verification (if needed)
2. Add privacy policy URL
3. Add terms of service URL

### 7.3 Environment Variables
Set production environment variables:
```bash
REACT_APP_GOOGLE_CLIENT_ID=your-production-client-id
REACT_APP_OAUTH_REDIRECT_URI=https://yourdomain.com/auth/google/callback
REACT_APP_BASE_URL=https://yourdomain.com
```

---

## Security Best Practices

### 1. State Parameter
- Always use state parameter to prevent CSRF attacks
- Verify state matches on callback

### 2. Token Storage
- Store tokens securely (httpOnly cookies in production)
- Never expose tokens in URLs
- Use short-lived access tokens

### 3. HTTPS
- Always use HTTPS in production
- Never send tokens over HTTP

### 4. Token Validation
- Verify token signature
- Check token expiration
- Validate issuer and audience

---

## Troubleshooting

### Error: "redirect_uri_mismatch"
**Solution:** Make sure redirect URI in code exactly matches the one in Google Console

### Error: "invalid_client"
**Solution:** Check your Client ID and Client Secret are correct

### Error: "access_denied"
**Solution:** User cancelled sign-in or app not verified

### Error: "popup_closed_by_user"
**Solution:** User closed popup before completing sign-in

### Tokens not working
**Solution:** Check token expiration, verify backend is validating correctly

---

## Flow Diagram

```
User clicks "Continue with Google"
    ↓
Redirect to Google OAuth
    ↓
User signs in with Google
    ↓
Google redirects to callback URL with code
    ↓
Frontend exchanges code for tokens
    ↓
Backend verifies tokens
    ↓
Create/update user in database
    ↓
Return session token to frontend
    ↓
User is authenticated
```

---

## API Endpoints

### Frontend Endpoints
- `GET /auth/google/callback` - OAuth callback handler

### Backend Endpoints
- `POST /api/auth/google/callback` - Exchange code for tokens
- `POST /api/auth/google/verify` - Verify Google token
- `GET /api/auth/google/user` - Get user info from Google

---

## Next Steps

1. ✅ Set up Google Cloud Console project
2. ✅ Create OAuth credentials
3. ✅ Configure environment variables
4. ✅ Test in development
5. ⏳ Deploy to production
6. ⏳ Submit for OAuth verification (if needed)

---

## Support

For issues:
1. Check Google Cloud Console logs
2. Check browser console for errors
3. Check backend server logs
4. Verify environment variables are set correctly

---

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Websites](https://developers.google.com/identity/sign-in/web)
- [OAuth 2.0 Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
