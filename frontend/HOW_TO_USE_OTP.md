# How to Use OTP for Profile Updates

## Quick Answer

When you update your **email** or **phone number**, the system will ask for OTP verification.

### In Development Mode:

**The OTP is automatically logged to your terminal/console!**

Look for this message in your terminal where the dev server is running:
```
📧 OTP for your-email@example.com: 123456
💡 Use this OTP to verify profile changes
```

Just copy the 6-digit code and paste it into the verification screen.

---

## Step-by-Step Guide

### Scenario 1: Updating Name or Address (No OTP Required)

1. Click **Settings** (gear icon)
2. Click **Edit Profile**
3. Update your **First Name**, **Last Name**, or **Address**
4. Click **Save Changes**
5. ✅ Profile updated immediately - no verification needed!

### Scenario 2: Updating Email or Phone (OTP Required)

1. Click **Settings** (gear icon)
2. Click **Edit Profile**
3. Update your **Email** or **Phone Number**
4. You'll see a warning: **"Verification Required"**
5. Click **Save Changes**
6. **OTP Verification Screen appears**
7. **Check your terminal** for the OTP code:
   ```
   📧 OTP for your-email@example.com: 123456
   💡 Use this OTP to verify profile changes
   ```
8. Enter the 6-digit code in the verification boxes
9. Click **Verify & Update**
10. ✅ Profile updated successfully!

---

## Where to Find the OTP

### Option 1: Terminal/Console (Primary)

Look at the terminal where you ran `npm start` or `npm run dev-server`:

```bash
🚀 AquaChain Development Server running on http://localhost:3002
...
📧 OTP for user@example.com: 456789
💡 Use this OTP to verify profile changes
```

### Option 2: Browser Console (Backup)

The OTP is also included in the API response during development:

1. Open Browser DevTools (F12)
2. Go to **Network** tab
3. Find the request to `/api/profile/request-otp`
4. Look at the **Response** tab
5. You'll see: `"devOtp": "123456"`

---

## OTP Details

### Format
- **Length**: 6 digits
- **Example**: `123456`, `789012`, `456789`
- **Valid Characters**: Numbers only (0-9)

### Expiration
- **Valid for**: 5 minutes
- **After expiration**: Request a new OTP

### Attempts
- **Maximum attempts**: 3 tries
- **After 3 failed attempts**: Must request a new OTP

### Resend
- **Cooldown**: 60 seconds between requests
- **How to resend**: Click "Resend Code" button (appears after cooldown)

---

## Common Issues

### Issue 1: "Invalid OTP"
**Cause**: Wrong code entered
**Solution**: 
- Check the terminal for the correct code
- Make sure you're using the most recent OTP
- Try copying and pasting instead of typing

### Issue 2: "OTP Expired"
**Cause**: More than 5 minutes passed
**Solution**: 
- Click "Resend Code"
- Check terminal for new OTP
- Enter the new code

### Issue 3: "Too Many Failed Attempts"
**Cause**: Entered wrong code 3 times
**Solution**: 
- Click "Resend Code"
- Get fresh OTP from terminal
- Be careful entering the new code

### Issue 4: "Can't Find OTP in Terminal"
**Solution**: 
1. Scroll up in your terminal
2. Look for the 📧 emoji
3. Or check Browser DevTools → Network → Response

---

## Testing Examples

### Test 1: Update Email
```
Current Email: user@example.com
New Email: newemail@example.com

Steps:
1. Edit Profile
2. Change email to newemail@example.com
3. Save Changes
4. Check terminal: 📧 OTP for user@example.com: 123456
5. Enter: 1 2 3 4 5 6
6. Verify & Update
7. ✅ Email changed!
```

### Test 2: Update Phone
```
Current Phone: +1234567890
New Phone: +9876543210

Steps:
1. Edit Profile
2. Change phone to +9876543210
3. Save Changes
4. Check terminal: 📧 OTP for user@example.com: 789012
5. Enter: 7 8 9 0 1 2
6. Verify & Update
7. ✅ Phone changed!
```

### Test 3: Update Both Email and Phone
```
Steps:
1. Edit Profile
2. Change both email and phone
3. Save Changes
4. Check terminal: 📧 OTP for user@example.com: 456789
5. Enter: 4 5 6 7 8 9
6. Verify & Update
7. ✅ Both changed!
```

---

## Production vs Development

### Development Mode (Current)
- ✅ OTP logged to terminal
- ✅ OTP included in API response
- ✅ Easy testing
- ✅ No email service needed

### Production Mode (Future)
- 📧 OTP sent to user's email
- ❌ Not logged to console
- ❌ Not in API response
- ✅ Real email service (AWS SES, SendGrid, etc.)

---

## Quick Reference

| Action | OTP Required? | Where to Find OTP |
|--------|---------------|-------------------|
| Update Name | ❌ No | N/A |
| Update Address | ❌ No | N/A |
| Update Email | ✅ Yes | Terminal/Console |
| Update Phone | ✅ Yes | Terminal/Console |
| Update Email + Phone | ✅ Yes | Terminal/Console |

---

## Tips

### Tip 1: Keep Terminal Visible
Keep your terminal window visible while testing so you can easily see the OTP.

### Tip 2: Copy-Paste
Copy the OTP from terminal and paste it into the verification boxes for accuracy.

### Tip 3: Test Different Scenarios
Try updating:
- Just name (no OTP)
- Just email (OTP required)
- Just phone (OTP required)
- Multiple fields (OTP if email/phone changed)

### Tip 4: Check Expiration
OTPs expire after 5 minutes. If you wait too long, request a new one.

### Tip 5: Use Browser DevTools
If you can't see the terminal, check Browser DevTools → Network tab for the OTP in the API response.

---

## Example Terminal Output

```bash
$ npm run dev-server

> aquachain-frontend@0.1.0 dev-server
> node src/dev-server.js

🚀 AquaChain Development Server running on http://localhost:3002
📊 RUM endpoint: http://localhost:3002/api/rum
🔍 Health check: http://localhost:3002/api/health
📈 Analytics: http://localhost:3002/api/analytics
🔌 WebSocket: ws://localhost:3002/ws

👥 Demo users available:
   - demo@aquachain.com / demo123 (Admin)
   - tech@aquachain.com / demo123 (Technician)
   - user@aquachain.com / demo123 (Consumer)

[User updates profile with new email]

📧 OTP for user@aquachain.com: 123456
💡 Use this OTP to verify profile changes

[User enters OTP and verifies]

✅ Profile updated for user@aquachain.com
```

---

## Need Help?

If you're still having trouble:
1. Check the terminal is running
2. Verify you're logged in
3. Make sure you're changing email or phone (not just name)
4. Look for the 📧 emoji in terminal
5. Try the Browser DevTools method

**Still stuck?** Check the [Profile Edit Guide](../docs/PROFILE_EDIT_GUIDE.md) for more details.

---

**Last Updated**: November 6, 2025
**Mode**: Development
**OTP Location**: Terminal/Console
