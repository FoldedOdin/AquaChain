#!/usr/bin/env python3
"""
Monitor SageMaker endpoint deployment status
"""

import boto3
import time
import sys
from datetime import datetime

def monitor_endpoint(endpoint_name, region='ap-south-1', max_wait_minutes=20):
    """Monitor endpoint deployment status"""
    sagemaker = boto3.client('sagemaker', region_name=region)
    
    print(f"Monitoring endpoint: {endpoint_name}")
    print(f"Max wait time: {max_wait_minutes} minutes")
    print("-" * 50)
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']
            creation_time = response['CreationTime']
            
            elapsed_minutes = (time.time() - start_time) / 60
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status} (elapsed: {elapsed_minutes:.1f}m)")
            
            if status == 'InService':
                print(f"✅ Endpoint {endpoint_name} is now InService!")
                return True
            elif status in ['Failed', 'RollingBack']:
                print(f"❌ Endpoint deployment failed with status: {status}")
                if 'FailureReason' in response:
                    print(f"Failure reason: {response['FailureReason']}")
                return False
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Error checking endpoint: {str(e)}")
            time.sleep(30)
    
    print(f"❌ Timeout after {max_wait_minutes} minutes")
    return False

if __name__ == "__main__":
    endpoint_name = sys.argv[1] if len(sys.argv) > 1 else "aquachain-wqi-working-dev"
    success = monitor_endpoint(endpoint_name)
    sys.exit(0 if success else 1)