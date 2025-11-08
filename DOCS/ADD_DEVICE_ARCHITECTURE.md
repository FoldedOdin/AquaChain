# Add Device Feature - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Consumer Dashboard                               │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │  Devices Card                                          │ │  │
│  │  │  ┌──────────────────────────────────────────────────┐ │ │  │
│  │  │  │  Active Devices: 0                               │ │ │  │
│  │  │  │  ┌────────────────────────────────────────────┐ │ │ │  │
│  │  │  │  │  [+] Add Your Device                       │ │ │ │  │
│  │  │  │  └────────────────────────────────────────────┘ │ │ │  │
│  │  │  └──────────────────────────────────────────────────┘ │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Click
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AddDeviceModal Component                        │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Register New Device                                          │  │
│  │  ─────────────────────────────────────────────────────────── │  │
│  │                                                               │  │
│  │  Device ID *:        [ESP32-ABC123____________]              │  │
│  │  Device Name:        [Kitchen Filter__________]              │  │
│  │  Location:           [Home - Kitchen Tap______]              │  │
│  │  Water Source Type:  [Household ▼]                           │  │
│  │  Pairing Code:       [F9G7A3___________________]             │  │
│  │                                                               │  │
│  │  [Cancel]                          [Register Device]         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Submit
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Device Service Layer                           │
│                                                                       │
│  deviceService.registerDevice({                                     │
│    device_id: "ESP32-ABC123",                                       │
│    name: "Kitchen Filter",                                          │
│    location: "Kitchen Tap",                                         │
│    water_source_type: "household",                                  │
│    pairing_code: "F9G7A3"                                           │
│  })                                                                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP POST
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                  │
│                                                                       │
│  POST /api/devices/register                                         │
│  Headers:                                                            │
│    Authorization: Bearer <JWT_TOKEN>                                │
│    Content-Type: application/json                                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
    ┌───────────────────────┐       ┌───────────────────────┐
    │  Development Server   │       │  Production Lambda    │
    │  (dev-server.js)      │       │  (register_device)    │
    └───────────┬───────────┘       └───────────┬───────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend Processing                              │
│                                                                       │
│  1. Validate JWT Token                                              │
│  2. Extract User ID                                                  │
│  3. Validate Device ID                                              │
│  4. Check for Duplicates                                            │
│  5. Create IoT Thing                                                │
│  6. Generate Certificates                                           │
│  7. Attach IoT Policy                                               │
│  8. Store in Database                                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  AWS IoT Core    │ │  DynamoDB    │ │  Certificate     │
    │                  │ │              │ │  Manager         │
    │  Create Thing:   │ │  Store:      │ │                  │
    │  aquachain-      │ │  - device_id │ │  Generate:       │
    │  ESP32-ABC123    │ │  - user_id   │ │  - X.509 cert    │
    │                  │ │  - name      │ │  - Private key   │
    │  Attach:         │ │  - location  │ │  - Public key    │
    │  - Certificate   │ │  - status    │ │                  │
    │  - Policy        │ │  - metadata  │ │  Attach Policy   │
    └──────────────────┘ └──────────────┘ └──────────────────┘
                │               │               │
                └───────────────┼───────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Response                                     │
│                                                                       │
│  {                                                                   │
│    "success": true,                                                  │
│    "message": "Device registered successfully",                     │
│    "device": {                                                       │
│      "device_id": "ESP32-ABC123",                                   │
│      "user_id": "us-east-1:xxx",                                    │
│      "name": "Kitchen Filter",                                      │
│      "status": "active",                                            │
│      "iot_thing_name": "aquachain-ESP32-ABC123",                   │
│      "provisioning": {                                              │
│        "certificate_pem": "-----BEGIN CERTIFICATE-----...",        │
│        "private_key": "-----BEGIN RSA PRIVATE KEY-----...",        │
│        "iot_endpoint": "xxxxx-ats.iot.ap-south-1.amazonaws.com"   │
│      }                                                               │
│    }                                                                 │
│  }                                                                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Success Feedback                                │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ✓ Device Registered Successfully!                           │  │
│  │                                                               │  │
│  │  Your device Kitchen Filter has been added to your account.  │  │
│  │                                                               │  │
│  │  Next Steps:                                                  │  │
│  │  • Your device will appear in the dashboard                  │  │
│  │  • Data will start flowing once device connects              │  │
│  │  • You'll receive alerts for water quality issues            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Dashboard Refresh                                 │
│                                                                       │
│  Devices Card now shows:                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Active Devices: 1                                           │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │  📱 Kitchen Filter                                      │ │  │
│  │  │  📍 Home - Kitchen Tap                                  │ │  │
│  │  │  🟢 Active                                              │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Sequence

```
User                Frontend              API                Backend              AWS Services
 │                     │                   │                    │                      │
 │  1. Click "Add      │                   │                    │                      │
 │     Device"         │                   │                    │                      │
 ├────────────────────>│                   │                    │                      │
 │                     │                   │                    │                      │
 │  2. Fill Form       │                   │                    │                      │
 │     & Submit        │                   │                    │                      │
 ├────────────────────>│                   │                    │                      │
 │                     │                   │                    │                      │
 │                     │  3. POST /api/    │                    │                      │
 │                     │     devices/      │                    │                      │
 │                     │     register      │                    │                      │
 │                     ├──────────────────>│                    │                      │
 │                     │                   │                    │                      │
 │                     │                   │  4. Validate JWT   │                      │
 │                     │                   │     & Extract      │                      │
 │                     │                   │     User ID        │                      │
 │                     │                   ├───────────────────>│                      │
 │                     │                   │                    │                      │
 │                     │                   │                    │  5. Create IoT Thing │
 │                     │                   │                    ├─────────────────────>│
 │                     │                   │                    │                      │
 │                     │                   │                    │  6. Generate Certs   │
 │                     │                   │                    ├─────────────────────>│
 │                     │                   │                    │                      │
 │                     │                   │                    │  7. Store Device     │
 │                     │                   │                    ├─────────────────────>│
 │                     │                   │                    │     (DynamoDB)       │
 │                     │                   │                    │                      │
 │                     │                   │  8. Return Device  │                      │
 │                     │                   │     + Credentials  │                      │
 │                     │                   │<───────────────────┤                      │
 │                     │                   │                    │                      │
 │                     │  9. Success       │                    │                      │
 │                     │     Response      │                    │                      │
 │                     │<──────────────────┤                    │                      │
 │                     │                   │                    │                      │
 │  10. Show Success   │                   │                    │                      │
 │      Message        │                   │                    │                      │
 │<────────────────────┤                   │                    │                      │
 │                     │                   │                    │                      │
 │                     │  11. Refresh      │                    │                      │
 │                     │      Dashboard    │                    │                      │
 │                     ├──────────────────>│                    │                      │
 │                     │                   │                    │                      │
 │  12. See New        │                   │                    │                      │
 │      Device         │                   │                    │                      │
 │<────────────────────┤                   │                    │                      │
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    ConsumerDashboard                             │
│                                                                   │
│  State:                                                          │
│  - showAddDevice: boolean                                        │
│  - dashboardData: DashboardData                                  │
│                                                                   │
│  Methods:                                                        │
│  - toggleAddDevice()                                             │
│  - handleDeviceAdded()                                           │
│  - refetch()                                                     │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Devices Card                                  │ │
│  │                                                             │ │
│  │  <button onClick={toggleAddDevice}>                        │ │
│  │    Add Your Device                                         │ │
│  │  </button>                                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         AddDeviceModal                                     │ │
│  │                                                             │ │
│  │  Props:                                                    │ │
│  │  - isOpen: showAddDevice                                   │ │
│  │  - onClose: toggleAddDevice                                │ │
│  │  - onDeviceAdded: handleDeviceAdded                        │ │
│  │                                                             │ │
│  │  Internal State:                                           │ │
│  │  - deviceId: string                                        │ │
│  │  - deviceName: string                                      │ │
│  │  - location: string                                        │ │
│  │  - waterSourceType: string                                 │ │
│  │  - pairingCode: string                                     │ │
│  │  - isSubmitting: boolean                                   │ │
│  │  - step: 'form' | 'success' | 'error'                      │ │
│  │                                                             │ │
│  │  Methods:                                                  │ │
│  │  - handleSubmit()                                          │ │
│  │  - handleClose()                                           │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │         deviceService                                │ │ │
│  │  │                                                       │ │ │
│  │  │  registerDevice(data)                                │ │ │
│  │  │    ↓                                                  │ │ │
│  │  │  fetch('/api/devices/register', {                    │ │ │
│  │  │    method: 'POST',                                   │ │ │
│  │  │    headers: {                                        │ │ │
│  │  │      'Authorization': 'Bearer <token>',              │ │ │
│  │  │      'Content-Type': 'application/json'              │ │ │
│  │  │    },                                                │ │ │
│  │  │    body: JSON.stringify(data)                        │ │ │
│  │  │  })                                                   │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Security Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
│                                                                   │
│  Layer 1: Frontend Authentication                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • User must be logged in                                  │ │
│  │  • JWT token stored in localStorage                        │ │
│  │  • Token included in Authorization header                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           ↓                                       │
│  Layer 2: API Gateway Validation                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Verify JWT signature                                    │ │
│  │  • Check token expiration                                  │ │
│  │  • Extract user claims                                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           ↓                                       │
│  Layer 3: Backend Authorization                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Validate user_id from token                             │ │
│  │  • Check device ownership                                  │ │
│  │  • Verify device_id uniqueness                             │ │
│  │  • Validate pairing code (if provided)                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           ↓                                       │
│  Layer 4: AWS IAM Permissions                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Lambda execution role                                   │ │
│  │  • IoT Core permissions                                    │ │
│  │  • DynamoDB access                                         │ │
│  │  • Certificate generation                                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           ↓                                       │
│  Layer 5: Device Security                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Unique X.509 certificates                               │ │
│  │  • Private key never stored                                │ │
│  │  • TLS 1.2+ for MQTT                                       │ │
│  │  • IoT policy restrictions                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Error Scenarios                             │
│                                                                   │
│  Scenario 1: Invalid Device ID                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  User Input → Validation → Error Message                   │ │
│  │  ""         → Required    → "Device ID is required"        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Scenario 2: Duplicate Device                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Backend Check → Error Response → User Feedback            │ │
│  │  Device exists → 400 Bad Request → "Device already exists" │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Scenario 3: Authentication Failure                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Token Check → Error Response → Redirect to Login          │ │
│  │  Invalid     → 401 Unauthorized → Show login modal         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Scenario 4: AWS Service Error                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  IoT Core → Error → Fallback → User Message                │ │
│  │  Fails    → Log   → Continue → "Partial registration"      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Scenario 5: Network Error                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Request → Timeout → Retry → User Message                  │ │
│  │  Sent    → 30s    → 3x    → "Please try again"            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend Stack                              │
│                                                                   │
│  • React 18 with TypeScript                                      │
│  • Framer Motion for animations                                  │
│  • Heroicons & Lucide for icons                                  │
│  • Tailwind CSS for styling                                      │
│  • React Router for navigation                                   │
│  • Custom hooks for state management                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Backend Stack                               │
│                                                                   │
│  Development:                                                    │
│  • Node.js + Express                                             │
│  • In-memory storage with file persistence                       │
│  • JWT authentication                                            │
│                                                                   │
│  Production:                                                     │
│  • AWS Lambda (Python 3.11)                                      │
│  • API Gateway for routing                                       │
│  • Cognito for authentication                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      AWS Services                                │
│                                                                   │
│  • IoT Core - Device management & MQTT                           │
│  • DynamoDB - Device data storage                                │
│  • Lambda - Serverless compute                                   │
│  • API Gateway - REST API                                        │
│  • Cognito - User authentication                                 │
│  • IAM - Access control                                          │
│  • CloudWatch - Logging & monitoring                             │
└─────────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: November 6, 2025
**Version**: 1.0
**Status**: Production Ready
