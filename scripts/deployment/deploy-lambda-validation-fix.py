#!/usr/bin/env python3
"""
Deploy Lambda validation fix for data_processing function
This fixes the JSON schema validation issue that was rejecting ESP32 data
"""

import boto3
import zipfile
import os
import json
import time
from pathlib import Path

def create_deployment_package():
    """Create Lambda deployment package"""
    print("Step 1: Creating deployment package...")
    
    lambda_dir = Path("lambda/data_processing")
    zip_path = lambda_dir / "package.zip"
    
    # Remove old package if exists
    if zip_path.exists():
        zip_path.unlink()
    
    # Create zip file with handler.py
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        handler_path = lambda_dir / "handler.py"
        zipf.write(handler_path, "handler.py")
    
    print(f"✓ Created deployment package: {zip_path}")
    return zip_path

def deploy_lambda(zip_path):
    """Deploy Lambda function to AWS"""
    print("\nStep 2: Deploying to AWS Lambda...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'aquachain-function-data-processing-dev'
    
    try:
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✓ Lambda function updated successfully")
        print(f"  Function ARN: {response['FunctionArn']}")
        print(f"  Last Modified: {response['LastModified']}")
        print(f"  Code Size: {response['CodeSize']} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Lambda deployment failed: {str(e)}")
        return False

def test_lambda():
    """Test Lambda function with sample ESP32 data"""
    print("\nStep 3: Testing Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'aquachain-function-data-processing-dev'
    
    # Sample ESP32 data
    test_payload = {
        "deviceId": "ESP32-001",
        "timestamp": "2026-03-08T14:00:00Z",
        "location": {
            "latitude": 0,
            "longitude": 0
        },
        "readings": {
            "pH": 7.0,
            "turbidity": 300,
            "tds": 45,
            "temperature": 30
        },
        "diagnostics": {
            "batteryLevel": 100,
            "signalStrength": -70,
            "sensorStatus": "normal"
        }
    }
    
    try:
        # Wait for Lambda to be ready
        print("  Waiting for Lambda to be ready...")
        time.sleep(5)
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"\n✓ Lambda test successful!")
        print(f"  Status Code: {response['StatusCode']}")
        print(f"  Response:")
        print(f"    {json.dumps(response_payload, indent=4)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Lambda test failed: {str(e)}")
        return False

def cleanup(zip_path):
    """Clean up deployment artifacts"""
    if zip_path.exists():
        zip_path.unlink()
        print(f"\n✓ Cleaned up deployment package")

def main():
    """Main deployment function"""
    print("=" * 50)
    print("Deploying Lambda Validation Fix")
    print("=" * 50)
    print()
    
    try:
        # Create deployment package
        zip_path = create_deployment_package()
        
        # Deploy to AWS
        if not deploy_lambda(zip_path):
            cleanup(zip_path)
            return 1
        
        # Test the deployment
        if not test_lambda():
            cleanup(zip_path)
            return 1
        
        # Cleanup
        cleanup(zip_path)
        
        print()
        print("=" * 50)
        print("Deployment Complete!")
        print("=" * 50)
        print()
        print("The Lambda function has been updated with simplified validation.")
        print("Your ESP32 device should now be able to send data successfully.")
        print()
        print("Next steps:")
        print("1. Check CloudWatch Logs for validation success messages")
        print("2. Query DynamoDB to verify new readings are being stored")
        print("3. Monitor your ESP32 device for successful data transmission")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Deployment failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
