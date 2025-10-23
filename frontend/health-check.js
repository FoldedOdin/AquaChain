#!/usr/bin/env node

/**
 * AquaChain Health Check
 * Verifies that all services are running correctly
 */

const fetch = require('node-fetch');

const FRONTEND_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:3002';

async function checkService(name, url, expectedContent) {
  try {
    console.log(`🔍 Checking ${name}...`);
    const response = await fetch(url, { timeout: 5000 });
    
    if (!response.ok) {
      console.log(`❌ ${name}: HTTP ${response.status}`);
      return false;
    }
    
    if (expectedContent) {
      const text = await response.text();
      if (!text.includes(expectedContent)) {
        console.log(`❌ ${name}: Unexpected content`);
        return false;
      }
    }
    
    console.log(`✅ ${name}: OK`);
    return true;
  } catch (error) {
    console.log(`❌ ${name}: ${error.message}`);
    return false;
  }
}

async function healthCheck() {
  console.log('🏥 AquaChain Health Check\n');
  
  const checks = [
    {
      name: 'Development API Server',
      url: `${API_URL}/api/health`,
      expected: 'aquachain-dev-server'
    },
    {
      name: 'Frontend Application',
      url: FRONTEND_URL,
      expected: 'AquaChain'
    }
  ];
  
  let allHealthy = true;
  
  for (const check of checks) {
    const isHealthy = await checkService(check.name, check.url, check.expected);
    if (!isHealthy) {
      allHealthy = false;
    }
  }
  
  console.log('\n📊 Service Status Summary:');
  
  if (allHealthy) {
    console.log('🎉 All services are healthy!');
    console.log('\n🚀 Ready to use:');
    console.log(`- Frontend: ${FRONTEND_URL}`);
    console.log(`- API: ${API_URL}`);
    console.log('\n💡 Try the authentication flow:');
    console.log('1. Open the frontend URL');
    console.log('2. Click "Get Started"');
    console.log('3. Sign up with any email/password');
    console.log('4. Watch the verification process');
    console.log('5. Sign in with the same credentials');
  } else {
    console.log('⚠️  Some services are not responding');
    console.log('\n🔧 Troubleshooting:');
    console.log('1. Make sure you ran: npm run start:full');
    console.log('2. Check that ports 3000 and 3002 are available');
    console.log('3. Wait a few seconds for services to start');
    console.log('4. Run this health check again');
  }
  
  process.exit(allHealthy ? 0 : 1);
}

// Run the health check
healthCheck();