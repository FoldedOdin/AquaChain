#!/usr/bin/env python3
"""
Create DynamoDB alerts table for AquaChain alert system
"""

import boto3
import sys

# Configuration
TABLE_NAME = 'aquachain-alerts'
REGION = 'ap-south-1'

def create_alerts_table():
    """Create alerts table with proper schema"""
    print(f"🔧 Creating DynamoDB table: {TABLE_NAME}")
    
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        
        # Create table
        response = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'alertId',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'alertId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'deviceId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'createdAt',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DeviceAlerts',
                    'KeySchema': [
                        {
                            'AttributeName': 'deviceId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'createdAt',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            StreamSpecification={
                'StreamEnabled': False
            },
            Tags=[
                {'Key': 'Project', 'Value': 'AquaChain'},
                {'Key': 'Environment', 'Value': 'dev'},
                {'Key': 'Service', 'Value': 'alert-system'}
            ]
        )
        
        print(f"✅ Table creation initiated")
        print(f"   Table ARN: {response['TableDescription']['TableArn']}")
        print(f"   Status: {response['TableDescription']['TableStatus']}")
        
        # Wait for table to be active
        print("\n⏳ Waiting for table to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        
        print(f"✅ Table {TABLE_NAME} is now active!")
        
        # Enable TTL
        print("\n🔧 Enabling TTL for automatic alert cleanup...")
        dynamodb.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        print("✅ TTL enabled on 'ttl' attribute")
        
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Table {TABLE_NAME} already exists")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def verify_table():
    """Verify table configuration"""
    print(f"\n🔍 Verifying table configuration...")
    
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        
        response = dynamodb.describe_table(TableName=TABLE_NAME)
        table = response['Table']
        
        print(f"✅ Table verified:")
        print(f"   Name: {table['TableName']}")
        print(f"   Status: {table['TableStatus']}")
        print(f"   Item Count: {table['ItemCount']}")
        print(f"   Size: {table['TableSizeBytes']} bytes")
        print(f"   Read Capacity: {table['ProvisionedThroughput']['ReadCapacityUnits']}")
        print(f"   Write Capacity: {table['ProvisionedThroughput']['WriteCapacityUnits']}")
        
        # Check GSI
        if 'GlobalSecondaryIndexes' in table:
            print(f"\n   Global Secondary Indexes:")
            for gsi in table['GlobalSecondaryIndexes']:
                print(f"     - {gsi['IndexName']}: {gsi['IndexStatus']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("🚨 AquaChain Alerts Table Creation")
    print("=" * 60)
    
    # Create table
    if not create_alerts_table():
        print("\n❌ Table creation failed!")
        sys.exit(1)
    
    # Verify table
    if not verify_table():
        print("\n⚠️  Table created but verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Alerts Table Ready!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Test alert generation:")
    print("   python scripts/testing/test-alert-generation.py critical")
    print("\n2. Check alerts:")
    print(f"   aws dynamodb scan --table-name {TABLE_NAME} --region {REGION}")

if __name__ == '__main__':
    main()
