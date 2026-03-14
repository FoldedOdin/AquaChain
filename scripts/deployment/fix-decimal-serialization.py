#!/usr/bin/env python3
"""
Fix Decimal serialization issue in readings Lambda
"""

import boto3
import zipfile
import os
import json
from pathlib import Path

def deploy_readings_lambda_fix():
    """Deploy the fixed readings Lambda with Decimal conversion"""
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Lambda function name
    function_name = 'aquachain-function-readings-service-dev'
    
    print(f"🔧 Deploying Decimal serialization fix to {function_name}...")
    
    # Create deployment package
    lambda_dir = Path('lambda/readings_service')
    zip_path = Path('readings_service_fixed.zip')
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add handler.py
        handler_path = lambda_dir / 'handler.py'
        if handler_path.exists():
            zipf.write(handler_path, 'handler.py')
            print(f"✅ Added {handler_path}")
        else:
            print(f"❌ Handler not found: {handler_path}")
            return False
    
    # Read the zip file
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Update Lambda function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"📦 Code SHA256: {response['CodeSha256']}")
        print(f"🕒 Last Modified: {response['LastModified']}")
        
        # Clean up
        os.remove(zip_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda function: {e}")
        # Clean up
        if zip_path.exists():
            os.remove(zip_path)
        return False

def test_fixed_endpoint():
    """Test the fixed endpoint"""
    import requests
    
    # Test endpoint
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    # Get a fresh token (you'll need to provide this)
    headers = {
        'Authorization': 'Bearer eyJraWQiOiJiWUJ3RGVsWVlkYmFIeVwvcUtlWXJPbDJlUVk2d1hIODVlM00zOFFBMEloWT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI1MWEzZWQ0YS1jMGIxLTcwZTgtYTdkNy0xOWQ3Y2EwMzVmZTAiLCJjb2duaXRvOmdyb3VwcyI6WyJjb25zdW1lcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb21cL2FwLXNvdXRoLTFfUVVEbDdoRzh1IiwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjUxYTNlZDRhLWMwYjEtNzBlOC1hN2Q3LTE5ZDdjYTAzNWZlMCIsImdpdmVuX25hbWUiOiJLYXJ0aGlrIiwib3JpZ2luX2p0aSI6ImFkNWE4MDlk',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🧪 Testing fixed endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Response data:")
            print(json.dumps(data, indent=2))
            
            # Check if reading contains proper float values
            if 'reading' in data:
                reading = data['reading']
                print(f"\n🔍 Checking data types:")
                for key, value in reading.items():
                    print(f"  {key}: {type(value).__name__} = {value}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Fixing Decimal serialization issue in readings Lambda...")
    
    if deploy_readings_lambda_fix():
        print("\n⏳ Waiting 5 seconds for deployment to propagate...")
        import time
        time.sleep(5)
        
        test_fixed_endpoint()
    else:
        print("❌ Deployment failed!")