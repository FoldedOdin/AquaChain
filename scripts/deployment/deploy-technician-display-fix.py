#!/usr/bin/env python3
"""
Deploy technician display fix - update get_orders Lambda to include technician details
"""

import boto3
import json
import zipfile
import os
import sys
from pathlib import Path

def create_lambda_package():
    """Create deployment package for get_orders Lambda"""
    
    # Create temporary directory for package
    package_dir = Path("temp_lambda_package")
    package_dir.mkdir(exist_ok=True)
    
    # Copy Lambda function
    lambda_file = Path("lambda/orders/get_orders.py")
    if not lambda_file.exists():
        print(f"❌ Lambda function not found: {lambda_file}")
        return None
    
    # Copy to package directory
    import shutil
    shutil.copy2(lambda_file, package_dir / "get_orders.py")
    
    # Create ZIP package
    zip_path = Path("get_orders_deployment.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(package_dir / "get_orders.py", "get_orders.py")
    
    # Cleanup
    shutil.rmtree(package_dir)
    
    return zip_path

def deploy_lambda_function():
    """Deploy the updated Lambda function"""
    
    print("🚀 Deploying technician display fix...")
    
    # Create deployment package
    zip_path = create_lambda_package()
    if not zip_path:
        return False
    
    try:
        # Initialize AWS clients
        lambda_client = boto3.client('lambda')
        
        # Function name (adjust based on your actual function name)
        function_names = [
            'AquaChain-Function-GetOrders-dev',
            'aquachain-get-orders-dev',
            'get-orders-dev'
        ]
        
        deployed = False
        
        for function_name in function_names:
            try:
                print(f"📦 Trying to update function: {function_name}")
                
                # Read the ZIP file
                with open(zip_path, 'rb') as zip_file:
                    zip_content = zip_file.read()
                
                # Update function code
                response = lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                print(f"✅ Successfully updated {function_name}")
                print(f"   Function ARN: {response['FunctionArn']}")
                print(f"   Last Modified: {response['LastModified']}")
                print(f"   Code Size: {response['CodeSize']} bytes")
                
                deployed = True
                break
                
            except lambda_client.exceptions.ResourceNotFoundException:
                print(f"⚠️  Function {function_name} not found, trying next...")
                continue
            except Exception as e:
                print(f"❌ Error updating {function_name}: {str(e)}")
                continue
        
        if not deployed:
            print("❌ Could not find any matching Lambda function to update")
            print("Available functions:")
            
            # List all Lambda functions
            try:
                paginator = lambda_client.get_paginator('list_functions')
                for page in paginator.paginate():
                    for func in page['Functions']:
                        if 'order' in func['FunctionName'].lower():
                            print(f"   - {func['FunctionName']}")
            except Exception as e:
                print(f"   Error listing functions: {e}")
            
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False
    
    finally:
        # Cleanup ZIP file
        if zip_path and zip_path.exists():
            zip_path.unlink()

def test_deployment():
    """Test the deployed function"""
    
    print("\n🧪 Testing deployed function...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Test event (simulating API Gateway event)
        test_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "test-user-id"
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/api/v1/orders"
        }
        
        function_names = [
            'AquaChain-Function-GetOrders-dev',
            'aquachain-get-orders-dev',
            'get-orders-dev'
        ]
        
        for function_name in function_names:
            try:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_event)
                )
                
                # Parse response
                payload = json.loads(response['Payload'].read())
                
                if response['StatusCode'] == 200:
                    print(f"✅ Function {function_name} test successful")
                    
                    # Check if response includes technician data structure
                    if 'body' in payload:
                        body = json.loads(payload['body'])
                        if 'orders' in body:
                            print(f"   📊 Response includes orders array")
                            if body['orders']:
                                sample_order = body['orders'][0]
                                if 'technician' in sample_order or 'technicianAssignment' in sample_order:
                                    print(f"   ✅ Technician data structure present")
                                else:
                                    print(f"   ℹ️  No technician data in sample order (expected if no assignments)")
                    
                    return True
                else:
                    print(f"⚠️  Function {function_name} returned status {response['StatusCode']}")
                    print(f"   Response: {payload}")
                
                break
                
            except lambda_client.exceptions.ResourceNotFoundException:
                continue
            except Exception as e:
                print(f"❌ Test failed for {function_name}: {str(e)}")
                continue
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main deployment function"""
    
    print("🔧 AquaChain Technician Display Fix Deployment")
    print("=" * 50)
    
    # Deploy Lambda function
    if not deploy_lambda_function():
        print("\n❌ Deployment failed!")
        sys.exit(1)
    
    # Test deployment
    if not test_deployment():
        print("\n⚠️  Deployment succeeded but tests failed")
        print("   The function was deployed but may have issues")
    else:
        print("\n✅ Deployment and testing completed successfully!")
    
    print("\n📋 Next Steps:")
    print("1. Test the frontend to see technician details")
    print("2. Create a test order with technician assignment")
    print("3. Verify the modal popup works correctly")
    print("4. Check that all technician information displays properly")

if __name__ == "__main__":
    main()