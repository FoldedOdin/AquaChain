# Complete Device Order Workflow
## From Consumer Request to Device Installation

This document explains the complete end-to-end workflow for a consumer ordering and receiving an AquaChain device.

---

## 🎯 Overview

**Total Steps:** 4 main stages  
**Roles Involved:** Consumer, Admin, Technician  
**Average Time:** 2-5 days (depending on logistics)

---

## 📋 Detailed Workflow

### **STAGE 1: Consumer Requests Device** 
**Status:** `pending`  
**Actor:** Consumer

#### What Happens:
1. Consumer logs into their dashboard (`phoneixknight18@gmail.com` / `admin1234`)
2. Clicks **"Request Device"** button in Quick Actions section
3. Fills out the device order form:
   - **Device Model:** AquaChain Home V1 (₹4,000)
   - **Installation Address:** Full address where device will be installed
   - **Phone Number:** Contact number
   - **Payment Method:** COD (Cash on Delivery) or Online
   - **Preferred Installation Slot:** Date and time preference
4. Clicks **"Submit Request"**

#### Backend Actions:
- Creates new order with `orderId` (e.g., `ord_1765187095768_l19i069q1`)
- Sets initial status to `pending`
- Stores consumer details (name, email, address, phone)
- Creates system alert for admins about new order
- Saves to `.dev-data.json` → `deviceOrders` array

#### Consumer Can:
- View order status in **"My Orders"** page
- See order in "Pending" state
- Track progress through 6-step timeline

#### API Endpoint:
```
POST /api/consumer/orders
Body: { deviceSKU, address, phone, paymentMethod, preferredSlot }
```

---

### **STAGE 2: Admin Reviews & Sets Quote**
**Status:** `pending` → `quoted`  
**Actor:** Admin

#### What Happens:
1. Admin logs into dashboard (`admin@aquachain.com` / `admin1234`)
2. Goes to **"Orders"** tab
3. Sees new order in "Pending" section
4. Reviews order details:
   - Consumer name and contact
   - Installation address
   - Device model requested
   - Preferred installation time
5. Clicks **"Set Quote"** button
6. Enters quote amount (e.g., ₹4,000)
7. Clicks **"Set Quote"**

#### Backend Actions:
- Updates order status to `quoted`
- Sets `quoteAmount` field
- Records `quotedAt` timestamp
- Updates `updatedAt` timestamp
- Creates notification for consumer

#### Consumer Sees:
- Order status changes to "Quoted"
- Quote amount displayed: ₹4,000
- **"Choose Payment" button appears** in My Orders
- Alert: "Action Required: Choose Payment Method"

#### API Endpoint:
```
PUT /api/admin/orders/:orderId/quote
Body: { quoteAmount: 4000 }
```

---

### **STAGE 2.5: Consumer Chooses Payment Method** ⭐ NEW
**Status:** `quoted` (payment method selected)  
**Actor:** Consumer

#### What Happens:
1. Consumer goes to **"My Orders"** page
2. Sees order with status "Quoted" and quote amount
3. Clicks **"Choose Payment"** button
4. Modal opens with two payment options:
   - **COD (Cash on Delivery)** - Pay when device is delivered and installed
   - **Online Payment** - Pay now via UPI, Card, or Net Banking
5. Selects preferred payment method
6. Clicks **"Confirm Payment Method"**

#### Backend Actions:
- Updates `paymentMethod` field (COD or ONLINE)
- Records action in `auditTrail`
- Updates `updatedAt` timestamp
- Creates alert for admin about payment method selection

#### Admin Sees:
- Alert: "Consumer selected [COD/ONLINE] payment for order"
- Order now shows payment method
- Can proceed with device provisioning

#### API Endpoint:
```
PUT /api/orders/:orderId/payment-method
Body: { paymentMethod: "COD" | "ONLINE" }
```

---

### **STAGE 3: Admin Provisions Device & Assigns Technician**
**Status:** `quoted` (with payment method) → `shipped`  
**Actor:** Admin

**Note:** Admin can only provision after consumer selects payment method

#### What Happens:
1. Admin clicks **"Provision Device"** button on quoted order
2. Modal opens with two dropdowns:
   
   **A. Select Device:**
   - Shows unassigned devices from inventory
   - Options: AC-INV-001, AC-INV-002, AC-INV-003, AC-INV-004, AC-INV-005
   - Each shows: Device ID - Location (e.g., "AC-INV-001 - Warehouse")
   
   **B. Assign Technician:**
   - Shows all technicians in system
   - Options: Sidharth Lenin, etc.
   - Shows: Name - Email

3. Admin selects device (e.g., AC-INV-001)
4. Admin selects technician (e.g., Sidharth Lenin)
5. Clicks **"Provision & Ship"**

#### Backend Actions (3 API calls in sequence):

**Step 1: Provision Device**
```
PUT /api/admin/orders/:orderId/provision
Body: { deviceId: "AC-INV-001" }
```
- Links device to order
- Sets `provisionedDeviceId` field
- Updates status to `provisioned`

**Step 2: Assign Technician**
```
PUT /api/admin/orders/:orderId/assign
Body: { 
  technicianId: "dev-user-1762509139325",
  technicianName: "Sidharth Lenin"
}
```
- Links technician to order
- Sets `assignedTechnicianId` and `assignedTechnicianName`
- Updates status to `assigned`

**Step 3: Mark as Shipped (Automatic)**
```
PUT /api/admin/orders/:orderId/ship
Body: {}
```
- Updates status to `shipped`
- Records `shippedAt` timestamp
- Order is now ready for installation

#### Consumer Sees:
- Order status changes to "Shipped"
- Assigned technician name displayed
- Device ID shown
- Timeline shows "Device Shipped" step completed

#### Technician Sees:
- New order appears in their dashboard
- Order details visible via `/api/technician/orders`
- Consumer address and contact info
- Preferred installation time
- Device to install: AC-INV-001

---

### **STAGE 4: Technician Completes Installation**
**Status:** `shipped` → `completed`  
**Actor:** Technician

#### What Happens:
1. Technician logs into dashboard (`leninsidharth@gmail.com` / `Sidharth@123`)
2. Sees assigned order in their task list
3. Reviews installation details:
   - Consumer: Joseph Shine
   - Address: Akuthoote House Kothad
   - Phone: 1234567890
   - Device: AC-INV-001
   - Preferred time: Dec 10, 2025 at 3:14 PM
4. Technician travels to consumer location
5. Installs the device at consumer's premises
6. Clicks **"Complete Installation"** in their dashboard
7. Provides installation details:
   - Device location (e.g., "Kitchen", "Bathroom")
   - Calibration data (pH offset, TDS factor)
   - Installation photos (optional)

#### Backend Actions:
```
POST /api/tech/installations/:orderId/complete
Body: {
  deviceId: "AC-INV-001",
  location: "Kitchen",
  calibrationData: { phOffset: 0, tdsFactor: 1 },
  installationPhotos: []
}
```

**Device Transfer Process:**
1. Finds device AC-INV-001 in INVENTORY
2. Removes device from INVENTORY
3. Updates device fields:
   - `user_id` → Consumer's userId
   - `status` → "active"
   - `installedBy` → "Sidharth Lenin"
   - `installedAt` → Current timestamp
   - `location` → "Kitchen"
   - `calibrationData` → Provided values
4. Adds device to consumer's device list
5. Updates order status to `completed`
6. Records `installedAt` timestamp

#### Consumer Sees:
- Order status changes to "Completed"
- Timeline shows all steps completed
- **NEW DEVICE APPEARS** in their dashboard!
- Device shows in "My Devices" section:
  - Device ID: AC-INV-001
  - Location: Kitchen
  - Status: Active
  - Installed by: Sidharth Lenin
- Can now view real-time water quality data
- Can see device on map
- Receives notifications about water quality

#### API Endpoint:
```
POST /api/tech/installations/:orderId/complete
```

---

## 🔄 Status Flow Summary

```
pending → quoted → quoted(+payment) → shipped → completed
   ↓         ↓            ↓              ↓          ↓
Consumer  Admin     Consumer        Admin    Technician
Request   Quote    Payment      Provision    Install
```

---

## 📊 Data Flow

### Order Object Structure:
```json
{
  "orderId": "ord_1765187095768_l19i069q1",
  "userId": "user_1764911573441_fknw3kp",
  "consumerName": "Joseph Shine",
  "consumerEmail": "phoneixknight18@gmail.com",
  "phone": "1234567890",
  "address": "Akuthoote House Kothad",
  "deviceSKU": "AC-HOME-V1",
  "status": "completed",
  "quoteAmount": 4000,
  "paymentMethod": "COD",
  "preferredSlot": "2025-12-10T15:14",
  "provisionedDeviceId": "AC-INV-001",
  "assignedTechnicianId": "dev-user-1762509139325",
  "assignedTechnicianName": "Sidharth Lenin",
  "createdAt": "2025-12-08T09:44:55.768Z",
  "quotedAt": "2025-12-08T09:45:40.114Z",
  "shippedAt": "2025-12-08T09:46:15.234Z",
  "installedAt": "2025-12-08T10:30:22.456Z",
  "updatedAt": "2025-12-08T10:30:22.456Z"
}
```

### Device Transfer:
```
BEFORE Installation:
devices: {
  "INVENTORY": [
    { device_id: "AC-INV-001", consumerName: "Unassigned", ... }
  ],
  "user_1764911573441_fknw3kp": []
}

AFTER Installation:
devices: {
  "INVENTORY": [],
  "user_1764911573441_fknw3kp": [
    { 
      device_id: "AC-INV-001", 
      consumerName: "Joseph Shine",
      installedBy: "Sidharth Lenin",
      location: "Kitchen",
      status: "active",
      ...
    }
  ]
}
```

---

## 🎭 User Perspectives

### Consumer View:
1. **Dashboard** → "Request Device" button
2. **My Orders** → Track order progress
3. **Timeline** → 6 steps showing current status
4. **My Devices** → Device appears after installation
5. **Real-time Data** → Water quality monitoring starts

### Admin View:
1. **Orders Tab** → See all orders
2. **Statistics** → Pending, Quoted, Shipped, Completed counts
3. **Actions** → Set Quote, Provision Device buttons
4. **Search/Filter** → Find specific orders

### Technician View:
1. **Dashboard** → See assigned orders
2. **Task List** → Installation jobs
3. **Order Details** → Consumer info, address, device
4. **Complete Installation** → Transfer device to consumer

---

## 🔧 Technical Details

### API Endpoints Used:
1. `POST /api/orders` - Create order (Consumer)
2. `GET /api/orders/my` - View my orders (Consumer)
3. `PUT /api/admin/orders/:orderId/quote` - Set quote (Admin)
4. `PUT /api/orders/:orderId/payment-method` - Select payment method (Consumer) ⭐ NEW
5. `PUT /api/admin/orders/:orderId/provision` - Assign device (Admin)
6. `PUT /api/admin/orders/:orderId/assign` - Assign technician (Admin)
7. `PUT /api/admin/orders/:orderId/ship` - Mark shipped (Admin)
8. `GET /api/technician/orders` - Get assigned orders (Technician)
9. `POST /api/tech/installations/:orderId/complete` - Complete installation (Technician)

### Real-time Updates:
- Orders auto-refresh every 10 seconds
- Toast notifications for status changes
- WebSocket updates for live data (after installation)

### Data Persistence:
- All data stored in `.dev-data.json`
- Automatic save on every change
- Survives server restarts

---

## ✅ Success Criteria

**Order is successful when:**
1. ✅ Consumer submits request (no payment method yet)
2. ✅ Admin sets quote
3. ✅ Consumer selects payment method (COD or Online) ⭐ NEW
4. ✅ Admin provisions device + assigns technician
5. ✅ Technician completes installation
6. ✅ Device appears in consumer's dashboard
7. ✅ Consumer can view real-time water quality data

---

## 🚀 Quick Test Flow

```bash
# 1. Start dev server
cd frontend
node src/dev-server.js

# 2. Start React app
npm start

# 3. Test as Consumer
Login: phoneixknight18@gmail.com / admin1234
→ Click "Request Device"
→ Fill form and submit
→ Go to "My Orders" to track

# 4. Test as Admin
Login: admin@aquachain.com / admin1234
→ Go to "Orders" tab
→ Click "Set Quote" on pending order
→ Enter ₹4000 and submit

# 5. Test as Consumer (Choose Payment)
Login: phoneixknight18@gmail.com / admin1234
→ Go to "My Orders"
→ Click "Choose Payment" on quoted order
→ Select COD or Online
→ Click "Confirm Payment Method"

# 6. Test as Admin (Provision)
Login: admin@aquachain.com / admin1234
→ Go to "Orders" tab
→ Click "Provision Device" on quoted order (with payment method)
→ Select AC-INV-002 and Sidharth Lenin
→ Click "Provision & Ship"

# 7. Test as Technician
Login: leninsidharth@gmail.com / Sidharth@123
→ See assigned order
→ Click "Complete Installation"
→ Enter location and details
→ Submit

# 8. Verify as Consumer
Login: phoneixknight18@gmail.com / admin1234
→ Check "My Devices" - NEW DEVICE APPEARS!
→ View real-time data
```

---

## 📝 Notes

- **Inventory Management:** Admin must add devices to INVENTORY before provisioning
- **Technician Assignment:** Happens automatically during provisioning
- **Device Ownership:** Transfers from INVENTORY to consumer on installation
- **Payment Method Selection:** ⭐ Consumer chooses COD or Online AFTER receiving quote
- **Admin Provisioning:** Can only proceed after consumer selects payment method
- **Notifications:** System creates alerts for admins on new orders and payment method selection
