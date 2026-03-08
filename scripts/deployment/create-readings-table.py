#!/usr/bin/env python3
"""
Create DynamoDB table for sensor readings
"""

import boto3
import time

def create_readings_table():
    """Create AquaChain-Readings table"""
    print("Creating AquaChain-Readings table...")
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    try:
        response = dynamodb.create_table(
            TableName='AquaChain-Readings',
            KeySchema=[
                {
                    'AttributeName': 'deviceId_month',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'deviceId_month',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'deviceId',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DeviceIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'deviceId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Environment',
                    'Value': 'dev'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'IoT sensor readings storage'
                }
            ]
        )
        
        print(f"✓ Table creation initiated")
        print(f"  Table ARN: {response['TableDescription']['TableArn']}")
        print(f"  Status: {response['TableDescription']['TableStatus']}")
        
        # Wait for table to be active
        print("\nWaiting for table to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(
            TableName='AquaChain-Readings',
            WaiterConfig={
                'Delay': 5,
                'MaxAttempts': 20
            }
        )
        
        print("✓ Table is now ACTIVE and ready to use!")
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print("✓ Table already exists")
        return True
    except Exception as e:
        print(f"✗ Failed to create table: {str(e)}")
        return False

def create_ledger_table():
    """Create aquachain-ledger table"""
    print("\nCreating aquachain-ledger table...")
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    try:
        response = dynamodb.create_table(
            TableName='aquachain-ledger',
            KeySchema=[
                {
                    'AttributeName': 'GLOBAL_SEQUENCE',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'sequenceNumber',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'GLOBAL_SEQUENCE',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sequenceNumber',
                    'AttributeType': 'N'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Environment',
                    'Value': 'dev'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'Immutable audit ledger'
                }
            ]
        )
        
        print(f"✓ Table creation initiated")
        print(f"  Table ARN: {response['TableDescription']['TableArn']}")
        print(f"  Status: {response['TableDescription']['TableStatus']}")
        
        # Wait for table to be active
        print("\nWaiting for table to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(
            TableName='aquachain-ledger',
            WaiterConfig={
                'Delay': 5,
                'MaxAttempts': 20
            }
        )
        
        print("✓ Table is now ACTIVE and ready to use!")
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print("✓ Table already exists")
        return True
    except Exception as e:
        print(f"✗ Failed to create table: {str(e)}")
        return False

def verify_tables():
    """Verify tables were created successfully"""
    print("\n" + "=" * 60)
    print("Verifying Tables")
    print("=" * 60)
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    tables = ['AquaChain-Readings', 'aquachain-ledger']
    
    for table_name in tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            table = response['Table']
            
            print(f"\n✓ {table_name}")
            print(f"  Status: {table['TableStatus']}")
            print(f"  Item Count: {table['ItemCount']}")
            print(f"  Size: {table['TableSizeBytes']} bytes")
            print(f"  ARN: {table['TableArn']}")
            
        except Exception as e:
            print(f"\n✗ {table_name}: {str(e)}")

def main():
    """Main function"""
    print("=" * 60)
    print("Creating DynamoDB Tables for AquaChain")
    print("=" * 60)
    print()
    
    # Create readings table
    if not create_readings_table():
        return 1
    
    # Create ledger table
    if not create_ledger_table():
        return 1
    
    # Verify tables
    verify_tables()
    
    print("\n" + "=" * 60)
    print("Table Creation Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Configure IoT Rule to trigger Lambda function")
    print("2. Test ESP32 device data flow")
    print("3. Verify data is being stored in AquaChain-Readings table")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())
