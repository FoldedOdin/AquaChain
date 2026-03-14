#!/usr/bin/env python3
"""
Debug the Lambda 500 error by checking CloudWatch logs.
"""

import boto3
import json
from datetime import datetime, timedelta

def check_cloudwatch_logs():
    """Check CloudWatch logs for the specific request ID"""
    logs_client = boto3.client('logs', region_name='ap-south-1')
    
    # The request ID from the error
    request_id = "98080cd0-7d75-44d9-9838-c1bd206d5640"
    
    # Lambda function log group
    log_group = "/aws/lambda/aquachain-function-readings-service-dev"
    
    print(f"🔍 Searching for request ID: {request_id}")
    print(f"📋 Log group: {log_group}")
    
    try:
        # Search for logs in the last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        # Convert to milliseconds
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        # Search for the request ID
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern=request_id
        )
        
        if response['events']:
            print(f"\n✅ Found {len(response['events'])} log events:")
            for event in response['events']:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"\n📅 {timestamp}")
                print(f"📝 {event['message']}")
        else:
            print(f"\n❌ No logs found for request ID: {request_id}")
            print(f"   This could mean:")
            print(f"   1. Lambda didn't execute (API Gateway issue)")
            print(f"   2. Different log group name")
            print(f"   3. Logs not yet available")
            
            # Let's check recent logs anyway
            print(f"\n🔍 Checking recent logs...")
            recent_response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_ms,
                endTime=end_ms,
                limit=10
            )
            
            if recent_response['events']:
                print(f"📋 Recent log entries:")
                for event in recent_response['events'][-5:]:  # Last 5 entries
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message'][:200] + "..." if len(event['message']) > 200 else event['message']
                    print(f"   {timestamp}: {message}")
            else:
                print(f"❌ No recent logs found")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

def main():
    print("🚀 Debugging Lambda 500 error...\n")
    check_cloudwatch_logs()

if __name__ == "__main__":
    main()