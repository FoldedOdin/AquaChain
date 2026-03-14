/**
 * Test script to verify technician modal functionality in the frontend
 * Run this in the browser console on the My Orders page
 */

console.log('🧪 Testing Technician Modal Functionality...');

// Function to simulate clicking on technician details
function testTechnicianModal() {
    console.log('🔍 Looking for orders with technician assignments...');
    
    // Look for orders with TECHNICIAN_ASSIGNED status
    const orderCards = document.querySelectorAll('[class*="bg-white"][class*="rounded-lg"][class*="shadow"]');
    console.log(`Found ${orderCards.length} order cards`);
    
    let technicianFound = false;
    
    orderCards.forEach((card, index) => {
        const statusText = card.textContent;
        
        if (statusText.includes('Technician Assigned')) {
            console.log(`✅ Found order with technician assignment (card ${index + 1})`);
            technicianFound = true;
            
            // Look for View Details button
            const viewDetailsButtons = card.querySelectorAll('button');
            viewDetailsButtons.forEach(button => {
                if (button.textContent.includes('View Details')) {
                    console.log('🔘 Found "View Details" button, clicking...');
                    button.click();
                    
                    // Wait a bit for modal to open
                    setTimeout(() => {
                        // Look for technician details in the modal
                        const modal = document.querySelector('[class*="fixed"][class*="inset-0"]');
                        if (modal) {
                            console.log('✅ Modal opened successfully');
                            
                            // Look for technician information
                            const technicianInfo = modal.textContent;
                            
                            if (technicianInfo.includes('Rahul Nair')) {
                                console.log('✅ Technician name found in modal');
                            }
                            
                            if (technicianInfo.includes('+91 9876543210')) {
                                console.log('✅ Technician phone found in modal');
                            }
                            
                            if (technicianInfo.includes('View Details')) {
                                console.log('🔍 Looking for technician "View Details" button...');
                                
                                // Look for technician View Details button
                                const techViewDetailsButtons = modal.querySelectorAll('button');
                                techViewDetailsButtons.forEach(btn => {
                                    if (btn.textContent.includes('View Details') && 
                                        btn.className.includes('text-indigo-600')) {
                                        console.log('🔘 Found technician "View Details" button, clicking...');
                                        btn.click();
                                        
                                        // Wait for technician modal
                                        setTimeout(() => {
                                            const techModal = document.querySelector('[class*="fixed"][class*="inset-0"][class*="z-50"]');
                                            if (techModal && techModal.textContent.includes('Technician Details')) {
                                                console.log('✅ Technician Details Modal opened successfully!');
                                                console.log('📋 Modal contains:');
                                                
                                                if (techModal.textContent.includes('Rahul Nair')) {
                                                    console.log('  ✅ Technician name');
                                                }
                                                if (techModal.textContent.includes('+91 9876543210')) {
                                                    console.log('  ✅ Phone number');
                                                }
                                                if (techModal.textContent.includes('rahul.nair@aquachain.in')) {
                                                    console.log('  ✅ Email address');
                                                }
                                                if (techModal.textContent.includes('Perumbavoor Service Center')) {
                                                    console.log('  ✅ Service center address');
                                                }
                                                if (techModal.textContent.includes('4.7')) {
                                                    console.log('  ✅ Rating');
                                                }
                                                if (techModal.textContent.includes('3 years')) {
                                                    console.log('  ✅ Experience');
                                                }
                                                
                                                console.log('🎉 Technician modal is working perfectly!');
                                                
                                                // Close the modal after 3 seconds
                                                setTimeout(() => {
                                                    const closeButton = techModal.querySelector('button[class*="hover:bg-gray-100"]');
                                                    if (closeButton) {
                                                        closeButton.click();
                                                        console.log('🔄 Closed technician modal');
                                                    }
                                                }, 3000);
                                            } else {
                                                console.log('❌ Technician Details Modal did not open');
                                            }
                                        }, 500);
                                    }
                                });
                            }
                            
                            // Close the main modal after 5 seconds
                            setTimeout(() => {
                                const closeButton = modal.querySelector('button');
                                if (closeButton) {
                                    closeButton.click();
                                    console.log('🔄 Closed order details modal');
                                }
                            }, 5000);
                        } else {
                            console.log('❌ Modal did not open');
                        }
                    }, 500);
                }
            });
        }
    });
    
    if (!technicianFound) {
        console.log('⚠️  No orders with technician assignments found on this page');
        console.log('💡 Make sure you:');
        console.log('   1. Are on the "My Orders" page');
        console.log('   2. Have orders with "Technician Assigned" status');
        console.log('   3. Are logged in with the correct user account');
    }
}

// Function to check if we're on the right page
function checkPage() {
    const pageTitle = document.title;
    const pageContent = document.body.textContent;
    
    if (pageContent.includes('My Orders') || pageContent.includes('Order Details')) {
        console.log('✅ On the correct page (My Orders)');
        return true;
    } else {
        console.log('❌ Not on the My Orders page');
        console.log('💡 Navigate to the My Orders page first');
        return false;
    }
}

// Main test function
function runTechnicianModalTest() {
    console.log('🚀 Starting Technician Modal Test...');
    
    if (checkPage()) {
        // Wait a bit for page to load
        setTimeout(() => {
            testTechnicianModal();
        }, 1000);
    }
}

// Auto-run the test
runTechnicianModalTest();

// Also provide manual trigger
window.testTechnicianModal = runTechnicianModalTest;
console.log('💡 You can also run the test manually by calling: testTechnicianModal()');