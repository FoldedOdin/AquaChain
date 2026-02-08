#!/usr/bin/env python3
"""
Trigger Auto-Progress for Demo Orders

This script manually triggers the auto-progression Lambda function
to progress demo orders through their stages.

Usage:
    python scripts/testing/trigger-auto-progress.py
"""

import sys
import os
import json

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders'))

from auto_progress_demo_orders import lambda_handler

def main():
    """Main function to trigger auto-progression"""
    print("🚀 Triggering auto-progression for demo orders...")
    print("=" * 60)
    
    # Simulate Lambda event
    event = {
        'source': 'manual-trigger',
        'detail-type': 'Manual Invocation'
    }
    
    # Simulate Lambda context
    class Context:
        function_name = 'auto-progress-demo-orders'
        memory_limit_in_mb = 128
        invoked_function_arn = 'arn:aws:lambda:local:000000000000:function:auto-progress-demo-orders'
        aws_request_id = 'local-test-request-id'
    
    context = Context()
    
    try:
        # Invoke the Lambda handler
        response = lambda_handler(event, context)
        
        print("\n✅ Auto-progression completed!")
        print("=" * 60)
        print(f"Status Code: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            if body.get('ordersProcessed', 0) > 0:
                print(f"\n🎉 Successfully progressed {body['ordersProcessed']} order(s)!")
            else:
                print("\nℹ️  No orders were ready to progress at this time.")
                print("   Orders progress automatically every 10 seconds after status change.")
        
    except Exception as e:
        print(f"\n❌ Error triggering auto-progression: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
