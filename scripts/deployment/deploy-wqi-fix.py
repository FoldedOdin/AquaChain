#!/usr/bin/env python3

"""
Deploy WQI Fix
Updates Lambda functions with WQI calculation fixes
"""

import boto3
import json
import zipfile
import os
import sys
from pathlib import Path

def create_lambda_zip(source_dir: str, zip_path: str, exclude_patterns: list = None):
    """Create a zip file for Lambda deployment"""
    exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', '.git', 'tests']
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
            
            for file in files:
                # Skip excluded files
                if any(pattern in file for pattern in exclude_patterns):
                    continue
                
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arc_path)
    
    print(f"   ✅ Created zip: {zip_path}")

def update_lambda_function(function_name: str, zip_path: str):
    """Update Lambda function code"""
    try:
        lambda_client = boto3.client('lambda')
        
        with open(zip_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file.read()
            )
        
        print(f"   ✅ Updated function: {function_name}")
        print(f"   📊 Version: {response['Version']}")
        print(f"   📊 Last Modified: {response['LastModified']}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating {function_name}: {e}")
        return False

def deploy_data_processing():
    """Deploy updated data processing Lambda"""
    print("🚀 Deploying data processing Lambda...")
    
    source_dir = "lambda/data_processing"
    zip_path = "lambda/data_processing.zip"
    function_name = "aquachain-function-data-processing-dev"
    
    if not os.path.exists(source_dir):
        print(f"   ❌ Source directory not found: {source_dir}")
        return False
    
    # Create deployment package
    create_lambda_zip(source_dir, zip_path)
    
    # Update function
    success = update_lambda_function(function_name, zip_path)
    
    # Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    return success

def deploy_readings_service():
    """Deploy updated readings service Lambda"""
    print("\n🚀 Deploying readings service Lambda...")
    
    source_dir = "lambda/readings_service"
    zip_path = "lambda/readings_service.zip"
    function_name = "aquachain-function-readings-service-dev"
    
    if not os.path.exists(source_dir):
        print(f"   ❌ Source directory not found: {source_dir}")
        return False
    
    # Create deployment package
    create_lambda_zip(source_dir, zip_path)
    
    # Update function
    success = update_lambda_function(function_name, zip_path)
    
    # Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    return success

def test_wqi_calculation():
    """Test WQI calculation after deployment"""
    print("\n🧪 Testing WQI calculation...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Test data processing Lambda
        test_payload = {
            "deviceId": "TEST-DEVICE-WQI",
            "timestamp": "2024-03-14T12:00:00Z",
            "location": {"latitude": 12.9716, "longitude": 77.5946},
            "readings": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            },
            "diagnostics": {
                "batteryLevel": 85,
                "signalStrength": -45,
                "sensorStatus": "normal"
            }
        }
        
        print("   🧪 Testing data processing Lambda...")
        response = lambda_client.invoke(
            FunctionName='aquachain-function-data-processing-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            wqi = body.get('wqi')
            print(f"   ✅ Data processing test successful!")
            print(f"   📊 WQI: {wqi}")
            
            if wqi and wqi != 'N/A':
                print(f"   🎉 WQI calculation is working!")
                return True
            else:
                print(f"   ⚠️  WQI still showing as N/A")
                return False
        else:
            print(f"   ❌ Data processing test failed: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing WQI calculation: {e}")
        return False

def test_readings_service():
    """Test readings service after deployment"""
    print("\n🧪 Testing readings service...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Test readings service
        test_event = {
            "httpMethod": "GET",
            "path": "/api/readings/TEST-DEVICE-001",
            "pathParameters": {"deviceId": "TEST-DEVICE-001"},
            "queryStringParameters": {"days": "7"},
            "headers": {"Authorization": "Bearer test-token"}
        }
        
        print("   🧪 Testing readings service Lambda...")
        response = lambda_client.invoke(
            FunctionName='aquachain-function-readings-service-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print(f"   ✅ Readings service test successful!")
            return True
        else:
            print(f"   ❌ Readings service test failed: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing readings service: {e}")
        return False

def main():
    """Main deployment function"""
    print("🔧 AquaChain WQI Fix Deployment")
    print("=" * 50)
    
    # Deploy Lambda functions
    data_processing_ok = deploy_data_processing()
    readings_service_ok = deploy_readings_service()
    
    if data_processing_ok and readings_service_ok:
        print("\n✅ All Lambda functions deployed successfully!")
        
        # Test the fixes
        wqi_test_ok = test_wqi_calculation()
        readings_test_ok = test_readings_service()
        
        print("\n📋 DEPLOYMENT SUMMARY")
        print("=" * 50)
        print(f"Data Processing Lambda: {'✅ Deployed' if data_processing_ok else '❌ Failed'}")
        print(f"Readings Service Lambda: {'✅ Deployed' if readings_service_ok else '❌ Failed'}")
        print(f"WQI Calculation Test:   {'✅ Working' if wqi_test_ok else '❌ Failed'}")
        print(f"Readings Service Test:  {'✅ Working' if readings_test_ok else '❌ Failed'}")
        
        if wqi_test_ok:
            print("\n🎉 WQI ISSUE FIXED!")
            print("✅ New IoT readings will have WQI and Quality calculated")
            print("✅ Existing readings will show calculated WQI when viewed")
            print("✅ Dashboard should now display proper WQI values")
        else:
            print("\n⚠️  WQI calculation may still have issues")
            print("📋 Check CloudWatch logs for detailed error information")
    else:
        print("\n❌ Deployment failed!")
        print("📋 Check AWS credentials and Lambda function names")

if __name__ == "__main__":
    main()