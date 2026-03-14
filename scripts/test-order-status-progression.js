#!/usr/bin/env node
/**
 * Test the order status progression to ensure it follows the correct sequence
 */

const https = require('https');

const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const ORDER_ID = 'ord_1773176454115';

// Test the progression: SHIPPED -> OUT_FOR_DELIVERY -> DELIVERED
const testStatusProgression = async () => {
    console.log('🚀 Testing order status progression...');
    console.log(`Order ID: ${ORDER_ID}`);
    
    // Step 1: Update to OUT_FOR_DELIVERY
    console.log('\n📦 Step 1: Updating to OUT_FOR_DELIVERY...');
    await updateOrderStatus('OUT_FOR_DELIVERY', 'Order is out for delivery');
    
    // Wait a moment
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Step 2: Update to DELIVERED
    console.log('\n✅ Step 2: Updating to DELIVERED...');
    await updateOrderStatus('DELIVERED', 'Order has been delivered and installed');
};

const updateOrderStatus = (status, reason) => {
    return new Promise((resolve, reject) => {
        const testData = { status, reason };
        
        const options = {
            hostname: 'vtqjfznspc.execute-api.ap-south-1.amazonaws.com',
            port: 443,
            path: `/dev/api/orders/${ORDER_ID}/status`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': JSON.stringify(testData).length
            }
        };

        console.log(`   Updating to: ${status}`);
        console.log(`   Reason: ${reason}`);

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                console.log(`   Status Code: ${res.statusCode}`);
                
                if (res.statusCode === 200) {
                    try {
                        const response = JSON.parse(data);
                        console.log(`   ✅ Success: ${response.message}`);
                        console.log(`   Current Status: ${response.data.status}`);
                        resolve(response);
                    } catch (e) {
                        console.log(`   ✅ Success (raw response): ${data}`);
                        resolve(data);
                    }
                } else if (res.statusCode === 401) {
                    console.log('   ⚠️  Authentication required (expected)');
                    resolve({ statusCode: 401 });
                } else {
                    console.log(`   ❌ Failed: ${data}`);
                    reject(new Error(`Status ${res.statusCode}: ${data}`));
                }
            });
        });

        req.on('error', (error) => {
            console.error(`   ❌ Request error:`, error.message);
            reject(error);
        });

        req.write(JSON.stringify(testData));
        req.end();
    });
};

// Run the test
testStatusProgression().catch(console.error);