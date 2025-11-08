#!/usr/bin/env node
/**
 * Switch AquaChain frontend to use AWS infrastructure
 */

const fs = require('fs');
const path = require('path');

console.log('🔄 Switching AquaChain to AWS Infrastructure Mode');
console.log('===============================================\n');

// Stop the dev server process
console.log('🛑 Stopping development server...');
try {
  const { execSync } = require('child_process');
  // Kill any running dev-server processes
  if (process.platform === 'win32') {
    execSync('taskkill /f /im node.exe 2>nul || echo "No dev server running"', { stdio: 'inherit' });
  } else {
    execSync('pkill -f "dev-server" || echo "No dev server running"', { stdio: 'inherit' });
  }
} catch (error) {
  // Ignore errors - process might not be running
}

// Check if AWS configuration exists
const envProductionPath = '.env.production';
const envLocalPath = '.env.local';

if (!fs.existsSync(envProductionPath)) {
  console.log('❌ .env.production not found');
  console.log('📋 Please run: node get-aws-config.js [environment]');
  console.log('   This will fetch your deployed AWS endpoints\n');
  process.exit(1);
}

// Copy production config to local for immediate use
console.log('📋 Copying AWS configuration...');
const productionConfig = fs.readFileSync(envProductionPath, 'utf8');

// Remove localhost references and ensure AWS endpoints
if (productionConfig.includes('localhost')) {
  console.log('⚠️  Warning: .env.production still contains localhost URLs');
  console.log('   Please update with your actual AWS endpoints\n');
}

fs.writeFileSync(envLocalPath, productionConfig);
console.log('✅ Created .env.local with AWS configuration');

// Create a backup of current development config
const envDevPath = '.env.development';
if (fs.existsSync(envDevPath)) {
  const backupPath = '.env.development.backup';
  if (!fs.existsSync(backupPath)) {
    fs.copyFileSync(envDevPath, backupPath);
    console.log('💾 Backed up .env.development');
  }
}

console.log('\n🚀 Configuration Summary:');
console.log('========================');

// Parse and display current config
const config = {};
productionConfig.split('\n').forEach(line => {
  if (line.startsWith('REACT_APP_') && line.includes('=')) {
    const [key, value] = line.split('=');
    config[key] = value;
  }
});

console.log(`API Endpoint: ${config.REACT_APP_API_ENDPOINT || 'Not set'}`);
console.log(`WebSocket: ${config.REACT_APP_WEBSOCKET_ENDPOINT || 'Not set'}`);
console.log(`User Pool: ${config.REACT_APP_USER_POOL_ID || 'Not set'}`);
console.log(`Region: ${config.REACT_APP_AWS_REGION || 'Not set'}`);

console.log('\n✅ Ready to use AWS infrastructure!');
console.log('\n📋 Next steps:');
console.log('1. Start your React app: npm start');
console.log('2. Your app will now use AWS Cognito and API Gateway');
console.log('3. Create users through AWS Cognito console or signup flow');
console.log('\n🔄 To switch back to development mode:');
console.log('   node switch-to-dev.js');