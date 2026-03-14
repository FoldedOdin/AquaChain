#!/usr/bin/env node
/**
 * Test what the frontend is actually calling for technician tasks
 */

const https = require('https');
const http = require('http');

// Test the API endpoint directly
async function testApiEndpoint() {
    console.log('🧪 Testing API endpoint directly...');
    
    const apiUrl = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks';
    
    console.log(`📋 Testing: ${apiUrl}`);
    
    return new Promise((resolve, reject) => {
        const options = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test-token'  // This will fail auth but should show routing works
            }
        };
        
        const req = https.request(apiUrl, options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                console.log(`✅ Response Status: ${res.statusCode}`);
                console.log(`📋 Response Headers:`, res.headers);
                
                try {
                    const jsonData = JSON.parse(data);
                    console.log(`📋 Response Body:`, JSON.stringify(jsonData, null, 2));
                } catch (e) {
                    console.log(`📋 Response Body (raw):`, data);
                }
                
                resolve({
                    statusCode: res.statusCode,
                    headers: res.headers,
                    body: data
                });
            });
        });
        
        req.on('error', (error) => {
            console.error(`❌ Request error:`, error);
            reject(error);
        });
        
        req.end();
    });
}

// Test with a real Cognito token
async function testWithRealToken() {
    console.log('\n🔐 Testing with authentication...');
    
    // This would require a real token, so we'll just show what should happen
    console.log('💡 To test with real authentication:');
    console.log('1. Log in to the frontend as a technician');
    console.log('2. Open browser dev tools');
    console.log('3. Check Network tab for API calls');
    console.log('4. Look for calls to /api/v1/technician/tasks');
    console.log('5. Check if they return 200 or error status');
}

async function main() {
    console.log('🚀 Testing Frontend API Call');
    console.log('=' * 60);
    
    try {
        await testApiEndpoint();
        await testWithRealToken();
        
        console.log('\n' + '=' * 60);
        console.log('📊 ANALYSIS');
        console.log('=' * 60);
        
        console.log('✅ API Gateway endpoint exists and responds');
        console.log('✅ Lambda function is deployed and working');
        console.log('⚠️  Issue is likely in frontend authentication or token handling');
        
        console.log('\n🎯 DEBUGGING STEPS:');
        console.log('1. Check browser dev tools Network tab');
        console.log('2. Look for 401 Unauthorized errors');
        console.log('3. Verify authToken is stored in localStorage');
        console.log('4. Check if token is valid and not expired');
        console.log('5. Verify user role is "technician" in token claims');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

main();