# 🧪 Authentication Flow Test Guide

## Quick Manual Testing Checklist

### 1. Auth Modal Test

**Steps:**
1. Navigate to landing page: `http://localhost:3000`
2. Click "Get Started" button
3. Verify modal opens with Login tab active
4. Click "Sign Up" tab
5. Verify tab switches smoothly
6. Click X button or press ESC
7. Verify modal closes

**Expected Results:**
- ✅ Modal opens smoothly with animation
- ✅ Tabs switch without page reload
- ✅ Modal closes on X or ESC
- ✅ Background is blurred when modal open

---

### 2. Login Form Test

**Steps:**
1. Open auth modal
2. Enter email: `test@example.com`
3. Enter password: `Test123!`
4. Check "Remember me"
5. Click "Sign In"

**Expected Results:**
- ✅ Form validates email format
- ✅ Password can be shown/hidden
- ✅ Submit button shows loading state
- ✅ Success redirects to dashboard
- ✅ Error shows user-friendly message

---

### 3. Signup Form Test

**Steps:**
1. Open auth modal
2. Click "Sign Up" tab
3. Fill in all fields:
   - Name: `John Doe`
   - Email: `john@example.com`
   - Password: `SecurePass123!`
   - Confirm: `SecurePass123!`
4. Select role: Consumer
5. Check "Accept Terms"
6. Click "Sign Up"

**Expected Results:**
- ✅ Password strength indicator shows
- ✅ Passwords must match
- ✅ Terms must be accepted
- ✅ Success shows verification message
- ✅ Email verification component appears

---

### 4. Password Reset Test

**Steps:**
1. Open auth modal (Login tab)
2. Click "Forgot your password?"
3. Enter email: `test@example.com`
4. Click "Send Reset Code"
5. Enter verification code: `123456`
6. Enter new password: `NewPass123!`
7. Confirm password: `NewPass123!`
8. Click "Reset Password"

**Expected Results:**
- ✅ Reset modal opens
- ✅ Email validation works
- ✅ Code sent confirmation shows
- ✅ Verification step appears
- ✅ Password validation works
- ✅ Success message displays
- ✅ Can close and return to login

---

### 5. Resend Code Test

**Steps:**
1. In password reset flow (step 2)
2. Click "Didn't receive the code? Resend"
3. Wait for confirmation

**Expected Results:**
- ✅ Shows "Code resent" message
- ✅ Button disabled during request
- ✅ Success feedback appears

---

### 6. Error Handling Test

**Test Invalid Email:**
1. Enter: `invalid-email`
2. Try to submit

**Expected:** ✅ Shows "Please enter a valid email"

**Test Weak Password:**
1. Enter: `123`
2. Check strength indicator

**Expected:** ✅ Shows "weak" with red indicator

**Test Password Mismatch:**
1. Password: `Test123!`
2. Confirm: `Different123!`
3. Try to submit

**Expected:** ✅ Shows "Passwords do not match"

---

### 7. Accessibility Test

**Keyboard Navigation:**
1. Press TAB to navigate through form
2. Press ENTER to submit
3. Press ESC to close modal

**Expected Results:**
- ✅ Focus visible on all elements
- ✅ Tab order is logical
- ✅ Enter submits forms
- ✅ ESC closes modals

**Screen Reader:**
1. Enable screen reader
2. Navigate through form

**Expected Results:**
- ✅ All labels read correctly
- ✅ Error messages announced
- ✅ Button states announced

---

### 8. Loading States Test

**Steps:**
1. Submit any form
2. Observe button during submission

**Expected Results:**
- ✅ Button shows spinner
- ✅ Button text changes to "Loading..."
- ✅ Button is disabled
- ✅ Form inputs disabled
- ✅ Modal cannot be closed

---

### 9. Google OAuth Test

**Steps:**
1. Open auth modal
2. Click "Continue with Google"
3. Follow OAuth flow

**Expected Results:**
- ✅ Redirects to Google
- ✅ Returns to app after auth
- ✅ User logged in
- ✅ Redirects to dashboard

---

### 10. Mobile Responsive Test

**Steps:**
1. Open DevTools
2. Switch to mobile view (375px)
3. Test all flows

**Expected Results:**
- ✅ Modal fits screen
- ✅ Forms are readable
- ✅ Buttons are tappable
- ✅ No horizontal scroll

---

## 🐛 Common Issues & Solutions

### Issue: Modal doesn't open
**Solution:** Check console for errors, verify AuthModalComponent import

### Issue: Password reset doesn't work
**Solution:** Check AWS Cognito configuration in production

### Issue: Form validation not working
**Solution:** Verify security utils are imported correctly

### Issue: Styles not applied
**Solution:** Ensure Tailwind CSS is configured and Headless UI installed

---

## 📊 Test Results Template

```
Date: ___________
Tester: ___________

[ ] Auth Modal Opens/Closes
[ ] Login Form Submits
[ ] Signup Form Submits
[ ] Password Reset Flow
[ ] Resend Code Works
[ ] Error Handling
[ ] Accessibility
[ ] Loading States
[ ] Google OAuth
[ ] Mobile Responsive

Issues Found: ___________
Status: PASS / FAIL
```

---

## 🚀 Automated Test Commands

```bash
# Run all tests
npm test

# Run specific test file
npm test AuthModal.test.tsx

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

---

## ✅ Success Criteria

All tests must pass with:
- ✅ No console errors
- ✅ Smooth animations
- ✅ Proper error messages
- ✅ Successful API calls
- ✅ Correct redirects
- ✅ Accessible to all users

---

**Happy Testing!** 🎉
