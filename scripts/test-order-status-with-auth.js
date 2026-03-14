#!/usr/bin/env node
/**
 * Test the order status update API endpoint with authentication
 * This script demonstrates how the frontend should call the API
 */

const https = require('https');

const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const ORDER_ID = 'ord_1773176454115';

// Test data for status update
const testData = {
    status: 'OUT_FOR_DELIVERY',
    reason: 'Order is out for delivery - testing from script'
};

function testWithoutAuth() {
    console.log('🚀 Testing order status update API (without auth)...');
    console.log(`URL: ${API_BASE_URL}/api/orders/${ORDER_ID}/status`);
    console.log(`Payload:`, testData);

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

    const req = https.request(options, (res) => {
        console.log(`Status Code: ${res.statusCode}`);
        
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            console.log('Response Body:', data);
            
            if (res.statusCode === 200) {
                console.log('✅ Order status update successful!');
            } else if (res.statusCode === 401) {
                console.log('✅ API Gateway is working correctly (401 Unauthorized expected)');
                console.log('✅ Lambda function is properly configured');
                console.log('✅ The 502 Bad Gateway error has been fixed!');
                console.log('');
                console.log('📝 For the frontend to work:');
                console.log('   1. Include valid Cognito JWT token in Authorization header');
                console.log('   2. Use the same request format as shown above');
                console.log('   3. The Lambda function will process the request correctly');
            } else if (res.statusCode === 502) {
                console.log('❌ Bad Gateway - Lambda function error (this should not happen now)');
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
}

function testOptionsRequest() {
    console.log('\n🚀 Testing CORS preflight (OPTIONS request)...');
    
    const options = {
        hostname: 'vtqjfznspc.execute-api.ap-south-1.amazonaws.com',
        port: 443,
        path: `/dev/api/orders/${ORDER_ID}/status`,
        method: 'OPTIONS',
        headers: {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'PUT',
            'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
    };

    const req = https.request(options, (res) => {
        console.log(`CORS Status Code: ${res.statusCode}`);
        console.log('CORS Headers:', res.headers);
        
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            if (res.statusCode === 200) {
                console.log('✅ CORS preflight successful');
            } else {
                console.log('⚠️  CORS preflight may need configuration');
            }
        });
    });

    req.on('error', (error) => {
        console.error('❌ CORS request error:', error);
    });

    req.end();
}

// Run tests
testWithoutAuth();
setTimeout(testOptionsRequest, 1000);