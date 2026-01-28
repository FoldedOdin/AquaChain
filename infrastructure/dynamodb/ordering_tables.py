"""
DynamoDB table definitions for Enhanced Consumer Ordering System
Implements orders, payments, technicians, and simulations tables with appropriate GSIs
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

class OrderingSystemTableManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
    
    def create_orders_table(self) -> Dict[str, Any]:
        """
        Create orders table with GSIs for consumer and status queries
        Partition Key: ORDER#{orderId}
        Sort Key: ORDER#{orderId}
        """
        table_definition = {
            'TableName': 'aquachain-orders',
            'KeySchema': [
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key: ORDER#{orderId}
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key: ORDER#{orderId}
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1SK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI2PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI2SK',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {
                            'AttributeName': 'GSI1PK',
                            'KeyType': 'HASH'  # CONSUMER#{consumerId}
                        },
                        {
                            'AttributeName': 'GSI1SK',
                            'KeyType': 'RANGE'  # ORDER#{createdAt}#{orderId}
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'GSI2',
                    'KeySchema': [
                        {
                            'AttributeName': 'GSI2PK',
                            'KeyType': 'HASH'  # STATUS#{status}
                        },
                        {
                            'AttributeName': 'GSI2SK',
                            'KeyType': 'RANGE'  # {createdAt}#{orderId}
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
                    'Key': 'Feature',
                    'Value': 'enhanced-consumer-ordering-system'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created orders table: {response['TableDescription']['TableName']}")
            
            # Enable TTL for demo orders (optional cleanup after 30 days)
            self._enable_ttl('aquachain-orders', 'ttl')
            
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Orders table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-orders')
    
    def create_payments_table(self) -> Dict[str, Any]:
        """
        Create payments table with GSI for order payments lookup
        Partition Key: PAYMENT#{paymentId}
        Sort Key: PAYMENT#{paymentId}
        """
        table_definition = {
            'TableName': 'aquachain-payments',
            'KeySchema': [
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key: PAYMENT#{paymentId}
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key: PAYMENT#{paymentId}
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1SK',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {
                            'AttributeName': 'GSI1PK',
                            'KeyType': 'HASH'  # ORDER#{orderId}
                        },
                        {
                            'AttributeName': 'GSI1SK',
                            'KeyType': 'RANGE'  # PAYMENT#{createdAt}
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
                    'Key': 'Feature',
                    'Value': 'enhanced-consumer-ordering-system'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created payments table: {response['TableDescription']['TableName']}")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Payments table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-payments')
    
    def create_technicians_table(self) -> Dict[str, Any]:
        """
        Create technicians table with GSI for location-based queries
        Partition Key: TECHNICIAN#{technicianId}
        Sort Key: TECHNICIAN#{technicianId}
        """
        table_definition = {
            'TableName': 'aquachain-technicians',
            'KeySchema': [
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key: TECHNICIAN#{technicianId}
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key: TECHNICIAN#{technicianId}
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1SK',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {
                            'AttributeName': 'GSI1PK',
                            'KeyType': 'HASH'  # LOCATION#{city}#{state}
                        },
                        {
                            'AttributeName': 'GSI1SK',
                            'KeyType': 'RANGE'  # AVAILABLE#{available}#{technicianId}
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
                    'Key': 'Feature',
                    'Value': 'enhanced-consumer-ordering-system'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created technicians table: {response['TableDescription']['TableName']}")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Technicians table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-technicians')
    
    def create_order_simulations_table(self) -> Dict[str, Any]:
        """
        Create order status simulation table for demo purposes
        Partition Key: SIMULATION#{orderId}
        Sort Key: SIMULATION#{orderId}
        """
        table_definition = {
            'TableName': 'aquachain-order-simulations',
            'KeySchema': [
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key: SIMULATION#{orderId}
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key: SIMULATION#{orderId}
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
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
                    'Key': 'Feature',
                    'Value': 'enhanced-consumer-ordering-system'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'demo-simulation'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created order simulations table: {response['TableDescription']['TableName']}")
            
            # Enable TTL for automatic cleanup of simulation records
            self._enable_ttl('aquachain-order-simulations', 'ttl')
            
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Order simulations table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-order-simulations')
    
    def _enable_ttl(self, table_name: str, ttl_attribute: str):
        """Enable TTL on a table"""
        try:
            self.dynamodb.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': ttl_attribute
                }
            )
            print(f"Enabled TTL on {table_name} with attribute {ttl_attribute}")
        except Exception as e:
            print(f"TTL already enabled or error: {e}")
    
    def create_all_ordering_tables(self):
        """Create all DynamoDB tables for Enhanced Consumer Ordering System"""
        print("Creating DynamoDB tables for Enhanced Consumer Ordering System...")
        
        tables = [
            self.create_orders_table,
            self.create_payments_table,
            self.create_technicians_table,
            self.create_order_simulations_table
        ]
        
        for create_table_func in tables:
            try:
                create_table_func()
            except Exception as e:
                print(f"Error creating table: {e}")
        
        print("Enhanced Consumer Ordering System table creation completed")

def calculate_ttl_timestamp(days: int = 30) -> int:
    """
    Calculate TTL timestamp for DynamoDB items
    Default: 30 days from now for demo orders
    """
    expiry_date = datetime.now() + timedelta(days=days)
    return int(expiry_date.timestamp())

if __name__ == "__main__":
    # Example usage
    manager = OrderingSystemTableManager()
    manager.create_all_ordering_tables()