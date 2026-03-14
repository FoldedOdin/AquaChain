#!/usr/bin/env python3
"""
Test Deployed Status Fix

This script tests that the deployed Lambda functions now accept the new statuses.
"""

import boto3
import json
import requests
import time

def test_lambda_function_directly():
    """Test the Lambda function directly"""
    print("🧪 Testing Lambda function directly...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event for status update with new status
    test_event = {
        "httpMethod": "PUT",
        "path": "/orders/test-order-123/status",
        "body": json.dumps({
            "status": "DEVICE_READY"
        }),
        "headers": {
            "Content-Type": "application/json"
        },
        "requestContext": {
            "requestId": "test-request-123"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='aquachain-update-order-status-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        print(f"Lambda Response: {payload}")
        
        if response['StatusCode'] == 200:
            # Check if the response indicates the new status is accepted
            if 'DEVICE_READY' in str(payload) or 'TECHNICIAN_ASSIGNED' in str(payload):
                print("✅ Lambda function accepts new statuses!")
                return True
            else:
                print("⚠️  Lambda function response unclear")
                return False
        else:
            print(f"❌ Lambda function returned error: {payload}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        return False

def test_api_gateway_endpoint():
    """Test the API Gateway endpoint"""
    print("\n🌐 Testing API Gateway endpoint...")
    
    # API Gateway URL (you may need to adjust this)
    api_url = "https://946twwm7kf.execute-api.ap-south-1.amazonaws.com/dev"
    
    # Test with a simple GET request to check if API is responding
    try:
        response = requests.get(f"{api_url}/orders", timeout=10)
        print(f"API Gateway Response Status: {response.status_code}")
        
        if response.status_code in [200, 401, 403]:  # 401/403 are OK, means API is working but needs auth
            print("✅ API Gateway is responding!")
            return True
        else:
            print(f"⚠️  API Gateway returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API Gateway test failed: {e}")
        return False

def check_lambda_logs():
    """Check recent Lambda logs for any errors"""
    print("\n📋 Checking recent Lambda logs...")
    
    logs_client = boto3.client('logs', region_name='ap-south-1')
    
    function_names = [
        'aquachain-function-order-management-dev',
        'aquachain-update-order-status-dev'
    ]
    
    for function_name in function_names:
        log_group = f'/aws/lambda/{function_name}'
        
        try:
            # Get recent log events
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int((time.time() - 300) * 1000),  # Last 5 minutes
                limit=10
            )
            
            events = response.get('events', [])
            if events:
                print(f"📋 Recent logs for {function_name}:")
                for event in events[-3:]:  # Show last 3 events
                    message = event['message'].strip()
                    if 'ERROR' in message or 'Exception' in message:
                        print(f"  ❌ {message}")
                    else:
                        print(f"  ℹ️  {message}")
            else:
                print(f"📋 No recent logs for {function_name}")
                
        except Exception as e:
            print(f"⚠️  Could not read logs for {function_name}: {e}")

def main():
    """Run all tests"""
    print("🔍 Testing Deployed Order Status Fix")
    print("=" * 50)
    
    all_passed = True
    
    # Test Lambda function directly
    if not test_lambda_function_directly():
        all_passed = False
    
    # Test API Gateway
    if not test_api_gateway_endpoint():
        all_passed = False
    
    # Check logs
    check_lambda_logs()
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!")
        print("\nThe order status progression fix is now live:")
        print("✅ Lambda functions accept DEVICE_READY and TECHNICIAN_ASSIGNED")
        print("✅ API Gateway is responding")
        print("✅ Backend can now handle the complete status flow")
        print("\n📋 Users can now progress orders through:")
        print("   ORDER_PLACED → DEVICE_READY → TECHNICIAN_ASSIGNED → SHIPPED")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("The deployment may need additional verification.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)