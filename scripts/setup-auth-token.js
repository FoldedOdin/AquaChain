/**
 * Authentication Token Setup Helper
 * Sets up proper authentication tokens for testing
 */

console.log('🔑 Authentication Token Setup Helper');

// Option 1: Development Token (for testing without real auth)
function setDevelopmentToken() {
  const devToken = 'dev-token-' + Date.now();
  localStorage.setItem('aquachain_token', devToken);
  localStorage.setItem('authToken', devToken);
  console.log('✅ Development token set:', devToken);
  console.log('⚠️ This will only work with mock data or local backend');
}

// Option 2: Real JWT Token (paste your actual token here)
function setRealToken(jwtToken) {
  if (!jwtToken) {
    console.error('❌ Please provide a JWT token');
    return;
  }
  
  // Validate JWT format
  const parts = jwtToken.split('.');
  if (parts.length !== 3) {
    console.error('❌ Invalid JWT format - should have 3 parts separated by dots');
    return;
  }
  
  localStorage.setItem('aquachain_token', jwtToken);
  localStorage.setItem('authToken', jwtToken);
  console.log('✅ Real JWT token set');
  console.log('Token preview:', jwtToken.substring(0, 50) + '...');
}

// Option 3: Clear all tokens
function clearTokens() {
  localStorage.removeItem('aquachain_token');
  localStorage.removeItem('authToken');
  console.log('✅ All tokens cleared');
}

// Option 4: Check current tokens
function checkTokens() {
  const aquachainToken = localStorage.getItem('aquachain_token');
  const authToken = localStorage.getItem('authToken');
  
  console.log('Current tokens:');
  console.log('aquachain_token:', aquachainToken ? aquachainToken.substring(0, 50) + '...' : 'None');
  console.log('authToken:', authToken ? authToken.substring(0, 50) + '...' : 'None');
}

// Make functions available globally
window.setDevelopmentToken = setDevelopmentToken;
window.setRealToken = setRealToken;
window.clearTokens = clearTokens;
window.checkTokens = checkTokens;

console.log('\n🎯 Available functions:');
console.log('- setDevelopmentToken() - Set a development token for testing');
console.log('- setRealToken("your-jwt-here") - Set a real JWT token');
console.log('- clearTokens() - Remove all tokens');
console.log('- checkTokens() - Check current token status');

// Auto-check current status
checkTokens();