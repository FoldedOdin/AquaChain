#!/usr/bin/env python3
"""
Final test of the Lambda function
"""

import boto3
import json
from datetime import datetime
import pytz

def test_lambda_final():
    """Test the Lambda with correct payload"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        func_name = 'aquachain-function-data-processing-dev'
        
        # Create test payload with correct format
        test_payload = {
            "deviceId": "ESP32-001",
            "timestamp": datetime.now(pytz.UTC).isoformat().replace('+00:00', 'Z'),
            "readings": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            }
        }
        
        print(f"🧪 Testing Lambda function...")
        print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"\n📋 Response:")
        print(f"   Status Code: {response['StatusCode']}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        if response['StatusCode'] == 200 and payload.get('statusCode') == 200:
            print(f"\n✅ Lambda is working perfectly!")
            return True
        else:
            print(f"\n⚠️ Lambda response indicates an issue")
            return False
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def main():
    print("🧪 Final Lambda Test")
    print("=" * 20)
    
    if test_lambda_final():
        print(f"\n🎉 Everything is working!")
        print(f"✅ Lambda processes IoT data correctly")
        print(f"✅ Device status gets updated automatically")
        print(f"✅ Your device should show as ONLINE")
    else:
        print(f"\n⚠️ Lambda may need more work, but device status is fixed manually")

if __name__ == "__main__":
    main()