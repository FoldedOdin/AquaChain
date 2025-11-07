# Add Device Feature Guide

## Overview

The "Add Device" functionality allows users to register their physical IoT devices (ESP32) to their AquaChain account securely. Once registered, devices can send water quality data via MQTT to AWS IoT Core.

## User Flow

### 1. Access the Feature

Users can access the "Add Device" feature from:
- **Consumer Dashboard**: Click the "Add Your Device" button in the Devices card (shown when no devices are registered)
- The button opens a modal dialog for device registration

### 2. Device Registration Form

The registration form collects the following information:

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| **Device ID** | ✅ Yes | Unique hardware ID from ESP32 | `ESP32-ABC123` |
| **Device Name** | ❌ Optional | Friendly name for display | `Kitchen Filter` |
| **Location** | ❌ Optional | Where the device is installed | `Home - Kitchen Tap` |
| **Water Source Type** | ❌ Optional | Type of water source | `Household`, `Industrial`, `Agricultural` |
| **Pairing Code** | ❌ Optional | Security code from device | `F9G7A3` |

### 3. Backend Processing

When a user submits the form:

1. **Frontend** sends a POST request to `/api/devices/register`
2. **Backend** (Lambda or Dev Server):
   - Validates the device ID
   - Checks if device already exists
   - Creates an IoT Thing in AWS IoT Core
   - Generates device certificates and keys
   - Attaches IoT policy to certificate
   - Stores device information in DynamoDB
3. **Response** includes:
   - Device registration confirmation
   - IoT credentials (for device provisioning)
   - IoT endpoint URL

### 4. Device Provisioning

After registration, the device needs to be provisioned with credentials:

```json
{
  "certificate_pem": "-----BEGIN CERTIFICATE-----...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----...",
  "iot_endpoint": "xxxxx-ats.iot.ap-south-1.amazonaws.com"
}
```

These credentials should be:
- Downloaded by the user
- Flashed to the ESP32 device
- Used for MQTT authentication

## Technical Implementation

### Frontend Components

#### AddDeviceModal Component
Location: `frontend/src/components/Dashboard/AddDeviceModal.tsx`

Features:
- Form validation
- Loading states
- Success/error feedback
- Responsive design
- Accessibility compliant

#### Device Service
Location: `frontend/src/services/deviceService.ts`

Methods:
- `registerDevice(data)` - Register new device
- `getDevices()` - Get all user devices
- `getDeviceById(id)` - Get single device
- `updateDevice(id, updates)` - Update device info
- `deleteDevice(id)` - Remove device

### Backend Endpoints

#### Development Server
Location: `frontend/src/dev-server.js`

Endpoints:
- `POST /api/devices/register` - Register device
- `GET /api/devices` - Get user's devices
- `GET /api/devices/:deviceId` - Get single device
- `PUT /api/devices/:deviceId` - Update device
- `DELETE /api/devices/:deviceId` - Delete device

#### Production Lambda Functions
Location: `lambda/device_management/`

Functions:
- `register_device_handler.py` - Device registration
- `get_devices_handler.py` - Retrieve devices
- `handler.py` - Device management operations

### Database Schema

#### DynamoDB Table: `AquaChain-Devices`

```json
{
  "device_id": "ESP32-ABC123",           // Partition Key
  "user_id": "us-east-1:xxx",            // GSI Partition Key
  "name": "Kitchen Filter",
  "location": "Home - Kitchen Tap",
  "water_source_type": "household",
  "status": "active",
  "created_at": "2025-11-06T12:30:00Z",
  "updated_at": "2025-11-06T12:30:00Z",
  "iot_thing_name": "aquachain-ESP32-ABC123",
  "certificate_arn": "arn:aws:iot:...",
  "pairing_code": "F9G7A3",
  "last_reading": "2025-11-06T13:00:00Z"
}
```

#### Global Secondary Index: `UserIdIndex`
- Partition Key: `user_id`
- Allows efficient querying of all devices for a user

### AWS IoT Core Integration

#### IoT Thing Creation

```python
iot_client.create_thing(
    thingName='aquachain-ESP32-ABC123',
    attributePayload={
        'attributes': {
            'device_id': 'ESP32-ABC123',
            'user_id': 'us-east-1:xxx',
            'location': 'Kitchen Tap',
            'water_source_type': 'household'
        }
    }
)
```

#### Certificate Generation

```python
cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
certificate_arn = cert_response['certificateArn']
certificate_pem = cert_response['certificatePem']
private_key = cert_response['keyPair']['PrivateKey']
```

#### Policy Attachment

```python
iot_client.attach_policy(
    policyName='AquaChainDevicePolicy',
    target=certificate_arn
)

iot_client.attach_thing_principal(
    thingName='aquachain-ESP32-ABC123',
    principal=certificate_arn
)
```

## ESP32 Device Side

### Device Boot Sequence

1. **First Boot**:
   - Display Device ID on OLED/Serial Monitor
   - Generate and display Pairing Code
   - Wait for user registration

2. **After Registration**:
   - User downloads credentials
   - Flash credentials to device via USB/OTA
   - Device connects to AWS IoT Core
   - Begin sending water quality data

### MQTT Topics

```
// Publish water quality data
aquachain/devices/{device_id}/data

// Subscribe to commands
aquachain/devices/{device_id}/commands

// Device status updates
aquachain/devices/{device_id}/status
```

### Sample ESP32 Code

```cpp
#include <WiFi.h>
#include <PubSubClient.h>

const char* deviceId = "ESP32-ABC123";
const char* mqttServer = "xxxxx-ats.iot.ap-south-1.amazonaws.com";
const int mqttPort = 8883;

void setup() {
  Serial.begin(115200);
  
  // Display device ID for registration
  Serial.println("Device ID: " + String(deviceId));
  Serial.println("Register this device in AquaChain dashboard");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  
  // Connect to AWS IoT Core
  // ... (with certificates)
}

void loop() {
  // Read sensors
  float pH = readPH();
  float turbidity = readTurbidity();
  float tds = readTDS();
  float temperature = readTemperature();
  
  // Publish to MQTT
  String payload = "{\"pH\":" + String(pH) + 
                   ",\"turbidity\":" + String(turbidity) +
                   ",\"tds\":" + String(tds) +
                   ",\"temperature\":" + String(temperature) + "}";
  
  client.publish("aquachain/devices/" + String(deviceId) + "/data", payload.c_str());
  
  delay(60000); // Send every minute
}
```

## Security Considerations

### Authentication
- Users must be authenticated to register devices
- JWT tokens validate user identity
- Device IDs must be unique per user

### Authorization
- Users can only register devices to their own account
- Users can only view/manage their own devices
- Admin users can view all devices

### Device Security
- Each device gets unique X.509 certificates
- Private keys never stored in database
- Certificates can be rotated
- Devices use TLS 1.2+ for MQTT

### Pairing Code (Optional)
- Adds extra security layer
- Prevents unauthorized device registration
- Code displayed on device screen
- User must enter code during registration

## Testing

### Development Mode

1. Start the dev server:
```bash
cd frontend
npm run dev-server
```

2. Login to dashboard
3. Click "Add Your Device"
4. Fill in the form:
   - Device ID: `TEST-ESP32-001`
   - Name: `Test Device`
   - Location: `Test Lab`
5. Submit and verify success

### Production Testing

1. Deploy Lambda functions
2. Create DynamoDB table with GSI
3. Set up IoT Core policy
4. Test device registration via API
5. Verify IoT Thing creation
6. Test certificate generation
7. Verify device can connect via MQTT

## Troubleshooting

### Common Issues

**Issue**: "Device already exists"
- **Solution**: Device ID must be unique. Use a different ID or delete the existing device.

**Issue**: "Authentication required"
- **Solution**: Ensure user is logged in and token is valid.

**Issue**: "Failed to create IoT Thing"
- **Solution**: Check AWS IoT Core permissions and quotas.

**Issue**: "Certificate generation failed"
- **Solution**: Verify IoT policy exists and has correct permissions.

### Debug Mode

Enable debug logging:
```bash
# Frontend
localStorage.setItem('debug', 'aquachain:*');

# Backend
export DEBUG=true
```

## Future Enhancements

### Auto-Provisioning
- QR code generation with credentials
- Device scans QR code to auto-configure
- No manual credential flashing needed

### Bulk Registration
- Register multiple devices at once
- CSV import for device list
- Useful for industrial deployments

### Device Groups
- Organize devices by location/type
- Group-level settings and alerts
- Hierarchical device management

### Device Health Monitoring
- Battery level tracking
- Signal strength monitoring
- Automatic offline alerts
- Predictive maintenance

### OTA Updates
- Push firmware updates to devices
- Scheduled update windows
- Rollback capability
- Update status tracking

## Related Documentation

- [IoT Simulator Guide](../iot-simulator/README.md)
- [MQTT Integration](./MQTT_INTEGRATION.md)
- [Device Management API](./API_DOCUMENTATION.md)
- [Security Best Practices](./SECURITY_GUIDE.md)

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [GitHub Issues](https://github.com/aquachain/issues)
- Contact support: support@aquachain.com
