#!/usr/bin/env python3
"""
Fix and redeploy alert detection Lambda function
Removes incompatible error handler and uses standard Python logging
"""

import boto3
import zipfile
import os
import sys
from pathlib import Path

# Configuration
LAMBDA_FUNCTION_NAME = 'aquachain-function-alert-detection-dev'
REGION = 'ap-south-1'
LAMBDA_DIR = 'lambda/alert_detection'

def create_deployment_package():
    """Create Lambda deployment package"""
    print("📦 Creating deployment package...")
    
    # Files to include
    files_to_include = [
        'handler.py',
        'requirements.txt'
    ]
    
    # Create zip file
    zip_path = os.path.join(LAMBDA_DIR, 'function.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_include:
            file_path = os.path.join(LAMBDA_DIR, file)
            if os.path.exists(file_path):
                zipf.write(file_path, file)
                print(f"  ✅ Added {file}")
            else:
                print(f"  ⚠️  Warning: {file} not found")
    
    print(f"✅ Deployment package created: {zip_path}")
    return zip_path

def deploy_lambda(zip_path):
    """Deploy Lambda function"""
    print(f"\n🚀 Deploying Lambda function: {LAMBDA_FUNCTION_NAME}")
    
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content,
            Publish=True
        )
        
        print(f"✅ Lambda deployed successfully!")
        print(f"   Function ARN: {response['FunctionArn']}")
        print(f"   Version: {response['Version']}")
        print(f"   Last Modified: {response['LastModified']}")
        print(f"   Code Size: {response['CodeSize']} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

def verify_deployment():
    """Verify Lambda deployment"""
    print("\n🔍 Verifying deployment...")
    
    try:
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Get function configuration
        response = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        
        config = response['Configuration']
        
        print(f"✅ Function verified:")
        print(f"   Runtime: {config['Runtime']}")
        print(f"   Handler: {config['Handler']}")
        print(f"   Memory: {config['MemorySize']} MB")
        print(f"   Timeout: {config['Timeout']} seconds")
        print(f"   State: {config['State']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main deployment process"""
    print("=" * 60)
    print("🔧 Alert Detection Lambda Fix & Deployment")
    print("=" * 60)
    
    # Step 1: Create deployment package
    zip_path = create_deployment_package()
    
    # Step 2: Deploy Lambda
    if not deploy_lambda(zip_path):
        print("\n❌ Deployment failed!")
        sys.exit(1)
    
    # Step 3: Verify deployment
    if not verify_deployment():
        print("\n⚠️  Deployment succeeded but verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Alert Detection Lambda Fixed and Deployed!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Test alert generation:")
    print("   python scripts/testing/test-alert-generation.py critical")
    print("\n2. Check Lambda logs:")
    print(f"   aws logs tail /aws/lambda/{LAMBDA_FUNCTION_NAME} --region {REGION} --follow")
    print("\n3. Verify alerts in DynamoDB:")
    print("   aws dynamodb scan --table-name aquachain-alerts --region ap-south-1")

if __name__ == '__main__':
    main()
