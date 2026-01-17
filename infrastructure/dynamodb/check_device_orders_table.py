"""
Check if DeviceOrders table exists and show its structure
"""
import boto3
import json
from botocore.exceptions import ClientError

def check_device_orders_table():
    """Check if DeviceOrders table exists"""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    try:
        # Try to describe the table
        response = dynamodb.describe_table(TableName='DeviceOrders')
        table = response['Table']
        
        print("✓ DeviceOrders table exists")
        print(f"  Table Name: {table['TableName']}")
        print(f"  Table Status: {table['TableStatus']}")
        
        # Show key schema
        print(f"\n  Primary Key:")
        for key in table['KeySchema']:
            print(f"    - {key['AttributeName']} ({key['KeyType']})")
        
        # Show attributes
        print(f"\n  Attribute Definitions:")
        for attr in table['AttributeDefinitions']:
            print(f"    - {attr['AttributeName']} ({attr['AttributeType']})")
        
        # Show GSIs if any
        gsis = table.get('GlobalSecondaryIndexes', [])
        if gsis:
            print(f"\n  Global Secondary Indexes ({len(gsis)}):")
            for gsi in gsis:
                print(f"    - {gsi['IndexName']}")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("✗ DeviceOrders table does not exist")
            print("\n  The table needs to be created.")
            print("  This table is used by the order management system.")
            return False
        else:
            print(f"✗ Error checking table: {e}")
            return False

if __name__ == '__main__':
    check_device_orders_table()
