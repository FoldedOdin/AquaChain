"""
Create AquaChain-ConfigHistory DynamoDB Table
This table stores version history for system configuration changes
"""

import boto3
import sys

def create_config_history_table():
    """
    Create the ConfigHistory table with proper schema
    """
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    table_name = 'AquaChain-ConfigHistory'
    
    try:
        # Check if table already exists
        try:
            dynamodb.describe_table(TableName=table_name)
            print(f"✅ Table {table_name} already exists")
            return True
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"Creating table {table_name}...")
        
        # Create table
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'configId',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'version',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'configId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'version',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'updatedBy',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'updatedBy-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'updatedBy',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'version',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand pricing
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
                    'Value': 'ConfigurationVersioning'
                }
            ]
        )
        
        print(f"✅ Table {table_name} created successfully")
        print(f"   Status: {response['TableDescription']['TableStatus']}")
        print(f"   ARN: {response['TableDescription']['TableArn']}")
        
        # Wait for table to be active
        print("Waiting for table to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"✅ Table {table_name} is now active and ready to use")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("AquaChain ConfigHistory Table Creation")
    print("=" * 60)
    print()
    
    success = create_config_history_table()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Deployment completed successfully")
        sys.exit(0)
    else:
        print("❌ Deployment failed")
        sys.exit(1)
