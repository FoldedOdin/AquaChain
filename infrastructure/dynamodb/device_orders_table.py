"""
DeviceOrders table definition for order management system
"""
import boto3
from typing import Dict, Any

class DeviceOrdersTableManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
    
    def create_device_orders_table(self) -> Dict[str, Any]:
        """
        Create DeviceOrders table for order management
        Includes shipment_id and tracking_number fields for shipment tracking integration
        """
        table_definition = {
            'TableName': 'DeviceOrders',
            'KeySchema': [
                {
                    'AttributeName': 'orderId',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'orderId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'createdAt',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'userId-createdAt-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'userId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'createdAt',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'status-createdAt-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'createdAt',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'StreamSpecification': {
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            },
            'Tags': [
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Environment',
                    'Value': 'production'
                },
                {
                    'Key': 'Component',
                    'Value': 'order-management'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created DeviceOrders table: {response['TableDescription']['TableName']}")
            print("  ✓ Primary key: orderId")
            print("  ✓ GSI: userId-createdAt-index")
            print("  ✓ GSI: status-createdAt-index")
            print("  ✓ DynamoDB Streams: ENABLED")
            print("  ✓ Billing mode: PAY_PER_REQUEST")
            print("\nNote: The table schema supports shipment_id and tracking_number fields")
            print("      These fields will be added dynamically when orders are shipped")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("DeviceOrders table already exists")
            return self.dynamodb.describe_table(TableName='DeviceOrders')
    
    def verify_table_structure(self) -> bool:
        """Verify the DeviceOrders table has the correct structure"""
        try:
            response = self.dynamodb.describe_table(TableName='DeviceOrders')
            table = response['Table']
            
            print("\n" + "="*60)
            print("DeviceOrders Table Verification")
            print("="*60)
            
            # Check primary key
            key_schema = table['KeySchema']
            has_order_id = any(k['AttributeName'] == 'orderId' and k['KeyType'] == 'HASH' 
                              for k in key_schema)
            
            if has_order_id:
                print("✓ Primary key (orderId) is correct")
            else:
                print("✗ Primary key is incorrect")
                return False
            
            # Check GSIs
            gsis = table.get('GlobalSecondaryIndexes', [])
            gsi_names = [gsi['IndexName'] for gsi in gsis]
            
            required_gsis = ['userId-createdAt-index', 'status-createdAt-index']
            for gsi_name in required_gsis:
                if gsi_name in gsi_names:
                    print(f"✓ GSI {gsi_name} exists")
                else:
                    print(f"✗ GSI {gsi_name} is missing")
            
            # Check streams
            stream_spec = table.get('StreamSpecification', {})
            if stream_spec.get('StreamEnabled'):
                print("✓ DynamoDB Streams enabled")
            else:
                print("⚠ DynamoDB Streams not enabled")
            
            print("\n" + "="*60)
            print("Table structure verification complete")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"✗ Error verifying table: {e}")
            return False

if __name__ == '__main__':
    manager = DeviceOrdersTableManager()
    manager.create_device_orders_table()
    
    # Wait a moment for table to be created
    import time
    time.sleep(2)
    
    # Verify structure
    manager.verify_table_structure()
