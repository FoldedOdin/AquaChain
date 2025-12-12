# Google OAuth Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Get Google OAuth Credentials (2 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Go to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure:
   - Application type: **Web application**
   - Name: **AquaChain Web Client**
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:3000/auth/google/callback`
6. Click **Create** and copy your **Client ID**

### Step 2: Configure Environment (1 minute)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Client ID:
   ```env
   REACT_APP_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   ```

### Step 3: Add Route (1 minute)

Add the callback route to your router (usually in `App.tsx` or `routes.tsx`):

```typescript
import GoogleCallbackHandler from './components/Auth/GoogleCallbackHandler';

// Add this route
<Route path="/auth/google/callback" element={<GoogleCallbackHandler />} />
```

### Step 4: Test (1 minute)

1. Restart your dev server:
   ```bash
   npm start
   ```

2. Go to login page
3. Click "Continue with Google"
4. Sign in with your Google account
5. You should be redirected back and logged in!

---

## ✅ What's Already Done

The following files have been created/updated:

- ✅ `frontend/src/config/googleOAuth.ts` - OAuth configuration
- ✅ `frontend/src/components/Auth/GoogleCallbackHandler.tsx` - Callback handler
- ✅ `frontend/src/components/LandingPage/GoogleOAuthButton.tsx` - Updated button
- ✅ `frontend/src/dev-server.js` - Backend endpoint added
- ✅ `.env.example` - Environment template
- ✅ `GOOGLE_OAUTH_SETUP.md` - Detailed setup guide

---

## 🔧 Troubleshooting

### "redirect_uri_mismatch" error
**Fix:** Make sure the redirect URI in your code matches exactly what's in Google Console:
- Code: `http://localhost:3000/auth/google/callback`
- Google Console: `http://localhost:3000/auth/google/callback`

### Button doesn't work
**Fix:** Check browser console for errors. Make sure:
1. `.env` file exists with `REACT_APP_GOOGLE_CLIENT_ID`
2. Dev server was restarted after adding `.env`
3. No typos in Client ID

### "Client ID not set" warning
**Fix:** 
1. Make sure `.env` file exists in project root
2. Variable name is exactly `REACT_APP_GOOGLE_CLIENT_ID`
3. Restart dev server after creating `.env`

---

## 📝 Testing Checklist

- [ ] Google Cloud Console project created
- [ ] OAuth credentials created
- [ ] Client ID copied
- [ ] `.env` file created with Client ID
- [ ] Callback route added to router
- [ ] Dev server restarted
- [ ] Can click "Continue with Google"
- [ ] Redirects to Google sign-in
- [ ] Redirects back to app after sign-in
- [ ] User is logged in successfully

---

## 🎯 Next Steps

After basic setup works:

1. **Add OAuth Consent Screen** (required for production)
   - Go to **APIs & Services** > **OAuth consent screen**
   - Fill in app information
   - Add test users for development

2. **Add Production URLs** (when deploying)
   - Add production domain to authorized origins
   - Add production callback URL to redirect URIs
   - Update `.env` for production

3. **Submit for Verification** (for public use)
   - Required if you want anyone to sign in
   - Add privacy policy and terms of service
   - Submit app for Google review

---

## 💡 Tips

- **Development:** Only test users can sign in until app is verified
- **Security:** Never commit `.env` file to git
- **Testing:** Use incognito mode to test with different accounts
- **Debugging:** Check browser console and server logs for errors

---

## 📚 More Information

See `GOOGLE_OAUTH_SETUP.md` for detailed documentation including:
- Complete setup instructions
- Security best practices
- Production deployment guide
- API endpoint documentation
- Flow diagrams

---

## 🆘 Need Help?

Common issues and solutions:

1. **No Client ID warning**
   - Create `.env` file in project root
   - Add `REACT_APP_GOOGLE_CLIENT_ID=your-id`
   - Restart dev server

2. **Redirect URI mismatch**
   - Check Google Console authorized redirect URIs
   - Must exactly match: `http://localhost:3000/auth/google/callback`

3. **Access denied**
   - Add your email as test user in OAuth consent screen
   - Or publish app (for production)

4. **Callback not working**
   - Make sure route is added to router
   - Check backend endpoint is running
   - Look for errors in console

---

## ✨ Features Included

- ✅ Secure OAuth 2.0 flow
- ✅ CSRF protection with state parameter
- ✅ Automatic user creation
- ✅ Profile picture from Google
- ✅ Email verification (Google emails are verified)
- ✅ Beautiful loading states
- ✅ Error handling
- ✅ Development mode simulation
- ✅ Production ready

---

That's it! You should now have Google OAuth working. 🎉
