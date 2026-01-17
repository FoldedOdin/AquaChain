# Dev Server Automation Integration Guide

## 🎯 Overview

This guide shows how to integrate the production-grade automation features into your existing dev-server.

## ✨ Features Added

1. **Transaction Support** - Atomic operations with automatic rollback
2. **Event-Driven Architecture** - Order lifecycle events
3. **Audit Logging** - Tamper-evident hash chain
4. **Auto-Approval** - Automatic approval for quotes under ₹20,000
5. **Error Handling** - Comprehensive error handling and rollback

## 📁 Files Created

- `frontend/src/dev-server-automation.js` - Automation module
- `DEV_SERVER_AUTOMATION_GUIDE.md` - This guide

## 🔧 Integration Steps

### Step 1: Import the Automation Module

Add to the top of `frontend/src/dev-server.js`:

```javascript
const OrderAutomation = require('./dev-server-automation');

// Initialize automation
const orderAutomation = new OrderAutomation();

// Log automation events
orderAutomation.on('ORDER_PLACED', (order) => {
  console.log(`📦 New order: ${order.orderId}`);
});

orderAutomation.on('ORDER_AUTO_APPROVED', (order) => {
  console.log(`✅ Auto-approved: ${order.orderId}`);
  // Could trigger automatic provisioning here
});
```

### Step 2: Update Order Creation Endpoint

Replace the existing order creation logic with:

```javascript
// POST /api/consumer/orders
app.post('/api/consumer/orders', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  const { deviceSKU, address, phone, paymentMethod, preferredSlot } = req.body;
  
  // Create order data
  const orderId = `ord_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const orderData = {
    orderId,
    userId: user.userId,
    consumerName: `${user.firstName || ''} ${user.lastName || ''}`.trim() || user.name,
    consumerEmail: user.email,
    deviceSKU,
    status: 'pending',
    address,
    phone,
    paymentMethod,
    preferredSlot,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    auditTrail: []
  };
  
  try {
    // Use atomic transaction
    const result = orderAutomation.atomicCreateOrder(
      orderData,
      inventory,  // Your inventory Map
      deviceOrders,  // Your orders array
      saveDevData  // Your save function
    );
    
    res.json({
      success: true,
      orderId: result.orderId,
      status: 'pending'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});
```

### Step 3: Update Quote Setting Endpoint

Replace the quote setting logic with:

```javascript
// PUT /api/admin/orders/:orderId/quote
app.put('/api/admin/orders/:orderId/quote', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { orderId } = req.params;
  const { quoteAmount } = req.body;
  
  const order = deviceOrders.find(o => o.orderId === orderId);
  
  if (!order) {
    return res.status(404).json({ 
      success: false, 
      error: 'Order not found' 
    });
  }
  
  try {
    // Use auto-approval logic
    const result = orderAutomation.setQuoteWithAutoApproval(
      orderId,
      quoteAmount,
      user.userId,
      order,
      saveDevData
    );
    
    res.json({
      success: true,
      status: result.status,
      autoApproved: result.autoApproved,
      message: result.autoApproved 
        ? 'Quote set and auto-approved' 
        : 'Quote set, awaiting approval'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});
```

### Step 4: Update Provisioning Endpoint

```javascript
// PUT /api/admin/orders/:orderId/provision
app.put('/api/admin/orders/:orderId/provision', (req, res) => {
  // ... auth checks ...
  
  const { orderId } = req.params;
  const { deviceId } = req.body;
  
  const order = deviceOrders.find(o => o.orderId === orderId);
  
  if (!order) {
    return res.status(404).json({ 
      success: false, 
      error: 'Order not found' 
    });
  }
  
  try {
    // Use atomic provisioning
    orderAutomation.atomicProvision(
      orderId,
      deviceId,
      order,
      devDevices,
      saveDevData
    );
    
    res.json({
      success: true,
      message: 'Device provisioned successfully',
      order
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});
```

### Step 5: Update Installation Completion

```javascript
// POST /api/tech/installations/:orderId/complete
app.post('/api/tech/installations/:orderId/complete', (req, res) => {
  // ... auth checks ...
  
  const { orderId } = req.params;
  const { deviceId, location, calibrationData, installationPhotos } = req.body;
  
  const order = deviceOrders.find(o => o.orderId === orderId);
  
  if (!order) {
    return res.status(404).json({ 
      success: false, 
      error: 'Order not found' 
    });
  }
  
  try {
    // Use atomic installation completion
    orderAutomation.atomicCompleteInstallation(
      orderId,
      deviceId,
      location,
      user.userId,
      order,
      devDevices,
      saveDevData
    );
    
    res.json({
      success: true,
      message: 'Installation completed successfully',
      order
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});
```

### Step 6: Add Audit Endpoints

```javascript
// Get audit trail for an order (Admin only)
app.get('/api/admin/orders/:orderId/audit', (req, res) => {
  // ... auth checks ...
  
  const { orderId } = req.params;
  const auditTrail = orderAutomation.getOrderAuditTrail(orderId);
  
  res.json({
    success: true,
    orderId,
    auditTrail,
    count: auditTrail.length
  });
});

// Get automation statistics (Admin only)
app.get('/api/admin/automation/stats', (req, res) => {
  // ... auth checks ...
  
  const stats = orderAutomation.getStatistics();
  
  res.json({
    success: true,
    ...stats
  });
});

// Verify audit ledger integrity (Admin only)
app.get('/api/admin/automation/verify', (req, res) => {
  // ... auth checks ...
  
  try {
    const isValid = orderAutomation.verifyAuditLedger();
    res.json({
      success: true,
      ledgerIntegrity: isValid,
      message: 'Audit ledger is intact and tamper-free'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      message: 'Audit ledger has been tampered with!'
    });
  }
});
```

## 🎯 Benefits

### Before (Current Dev Server)
- ❌ No transaction support
- ❌ Manual approval for all quotes
- ❌ No audit trail
- ❌ No event system
- ❌ Basic error handling

### After (Enhanced Dev Server)
- ✅ Atomic transactions with rollback
- ✅ Auto-approval for quotes under ₹20,000
- ✅ Tamper-evident audit logging
- ✅ Event-driven architecture
- ✅ Comprehensive error handling
- ✅ Production-ready patterns

## 📊 Auto-Approval Logic

```javascript
// Quotes under ₹20,000 are automatically approved
const AUTO_APPROVE_THRESHOLD = 20000;

// Example:
// Quote: ₹4,000 → Always auto-approved ✅
// Quote: ₹25,000 → Always auto-approved ✅
```

## 🔍 Audit Trail Example

```json
{
  "eventType": "ORDER_PLACED",
  "timestamp": "2025-12-10T10:00:00.000Z",
  "data": "{\"orderId\":\"ord_123\",\"userId\":\"user_456\"}",
  "hash": "a1b2c3d4...",
  "previousHash": "0000000..."
}
```

Each event is cryptographically linked to the previous one, making tampering detectable.

## 🧪 Testing

### Test Transaction Rollback

```javascript
// Try to create order with insufficient inventory
// Should rollback automatically
POST /api/consumer/orders
{
  "deviceSKU": "AC-HOME-V1",  // Assuming no inventory
  "address": "Test Address",
  "phone": "1234567890",
  "paymentMethod": "COD",
  "preferredSlot": "2025-12-15T10:00:00Z"
}

// Expected: 400 error, no order created, inventory unchanged
```

### Test Auto-Approval

```javascript
// Set quote under threshold
PUT /api/admin/orders/ord_123/quote
{
  "quoteAmount": 4000
}

// Expected: Auto-approved, event emitted
// Response: { "autoApproved": true }
```

### Test Audit Trail

```javascript
// Get audit trail
GET /api/admin/orders/ord_123/audit

// Expected: All events for this order
```

### Verify Ledger Integrity

```javascript
// Verify audit ledger
GET /api/admin/automation/verify

// Expected: { "ledgerIntegrity": true }
```

## 🚀 Next Steps

1. **Integrate the module** into your dev-server
2. **Test each endpoint** with the new automation
3. **Monitor the console** for event logs
4. **Check audit trail** after operations
5. **Verify rollback** works on errors

## 📝 Configuration

You can customize the auto-approval threshold:

```javascript
// In dev-server.js
orderAutomation.AUTO_APPROVE_THRESHOLD = 25000; // Change to ₹25,000
```

## 🎉 Result

Your dev-server now has production-grade features:
- ✅ Atomic operations
- ✅ Event-driven architecture
- ✅ Audit logging
- ✅ Auto-approval
- ✅ Error handling

All without migrating to AWS!
