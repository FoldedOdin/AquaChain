#!/usr/bin/env python3
"""
Deploy Lambda function with device ID validation fix
"""

import boto3
import zipfile
import os
import sys
import shutil
from pathlib import Path

def create_deployment_package():
    """Create Lambda deployment package"""
    print("📦 Creating deployment package...")
    
    lambda_dir = Path("lambda/data_processing")
    package_dir = lambda_dir / "package"
    zip_path = lambda_dir / "data_processing.zip"
    
    # Clean up old package
    if package_dir.exists():
        shutil.rmtree(package_dir)
    if zip_path.exists():
        zip_path.unlink()
    
    package_dir.mkdir(exist_ok=True)
    
    # Install dependencies
    print("   Installing dependencies...")
    os.system(f"pip install -r {lambda_dir}/requirements.txt -t {package_dir} --quiet")
    
    # Copy handler
    print("   Copying handler.py...")
    shutil.copy(lambda_dir / "handler.py", package_dir / "handler.py")
    
    # Create zip file
    print("   Creating zip archive...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(package_dir)
    
    print(f"   ✅ Package created: {zip_path}")
    return zip_path

def deploy_lambda(zip_path):
    """Deploy Lambda function"""
    print("\n🚀 Deploying to AWS Lambda...")
    
    lambda_client = boto3.client('lambda')
    function_name = 'aquachain-function-data-processing-dev'  # Correct function name
    
    try:
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"   ✅ Function updated: {response['FunctionArn']}")
        print(f"   Version: {response['Version']}")
        print(f"   Last Modified: {response['LastModified']}")
        
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"   ❌ Function '{function_name}' not found")
        print(f"   Create the function first using CDK deployment")
        return False
        
    except Exception as e:
        print(f"   ❌ Deployment failed: {e}")
        return False

def verify_deployment():
    """Verify the deployment"""
    print("\n🔍 Verifying deployment...")
    
    lambda_client = boto3.client('lambda')
    function_name = 'aquachain-function-data-processing-dev'  # Correct function name
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        
        print(f"   Function: {response['Configuration']['FunctionName']}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Handler: {response['Configuration']['Handler']}")
        print(f"   Memory: {response['Configuration']['MemorySize']} MB")
        print(f"   Timeout: {response['Configuration']['Timeout']} seconds")
        print(f"   ✅ Deployment verified")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False

def main():
    print("="*60)
    print("Deploy Lambda Device ID Validation Fix")
    print("="*60)
    print()
    
    # Check if we're in the right directory
    if not Path("lambda/data_processing/handler.py").exists():
        print("❌ Error: Run this script from the project root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    # Create deployment package
    zip_path = create_deployment_package()
    
    # Deploy to Lambda
    if not deploy_lambda(zip_path):
        sys.exit(1)
    
    # Verify deployment
    if not verify_deployment():
        sys.exit(1)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    zip_path.unlink()
    print("   ✅ Cleanup complete")
    
    print("\n" + "="*60)
    print("✅ Deployment Complete!")
    print("="*60)
    print()
    print("Updated validation pattern:")
    print("  - Accepts: DEV-0001 through DEV-9999")
    print("  - Accepts: ESP32-001 through ESP32-999")
    print()
    print("Next steps:")
    print("  1. Test with: python scripts/testing/test_esp32_format.py")
    print("  2. Check CloudWatch logs for validation success")
    print("  3. Verify data in DynamoDB tables")
    print()

if __name__ == '__main__':
    main()
