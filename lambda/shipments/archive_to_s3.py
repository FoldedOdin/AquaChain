"""
Lambda function to archive old shipment data to S3 for long-term storage

This function:
1. Queries shipments approaching TTL expiration (within 30 days)
2. Exports them to S3 in compressed JSON format
3. Maintains compliance with data retention regulations

Triggered by: CloudWatch Event Rule (daily)

Requirements: 15.5
"""
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import boto3
import json
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')
ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET', 'aquachain-shipment-archives')
ARCHIVE_PREFIX = os.environ.get('ARCHIVE_PREFIX', 'shipments/')


def handler(event, context):
    """
    Archive shipments approaching TTL expiration to S3
    
    Output:
    {
      "success": true,
      "archived_count": 42,
      "s3_key": "shipments/2025/01/archive-2025-01-01.json.gz"
    }
    """
    try:
        print("Starting shipment archival process")
        
        # Get shipments approaching expiration (within 30 days)
        shipments_to_archive = get_expiring_shipments(days_until_expiration=30)
        
        if not shipments_to_archive:
            print("No shipments to archive")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'archived_count': 0,
                    'message': 'No shipments to archive'
                })
            }
        
        print(f"Found {len(shipments_to_archive)} shipments to archive")
        
        # Archive to S3
        s3_key = archive_shipments_to_s3(shipments_to_archive)
        
        print(f"Successfully archived {len(shipments_to_archive)} shipments to {s3_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'archived_count': len(shipments_to_archive),
                's3_key': s3_key
            })
        }
        
    except Exception as e:
        print(f"ERROR: Archival failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


def get_expiring_shipments(days_until_expiration: int = 30) -> List[Dict]:
    """
    Query shipments that will expire within specified days
    
    Args:
        days_until_expiration: Number of days until TTL expiration
        
    Returns:
        List of shipment records
    """
    try:
        shipments_table = dynamodb.Table(SHIPMENTS_TABLE)
        
        # Calculate expiration threshold
        threshold_date = datetime.utcnow() + timedelta(days=days_until_expiration)
        threshold_timestamp = int(threshold_date.timestamp())
        
        print(f"Querying shipments with audit_ttl < {threshold_timestamp}")
        
        # Scan table for shipments approaching expiration
        # Note: In production, consider using a GSI on audit_ttl for better performance
        response = shipments_table.scan(
            FilterExpression='audit_ttl < :threshold AND attribute_exists(audit_ttl)',
            ExpressionAttributeValues={
                ':threshold': threshold_timestamp
            }
        )
        
        shipments = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = shipments_table.scan(
                FilterExpression='audit_ttl < :threshold AND attribute_exists(audit_ttl)',
                ExpressionAttributeValues={
                    ':threshold': threshold_timestamp
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            shipments.extend(response.get('Items', []))
        
        print(f"Found {len(shipments)} shipments approaching expiration")
        return shipments
        
    except Exception as e:
        print(f"ERROR: Failed to query expiring shipments: {str(e)}")
        raise


def archive_shipments_to_s3(shipments: List[Dict]) -> str:
    """
    Archive shipments to S3 in compressed JSON format
    
    Args:
        shipments: List of shipment records
        
    Returns:
        S3 key where data was archived
    """
    try:
        # Generate S3 key with date partitioning
        now = datetime.utcnow()
        s3_key = f"{ARCHIVE_PREFIX}{now.year}/{now.month:02d}/archive-{now.strftime('%Y-%m-%d-%H%M%S')}.json.gz"
        
        # Prepare archive data
        archive_data = {
            'archived_at': now.isoformat() + 'Z',
            'shipment_count': len(shipments),
            'shipments': shipments
        }
        
        # Convert to JSON
        json_data = json.dumps(archive_data, default=str, indent=2)
        
        # Compress with gzip
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        print(f"Uploading {len(compressed_data)} bytes to s3://{ARCHIVE_BUCKET}/{s3_key}")
        
        # Upload to S3
        s3.put_object(
            Bucket=ARCHIVE_BUCKET,
            Key=s3_key,
            Body=compressed_data,
            ContentType='application/json',
            ContentEncoding='gzip',
            Metadata={
                'archived_at': now.isoformat(),
                'shipment_count': str(len(shipments)),
                'original_size_bytes': str(len(json_data)),
                'compressed_size_bytes': str(len(compressed_data))
            },
            StorageClass='GLACIER_IR'  # Use Glacier Instant Retrieval for cost savings
        )
        
        print(f"Successfully uploaded archive to S3")
        print(f"  Original size: {len(json_data)} bytes")
        print(f"  Compressed size: {len(compressed_data)} bytes")
        print(f"  Compression ratio: {len(compressed_data) / len(json_data) * 100:.1f}%")
        
        return s3_key
        
    except Exception as e:
        print(f"ERROR: Failed to archive to S3: {str(e)}")
        raise


def restore_from_archive(s3_key: str) -> List[Dict]:
    """
    Restore shipments from S3 archive (utility function)
    
    Args:
        s3_key: S3 key of the archive file
        
    Returns:
        List of shipment records
    """
    try:
        print(f"Restoring archive from s3://{ARCHIVE_BUCKET}/{s3_key}")
        
        # Download from S3
        response = s3.get_object(
            Bucket=ARCHIVE_BUCKET,
            Key=s3_key
        )
        
        # Decompress
        compressed_data = response['Body'].read()
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        
        # Parse JSON
        archive_data = json.loads(json_data)
        
        shipments = archive_data.get('shipments', [])
        print(f"Restored {len(shipments)} shipments from archive")
        
        return shipments
        
    except Exception as e:
        print(f"ERROR: Failed to restore from archive: {str(e)}")
        raise
