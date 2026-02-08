/**
 * Local Auto-Progression Script for Demo Orders
 * 
 * This script automatically progresses orders through their lifecycle
 * for demonstration purposes in local development.
 * 
 * Progression: ORDER_PLACED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
 */

const http = require('http');

const API_BASE = 'http://localhost:3002';

// Status progression map
const STATUS_PROGRESSION = {
  'ORDER_PLACED': 'SHIPPED',
  'SHIPPED': 'OUT_FOR_DELIVERY',
  'OUT_FOR_DELIVERY': 'DELIVERED',
  'pending': 'ORDER_PLACED'  // Handle old status format
};

/**
 * Make HTTP request
 */
function makeRequest(method, path, data = null, token = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, API_BASE);
    
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    const req = http.request(options, (res) => {
      let body = '';
      
      res.on('data', (chunk) => {
        body += chunk;
      });
      
      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          resolve({ statusCode: res.statusCode, data: response });
        } catch (e) {
          resolve({ statusCode: res.statusCode, data: body });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (data) {
      req.write(JSON.stringify(data));
    }
    
    req.end();
  });
}

/**
 * Get admin token (for demo purposes, we'll use a test token)
 */
async function getAdminToken() {
  // In local dev, we need to login as admin first
  try {
    const response = await makeRequest('POST', '/api/auth/login', {
      email: 'admin@aquachain.com',
      password: 'admin123'  // Default demo password
    });
    
    if (response.data.success && response.data.token) {
      return response.data.token;
    }
  } catch (error) {
    console.log('⚠️  Could not get admin token, using mock token');
  }
  
  // Return a mock token for testing
  return 'mock_admin_token_for_testing';
}

/**
 * Get all orders
 */
async function getAllOrders(token) {
  try {
    const response = await makeRequest('GET', '/api/admin/orders', null, token);
    
    if (response.data.success) {
      return response.data.orders || [];
    }
  } catch (error) {
    console.error('Error fetching orders:', error.message);
  }
  
  return [];
}

/**
 * Update order status
 */
async function updateOrderStatus(orderId, newStatus, token) {
  try {
    const response = await makeRequest(
      'PUT',
      `/api/orders/${orderId}/status`,
      {
        status: newStatus,
        reason: `Auto-progressed to ${newStatus}`,
        metadata: {
          autoProgressed: true,
          timestamp: new Date().toISOString()
        }
      },
      token
    );
    
    return response.data.success;
  } catch (error) {
    console.error(`Error updating order ${orderId}:`, error.message);
    return false;
  }
}

/**
 * Main auto-progression logic
 */
async function progressOrders() {
  console.log('🚀 Starting local auto-progression...\n');
  
  // Get admin token
  const token = await getAdminToken();
  console.log('✅ Got authentication token\n');
  
  // Get all orders
  const orders = await getAllOrders(token);
  console.log(`📦 Found ${orders.length} total orders\n`);
  
  if (orders.length === 0) {
    console.log('ℹ️  No orders to progress');
    return;
  }
  
  // Filter orders that can be progressed
  const progressableOrders = orders.filter(order => {
    const nextStatus = STATUS_PROGRESSION[order.status];
    return nextStatus && order.status !== 'DELIVERED' && order.status !== 'CANCELLED';
  });
  
  console.log(`🔄 ${progressableOrders.length} orders can be progressed\n`);
  
  if (progressableOrders.length === 0) {
    console.log('ℹ️  No orders ready for progression');
    return;
  }
  
  // Progress each order
  let successCount = 0;
  let failCount = 0;
  
  for (const order of progressableOrders) {
    const currentStatus = order.status;
    const nextStatus = STATUS_PROGRESSION[currentStatus];
    
    console.log(`📦 Order ${order.orderId.substring(0, 12)}...`);
    console.log(`   Current: ${currentStatus}`);
    console.log(`   Next: ${nextStatus}`);
    
    const success = await updateOrderStatus(order.orderId, nextStatus, token);
    
    if (success) {
      console.log(`   ✅ Successfully progressed\n`);
      successCount++;
    } else {
      console.log(`   ❌ Failed to progress\n`);
      failCount++;
    }
  }
  
  console.log('═══════════════════════════════════════');
  console.log(`✅ Successfully progressed: ${successCount}`);
  console.log(`❌ Failed: ${failCount}`);
  console.log('═══════════════════════════════════════\n');
}

/**
 * Run with interval
 */
async function runWithInterval() {
  console.log('🔄 Auto-Progression Service Started');
  console.log('═══════════════════════════════════════');
  console.log('Progressing orders every 10 seconds...');
  console.log('Press Ctrl+C to stop\n');
  
  // Run immediately
  await progressOrders();
  
  // Then run every 10 seconds
  setInterval(async () => {
    console.log(`\n⏰ ${new Date().toLocaleTimeString()} - Running auto-progression...\n`);
    await progressOrders();
  }, 10000);
}

// Check if server is running
async function checkServer() {
  try {
    const response = await makeRequest('GET', '/api/health');
    if (response.statusCode === 200) {
      return true;
    }
  } catch (error) {
    return false;
  }
  return false;
}

// Main execution
(async () => {
  console.log('🔍 Checking if dev server is running...\n');
  
  const serverRunning = await checkServer();
  
  if (!serverRunning) {
    console.log('❌ Dev server is not running on http://localhost:3002');
    console.log('\nTo start the server:');
    console.log('  cd frontend && npm run start:full\n');
    process.exit(1);
  }
  
  console.log('✅ Dev server is running\n');
  
  // Check if we should run once or continuously
  const runOnce = process.argv.includes('--once');
  
  if (runOnce) {
    await progressOrders();
  } else {
    await runWithInterval();
  }
})();
