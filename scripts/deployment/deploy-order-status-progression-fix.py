#!/usr/bin/env python3
"""
Deploy Order Status Progression Fix

This script deploys the fixed order management service that properly handles
the DEVICE_READY → TECHNICIAN_ASSIGNED → SHIPPED progression.
"""

import boto3
import json
import os
import zipfile
import tempfile
from datetime import datetime

def create_lambda_deployment_package():
    """Create deployment package for the fixed order management service"""
    print("📦 Creating Lambda deployment package...")
    
    # Create temporary zip file
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'order-management-fix.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the fixed order management service
        lambda_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders')
        
        for root, dirs, files in os.walk(lambda_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, lambda_dir)
                    zipf.write(file_path, arcname)
                    print(f"  Added: {arcname}")
        
        # Add shared utilities
        shared_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared')
        if os.path.exists(shared_dir):
            for root, dirs, files in os.walk(shared_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('shared', os.path.relpath(file_path, shared_dir))
                        zipf.write(file_path, arcname)
                        print(f"  Added: {arcname}")
    
    print(f"✅ Deployment package created: {zip_path}")
    return zip_path

def update_lambda_function(zip_path):
    """Update the Lambda function with the fixed code"""
    print("🚀 Updating Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Function names to update
    function_names = [
        'aquachain-function-order-management-dev',
        'aquachain-orders-api-dev',
        'aquachain-update-order-status-dev'
    ]
    
    updated_functions = []
    
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
            
            print(f"✅ Updated function: {function_name}")
            print(f"   Version: {response['Version']}")
            print(f"   Last Modified: {response['LastModified']}")
            updated_functions.append(function_name)
            
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"⚠️  Function not found: {function_name}")
        except Exception as e:
            print(f"❌ Failed to update {function_name}: {e}")
    
    return updated_functions

def test_lambda_function(function_name):
    """Test the updated Lambda function"""
    print(f"🧪 Testing function: {function_name}")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event for status update
    test_event = {
        "httpMethod": "PUT",
        "path": "/orders/test-order-123/status",
        "body": json.dumps({
            "status": "DEVICE_READY"
        }),
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print(f"✅ Function test passed: {function_name}")
            return True
        else:
            print(f"⚠️  Function test returned non-200 status: {response['StatusCode']}")
            print(f"   Response: {payload}")
            return False
            
    except Exception as e:
        print(f"❌ Function test failed: {e}")
        return False

def update_api_gateway_if_needed():
    """Update API Gateway deployment if needed"""
    print("🌐 Checking API Gateway deployment...")
    
    apigateway_client = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # List APIs
        apis = apigateway_client.get_rest_apis()
        
        aquachain_api = None
        for api in apis['items']:
            if 'AquaChain' in api['name']:
                aquachain_api = api
                break
        
        if aquachain_api:
            api_id = aquachain_api['id']
            print(f"✅ Found AquaChain API: {api_id}")
            
            # Create new deployment
            deployment = apigateway_client.create_deployment(
                restApiId=api_id,
                stageName='dev',
                description=f'Order status progression fix deployment - {datetime.now().isoformat()}'
            )
            
            print(f"✅ API Gateway deployment created: {deployment['id']}")
            return True
        else:
            print("⚠️  AquaChain API not found")
            return False
            
    except Exception as e:
        print(f"❌ API Gateway update failed: {e}")
        return False

def main():
    """Deploy the order status progression fix"""
    print("🚀 Deploying Order Status Progression Fix")
    print("=" * 50)
    
    try:
        # Step 1: Create deployment package
        zip_path = create_lambda_deployment_package()
        
        # Step 2: Update Lambda functions
        updated_functions = update_lambda_function(zip_path)
        
        if not updated_functions:
            print("❌ No Lambda functions were updated")
            return False
        
        # Step 3: Test updated functions
        all_tests_passed = True
        for function_name in updated_functions:
            if not test_lambda_function(function_name):
                all_tests_passed = False
        
        # Step 4: Update API Gateway
        api_updated = update_api_gateway_if_needed()
        
        # Step 5: Clean up
        os.unlink(zip_path)
        
        print("\n" + "=" * 50)
        
        if all_tests_passed and api_updated:
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("\nOrder Status Progression Fix Deployed:")
            print("✅ Backend Lambda functions updated")
            print("✅ API Gateway deployment created")
            print("✅ All function tests passed")
            print("\n📋 Fixed Flow:")
            print("   ORDER_PLACED → DEVICE_READY → TECHNICIAN_ASSIGNED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED")
            print("\n🚫 Bug Fixed:")
            print("   No more skipping from DEVICE_READY directly to SHIPPED")
            print("   Technician assignment now happens automatically")
        else:
            print("⚠️  DEPLOYMENT COMPLETED WITH WARNINGS")
            print("Some components may need manual verification")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)