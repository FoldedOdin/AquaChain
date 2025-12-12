# Google Maps Address Picker - Setup Guide

## Overview
Users can now select their address using an interactive Google Map, similar to Amazon's address picker. They can search for addresses, use current location, or drag a marker to the exact spot.

## Implementation Status: ✅ COMPLETE

---

## Features

### 1. Address Search with Autocomplete
- Type to search for addresses
- Real-time suggestions as you type
- Powered by Google Places Autocomplete
- Restricted to India (configurable)

### 2. Interactive Map
- Drag marker to exact location
- Click anywhere on map to set location
- Zoom in/out for precision
- Clean, minimal design

### 3. Current Location
- "Use Current Location" button
- Automatically gets GPS coordinates
- Reverse geocodes to address

### 4. Address Details
- Shows formatted address
- Displays city, state, ZIP code
- Shows exact coordinates (latitude/longitude)
- All data saved to user profile

---

## Setup Required

### Step 1: Get Google Maps API Key (5 minutes)

#### 1.1 Go to Google Cloud Console
Visit: https://console.cloud.google.com/

#### 1.2 Create/Select Project
- Click "Select a project"
- Create new project or select existing
- Name: "AquaChain" (or any name)

#### 1.3 Enable Required APIs
Go to "APIs & Services" > "Library" and enable:

1. **Maps JavaScript API**
   - Search for "Maps JavaScript API"
   - Click "Enable"

2. **Places API**
   - Search for "Places API"
   - Click "Enable"

3. **Geocoding API**
   - Search for "Geocoding API"
   - Click "Enable"

#### 1.4 Create API Key
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy your API key
4. Click "Restrict Key" (recommended)

#### 1.5 Restrict API Key (Recommended)
**Application restrictions:**
- HTTP referrers (websites)
- Add: `http://localhost:3000/*` (development)
- Add: `https://yourdomain.com/*` (production)

**API restrictions:**
- Restrict key
- Select:
  - Maps JavaScript API
  - Places API
  - Geocoding API

5. Click "Save"

---

### Step 2: Add API Key to Environment

Edit `frontend/.env`:

```env
# Google Maps Configuration
REACT_APP_GOOGLE_MAPS_API_KEY=your-api-key-here
```

**Example:**
```env
REACT_APP_GOOGLE_MAPS_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### Step 3: Restart Application

```bash
# Stop React app (Ctrl+C)
# Restart
npm start
```

---

## How It Works

### User Flow:

```
User clicks "Edit Profile"
    ↓
Clicks "Pick Address on Map"
    ↓
Map loads with current location (or default)
    ↓
User can:
  - Search for address
  - Use current location
  - Drag marker
  - Click on map
    ↓
Address details shown
    ↓
Click "Confirm Address"
    ↓
Address saved to profile
```

### Technical Flow:

```
1. Load Google Maps JavaScript API
2. Initialize map with default location (Kerala, India)
3. Create draggable marker
4. User interacts:
   - Search → Autocomplete → Geocode → Update map
   - Current location → Geolocation → Reverse geocode
   - Drag marker → Reverse geocode
   - Click map → Reverse geocode
5. Parse address components
6. Return formatted address + coordinates
7. Save to user profile
```

---

## Features in Detail

### 1. Address Search
**How it works:**
- Type at least 3 characters
- Google Places Autocomplete suggests addresses
- Click suggestion to select
- Map centers on selected location
- Marker moves to location

**Example searches:**
- "123 MG Road, Kochi"
- "Ernakulam, Kerala"
- "Cochin International Airport"

### 2. Current Location
**How it works:**
- Click "Use Current Location"
- Browser requests location permission
- Gets GPS coordinates
- Reverse geocodes to address
- Updates map and marker

**Requirements:**
- HTTPS (or localhost for testing)
- User grants location permission
- GPS/location services enabled

### 3. Drag Marker
**How it works:**
- Click and hold marker
- Drag to desired location
- Release to set
- Automatically reverse geocodes
- Updates address display

### 4. Click Map
**How it works:**
- Click anywhere on map
- Marker jumps to clicked location
- Automatically reverse geocodes
- Updates address display

---

## Address Data Structure

### What Gets Saved:

```typescript
{
  formatted: "123 MG Road, Ernakulam, Kerala 682016, India",
  street: "123 MG Road",
  city: "Ernakulam",
  state: "Kerala",
  zipCode: "682016",
  country: "India",
  latitude: 9.9312,
  longitude: 76.2673
}
```

### In User Profile:

```javascript
user.profile = {
  firstName: "John",
  lastName: "Doe",
  phone: "+91-9876543210",
  address: "123 MG Road, Ernakulam, Kerala 682016, India",
  // Coordinates stored separately if needed
  location: {
    lat: 9.9312,
    lng: 76.2673
  }
}
```

---

## Testing

### Test Checklist:

- [ ] API key added to `.env`
- [ ] App restarted
- [ ] Can open Edit Profile modal
- [ ] Can click "Pick Address on Map"
- [ ] Map loads successfully
- [ ] Can search for address
- [ ] Autocomplete suggestions appear
- [ ] Can select suggestion
- [ ] Map centers on selected address
- [ ] Can click "Use Current Location"
- [ ] Browser asks for permission
- [ ] Current location detected
- [ ] Can drag marker
- [ ] Address updates when dragging
- [ ] Can click on map
- [ ] Marker moves to clicked location
- [ ] Address details display correctly
- [ ] Can click "Confirm Address"
- [ ] Address saved to profile
- [ ] Can cancel and return to text input

---

## Troubleshooting

### Map doesn't load
**Check:**
1. API key is correct in `.env`
2. Maps JavaScript API is enabled
3. App was restarted after adding key
4. Check browser console for errors

**Common errors:**
- "InvalidKeyMapError" → Wrong API key
- "RefererNotAllowedMapError" → Add localhost to restrictions
- "ApiNotActivatedMapError" → Enable Maps JavaScript API

### Autocomplete doesn't work
**Check:**
1. Places API is enabled
2. Typing at least 3 characters
3. Internet connection
4. API key restrictions allow Places API

### Current location doesn't work
**Check:**
1. Using HTTPS or localhost
2. Browser has location permission
3. Location services enabled on device
4. Check browser console for errors

### Reverse geocoding fails
**Check:**
1. Geocoding API is enabled
2. API key restrictions allow Geocoding API
3. Internet connection
4. Check browser console for errors

---

## Cost Considerations

### Google Maps Pricing:

**Free tier (per month):**
- Maps JavaScript API: $200 credit (≈28,000 loads)
- Places Autocomplete: $200 credit (≈1,000 requests)
- Geocoding API: $200 credit (≈40,000 requests)

**For most applications:**
- Free tier is sufficient
- Monitor usage in Google Cloud Console
- Set up billing alerts

**Cost optimization:**
- Restrict API key to your domain
- Enable only required APIs
- Cache geocoding results
- Use session tokens for autocomplete

---

## Files Created/Modified

### New Files:
1. `frontend/src/components/Dashboard/AddressMapPicker.tsx` - Map picker component
2. `frontend/src/types/google-maps.d.ts` - TypeScript declarations
3. `GOOGLE_MAPS_ADDRESS_PICKER_SETUP.md` - This guide

### Modified Files:
1. `frontend/src/components/Dashboard/EditProfileModal.tsx` - Integrated map picker
2. `frontend/.env` - Added REACT_APP_GOOGLE_MAPS_API_KEY

---

## Configuration Options

### Default Location
Change in `AddressMapPicker.tsx`:
```typescript
initialLat = 10.8505,  // Kochi, Kerala
initialLng = 76.2711
```

### Country Restriction
Change in `AddressMapPicker.tsx`:
```typescript
componentRestrictions: { country: 'in' } // India
// Change to: 'us', 'uk', 'au', etc.
```

### Map Zoom Level
Change in `AddressMapPicker.tsx`:
```typescript
zoom: 15  // 1-20, higher = more zoomed in
```

### Map Style
Customize in `AddressMapPicker.tsx`:
```typescript
styles: [
  // Add custom map styles
]
```

---

## Security Best Practices

1. **Restrict API Key:**
   - Add HTTP referrer restrictions
   - Limit to required APIs only
   - Never commit API key to git

2. **Environment Variables:**
   - Use `.env` for API keys
   - Add `.env` to `.gitignore`
   - Use different keys for dev/prod

3. **Rate Limiting:**
   - Monitor API usage
   - Set up billing alerts
   - Implement client-side caching

4. **Validation:**
   - Validate address format
   - Check coordinates are reasonable
   - Sanitize user input

---

## Future Enhancements (Optional)

1. **Save Multiple Addresses:**
   - Home, work, other
   - Select from saved addresses
   - Set default address

2. **Address Validation:**
   - Verify address exists
   - Check deliverability
   - Suggest corrections

3. **Delivery Zone Check:**
   - Check if address is in service area
   - Show delivery availability
   - Estimate delivery time

4. **Street View:**
   - Show street view of location
   - Help user verify address
   - Better visualization

5. **Drawing Tools:**
   - Draw delivery area
   - Mark landmarks
   - Add notes to location

---

## Support

### Documentation:
- [Google Maps JavaScript API](https://developers.google.com/maps/documentation/javascript)
- [Places API](https://developers.google.com/maps/documentation/places/web-service)
- [Geocoding API](https://developers.google.com/maps/documentation/geocoding)

### Common Issues:
- Check Google Cloud Console for API errors
- Monitor API usage and quotas
- Review API key restrictions

---

## Summary

Users can now select their address using an interactive Google Map with:
- ✅ Address search with autocomplete
- ✅ Current location detection
- ✅ Draggable marker
- ✅ Click-to-place
- ✅ Detailed address information
- ✅ Coordinates saved

**Setup time:** 5 minutes  
**User experience:** Significantly improved  
**Accuracy:** GPS-level precision

Just add your Google Maps API key to `.env` and restart the app! 🗺️
