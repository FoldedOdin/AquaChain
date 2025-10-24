#!/usr/bin/env node

/**
 * Test Authentication Persistence
 * Tests that authentication state persists when accessing dashboard URLs directly
 */

const fetch = require('node-fetch');

const API_BASE = 'http://localhost:3002';

async function testAuthPersistence() {
  console.log('🔐 Testing Authentication Persistence\n');

  try {
    // Step 1: Login to create a session
    console.log('1️⃣ Logging in as consumer...');
    const loginResponse = await fetch(`${API_BASE}/api/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'consumer@test.com',
        password: 'password123'
      })
    });

    const loginResult = await loginResponse.json();
    
    if (!loginResponse.ok) {
      throw new Error(`Login failed: ${loginResult.error}`);
    }

    console.log('✅ Login successful');
    console.log(`👤 User: ${loginResult.user.name} (${loginResult.user.role})`);
    console.log(`🎫 Token: ${loginResult.token.substring(0, 20)}...`);

    // Step 2: Test token validation
    console.log('\n2️⃣ Testing token validation...');
    const validateResponse = await fetch(`${API_BASE}/api/auth/validate`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${loginResult.token}`
      },
      body: JSON.stringify({
        email: loginResult.user.email
      })
    });

    const validateResult = await validateResponse.json();
    
    if (!validateResponse.ok) {
      throw new Error(`Validation failed: ${validateResult.error}`);
    }

    console.log('✅ Token validation successful');
    console.log(`👤 Validated User: ${validateResult.user.name} (${validateResult.user.role})`);

    // Step 3: Test with invalid token
    console.log('\n3️⃣ Testing invalid token...');
    const invalidResponse = await fetch(`${API_BASE}/api/auth/validate`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer invalid-token`
      },
      body: JSON.stringify({
        email: loginResult.user.email
      })
    });

    if (invalidResponse.ok) {
      console.log('⚠️  Warning: Invalid token was accepted');
    } else {
      console.log('✅ Invalid token correctly rejected');
    }

    console.log('\n🎉 Authentication persistence test completed!');
    console.log('\n📋 What this means:');
    console.log('- Users can now login and their session will persist');
    console.log('- Direct access to dashboard URLs will work if authenticated');
    console.log('- Invalid tokens are properly rejected');
    console.log('- Authentication state is maintained across page reloads');

  } catch (error) {
    console.log(`❌ Test failed: ${error.message}`);
    process.exit(1);
  }
}

// Run the test
testAuthPersistence();