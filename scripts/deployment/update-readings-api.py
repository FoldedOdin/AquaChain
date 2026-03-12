#!/usr/bin/env python3
"""
Update the data processing Lambda function with new readings API endpoints
"""

import boto3
import json
import zipfile
import os
import sys
from pathlib import Path

def update_lambda_function():
    """Update the data processing Lambda function"""
    
    # Get the Lambda function name
    function_name = "aquachain-function-data-processing-dev"
    
    # Create Lambda client
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    try:
        # Get current function configuration
        response = lambda_client.get_function(FunctionName=function_name)
        print(f"✅ Found Lambda function: {function_name}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Handler: {response['Configuration']['Handler']}")
        
        # Create a zip file with the updated code
        lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "data_processing"
        zip_path = Path("/tmp/data_processing_update.zip")
        
        print(f"📦 Creating deployment package from: {lambda_dir}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in lambda_dir.rglob("*.py"):
                if "__pycache__" not in str(file_path):
                    arcname = file_path.relative_to(lambda_dir)
                    zipf.write(file_path, arcname)
                    print(f"   Added: {arcname}")
        
        # Update the function code
        print(f"🚀 Updating Lambda function code...")
        
        with open(zip_path, 'rb') as zip_file:
            update_response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"   Version: {update_response['Version']}")
        print(f"   Last Modified: {update_response['LastModified']}")
        
        # Clean up
        os.remove(zip_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda function: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Updating data processing Lambda function with readings API endpoints...")
    
    success = update_lambda_function()
    
    if success:
        print("\n✅ Deployment completed successfully!")
        print("\n📋 New endpoints available:")
        print("   - GET /api/v1/readings/{deviceId}")
        print("   - GET /api/v1/readings/{deviceId}/latest")
        print("   - GET /api/v1/readings/{deviceId}/history")
        print("\n🔍 Test the endpoints:")
        print("   curl -H 'Authorization: Bearer <token>' https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest")
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()