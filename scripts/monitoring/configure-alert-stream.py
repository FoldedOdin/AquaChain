#!/usr/bin/env python3
"""
Configure DynamoDB Stream and Lambda trigger for Alert Detection
Enables stream on AquaChain-Readings table and connects to alert Lambda
"""

import boto3
import sys
import time

def configure_alert_stream(environment='dev'):
    """Configure DynamoDB Stream and Lambda trigger"""
    
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    table_name = 'AquaChain-Readings'
    function_name = f'aquachain-function-alert-detection-{environment}'
    
    print(f"Configuring Alert Detection Stream for {environment}")
    print("=" * 60)
    
    # Step 1: Enable DynamoDB Stream
    print(f"\n1. Enabling DynamoDB Stream on {table_name}...")
    try:
        # First check if stream is already enabled
        table_info = dynamodb.describe_table(TableName=table_name)
        stream_spec = table_info['Table'].get('StreamSpecification', {})
        
        if stream_spec.get('StreamEnabled'):
            print(f"✓ Stream already enabled on {table_name}")
            print(f"  Stream View Type: {stream_spec.get('StreamViewType')}")
        else:
            response = dynamodb.update_table(
                TableName=table_name,
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            print(f"✓ Stream enabled on {table_name}")
            print(f"  Stream View Type: NEW_AND_OLD_IMAGES")
            
            # Wait for stream to be active
            print("  Waiting for stream to become active...")
            time.sleep(5)
        
    except Exception as e:
        print(f"✗ Error with stream configuration: {e}")
        return False
    
    # Step 2: Get Stream ARN
    print(f"\n2. Getting Stream ARN...")
    try:
        table_info = dynamodb.describe_table(TableName=table_name)
        stream_arn = table_info['Table'].get('LatestStreamArn')
        
        if not stream_arn:
            print("✗ Stream ARN not found. Stream may not be fully enabled yet.")
            print("  Wait a few seconds and try again.")
            return False
        
        print(f"✓ Stream ARN: {stream_arn}")
        
    except Exception as e:
        print(f"✗ Error getting stream ARN: {e}")
        return False
    
    # Step 3: Create Event Source Mapping
    print(f"\n3. Creating Lambda event source mapping...")
    try:
        # Check if mapping already exists
        existing_mappings = lambda_client.list_event_source_mappings(
            FunctionName=function_name
        )
        
        if existing_mappings['EventSourceMappings']:
            print(f"✓ Event source mapping already exists")
            for mapping in existing_mappings['EventSourceMappings']:
                print(f"  UUID: {mapping['UUID']}")
                print(f"  State: {mapping['State']}")
                print(f"  Batch Size: {mapping['BatchSize']}")
        else:
            # Create new mapping
            mapping_response = lambda_client.create_event_source_mapping(
                EventSourceArn=stream_arn,
                FunctionName=function_name,
                Enabled=True,
                BatchSize=10,  # Process up to 10 records at a time
                StartingPosition='LATEST',  # Start from latest records
                MaximumBatchingWindowInSeconds=5,  # Wait up to 5 seconds to batch records
                MaximumRecordAgeInSeconds=3600,  # Discard records older than 1 hour
                MaximumRetryAttempts=3,  # Retry failed batches 3 times
                ParallelizationFactor=1  # Process one shard at a time
            )
            
            print(f"✓ Event source mapping created")
            print(f"  UUID: {mapping_response['UUID']}")
            print(f"  State: {mapping_response['State']}")
            print(f"  Batch Size: {mapping_response['BatchSize']}")
    
    except lambda_client.exceptions.ResourceConflictException:
        print(f"✓ Event source mapping already exists")
    except Exception as e:
        print(f"✗ Error creating event source mapping: {e}")
        return False
    
    # Step 4: Verify Configuration
    print(f"\n4. Verifying configuration...")
    try:
        # Check Lambda function
        function_info = lambda_client.get_function(FunctionName=function_name)
        print(f"✓ Lambda function: {function_name}")
        print(f"  Status: {function_info['Configuration']['State']}")
        
        # Check event source mappings
        mappings = lambda_client.list_event_source_mappings(FunctionName=function_name)
        active_mappings = [m for m in mappings['EventSourceMappings'] if m['State'] in ['Enabled', 'Enabling']]
        
        print(f"✓ Active event source mappings: {len(active_mappings)}")
        
    except Exception as e:
        print(f"⚠ Warning during verification: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Alert Detection Stream Configuration Complete!")
    print("\nThe alert system will now:")
    print("  1. Monitor all new readings in AquaChain-Readings table")
    print("  2. Detect threshold violations automatically")
    print("  3. Generate alerts for critical/warning conditions")
    print("  4. Send notifications via SNS")
    print("  5. Escalate sustained critical issues")
    
    print("\nNext Steps:")
    print("  1. Insert a test reading with critical values")
    print("  2. Check CloudWatch logs for alert processing")
    print("  3. Verify alert appears in aquachain-alerts table")
    print("  4. Configure SNS subscriptions for notifications")
    
    return True

if __name__ == '__main__':
    environment = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    
    success = configure_alert_stream(environment)
    
    if not success:
        print("\n✗ Configuration failed")
        sys.exit(1)
    
    print("\n✓ Configuration successful")
