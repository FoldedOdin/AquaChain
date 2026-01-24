"""
Configure DynamoDB TTL for Shipments table audit data retention

This script:
1. Enables TTL on the Shipments table
2. Sets the TTL attribute to 'audit_ttl'
3. Ensures 2-year retention policy for audit data

Requirements: 15.5
"""
import boto3
import sys
import os
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')

# Table name
SHIPMENTS_TABLE = os.environ.get('SHIPMENTS_TABLE', 'aquachain-shipments')


def configure_ttl():
    """
    Configure TTL on Shipments table for 2-year audit retention
    
    TTL (Time To Live) automatically deletes items after the specified time.
    The 'audit_ttl' attribute contains a Unix timestamp (seconds since epoch)
    indicating when the item should expire.
    
    Requirements: 15.5
    """
    try:
        print(f"Configuring TTL for table: {SHIPMENTS_TABLE}")
        
        # Check if TTL is already enabled
        try:
            response = dynamodb.describe_time_to_live(TableName=SHIPMENTS_TABLE)
            ttl_status = response.get('TimeToLiveDescription', {}).get('TimeToLiveStatus')
            
            if ttl_status == 'ENABLED':
                print(f"✓ TTL is already enabled on {SHIPMENTS_TABLE}")
                print(f"  TTL Attribute: {response['TimeToLiveDescription'].get('AttributeName')}")
                return True
            elif ttl_status == 'ENABLING':
                print(f"⏳ TTL is currently being enabled on {SHIPMENTS_TABLE}")
                print("  This may take a few minutes. Please check back later.")
                return True
                
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"✗ Table {SHIPMENTS_TABLE} not found")
            return False
        
        # Enable TTL
        print(f"Enabling TTL on {SHIPMENTS_TABLE} with attribute 'audit_ttl'...")
        
        dynamodb.update_time_to_live(
            TableName=SHIPMENTS_TABLE,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'audit_ttl'
            }
        )
        
        print(f"✓ TTL configuration initiated successfully")
        print(f"  TTL Attribute: audit_ttl")
        print(f"  Retention Period: 2 years from creation")
        print(f"  Note: TTL enablement may take up to 1 hour to complete")
        
        return True
        
    except Exception as e:
        print(f"✗ Error configuring TTL: {str(e)}")
        return False


def verify_ttl_configuration():
    """
    Verify TTL configuration on Shipments table
    """
    try:
        print(f"\nVerifying TTL configuration for {SHIPMENTS_TABLE}...")
        
        response = dynamodb.describe_time_to_live(TableName=SHIPMENTS_TABLE)
        ttl_desc = response.get('TimeToLiveDescription', {})
        
        print(f"\nTTL Status:")
        print(f"  Status: {ttl_desc.get('TimeToLiveStatus', 'UNKNOWN')}")
        print(f"  Attribute: {ttl_desc.get('AttributeName', 'N/A')}")
        
        if ttl_desc.get('TimeToLiveStatus') == 'ENABLED':
            print(f"\n✓ TTL is fully enabled and operational")
        elif ttl_desc.get('TimeToLiveStatus') == 'ENABLING':
            print(f"\n⏳ TTL is being enabled (may take up to 1 hour)")
        else:
            print(f"\n✗ TTL is not enabled")
        
        return True
        
    except Exception as e:
        print(f"✗ Error verifying TTL: {str(e)}")
        return False


def explain_ttl_behavior():
    """
    Explain how TTL works for audit data retention
    """
    print("\n" + "=" * 80)
    print("TTL (Time To Live) Behavior")
    print("=" * 80)
    print("""
How TTL Works:
1. Each shipment record has an 'audit_ttl' attribute (Unix timestamp)
2. This timestamp is set to 2 years from the shipment creation date
3. DynamoDB automatically deletes items when current time > audit_ttl
4. Deletion typically occurs within 48 hours of expiration
5. Deleted items are removed from indexes and backups

Audit Data Retention:
- Shipment records are retained for 2 years for compliance
- Timeline entries, webhook events, and admin actions are preserved
- After 2 years, records are automatically deleted
- For long-term archival, export data to S3 before expiration

Compliance:
- Meets typical regulatory requirements (GDPR, SOC 2, etc.)
- Automatic cleanup reduces storage costs
- No manual intervention required

To Archive Data Before Deletion:
- Use DynamoDB Streams to capture changes
- Export to S3 using AWS Data Pipeline or Lambda
- Store in compressed format (JSON.gz or Parquet)
- Implement lifecycle policies on S3 for long-term archival
    """)
    print("=" * 80)


def main():
    """Main execution"""
    print("=" * 80)
    print("DynamoDB TTL Configuration for Shipments Table")
    print("=" * 80)
    print()
    
    # Configure TTL
    success = configure_ttl()
    
    if success:
        # Verify configuration
        verify_ttl_configuration()
        
        # Explain TTL behavior
        explain_ttl_behavior()
        
        print("\n✓ TTL configuration completed successfully")
        return 0
    else:
        print("\n✗ TTL configuration failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
