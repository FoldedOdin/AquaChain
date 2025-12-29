"""
Shipments table definition for courier tracking subsystem
"""
import boto3
from typing import Dict, Any

class ShipmentsTableManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
    
    def create_shipments_table(self) -> Dict[str, Any]:
        """
        Create shipments table for automated courier tracking
        """
        table_definition = {
            'TableName': 'aquachain-shipments',
            'KeySchema': [
                {
                    'AttributeName': 'shipment_id',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'shipment_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'order_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'tracking_number',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'internal_status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'order_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'order_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'tracking_number-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'tracking_number',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'status-created_at-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'internal_status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
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
                    'Value': 'shipment-tracking'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created shipments table: {response['TableDescription']['TableName']}")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Shipments table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-shipments')

if __name__ == '__main__':
    manager = ShipmentsTableManager()
    manager.create_shipments_table()
