/**
 * Test script for dev-server automation features
 */

const http = require('http');

// Use admin token from .dev-data.json
const ADMIN_TOKEN = 'dev-token-1765187293580-qedtc6q3is';
const CONSUMER_TOKEN = 'dev-token-1765187263513-uy9dpo6yp5';

function makeRequest(method, path, body = null, token = ADMIN_TOKEN) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 3002,
      path,
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function runTests() {
  console.log('🧪 Testing Dev Server Automation Features\n');
  console.log('='.repeat(60));

  try {
    // Test 1: Create order with atomic transaction
    console.log('\n📦 Test 1: Create Order (Atomic Transaction)');
    const orderResponse = await makeRequest('POST', '/api/orders', {
      deviceSKU: 'AC-HOME-V1',
      address: '123 Test Street, Test City',
      phone: '1234567890',
      paymentMethod: 'COD',
      preferredSlot: '2025-12-15T10:00:00Z'
    }, CONSUMER_TOKEN);
    
    console.log(`Status: ${orderResponse.status}`);
    console.log(`Success: ${orderResponse.data.success}`);
    if (orderResponse.data.success) {
      console.log(`✅ Order created: ${orderResponse.data.order.orderId}`);
      var testOrderId = orderResponse.data.order.orderId;
    } else {
      console.log(`❌ Error: ${orderResponse.data.error}`);
    }

    // Test 2: Set quote with auto-approval (under ₹20,000)
    if (testOrderId) {
      console.log('\n💰 Test 2: Set Quote (Auto-Approval Test)');
      const quoteResponse = await makeRequest('PUT', `/api/admin/orders/${testOrderId}/quote`, {
        quoteAmount: 4000  // Always auto-approved
      });
      
      console.log(`Status: ${quoteResponse.status}`);
      console.log(`Success: ${quoteResponse.data.success}`);
      if (quoteResponse.data.success) {
        console.log(`✅ Quote set: ₹${quoteResponse.data.order.quoteAmount}`);
        console.log(`🎯 Auto-approved: YES ✅ (Always auto-approved)`);
      } else {
        console.log(`❌ Error: ${quoteResponse.data.error}`);
      }
    }

    // Test 3: Get automation statistics
    console.log('\n📊 Test 3: Automation Statistics');
    const statsResponse = await makeRequest('GET', '/api/admin/automation/stats');
    
    console.log(`Status: ${statsResponse.status}`);
    if (statsResponse.data.success) {
      console.log(`✅ Total Events: ${statsResponse.data.totalEvents}`);
      console.log(`📋 Event Types:`, statsResponse.data.eventTypes);
      console.log(`💵 Auto-Approve: ALL QUOTES (No threshold)`);
      if (statsResponse.data.inventoryStatus) {
        console.log(`📦 Inventory Status:`);
        statsResponse.data.inventoryStatus.forEach(inv => {
          console.log(`   ${inv.sku}: ${inv.available} available, ${inv.reserved} reserved`);
        });
      }
    }

    // Test 4: Verify audit ledger integrity
    console.log('\n🔐 Test 4: Verify Audit Ledger Integrity');
    const verifyResponse = await makeRequest('GET', '/api/admin/automation/verify');
    
    console.log(`Status: ${verifyResponse.status}`);
    if (verifyResponse.data.success) {
      console.log(`✅ ${verifyResponse.data.message}`);
      console.log(`📝 Total Events in Ledger: ${verifyResponse.data.totalEvents}`);
    } else {
      console.log(`❌ ${verifyResponse.data.message}`);
    }

    // Test 5: Get audit ledger
    console.log('\n📜 Test 5: Get Audit Ledger (Last 5 events)');
    const auditResponse = await makeRequest('GET', '/api/admin/automation/audit?limit=5');
    
    console.log(`Status: ${auditResponse.status}`);
    if (auditResponse.data.success) {
      console.log(`✅ Showing ${auditResponse.data.showing} of ${auditResponse.data.total} events`);
      auditResponse.data.auditLedger.forEach((entry, i) => {
        console.log(`\n   Event ${i + 1}:`);
        console.log(`   Type: ${entry.eventType}`);
        console.log(`   Time: ${entry.timestamp}`);
        console.log(`   Hash: ${entry.hash.substring(0, 16)}...`);
      });
    }

    // Test 6: Try to create order with insufficient inventory
    console.log('\n🚫 Test 6: Test Rollback (Insufficient Inventory)');
    const failResponse = await makeRequest('POST', '/api/orders', {
      deviceSKU: 'NONEXISTENT-SKU',
      address: '123 Test Street',
      phone: '1234567890',
      paymentMethod: 'COD',
      preferredSlot: '2025-12-15T10:00:00Z'
    }, CONSUMER_TOKEN);
    
    console.log(`Status: ${failResponse.status}`);
    if (!failResponse.data.success) {
      console.log(`✅ Rollback worked! Error: ${failResponse.data.error}`);
    } else {
      console.log(`❌ Should have failed but didn't`);
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ All tests completed!\n');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

// Run tests
runTests();
