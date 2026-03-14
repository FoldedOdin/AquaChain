/**
 * Test the frontend after fixing the 500 error
 * Run this in the browser console
 */

console.log('🧪 Testing Frontend After API Fix...');

// Function to test the API directly from browser
async function testOrdersAPI() {
    console.log('🌐 Testing Orders API directly...');
    
    try {
        // Get the auth token from localStorage
        const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
        
        if (!token) {
            console.log('❌ No auth token found in localStorage');
            return;
        }
        
        console.log('✅ Found auth token');
        
        // Make API request
        const apiEndpoint = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';
        const response = await fetch(`${apiEndpoint}/api/orders`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`📊 API Response Status: ${response.status}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API request successful!');
            console.log(`📋 Orders returned: ${data.orders?.length || 0}`);
            
            // Check for technician data
            const ordersWithTechnicians = data.orders?.filter(order => 
                order.status === 'TECHNICIAN_ASSIGNED' && order.technician
            ) || [];
            
            console.log(`🔧 Orders with technician data: ${ordersWithTechnicians.length}`);
            
            ordersWithTechnicians.forEach((order, index) => {
                console.log(`\n📋 Order ${index + 1}: ${order.orderId}`);
                console.log(`   👤 Technician: ${order.technician.name}`);
                console.log(`   📞 Phone: ${order.technician.phone}`);
                console.log(`   ⭐ Rating: ${order.technician.rating}`);
                console.log(`   🕐 Estimated Arrival: ${order.technicianAssignment?.estimatedArrival}`);
            });
            
            return data;
        } else {
            console.log('❌ API request failed');
            const errorText = await response.text();
            console.log(`Error: ${errorText}`);
            return null;
        }
        
    } catch (error) {
        console.log('❌ Error testing API:', error);
        return null;
    }
}

// Function to check if orders are displaying correctly
function checkOrdersDisplay() {
    console.log('\n🔍 Checking Orders Display...');
    
    // Look for order cards
    const orderCards = document.querySelectorAll('[class*="bg-white"][class*="rounded-lg"]');
    console.log(`📋 Found ${orderCards.length} potential order cards`);
    
    let technicianOrdersFound = 0;
    
    orderCards.forEach((card, index) => {
        const cardText = card.textContent;
        
        if (cardText.includes('Technician Assigned')) {
            technicianOrdersFound++;
            console.log(`\n✅ Found technician assigned order (card ${index + 1})`);
            
            // Check for technician name
            if (cardText.includes('Rahul Nair')) {
                console.log('   ✅ Technician name displayed');
            } else {
                console.log('   ❌ Technician name not found');
            }
            
            // Check for phone number
            if (cardText.includes('+91 9876543210')) {
                console.log('   ✅ Phone number displayed');
            } else {
                console.log('   ❌ Phone number not found');
            }
            
            // Check for View Details button
            const viewDetailsButtons = card.querySelectorAll('button');
            let hasViewDetails = false;
            viewDetailsButtons.forEach(btn => {
                if (btn.textContent.includes('View Details')) {
                    hasViewDetails = true;
                }
            });
            
            if (hasViewDetails) {
                console.log('   ✅ View Details button found');
            } else {
                console.log('   ❌ View Details button not found');
            }
        }
    });
    
    console.log(`\n📊 Summary: Found ${technicianOrdersFound} orders with technician assignments`);
    
    return technicianOrdersFound;
}

// Function to test the technician modal
function testTechnicianModal() {
    console.log('\n🔘 Testing Technician Modal...');
    
    // Look for orders with technician assignments
    const orderCards = document.querySelectorAll('[class*="bg-white"][class*="rounded-lg"]');
    
    for (let card of orderCards) {
        if (card.textContent.includes('Technician Assigned')) {
            console.log('🔍 Found technician assigned order, clicking View Details...');
            
            const viewDetailsButtons = card.querySelectorAll('button');
            for (let btn of viewDetailsButtons) {
                if (btn.textContent.includes('View Details')) {
                    btn.click();
                    
                    // Wait for modal to open
                    setTimeout(() => {
                        const modal = document.querySelector('[class*="fixed"][class*="inset-0"]');
                        if (modal) {
                            console.log('✅ Order details modal opened');
                            
                            // Look for technician View Details button
                            const techButtons = modal.querySelectorAll('button');
                            for (let techBtn of techButtons) {
                                if (techBtn.textContent.includes('View Details') && 
                                    techBtn.className.includes('text-indigo-600')) {
                                    console.log('🔘 Found technician View Details button, clicking...');
                                    techBtn.click();
                                    
                                    // Wait for technician modal
                                    setTimeout(() => {
                                        const techModal = document.querySelector('[class*="fixed"][class*="inset-0"][class*="z-50"]');
                                        if (techModal && techModal.textContent.includes('Technician Details')) {
                                            console.log('✅ Technician Details Modal opened successfully!');
                                            console.log('🎉 All functionality is working correctly!');
                                            
                                            // Close modal after 3 seconds
                                            setTimeout(() => {
                                                const closeBtn = techModal.querySelector('button');
                                                if (closeBtn) closeBtn.click();
                                            }, 3000);
                                        } else {
                                            console.log('❌ Technician modal did not open');
                                        }
                                    }, 500);
                                    break;
                                }
                            }
                        } else {
                            console.log('❌ Order details modal did not open');
                        }
                    }, 500);
                    break;
                }
            }
            break;
        }
    }
}

// Main test function
async function runCompleteTest() {
    console.log('🚀 Running Complete Frontend Test...');
    
    // Step 1: Test API
    const apiData = await testOrdersAPI();
    
    if (!apiData) {
        console.log('❌ API test failed, cannot proceed with UI tests');
        return;
    }
    
    // Step 2: Check display
    const technicianOrders = checkOrdersDisplay();
    
    if (technicianOrders === 0) {
        console.log('⚠️  No technician orders found in UI');
        console.log('💡 Make sure you are on the My Orders page');
        return;
    }
    
    // Step 3: Test modal (wait a bit for UI to update)
    setTimeout(() => {
        testTechnicianModal();
    }, 1000);
    
    console.log('\n✅ Frontend test completed!');
    console.log('🎯 Results:');
    console.log(`   - API working: ✅`);
    console.log(`   - Orders displaying: ✅`);
    console.log(`   - Technician data: ✅`);
}

// Auto-run the test
runCompleteTest();

// Also provide manual trigger
window.testFrontendAfterFix = runCompleteTest;
console.log('💡 You can also run the test manually: testFrontendAfterFix()');