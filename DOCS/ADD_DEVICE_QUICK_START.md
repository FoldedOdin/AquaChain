# Add Device - Quick Start Guide

## For End Users

### Step 1: Prepare Your Device

Before registering your device in the AquaChain dashboard:

1. **Power on your ESP32 device**
2. **Connect it to your computer via USB**
3. **Open Serial Monitor** (115200 baud rate)
4. **Note down the Device ID** displayed (e.g., `ESP32-ABC123`)
5. **Note the Pairing Code** if shown (optional security feature)

### Step 2: Register in Dashboard

1. **Login** to your AquaChain account
2. **Navigate** to Consumer Dashboard
3. **Click** "Add Your Device" button (in the Devices card)
4. **Fill in the form**:
   - **Device ID**: Enter the ID from your device (required)
   - **Device Name**: Give it a friendly name like "Kitchen Filter" (optional)
   - **Location**: Where it's installed, e.g., "Kitchen Tap" (optional)
   - **Water Source Type**: Select Household/Industrial/Agricultural (optional)
   - **Pairing Code**: Enter if your device displays one (optional)
5. **Click** "Register Device"

### Step 3: Download Credentials

After successful registration:

1. **Download** the device credentials (certificate and private key)
2. **Save** them securely - you'll need them to configure your device
3. **Note** the IoT endpoint URL provided

### Step 4: Configure Your Device

#### Option A: Manual Configuration (via Serial)
```
1. Open Serial Monitor
2. Send command: CONFIG_MODE
3. Paste certificate when prompted
4. Paste private key when prompted
5. Enter IoT endpoint URL
6. Device will restart and connect
```

#### Option B: Flash via USB
```
1. Use ESP32 flash tool
2. Upload credentials file
3. Device will auto-configure
```

#### Option C: QR Code (if supported)
```
1. Device displays QR code scanner
2. Scan QR code from dashboard
3. Device auto-configures
```

### Step 5: Verify Connection

1. **Check dashboard** - device should appear in your devices list
2. **Wait 1-2 minutes** for first data transmission
3. **Verify** water quality data appears in dashboard
4. **Check** device status shows "Online"

## Troubleshooting

### Device Not Appearing?
- Wait 2-3 minutes after registration
- Refresh the dashboard page
- Check device is powered on
- Verify WiFi connection on device

### Registration Failed?
- Ensure Device ID is correct
- Check you're logged in
- Try a different Device ID
- Contact support if issue persists

### Device Shows Offline?
- Check device power
- Verify WiFi credentials
- Ensure credentials were flashed correctly
- Check IoT endpoint URL is correct

### No Data Showing?
- Wait 5 minutes for first reading
- Check device sensors are connected
- Verify MQTT topics are correct
- Check device logs in Serial Monitor

## What Happens Next?

Once your device is registered and connected:

✅ **Real-time monitoring** begins immediately
✅ **Water quality data** updates every minute
✅ **Alerts** sent for quality issues
✅ **Historical data** tracked for analysis
✅ **Reports** available for download

## Need Help?

- 📖 [Full Documentation](./ADD_DEVICE_GUIDE.md)
- 🔧 [Technical Guide](./DEVICE_TECHNICAL_GUIDE.md)
- 💬 [Community Forum](https://community.aquachain.com)
- 📧 [Support Email](mailto:support@aquachain.com)

## Video Tutorial

🎥 Watch our step-by-step video guide: [Add Device Tutorial](https://youtube.com/aquachain-add-device)

---

**Estimated Time**: 5-10 minutes
**Difficulty**: Easy
**Requirements**: ESP32 device, USB cable, WiFi connection
