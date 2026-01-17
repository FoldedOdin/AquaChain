# Google Maps API Key - Security Configuration Guide

## 🔐 Your API Key Security Checklist

Your API key: `AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw`

**IMPORTANT:** This key is currently UNRESTRICTED and needs to be secured immediately!

---

## ⚠️ IMMEDIATE ACTION REQUIRED

### Step 1: Restrict Your API Key (Do This Now!)

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/apis/credentials
   - Sign in with your Google account

2. **Find Your API Key**
   - Look for the key ending in `...0XnWhuw`
   - Click on the key name to edit

3. **Set Application Restrictions**
   
   Choose **HTTP referrers (web sites)**
   
   Add these referrers:
   ```
   http://localhost:3000/*
   http://localhost:3001/*
   http://localhost:3002/*
   https://yourdomain.com/*
   https://*.yourdomain.com/*
   ```
   
   Replace `yourdomain.com` with your actual production domain.

4. **Set API Restrictions**
   
   Choose **Restrict key**
   
   Select ONLY these APIs:
   - ✅ Maps JavaScript API
   - ✅ Places API
   - ✅ Geocoding API
   
   **DO NOT** select other APIs you're not using.

5. **Click "Save"**

---

## 🛡️ Security Best Practices

### 1. Never Commit API Keys to Git

**Check if your key is in git:**
```bash
git log --all -p | grep "AIzaSy"
```

**If found, you MUST:**
1. Regenerate the API key in Google Cloud Console
2. Update your `.env` file with the new key
3. Add `.env` to `.gitignore` (should already be there)

**Verify `.gitignore` includes:**
```
# Environment files
.env
.env.local
.env.development
.env.production
frontend/.env
frontend/.env.local
```

### 2. Use Environment Variables

**✅ CORRECT (Current Setup):**
```env
# frontend/.env
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw
```

**❌ WRONG:**
```javascript
// Hardcoded in code
const apiKey = "AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw";
```

### 3. Different Keys for Different Environments

**Recommended Setup:**

**Development (`.env.development`):**
```env
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSy...dev-key...
```

**Production (`.env.production`):**
```env
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSy...prod-key...
```

**Benefits:**
- Separate usage tracking
- Different restrictions per environment
- Easy to revoke if compromised

### 4. Monitor API Usage

**Set up monitoring:**
1. Go to: https://console.cloud.google.com/apis/dashboard
2. Check daily usage
3. Set up billing alerts
4. Review unusual spikes

**Set billing alerts:**
1. Go to: https://console.cloud.google.com/billing
2. Click "Budgets & alerts"
3. Create alert for $10, $50, $100

---

## 🔒 API Key Restrictions Configuration

### Application Restrictions

#### For Development:
```
HTTP referrers:
- http://localhost:3000/*
- http://localhost:3001/*
- http://localhost:3002/*
- http://127.0.0.1:3000/*
```

#### For Production:
```
HTTP referrers:
- https://yourdomain.com/*
- https://*.yourdomain.com/*
- https://www.yourdomain.com/*
```

#### For Both (Recommended):
Create TWO separate API keys:
1. **Development Key** - Restricted to localhost
2. **Production Key** - Restricted to your domain

### API Restrictions

**Enable ONLY these APIs:**

1. **Maps JavaScript API**
   - Required for: Map display
   - Usage: Every map load
   - Cost: ~$7 per 1,000 loads (after free tier)

2. **Places API**
   - Required for: Address autocomplete
   - Usage: Every search query
   - Cost: ~$17 per 1,000 requests (after free tier)

3. **Geocoding API**
   - Required for: Converting coordinates to addresses
   - Usage: Every marker drag, current location
   - Cost: ~$5 per 1,000 requests (after free tier)

**DO NOT enable:**
- ❌ Directions API (not used)
- ❌ Distance Matrix API (not used)
- ❌ Roads API (not used)
- ❌ Street View API (not used)

---

## 💰 Cost Management

### Free Tier (Monthly)

Google provides $200 free credit per month:
- **Maps JavaScript API**: ~28,000 free loads
- **Places API**: ~1,000 free autocomplete requests
- **Geocoding API**: ~40,000 free requests

### Typical Usage for Your App

**Small app (100 users/day):**
- Map loads: ~100/day = 3,000/month ✅ FREE
- Autocomplete: ~50/day = 1,500/month ⚠️ $8.50/month
- Geocoding: ~100/day = 3,000/month ✅ FREE
- **Total: ~$8.50/month**

**Medium app (1,000 users/day):**
- Map loads: ~1,000/day = 30,000/month ⚠️ $14/month
- Autocomplete: ~500/day = 15,000/month ⚠️ $238/month
- Geocoding: ~1,000/day = 30,000/month ✅ FREE
- **Total: ~$252/month**

### Cost Optimization Tips

1. **Cache Geocoding Results**
   ```javascript
   // Store in localStorage
   const cachedAddress = localStorage.getItem(`geocode_${lat}_${lng}`);
   ```

2. **Debounce Autocomplete**
   ```javascript
   // Wait 300ms before searching
   const debouncedSearch = debounce(searchAddress, 300);
   ```

3. **Use Session Tokens**
   ```javascript
   // Reduces autocomplete cost by 60%
   const sessionToken = new google.maps.places.AutocompleteSessionToken();
   ```

4. **Limit Autocomplete Requests**
   ```javascript
   // Only search after 3 characters
   if (query.length < 3) return;
   ```

---

## 🚨 What to Do If Key Is Compromised

### Signs of Compromise:
- Unexpected high usage
- Requests from unknown domains
- Billing alerts triggered
- Unusual geographic patterns

### Immediate Actions:

1. **Regenerate API Key**
   ```
   1. Go to Google Cloud Console
   2. Click on your API key
   3. Click "Regenerate Key"
   4. Copy new key
   5. Update .env file
   6. Restart application
   ```

2. **Review Usage**
   ```
   1. Check API Dashboard
   2. Look for unusual patterns
   3. Check request origins
   4. Review timestamps
   ```

3. **Tighten Restrictions**
   ```
   1. Add stricter HTTP referrer rules
   2. Reduce enabled APIs
   3. Set up rate limiting
   4. Enable billing alerts
   ```

4. **Contact Google Support**
   - Report suspicious activity
   - Request usage review
   - Dispute fraudulent charges

---

## ✅ Security Verification Checklist

Use this checklist to verify your API key is secure:

### Basic Security
- [ ] API key is in `.env` file (not hardcoded)
- [ ] `.env` is in `.gitignore`
- [ ] API key is not committed to git
- [ ] Application restrictions are set
- [ ] API restrictions are set
- [ ] Only required APIs are enabled

### Advanced Security
- [ ] Separate keys for dev/prod
- [ ] HTTP referrer restrictions configured
- [ ] Billing alerts set up
- [ ] Usage monitoring enabled
- [ ] Rate limiting implemented
- [ ] Caching implemented

### Monitoring
- [ ] Daily usage checked
- [ ] Unusual patterns monitored
- [ ] Billing alerts configured
- [ ] Request origins reviewed

---

## 🔧 Implementation Steps

### Step-by-Step Security Setup

#### 1. Secure Your Current Key (5 minutes)

```bash
# 1. Go to Google Cloud Console
open https://console.cloud.google.com/apis/credentials

# 2. Click on your API key
# 3. Set Application restrictions: HTTP referrers
# 4. Add: http://localhost:3000/*
# 5. Set API restrictions: Select only Maps, Places, Geocoding
# 6. Click Save
```

#### 2. Verify .gitignore (1 minute)

```bash
# Check if .env is ignored
cat .gitignore | grep ".env"

# Should see:
# .env
# .env.local
# frontend/.env
```

#### 3. Check Git History (2 minutes)

```bash
# Search for API key in git history
git log --all -p | grep "AIzaSy"

# If found, regenerate key immediately!
```

#### 4. Set Up Monitoring (3 minutes)

```bash
# 1. Go to API Dashboard
open https://console.cloud.google.com/apis/dashboard

# 2. Click "Quotas"
# 3. Review current usage
# 4. Set up alerts
```

#### 5. Test Restrictions (2 minutes)

```bash
# Start your app
cd frontend
npm start

# Test:
# 1. Map loads correctly
# 2. Address search works
# 3. Current location works
# 4. No console errors
```

---

## 📋 Quick Reference

### Your Current Configuration

**API Key Location:**
```
frontend/.env
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSyCbNfmOrTnjyFCp3A4fVqT7Qjwz0XnWhuw
```

**Required APIs:**
- Maps JavaScript API
- Places API
- Geocoding API

**Recommended Restrictions:**
```
Application: HTTP referrers
- http://localhost:3000/*
- https://yourdomain.com/*

API: Restrict key
- Maps JavaScript API
- Places API
- Geocoding API
```

### Useful Links

- **API Credentials**: https://console.cloud.google.com/apis/credentials
- **API Dashboard**: https://console.cloud.google.com/apis/dashboard
- **Billing**: https://console.cloud.google.com/billing
- **Documentation**: https://developers.google.com/maps/documentation

---

## 🆘 Troubleshooting

### "RefererNotAllowedMapError"
**Cause:** Your domain is not in the allowed referrers list
**Fix:** Add your domain to HTTP referrer restrictions

### "ApiNotActivatedMapError"
**Cause:** Required API is not enabled
**Fix:** Enable Maps JavaScript API, Places API, and Geocoding API

### "InvalidKeyMapError"
**Cause:** API key is incorrect or regenerated
**Fix:** Update `.env` with correct key and restart app

### Map loads but autocomplete doesn't work
**Cause:** Places API not enabled or restricted
**Fix:** Enable Places API and add to API restrictions

### High unexpected costs
**Cause:** API key compromised or no restrictions
**Fix:** Regenerate key, add restrictions, implement caching

---

## 📞 Support

### Need Help?

1. **Check Google Cloud Console**
   - Review error messages
   - Check API status
   - Verify restrictions

2. **Review Documentation**
   - [API Key Best Practices](https://developers.google.com/maps/api-security-best-practices)
   - [API Key Restrictions](https://cloud.google.com/docs/authentication/api-keys)

3. **Contact Google Support**
   - For billing issues
   - For security concerns
   - For technical problems

---

## ✅ Summary

**Immediate Actions:**
1. ✅ API key added to `.env`
2. ⚠️ **SECURE YOUR KEY NOW** - Add restrictions in Google Cloud Console
3. ✅ Verify `.env` is in `.gitignore`
4. ⚠️ Set up billing alerts
5. ⚠️ Monitor usage regularly

**Your key is currently UNRESTRICTED - secure it immediately to prevent unauthorized usage and unexpected costs!**

---

**Last Updated**: January 2, 2026  
**Security Level**: ⚠️ NEEDS IMMEDIATE ATTENTION  
**Next Review**: After securing restrictions
