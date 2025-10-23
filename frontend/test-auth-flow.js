#!/usr/bin/env node

/**
 * Test Authentication Flow
 * Tests the complete signup -> email verification -> login flow
 */

const fetch = require('node-fetch');

const API_BASE = 'http://localhost:3002';
const TEST_USER = {
  email: 'test@example.com',
  password: 'password123',
  name: 'Test User',
  role: 'consumer'
};

async function testAuthFlow() {
  console.log('🧪 Testing AquaChain Authentication Flow\n');

  try {
    // Step 1: Test signup
    console.log('1️⃣ Testing Signup...');
    const signupResponse = await fetch(`${API_BASE}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(TEST_USER)
    });

    const signupResult = await signupResponse.json();
    console.log('Signup Response:', signupResult);

    if (!signupResponse.ok) {
      throw new Error(`Signup failed: ${signupResult.error}`);
    }

    console.log('✅ Signup successful!\n');

    // Step 2: Test immediate login (should fail - email not verified)
    console.log('2️⃣ Testing Login (before verification)...');
    const loginResponse1 = await fetch(`${API_BASE}/api/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: TEST_USER.email,
        password: TEST_USER.password
      })
    });

    const loginResult1 = await loginResponse1.json();
    console.log('Login Response (before verification):', loginResult1);

    if (loginResponse1.ok) {
      console.log('⚠️  Warning: Login succeeded before email verification');
    } else {
      console.log('✅ Login correctly blocked before verification\n');
    }

    // Step 3: Wait for auto-verification (2 seconds)
    console.log('3️⃣ Waiting for email verification (2 seconds)...');
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Step 4: Check verification status
    console.log('4️⃣ Checking verification status...');
    const statusResponse = await fetch(`${API_BASE}/api/auth/verification-status/${encodeURIComponent(TEST_USER.email)}`);
    const statusResult = await statusResponse.json();
    console.log('Verification Status:', statusResult);

    if (statusResult.emailVerified) {
      console.log('✅ Email verified successfully!\n');
    } else {
      console.log('❌ Email not verified yet\n');
    }

    // Step 5: Test login after verification
    console.log('5️⃣ Testing Login (after verification)...');
    const loginResponse2 = await fetch(`${API_BASE}/api/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: TEST_USER.email,
        password: TEST_USER.password
      })
    });

    const loginResult2 = await loginResponse2.json();
    console.log('Login Response (after verification):', loginResult2);

    if (loginResponse2.ok) {
      console.log('✅ Login successful after verification!\n');
    } else {
      console.log('❌ Login failed after verification:', loginResult2.error);
    }

    // Step 6: Test wrong password
    console.log('6️⃣ Testing Login (wrong password)...');
    const loginResponse3 = await fetch(`${API_BASE}/api/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: TEST_USER.email,
        password: 'wrongpassword'
      })
    });

    const loginResult3 = await loginResponse3.json();
    console.log('Login Response (wrong password):', loginResult3);

    if (!loginResponse3.ok) {
      console.log('✅ Wrong password correctly rejected\n');
    } else {
      console.log('❌ Wrong password was accepted (security issue!)\n');
    }

    // Step 7: List all dev users
    console.log('7️⃣ Checking dev users...');
    const usersResponse = await fetch(`${API_BASE}/api/auth/dev-users`);
    const usersResult = await usersResponse.json();
    console.log('Dev Users:', usersResult);

    console.log('\n🎉 Authentication flow test completed!');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the test
testAuthFlow();