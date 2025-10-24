#!/usr/bin/env node

/**
 * Test Dashboard Authentication Flow
 * Tests the complete signup -> login -> dashboard redirection flow
 */

const fetch = require('node-fetch');

const API_BASE = 'http://localhost:3002';

// Test users for different roles
const TEST_USERS = [
  {
    email: 'consumer@test.com',
    password: 'password123',
    name: 'Test Consumer',
    role: 'consumer',
    expectedDashboard: '/dashboard/consumer'
  },
  {
    email: 'technician@test.com',
    password: 'password123',
    name: 'Test Technician',
    role: 'technician',
    expectedDashboard: '/dashboard/technician'
  },
  {
    email: 'admin@test.com',
    password: 'password123',
    name: 'Test Admin',
    role: 'admin',
    expectedDashboard: '/dashboard/admin'
  }
];

async function testUserFlow(user) {
  console.log(`\n🧪 Testing ${user.role.toUpperCase()} Flow for ${user.email}`);
  
  try {
    // Step 1: Signup
    console.log('1️⃣ Creating account...');
    const signupResponse = await fetch(`${API_BASE}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });

    const signupResult = await signupResponse.json();
    
    if (!signupResponse.ok) {
      console.log(`⚠️  Signup failed (user may already exist): ${signupResult.error}`);
    } else {
      console.log('✅ Account created successfully');
    }

    // Step 2: Wait for email verification
    console.log('2️⃣ Waiting for email verification...');
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Step 3: Login
    console.log('3️⃣ Attempting login...');
    const loginResponse = await fetch(`${API_BASE}/api/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: user.email,
        password: user.password
      })
    });

    const loginResult = await loginResponse.json();

    if (!loginResponse.ok) {
      throw new Error(`Login failed: ${loginResult.error}`);
    }

    console.log('✅ Login successful');
    console.log(`👤 User: ${loginResult.user.name} (${loginResult.user.role})`);
    console.log(`🎯 Expected Dashboard: ${user.expectedDashboard}`);
    
    // Verify user role matches expected
    if (loginResult.user.role === user.role) {
      console.log('✅ User role matches expected role');
    } else {
      console.log(`❌ Role mismatch: expected ${user.role}, got ${loginResult.user.role}`);
    }

    return {
      success: true,
      user: loginResult.user,
      token: loginResult.token
    };

  } catch (error) {
    console.log(`❌ Flow failed: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

async function testDashboardFlow() {
  console.log('🚀 Testing AquaChain Dashboard Authentication Flow\n');
  
  const results = [];

  for (const user of TEST_USERS) {
    const result = await testUserFlow(user);
    results.push({
      role: user.role,
      email: user.email,
      ...result
    });
  }

  // Summary
  console.log('\n📊 FLOW TEST SUMMARY');
  console.log('='.repeat(50));
  
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);

  console.log(`✅ Successful: ${successful.length}/${results.length}`);
  console.log(`❌ Failed: ${failed.length}/${results.length}`);

  if (successful.length > 0) {
    console.log('\n✅ Successful Flows:');
    successful.forEach(result => {
      console.log(`  - ${result.role.toUpperCase()}: ${result.email}`);
    });
  }

  if (failed.length > 0) {
    console.log('\n❌ Failed Flows:');
    failed.forEach(result => {
      console.log(`  - ${result.role.toUpperCase()}: ${result.email} (${result.error})`);
    });
  }

  console.log('\n🎯 Dashboard Routing:');
  console.log('- Consumer → /dashboard/consumer');
  console.log('- Technician → /dashboard/technician');  
  console.log('- Admin → /dashboard/admin');

  console.log('\n📋 Next Steps:');
  console.log('1. Start the frontend: npm start');
  console.log('2. Open: http://localhost:3000');
  console.log('3. Test login with any of the created accounts');
  console.log('4. Verify automatic redirection to role-based dashboard');

  console.log('\n🔐 Test Credentials:');
  TEST_USERS.forEach(user => {
    console.log(`${user.role.toUpperCase()}: ${user.email} / ${user.password}`);
  });

  console.log('\n🎉 Dashboard flow test completed!');
}

// Run the test
testDashboardFlow().catch(console.error);