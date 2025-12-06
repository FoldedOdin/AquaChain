# Device Not Showing - Complete Troubleshooting Checklist

## Current Situation
- ✅ Devices are being registered successfully (notifications appear)
- ✅ Devices are stored in backend (dev-server shows "Loaded 3 devices")
- ❌ Devices not appearing in Consumer Dashboard (shows 0)

## Root Causes Fixed
1. ✅ API response format changed from `devices` to `data`
2. ✅ dataService now gets fresh token on each request
3. ✅ dataService checks both `aquachain_token` and `authToken`
4. ✅ Added detailed console logging

## CRITICAL: Must Do These Steps

### Step 1: Hard Refresh Browser ⚠️ MOST IMPORTANT
The updated JavaScript code needs to be loaded:

**Windows/Linux:**
```
Ctrl + Shift + R
```

**Mac:**
```
Cmd + Shift + R
```

**Or:**
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Step 2: Check Browser Console
1. Press F12 to open DevTools
2. Go to Console tab
3. Refresh the page
4. Look for these logs:

**Expected logs when loading dashboard:**
```
🌐 [makeRequest] Calling: http://localhost:3002/api/devices
🔑 [makeRequest] Auth token: Present
📡 [makeRequest] Response status: 200
📥 [makeRequest] Raw response: { success: true, data: [...], count: 3 }
✅ [makeRequest] Returning result.data: [...]
🔍 [dataService] Fetching devices from /devices
📦 [dataService] Devices received: [...]
📊 [dataService] Device count: 3
```

**If you see errors:**
- `Auth token: Missing` → Login again
- `Response status: 401` → Token expired, login again
- `Response status: 404` → Dev server not running
- `data: null` or `data: undefined` → Old code still cached

### Step 3: Verify Dev Server
Check server logs:
```bash
# Should show:
✅ Loaded 3 devices from storage
```

If not showing devices, check `.dev-data.json`:
```bash
# Look for devDevices section
```

### Step 4: Check Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Refresh page
4. Find request to `/api/devices`
5. Click on it
6. Check Response tab

**Expected response:**
```json
{
  "success": true,
  "data": [
    {
      "device_id": "Kitchen Danj",
      "user_id": "...",
      "name": "Kitchen Danj",
      "location": "...",
      "status": "active"
    },
    {
      "device_id": "Bathroom",
      "user_id": "...",
      "name": "Bathroom",
      "location": "...",
      "status": "active"
    }
  ],
  "count": 2
}
```

**If response shows `devices` instead of `data`:**
- Dev server needs restart (already done)
- Browser cache issue (do hard refresh)

## Step 5: Verify Token
In browser console, run:
```javascript
localStorage.getItem('aquachain_token')
```

Should return a long string like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

If null or undefined:
1. Logout
2. Login again
3. Check again

## Step 6: Check User ID Match
The devices must be assigned to the correct user ID.

**In browser console:**
```javascript
// Get current user
JSON.parse(localStorage.getItem('aquachain_user'))

// Should show userId like: "user-123-abc"
```

**In .dev-data.json:**
```json
{
  "devDevices": {
    "user-123-abc": [  // ← This must match the userId above
      { "device_id": "Kitchen Danj", ... }
    ]
  }
}
```

## Common Issues & Solutions

### Issue 1: Still Shows 0 Devices After Hard Refresh
**Solution:**
1. Clear all browser data:
   ```javascript
   // In console:
   localStorage.clear()
   sessionStorage.clear()
   location.reload()
   ```
2. Login again
3. Check console logs

### Issue 2: Console Shows "Auth token: Missing"
**Solution:**
1. Logout
2. Login again
3. Token should now be present

### Issue 3: Response Has `devices` Key Instead of `data`
**Solution:**
1. Verify dev-server.js line 441 has: `data: userDevices`
2. Restart dev server
3. Hard refresh browser

### Issue 4: Network Tab Shows 401 Unauthorized
**Solution:**
1. Token expired
2. Logout and login again
3. Or check if token is valid:
   ```javascript
   fetch('http://localhost:3002/api/devices', {
     headers: {
       'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
     }
   }).then(r => r.json()).then(console.log)
   ```

### Issue 5: Devices Exist But Wrong User
**Solution:**
Check which user the devices are assigned to:
1. Open `.dev-data.json`
2. Find `devDevices` section
3. Check which userId has the devices
4. Make sure you're logged in as that user

## Files Changed

### 1. frontend/src/dev-server.js (Line ~441)
```javascript
// Changed from:
res.json({ success: true, devices: userDevices, count: ... });

// To:
res.json({ success: true, data: userDevices, count: ... });
```

### 2. frontend/src/services/dataService.ts
```typescript
// Added fresh token retrieval:
const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');

// Added detailed logging:
console.log('🌐 [makeRequest] Calling:', url);
console.log('🔑 [makeRequest] Auth token:', token ? 'Present' : 'Missing');
console.log('📡 [makeRequest] Response status:', response.status);
console.log('📥 [makeRequest] Raw response:', result);
```

## Quick Test Commands

### Test 1: Check if devices exist in backend
```bash
# In .dev-data.json, search for "Kitchen Danj" or "Bathroom"
```

### Test 2: Test API directly
```javascript
// In browser console:
fetch('http://localhost:3002/api/devices', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`,
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(data => {
  console.log('Success:', data.success);
  console.log('Has data key:', 'data' in data);
  console.log('Has devices key:', 'devices' in data);
  console.log('Count:', data.count);
  console.log('Devices:', data.data || data.devices);
});
```

### Test 3: Force refresh dashboard data
```javascript
// In browser console:
window.location.reload(true);
```

## Expected Final Result

After all fixes and hard refresh:
- Consumer Dashboard shows: **Devices: 2** (or 3)
- Device cards visible with names "Kitchen Danj", "Bathroom"
- Each card shows status, location, WQI
- Console shows successful API calls with device data

## If Still Not Working

1. **Share console logs** - Copy all logs from console
2. **Share network response** - Copy response from Network tab
3. **Check .dev-data.json** - Verify devices are stored
4. **Verify user ID** - Make sure logged-in user matches device owner

## Status
- ✅ Backend fixed (response format)
- ✅ Frontend fixed (token retrieval)
- ✅ Dev server restarted
- ⚠️ **NEEDS: Hard browser refresh to load new code**
