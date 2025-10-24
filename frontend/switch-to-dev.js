#!/usr/bin/env node
/**
 * Switch AquaChain frontend back to development mode
 */

const fs = require('fs');
const path = require('path');

console.log('🔄 Switching AquaChain to Development Mode');
console.log('=========================================\n');

// Remove .env.local to use .env.development
const envLocalPath = '.env.local';
if (fs.existsSync(envLocalPath)) {
  fs.unlinkSync(envLocalPath);
  console.log('🗑️  Removed .env.local');
}

// Ensure .env.development exists
const envDevPath = '.env.development';
if (!fs.existsSync(envDevPath)) {
  console.log('❌ .env.development not found, creating default...');
  
  const defaultDevConfig = `# Development Environment Configuration
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=us-east-1_dev_example
REACT_APP_USER_POOL_CLIENT_ID=dev_client_id
REACT_APP_IDENTITY_POOL_ID=us-east-1:dev-identity-pool-id

# Local API Configuration
REACT_APP_API_ENDPOINT=http://localhost:3002

# Local WebSocket Configuration
REACT_APP_WEBSOCKET_ENDPOINT=ws://localhost:3002/ws

# Analytics Configuration (Development)
REACT_APP_PINPOINT_APPLICATION_ID=dev-pinpoint-app-id
REACT_APP_AWS_ACCESS_KEY_ID=your-dev-access-key-id
REACT_APP_AWS_SECRET_ACCESS_KEY=your-dev-secret-access-key
REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX

# Development Feature Flags
REACT_APP_ENABLE_MOCK_DATA=true
REACT_APP_ENABLE_ANALYTICS=false

# reCAPTCHA Configuration (Development - use test keys)
REACT_APP_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI

# RUM Configuration
REACT_APP_RUM_ENDPOINT=http://localhost:3002/api/rum
`;
  
  fs.writeFileSync(envDevPath, defaultDevConfig);
  console.log('✅ Created default .env.development');
}

console.log('\n🚀 Development Mode Active');
console.log('=========================');
console.log('API Endpoint: http://localhost:3002');
console.log('WebSocket: ws://localhost:3002/ws');
console.log('Mode: Development with local dev server');

console.log('\n📋 Next steps:');
console.log('1. Start the development server: npm run dev-server');
console.log('2. Start your React app: npm start');
console.log('3. Use test credentials for authentication');
console.log('\n🔄 To switch back to AWS mode:');
console.log('   node switch-to-aws.js');