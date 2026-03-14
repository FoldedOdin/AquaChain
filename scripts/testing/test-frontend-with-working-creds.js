// Test the frontend authentication with working credentials

console.log('🧪 Testing frontend authentication with working credentials...');

// Test credentials that work
const testCredentials = {
    email: 'test@aquachain.com',
    password: 'TestPassword123!'
};

// Get the API endpoint from environment
const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

console.log(`🔗 API Endpoint: ${apiEndpoint}`);

// Test the signin endpoint directly
async function testSignin() {
    try {
        console.log('📡 Making signin request...');
        
        const response = await fetch(`${apiEndpoint}/api/auth/signin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testCredentials),
        });

        console.log(`📊 Response Status: ${response.status}`);
        console.log(`📊 Response Headers:`, Object.fromEntries(response.headers.entries()));

        const result = await response.text();
        console.log(`📄 Raw Response: ${result}`);

        if (response.ok) {
            const jsonResult = JSON.parse(result);
            console.log('✅ Authentication successful!');
            console.log('🔑 Token received:', jsonResult.token ? 'Yes' : 'No');
            console.log('👤 User info:', jsonResult.user);
            return jsonResult;
        } else {
            console.log('❌ Authentication failed');
            try {
                const errorResult = JSON.parse(result);
                console.log('🔍 Error details:', errorResult);
            } catch (e) {
                console.log('🔍 Raw error:', result);
            }
            return null;
        }
    } catch (error) {
        console.log('❌ Network error:', error.message);
        return null;
    }
}

// Run the test
testSignin().then(result => {
    if (result) {
        console.log('\n✅ Frontend authentication test PASSED');
        console.log('🎯 The issue was incorrect user credentials');
        console.log('💡 Solution: Use the test user credentials or fix the original user password');
    } else {
        console.log('\n❌ Frontend authentication test FAILED');
        console.log('🔍 There may be additional issues beyond credentials');
    }
});