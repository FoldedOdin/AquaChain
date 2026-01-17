"""
Verify Shipments table creation and structure
"""
import boto3
import json
from botocore.exceptions import ClientError

def verify_shipments_table():
    """Verify the Shipments table exists and has correct structure"""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    try:
        # Describe the table
        response = dynamodb.describe_table(TableName='aquachain-shipments')
        table = response['Table']
        
        print("✓ Shipments table exists")
        print(f"  Table Name: {table['TableName']}")
        print(f"  Table Status: {table['TableStatus']}")
        print(f"  Billing Mode: {table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}")
        
        # Verify primary key
        key_schema = table['KeySchema']
        print(f"\n✓ Primary Key:")
        for key in key_schema:
            print(f"  - {key['AttributeName']} ({key['KeyType']})")
        
        # Verify GSIs
        gsis = table.get('GlobalSecondaryIndexes', [])
        print(f"\n✓ Global Secondary Indexes ({len(gsis)}):")
        for gsi in gsis:
            print(f"  - {gsi['IndexName']}")
            for key in gsi['KeySchema']:
                print(f"    {key['AttributeName']} ({key['KeyType']})")
        
        # Verify DynamoDB Streams
        stream_spec = table.get('StreamSpecification', {})
        if stream_spec.get('StreamEnabled'):
            print(f"\n✓ DynamoDB Streams: ENABLED")
            print(f"  Stream View Type: {stream_spec.get('StreamViewType')}")
        else:
            print(f"\n✗ DynamoDB Streams: DISABLED")
        
        # Verify attributes
        attributes = table['AttributeDefinitions']
        print(f"\n✓ Attribute Definitions ({len(attributes)}):")
        for attr in attributes:
            print(f"  - {attr['AttributeName']} ({attr['AttributeType']})")
        
        print("\n" + "="*60)
        print("Shipments table verification PASSED")
        print("="*60)
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("✗ Shipments table does not exist")
            print("  Run: python infrastructure/dynamodb/shipments_table.py")
        else:
            print(f"✗ Error verifying table: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    verify_shipments_table()
