# Edit Profile Modal - Debug Guide

## Issue
Edit Profile button doesn't open the modal when clicked.

## Debugging Steps

### 1. Check Browser Console
Open browser DevTools (F12) and check the Console tab for:
- "Toggle Edit Profile clicked, current state: false"
- "Setting showEditProfile from false to true"
- "EditProfileModal render - isOpen: true"

### 2. Check React DevTools
1. Install React DevTools extension
2. Open DevTools → Components tab
3. Find ConsumerDashboard component
4. Check state: `showEditProfile` should change from `false` to `true` when button clicked

### 3. Verify Import
Check that EditProfileModal is properly imported:
```typescript
import EditProfileModal from './EditProfileModal';
```

### 4. Check Modal Rendering
The modal should be rendered at the end of ConsumerDashboard:
```tsx
<EditProfileModal
  isOpen={showEditProfile}
  onClose={toggleEditProfile}
  currentProfile={{...}}
  onProfileUpdated={handleProfileUpdated}
/>
```

### 5. Verify Button Click Handler
The button should have:
```tsx
<button onClick={toggleEditProfile}>
  Edit Profile
</button>
```

## Common Issues

### Issue 1: Modal Not Imported
**Symptom**: Console error "EditProfileModal is not defined"
**Solution**: Add import at top of ConsumerDashboard.tsx

### Issue 2: State Not Updating
**Symptom**: Console shows click but state doesn't change
**Solution**: Check useState declaration and toggleEditProfile function

### Issue 3: Modal Renders But Not Visible
**Symptom**: Modal renders but nothing appears on screen
**Solution**: Check z-index and positioning in EditProfileModal.tsx

### Issue 4: React Not Re-rendering
**Symptom**: State changes but UI doesn't update
**Solution**: Restart dev server

## Quick Fix Steps

1. **Restart Dev Server**
   ```bash
   # Stop current server (Ctrl+C)
   cd frontend
   npm start
   ```

2. **Clear Browser Cache**
   - Press Ctrl+Shift+Delete
   - Clear cached images and files
   - Reload page (Ctrl+F5)

3. **Check File Saved**
   - Ensure ConsumerDashboard.tsx is saved
   - Ensure EditProfileModal.tsx is saved
   - Check for any unsaved changes indicator

4. **Verify Build**
   ```bash
   cd frontend
   npm run build
   ```
   Check for any compilation errors

## Testing the Modal

### Manual Test
1. Login to dashboard
2. Click Settings icon (gear icon)
3. Look for "Edit Profile" button in Profile Information section
4. Click "Edit Profile" button
5. Modal should appear with form

### Expected Behavior
- Modal slides in from center
- Background darkens (overlay)
- Form shows current profile data
- Can edit fields
- Can close with X button or Cancel

## Console Commands for Testing

Open browser console and run:

```javascript
// Check if component is mounted
document.querySelector('[class*="EditProfileModal"]')

// Check if modal is in DOM
document.querySelector('.fixed.inset-0')

// Manually trigger modal (for testing)
// Find the button and click it programmatically
document.querySelector('button').click()
```

## If Still Not Working

1. **Check React Version**
   ```bash
   cd frontend
   npm list react react-dom
   ```
   Should be React 18+

2. **Reinstall Dependencies**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm start
   ```

3. **Check for Conflicting CSS**
   - Open DevTools → Elements
   - Find the modal element
   - Check computed styles
   - Look for `display: none` or `visibility: hidden`

4. **Verify Modal Structure**
   The modal should have:
   - `position: fixed`
   - `inset: 0` (covers full screen)
   - `z-index: 50` (appears on top)
   - Background overlay with opacity

## Success Indicators

When working correctly, you should see:
1. ✅ Button click triggers console logs
2. ✅ State changes in React DevTools
3. ✅ Modal appears with animation
4. ✅ Background darkens
5. ✅ Form is interactive
6. ✅ Can close modal

## Contact Support

If issue persists after all debugging steps:
1. Take screenshot of browser console
2. Take screenshot of React DevTools
3. Note any error messages
4. Report issue with details
