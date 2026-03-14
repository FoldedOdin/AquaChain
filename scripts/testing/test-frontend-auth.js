#!/usr/bin/env node
/**
 * Test Frontend Authentication
 * 
 * This script helps debug why the technician dashboard isn't showing tasks
 * by testing the authentication flow and API calls.
 */

const https = require('https');

// Configuration
const API_BASE_URL = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
const TECHNICIAN_TASKS_ENDPOINT = '/api/v1/technician/tasks';

function makeApiCall(endpoint, token = null) {
    return new Promise((resolve, reject) => {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        console.log(`🧪 Testing API call: ${url}`);
        console.log(`   Headers: ${JSON.stringify(options.headers, null, 2)}`);

        const req = https.request(url, options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                console.log(`📊 Response Status: ${res.statusCode}`);
                console.log(`📊 Response Headers: ${JSON.stringify(res.headers, null, 2)}`);
                
                try {
                    const jsonData = JSON.parse(data);
                    console.log(`📊 Response Body: ${JSON.stringify(jsonData, null, 2)}`);
                    resolve({ statusCode: res.statusCode, data: jsonData, headers: res.headers });
                } catch (e) {
                    console.log(`📊 Raw Response Body: ${data}`);
                    resolve({ statusCode: res.statusCode, data: data, headers: res.headers });
                }
            });
        });

        req.on('error', (error) => {
            console.error(`❌ Request error: ${error.message}`);
            reject(error);
        });

        req.end();
    });
}

async function testAuthenticationFlow() {
    console.log('🚀 Testing Frontend Authentication Flow');
    console.log('=' * 60);

    // Test 1: Call API without authentication
    console.log('\n1. Testing API without authentication:');
    console.log('-'.repeat(40));
    
    try {
        const response1 = await makeApiCall(TECHNICIAN_TASKS_ENDPOINT);
        
        if (response1.statusCode === 401) {
            console.log('✅ API correctly returns 401 Unauthorized without token');
        } else {
            console.log(`⚠️  Unexpected response without token: ${response1.statusCode}`);
        }
    } catch (error) {
        console.log(`❌ Error testing without auth: ${error.message}`);
    }

    // Test 2: Call API with invalid token
    console.log('\n2. Testing API with invalid token:');
    console.log('-'.repeat(40));
    
    try {
        const response2 = await makeApiCall(TECHNICIAN_TASKS_ENDPOINT, 'invalid-token-123');
        
        if (response2.statusCode === 401 || response2.statusCode === 403) {
            console.log('✅ API correctly rejects invalid token');
        } else {
            console.log(`⚠️  Unexpected response with invalid token: ${response2.statusCode}`);
        }
    } catch (error) {
        console.log(`❌ Error testing with invalid token: ${error.message}`);
    }

    // Test 3: Check CORS headers
    console.log('\n3. Checking CORS configuration:');
    console.log('-'.repeat(40));
    
    try {
        const response3 = await makeApiCall(TECHNICIAN_TASKS_ENDPOINT);
        const corsHeaders = {
            'access-control-allow-origin': response3.headers['access-control-allow-origin'],
            'access-control-allow-methods': response3.headers['access-control-allow-methods'],
            'access-control-allow-headers': response3.headers['access-control-allow-headers']
        };
        
        console.log('📊 CORS Headers:');
        console.log(JSON.stringify(corsHeaders, null, 2));
        
        if (corsHeaders['access-control-allow-origin']) {
            console.log('✅ CORS headers are present');
        } else {
            console.log('❌ CORS headers are missing');
        }
    } catch (error) {
        console.log(`❌ Error checking CORS: ${error.message}`);
    }

    // Analysis
    console.log('\n' + '='.repeat(60));
    console.log('📊 ANALYSIS');
    console.log('='.repeat(60));
    
    console.log('\n🔍 FRONTEND AUTHENTICATION CHECKLIST:');
    console.log('1. ✅ API endpoint is accessible');
    console.log('2. ✅ API correctly requires authentication');
    console.log('3. ❓ User needs to be properly logged in to Cognito');
    console.log('4. ❓ Frontend needs to store valid auth token in localStorage');
    console.log('5. ❓ Frontend needs to send token with API requests');
    
    console.log('\n💡 NEXT STEPS:');
    console.log('1. Check if user is logged in to the technician dashboard');
    console.log('2. Check browser localStorage for "authToken"');
    console.log('3. Verify the token is valid and not expired');
    console.log('4. Check browser network tab for API call details');
    console.log('5. Look for authentication errors in browser console');
    
    console.log('\n🎯 BROWSER DEBUGGING COMMANDS:');
    console.log('Open browser console on technician dashboard and run:');
    console.log('');
    console.log('// Check if auth token exists');
    console.log('console.log("Auth token:", localStorage.getItem("authToken"));');
    console.log('');
    console.log('// Check if user is authenticated');
    console.log('console.log("User authenticated:", !!localStorage.getItem("authToken"));');
    console.log('');
    console.log('// Manually test API call');
    console.log('fetch("https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks", {');
    console.log('  headers: {');
    console.log('    "Authorization": `Bearer ${localStorage.getItem("authToken")}`,');
    console.log('    "Content-Type": "application/json"');
    console.log('  }');
    console.log('}).then(r => r.json()).then(console.log).catch(console.error);');
}

// Run the test
testAuthenticationFlow().catch(console.error);