#!/usr/bin/env node
/**
 * Test CORS and response parsing to identify the exact issue
 */

const https = require('https');

function testCorsAndResponse() {
    console.log('🧪 Testing CORS and Response Parsing');
    console.log('=' * 50);
    
    const postData = JSON.stringify({
        email: 'leninat259@gmail.com',
        password: 'AquaChain123!'
    });
    
    const options = {
        hostname: 'vtqjfznspc.execute-api.ap-south-1.amazonaws.com',
        port: 443,
        path: '/dev/api/auth/signin',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData),
            'Origin': 'http://localhost:3000',  // Simulate frontend origin
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
    };
    
    console.log('📋 Request Details:');
    console.log('  URL:', `https://${options.hostname}${options.path}`);
    console.log('  Method:', options.method);
    console.log('  Headers:', options.headers);
    console.log('  Body:', postData);
    
    const req = https.request(options, (res) => {
        console.log('\n✅ Response Details:');
        console.log('  Status:', res.statusCode);
        console.log('  Headers:', res.headers);
        
        // Check CORS headers
        const corsHeaders = {
            'access-control-allow-origin': res.headers['access-control-allow-origin'],
            'access-control-allow-methods': res.headers['access-control-allow-methods'],
            'access-control-allow-headers': res.headers['access-control-allow-headers']
        };
        
        console.log('\n🔍 CORS Headers:');
        Object.entries(corsHeaders).forEach(([key, value]) => {
            console.log(`  ${key}: ${value || 'NOT SET'}`);
        });
        
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            console.log('\n📋 Response Body:');
            console.log(data);
            
            try {
                const parsed = JSON.parse(data);
                console.log('\n✅ JSON Parsing: SUCCESS');
                console.log('  Success field:', parsed.success);
                console.log('  Has token:', !!parsed.token);
                console.log('  Has user:', !!parsed.user);
                
                if (parsed.user) {
                    console.log('  User ID:', parsed.user.id);
                    console.log('  User Role:', parsed.user.role);
                }
            } catch (parseError) {
                console.log('\n❌ JSON Parsing: FAILED');
                console.log('  Error:', parseError.message);
            }
            
            console.log('\n🎯 DIAGNOSIS:');
            if (res.statusCode === 200) {
                console.log('✅ API returns 200 OK');
            } else {
                console.log('❌ API returns error status:', res.statusCode);
            }
            
            if (corsHeaders['access-control-allow-origin']) {
                console.log('✅ CORS headers are present');
            } else {
                console.log('❌ CORS headers missing - this could cause frontend issues');
            }
        });
    });
    
    req.on('error', (error) => {
        console.error('❌ Request Error:', error);
    });
    
    req.write(postData);
    req.end();
}

testCorsAndResponse();