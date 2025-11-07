# Edit Profile Name Field Disappearing - Fix

## Issue
When editing the profile, the name fields (First Name, Last Name) would disappear after entering text and moving to another field.

## Root Cause

The `EditProfileModal` component had a `useEffect` that reset form fields whenever the modal was open OR when `currentProfile` changed:

```typescript
// ❌ BEFORE: Reset on every render
useEffect(() => {
  if (isOpen) {
    setFirstName(currentProfile.firstName || '');
    setLastName(currentProfile.lastName || '');
    setEmail(currentProfile.email || '');
    setPhone(currentProfile.phone || '');
    setAddress(currentProfile.address || '');
  }
}, [isOpen, currentProfile]); // ❌ currentProfile changes on every render
```

### Why `currentProfile` Changed on Every Render

In `ConsumerDashboard.tsx`, the `currentProfile` prop was created as an inline object:

```typescript
<EditProfileModal
  currentProfile={{  // ❌ New object created on every render
    firstName: user.profile?.firstName,
    lastName: user.profile?.lastName,
    email: user.email,
    phone: user.profile?.phone,
    address: ...
  }}
/>
```

### The Problem Flow:
1. User types in First Name field → state updates
2. Component re-renders (normal React behavior)
3. Parent component re-renders
4. New `currentProfile` object created (different reference)
5. `useEffect` detects `currentProfile` changed
6. Form fields reset to original values
7. **User's input disappears!**

## Solution

Used `useRef` to track when the modal transitions from closed to open, and only initialize form fields at that moment:

```typescript
// ✅ AFTER: Only reset when modal first opens
const prevIsOpenRef = useRef(false);

useEffect(() => {
  // Only initialize when modal transitions from closed to open
  if (isOpen && !prevIsOpenRef.current) {
    setFirstName(currentProfile.firstName || '');
    setLastName(currentProfile.lastName || '');
    setEmail(currentProfile.email || '');
    setPhone(currentProfile.phone || '');
    setAddress(currentProfile.address || '');
  }
  prevIsOpenRef.current = isOpen;
}, [isOpen, currentProfile.firstName, currentProfile.lastName, currentProfile.email, currentProfile.phone, currentProfile.address]);
```

### How It Works:

1. **Track Previous State**: `prevIsOpenRef` stores whether modal was open in previous render
2. **Detect Transition**: Only initialize when `isOpen` is `true` AND `prevIsOpenRef.current` is `false`
3. **Update Ref**: After checking, update ref to current `isOpen` state
4. **Result**: Form only initializes when modal opens, not on every render

### Benefits:
- ✅ Form fields don't reset while user is typing
- ✅ User input is preserved
- ✅ Still initializes correctly when modal opens
- ✅ Still updates if profile data changes while modal is closed

## Testing

### Test Case 1: Type in Name Field
1. Open Edit Profile modal
2. Type in First Name field
3. Click in Last Name field
4. **Expected**: First Name value is preserved ✓

### Test Case 2: Switch Between Fields
1. Type in First Name
2. Type in Last Name
3. Type in Email
4. Type in Phone
5. **Expected**: All values preserved ✓

### Test Case 3: Close and Reopen
1. Type in fields
2. Close modal (Cancel)
3. Reopen modal
4. **Expected**: Fields reset to original profile values ✓

### Test Case 4: Profile Updates
1. Open modal
2. Update profile from another tab/window
3. Close and reopen modal
4. **Expected**: Shows updated profile values ✓

## Alternative Solutions Considered

### Option 1: Memoize currentProfile (Not Chosen)
```typescript
// In ConsumerDashboard.tsx
const currentProfile = useMemo(() => ({
  firstName: user.profile?.firstName,
  lastName: user.profile?.lastName,
  email: user.email,
  phone: user.profile?.phone,
  address: ...
}), [user.profile?.firstName, user.profile?.lastName, user.email, user.profile?.phone, ...]);
```

**Why not chosen**: 
- Requires changes in parent component
- More dependencies to track
- Doesn't solve the core issue

### Option 2: Remove currentProfile from Dependencies (Not Chosen)
```typescript
useEffect(() => {
  if (isOpen) {
    // initialize fields
  }
}, [isOpen]); // ❌ Missing currentProfile - ESLint warning
```

**Why not chosen**:
- Violates React hooks rules
- Won't update if profile changes
- ESLint warning

### Option 3: Use Controlled vs Uncontrolled (Not Chosen)
Make form uncontrolled with `defaultValue` instead of `value`.

**Why not chosen**:
- Harder to validate
- Can't show real-time warnings
- Less control over form state

## Code Changes

**File**: `frontend/src/components/Dashboard/EditProfileModal.tsx`

### Added Import:
```typescript
import React, { useState, useEffect, useRef } from 'react';
```

### Modified useEffect:
```typescript
// Track if modal was just opened
const prevIsOpenRef = useRef(false);

// Update form only when modal is first opened
useEffect(() => {
  if (isOpen && !prevIsOpenRef.current) {
    setFirstName(currentProfile.firstName || '');
    setLastName(currentProfile.lastName || '');
    setEmail(currentProfile.email || '');
    setPhone(currentProfile.phone || '');
    setAddress(currentProfile.address || '');
  }
  prevIsOpenRef.current = isOpen;
}, [isOpen, currentProfile.firstName, currentProfile.lastName, currentProfile.email, currentProfile.phone, currentProfile.address]);
```

## Related Patterns

This fix uses the **"Previous Value Tracking"** pattern, useful for:

### Detecting State Transitions:
```typescript
const prevValueRef = useRef(initialValue);

useEffect(() => {
  if (value !== prevValueRef.current) {
    // Value changed - do something
  }
  prevValueRef.current = value;
}, [value]);
```

### Detecting First Render:
```typescript
const isFirstRenderRef = useRef(true);

useEffect(() => {
  if (isFirstRenderRef.current) {
    isFirstRenderRef.current = false;
    return; // Skip first render
  }
  // Run on subsequent renders
}, [dependency]);
```

### Comparing Previous Props:
```typescript
const prevPropsRef = useRef(props);

useEffect(() => {
  if (props.id !== prevPropsRef.current.id) {
    // ID changed - fetch new data
  }
  prevPropsRef.current = props;
}, [props]);
```

## Prevention

To avoid similar issues:

### 1. Be Careful with Object Dependencies
```typescript
// ❌ BAD: Object created inline
useEffect(() => {
  // ...
}, [{ prop1, prop2 }]); // New object every render

// ✅ GOOD: Depend on primitive values
useEffect(() => {
  // ...
}, [prop1, prop2]);
```

### 2. Use useMemo for Complex Objects
```typescript
const config = useMemo(() => ({
  setting1: value1,
  setting2: value2
}), [value1, value2]);
```

### 3. Track State Transitions
```typescript
// When you need to detect "just opened" or "just changed"
const prevStateRef = useRef(state);

useEffect(() => {
  if (state && !prevStateRef.current) {
    // Just transitioned to true
  }
  prevStateRef.current = state;
}, [state]);
```

## Status
✅ **Fixed** - Name fields now preserve user input while typing

---

**Date**: November 6, 2025
**Issue**: Name fields disappearing while typing
**Resolution**: Track modal open transition with useRef
**Impact**: Improved user experience, no data loss
