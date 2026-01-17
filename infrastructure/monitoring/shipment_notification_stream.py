"""
Configure DynamoDB Stream for Shipments table to trigger notification Lambda

This script:
1. Enables DynamoDB Streams on Shipments table
2. Creates event source mapping to notification_handler Lambda
3. Configures stream settings (batch size, starting position)

Requirements: 1.5, 4.1, 13.1, 13.2, 13.3, 13.4
"""
import boto3
import json
import os
from datetime import datetime

dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
NOTIFICATION_LAMBDA_ARN = os.environ.get('NOTIFICATION_LAMBDA_ARN', '')


def enable_dynamodb_stream():
    """
    Enable DynamoDB Streams on Shipments table
    
    Stream view type: NEW_AND_OLD_IMAGES
    - Allows detection of status changes by comparing old and new images
    """
    try:
        print(f"Enabling DynamoDB Stream on {SHIPMENTS_TABLE}...")
        
        response = dynamodb.update_table(
            TableName=SHIPMENTS_TABLE,
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            }
        )
        
        stream_arn = response['TableDescription']['LatestStreamArn']
        print(f"✓ DynamoDB Stream enabled: {stream_arn}")
        
        return stream_arn
        
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"✗ Table {SHIPMENTS_TABLE} not found")
        return None
    except Exception as e:
        print(f"✗ Error enabling stream: {str(e)}")
        return None


def create_event_source_mapping(stream_arn: str, lambda_arn: str):
    """
    Create event source mapping from DynamoDB Stream to Lambda
    
    Configuration:
    - Batch size: 10 records
    - Starting position: LATEST (only new records)
    - Maximum retry attempts: 3
    - Bisect batch on error: True (for better error isolation)
    """
    try:
        print(f"Creating event source mapping...")
        
        # Check if mapping already exists
        existing_mappings = lambda_client.list_event_source_mappings(
            EventSourceArn=stream_arn,
            FunctionName=lambda_arn
        )
        
        if existing_mappings['EventSourceMappings']:
            print("✓ Event source mapping already exists")
            return existing_mappings['EventSourceMappings'][0]['UUID']
        
        # Create new mapping
        response = lambda_client.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName=lambda_arn,
            Enabled=True,
            BatchSize=10,
            StartingPosition='LATEST',
            MaximumRetryAttempts=3,
            BisectBatchOnFunctionError=True,
            MaximumRecordAgeInSeconds=86400,  # 24 hours
            ParallelizationFactor=1
        )
        
        mapping_uuid = response['UUID']
        print(f"✓ Event source mapping created: {mapping_uuid}")
        
        return mapping_uuid
        
    except Exception as e:
        print(f"✗ Error creating event source mapping: {str(e)}")
        return None


def verify_lambda_permissions(lambda_arn: str):
    """
    Verify Lambda has permissions to read from DynamoDB Stream
    
    Required permissions:
    - dynamodb:GetRecords
    - dynamodb:GetShardIterator
    - dynamodb:DescribeStream
    - dynamodb:ListStreams
    """
    try:
        print("Verifying Lambda permissions...")
        
        # Get Lambda function configuration
        response = lambda_client.get_function(FunctionName=lambda_arn)
        role_arn = response['Configuration']['Role']
        
        print(f"✓ Lambda execution role: {role_arn}")
        print("  Ensure role has DynamoDB Stream read permissions")
        
        return True
        
    except Exception as e:
        print(f"✗ Error verifying permissions: {str(e)}")
        return False


def main():
    """
    Main setup function
    """
    print("=" * 60)
    print("Shipment Notification DynamoDB Stream Setup")
    print("=" * 60)
    print()
    
    # Check environment variables
    if not NOTIFICATION_LAMBDA_ARN:
        print("✗ NOTIFICATION_LAMBDA_ARN environment variable not set")
        print("  Set it to the ARN of the notification_handler Lambda function")
        return
    
    # Step 1: Enable DynamoDB Stream
    stream_arn = enable_dynamodb_stream()
    if not stream_arn:
        print("\n✗ Failed to enable DynamoDB Stream")
        return
    
    print()
    
    # Step 2: Verify Lambda permissions
    verify_lambda_permissions(NOTIFICATION_LAMBDA_ARN)
    print()
    
    # Step 3: Create event source mapping
    mapping_uuid = create_event_source_mapping(stream_arn, NOTIFICATION_LAMBDA_ARN)
    if not mapping_uuid:
        print("\n✗ Failed to create event source mapping")
        return
    
    print()
    print("=" * 60)
    print("✓ Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test the notification system by creating a shipment")
    print("2. Monitor CloudWatch Logs for notification_handler Lambda")
    print("3. Verify emails, SMS, and WebSocket notifications are sent")
    print()


if __name__ == '__main__':
    main()
