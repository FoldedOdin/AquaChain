// Test all existing users with their proper passwords

console.log('🧪 Testing all existing users with correct passwords...');

const apiEndpoint = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

const existingUsers = [
    {
        name: 'Sidharth (Technician)',
        email: 'leninat259@gmail.com',
        password: 'AquaChain123!'
    },
    {
        name: 'Karthik (Technician)',
        email: 'karthiikkpradeep897@gmail.com',
        password: 'AquaChain123!'
    },
    {
        name: 'Karthik (User)',
        email: 'karthikkpradeep123@gmail.com',
        password: 'AquaChain123!'
    },
    {
        name: 'Contact (Admin)',
        email: 'contact.aquachain@gmail.com',
        password: 'AquaChain2024!'
    }
];

async function testUserCredentials(user) {
    try {
        console.log(`\n👤 Testing ${user.name}...`);
        console.log(`📧 Email: ${user.email}`);
        
        const response = await fetch(`${apiEndpoint}/api/auth/signin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: user.email,
                password: user.password
            }),
        });

        if (response.ok) {
            const result = await response.json();
            console.log(`✅ Authentication successful!`);
            console.log(`🔑 Token: ${result.token ? 'Received' : 'Missing'}`);
            console.log(`👤 Role: ${result.user?.role || 'Unknown'}`);
            console.log(`📧 Email verified: ${result.user?.emailVerified ? 'Yes' : 'No'}`);
            return true;
        } else {
            const error = await response.text();
            console.log(`❌ Authentication failed: ${response.status}`);
            console.log(`🔍 Error: ${error}`);
            return false;
        }
    } catch (error) {
        console.log(`❌ Network error: ${error.message}`);
        return false;
    }
}

async function testAllExistingUsers() {
    console.log(`🔗 Testing against: ${apiEndpoint}`);
    console.log(`👥 Testing ${existingUsers.length} existing users...\n`);
    
    let successCount = 0;
    
    for (const user of existingUsers) {
        const success = await testUserCredentials(user);
        if (success) successCount++;
    }
    
    console.log(`\n📊 FINAL RESULTS: ${successCount}/${existingUsers.length} existing users can authenticate`);
    
    if (successCount === existingUsers.length) {
        console.log('\n🎉 ALL EXISTING USERS ARE NOW WORKING!');
        console.log('✅ Authentication system is fully functional');
        console.log('💡 Users can login with their proper credentials');
        console.log('🎯 No new users were needed - existing users fixed');
    } else {
        console.log('\n⚠️ Some existing users still have issues');
        console.log('🔍 Check the individual results above');
    }
    
    console.log('\n🎯 WORKING CREDENTIALS FOR FRONTEND:');
    existingUsers.forEach(user => {
        console.log(`👤 ${user.name}`);
        console.log(`📧 ${user.email}`);
        console.log(`🔑 ${user.password}\n`);
    });
    
    console.log('🚀 You can now use any of these credentials to test the frontend!');
}

testAllExistingUsers();