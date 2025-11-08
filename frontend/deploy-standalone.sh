#!/bin/bash

# AquaChain Frontend Standalone Deployment Script
# This script deploys the frontend with mock data for demonstration purposes

set -e

echo "🚀 AquaChain Frontend Standalone Deployment"
echo "============================================"

# Configuration
DEPLOYMENT_TYPE=${1:-netlify}
BUILD_ENV=${2:-standalone}

echo "📋 Deployment Configuration:"
echo "   Type: $DEPLOYMENT_TYPE"
echo "   Environment: $BUILD_ENV"
echo ""

# Step 1: Setup Environment
echo "🔧 Setting up environment..."
if [ "$BUILD_ENV" = "standalone" ]; then
    cp .env.standalone .env.production
    echo "✅ Standalone environment configured"
else
    echo "✅ Using existing environment configuration"
fi

# Step 2: Install Dependencies
echo "📦 Installing dependencies..."
if [ ! -d "node_modules" ]; then
    npm ci
else
    echo "✅ Dependencies already installed"
fi

# Step 3: Run Health Check
echo "🏥 Running health check..."
npm run health-check || echo "⚠️  Health check failed, continuing..."

# Step 4: Run Tests (optional)
echo "🧪 Running tests..."
npm run test:ci || echo "⚠️  Tests failed, continuing with deployment..."

# Step 5: Build Application
echo "🔨 Building application..."
npm run build

# Verify build
if [ ! -d "build" ]; then
    echo "❌ Build failed - build directory not found"
    exit 1
fi

echo "✅ Build completed successfully"

# Step 6: Deploy based on type
case $DEPLOYMENT_TYPE in
    "netlify")
        echo "🌐 Preparing Netlify deployment..."
        echo "📋 Next steps:"
        echo "   1. Install Netlify CLI: npm install -g netlify-cli"
        echo "   2. Login to Netlify: netlify login"
        echo "   3. Deploy: netlify deploy --prod --dir=build"
        echo ""
        echo "   Or drag and drop the 'build' folder to https://app.netlify.com/drop"
        ;;
    
    "vercel")
        echo "🌐 Preparing Vercel deployment..."
        echo "📋 Next steps:"
        echo "   1. Install Vercel CLI: npm install -g vercel"
        echo "   2. Deploy: vercel --prod"
        ;;
    
    "surge")
        echo "🌐 Deploying to Surge.sh..."
        if ! command -v surge &> /dev/null; then
            echo "Installing Surge CLI..."
            npm install -g surge
        fi
        
        # Create CNAME file for custom domain (optional)
        echo "aquachain-demo.surge.sh" > build/CNAME
        
        echo "Deploying to Surge..."
        surge build/ aquachain-demo.surge.sh
        ;;
    
    "github-pages")
        echo "🌐 Preparing GitHub Pages deployment..."
        npm install --save-dev gh-pages
        
        # Add deploy script to package.json if not exists
        node -e "
        const fs = require('fs');
        const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        if (!pkg.scripts.deploy) {
            pkg.scripts.predeploy = 'npm run build';
            pkg.scripts.deploy = 'gh-pages -d build';
            fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
            console.log('✅ Deploy scripts added to package.json');
        }
        "
        
        echo "📋 Next steps:"
        echo "   1. Update homepage in package.json to your GitHub Pages URL"
        echo "   2. Deploy: npm run deploy"
        ;;
    
    "docker")
        echo "🐳 Building Docker image..."
        docker build -f docker/Dockerfile -t aquachain-frontend:latest .
        
        echo "🚀 Starting Docker container..."
        docker-compose -f docker/docker-compose.yml up -d
        
        echo "✅ Frontend deployed with Docker"
        echo "🌐 Access at: http://localhost:3000"
        ;;
    
    "local")
        echo "🏠 Starting local development server..."
        echo "🌐 Frontend will be available at: http://localhost:3000"
        npm start
        ;;
    
    *)
        echo "❌ Unknown deployment type: $DEPLOYMENT_TYPE"
        echo "Available options: netlify, vercel, surge, github-pages, docker, local"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment preparation completed!"
echo "🎉 AquaChain Frontend is ready for $DEPLOYMENT_TYPE deployment"

# Create deployment summary
cat > deployment-summary.md << EOF
# AquaChain Frontend Deployment Summary

**Deployment Type:** $DEPLOYMENT_TYPE  
**Environment:** $BUILD_ENV  
**Build Date:** $(date)  
**Version:** $(node -p "require('./package.json').version")

## Features Enabled
- Mock Data: ✅ Enabled
- Analytics: ❌ Disabled (standalone mode)
- Real-time Updates: ❌ Disabled (standalone mode)
- Authentication: 🔄 Mock Authentication

## Build Information
- Build Size: $(du -sh build 2>/dev/null | cut -f1 || echo "Unknown")
- Node Version: $(node --version)
- NPM Version: $(npm --version)

## Access Information
- Demo User: demo@aquachain.com
- Demo Password: demo123
- Features: All dashboard features available with mock data

## Next Steps
Follow the deployment instructions above to complete the deployment process.
EOF

echo "📄 Deployment summary saved to deployment-summary.md"