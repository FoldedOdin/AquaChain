# Complete Device-to-Consumer Flow

**Document:** End-to-End IoT Device Delivery Process  
**Date:** December 29, 2025  
**Version:** 1.0

---

## 📋 Overview

This document describes the complete journey of an IoT water quality monitoring device from inventory to consumer's home, including all UI interactions, backend processes, database operations, and stakeholder actions.

---

## 🎯 Stakeholders

1. **Consumer** - End user who orders and receives the device
2. **Admin** - Manages inventory, processes orders, assigns technicians
3. **Technician** - Installs device at consumer's location
4. **System** - Backend automation and notifications

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: ORDER PLACEMENT                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Consumer Dashboard → "Request Device" Button
                              │
                              ↓
        Profile Validation (Address, Phone Required)
                              │
                              ↓
        Device Request Modal Opens
                              │
                              ↓
        Consumer Fills: Device Type, Location, Preferred Date
                              │
                              ↓
        POST /api/device-orders (Backend)
                              │
                              ↓
        DynamoDB: DeviceOrders Table (status: pending)
                              │
                              ↓
        Notification: Admin receives "New Order" alert
                              │
                              ↓
        Consumer sees: "Order Submitted Successfully"

┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 2: ADMIN PROCESSING                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Admin Dashboard → "Orders Queue" Tab
                              │
                              ↓
        Admin sees: New order with "pending" status
                              │
                              ↓
        Admin clicks: "View Details" button
                              │
                              ↓
        Order Details Modal shows:
        - Consumer info (name, email, phone, address)
        - Device type requested
        - Preferred installation date
        - Order timestamp
                              │
                              ↓
        Admin checks: Inventory availability
                              │
                              ↓
        Admin clicks: "Approve Order" button
                              │
                              ↓
        Approval Modal opens:
        - Select device from inventory dropdown
        - Enter quote amount
        - Add admin notes
                              │
                              ↓
        PUT /api/device-orders/:orderId/approve (Backend)
                              │
                              ↓
        DynamoDB Updates:
        - DeviceOrders: status → "approved"
        - Devices: status → "reserved" (linked to order)
        - Inventory: available_count decremented
                              │
                              ↓
        Notifications sent:
        - Consumer: "Order Approved - Quote: ₹X"
        - Admin: "Order approved successfully"
                              │
                              ↓
        Consumer Dashboard updates: Order status → "Approved"

┌─────────────────────────────────────────────────────────────────┐
│               PHASE 3: TECHNICIAN ASSIGNMENT                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Admin Dashboard → "Approved Orders" section
                              │
                              ↓
        Admin clicks: "Assign Technician" button
                              │
                              ↓
        Assignment Modal opens:
        - List of available technicians
        - Technician ratings and availability
        - Distance from installation location
                              │
                              ↓
        Admin selects: Technician from dropdown
                              │
                              ↓
        PUT /api/device-orders/:orderId/assign (Backend)
                              │
                              ↓
        DynamoDB Updates:
        - DeviceOrders: status → "assigned"
        - DeviceOrders: technician_id added
        - DeviceOrders: assigned_at timestamp
                              │
                              ↓
        Notifications sent:
        - Technician: "New Task Assigned - Install at [Address]"
        - Consumer: "Technician Assigned - [Name] will install"
        - Admin: "Technician assigned successfully"
                              │
                              ↓
        Technician Dashboard: New task appears in "Pending" tab

┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 4: DEVICE SHIPMENT                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Admin Dashboard → Assigned order
                              │
                              ↓
        Admin clicks: "Mark as Shipped" button
                              │
                              ↓
        Shipping Modal opens:
        - Enter tracking number
        - Select courier service
        - Add shipping notes
                              │
                              ↓
        PUT /api/device-orders/:orderId/ship (Backend)
                              │
                              ↓
        DynamoDB Updates:
        - DeviceOrders: status → "shipped"
        - DeviceOrders: tracking_number added
        - DeviceOrders: shipped_at timestamp
        - Devices: status → "in_transit"
                              │
                              ↓
        Notifications sent:
        - Consumer: "Device Shipped - Track: [Number]"
        - Technician: "Device shipped to installation location"
        - Admin: "Order marked as shipped"
                              │
                              ↓
        Consumer Dashboard: Shows tracking information
        Technician Dashboard: Task status → "Ready to Install"

┌─────────────────────────────────────────────────────────────────┐
│              PHASE 5: TECHNICIAN ACCEPTANCE                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Technician Dashboard → "Pending Tasks" tab
                              │
                              ↓
        Technician sees: New task with "shipped" status
                              │
                              ↓
        Technician clicks: "View Details" button
                              │
                              ↓
        Task Details Modal shows:
        - Order ID and device info
        - Customer name, phone, address
        - Preferred installation date/time
        - Quote amount
        - Special instructions
                              │
                              ↓
        Technician clicks: "Accept Task" button
                              │
                              ↓
        PUT /api/technician/tasks/:taskId/accept (Backend)
                              │
                              ↓
        DynamoDB Updates:
        - DeviceOrders: status → "accepted"
        - DeviceOrders: accepted_at timestamp
        - AuditLogs: Record technician acceptance
                              │
                              ↓
        Notifications sent:
        - Consumer: "Technician accepted - Will arrive on [Date]"
        - Admin: "Task accepted by [Technician Name]"
        - Technician: "Task accepted successfully"
                              │
                              ↓
        Technician Dashboard: Task moves to "Accepted" tab
        Consumer Dashboard: Status → "Technician Confirmed"

┌─────────────────────────────────────────────────────────────────┐
│                PHASE 6: INSTALLATION START                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Technician arrives at consumer's location
                              │
                              ↓
        Technician Dashboard → "Accepted Tasks" tab
                              │
                              ↓
        Technician clicks: "Start Work" button
                              │
                              ↓
        PUT /api/technician/tasks/:taskId/start (Backend)
                              │
                              ↓
        DynamoDB Updates:
        - DeviceOrders: status → "installing"
        - DeviceOrders: installation_started_at timestamp
        - Devices: status → "installing"
        - AuditLogs: Record installation start
                              │
                              ↓
        Notifications sent:
        - Consumer: "Installation started"
        - Admin: "Installation in progress - [Technician]"
        - Technician: "Work started - Timer running"
                              │
                              ↓
        Technician Dashboard: Task moves to "In Progress" tab
        Consumer Dashboard: Status → "Installing"

┌─────────────────────────────────────────────────────────────────┐
│              PHASE 7: DEVICE PROVISIONING                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Technician physically installs device:
        - Connects sensors (pH, Turbidity, TDS, Temperature)
        - Powers on ESP32 device
        - Connects to consumer's Wi-Fi
                              │
                              ↓
        Backend: Device Provisioning Script runs
                              │
                              ↓
        POST /api/iot/provision-device (Backend)
        Parameters:
        - device_id: "AquaChain-Device-XXX"
        - user_id: consumer's Cognito sub
        - location: installation address
                              │
                              ↓
        AWS IoT Core Operations:
        1. Create Thing in IoT Registry
        2. Generate X.509 certificate and private key
        3. Create device-specific IoT policy
        4. Attach certificate to Thing
        5. Attach policy to certificate
                              │
                              ↓
        DynamoDB Updates:
        - Devices Table:
          * device_id: "AquaChain-Device-XXX"
          * user_id: consumer's ID
          * status: "provisioning"
          * certificate_arn: AWS certificate ARN
          * iot_endpoint: AWS IoT endpoint
          * location: installation address
          * provisioned_at: timestamp
                              │
                              ↓
        Certificates stored in S3:
        - s3://aquachain-certificates/device-XXX/certificate.pem
        - s3://aquachain-certificates/device-XXX/private.key
        - s3://aquachain-certificates/device-XXX/root-ca.pem
                              │
                              ↓
        Device Configuration:
        - Technician uploads certificates to ESP32
        - Device connects to AWS IoT Core via MQTT
        - First heartbeat message sent
                              │
                              ↓
        IoT Core receives connection:
        - Topic: aquachain/device-XXX/status
        - Payload: {"status": "online", "timestamp": "..."}
                              │
                              ↓
        Lambda: IoT Connection Handler triggered
                              │
                              ↓
        DynamoDB Updates:
        - Devices: status → "online"
        - Devices: last_seen → current timestamp
        - Devices: connection_status → "connected"

┌─────────────────────────────────────────────────────────────────┐
│            PHASE 8: INSTALLATION COMPLETION                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Technician verifies:
        - Device is online
        - Sensors are reading correctly
        - Data is flowing to cloud
                              │
                              ↓
        Technician Dashboard → "In Progress" task
                              │
                              ↓
        Technician clicks: "Complete Installation" button
                              │
                              ↓
        Completion Modal opens:
        - Enter device location (exact placement)
        - Add installation notes
        - Upload photos (optional)
        - Consumer signature (optional)
                              │
                              ↓
        PUT /api/technician/tasks/:taskId/complete (Backend)
        Body:
        {
          "device_location": "Kitchen sink area",
          "notes": "Installed successfully, all sensors working",
          "photos": ["photo1.jpg", "photo2.jpg"],
          "completion_time": "2025-12-29T14:30:00Z"
        }
                              │
                              ↓
        DynamoDB Updates:
        - DeviceOrders: status → "completed"
        - DeviceOrders: completed_at timestamp
        - DeviceOrders: installation_notes added
        - Devices: status → "active"
        - Devices: owner_id → consumer's user_id
        - Devices: location → installation location
        - AuditLogs: Record completion
                              │
                              ↓
        Device Ownership Transfer:
        - Device moved from inventory to consumer's account
        - Consumer gains full access to device
        - Device appears in consumer's dashboard
                              │
                              ↓
        Notifications sent:
        - Consumer: "Installation Complete! Your device is now active"
        - Admin: "Installation completed by [Technician]"
        - Technician: "Task completed successfully"
                              │
                              ↓
        Technician Dashboard: Task moves to "Completed" tab
        Consumer Dashboard: Device appears in "My Devices" list

┌─────────────────────────────────────────────────────────────────┐
│              PHASE 9: CONSUMER DEVICE ACCESS                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Consumer logs into dashboard
                              │
                              ↓
        GET /api/devices (Backend)
        Headers: Authorization: Bearer {JWT}
                              │
                              ↓
        Lambda: Extract user_id from JWT
                              │
                              ↓
        DynamoDB Query:
        - Table: Devices
        - Filter: owner_id = user_id AND status = "active"
                              │
                              ↓
        Response: List of consumer's devices
        [
          {
            "device_id": "AquaChain-Device-XXX",
            "device_name": "Kitchen Water Monitor",
            "status": "online",
            "location": "Kitchen sink area",
            "last_reading": {
              "pH": 7.2,
              "turbidity": 1.5,
              "tds": 150,
              "temperature": 22.5,
              "wqi": 85,
              "timestamp": "2025-12-29T14:35:00Z"
            }
          }
        ]
                              │
                              ↓
        Consumer Dashboard displays:
        - Device card with current WQI
        - Real-time sensor readings
        - Device status (online/offline)
        - Last update timestamp
                              │
                              ↓
        Consumer clicks: Device card
                              │
                              ↓
        Device Details Page opens:
        - Current water quality metrics
        - Historical charts (24h, 7d, 30d)
        - Alert history
        - Device settings

┌─────────────────────────────────────────────────────────────────┐
│              PHASE 10: REAL-TIME DATA FLOW                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        ESP32 Device reads sensors every 60 seconds
                              │
                              ↓
        Device publishes to IoT Core:
        Topic: aquachain/device-XXX/data
        Payload:
        {
          "device_id": "AquaChain-Device-XXX",
          "timestamp": "2025-12-29T14:36:00Z",
          "readings": {
            "pH": 7.2,
            "turbidity": 1.5,
            "tds": 150,
            "temperature": 22.5
          },
          "firmware_version": "1.0.0",
          "signal_strength": -45
        }
                              │
                              ↓
        IoT Rule Engine triggers:
        Rule: "SELECT * FROM 'aquachain/+/data'"
                              │
                              ↓
        Lambda: Data Processing Handler
        1. Validate payload schema
        2. Sanitize inputs
        3. Lookup device owner (user_id)
        4. Enrich with metadata
                              │
                              ↓
        Lambda: WQI Calculation
        - Calculate Water Quality Index
        - Formula: Weighted average of pH, turbidity, TDS
        - Result: WQI = 85 (Good)
                              │
                              ↓
        Lambda: ML Inference
        - Load trained XGBoost model
        - Predict anomaly probability
        - Result: Normal (99.8% confidence)
                              │
                              ↓
        DynamoDB: Store Reading
        Table: Readings
        Partition Key: user_id#device_id#2025-12
        Sort Key: timestamp
        Data:
        {
          "reading_id": "uuid",
          "user_id": "consumer-id",
          "device_id": "device-XXX",
          "timestamp": "2025-12-29T14:36:00Z",
          "pH": 7.2,
          "turbidity": 1.5,
          "tds": 150,
          "temperature": 22.5,
          "wqi": 85,
          "anomaly_type": "normal",
          "anomaly_confidence": 0.998
        }
                              │
                              ↓
        Lambda: Alert Detection
        - Check thresholds
        - pH: 6.5-8.5 (OK)
        - Turbidity: <5 NTU (OK)
        - TDS: <500 ppm (OK)
        - No alerts generated
                              │
                              ↓
        DynamoDB Streams: Trigger
        - New reading inserted
        - Stream event generated
                              │
                              ↓
        Lambda: WebSocket Handler
        - Identify connected clients for device
        - Find WebSocket connection_id
                              │
                              ↓
        API Gateway WebSocket:
        - POST to connection endpoint
        - Send real-time update to consumer's browser
                              │
                              ↓
        Consumer Dashboard (Browser):
        - WebSocket receives message
        - Updates UI in real-time
        - Shows new WQI: 85
        - Updates chart with new data point
        - Shows "Last updated: Just now"

┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 11: ALERT SCENARIO                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        Device detects contamination:
        Readings: pH = 4.5 (Critical!)
                              │
                              ↓
        Same data flow as Phase 10, but:
                              │
                              ↓
        Lambda: Alert Detection
        - pH = 4.5 < 6.5 (CRITICAL)
        - Generate alert
                              │
                              ↓
        DynamoDB: Store Alert
        Table: Alerts
        Data:
        {
          "alert_id": "uuid",
          "user_id": "consumer-id",
          "device_id": "device-XXX",
          "severity": "critical",
          "type": "pH_low",
          "message": "Critical: pH level too low (4.5)",
          "reading_value": 4.5,
          "threshold": 6.5,
          "timestamp": "2025-12-29T15:00:00Z",
          "status": "active"
        }
                              │
                              ↓
        Lambda: Notification Service
        - Lookup user preferences
        - Get contact info (email, phone)
                              │
                              ↓
        Multi-channel notifications:
        1. SMS via SNS:
           "ALERT: Critical water quality issue detected.
            pH level: 4.5 (too acidic). Check your AquaChain app."
        
        2. Email via SES:
           Subject: "Critical Water Quality Alert"
           Body: Detailed alert with recommendations
        
        3. Push Notification (if enabled):
           "Critical Alert: pH too low"
        
        4. WebSocket (real-time):
           Dashboard shows red alert banner
                              │
                              ↓
        Consumer Dashboard:
        - Alert banner appears (red, critical)
        - Alert bell icon shows count
        - Device card shows alert status
        - Notification center updated
                              │
                              ↓
        Consumer clicks: Alert notification
                              │
                              ↓
        Alert Details Modal:
        - Shows severity, type, message
        - Shows current vs. threshold values
        - Provides recommendations
        - Option to acknowledge alert
                              │
                              ↓
        Consumer clicks: "Acknowledge" button
                              │
                              ↓
        PUT /api/alerts/:alertId/acknowledge (Backend)
                              │
                              ↓
        DynamoDB Updates:
        - Alerts: status → "acknowledged"
        - Alerts: acknowledged_at timestamp
        - Alerts: acknowledged_by user_id
                              │
                              ↓
        Dashboard: Alert marked as acknowledged

---

## 📊 Database Schema Details

### DeviceOrders Table

```json
{
  "order_id": "order-uuid",
  "user_id": "consumer-cognito-sub",
  "device_type": "standard",
  "status": "pending|approved|assigned|shipped|accepted|installing|completed",
  "quote_amount": 5000,
  "device_id": "AquaChain-Device-XXX",
  "technician_id": "tech-cognito-sub",
  "installation_address": "123 Main St, City",
  "preferred_date": "2025-12-30",
  "tracking_number": "TRACK123",
  "created_at": "2025-12-29T10:00:00Z",
  "approved_at": "2025-12-29T10:30:00Z",
  "assigned_at": "2025-12-29T11:00:00Z",
  "shipped_at": "2025-12-29T12:00:00Z",
  "accepted_at": "2025-12-29T13:00:00Z",
  "installation_started_at": "2025-12-29T14:00:00Z",
  "completed_at": "2025-12-29T14:30:00Z"
}
```

### Devices Table

```json
{
  "device_id": "AquaChain-Device-XXX",
  "owner_id": "consumer-cognito-sub",
  "device_name": "Kitchen Water Monitor",
  "device_type": "standard",
  "status": "inventory|reserved|in_transit|provisioning|online|offline|active",
  "location": "Kitchen sink area",
  "certificate_arn": "arn:aws:iot:...",
  "iot_endpoint": "xxxxx-ats.iot.ap-south-1.amazonaws.com",
  "firmware_version": "1.0.0",
  "last_seen": "2025-12-29T14:36:00Z",
  "connection_status": "connected",
  "provisioned_at": "2025-12-29T14:20:00Z",
  "created_at": "2025-12-01T00:00:00Z"
}
```

### Readings Table

```json
{
  "reading_id": "uuid",
  "user_id": "consumer-cognito-sub",
  "device_id": "AquaChain-Device-XXX",
  "deviceId_month": "consumer-id#device-XXX#2025-12",
  "timestamp": "2025-12-29T14:36:00Z",
  "pH": 7.2,
  "turbidity": 1.5,
  "tds": 150,
  "temperature": 22.5,
  "wqi": 85,
  "anomaly_type": "normal|minor|critical",
  "anomaly_confidence": 0.998
}
```

### Alerts Table

```json
{
  "alert_id": "uuid",
  "user_id": "consumer-cognito-sub",
  "device_id": "AquaChain-Device-XXX",
  "severity": "low|medium|high|critical",
  "type": "pH_low|pH_high|turbidity_high|tds_high|anomaly_detected",
  "message": "Critical: pH level too low (4.5)",
  "reading_value": 4.5,
  "threshold": 6.5,
  "status": "active|acknowledged|resolved",
  "timestamp": "2025-12-29T15:00:00Z",
  "acknowledged_at": "2025-12-29T15:05:00Z",
  "acknowledged_by": "consumer-cognito-sub"
}
```

---

## 🔐 Security & Authorization Flow

### JWT Token Validation

Every API request includes JWT token:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Backend Validation:**
1. API Gateway Cognito Authorizer validates token
2. Extracts user_id from token claims
3. Passes user_id to Lambda function
4. Lambda verifies resource ownership

**Example:**
```python
def authorize_device_access(event, device_id):
    # Extract user_id from JWT
    user_id = event['requestContext']['authorizer']['claims']['sub']
    
    # Query device ownership
    device = dynamodb.get_item(
        TableName='Devices',
        Key={'device_id': device_id}
    )
    
    # Verify ownership
    if device['owner_id'] != user_id:
        raise PermissionError("Access denied")
    
    return True
```

---

## 📱 UI Components Involved

### Consumer Dashboard Components

1. **DeviceRequestModal.tsx**
   - Form for requesting new device
   - Validates profile completeness
   - Submits order to backend

2. **MyOrdersPage.tsx**
   - Lists all device orders
   - Shows order status and timeline
   - Allows order tracking

3. **DeviceCard.tsx**
   - Displays device info and current WQI
   - Shows real-time status
   - Links to device details

4. **DeviceDetailsPage.tsx**
   - Shows detailed metrics
   - Historical charts
   - Alert history
   - Device settings

5. **AlertNotification.tsx**
   - Displays alert banners
   - Shows alert details
   - Allows acknowledgment

### Admin Dashboard Components

1. **OrdersQueueTab.tsx**
   - Lists pending orders
   - Approve/reject functionality
   - Assign technician

2. **InventoryManagement.tsx**
   - Manage device inventory
   - Track available devices
   - Reserve devices for orders

3. **TechnicianAssignment.tsx**
   - Select technician for order
   - View technician availability
   - Track assignments

### Technician Dashboard Components

1. **TaskList.tsx**
   - Shows assigned tasks
   - Filter by status
   - Accept/decline tasks

2. **TaskDetailsModal.tsx**
   - Shows task details
   - Customer information
   - Installation instructions

3. **TaskActions.tsx**
   - Accept Task button
   - Start Work button
   - Complete Installation button

---

## 🔄 API Endpoints Summary

### Device Orders

```
POST   /api/device-orders
GET    /api/device-orders
GET    /api/device-orders/:orderId
PUT    /api/device-orders/:orderId/approve
PUT    /api/device-orders/:orderId/assign
PUT    /api/device-orders/:orderId/ship
DELETE /api/device-orders/:orderId
```

### Devices

```
GET    /api/devices
GET    /api/devices/:deviceId
POST   /api/devices
PUT    /api/devices/:deviceId
DELETE /api/devices/:deviceId
POST   /api/iot/provision-device
```

### Readings

```
GET    /api/readings
GET    /api/readings/:deviceId
POST   /api/readings/export
```

### Alerts

```
GET    /api/alerts
GET    /api/alerts/:alertId
PUT    /api/alerts/:alertId/acknowledge
PUT    /api/alerts/:alertId/resolve
DELETE /api/alerts/:alertId
```

### Technician Tasks

```
GET    /api/technician/tasks
GET    /api/technician/tasks/:taskId
PUT    /api/technician/tasks/:taskId/accept
PUT    /api/technician/tasks/:taskId/decline
PUT    /api/technician/tasks/:taskId/start
PUT    /api/technician/tasks/:taskId/complete
```

---

## ⏱️ Timeline Summary

**Typical Order-to-Installation Timeline:**

| Phase | Duration | Status |
|-------|----------|--------|
| Order Placement | 5 minutes | Consumer submits |
| Admin Review | 1-24 hours | Admin approves |
| Technician Assignment | 1-4 hours | Admin assigns |
| Device Shipment | 1-3 days | In transit |
| Technician Acceptance | 1-24 hours | Tech confirms |
| Installation | 1-2 hours | On-site work |
| **Total** | **2-5 days** | **Complete** |

---

## 🎯 Success Criteria

### Order Completion
- ✅ Order placed successfully
- ✅ Admin approved within 24 hours
- ✅ Technician assigned within 4 hours
- ✅ Device shipped within 24 hours
- ✅ Installation completed within 2 hours
- ✅ Device online and sending data
- ✅ Consumer can access device

### Data Flow
- ✅ Device sends data every 60 seconds
- ✅ Data processed within 500ms
- ✅ WQI calculated accurately
- ✅ Anomalies detected in real-time
- ✅ Alerts sent within 2 seconds
- ✅ Dashboard updates in real-time

---

## 🚨 Error Handling

### Common Errors & Solutions

**1. Profile Incomplete**
- Error: "Please complete your profile"
- Solution: Redirect to profile edit
- Required: Address, phone number

**2. No Inventory Available**
- Error: "No devices available"
- Solution: Admin adds inventory
- Notification: Consumer notified when available

**3. Device Provisioning Failed**
- Error: "Failed to provision device"
- Solution: Retry provisioning
- Fallback: Manual provisioning by admin

**4. Connection Lost**
- Error: "Device offline"
- Solution: Technician checks connection
- Notification: Consumer alerted

**5. Payment Failed**
- Error: "Payment processing failed"
- Solution: Retry payment
- Alternative: Cash on delivery

---

## 📊 Monitoring & Analytics

### Tracked Metrics

**Order Metrics:**
- Orders placed per day
- Approval time (avg, p95, p99)
- Assignment time
- Installation time
- Completion rate

**Device Metrics:**
- Devices in inventory
- Devices in transit
- Devices active
- Device uptime
- Data transmission rate

**Performance Metrics:**
- API latency
- Data processing time
- Alert generation time
- WebSocket connection count
- Error rate

---

## 🔍 Audit Trail

Every action is logged in AuditLogs table:

```json
{
  "log_id": "uuid",
  "timestamp": "2025-12-29T14:30:00Z",
  "user_id": "actor-id",
  "action_type": "ORDER_CREATED|ORDER_APPROVED|DEVICE_PROVISIONED|...",
  "resource_type": "order|device|reading|alert",
  "resource_id": "resource-uuid",
  "details": {
    "before": {...},
    "after": {...},
    "changes": [...]
  },
  "ip_address": "1.2.3.4",
  "user_agent": "Mozilla/5.0..."
}
```

---

## ✅ Conclusion

This document provides a complete end-to-end view of how an IoT device reaches a consumer in the AquaChain platform. The process involves:

- **11 distinct phases** from order to real-time monitoring
- **3 stakeholders** (Consumer, Admin, Technician)
- **5 DynamoDB tables** for data persistence
- **20+ API endpoints** for operations
- **10+ UI components** for user interaction
- **Real-time data flow** via WebSocket and MQTT
- **Comprehensive security** with JWT and IAM
- **Complete audit trail** for compliance

**Status:** ✅ Fully Implemented and Production-Ready

---

**Document Version:** 1.0  
**Last Updated:** December 29, 2025  
**Maintained By:** AquaChain Development Team
