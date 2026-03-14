#!/usr/bin/env python3
"""
Search CloudWatch logs for specific request ID to find the exact error
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def search_logs_for_request_id(request_id):
    """Search CloudWatch logs for a specific request ID"""
    
    logs_client = boto3.client('logs', region_name='ap-south-1')
    log_group = '/aws/lambda/aquachain-function-readings-service-dev'
    
    print(f"🔍 Searching CloudWatch logs for request ID: {request_id}")
    
    try:
        # Search in the last 24 hours
        end_time = int(time.time() * 1000)
        start_time = end_time - (24 * 60 * 60 * 1000)  # 24 hours ago
        
        # Search for the request ID
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            filterPattern=request_id,
            limit=50
        )
        
        events = response.get('events', [])
        
        if events:
            print(f"✅ Found {len(events)} log events for request ID: {request_id}")
            
            # Group events by request
            request_events = []
            for event in events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                request_events.append({
                    'timestamp': timestamp,
                    'message': message
                })
            
            # Sort by timestamp
            request_events.sort(key=lambda x: x['timestamp'])
            
            print(f"\n📋 Complete log sequence for request {request_id}:")
            print("="*80)
            
            for event in request_events:
                timestamp_str = event['timestamp'].strftime('%H:%M:%S.%f')[:-3]
                message = event['message']
                
                # Highlight important messages
                if any(keyword in message.lower() for keyword in ['error', 'exception', 'traceback', 'failed']):
                    print(f"❌ {timestamp_str}: {message}")
                elif any(keyword in message.lower() for keyword in ['start', 'end', 'report']):
                    print(f"📊 {timestamp_str}: {message}")
                elif 'user info' in message.lower() or 'authorizer' in message.lower():
                    print(f"🔑 {timestamp_str}: {message}")
                else:
                    print(f"📋 {timestamp_str}: {message}")
            
            print("="*80)
            
            # Look for specific error patterns
            error_found = False
            for event in request_events:
                message = event['message']
                if 'traceback' in message.lower() or 'exception' in message.lower():
                    error_found = True
                    print(f"\n🚨 ERROR FOUND:")
                    print(message)
            
            if not error_found:
                print(f"\n✅ No explicit errors found in logs")
                print(f"ℹ️  This suggests the error happens during response serialization")
            
            return request_events
            
        else:
            print(f"❌ No log events found for request ID: {request_id}")
            print(f"ℹ️  This could mean:")
            print(f"   - The request ID is from a different time period")
            print(f"   - The request never reached Lambda")
            print(f"   - The logs have been rotated")
            return []
        
    except Exception as e:
        print(f"❌ Error searching logs: {e}")
        return []

def search_recent_500_errors():
    """Search for recent 500 errors in logs"""
    
    logs_client = boto3.client('logs', region_name='ap-south-1')
    log_group = '/aws/lambda/aquachain-function-readings-service-dev'
    
    print(f"\n🔍 Searching for recent 500 errors...")
    
    try:
        # Search in the last 2 hours
        end_time = int(time.time() * 1000)
        start_time = end_time - (2 * 60 * 60 * 1000)  # 2 hours ago
        
        # Search for error patterns
        error_patterns = [
            "ERROR",
            "Exception",
            "Traceback",
            "TypeError",
            "KeyError",
            "Decimal",
            "JSON"
        ]
        
        all_errors = []
        
        for pattern in error_patterns:
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                filterPattern=pattern,
                limit=20
            )
            
            events = response.get('events', [])
            all_errors.extend(events)
        
        if all_errors:
            # Remove duplicates and sort by timestamp
            unique_errors = {}
            for event in all_errors:
                unique_errors[event['eventId']] = event
            
            sorted_errors = sorted(unique_errors.values(), key=lambda x: x['timestamp'])
            
            print(f"✅ Found {len(sorted_errors)} recent error events:")
            
            for event in sorted_errors[-10:]:  # Show last 10 errors
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"❌ {timestamp.strftime('%H:%M:%S')}: {message}")
        else:
            print(f"✅ No recent error patterns found")
        
    except Exception as e:
        print(f"❌ Error searching for recent errors: {e}")

if __name__ == "__main__":
    print("🚀 Searching CloudWatch logs for Lambda errors...")
    
    # Search for specific request IDs from browser network trace
    request_ids = [
        "5644bfd9-4112-4841-b409-f6c553990dec",  # From your browser trace
        "2f4c9758-d831-4127-95e9-683c795ffd0e",  # Another from trace
        "871c5243-089e-4094-ac52-a40359c9c8ad"   # Another from trace
    ]
    
    found_any = False
    
    for request_id in request_ids:
        events = search_logs_for_request_id(request_id)
        if events:
            found_any = True
            break
        print()  # Add spacing between searches
    
    if not found_any:
        print(f"\n📋 No specific request IDs found. Searching for recent errors...")
        search_recent_500_errors()
    
    print(f"\n" + "="*80)
    print("NEXT STEPS:")
    print("1. If errors found above, fix the specific issue")
    print("2. If no errors found, the issue is likely response serialization")
    print("3. Check for hidden Decimal objects in nested data")
    print("4. Verify Lambda returns proper proxy response structure")
    print("="*80)