/**
 * Complete Authentication Fix
 * 
 * This script will:
 * 1. Clear mock data mode
 * 2. Clear old tokens
 * 3. Test the authentication endpoint
 * 4. Provide instructions for proper login
 */

console.log('🔧 AquaChain Complete Authentication Fix\n');

// Step 1: Clear mock data mode and old tokens
console.log('🧹 Step 1: Clearing mock data mode and old tokens...');
localStorage.removeItem('REACT_APP_USE_MOCK_DATA');
localStorage.removeItem('aquachain_token');
localStorage.removeItem('authToken');
console.log('✅ Cleared mock data flag and tokens');

// Step 2: Test authentication endpoint
console.log('\n📡 Step 2: Testing authentication endpoint...');

const API_ENDPOINT = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

async function testAuthEndpoint() {
  try {
    // Test the main auth endpoint
    const response = await fetch(`${API_ENDPOINT}/api/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'testpassword123'
      }),
    });

    console.log('📊 Auth endpoint status:', response.status);
    
    if (response.status === 404) {
      console.log('❌ Auth endpoint not found at /api/auth/signin');
      
      // Try alternative endpoint
      const altResponse = await fetch(`${API_ENDPOINT}/auth/signin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'testpassword123'
        }),
      });
      
      console.log('📊 Alternative endpoint status:', altResponse.status);
      
      if (altResponse.status !== 404) {
        console.log('✅ Found auth endpoint at /auth/signin');
        console.log('⚠️  Frontend needs to be updated to use /auth/signin instead of /api/auth/signin');
        return '/auth/signin';
      } else {
        console.log('❌ Auth service not deployed or not accessible');
        return null;
      }
    } else {
      console.log('✅ Auth endpoint found at /api/auth/signin');
      const data = await response.json();
      
      if (data.error && (data.error.includes('Invalid') || data.error.includes('password'))) {
        console.log('✅ Endpoint is working (expected error for dummy credentials)');
        return '/api/auth/signin';
      } else {
        console.log('📦 Unexpected response:', data);
        return '/api/auth/signin';
      }
    }
    
  } catch (error) {
    console.error('❌ Auth endpoint test failed:', error);
    return null;
  }
}

// Step 3: Provide login function
function createLoginFunction(endpoint) {
  if (!endpoint) {
    console.log('\n❌ Cannot create login function - auth endpoint not available');
    return;
  }
  
  console.log('\n🔐 Step 3: Login function created');
  console.log('Use this function to log in with your credentials:');
  console.log('');
  console.log(`window.loginToAquaChain = async function(email, password) {`);
  console.log(`  try {`);
  console.log(`    console.log('🔐 Attempting login...');`);
  console.log(`    const response = await fetch('${API_ENDPOINT}${endpoint}', {`);
  console.log(`      method: 'POST',`);
  console.log(`      headers: { 'Content-Type': 'application/json' },`);
  console.log(`      body: JSON.stringify({ email, password })`);
  console.log(`    });`);
  console.log(`    `);
  console.log(`    const data = await response.json();`);
  console.log(`    console.log('📦 Login response:', data);`);
  console.log(`    `);
  console.log(`    if (response.ok && data.token) {`);
  console.log(`      localStorage.setItem('aquachain_token', data.token);`);
  console.log(`      localStorage.setItem('aquachain_user', JSON.stringify(data.user));`);
  console.log(`      console.log('✅ Login successful! Token stored.');`);
  console.log(`      console.log('🔄 Refreshing page...');`);
  console.log(`      window.location.reload();`);
  console.log(`    } else {`);
  console.log(`      console.error('❌ Login failed:', data.error || 'Unknown error');`);
  console.log(`    }`);
  console.log(`  } catch (error) {`);
  console.log(`    console.error('❌ Login error:', error);`);
  console.log(`  }`);
  console.log(`};`);
  
  // Actually create the function
  window.loginToAquaChain = async function(email, password) {
    try {
      console.log('🔐 Attempting login...');
      const response = await fetch(`${API_ENDPOINT}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      console.log('📦 Login response:', data);
      
      if (response.ok && data.token) {
        localStorage.setItem('aquachain_token', data.token);
        localStorage.setItem('aquachain_user', JSON.stringify(data.user));
        console.log('✅ Login successful! Token stored.');
        console.log('🔄 Refreshing page...');
        window.location.reload();
      } else {
        console.error('❌ Login failed:', data.error || 'Unknown error');
      }
    } catch (error) {
      console.error('❌ Login error:', error);
    }
  };
}

// Run the test and setup
testAuthEndpoint().then(endpoint => {
  createLoginFunction(endpoint);
  
  console.log('\n🎯 NEXT STEPS:');
  console.log('1. Call: loginToAquaChain("your-email@example.com", "your-password")');
  console.log('2. If successful, the page will refresh with real data');
  console.log('3. If login fails, check your credentials or contact support');
  console.log('');
  console.log('📚 Example usage:');
  console.log('loginToAquaChain("user@example.com", "mypassword123")');
});

console.log('\n⏳ Testing authentication endpoint...');