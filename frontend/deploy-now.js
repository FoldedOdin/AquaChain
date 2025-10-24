#!/usr/bin/env node

/**
 * One-Click Frontend Deployment
 * Quick deployment script for AquaChain frontend
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 AquaChain Frontend - One-Click Deployment\n');

// Check if we're in the right directory
if (!fs.existsSync('package.json')) {
    console.error('❌ Please run this script from the frontend directory');
    process.exit(1);
}

// Setup standalone environment
console.log('🔧 Setting up standalone environment...');
if (fs.existsSync('.env.standalone')) {
    fs.copyFileSync('.env.standalone', '.env.production');
    console.log('✅ Environment configured for standalone deployment\n');
}

// Install dependencies if needed
console.log('📦 Checking dependencies...');
if (!fs.existsSync('node_modules')) {
    console.log('Installing dependencies...');
    execSync('npm ci', { stdio: 'inherit' });
} else {
    console.log('✅ Dependencies already installed\n');
}

// Build the application
console.log('🔨 Building application...');
try {
    execSync('npm run build', { stdio: 'inherit' });
    console.log('✅ Build completed successfully\n');
} catch (error) {
    console.error('❌ Build failed');
    process.exit(1);
}

// Show deployment options
console.log('🌐 Choose your deployment platform:\n');
console.log('1. 📱 Netlify (Recommended - Drag & Drop)');
console.log('2. ⚡ Vercel (Fast & Easy)');
console.log('3. 🌊 Surge.sh (Simple & Quick)');
console.log('4. 🐙 GitHub Pages');
console.log('5. 🐳 Docker (Local)');
console.log('6. 🏠 Local Development Server\n');

// Create deployment instructions
const instructions = `
🎉 BUILD COMPLETED SUCCESSFULLY!

Your AquaChain frontend is ready for deployment. Choose your preferred method:

📱 NETLIFY (Easiest - Recommended)
   → Go to: https://app.netlify.com/drop
   → Drag the 'build' folder to the page
   → Your site will be live in seconds!

⚡ VERCEL
   → Install: npm install -g vercel
   → Deploy: vercel --prod

🌊 SURGE.SH
   → Install: npm install -g surge
   → Deploy: surge build/ aquachain-production.surge.sh

🐙 GITHUB PAGES
   → Push to GitHub repository
   → Enable GitHub Pages in repository settings
   → Run: npm run deploy

🐳 DOCKER (Local)
   → Run: docker-compose -f docker/docker-compose.yml up -d
   → Access: http://localhost:3000

🏠 LOCAL DEVELOPMENT
   → Run: npm start
   → Access: http://localhost:3000

🎯 FEATURES INCLUDED:
   ✅ Interactive dashboards
   ✅ Real-time data integration
   ✅ User management
   ✅ Service requests
   ✅ Data visualization
   ✅ Responsive design
   ✅ PWA capabilities
   ✅ Production-ready authentication

📄 For detailed instructions, see: DEPLOYMENT_GUIDE.md
`;

console.log(instructions);

// Save instructions to file
fs.writeFileSync('DEPLOYMENT_INSTRUCTIONS.txt', instructions);
console.log('💾 Instructions saved to DEPLOYMENT_INSTRUCTIONS.txt');

// Create deployment summary
const summary = {
    buildDate: new Date().toISOString(),
    version: require('./package.json').version,
    buildSize: getBuildSize(),
    features: {
        mockData: false,
        authentication: 'production',
        realTimeData: 'live',
        analytics: true,
        pwa: true
    }
};

fs.writeFileSync('build-summary.json', JSON.stringify(summary, null, 2));
console.log('📊 Build summary saved to build-summary.json\n');

function getBuildSize() {
    try {
        const { execSync } = require('child_process');
        const size = execSync('du -sh build 2>/dev/null || echo "Unknown"', { encoding: 'utf8' });
        return size.trim().split('\t')[0];
    } catch {
        return 'Unknown';
    }
}