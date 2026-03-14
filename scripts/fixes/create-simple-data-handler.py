#!/usr/bin/env python3
"""
Create a simple data processing handler that works with IoT device data
"""

import boto3
import json
import os
import tempfile
import zipfile

def create_simple_handler():
    """Create a simple handler that doesn't require location/diagnostics"""
    
    handler_code = '''import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
devices_table = dynamodb.Table(os.environ.get('DEVICES_TABLE', 'AquaChain-Devices'))
readings_table = dynamodb.Table(os.environ.get('READINGS_TABLE', 'AquaChain-Readings'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simple IoT data processing handler
    Accepts: deviceId, timestamp, readings (pH, turbidity, tds, temperature)
    """
    print(f"📥 Received event: {json.dumps(event)}")
    
    try:
        # Extract required fields
        device_id = event.get('deviceId')
        readings = event.get('readings', {})
        timestamp = event.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        
        if not device_id:
            raise ValueError("Missing deviceId")
        
        if not readings:
            raise ValueError("Missing readings")
        
        # Validate required readings
        required_readings = ['pH', 'turbidity', 'tds', 'temperature']
        for reading in required_readings:
            if reading not in readings:
                raise ValueError(f"Missing required reading: {reading}")
        
        print(f"✅ Processing data for device: {device_id}")
        
        # Store reading in DynamoDB
        month_key = f"{device_id}_{datetime.fromisoformat(timestamp.replace('Z', '')).strftime('%Y-%m')}"
        
        reading_item = {
            'deviceId_month': month_key,
            'timestamp': timestamp,
            'deviceId': device_id,
            'pH': float(readings['pH']),
            'turbidity': float(readings['turbidity']),
            'tds': float(readings['tds']),
            'temperature': float(readings['temperature']),
            'metric_type': 'sensor_reading'
        }
        
        readings_table.put_item(Item=reading_item)
        print(f"✅ Stored reading in DynamoDB")
        
        # Update device lastSeen and status
        devices_table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression='SET lastSeen = :ts, connectionStatus = :status, statusUpdatedAt = :status_ts',
            ExpressionAttributeValues={
                ':ts': timestamp,
                ':status': 'online',
                ':status_ts': timestamp
            }
        )
        print(f"✅ Updated device {device_id} lastSeen and status to online")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Reading processed successfully',
                'deviceId': device_id,
                'timestamp': timestamp
            })
        }
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
'''
    
    return handler_code

def deploy_simple_handler():
    """Deploy the simple handler to Lambda"""
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Write handler code
        handler_path = os.path.join(temp_dir, 'handler.py')
        with open(handler_path, 'w', encoding='utf-8') as f:
            f.write(create_simple_handler())
        
        print(f"Created simple handler: {handler_path}")
        
        # Create zip file
        zip_path = os.path.join(temp_dir, 'simple_handler.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            zip_ref.write(handler_path, 'handler.py')
        
        print(f"Created deployment package: {zip_path}")
        
        # Update Lambda function
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        func_name = 'aquachain-function-data-processing-dev'
        
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=func_name,
            ZipFile=zip_content
        )
        
        print(f"Updated Lambda function: {func_name}")
        print(f"New code SHA256: {response['CodeSha256']}")
        
        # Test the function
        from datetime import datetime
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
        
        print(f"Testing simple handler...")
        
        test_response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        test_result = json.loads(test_response['Payload'].read())
        
        print(f"Test Result:")
        print(json.dumps(test_result, indent=2))
        
        if test_result.get('statusCode') == 200:
            print(f"Simple handler is working correctly!")
            return True
        else:
            print(f"Simple handler test failed")
            return False
        
    except Exception as e:
        print(f"❌ Error deploying simple handler: {e}")
        return False

def main():
    print("🔧 Creating Simple Data Processing Handler")
    print("=" * 40)
    
    if deploy_simple_handler():
        print(f"\n🎉 Simple handler deployed successfully!")
        print(f"\nThis handler:")
        print(f"✅ Accepts IoT data without location/diagnostics requirements")
        print(f"✅ Updates device lastSeen timestamp automatically")
        print(f"✅ Sets device status to 'online' when data is received")
        print(f"✅ Stores readings in DynamoDB")
        
        print(f"\nYour device should now show as 'Online' and stay updated!")
    else:
        print(f"\n❌ Failed to deploy simple handler")

if __name__ == "__main__":
    main()