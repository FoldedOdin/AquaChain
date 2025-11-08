#!/usr/bin/env node

/**
 * CloudFront Deployment Script
 * Deploys the AquaChain React frontend to S3 with CloudFront cache invalidation
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class CloudFrontDeployer {
    constructor() {
        this.projectRoot = __dirname;
        this.buildDir = path.join(this.projectRoot, 'build');
        this.config = this.loadConfig();
    }

    loadConfig() {
        // Load from environment variables or config file
        return {
            bucketName: process.env.FRONTEND_BUCKET_NAME || 'aquachain-frontend-production',
            distributionId: process.env.CLOUDFRONT_DISTRIBUTION_ID,
            region: process.env.AWS_REGION || 'us-east-1',
            environment: process.env.ENVIRONMENT || 'production',
            buildCommand: 'npm run build',
            invalidatePaths: ['/*'],
            dryRun: process.argv.includes('--dry-run')
        };
    }

    async deploy() {
        console.log('🚀 Starting CloudFront Deployment...\n');
        console.log(`Environment: ${this.config.environment}`);
        console.log(`Bucket: ${this.config.bucketName}`);
        console.log(`Distribution: ${this.config.distributionId || 'Not configured'}`);
        console.log(`Dry Run: ${this.config.dryRun ? 'Yes' : 'No'}\n`);
        
        try {
            // Step 1: Validate prerequisites
            await this.validatePrerequisites();
            
            // Step 2: Build application
            await this.buildApplication();
            
            // Step 3: Upload to S3
            await this.uploadToS3();
            
            // Step 4: Set cache headers
            await this.setCacheHeaders();
            
            // Step 5: Invalidate CloudFront cache
            await this.invalidateCache();
            
            console.log('\n✅ CloudFront deployment completed successfully!');
            console.log(`\n🌐 Frontend URL: https://${this.config.distributionId ? 'your-domain.com' : `${this.config.bucketName}.s3-website-${this.config.region}.amazonaws.com`}`);
            
        } catch (error) {
            console.error('\n❌ Deployment failed:', error.message);
            process.exit(1);
        }
    }

    async validatePrerequisites() {
        console.log('🔍 Validating prerequisites...');
        
        // Check AWS CLI
        try {
            execSync('aws --version', { stdio: 'pipe' });
        } catch (error) {
            throw new Error('AWS CLI not found. Please install it: https://aws.amazon.com/cli/');
        }
        
        // Check AWS credentials
        try {
            execSync('aws sts get-caller-identity', { stdio: 'pipe' });
        } catch (error) {
            throw new Error('AWS credentials not configured. Run: aws configure');
        }
        
        // Check bucket exists
        try {
            execSync(`aws s3 ls s3://${this.config.bucketName}`, { stdio: 'pipe' });
        } catch (error) {
            throw new Error(`S3 bucket not found: ${this.config.bucketName}`);
        }
        
        console.log('✅ Prerequisites validated');
    }

    async buildApplication() {
        console.log('🔨 Building application...');
        
        if (this.config.dryRun) {
            console.log('⏭️  Skipping build (dry run)');
            return;
        }
        
        try {
            // Set production environment
            process.env.NODE_ENV = 'production';
            process.env.GENERATE_SOURCEMAP = 'false';
            
            execSync(this.config.buildCommand, { 
                cwd: this.projectRoot, 
                stdio: 'inherit',
                env: { ...process.env }
            });
            
            // Verify build output
            if (!fs.existsSync(this.buildDir)) {
                throw new Error('Build directory not found');
            }
            
            // Get build size
            const buildSize = this.getBuildSize();
            console.log(`✅ Application built successfully (${buildSize})`);
            
        } catch (error) {
            throw new Error(`Build failed: ${error.message}`);
        }
    }

    getBuildSize() {
        const { execSync } = require('child_process');
        try {
            const output = execSync(`du -sh ${this.buildDir}`, { encoding: 'utf8' });
            return output.split('\t')[0];
        } catch (error) {
            return 'unknown';
        }
    }

    async uploadToS3() {
        console.log('📤 Uploading to S3...');
        
        const dryRunFlag = this.config.dryRun ? '--dryrun' : '';
        
        try {
            // Sync all files to S3
            const syncCommand = `aws s3 sync ${this.buildDir}/ s3://${this.config.bucketName}/ \
                --delete \
                --region ${this.config.region} \
                ${dryRunFlag}`;
            
            execSync(syncCommand, { 
                cwd: this.projectRoot, 
                stdio: 'inherit' 
            });
            
            console.log('✅ Files uploaded to S3');
            
        } catch (error) {
            throw new Error(`S3 upload failed: ${error.message}`);
        }
    }

    async setCacheHeaders() {
        console.log('🏷️  Setting cache headers...');
        
        if (this.config.dryRun) {
            console.log('⏭️  Skipping cache headers (dry run)');
            return;
        }
        
        try {
            // Set long cache for static assets (365 days)
            console.log('   Setting cache headers for static assets (365 days)...');
            const staticCommand = `aws s3 cp s3://${this.config.bucketName}/static/ s3://${this.config.bucketName}/static/ \
                --recursive \
                --metadata-directive REPLACE \
                --cache-control "public, max-age=31536000, immutable" \
                --region ${this.config.region}`;
            
            execSync(staticCommand, { stdio: 'pipe' });
            
            // Set short cache for HTML files (5 minutes)
            console.log('   Setting cache headers for HTML files (5 minutes)...');
            const htmlCommand = `aws s3 cp s3://${this.config.bucketName}/ s3://${this.config.bucketName}/ \
                --recursive \
                --exclude "*" \
                --include "*.html" \
                --metadata-directive REPLACE \
                --cache-control "public, max-age=300, must-revalidate" \
                --content-type "text/html" \
                --region ${this.config.region}`;
            
            execSync(htmlCommand, { stdio: 'pipe' });
            
            // Set cache for JSON files (1 hour)
            console.log('   Setting cache headers for JSON files (1 hour)...');
            const jsonCommand = `aws s3 cp s3://${this.config.bucketName}/ s3://${this.config.bucketName}/ \
                --recursive \
                --exclude "*" \
                --include "*.json" \
                --metadata-directive REPLACE \
                --cache-control "public, max-age=3600" \
                --content-type "application/json" \
                --region ${this.config.region}`;
            
            execSync(jsonCommand, { stdio: 'pipe' });
            
            console.log('✅ Cache headers configured');
            
        } catch (error) {
            console.warn('⚠️  Failed to set cache headers:', error.message);
        }
    }

    async invalidateCache() {
        if (!this.config.distributionId) {
            console.log('⏭️  Skipping cache invalidation (no distribution ID configured)');
            return;
        }
        
        console.log('🔄 Invalidating CloudFront cache...');
        
        if (this.config.dryRun) {
            console.log('⏭️  Skipping cache invalidation (dry run)');
            return;
        }
        
        try {
            const paths = this.config.invalidatePaths.join(' ');
            const invalidateCommand = `aws cloudfront create-invalidation \
                --distribution-id ${this.config.distributionId} \
                --paths ${paths}`;
            
            const output = execSync(invalidateCommand, { 
                encoding: 'utf8',
                stdio: 'pipe'
            });
            
            const invalidation = JSON.parse(output);
            const invalidationId = invalidation.Invalidation.Id;
            
            console.log(`✅ Cache invalidation created: ${invalidationId}`);
            console.log('   Note: Invalidation may take 5-10 minutes to complete');
            
        } catch (error) {
            throw new Error(`Cache invalidation failed: ${error.message}`);
        }
    }

    async checkInvalidationStatus(invalidationId) {
        console.log('⏳ Checking invalidation status...');
        
        try {
            const statusCommand = `aws cloudfront get-invalidation \
                --distribution-id ${this.config.distributionId} \
                --id ${invalidationId}`;
            
            const output = execSync(statusCommand, { 
                encoding: 'utf8',
                stdio: 'pipe'
            });
            
            const invalidation = JSON.parse(output);
            const status = invalidation.Invalidation.Status;
            
            console.log(`   Status: ${status}`);
            return status;
            
        } catch (error) {
            console.warn('⚠️  Failed to check invalidation status:', error.message);
            return 'Unknown';
        }
    }
}

// CLI Interface
if (require.main === module) {
    const args = process.argv.slice(2);
    
    // Show help
    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
CloudFront Deployment Script

Usage:
  node deploy-cloudfront.js [options]

Options:
  --dry-run              Simulate deployment without making changes
  --help, -h             Show this help message

Environment Variables:
  FRONTEND_BUCKET_NAME          S3 bucket name (required)
  CLOUDFRONT_DISTRIBUTION_ID    CloudFront distribution ID (optional)
  AWS_REGION                    AWS region (default: us-east-1)
  ENVIRONMENT                   Deployment environment (default: production)

Examples:
  # Deploy to production
  FRONTEND_BUCKET_NAME=aquachain-frontend-prod \\
  CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC \\
  node deploy-cloudfront.js

  # Dry run
  FRONTEND_BUCKET_NAME=aquachain-frontend-prod \\
  node deploy-cloudfront.js --dry-run
        `);
        process.exit(0);
    }
    
    const deployer = new CloudFrontDeployer();
    deployer.deploy().catch(console.error);
}

module.exports = CloudFrontDeployer;
