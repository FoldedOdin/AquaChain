#!/usr/bin/env node

/**
 * Development Setup Script
 * Helps set up the development environment for AquaChain
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Setting up AquaChain Development Environment...\n');

// Check if node_modules exists
if (!fs.existsSync('node_modules')) {
  console.log('📦 Installing dependencies...');
  try {
    execSync('npm install', { stdio: 'inherit' });
    console.log('✅ Dependencies installed successfully\n');
  } catch (error) {
    console.error('❌ Failed to install dependencies:', error.message);
    process.exit(1);
  }
}

// Check environment files
const envFiles = ['.env.development', '.env'];
envFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`✅ Found ${file}`);
  } else {
    console.log(`⚠️  Missing ${file} - using defaults`);
  }
});

console.log('\n🔧 Development Environment Configuration:');
console.log('- Frontend: http://localhost:3000');
console.log('- Development API: http://localhost:3001');
console.log('- WebSocket: ws://localhost:3001/ws');
console.log('- reCAPTCHA: Test keys configured');

console.log('\n📋 Available Scripts:');
console.log('- npm run start:full    # Start both frontend and dev server');
console.log('- npm run start         # Start frontend only');
console.log('- npm run dev-server    # Start development API server only');
console.log('- npm run test          # Run tests');
console.log('- npm run build         # Build for production');

console.log('\n🎯 Quick Start:');
console.log('1. Run: npm run start:full');
console.log('2. Open: http://localhost:3000');
console.log('3. Test the authentication flow:');
console.log('   - Click "Get Started" → "Sign Up"');
console.log('   - Fill form and create account');
console.log('   - Watch email verification status');
console.log('   - Switch to "Sign In" and login');

console.log('\n🧪 Test Authentication Flow:');
console.log('- Run: node test-auth-flow.js');
console.log('- This tests the complete signup → verification → login flow');

console.log('\n📚 Documentation:');
console.log('- DEVELOPMENT_FIXES.md     # Console error fixes');
console.log('- EMAIL_VERIFICATION_FLOW.md # Authentication flow details');
console.log('- PRODUCTION_SETUP.md      # Production deployment guide');
console.log('- AUTHENTICATION_GUIDE.md  # User testing guide');

console.log('\n✨ Setup complete! Happy coding!');