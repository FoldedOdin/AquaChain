#!/usr/bin/env node

/**
 * AquaChain Authentication Fix Script
 * 
 * This script helps diagnose and fix the "API error: undefined" issue
 * that occurs when development tokens are used with production APIs.
 */

console.log('🔧 AquaChain Authentication Diagnostic Tool\n');

// Check if we're in a browser environment
if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
  console.log('📱 Running in browser environment');
  
  // Check current tokens
  const aquachainToken = localStorage.getItem('aquachain_token');
  const authToken = localStorage.getItem('authToken');
  
  console.log('🔑 Current Authentication Status:');
  console.log(`   aquachain_token: ${aquachainToken ? 'Present' : 'Missing'}`);
  console.log(`   authToken: ${authToken ? 'Present' : 'Missing'}`);
  
  if (aquachainToken) {
    const isDevelopmentToken = aquachainToken.startsWith('dev-token-');
    console.log(`   Token type: ${isDevelopmentToken ? 'Development' : 'Production'}`);
    
    if (isDevelopmentToken) {
      console.log('\n⚠️  ISSUE DETECTED:');
      console.log('   You are using a development token with a production API.');
      console.log('   This will cause "API error: undefined" messages.');
      console.log('\n🔧 SOLUTIONS:');
      console.log('   1. Use proper Cognito authentication (recommended)');
      console.log('   2. Switch to mock data for development');
      console.log('   3. Set up a local backend server');
      
      console.log('\n🚀 Quick Fix - Clear tokens and re-login:');
      console.log('   localStorage.removeItem("aquachain_token");');
      console.log('   localStorage.removeItem("authToken");');
      console.log('   // Then refresh page and login again');
    } else {
      console.log('\n✅ Token appears to be valid');
    }
  } else {
    console.log('\n⚠️  ISSUE DETECTED:');
    console.log('   No authentication token found.');
    console.log('   Please log in to access the dashboard.');
  }
  
} else {
  console.log('📋 Running in Node.js environment');
  console.log('\n🔧 To diagnose authentication issues:');
  console.log('   1. Open your browser developer console');
  console.log('   2. Go to the AquaChain dashboard');
  console.log('   3. Run: localStorage.getItem("aquachain_token")');
  console.log('   4. Check if the token starts with "dev-token-"');
  console.log('\n💡 If you see "dev-token-", you need proper authentication.');
}

console.log('\n📚 For more help, check the documentation or contact support.');