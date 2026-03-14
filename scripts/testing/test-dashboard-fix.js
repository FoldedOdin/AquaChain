#!/usr/bin/env node
/**
 * Test Dashboard Fix
 * This script verifies the dashboard should now work with the correct API configuration
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

console.log('🔧 Dashboard Fix Verification');
console.log('=' .repeat(60));

/**
 * Check environment configuration
 */
function checkEnvironmentConfig() {
  console.log('\n📋 Checking Environment Configuration');
  console.log('-'.repeat(50));
  
  const envPath = path.join(__dirname, '../../frontend/.env.local');
  
  try {
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      console.log('✅ .env.local file exists');
      
      // Check for required variables
      const requiredVars = [
        'REACT_APP_API_ENDPOINT',
        'REACT_APP_USER_POOL_ID',
        'REACT_APP_USER_POOL_CLIENT_ID'
      ];
      
      let allPresent = true;
      requiredVars.forEach(varName => {
        if (envContent.includes(varName)) {
          const match = envContent.match(new RegExp(`${varName}=(.+)`));
          if (match) {
            console.log(`✅ ${varName}: ${match[1]}`);
          }
        } else {
          console.log(`❌ Missing: ${varName}`);
          allPresent = false;
        }
      });
      
      return allPresent;
    } else {
      console.log('❌ .env.local file not found');
      return false;
    }
  } catch (error) {
    console.log(`❌ Error reading .env.local: ${error.message}`);
    return false;
  }
}

/**
 * Test API connectivity
 */
function testAPIConnectivity() {
  return new Promise((resolve) => {
    console.log('\n🌐 Testing API Connectivity');
    console.log('-'.repeat(50));
    
    const apiUrl = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/device-readings/ESP32-001/latest';
    
    const req = https.get(apiUrl, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          
          if (res.statusCode === 200 && jsonData.success) {
            console.log('✅ API is responding correctly');
            console.log(`📊 Device: ${jsonData.deviceId}`);
            console.log(`📊 pH: ${jsonData.reading.pH}`);
            console.log(`📊 Temperature: ${jsonData.reading.temperature}°C`);
            console.log(`📊 WQI: ${jsonData.reading.qualityScore || 'N/A'}`);
            resolve(true);
          } else {
            console.log(`❌ API error: ${res.statusCode}`);
            console.log(`📋 Response: ${data}`);
            resolve(false);
          }
        } catch (error) {
          console.log(`❌ JSON parse error: ${error.message}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (error) => {
      console.log(`❌ Network error: ${error.message}`);
      resolve(false);
    });
    
    req.setTimeout(10000, () => {
      console.log('❌ Request timeout');
      req.destroy();
      resolve(false);
    });
  });
}

/**
 * Generate dashboard instructions
 */
function generateDashboardInstructions() {
  console.log('\n📝 Dashboard Setup Instructions');
  console.log('-'.repeat(50));
  
  console.log('To get your dashboard working:');
  console.log('');
  console.log('1. 🔄 Restart the frontend development server:');
  console.log('   cd frontend');
  console.log('   npm start');
  console.log('');
  console.log('2. 🌐 Open your browser to:');
  console.log('   http://localhost:3000');
  console.log('');
  console.log('3. 📊 You should now see:');
  console.log('   - Device ESP32-001 showing as "Online"');
  console.log('   - Water Quality Index: 50');
  console.log('   - pH: 7.05');
  console.log('   - Temperature: 30.2°C');
  console.log('   - Real-time sensor data');
  console.log('');
  console.log('4. 🔧 If you still see "No Data":');
  console.log('   - Check browser console for errors');
  console.log('   - Verify the API endpoint in Network tab');
  console.log('   - Make sure .env.local is loaded (restart server)');
}

/**
 * Create a simple test HTML file
 */
function createTestHTML() {
  console.log('\n🧪 Creating Test HTML File');
  console.log('-'.repeat(50));
  
  const testHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaChain API Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .data { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 AquaChain API Test</h1>
        <p>This page tests the API connection that your dashboard will use.</p>
        
        <button onclick="testAPI()">🔄 Test API Connection</button>
        <button onclick="testContinuous()">📊 Start Continuous Updates</button>
        <button onclick="stopContinuous()">⏹️ Stop Updates</button>
        
        <div id="status"></div>
        <div id="data"></div>
    </div>

    <script>
        const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
        const DEVICE_ID = 'ESP32-001';
        let updateInterval = null;

        function showStatus(message, isError = false) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = \`<div class="status \${isError ? 'error' : 'success'}">\${message}</div>\`;
        }

        function showData(data) {
            const dataDiv = document.getElementById('data');
            if (data && data.reading) {
                const reading = data.reading;
                dataDiv.innerHTML = \`
                    <div class="data">
                        <h3>📊 Device: \${data.deviceId}</h3>
                        <p><strong>Timestamp:</strong> \${reading.timestamp}</p>
                        <p><strong>pH:</strong> \${reading.pH}</p>
                        <p><strong>Temperature:</strong> \${reading.temperature}°C</p>
                        <p><strong>TDS:</strong> \${reading.tds} ppm</p>
                        <p><strong>Turbidity:</strong> \${reading.turbidity} NTU</p>
                        <p><strong>Water Quality Index:</strong> \${reading.qualityScore || reading.wqi || 'N/A'}</p>
                        <p><strong>Status:</strong> \${reading.qualityStatus || 'Unknown'}</p>
                    </div>
                \`;
            }
        }

        async function testAPI() {
            showStatus('🔄 Testing API connection...', false);
            
            try {
                const response = await fetch(\`\${API_BASE_URL}/api/device-readings/\${DEVICE_ID}/latest\`);
                const data = await response.json();
                
                if (response.ok && data.success) {
                    showStatus('✅ API connection successful!', false);
                    showData(data);
                } else {
                    showStatus(\`❌ API error: \${data.error || 'Unknown error'}\`, true);
                }
            } catch (error) {
                showStatus(\`❌ Network error: \${error.message}\`, true);
            }
        }

        function testContinuous() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            
            showStatus('📊 Starting continuous updates (every 30 seconds)...', false);
            testAPI(); // Initial test
            
            updateInterval = setInterval(() => {
                testAPI();
            }, 30000);
        }

        function stopContinuous() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
                showStatus('⏹️ Continuous updates stopped', false);
            }
        }

        // Test on page load
        window.onload = () => {
            testAPI();
        };
    </script>
</body>
</html>`;

  const testPath = path.join(__dirname, '../../api-test.html');
  
  try {
    fs.writeFileSync(testPath, testHTML);
    console.log(`✅ Test HTML created: ${testPath}`);
    console.log('🌐 Open this file in your browser to test the API');
    return true;
  } catch (error) {
    console.log(`❌ Error creating test HTML: ${error.message}`);
    return false;
  }
}

/**
 * Main function
 */
async function main() {
  const configOK = checkEnvironmentConfig();
  const apiOK = await testAPIConnectivity();
  const testFileOK = createTestHTML();
  
  generateDashboardInstructions();
  
  console.log('\n📋 SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Environment Config: ${configOK ? 'OK' : 'NEEDS FIX'}`);
  console.log(`✅ API Connectivity: ${apiOK ? 'OK' : 'NEEDS FIX'}`);
  console.log(`✅ Test File Created: ${testFileOK ? 'OK' : 'FAILED'}`);
  
  if (configOK && apiOK) {
    console.log('\n🎉 Everything is ready!');
    console.log('💡 Your dashboard should now display device data.');
    console.log('🔄 Restart the frontend server and check http://localhost:3000');
  } else {
    console.log('\n🔧 Issues need to be resolved before dashboard will work');
  }
}

main().catch(console.error);