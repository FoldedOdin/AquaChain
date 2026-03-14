#!/usr/bin/env node
/**
 * Test Dashboard Direct Connection
 * This script tests if the dashboard can connect to the API and display device data
 */

const https = require('https');

// Configuration from the working API test
const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const DEVICE_ID = 'ESP32-001';

console.log('🧪 Dashboard Direct Connection Test');
console.log('=' .repeat(60));

/**
 * Make HTTPS request
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: 443,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'AquaChain-Dashboard/1.0',
        'Origin': 'http://localhost:3000',
        ...options.headers
      }
    };
    
    const req = https.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: jsonData
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: data
          });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (options.body) {
      req.write(JSON.stringify(options.body));
    }
    
    req.end();
  });
}

/**
 * Test device latest reading
 */
async function testLatestReading() {
  console.log('\n📊 Testing Latest Reading Endpoint');
  console.log('-'.repeat(50));
  
  try {
    const endpoint = `${API_BASE_URL}/api/device-readings/${DEVICE_ID}/latest`;
    console.log(`🔍 Endpoint: ${endpoint}`);
    
    const response = await makeRequest(endpoint);
    
    console.log(`📊 Status: ${response.status}`);
    
    if (response.status === 200 && response.data.success) {
      const reading = response.data.reading;
      console.log('✅ Latest reading retrieved successfully!');
      console.log(`📋 Reading Details:`);
      console.log(`   Timestamp: ${reading.timestamp}`);
      console.log(`   pH: ${reading.pH}`);
      console.log(`   Temperature: ${reading.temperature}°C`);
      console.log(`   TDS: ${reading.tds} ppm`);
      console.log(`   Turbidity: ${reading.turbidity} NTU`);
      console.log(`   WQI: ${reading.qualityScore || reading.wqi || 'N/A'}`);
      
      return {
        success: true,
        reading: reading
      };
    } else {
      console.log('❌ Failed to get reading');
      console.log(`📋 Response:`, response.data);
      return { success: false };
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    return { success: false };
  }
}

/**
 * Test device history
 */
async function testDeviceHistory() {
  console.log('\n📈 Testing Device History Endpoint');
  console.log('-'.repeat(50));
  
  try {
    const endpoint = `${API_BASE_URL}/api/device-readings/${DEVICE_ID}/history?days=7`;
    console.log(`🔍 Endpoint: ${endpoint}`);
    
    const response = await makeRequest(endpoint);
    
    console.log(`📊 Status: ${response.status}`);
    
    if (response.status === 200 && response.data.success) {
      const readings = response.data.readings;
      console.log('✅ Device history retrieved successfully!');
      console.log(`📋 Found ${readings.length} readings`);
      
      if (readings.length > 0) {
        console.log(`📋 Latest 3 readings:`);
        readings.slice(0, 3).forEach((reading, index) => {
          console.log(`   ${index + 1}. ${reading.timestamp} - pH: ${reading.pH}, Temp: ${reading.temperature}°C`);
        });
      }
      
      return {
        success: true,
        readings: readings
      };
    } else {
      console.log('❌ Failed to get history');
      console.log(`📋 Response:`, response.data);
      return { success: false };
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    return { success: false };
  }
}

/**
 * Generate frontend code snippet
 */
function generateFrontendCode(latestResult, historyResult) {
  console.log('\n💻 Frontend Integration Code');
  console.log('-'.repeat(50));
  
  if (latestResult.success) {
    console.log('✅ Use this code in your React component:');
    console.log('');
    console.log('```javascript');
    console.log('// In your React component');
    console.log('const API_BASE_URL = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev";');
    console.log('');
    console.log('const fetchLatestReading = async () => {');
    console.log('  try {');
    console.log(`    const response = await fetch(\`\${API_BASE_URL}/api/device-readings/\${deviceId}/latest\`);`);
    console.log('    const data = await response.json();');
    console.log('    ');
    console.log('    if (data.success && data.reading) {');
    console.log('      setWaterQualityData(data.reading);');
    console.log('      setWqi(data.reading.qualityScore || data.reading.wqi || 0);');
    console.log('    }');
    console.log('  } catch (error) {');
    console.log('    console.error("Error fetching reading:", error);');
    console.log('  }');
    console.log('};');
    console.log('```');
    console.log('');
    
    // Show expected data structure
    console.log('📋 Expected data structure:');
    console.log('```json');
    console.log(JSON.stringify({
      success: true,
      reading: {
        timestamp: latestResult.reading.timestamp,
        pH: latestResult.reading.pH,
        temperature: latestResult.reading.temperature,
        tds: latestResult.reading.tds,
        turbidity: latestResult.reading.turbidity,
        qualityScore: latestResult.reading.qualityScore
      },
      deviceId: DEVICE_ID
    }, null, 2));
    console.log('```');
  }
}

/**
 * Main test function
 */
async function main() {
  console.log(`🎯 Testing API connection for device: ${DEVICE_ID}`);
  console.log(`🌐 API Base URL: ${API_BASE_URL}`);
  
  // Test latest reading
  const latestResult = await testLatestReading();
  
  // Test device history
  const historyResult = await testDeviceHistory();
  
  // Generate frontend code
  generateFrontendCode(latestResult, historyResult);
  
  // Summary
  console.log('\n📋 SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Latest Reading: ${latestResult.success ? 'Working' : 'Failed'}`);
  console.log(`✅ Device History: ${historyResult.success ? 'Working' : 'Failed'}`);
  
  if (latestResult.success && historyResult.success) {
    console.log('\n🎉 API is fully functional!');
    console.log('💡 To fix the dashboard:');
    console.log('   1. Update frontend/.env.local with correct API_BASE_URL');
    console.log('   2. Restart the frontend development server');
    console.log('   3. The dashboard should now show device data');
    console.log('');
    console.log('🔧 Quick fix command:');
    console.log('   echo "REACT_APP_API_ENDPOINT=https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev" > frontend/.env.local');
  } else {
    console.log('\n🔧 Issues found - check API configuration');
  }
}

// Run the test
main().catch(console.error);