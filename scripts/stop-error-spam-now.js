/**
 * Emergency Script: Stop Error Spam Immediately
 * Run this in browser console to stop the endless polling
 */

console.log('🛑 Stopping all error spam immediately...');

// Clear all intervals to stop polling
let intervalId = setInterval(() => {}, 1000);
for (let i = 1; i <= intervalId; i++) {
  clearInterval(i);
}
console.log('✅ Cleared all intervals');

// Clear all timeouts
let timeoutId = setTimeout(() => {}, 1000);
for (let i = 1; i <= timeoutId; i++) {
  clearTimeout(i);
}
console.log('✅ Cleared all timeouts');

// Override console.error temporarily to reduce spam
const originalError = console.error;
let errorCount = 0;
console.error = function(...args) {
  errorCount++;
  if (errorCount <= 5) {
    originalError.apply(console, args);
  } else if (errorCount === 6) {
    originalError('🛑 Error spam detected - suppressing further errors');
  }
};

// Restore console.error after 30 seconds
setTimeout(() => {
  console.error = originalError;
  console.log('✅ Console.error restored');
}, 30000);

console.log('🎯 Error spam should be stopped now');
console.log('🔧 Now fix the authentication issues and refresh the page');