# Google OAuth - Quick Reference Card

## 🚀 5-Minute Setup

### 1. Get Client ID (2 min)
```
https://console.cloud.google.com/
→ APIs & Services → Credentials
→ Create OAuth 2.0 Client ID
→ Copy Client ID
```

### 2. Configure (1 min)
```bash
cp .env.example .env
# Edit .env and add:
REACT_APP_GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
```

### 3. Add Route (1 min)
```typescript
import GoogleCallbackHandler from './components/Auth/GoogleCallbackHandler';
<Route path="/auth/google/callback" element={<GoogleCallbackHandler />} />
```

### 4. Restart (1 min)
```bash
npm start
```

---

## 📁 Files Created

```
frontend/src/
├── config/
│   └── googleOAuth.ts              ← OAuth configuration
├── components/
│   ├── Auth/
│   │   └── GoogleCallbackHandler.tsx  ← Callback handler
│   └── LandingPage/
│       └── GoogleOAuthButton.tsx   ← Updated button
.env.example                        ← Environment template
```

---

## 🔧 Backend Endpoint

```javascript
POST /api/auth/google/callback

Request:
{
  "code": "auth_code",
  "redirectUri": "http://localhost:3000/auth/google/callback"
}

Response:
{
  "success": true,
  "token": "session_token",
  "user": { ... }
}
```

---

## 🌐 Google Console Setup

### Authorized JavaScript Origins:
```
http://localhost:3000
https://yourdomain.com
```

### Authorized Redirect URIs:
```
http://localhost:3000/auth/google/callback
https://yourdomain.com/auth/google/callback
```

---

## 🔐 Environment Variables

```env
# Required
REACT_APP_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com

# Optional (has defaults)
REACT_APP_OAUTH_REDIRECT_URI=http://localhost:3000/auth/google/callback
REACT_APP_BASE_URL=http://localhost:3000
```

---

## ✅ Testing Checklist

- [ ] Client ID added to `.env`
- [ ] Dev server restarted
- [ ] Callback route added
- [ ] Button redirects to Google
- [ ] Can sign in with Google
- [ ] Redirects back to app
- [ ] User is authenticated

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Client ID not set" | Create `.env` with `REACT_APP_GOOGLE_CLIENT_ID` |
| "redirect_uri_mismatch" | Check Google Console redirect URIs match exactly |
| Button doesn't work | Restart dev server after adding `.env` |
| Callback error | Make sure route is added to router |

---

## 📚 Documentation

- **Quick Start:** `GOOGLE_OAUTH_QUICK_START.md`
- **Full Setup:** `GOOGLE_OAUTH_SETUP.md`
- **Implementation:** `GOOGLE_OAUTH_IMPLEMENTATION_COMPLETE.md`

---

## 🎯 Flow

```
Click Button → Google Sign-in → Callback → Exchange Code → Create User → Login ✅
```

---

## 💡 Tips

- Use incognito mode to test with different accounts
- Check browser console for errors
- Check server logs for backend issues
- Add test users in Google Console for development

---

## 🔗 Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)

---

**Status:** ✅ Ready to Use  
**Setup Time:** 5 minutes  
**Difficulty:** Easy
