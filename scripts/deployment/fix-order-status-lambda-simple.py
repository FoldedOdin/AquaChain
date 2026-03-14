#!/usr/bin/env python3
"""
Fix the order status update Lambda function deployment - simple version
"""
import boto3
import zipfile
import os
import tempfile
import shutil
from pathlib import Path

def create_deployment_package():
    """Create a deployment package for the update_order_status Lambda"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy the update_order_status.py file
        source_file = Path("lambda/orders/update_order_status.py")
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Copy to temp directory
        shutil.copy2(source_file, temp_path / "update_order_status.py")
        
        # Create zip file
        zip_path = temp_path / "deployment.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_path / "update_order_status.py", "update_order_status.py")
        
        return zip_path.read_bytes()

def update_lambda_function():
    """Update the Lambda function with correct code"""
    
    lambda_client = boto3.client('lambda')
    function_name = 'aquachain-update-order-status-dev'
    
    try:
        # Create deployment package
        print("Creating deployment package...")
        deployment_package = create_deployment_package()
        
        # Update function code
        print("Updating Lambda function code...")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=deployment_package
        )
        
        print(f"✅ Successfully updated Lambda function code: {function_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda function: {e}")
        return False

def test_lambda_function():
    """Test the Lambda function with a sample request"""
    
    lambda_client = boto3.client('lambda')
    function_name = 'aquachain-update-order-status-dev'
    
    # Test payload
    test_payload = {
        "httpMethod": "PUT",
        "path": "/api/orders/test-order/status",
        "pathParameters": {
            "orderId": "test-order"
        },
        "body": '{"status": "SHIPPED", "reason": "Test status update"}'
    }
    
    try:
        print("Testing Lambda function...")
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=str(test_payload).replace("'", '"')
        )
        
        # Read response
        response_payload = response['Payload'].read().decode('utf-8')
        print(f"Response: {response_payload}")
        
        if response.get('FunctionError'):
            print(f"❌ Function error: {response['FunctionError']}")
            return False
        else:
            print("✅ Lambda function test completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing order status update Lambda function (code only)...")
    
    # Update the Lambda function
    if update_lambda_function():
        # Test the function
        test_lambda_function()
    else:
        print("❌ Failed to update Lambda function")