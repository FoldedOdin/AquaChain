#!/usr/bin/env node
/**
 * Debug Order Status Display Issue
 * 
 * This script helps debug why the UI shows "Order Placed" when the backend status is "DEVICE_READY"
 */

// Simulate the frontend logic
const OrderStatus = {
  PENDING_PAYMENT: 'PENDING_PAYMENT',
  PENDING_CONFIRMATION: 'PENDING_CONFIRMATION',
  ORDER_PLACED: 'ORDER_PLACED',
  DEVICE_READY: 'DEVICE_READY',
  TECHNICIAN_ASSIGNED: 'TECHNICIAN_ASSIGNED',
  SHIPPED: 'SHIPPED',
  OUT_FOR_DELIVERY: 'OUT_FOR_DELIVERY',
  DELIVERED: 'DELIVERED',
  CANCELLED: 'CANCELLED',
  FAILED: 'FAILED'
};

// Status progression (same as frontend)
const statusProgression = [
  OrderStatus.ORDER_PLACED,
  OrderStatus.DEVICE_READY,
  OrderStatus.TECHNICIAN_ASSIGNED,
  OrderStatus.SHIPPED,
  OrderStatus.OUT_FOR_DELIVERY,
  OrderStatus.DELIVERED
];

function debugStatusDisplay(currentStatus, order = null) {
  console.log('🔍 Debugging Order Status Display');
  console.log('=' * 50);
  
  const currentStatusStr = String(currentStatus);
  console.log(`Current Status: "${currentStatusStr}"`);
  
  // Check status progression
  const progressionStrings = statusProgression.map(status => String(status));
  const currentIndex = progressionStrings.indexOf(currentStatusStr);
  
  console.log(`\nStatus Progression:`);
  progressionStrings.forEach((status, index) => {
    const isCurrent = status === currentStatusStr;
    const isCompleted = currentIndex >= index && currentIndex !== -1;
    const marker = isCurrent ? '👉' : isCompleted ? '✅' : '⏳';
    console.log(`  ${marker} ${index + 1}. ${status} ${isCurrent ? '(CURRENT)' : ''}`);
  });
  
  // Calculate progress percentage
  const progressPercentage = currentIndex === -1 ? 0 : ((currentIndex + 1) / statusProgression.length) * 100;
  console.log(`\nProgress Percentage: ${Math.round(progressPercentage)}%`);
  
  // Check timeline logic
  if (order?.timeline && Array.isArray(order.timeline)) {
    console.log(`\nTimeline Data Found:`);
    order.timeline.forEach((item, index) => {
      console.log(`  ${index + 1}. ${item.status} - ${item.description || 'No description'}`);
    });
    
    // Timeline mapping logic
    const statusMapping = {
      'placed': OrderStatus.ORDER_PLACED,
      'confirmed': OrderStatus.ORDER_PLACED,
      'device_ready': OrderStatus.DEVICE_READY,
      'assigned': OrderStatus.TECHNICIAN_ASSIGNED,
      'shipped': OrderStatus.SHIPPED,
      'out_for_delivery': OrderStatus.OUT_FOR_DELIVERY,
      'delivered': OrderStatus.DELIVERED
    };
    
    const timelineStatuses = order.timeline.map(item => String(item.status));
    console.log(`\nTimeline Statuses: [${timelineStatuses.join(', ')}]`);
    
    // Check which steps are completed based on timeline
    console.log(`\nTimeline-based Completion:`);
    statusProgression.forEach((progressStatus, index) => {
      const progressStatusStr = String(progressStatus);
      
      const hasTimelineEntry = timelineStatuses.some(timelineStatus => {
        const mappedStatus = statusMapping[timelineStatus];
        return mappedStatus && String(mappedStatus) === progressStatusStr;
      });
      
      const isCurrentStatus = currentStatusStr === progressStatusStr;
      const isCompleted = hasTimelineEntry || isCurrentStatus;
      
      console.log(`  ${isCompleted ? '✅' : '⏳'} ${progressStatus} - Timeline: ${hasTimelineEntry}, Current: ${isCurrentStatus}`);
    });
  } else {
    console.log(`\nNo Timeline Data - Using Fallback Logic`);
    console.log(`Current Index: ${currentIndex}`);
    console.log(`Total Steps: ${statusProgression.length}`);
  }
  
  // Check what should be highlighted
  console.log(`\nUI Display Logic:`);
  statusProgression.forEach((status, index) => {
    const progressStatusStr = String(status);
    const isCurrent = currentStatusStr === progressStatusStr;
    const isCompleted = currentIndex >= index && currentIndex !== -1;
    
    console.log(`  Step ${index + 1}: ${status}`);
    console.log(`    - Is Current: ${isCurrent}`);
    console.log(`    - Is Completed: ${isCompleted}`);
    console.log(`    - Should Highlight: ${isCompleted ? 'YES' : 'NO'}`);
    console.log(`    - Text Color: ${isCurrent ? 'CURRENT COLOR' : isCompleted ? 'COMPLETED COLOR' : 'INACTIVE COLOR'}`);
  });
}

// Test cases
console.log('🧪 Test Case 1: DEVICE_READY status without timeline');
debugStatusDisplay('DEVICE_READY');

console.log('\n' + '='.repeat(80) + '\n');

console.log('🧪 Test Case 2: DEVICE_READY status with timeline');
debugStatusDisplay('DEVICE_READY', {
  timeline: [
    { status: 'placed', description: 'Order placed' },
    { status: 'device_ready', description: 'Device ready for assignment' }
  ]
});

console.log('\n' + '='.repeat(80) + '\n');

console.log('🧪 Test Case 3: ORDER_PLACED status (for comparison)');
debugStatusDisplay('ORDER_PLACED');

console.log('\n🔧 POTENTIAL ISSUES TO CHECK:');
console.log('1. Is the currentStatus prop being passed correctly to OrderStatusTracker?');
console.log('2. Is localCurrentStatus being updated when currentStatus changes?');
console.log('3. Is the order object missing timeline data?');
console.log('4. Are there any console errors in the browser?');
console.log('5. Is the component re-rendering when status changes?');

console.log('\n💡 DEBUGGING STEPS:');
console.log('1. Check browser console for errors');
console.log('2. Add console.log in OrderStatusTracker to see currentStatus prop');
console.log('3. Check if order object has timeline property');
console.log('4. Verify API response contains correct status');
console.log('5. Check if component state is updating correctly');