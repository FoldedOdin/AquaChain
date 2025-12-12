# Google Maps Address Picker - Quick Setup

## 🚀 5-Minute Setup

### Step 1: Get API Key (3 minutes)

1. **Go to:** https://console.cloud.google.com/
2. **Create project** (or select existing)
3. **Enable APIs:**
   - Maps JavaScript API
   - Places API
   - Geocoding API
4. **Create API Key:**
   - Go to Credentials
   - Create Credentials > API Key
   - Copy the key

### Step 2: Add to .env (1 minute)

Edit `frontend/.env`:
```env
REACT_APP_GOOGLE_MAPS_API_KEY=your-api-key-here
```

### Step 3: Restart (1 minute)

```bash
npm start
```

---

## ✅ Test It

1. Login to dashboard
2. Click "Edit Profile" (settings icon)
3. Click "Pick Address on Map"
4. Map should load!
5. Try:
   - Search for address
   - Use current location
   - Drag marker
   - Click on map
6. Click "Confirm Address"
7. Address saved! ✅

---

## 🎯 Features

- **Search:** Type address, get suggestions
- **Current Location:** GPS-based location
- **Drag Marker:** Precise positioning
- **Click Map:** Quick selection
- **Address Details:** Full address + coordinates

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Map doesn't load | Check API key in `.env`, restart app |
| "Invalid API key" | Verify key is correct, no extra spaces |
| Search doesn't work | Enable Places API in Google Console |
| Current location fails | Allow location permission in browser |

---

## 💰 Cost

**Free tier:** $200/month credit
- ~28,000 map loads
- ~1,000 searches
- ~40,000 geocodes

**For most apps:** Completely free!

---

## 📚 Full Documentation

See `GOOGLE_MAPS_ADDRESS_PICKER_SETUP.md` for:
- Detailed setup instructions
- API restrictions
- Security best practices
- Advanced configuration
- Troubleshooting guide

---

**Status:** ✅ Ready to use  
**Setup time:** 5 minutes  
**Difficulty:** Easy
