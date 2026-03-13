/**
 * Verification Script for Mock Data Fix
 * 
 * Run this in browser console to verify the fix is working
 */

console.log('🔍 Verifying Mock Data Fix...\n');

// Check if mock data flag is set
const useMockData = localStorage.getItem('REACT_APP_USE_MOCK_DATA');
console.log('📊 Mock Data Flag:', useMockData);

// Check authentication tokens
const aquachainToken = localStorage.getItem('aquachain_token');
const authToken = localStorage.getItem('authToken');
console.log('🔑 Tokens:');
console.log('   aquachain_token:', aquachainToken ? 'Present' : 'Missing');
console.log('   authToken:', authToken ? 'Present' : 'Missing');

// Check if unified data service is working
if (typeof window !== 'undefined' && window.unifiedDataService) {
  console.log('✅ Unified Data Service: Available');
  console.log('📊 Using Mock Data:', window.unifiedDataService.isUsingMockData());
} else {
  console.log('⚠️  Unified Data Service: Not available in global scope');
}

// Check for the data source indicator
const indicator = document.querySelector('[class*="Using Mock Data"]');
if (indicator) {
  console.log('✅ Data Source Indicator: Visible');
} else {
  console.log('ℹ️  Data Source Indicator: Not visible (normal if using real API)');
}

// Check console for data service messages
console.log('\n📝 Expected Console Messages:');
console.log('   - "📊 Using mock data for devices"');
console.log('   - "🔄 Switching to mock data: ..."');
console.log('   - Blue indicator showing "Using Mock Data"');

console.log('\n✅ Verification Complete!');
console.log('If you see mock data messages above, the fix is working correctly.');

// Test the data service selector logic
try {
  const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  const isDevelopmentToken = token && token.startsWith('dev-token-');
  const isProductionAPI = (process.env.REACT_APP_API_ENDPOINT || '').includes('amazonaws.com');
  const shouldUseMock = !token || (isDevelopmentToken && isProductionAPI) || useMockData === 'true';
  
  console.log('\n🧪 Logic Test:');
  console.log('   Should use mock data:', shouldUseMock);
  console.log('   Reason:', 
    !token ? 'No token' :
    isDevelopmentToken && isProductionAPI ? 'Dev token + Prod API' :
    useMockData === 'true' ? 'Explicitly enabled' :
    'Using real API'
  );
} catch (error) {
  console.log('⚠️  Logic test failed:', error.message);
}