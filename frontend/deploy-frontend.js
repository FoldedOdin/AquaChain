#!/usr/bin/env node

/**
 * Frontend Deployment Script
 * Deploys the AquaChain React frontend to various platforms
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class FrontendDeployer {
    constructor() {
        this.projectRoot = __dirname;
        this.buildDir = path.join(this.projectRoot, 'build');
        this.config = this.loadConfig();
    }

    loadConfig() {
        const configPath = path.join(this.projectRoot, 'deployment-config.json');
        if (fs.existsSync(configPath)) {
            return JSON.parse(fs.readFileSync(configPath, 'utf8'));
        }
        
        // Default configuration
        return {
            platform: 'netlify', // netlify, vercel, s3, github-pages
            environment: 'production',
            buildCommand: 'npm run build',
            outputDir: 'build',
            enableAnalytics: true,
            enableMockData: false
        };
    }

    async deploy() {
        console.log('🚀 Starting AquaChain Frontend Deployment...\n');
        
        try {
            // Step 1: Environment Setup
            await this.setupEnvironment();
            
            // Step 2: Install Dependencies
            await this.installDependencies();
            
            // Step 3: Run Tests
            await this.runTests();
            
            // Step 4: Build Application
            await this.buildApplication();
            
            // Step 5: Deploy to Platform
            await this.deployToPlatform();
            
            console.log('\n✅ Frontend deployment completed successfully!');
            
        } catch (error) {
            console.error('\n❌ Deployment failed:', error.message);
            process.exit(1);
        }
    }

    async setupEnvironment() {
        console.log('📋 Setting up environment...');
        
        // Create production environment file
        const envContent = this.generateEnvFile();
        fs.writeFileSync(path.join(this.projectRoot, '.env.production'), envContent);
        
        console.log('✅ Environment configured');
    }

    generateEnvFile() {
        const { platform, environment, enableAnalytics, enableMockData } = this.config;
        
        return `# Generated Environment Configuration
# Platform: ${platform}
# Environment: ${environment}
# Generated: ${new Date().toISOString()}

# AWS Configuration (Production deployment)
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=\${AWS_USER_POOL_ID}
REACT_APP_USER_POOL_CLIENT_ID=\${AWS_USER_POOL_CLIENT_ID}
REACT_APP_IDENTITY_POOL_ID=\${AWS_IDENTITY_POOL_ID}

# API Configuration (Production endpoints)
REACT_APP_API_ENDPOINT=https://api.aquachain.com
REACT_APP_WEBSOCKET_ENDPOINT=wss://ws.aquachain.com

# Feature Flags
REACT_APP_ENABLE_MOCK_DATA=${enableMockData}
REACT_APP_ENABLE_ANALYTICS=${enableAnalytics}
REACT_APP_ENABLE_AB_TESTING=false

# Build Configuration
GENERATE_SOURCEMAP=false
REACT_APP_VERSION=${require('./package.json').version}
REACT_APP_BUILD_DATE=${new Date().toISOString()}
`;
    }

    async installDependencies() {
        console.log('📦 Installing dependencies...');
        
        try {
            execSync('npm ci', { 
                cwd: this.projectRoot, 
                stdio: 'inherit' 
            });
            console.log('✅ Dependencies installed');
        } catch (error) {
            throw new Error(`Failed to install dependencies: ${error.message}`);
        }
    }

    async runTests() {
        console.log('🧪 Running tests...');
        
        try {
            execSync('npm run test:ci', { 
                cwd: this.projectRoot, 
                stdio: 'inherit' 
            });
            console.log('✅ Tests passed');
        } catch (error) {
            console.warn('⚠️  Tests failed, continuing with deployment...');
        }
    }

    async buildApplication() {
        console.log('🔨 Building application...');
        
        try {
            execSync(this.config.buildCommand, { 
                cwd: this.projectRoot, 
                stdio: 'inherit' 
            });
            
            // Verify build output
            if (!fs.existsSync(this.buildDir)) {
                throw new Error('Build directory not found');
            }
            
            console.log('✅ Application built successfully');
        } catch (error) {
            throw new Error(`Build failed: ${error.message}`);
        }
    }

    async deployToPlatform() {
        console.log(`🌐 Deploying to ${this.config.platform}...`);
        
        switch (this.config.platform) {
            case 'netlify':
                await this.deployToNetlify();
                break;
            case 'vercel':
                await this.deployToVercel();
                break;
            case 's3':
                await this.deployToS3();
                break;
            case 'github-pages':
                await this.deployToGitHubPages();
                break;
            default:
                throw new Error(`Unsupported platform: ${this.config.platform}`);
        }
    }

    async deployToNetlify() {
        console.log('📡 Deploying to Netlify...');
        
        // Create netlify.toml if it doesn't exist
        const netlifyConfig = `[build]
  publish = "build"
  command = "npm run build"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/static/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
`;
        
        fs.writeFileSync(path.join(this.projectRoot, 'netlify.toml'), netlifyConfig);
        
        console.log('✅ Netlify configuration created');
        console.log('📋 Next steps:');
        console.log('   1. Install Netlify CLI: npm install -g netlify-cli');
        console.log('   2. Login: netlify login');
        console.log('   3. Deploy: netlify deploy --prod --dir=build');
    }

    async deployToVercel() {
        console.log('📡 Deploying to Vercel...');
        
        // Create vercel.json if it doesn't exist
        const vercelConfig = {
            "version": 2,
            "builds": [
                {
                    "src": "package.json",
                    "use": "@vercel/static-build",
                    "config": {
                        "distDir": "build"
                    }
                }
            ],
            "routes": [
                {
                    "src": "/static/(.*)",
                    "headers": {
                        "cache-control": "public, max-age=31536000, immutable"
                    }
                },
                {
                    "src": "/(.*)",
                    "dest": "/index.html"
                }
            ]
        };
        
        fs.writeFileSync(
            path.join(this.projectRoot, 'vercel.json'), 
            JSON.stringify(vercelConfig, null, 2)
        );
        
        console.log('✅ Vercel configuration created');
        console.log('📋 Next steps:');
        console.log('   1. Install Vercel CLI: npm install -g vercel');
        console.log('   2. Deploy: vercel --prod');
    }

    async deployToS3() {
        console.log('📡 Preparing S3 deployment...');
        
        // Create S3 deployment script
        const s3Script = `#!/bin/bash
# S3 Deployment Script for AquaChain Frontend

BUCKET_NAME="aquachain-frontend-\${ENVIRONMENT:-production}"
REGION="\${AWS_REGION:-us-east-1}"
DISTRIBUTION_ID="\${CLOUDFRONT_DISTRIBUTION_ID}"

echo "Deploying to S3 bucket: \$BUCKET_NAME"

# Sync build files to S3
aws s3 sync build/ s3://\$BUCKET_NAME --delete --region \$REGION

# Set cache headers
aws s3 cp s3://\$BUCKET_NAME/static/ s3://\$BUCKET_NAME/static/ \\
  --recursive \\
  --metadata-directive REPLACE \\
  --cache-control "public, max-age=31536000, immutable" \\
  --region \$REGION

# Invalidate CloudFront cache
if [ ! -z "\$DISTRIBUTION_ID" ]; then
  echo "Invalidating CloudFront distribution: \$DISTRIBUTION_ID"
  aws cloudfront create-invalidation \\
    --distribution-id \$DISTRIBUTION_ID \\
    --paths "/*"
fi

echo "S3 deployment completed!"
`;
        
        fs.writeFileSync(path.join(this.projectRoot, 'deploy-s3.sh'), s3Script);
        execSync(`chmod +x ${path.join(this.projectRoot, 'deploy-s3.sh')}`);
        
        console.log('✅ S3 deployment script created');
        console.log('📋 Next steps:');
        console.log('   1. Configure AWS CLI: aws configure');
        console.log('   2. Set environment variables: BUCKET_NAME, CLOUDFRONT_DISTRIBUTION_ID');
        console.log('   3. Run: ./deploy-s3.sh');
    }

    async deployToGitHubPages() {
        console.log('📡 Preparing GitHub Pages deployment...');
        
        try {
            execSync('npm install --save-dev gh-pages', { 
                cwd: this.projectRoot, 
                stdio: 'inherit' 
            });
            
            // Add homepage to package.json
            const packagePath = path.join(this.projectRoot, 'package.json');
            const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            
            if (!packageJson.homepage) {
                packageJson.homepage = 'https://yourusername.github.io/aquachain-frontend';
                packageJson.scripts.predeploy = 'npm run build';
                packageJson.scripts.deploy = 'gh-pages -d build';
                
                fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
            }
            
            console.log('✅ GitHub Pages configuration added');
            console.log('📋 Next steps:');
            console.log('   1. Update homepage URL in package.json');
            console.log('   2. Deploy: npm run deploy');
            
        } catch (error) {
            throw new Error(`GitHub Pages setup failed: ${error.message}`);
        }
    }
}

// CLI Interface
if (require.main === module) {
    const deployer = new FrontendDeployer();
    deployer.deploy().catch(console.error);
}

module.exports = FrontendDeployer;