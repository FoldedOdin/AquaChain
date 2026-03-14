// Frontend Authentication Test Script
// Run this in the browser console on the technician dashboard

console.log('Testing Frontend Authentication');

// 1. Check if auth token exists
const authToken = localStorage.getItem('authToken');
console.log('Auth token exists:', !!authToken);
if (authToken) {
    console.log('Token preview:', authToken.substring(0, 50) + '...');
}

// 2. Check if user is logged in
const isLoggedIn = !!authToken;
console.log('User logged in:', isLoggedIn);

// 3. Test API call manually
if (authToken) {
    console.log('Testing API call...');
    
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
        if (data.tasks) {
            console.log('Tasks found:', data.tasks.length);
            data.tasks.forEach((task, index) => {
                console.log(`Task ${index + 1}:`, task.description);
            });
        } else {
            console.log('No tasks in response');
        }
    })
    .catch(error => {
        console.error('API Error:', error);
    });
} else {
    console.log('Cannot test API - no auth token');
    console.log('User needs to log in first');
}

// 4. Check network requests
console.log('Check Network tab for API requests');
console.log('Look for 401 Unauthorized responses');

// 5. Instructions
console.log('TROUBLESHOOTING STEPS:');
console.log('1. If no auth token: User needs to log in');
console.log('2. If token exists but API fails: Token might be expired');
console.log('3. If 401 error: Authentication issue');
console.log('4. If 200 but no tasks: Check Lambda function');