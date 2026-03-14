// Fix Token Key Mismatch
// Run this in the browser console to fix the authentication issue

console.log('🔧 Fixing token key mismatch...');

// 1. Check current token storage
const aquachainToken = localStorage.getItem('aquachain_token');
const authToken = localStorage.getItem('authToken');

console.log('Current tokens:');
console.log('  aquachain_token:', !!aquachainToken);
console.log('  authToken:', !!authToken);

if (aquachainToken && !authToken) {
    console.log('✅ Found token in aquachain_token, copying to authToken...');
    
    // Copy the token to the expected key
    localStorage.setItem('authToken', aquachainToken);
    
    console.log('✅ Token copied successfully!');
    
    // Verify the fix
    const newAuthToken = localStorage.getItem('authToken');
    console.log('Verification - authToken now exists:', !!newAuthToken);
    
    // Test the API call
    console.log('🧪 Testing API call with fixed token...');
    
    fetch('https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${newAuthToken}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('API Response Status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('API Response Data:', data);
        if (data.tasks && data.tasks.length > 0) {
            console.log('🎉 SUCCESS! Tasks found:', data.tasks.length);
            console.log('Tasks:');
            data.tasks.forEach((task, index) => {
                console.log(`  ${index + 1}. ${task.description}`);
            });
            console.log('💡 Refresh the page to see tasks in dashboard!');
        } else {
            console.log('❌ No tasks in response');
        }
    })
    .catch(error => {
        console.error('API Error:', error);
    });
    
} else if (authToken) {
    console.log('✅ authToken already exists, testing API...');
    
    fetch('https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/technician/tasks', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('API Response Status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('API Response Data:', data);
        if (data.tasks && data.tasks.length > 0) {
            console.log('🎉 Tasks found:', data.tasks.length);
            console.log('💡 Refresh the page to see tasks in dashboard!');
        }
    })
    .catch(error => {
        console.error('API Error:', error);
    });
    
} else {
    console.log('❌ No tokens found. User needs to log in.');
}