# Device Order System - MVP Implementation Plan

## 🎯 MVP Scope (Development Environment)

Build a working order system using the existing dev-server.js infrastructure before moving to AWS.

## 📊 Data Structure (dev-data.json)

### New: deviceOrders
```json
{
  "deviceOrders": [
    {
      "orderId": "ord_1234567890_abc123",
      "userId": "user_id",
      "userName": "John Doe",
      "userEmail": "john@example.com",
      "phone": "+91-9876543210",
      "address": "123 Main St, Kochi, Kerala, 682001",
      "deviceSKU": "AC-HOME-V1",
      "status": "REQUESTED",
      "quoteAmount": null,
      "paymentMethod": null,
      "paymentReference": null,
      "assignedTechnicianId": null,
      "assignedTechnicianName": null,
      "deviceId": null,
      "shippingCarrier": null,
      "shippingTrackingNo": null,
      "installationPhotos": [],
      "createdAt": "2025-12-08T10:00:00Z",
      "updatedAt": "2025-12-08T10:00:00Z",
      "quotedAt": null,
      "paidAt": null,
      "shippedAt": null,
      "installedAt": null
    }
  ]
}
```

### Extended: devices
Add new fields:
- `inventoryStatus`: "AVAILABLE" | "RESERVED" | "ASSIGNED" | "INSTALLED"
- `reservedForOrderId`: order ID if reserved
- `reservedAt`: timestamp

## 🔌 API Endpoints (dev-server.js)

### Consumer Endpoints
- `POST /api/orders` - Create new device order
- `GET /api/orders/my` - Get user's orders
- `GET /api/orders/:orderId` - Get order details

### Admin Endpoints
- `GET /api/admin/orders` - List all orders
- `PUT /api/admin/orders/:orderId/quote` - Set quote
- `PUT /api/admin/orders/:orderId/provision` - Reserve device
- `PUT /api/admin/orders/:orderId/assign` - Assign technician
- `PUT /api/admin/orders/:orderId/ship` - Mark as shipped
- `PUT /api/admin/orders/:orderId/cancel` - Cancel order

### Technician Endpoints
- `GET /api/tech/installations` - Get assigned installations
- `POST /api/tech/installations/:orderId/complete` - Complete installation

## 🎨 UI Components

### Consumer
1. **RequestDeviceButton** - CTA in dashboard
2. **RequestDeviceModal** - Order form
3. **MyOrdersPage** - Order list and tracking
4. **OrderDetailModal** - Status timeline

### Admin
1. **OrdersQueueTab** - New tab in admin dashboard
2. **OrderCard** - Order management card
3. **QuoteModal** - Set pricing
4. **ProvisionModal** - Select device from inventory
5. **AssignTechnicianModal** - Select technician

### Technician
1. **InstallationsTab** - Assigned jobs
2. **InstallationCard** - Job details
3. **CompleteInstallModal** - Finish installation

## 📅 Implementation Timeline

### Day 1: Backend Foundation
- [ ] Add deviceOrders storage
- [ ] Create order endpoints
- [ ] Add order status management
- [ ] Test with Postman

### Day 2: Consumer UI
- [ ] Request device button
- [ ] Order form modal
- [ ] My orders page
- [ ] Order tracking

### Day 3: Admin UI
- [ ] Orders queue tab
- [ ] Quote management
- [ ] Device provisioning
- [ ] Technician assignment

### Day 4: Technician UI
- [ ] Installations list
- [ ] Complete installation flow
- [ ] Device activation
- [ ] Testing

### Day 5: Integration & Polish
- [ ] End-to-end testing
- [ ] Notifications
- [ ] Error handling
- [ ] Documentation

## ✅ Acceptance Criteria

1. Consumer can request a device
2. Admin receives notification
3. Admin can quote and provision
4. Technician receives assignment
5. Technician can complete install
6. Device appears in consumer dashboard
7. All state transitions logged

## 🚀 Ready to Start?

Reply "start implementation" to begin building!
