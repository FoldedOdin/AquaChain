# 🔑 Get Your reCAPTCHA Site Key - Quick Guide

## ⚠️ Current Status

Your reCAPTCHA Site Key is **empty** in `frontend/.env`:

```env
REACT_APP_RECAPTCHA_SITE_KEY=
```

You need to add a valid reCAPTCHA Site Key to enable bot protection on your forms.

---

## 🎯 Two Options: Choose One

### Option 1: Test Key (Instant - For Development) ⚡

**Use this if you want to:**
- Continue developing immediately
- Test the app without setup
- Skip configuration for now

**Add this to `frontend/.env`:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
```

**What this does:**
- ✅ Works immediately (no setup needed)
- ✅ Always passes validation
- ✅ Perfect for development/testing
- ⚠️ **NOT for production** (everyone can bypass it)

**Then restart your app:**
```bash
cd frontend
npm start
```

---

### Option 2: Real Key (5 Minutes - For Production) 🔒

**Use this if you want to:**
- Protect your forms from bots
- Deploy to production
- Have real security

#### Step 1: Open reCAPTCHA Admin (30 seconds)

**Click this link:** https://www.google.com/recaptcha/admin/create

Sign in with your Google account.

#### Step 2: Fill in the Registration Form (2 minutes)

**Label:**
```
AquaChain
```

**reCAPTCHA type:**
- Select: ☑️ **reCAPTCHA v2**
- Then select: ☑️ **"I'm not a robot" Checkbox**

**Domains:**
```
localhost
```

(You can add your production domain later)

**Accept Terms:**
- ✅ Check "Accept the reCAPTCHA Terms of Service"

**Click "Submit"**

#### Step 3: Copy Your Site Key (1 minute)

After submitting, you'll see two keys:

```
┌─────────────────────────────────────────────┐
│ Site Key                                    │
│ 6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  │  ← Copy this one!
│ [Copy]                                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Secret Key                                  │
│ 6LcYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY  │  ← Keep this private!
│ [Copy]                                      │
└─────────────────────────────────────────────┘
```

**Copy the Site Key** (the first one)

#### Step 4: Add to Your .env File (30 seconds)

Open `frontend/.env` and update:

```env
REACT_APP_RECAPTCHA_SITE_KEY=6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

(Replace with your actual Site Key)

#### Step 5: Restart Your App (30 seconds)

```bash
cd frontend
npm start
```

---

## ✅ How to Verify It's Working

### 1. Check the Key Format

A valid reCAPTCHA Site Key should:
- ✅ Start with `6L`
- ✅ Be about 40 characters long
- ✅ Contain only letters, numbers, hyphens, underscores
- ❌ NOT be a URL
- ❌ NOT contain `https://`
- ❌ NOT contain `googleapis.com`

**Examples:**

✅ **CORRECT:**
```
6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

❌ **WRONG:**
```
https://recaptchaenterprise.googleapis.com/v1/projects/...
AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
740926138916-gn6ne63km7o8d44f3um3rlded4nirqrp.apps.googleusercontent.com
```

### 2. Test in Your App

1. Start your app: `npm start`
2. Find a form with reCAPTCHA (contact form, registration, etc.)
3. You should see the **"I'm not a robot" checkbox**
4. Check the box
5. Submit the form
6. Should work without errors

### 3. Check Browser Console

Press **F12** to open browser console and look for:
- ✅ No reCAPTCHA errors
- ❌ "Invalid site key" → Key is wrong or domain not registered
- ❌ "Timeout or duplicate" → Domain not registered

---

## 🔍 Common Mistakes

### Mistake 1: Using reCAPTCHA Enterprise URL

**Wrong:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=https://recaptchaenterprise.googleapis.com/v1/projects/project-79619d34-9360-45e4-9f6/assessments?key=API_KEY
```

This is an API endpoint, not a Site Key!

**Correct:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
```

### Mistake 2: Using Secret Key Instead of Site Key

**Wrong:**
```env
# This is the SECRET key (for backend only)
REACT_APP_RECAPTCHA_SITE_KEY=6LcYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

**Correct:**
```env
# This is the SITE key (for frontend)
REACT_APP_RECAPTCHA_SITE_KEY=6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Mistake 3: Using Google Maps API Key

**Wrong:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw
```

This is a Google Maps key, not reCAPTCHA!

**Correct:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
```

### Mistake 4: Using Google OAuth Client ID

**Wrong:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=740926138916-gn6ne63km7o8d44f3um3rlded4nirqrp.apps.googleusercontent.com
```

This is OAuth, not reCAPTCHA!

**Correct:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
```

---

## 📋 Your Current Configuration Status

### ✅ Google OAuth Client ID - VALID
```env
REACT_APP_GOOGLE_CLIENT_ID=740926138916-gn6ne63km7o8d44f3um3rlded4nirqrp.apps.googleusercontent.com
```
Format is correct! This enables "Sign in with Google".

### ❌ reCAPTCHA Site Key - EMPTY
```env
REACT_APP_RECAPTCHA_SITE_KEY=
```
**Action needed:** Add a valid Site Key (see options above).

### ✅ Google Maps API Key - VALID
```env
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw
```
Format is correct! But needs security restrictions (see SECURE_GOOGLE_MAPS_API_NOW.md).

---

## 🎯 Recommended Next Steps

### For Development (Right Now):

**Use the test key:**
```env
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
```

**Why?**
- ✅ Works immediately
- ✅ No setup required
- ✅ Can continue developing
- ✅ Can test reCAPTCHA functionality

### Before Production:

**Get a real key:**
1. Go to https://www.google.com/recaptcha/admin/create
2. Register your site
3. Copy the Site Key
4. Update `.env` with real key
5. Add your production domain
6. Test thoroughly

---

## 🆘 Troubleshooting

### "I registered but don't see my keys"

1. Go to: https://www.google.com/recaptcha/admin
2. You should see a list of your registered sites
3. Click on your site name
4. You'll see both Site Key and Secret Key

### "I'm on reCAPTCHA Enterprise page"

You're in the wrong place! 

**Wrong:** https://cloud.google.com/recaptcha-enterprise  
**Correct:** https://www.google.com/recaptcha/admin

Standard reCAPTCHA is free and simpler. Use that!

### "reCAPTCHA doesn't appear on my forms"

**Check:**
1. Site Key is correct in `.env`
2. App was restarted after changing `.env`
3. Browser console for errors (F12)
4. Domain is registered in reCAPTCHA admin

### "Invalid site key" error

**Possible causes:**
- Site Key is wrong (check you copied it correctly)
- Domain not registered (add `localhost` in reCAPTCHA admin)
- Using Secret Key instead of Site Key
- Using a different Google service's key

---

## 💡 Quick Reference

### What Each Key Is For:

| Key Type | Starts With | Used For | Where |
|----------|-------------|----------|-------|
| **reCAPTCHA Site Key** | `6L` | Frontend reCAPTCHA | `REACT_APP_RECAPTCHA_SITE_KEY` |
| **reCAPTCHA Secret Key** | `6L` | Backend validation | Backend env (NOT frontend) |
| **Google Maps API Key** | `AIza` | Google Maps | `REACT_APP_GOOGLE_MAPS_API_KEY` |
| **Google OAuth Client ID** | Numbers-letters`.apps.googleusercontent.com` | Sign in with Google | `REACT_APP_GOOGLE_CLIENT_ID` |

### Your Complete .env Should Look Like:

```env
# Security Configuration
REACT_APP_GOOGLE_CLIENT_ID=740926138916-gn6ne63km7o8d44f3um3rlded4nirqrp.apps.googleusercontent.com
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI

# Google Maps Configuration
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw
```

---

## 📚 Additional Resources

- **reCAPTCHA Admin Console**: https://www.google.com/recaptcha/admin
- **reCAPTCHA Documentation**: https://developers.google.com/recaptcha/docs/display
- **Full Setup Guide**: [SETUP_GOOGLE_OAUTH_AND_RECAPTCHA.md](SETUP_GOOGLE_OAUTH_AND_RECAPTCHA.md)
- **Google Maps Security**: [SECURE_GOOGLE_MAPS_API_NOW.md](SECURE_GOOGLE_MAPS_API_NOW.md)

---

## ✅ Quick Action Checklist

**Choose one:**

### Option A: Test Key (30 seconds)
- [ ] Copy test key: `6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI`
- [ ] Add to `frontend/.env` as `REACT_APP_RECAPTCHA_SITE_KEY=`
- [ ] Restart app: `npm start`
- [ ] Test that reCAPTCHA appears

### Option B: Real Key (5 minutes)
- [ ] Go to https://www.google.com/recaptcha/admin/create
- [ ] Register site (choose reCAPTCHA v2)
- [ ] Copy Site Key (starts with `6L`)
- [ ] Add to `frontend/.env` as `REACT_APP_RECAPTCHA_SITE_KEY=`
- [ ] Restart app: `npm start`
- [ ] Test that reCAPTCHA appears

---

**Need help?** Check the troubleshooting section or see [SETUP_GOOGLE_OAUTH_AND_RECAPTCHA.md](SETUP_GOOGLE_OAUTH_AND_RECAPTCHA.md) for detailed instructions.

---

**Created**: January 2, 2026  
**Last Updated**: January 2, 2026  
**Time Required**: 30 seconds (test key) or 5 minutes (real key)  
**Difficulty**: Easy
