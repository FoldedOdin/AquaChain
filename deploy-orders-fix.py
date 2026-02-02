#!/usr/bin/env python3
"""
Deploy the orders Lambda function with deduplication fix
"""

import boto3
import zipfile
import os
import json
from pathlib import Path

def create_lambda_package():
    """Create deployment package for the orders Lambda"""
    
    # Create a zip file
    zip_path = 'orders-lambda-fix.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the main handler
        zipf.write('lambda/orders/get_orders.py', 'get_orders.py')
        
        # Add shared dependencies
        shared_dir = Path('lambda/shared')
        if shared_dir.exists():
            for file_path in shared_dir.rglob('*.py'):
                arcname = str(file_path.relative_to('lambda/shared'))
                zipf.write(file_path, arcname)
    
    print(f"✅ Created deployment package: {zip_path}")
    return zip_path

def update_lambda_function(zip_path):
    """Update the Lambda function with the new code"""
    
    lambda_client = boto3.client('lambda')
    
    # Function name - adjust based on your deployment
    function_names = [
        'AquaChain-GetOrders-dev',
        'AquaChain-Orders-GetOrders-dev',
        'get-orders',
        'orders-get'
    ]
    
    for function_name in function_names:
        try:
            # Check if function exists
            lambda_client.get_function(FunctionName=function_name)
            
            # Update function code
            with open(zip_path, 'rb') as zip_file:
                response = lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_file.read()
                )
            
            print(f"✅ Updated Lambda function: {function_name}")
            print(f"   Version: {response['Version']}")
            print(f"   Last Modified: {response['LastModified']}")
            return True
            
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"⚠️  Function not found: {function_name}")
            continue
        except Exception as e:
            print(f"❌ Error updating {function_name}: {str(e)}")
            continue
    
    print("❌ No Lambda functions were updated")
    return False

def main():
    """Main deployment function"""
    
    print("🚀 Deploying Orders Lambda Fix")
    print("=" * 40)
    
    try:
        # Create deployment package
        zip_path = create_lambda_package()
        
        # Update Lambda function
        success = update_lambda_function(zip_path)
        
        # Clean up
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"🧹 Cleaned up: {zip_path}")
        
        if success:
            print("\n✅ Deployment completed successfully!")
            print("\n📋 Next Steps:")
            print("1. Test the API: GET /api/orders/my")
            print("2. Check CloudWatch logs for deduplication warnings")
            print("3. Verify frontend no longer shows duplicate console messages")
        else:
            print("\n❌ Deployment failed!")
            print("\n🔧 Manual Steps:")
            print("1. Check your Lambda function names in AWS Console")
            print("2. Update the function_names list in this script")
            print("3. Ensure you have proper AWS credentials configured")
            
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")

if __name__ == "__main__":
    main()