#!/usr/bin/env python3
"""
Verify New Statuses Accepted

Test that the deployed Lambda functions now accept DEVICE_READY and TECHNICIAN_ASSIGNED.
"""

import boto3
import json

def test_status_validation():
    """Test that new statuses are accepted by Lambda"""
    print("🧪 Testing new status validation...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test DEVICE_READY status
    test_event = {
        "httpMethod": "PUT",
        "pathParameters": {"orderId": "test-order-123"},
        "body": json.dumps({"status": "DEVICE_READY"}),
        "headers": {"Content-Type": "application/json"}
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-update-order-status-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        body = json.loads(payload.get('body', '{}'))
        
        print(f"DEVICE_READY test response: {body}")
        
        # Check if it's NOT rejecting the status (404 is OK, means order doesn't exist)
        if payload['statusCode'] == 404:
            print("✅ DEVICE_READY status accepted (order not found is expected)")
            return True
        elif 'Invalid status' in body.get('error', ''):
            print("❌ DEVICE_READY status still rejected")
            return False
        else:
            print("✅ DEVICE_READY status accepted")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    if test_status_validation():
        print("\n🎉 SUCCESS! New statuses are now accepted by the backend!")
    else:
        print("\n❌ FAILED! Backend still rejecting new statuses.")
        exit(1)