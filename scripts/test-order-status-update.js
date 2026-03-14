#!/usr/bin/env node
/**
 * Test the order status update API endpoint
 */

const https = require('https');

const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const ORDER_ID = 'ord_1773176454115';

// You'll need to get a valid Cognito token for this test
// For now, let's test without authentication to see if the endpoint is reachable
const testData = {
    status: 'OUT_FOR_DELIVERY',
    reason: 'Order is out for delivery'
};

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

console.log('🚀 Testing order status update API...');
console.log(`URL: ${API_BASE_URL}/api/orders/${ORDER_ID}/status`);
console.log(`Payload:`, testData);

const req = https.request(options, (res) => {
    console.log(`Status Code: ${res.statusCode}`);
    console.log(`Headers:`, res.headers);
    
    let data = '';
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        console.log('Response Body:', data);
        
        if (res.statusCode === 200) {
            console.log('✅ Order status update successful!');
        } else if (res.statusCode === 401) {
            console.log('⚠️  Authentication required (expected for production)');
        } else if (res.statusCode === 502) {
            console.log('❌ Bad Gateway - Lambda function error');
        } else {
            console.log(`❌ Request failed with status ${res.statusCode}`);
        }
    });
});

req.on('error', (error) => {
    console.error('❌ Request error:', error);
});

req.write(JSON.stringify(testData));
req.end();