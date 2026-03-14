#!/usr/bin/env python3
"""
Fix the data processing Lambda validation to make location and diagnostics optional
"""

import boto3
import json
import zipfile
import os
import tempfile
from datetime import datetime

def download_lambda_code():
    """Download the current Lambda function code"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        func_name = 'aquachain-function-data-processing-dev'
        
        # Get function code
        response = lambda_client.get_function(FunctionName=func_name)
        
        code_location = response['Code']['Location']
        
        print(f"📥 Downloading Lambda code from: {code_location}")
        
        # Download the zip file
        import requests
        zip_response = requests.get(code_location)
        
        if zip_response.status_code != 200:
            print(f"❌ Failed to download code: {zip_response.status_code}")
            return None
        
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'lambda_code.zip')
        
        with open(zip_path, 'wb') as f:
            f.write(zip_response.content)
        
        print(f"✅ Downloaded code to: {zip_path}")
        return zip_path, temp_dir
        
    except Exception as e:
        print(f"❌ Error downloading Lambda code: {e}")
        return None, None

def extract_and_fix_code(zip_path, temp_dir):
    """Extract Lambda code and fix the validation"""
    try:
        # Extract zip file
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"📂 Extracted code to: {extract_dir}")
        
        # Find handler.py
        handler_path = os.path.join(extract_dir, 'handler.py')
        
        if not os.path.exists(handler_path):
            print(f"❌ handler.py not found in extracted code")
            return None
        
        # Read current handler.py
        with open(handler_path, 'r') as f:
            handler_content = f.read()
        
        print(f"📋 Original handler.py size: {len(handler_content)} characters")
        
        # Fix the validation function
        old_validation = '''def validate_data_structure(data: Dict[str, Any]) -> None:
    """
    Validate data structure using simple Python checks.
    More reliable than JSON schema validation.
    """
    # Check required top-level fields
    required_fields = ["deviceId", "timestamp", "location", "readings", "diagnostics"]
    for field in required_fields:
        if field not in data:
            raise AquaChainValidationError(
                message=f"Missing required field: {field}",
                details={'missing_field': field}
            )
    
    # Validate deviceId format (DEV-XXXX or ESP32-XXX)
    device_id = data['deviceId']
    if not isinstance(device_id, str):
        raise AquaChainValidationError(
            message="deviceId must be a string",
            details={'deviceId': device_id}
        )
    
    # Validate location
    location = data['location']
    if not isinstance(location, dict):
        raise AquaChainValidationError(
            message="location must be an object",
            details={'location': location}
        )
    if 'latitude' not in location or 'longitude' not in location:
        raise AquaChainValidationError(
            message="location must have latitude and longitude",
            details={'location': location}
        )
    
    # Validate readings
    readings = data['readings']
    if not isinstance(readings, dict):
        raise AquaChainValidationError(
            message="readings must be an object",
            details={'readings': readings}
        )
    
    required_readings = ["pH", "turbidity", "tds", "temperature"]
    for reading in required_readings:
        if reading not in readings:
            raise AquaChainValidationError(
                message=f"Missing required reading: {reading}",
                details={'missing_reading': reading}
            )
    
    # Validate diagnostics
    diagnostics = data['diagnostics']
    if not isinstance(diagnostics, dict):
        raise AquaChainValidationError(
            message="diagnostics must be an object",
            details={'diagnostics': diagnostics}
        )
    
    required_diagnostics = ["batteryLevel", "signalStrength", "sensorStatus"]
    for diag in required_diagnostics:
        if diag not in diagnostics:
            raise AquaChainValidationError(
                message=f"Missing required diagnostic: {diag}",
                details={'missing_diagnostic': diag}
            )'''

        new_validation = '''def validate_data_structure(data: Dict[str, Any]) -> None:
    """
    Validate data structure using simple Python checks.
    More reliable than JSON schema validation.
    """
    # Check required top-level fields (location and diagnostics are now optional)
    required_fields = ["deviceId", "timestamp", "readings"]
    for field in required_fields:
        if field not in data:
            raise AquaChainValidationError(
                message=f"Missing required field: {field}",
                details={'missing_field': field}
            )
    
    # Validate deviceId format (DEV-XXXX or ESP32-XXX)
    device_id = data['deviceId']
    if not isinstance(device_id, str):
        raise AquaChainValidationError(
            message="deviceId must be a string",
            details={'deviceId': device_id}
        )
    
    # Validate location (optional)
    if 'location' in data:
        location = data['location']
        if not isinstance(location, dict):
            raise AquaChainValidationError(
                message="location must be an object",
                details={'location': location}
            )
        if 'latitude' not in location or 'longitude' not in location:
            raise AquaChainValidationError(
                message="location must have latitude and longitude",
                details={'location': location}
            )
    
    # Validate readings
    readings = data['readings']
    if not isinstance(readings, dict):
        raise AquaChainValidationError(
            message="readings must be an object",
            details={'readings': readings}
        )
    
    required_readings = ["pH", "turbidity", "tds", "temperature"]
    for reading in required_readings:
        if reading not in readings:
            raise AquaChainValidationError(
                message=f"Missing required reading: {reading}",
                details={'missing_reading': reading}
            )
    
    # Validate diagnostics (optional)
    if 'diagnostics' in data:
        diagnostics = data['diagnostics']
        if not isinstance(diagnostics, dict):
            raise AquaChainValidationError(
                message="diagnostics must be an object",
                details={'diagnostics': diagnostics}
            )
        
        required_diagnostics = ["batteryLevel", "signalStrength", "sensorStatus"]
        for diag in required_diagnostics:
            if diag not in diagnostics:
                raise AquaChainValidationError(
                    message=f"Missing required diagnostic: {diag}",
                    details={'missing_diagnostic': diag}
                )'''

        # Replace the validation function
        if old_validation in handler_content:
            handler_content = handler_content.replace(old_validation, new_validation)
            print(f"✅ Updated validation function to make location and diagnostics optional")
        else:
            print(f"⚠️ Could not find exact validation function to replace")
            print(f"   Will try a different approach...")
            
            # Try to replace just the required_fields line
            old_line = 'required_fields = ["deviceId", "timestamp", "location", "readings", "diagnostics"]'
            new_line = 'required_fields = ["deviceId", "timestamp", "readings"]  # location and diagnostics are optional'
            
            if old_line in handler_content:
                handler_content = handler_content.replace(old_line, new_line)
                print(f"✅ Updated required_fields to make location and diagnostics optional")
            else:
                print(f"❌ Could not find required_fields line to update")
                return None
        
        # Also need to fix the extract_iot_data function to provide defaults
        # Look for the function that creates the data structure
        extract_function_old = '''def extract_iot_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize IoT data from various event sources.
    
    Handles events from:
    - Direct IoT Core messages
    - API Gateway requests  
    - SQS messages
    - EventBridge events
    
    Returns normalized data structure for processing.
    """
    logger.info("Extracting IoT data from event", extra={
        'event_keys': list(event.keys()),
        'event_source': event.get('source', 'unknown')
    })
    
    # Handle direct IoT data (most common case)
    if all(key in event for key in ['deviceId', 'readings']):
        logger.info("Processing as IoT data event")
        return {
            'deviceId': event.get('deviceId', 'ESP32-001'),
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            'location': {
                'latitude': event.get('latitude', 0.0),
                'longitude': event.get('longitude', 0.0)
            },
            'readings': event.get('readings', {}),
            'diagnostics': {
                'batteryLevel': event.get('batteryLevel', 100),
                'signalStrength': event.get('signalStrength', -50),
                'sensorStatus': event.get('sensorStatus', 'normal')
            }
        }'''

        extract_function_new = '''def extract_iot_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize IoT data from various event sources.
    
    Handles events from:
    - Direct IoT Core messages
    - API Gateway requests  
    - SQS messages
    - EventBridge events
    
    Returns normalized data structure for processing.
    """
    logger.info("Extracting IoT data from event", extra={
        'event_keys': list(event.keys()),
        'event_source': event.get('source', 'unknown')
    })
    
    # Handle direct IoT data (most common case)
    if all(key in event for key in ['deviceId', 'readings']):
        logger.info("Processing as IoT data event")
        
        # Build base data structure
        data = {
            'deviceId': event.get('deviceId', 'ESP32-001'),
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            'readings': event.get('readings', {})
        }
        
        # Add optional location if provided
        if 'latitude' in event and 'longitude' in event:
            data['location'] = {
                'latitude': event.get('latitude', 0.0),
                'longitude': event.get('longitude', 0.0)
            }
        elif 'location' in event:
            data['location'] = event['location']
        
        # Add optional diagnostics if provided
        if any(key in event for key in ['batteryLevel', 'signalStrength', 'sensorStatus']):
            data['diagnostics'] = {
                'batteryLevel': event.get('batteryLevel', 100),
                'signalStrength': event.get('signalStrength', -50),
                'sensorStatus': event.get('sensorStatus', 'normal')
            }
        elif 'diagnostics' in event:
            data['diagnostics'] = event['diagnostics']
        
        return data'''

        # Try to replace the extract function
        if extract_function_old in handler_content:
            handler_content = handler_content.replace(extract_function_old, extract_function_new)
            print(f"✅ Updated extract_iot_data function to handle optional fields")
        else:
            print(f"⚠️ Could not find exact extract_iot_data function to replace")
        
        # Write the fixed handler.py
        with open(handler_path, 'w') as f:
            f.write(handler_content)
        
        print(f"✅ Fixed handler.py saved")
        print(f"📋 New handler.py size: {len(handler_content)} characters")
        
        return extract_dir
        
    except Exception as e:
        print(f"❌ Error fixing code: {e}")
        return None

def create_new_zip(extract_dir, temp_dir):
    """Create new zip file with fixed code"""
    try:
        new_zip_path = os.path.join(temp_dir, 'fixed_lambda_code.zip')
        
        with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, extract_dir)
                    zip_ref.write(file_path, arc_name)
        
        print(f"✅ Created new zip file: {new_zip_path}")
        return new_zip_path
        
    except Exception as e:
        print(f"❌ Error creating zip: {e}")
        return None

def update_lambda_function(zip_path):
    """Update the Lambda function with fixed code"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        func_name = 'aquachain-function-data-processing-dev'
        
        # Read the zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        print(f"📤 Updating Lambda function: {func_name}")
        print(f"📋 New code size: {len(zip_content)} bytes")
        
        # Update function code
        response = lambda_client.update_function_code(
            FunctionName=func_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully")
        print(f"📋 New code SHA256: {response['CodeSha256']}")
        print(f"📋 Last modified: {response['LastModified']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda function: {e}")
        return False

def test_fixed_lambda():
    """Test the fixed Lambda function"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        func_name = 'aquachain-function-data-processing-dev'
        
        # Create test payload (without location and diagnostics)
        test_payload = {
            "deviceId": "ESP32-001",
            "timestamp": datetime.now().isoformat() + 'Z',
            "readings": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            }
        }
        
        print(f"\n🧪 Testing fixed Lambda with payload:")
        print(json.dumps(test_payload, indent=2))
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"\n📋 Test Response:")
        print(f"   Status Code: {response['StatusCode']}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        # Check if successful
        if response['StatusCode'] == 200 and payload.get('statusCode') == 200:
            print(f"\n✅ Fixed Lambda is working correctly!")
            return True
        else:
            print(f"\n❌ Fixed Lambda still has issues")
            return False
        
    except Exception as e:
        print(f"❌ Error testing fixed Lambda: {e}")
        return False

def main():
    print("🔧 Fixing Data Processing Lambda Validation")
    print("=" * 45)
    
    # Step 1: Download current code
    print("\n1. Downloading current Lambda code...")
    zip_path, temp_dir = download_lambda_code()
    
    if not zip_path:
        print("❌ Failed to download code")
        return
    
    # Step 2: Extract and fix code
    print("\n2. Extracting and fixing code...")
    extract_dir = extract_and_fix_code(zip_path, temp_dir)
    
    if not extract_dir:
        print("❌ Failed to fix code")
        return
    
    # Step 3: Create new zip
    print("\n3. Creating new deployment package...")
    new_zip_path = create_new_zip(extract_dir, temp_dir)
    
    if not new_zip_path:
        print("❌ Failed to create new zip")
        return
    
    # Step 4: Update Lambda function
    print("\n4. Updating Lambda function...")
    if not update_lambda_function(new_zip_path):
        print("❌ Failed to update Lambda function")
        return
    
    # Step 5: Test fixed Lambda
    print("\n5. Testing fixed Lambda...")
    if test_fixed_lambda():
        print("\n🎉 Lambda fix completed successfully!")
        
        # Step 6: Check device status
        print("\n6. Checking if device status updates now...")
        import time
        time.sleep(5)  # Wait for processing
        
        try:
            dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
            devices_table = dynamodb.Table('AquaChain-Devices')
            
            response = devices_table.get_item(Key={'deviceId': 'ESP32-001'})
            
            if 'Item' in response:
                device = response['Item']
                print(f"📋 Device Status After Fix:")
                print(f"   Connection Status: {device.get('connectionStatus', 'Not set')}")
                print(f"   Last Seen: {device.get('lastSeen', 'Not set')}")
                
                # Check if lastSeen is recent
                last_seen = device.get('lastSeen')
                if last_seen:
                    try:
                        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        now = datetime.now(last_seen_dt.tzinfo)
                        time_diff = now - last_seen_dt
                        
                        if time_diff.total_seconds() <= 300:  # 5 minutes
                            print(f"   ✅ Device lastSeen is now recent!")
                        else:
                            print(f"   ⚠️ Device lastSeen still old - may need more time")
                    except Exception as e:
                        print(f"   ❌ Error parsing lastSeen: {e}")
        except Exception as e:
            print(f"❌ Error checking device status: {e}")
    else:
        print("\n❌ Lambda fix failed")
    
    # Cleanup
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary files")
    except:
        pass

if __name__ == "__main__":
    main()