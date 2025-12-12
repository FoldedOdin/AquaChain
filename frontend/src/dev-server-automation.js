/**
 * Dev Server Automation Module
 * Adds production-grade features to the development server:
 * - Transaction support for atomic operations
 * - Event-driven architecture
 * - Audit logging with hash chain
 * - Auto-approval logic
 * - Error handling and rollback
 */

const EventEmitter = require('events');
const crypto = require('crypto');

class OrderAutomation extends EventEmitter {
  constructor() {
    super();
    this.auditLedger = [];
    this.AUTO_APPROVE_THRESHOLD = 20000; // ₹20,000
    this.setupEventHandlers();
  }

  /**
   * Setup event handlers for order lifecycle
   */
  setupEventHandlers() {
    this.on('ORDER_PLACED', (order) => {
      console.log(`📦 [EVENT] Order placed: ${order.orderId}`);
      this.auditLog('ORDER_PLACED', order);
      // Could trigger notifications here
    });

    this.on('ORDER_QUOTED', (order) => {
      console.log(`💰 [EVENT] Order quoted: ${order.orderId} - ₹${order.quoteAmount}`);
      this.auditLog('ORDER_QUOTED', order);
      
      // Auto-approve if under threshold
      if (order.quoteAmount < this.AUTO_APPROVE_THRESHOLD) {
        console.log(`✅ [AUTO-APPROVE] Order ${order.orderId} auto-approved (under ₹${this.AUTO_APPROVE_THRESHOLD})`);
        this.emit('ORDER_AUTO_APPROVED', order);
      }
    });

    this.on('ORDER_PROVISIONED', (order) => {
      console.log(`📱 [EVENT] Order provisioned: ${order.orderId}`);
      this.auditLog('ORDER_PROVISIONED', order);
    });

    this.on('ORDER_SHIPPED', (order) => {
      console.log(`🚚 [EVENT] Order shipped: ${order.orderId}`);
      this.auditLog('ORDER_SHIPPED', order);
    });

    this.on('ORDER_COMPLETED', (order) => {
      console.log(`✅ [EVENT] Order completed: ${order.orderId}`);
      this.auditLog('ORDER_COMPLETED', order);
    });

    this.on('ORDER_FAILED', (error) => {
      console.error(`❌ [EVENT] Order failed:`, error);
      this.auditLog('ORDER_FAILED', error);
    });
  }

  /**
   * Create order with atomic inventory reservation
   * Implements transaction-like behavior
   */
  atomicCreateOrder(orderData, inventory, deviceOrders, saveCallback) {
    // Create backup for rollback
    const backup = {
      orders: JSON.parse(JSON.stringify(deviceOrders)),
      inventory: new Map(inventory)
    };

    try {
      // Validate inventory
      const inv = inventory.get(orderData.deviceSKU);
      if (!inv) {
        throw new Error(`Device SKU not found: ${orderData.deviceSKU}`);
      }
      
      if (inv.availableCount < 1) {
        throw new Error('Insufficient inventory');
      }

      // Step 1: Reserve inventory
      inv.reservedCount = (inv.reservedCount || 0) + 1;
      inv.availableCount -= 1;
      inv.updatedAt = new Date().toISOString();

      // Step 2: Create order
      deviceOrders.push(orderData);

      // Step 3: Commit (save to file)
      saveCallback();

      // Step 4: Emit event
      this.emit('ORDER_PLACED', orderData);

      console.log(`✅ [TRANSACTION] Order created successfully: ${orderData.orderId}`);
      return { success: true, orderId: orderData.orderId };

    } catch (error) {
      // Rollback on error
      console.error(`❌ [TRANSACTION] Rolling back order creation:`, error.message);
      
      // Restore from backup
      deviceOrders.length = 0;
      deviceOrders.push(...backup.orders);
      
      // Restore inventory
      inventory.clear();
      backup.inventory.forEach((value, key) => {
        inventory.set(key, value);
      });

      this.emit('ORDER_FAILED', { 
        action: 'CREATE_ORDER', 
        error: error.message,
        orderData 
      });

      throw error;
    }
  }

  /**
   * Set quote with auto-approval logic
   */
  setQuoteWithAutoApproval(orderId, quoteAmount, adminId, order, updateCallback) {
    try {
      // Validate state transition
      if (order.status !== 'pending') {
        throw new Error(`Invalid state transition. Current status: ${order.status}`);
      }

      // Determine if auto-approve
      const autoApproved = quoteAmount < this.AUTO_APPROVE_THRESHOLD;
      const newStatus = autoApproved ? 'quoted' : 'quoted';
      const timestamp = new Date().toISOString();

      // Update order
      order.status = newStatus;
      order.quoteAmount = quoteAmount;
      order.quotedAt = timestamp;
      order.quotedBy = adminId;
      order.autoApproved = autoApproved;
      order.updatedAt = timestamp;

      // Add to audit trail
      if (!order.auditTrail) order.auditTrail = [];
      order.auditTrail.push({
        action: 'QUOTE_SET',
        by: adminId,
        at: timestamp,
        amount: quoteAmount,
        autoApproved
      });

      // Commit changes
      updateCallback();

      // Emit event
      this.emit('ORDER_QUOTED', { ...order, quoteAmount, autoApproved });

      console.log(`✅ [QUOTE] Set for order ${orderId}: ₹${quoteAmount} (auto-approved: ${autoApproved})`);
      
      return { success: true, status: newStatus, autoApproved };

    } catch (error) {
      console.error(`❌ [QUOTE] Failed to set quote:`, error.message);
      this.emit('ORDER_FAILED', { 
        action: 'SET_QUOTE', 
        orderId, 
        error: error.message 
      });
      throw error;
    }
  }

  /**
   * Provision device with atomic operations
   */
  atomicProvision(orderId, deviceId, order, devices, updateCallback) {
    const backup = {
      order: JSON.parse(JSON.stringify(order)),
      devices: new Map(devices)
    };

    try {
      // Find device
      let deviceFound = false;
      let device = null;

      for (const [userId, userDevices] of devices.entries()) {
        const foundDevice = userDevices.find(d => d.device_id === deviceId);
        if (foundDevice) {
          device = foundDevice;
          deviceFound = true;
          break;
        }
      }

      if (!deviceFound) {
        throw new Error('Device not found or not available');
      }

      // Update order
      order.provisionedDeviceId = deviceId;
      order.status = 'provisioned';
      order.updatedAt = new Date().toISOString();

      if (!order.auditTrail) order.auditTrail = [];
      order.auditTrail.push({
        action: 'DEVICE_PROVISIONED',
        deviceId,
        at: new Date().toISOString()
      });

      // Commit
      updateCallback();

      // Emit event
      this.emit('ORDER_PROVISIONED', { ...order, deviceId });

      console.log(`✅ [PROVISION] Device ${deviceId} provisioned for order ${orderId}`);
      return { success: true };

    } catch (error) {
      console.error(`❌ [PROVISION] Failed:`, error.message);
      
      // Rollback
      Object.assign(order, backup.order);
      
      this.emit('ORDER_FAILED', { 
        action: 'PROVISION', 
        orderId, 
        error: error.message 
      });
      throw error;
    }
  }

  /**
   * Complete installation with atomic device transfer
   */
  atomicCompleteInstallation(orderId, deviceId, location, techId, order, devices, updateCallback) {
    const backup = {
      order: JSON.parse(JSON.stringify(order)),
      devices: new Map()
    };

    // Deep copy devices
    for (const [userId, userDevices] of devices.entries()) {
      backup.devices.set(userId, JSON.parse(JSON.stringify(userDevices)));
    }

    try {
      // Find and transfer device
      let deviceFound = false;
      let device = null;
      let sourceUserId = null;

      for (const [userId, userDevices] of devices.entries()) {
        const deviceIndex = userDevices.findIndex(d => d.device_id === deviceId);
        if (deviceIndex !== -1) {
          device = userDevices[deviceIndex];
          sourceUserId = userId;
          
          // Remove from source
          userDevices.splice(deviceIndex, 1);
          
          // Update device
          device.user_id = order.userId;
          device.status = 'active';
          device.installedBy = order.assignedTechnicianName;
          device.installedAt = new Date().toISOString();
          device.location = location;
          
          // Add to consumer
          const consumerDevices = devices.get(order.userId) || [];
          consumerDevices.push(device);
          devices.set(order.userId, consumerDevices);
          
          deviceFound = true;
          break;
        }
      }

      if (!deviceFound) {
        throw new Error('Device not found');
      }

      // Update order
      order.status = 'completed';
      order.installedAt = new Date().toISOString();
      order.completedBy = techId;
      order.updatedAt = new Date().toISOString();

      if (!order.auditTrail) order.auditTrail = [];
      order.auditTrail.push({
        action: 'INSTALLATION_COMPLETED',
        deviceId,
        techId,
        location,
        at: new Date().toISOString()
      });

      // Commit
      updateCallback();

      // Emit event
      this.emit('ORDER_COMPLETED', { ...order, deviceId, location });

      console.log(`✅ [INSTALLATION] Completed for order ${orderId}, device transferred to consumer`);
      return { success: true };

    } catch (error) {
      console.error(`❌ [INSTALLATION] Failed:`, error.message);
      
      // Rollback
      Object.assign(order, backup.order);
      devices.clear();
      backup.devices.forEach((value, key) => {
        devices.set(key, value);
      });
      
      this.emit('ORDER_FAILED', { 
        action: 'COMPLETE_INSTALLATION', 
        orderId, 
        error: error.message 
      });
      throw error;
    }
  }

  /**
   * Audit logging with hash chain for tamper-evidence
   */
  auditLog(eventType, data) {
    const timestamp = new Date().toISOString();
    
    // Get previous hash
    const prevHash = this.auditLedger.length > 0 
      ? this.auditLedger[this.auditLedger.length - 1].hash 
      : '0'.repeat(64);
    
    // Create event data
    const eventData = {
      eventType,
      timestamp,
      data: JSON.stringify(data)
    };
    
    // Create hash
    const hashInput = prevHash + JSON.stringify(eventData);
    const hash = crypto.createHash('sha256').update(hashInput).digest('hex');
    
    // Add to ledger
    const entry = {
      ...eventData,
      hash,
      previousHash: prevHash
    };
    
    this.auditLedger.push(entry);
    
    // Keep only last 1000 entries in memory
    if (this.auditLedger.length > 1000) {
      this.auditLedger.shift();
    }
    
    return entry;
  }

  /**
   * Verify audit ledger integrity
   */
  verifyAuditLedger() {
    for (let i = 1; i < this.auditLedger.length; i++) {
      const prevEntry = this.auditLedger[i - 1];
      const currEntry = this.auditLedger[i];
      
      // Verify hash chain
      const eventData = {
        eventType: currEntry.eventType,
        timestamp: currEntry.timestamp,
        data: currEntry.data
      };
      
      const hashInput = prevEntry.hash + JSON.stringify(eventData);
      const expectedHash = crypto.createHash('sha256').update(hashInput).digest('hex');
      
      if (currEntry.hash !== expectedHash) {
        throw new Error(`Audit ledger tampered at index ${i}, timestamp ${currEntry.timestamp}`);
      }
    }
    
    return true;
  }

  /**
   * Get audit trail for an order
   */
  getOrderAuditTrail(orderId) {
    return this.auditLedger.filter(entry => {
      try {
        const data = JSON.parse(entry.data);
        return data.orderId === orderId;
      } catch {
        return false;
      }
    });
  }

  /**
   * Get statistics
   */
  getStatistics() {
    const eventTypes = {};
    this.auditLedger.forEach(entry => {
      eventTypes[entry.eventType] = (eventTypes[entry.eventType] || 0) + 1;
    });

    return {
      totalEvents: this.auditLedger.length,
      eventTypes,
      ledgerIntegrity: this.verifyAuditLedger(),
      autoApproveThreshold: this.AUTO_APPROVE_THRESHOLD
    };
  }
}

module.exports = OrderAutomation;
