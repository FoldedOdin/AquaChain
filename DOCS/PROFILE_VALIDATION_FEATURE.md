# Profile Validation Before Device Request

## Overview
Users must complete their profile (address and phone number) before they can request a device.

## Implementation Status: ✅ COMPLETE

---

## Features Implemented

### 1. Profile Completeness Check
**Location:** `frontend/src/components/Dashboard/ConsumerDashboard.tsx`

**Validation:**
- Checks if user has **address** (string or object with street/city)
- Checks if user has **phone number**
- Both fields must be non-empty

**Code:**
```typescript
const isProfileComplete = useMemo(() => {
  const address = user?.profile?.address;
  const hasAddress = address && 
    (typeof address === 'string' ? (address as string).trim().length > 0 : 
     !!(address as any)?.street && !!(address as any)?.city);
  const phone = user?.profile?.phone;
  const hasPhone = phone && typeof phone === 'string' && (phone as string).trim().length > 0;
  return !!(hasAddress && hasPhone);
}, [user]);
```

---

### 2. Request Device Button Validation
**Behavior:**
- If profile is **complete**: Opens device request modal
- If profile is **incomplete**: Shows confirmation dialog

**Confirmation Dialog:**
```
Please complete your profile before requesting a device.

Missing: address and phone number

Would you like to update your profile now?
```

**Actions:**
- **OK**: Opens settings and profile edit modal
- **Cancel**: Closes dialog, stays on dashboard

---

### 3. Visual Indicator on Button
**Complete Profile:**
- Blue border and icon
- Normal hover effect (blue)
- Text: "Request Device"

**Incomplete Profile:**
- Amber/yellow border and background
- Amber icon
- Warning text: "Complete profile first" with warning icon
- Hover effect: Darker amber

**Visual Comparison:**
```
Complete:
┌─────────────────────────┐
│ + Request Device        │  (Blue)
└─────────────────────────┘

Incomplete:
┌─────────────────────────┐
│ + Request Device        │  (Amber background)
│   ⚠ Complete profile    │
│     first               │
└─────────────────────────┘
```

---

## User Flow

### Scenario 1: Complete Profile
```
User clicks "Request Device"
    ↓
Profile check: ✅ Has address and phone
    ↓
Opens Request Device Modal
    ↓
User fills form and submits
    ↓
Order created
```

### Scenario 2: Incomplete Profile
```
User clicks "Request Device"
    ↓
Profile check: ❌ Missing address or phone
    ↓
Shows confirmation dialog
    ↓
User clicks "OK"
    ↓
Opens Settings page
    ↓
Opens Edit Profile modal
    ↓
User fills address and phone
    ↓
Saves profile
    ↓
Can now request device
```

---

## Required Profile Fields

### Address
**Accepted formats:**
1. **String:** Any non-empty string
   ```typescript
   profile: {
     address: "123 Main St, City, State 12345"
   }
   ```

2. **Object:** Must have `street` and `city`
   ```typescript
   profile: {
     address: {
       street: "123 Main St",
       city: "City Name",
       state: "State",
       zipCode: "12345"
     }
   }
   ```

### Phone Number
**Format:** Any non-empty string
```typescript
profile: {
  phone: "+1-234-567-8900"
}
```

---

## Testing

### Test Case 1: New User (No Profile)
1. Login as new user
2. Go to dashboard
3. Notice "Request Device" button has amber background
4. Click button
5. Should see: "Missing: address and phone number"
6. Click "OK"
7. Should open profile edit modal
8. Fill address and phone
9. Save
10. Button should turn blue
11. Click button again
12. Should open device request modal ✅

### Test Case 2: Partial Profile (Only Address)
1. User has address but no phone
2. Click "Request Device"
3. Should see: "Missing: phone number"
4. Complete phone number
5. Can now request device ✅

### Test Case 3: Partial Profile (Only Phone)
1. User has phone but no address
2. Click "Request Device"
3. Should see: "Missing: address"
4. Complete address
5. Can now request device ✅

### Test Case 4: Complete Profile
1. User has both address and phone
2. Button shows blue (normal)
3. Click button
4. Opens device request modal immediately ✅

---

## Code Changes

### File Modified:
`frontend/src/components/Dashboard/ConsumerDashboard.tsx`

### Changes Made:

#### 1. Added Profile Completeness Check
```typescript
const isProfileComplete = useMemo(() => {
  // Check address and phone
  return !!(hasAddress && hasPhone);
}, [user]);
```

#### 2. Updated toggleRequestDevice Function
```typescript
const toggleRequestDevice = useCallback(() => {
  if (!isProfileComplete) {
    // Show confirmation and redirect to profile
    if (window.confirm(message)) {
      setShowSettings(true);
      setShowEditProfile(true);
    }
    return;
  }
  setShowRequestDevice(prev => !prev);
}, [user, isProfileComplete]);
```

#### 3. Updated Button UI
```typescript
<button 
  onClick={toggleRequestDevice}
  className={`relative flex items-center space-x-3 p-4 border-2 rounded-lg transition ${
    isProfileComplete 
      ? 'border-gray-200 hover:border-blue-500 hover:bg-blue-50' 
      : 'border-amber-200 bg-amber-50 hover:border-amber-400'
  }`}
>
  <Plus className={`w-6 h-6 ${isProfileComplete ? 'text-blue-600' : 'text-amber-600'}`} />
  <div className="flex flex-col items-start">
    <span className="font-medium text-gray-700">Request Device</span>
    {!isProfileComplete && (
      <span className="text-xs text-amber-600 flex items-center gap-1">
        <AlertTriangle className="w-3 h-3" />
        Complete profile first
      </span>
    )}
  </div>
</button>
```

---

## Benefits

### For Users:
- ✅ Clear indication of what's needed
- ✅ Direct path to complete profile
- ✅ Prevents incomplete orders
- ✅ Better user experience

### For Business:
- ✅ Ensures all orders have delivery information
- ✅ Reduces failed deliveries
- ✅ Improves data quality
- ✅ Better customer communication

---

## Edge Cases Handled

1. **Empty strings:** Trimmed and checked for length
2. **Null/undefined:** Safely handled with optional chaining
3. **Address as string:** Supported
4. **Address as object:** Supported (checks for street and city)
5. **Phone format:** Any non-empty string accepted
6. **User cancels dialog:** No action taken, stays on dashboard

---

## Future Enhancements (Optional)

1. **Inline validation:** Show missing fields directly on button hover
2. **Profile completion progress:** Show percentage complete
3. **Email verification:** Require verified email before device request
4. **Address validation:** Validate address format/existence
5. **Phone validation:** Validate phone number format
6. **Auto-fill:** Pre-fill address from previous orders
7. **Multiple addresses:** Let user choose delivery address

---

## Related Features

- **Edit Profile Modal:** Where users update their information
- **Request Device Modal:** The modal that opens after validation
- **Settings Page:** Contains profile edit functionality
- **User Profile:** Stores address and phone information

---

## Summary

Users must now complete their profile (address and phone number) before requesting a device. The system provides clear visual indicators and helpful guidance to complete the profile. This ensures all device orders have the necessary delivery information.

**Status:** ✅ Complete and Working  
**User Experience:** Improved  
**Data Quality:** Enhanced
