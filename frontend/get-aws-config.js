#!/usr/bin/env node
/**
 * Script to help get AWS infrastructure configuration
 * Run this after deploying your CDK stacks to get the actual endpoints
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 AquaChain AWS Configuration Helper');
console.log('=====================================\n');

// Check if AWS CLI is available
try {
  execSync('aws --version', { stdio: 'ignore' });
  console.log('✅ AWS CLI is available');
} catch (error) {
  console.log('❌ AWS CLI not found. Please install AWS CLI first:');
  console.log('   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html\n');
  process.exit(1);
}

// Check AWS credentials
try {
  const identity = execSync('aws sts get-caller-identity --output json', { encoding: 'utf8' });
  const { Account, Arn } = JSON.parse(identity);
  console.log(`✅ AWS credentials configured for account: ${Account}`);
  console.log(`   Identity: ${Arn}\n`);
} catch (error) {
  console.log('❌ AWS credentials not configured. Run: aws configure\n');
  process.exit(1);
}

async function getStackOutputs() {
  const environment = process.argv[2] || 'dev';
  console.log(`🔍 Looking for AquaChain stacks in environment: ${environment}\n`);

  try {
    // Get API stack outputs
    const apiStackName = `AquaChain-API-${environment}`;
    console.log(`📡 Getting outputs from ${apiStackName}...`);
    
    const apiOutputs = execSync(
      `aws cloudformation describe-stacks --stack-name ${apiStackName} --query "Stacks[0].Outputs" --output json`,
      { encoding: 'utf8' }
    );
    
    const outputs = JSON.parse(apiOutputs);
    
    // Extract key values
    const config = {};
    outputs.forEach(output => {
      switch (output.OutputKey) {
        case 'RestAPIEndpoint':
          config.apiEndpoint = output.OutputValue;
          break;
        case 'WebSocketAPIEndpoint':
          config.websocketEndpoint = output.OutputValue;
          break;
        case 'UserPoolId':
          config.userPoolId = output.OutputValue;
          break;
        case 'UserPoolClientId':
          config.userPoolClientId = output.OutputValue;
          break;
      }
    });

    // Try to get Identity Pool ID from Security stack
    try {
      const securityStackName = `AquaChain-Security-${environment}`;
      const securityOutputs = execSync(
        `aws cloudformation describe-stacks --stack-name ${securityStackName} --query "Stacks[0].Outputs" --output json`,
        { encoding: 'utf8' }
      );
      
      const securityOutputsData = JSON.parse(securityOutputs);
      securityOutputsData.forEach(output => {
        if (output.OutputKey === 'IdentityPoolId') {
          config.identityPoolId = output.OutputValue;
        }
      });
    } catch (error) {
      console.log('⚠️  Could not get Identity Pool ID from Security stack');
    }

    console.log('✅ Found configuration:');
    console.log('========================');
    console.log(`API Endpoint: ${config.apiEndpoint || 'Not found'}`);
    console.log(`WebSocket Endpoint: ${config.websocketEndpoint || 'Not found'}`);
    console.log(`User Pool ID: ${config.userPoolId || 'Not found'}`);
    console.log(`User Pool Client ID: ${config.userPoolClientId || 'Not found'}`);
    console.log(`Identity Pool ID: ${config.identityPoolId || 'Not found'}\n`);

    // Generate .env.production content
    const envContent = `# Production Environment Configuration - Generated ${new Date().toISOString()}
# AWS Configuration
REACT_APP_AWS_REGION=us-east-1
REACT_APP_USER_POOL_ID=${config.userPoolId || 'YOUR_USER_POOL_ID'}
REACT_APP_USER_POOL_CLIENT_ID=${config.userPoolClientId || 'YOUR_CLIENT_ID'}
REACT_APP_IDENTITY_POOL_ID=${config.identityPoolId || 'YOUR_IDENTITY_POOL_ID'}

# API Configuration
REACT_APP_API_ENDPOINT=${config.apiEndpoint || 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev'}
REACT_APP_WEBSOCKET_ENDPOINT=${config.websocketEndpoint || 'wss://YOUR_WEBSOCKET_API_ID.execute-api.us-east-1.amazonaws.com/dev'}

# Analytics Configuration
REACT_APP_PINPOINT_APPLICATION_ID=your-pinpoint-app-id
REACT_APP_AWS_ACCESS_KEY_ID=your-access-key-id
REACT_APP_AWS_SECRET_ACCESS_KEY=your-secret-access-key
REACT_APP_GA4_MEASUREMENT_ID=G-XXXXXXXXXX

# Security Configuration
REACT_APP_RECAPTCHA_SITE_KEY=your_production_recaptcha_key

# Feature Flags
REACT_APP_ENABLE_MOCK_DATA=false
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_AB_TESTING=true

# RUM Configuration
REACT_APP_RUM_ENDPOINT=${config.apiEndpoint ? config.apiEndpoint + '/api/rum' : 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/api/rum'}
`;

    // Write to .env.production
    fs.writeFileSync('.env.production', envContent);
    console.log('✅ Updated .env.production with actual values');
    
    // Also create .env.local for immediate use
    fs.writeFileSync('.env.local', envContent);
    console.log('✅ Created .env.local for immediate use\n');

    console.log('🚀 Next steps:');
    console.log('1. Review the generated .env.production file');
    console.log('2. Add any missing values (Pinpoint, reCAPTCHA, etc.)');
    console.log('3. Restart your React app: npm start');
    console.log('4. Your app will now connect to the deployed AWS infrastructure!\n');

  } catch (error) {
    console.error('❌ Error getting stack outputs:', error.message);
    console.log('\n💡 Troubleshooting:');
    console.log('1. Make sure your CDK stacks are deployed');
    console.log('2. Check the stack names match the expected pattern');
    console.log('3. Verify you have permissions to describe CloudFormation stacks');
    console.log('\n📋 Manual steps:');
    console.log('1. Go to AWS Console > CloudFormation');
    console.log('2. Find your AquaChain stacks');
    console.log('3. Copy the Output values to .env.production');
  }
}

getStackOutputs();