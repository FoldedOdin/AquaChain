#!/usr/bin/env python3
"""
Deploy the fix for the orders API 500 error
"""

import boto3
import zipfile
import os
import json
from datetime import datetime

def create_lambda_deployment_package():
    """Create a deployment package for the Lambda function"""
    
    print("📦 Creating Lambda deployment package...")
    
    # Create a zip file
    zip_filename = 'get_orders_fixed.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the fixed get_orders.py file
        lambda_file_path = os.path.join('..', '..', 'lambda', 'orders', 'get_orders.py')
        if os.path.exists(lambda_file_path):
            zipf.write(lambda_file_path, 'get_orders.py')
            print(f"✅ Added {lambda_file_path} to deployment package")
        else:
            print(f"❌ Lambda file not found: {lambda_file_path}")
            return None
    
    print(f"✅ Created deployment package: {zip_filename}")
    return zip_filename

def deploy_lambda_function(zip_filename):
    """Deploy the Lambda function to AWS"""
    
    print("🚀 Deploying Lambda function to AWS...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Read the zip file
        with open(zip_filename, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Update the Lambda function code
        function_name = 'aquachain-get-orders-dev'  # Correct function name
        
        try:
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            print(f"✅ Successfully updated Lambda function: {function_name}")
            print(f"   Function ARN: {response.get('FunctionArn')}")
            print(f"   Last Modified: {response.get('LastModified')}")
            print(f"   Code Size: {response.get('CodeSize')} bytes")
            
            return True
            
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"❌ Lambda function '{function_name}' not found")
            print("Available functions:")
            
            # List available functions
            functions = lambda_client.list_functions()
            for func in functions['Functions']:
                if 'order' in func['FunctionName'].lower():
                    print(f"   - {func['FunctionName']}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error deploying Lambda function: {e}")
        return False

def test_deployed_function():
    """Test the deployed function"""
    
    print("🧪 Testing deployed Lambda function...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Create test payload
        test_payload = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0'
                    }
                }
            },
            'httpMethod': 'GET',
            'path': '/api/orders'
        }
        
        function_name = 'aquachain-get-orders-dev'
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        # Read the response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"📊 Test Response Status: {response_payload.get('statusCode')}")
        
        if response_payload.get('statusCode') == 200:
            body = json.loads(response_payload.get('body', '{}'))
            orders = body.get('orders', [])
            print(f"✅ Function test successful - returned {len(orders)} orders")
            
            # Check for technician data
            for order in orders:
                if order.get('technician'):
                    print(f"   ✅ Order {order['orderId']} has technician data")
                    break
        else:
            print(f"❌ Function test failed")
            print(f"Response: {response_payload}")
        
        return response_payload.get('statusCode') == 200
        
    except Exception as e:
        print(f"❌ Error testing deployed function: {e}")
        return False

def cleanup_deployment_files():
    """Clean up temporary deployment files"""
    
    print("🧹 Cleaning up deployment files...")
    
    files_to_remove = ['get_orders_fixed.zip']
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"✅ Removed {filename}")

def main():
    """Main deployment process"""
    
    print("🚀 Starting Orders API 500 Error Fix Deployment...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Step 1: Create deployment package
        zip_filename = create_lambda_deployment_package()
        if not zip_filename:
            print("❌ Failed to create deployment package")
            return
        
        # Step 2: Deploy to AWS
        if deploy_lambda_function(zip_filename):
            print("✅ Deployment successful")
            
            # Step 3: Test the deployed function
            if test_deployed_function():
                print("✅ Function test passed")
            else:
                print("⚠️  Function deployed but test failed")
        else:
            print("❌ Deployment failed")
        
        # Step 4: Cleanup
        cleanup_deployment_files()
        
        print("\n🎯 Next Steps:")
        print("1. Test the frontend to verify the 500 error is fixed")
        print("2. Check that technician data displays correctly")
        print("3. Verify the 'View Details' modal works")
        
    except Exception as e:
        print(f"❌ Deployment process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()