#!/usr/bin/env python3
"""
Check CloudWatch logs for the Lambda function to debug the 500 error
"""

import boto3
import json
from datetime import datetime, timedelta

def get_recent_lambda_logs():
    """Get recent logs from the Lambda function"""
    
    print("📋 Checking CloudWatch logs for Lambda function...")
    
    try:
        logs_client = boto3.client('logs', region_name='ap-south-1')
        
        # Log group name for the Lambda function
        log_group_name = '/aws/lambda/aquachain-get-orders-dev'
        
        # Get logs from the last 10 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        # Convert to milliseconds since epoch
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        print(f"🔍 Searching logs from {start_time} to {end_time}")
        
        # Get log events
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=start_time_ms,
            endTime=end_time_ms,
            limit=50
        )
        
        events = response.get('events', [])
        print(f"📊 Found {len(events)} log events")
        
        if events:
            print("\n📋 Recent Log Events:")
            print("=" * 80)
            
            for event in events[-10:]:  # Show last 10 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                
                print(f"[{timestamp}] {message}")
                
                # Highlight errors
                if 'ERROR' in message or 'Exception' in message or 'Traceback' in message:
                    print("🚨 ERROR DETECTED 🚨")
        else:
            print("⚠️  No recent log events found")
            
        return events
        
    except Exception as e:
        print(f"❌ Error retrieving logs: {e}")
        return []

def invoke_lambda_with_debug():
    """Invoke the Lambda function and capture detailed error info"""
    
    print("\n🧪 Invoking Lambda function with debug info...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        # Test payload
        test_payload = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0'
                    }
                }
            },
            'httpMethod': 'GET',
            'path': '/api/orders'
        }
        
        function_name = 'aquachain-get-orders-dev'
        
        print(f"📞 Invoking {function_name}...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload),
            LogType='Tail'  # Include execution logs
        )
        
        # Get the response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"📊 Response Status: {response_payload.get('statusCode')}")
        
        # Get execution logs
        if 'LogResult' in response:
            import base64
            log_data = base64.b64decode(response['LogResult']).decode('utf-8')
            print("\n📋 Execution Logs:")
            print("=" * 50)
            print(log_data)
        
        if response_payload.get('statusCode') != 200:
            print(f"\n❌ Error Response:")
            print(json.dumps(response_payload, indent=2))
        
        return response_payload
        
    except Exception as e:
        print(f"❌ Error invoking Lambda: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main execution"""
    
    print("🚀 Debugging Lambda function logs...")
    
    # Step 1: Get recent logs
    get_recent_lambda_logs()
    
    # Step 2: Invoke with debug info
    invoke_lambda_with_debug()

if __name__ == "__main__":
    main()