"""
DynamoDB table definitions for AquaChain system
Implements time-windowed partitions, global sequence management, and TTL policies
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class DynamoDBTableManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
    
    def create_readings_table(self) -> Dict[str, Any]:
        """
        Create readings table with time-windowed partition keys
        Partition Key: deviceId#YYYYMM (for time-based partitioning)
        Sort Key: timestamp (ISO 8601)
        """
        table_definition = {
            'TableName': 'aquachain-readings',
            'KeySchema': [
                {
                    'AttributeName': 'deviceId_month',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            'AttributeDefinitions': [
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
            'GlobalSecondaryIndexes': [
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
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created readings table: {response['TableDescription']['TableName']}")
            
            # Enable TTL for data lifecycle management (90 days)
            self._enable_ttl('aquachain-readings', 'ttl')
            
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Readings table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-readings')
    
    def create_ledger_table(self) -> Dict[str, Any]:
        """
        Create ledger table for immutable record keeping
        Partition Key: GLOBAL_SEQUENCE (fixed value for global ordering)
        Sort Key: sequenceNumber (auto-incrementing)
        """
        table_definition = {
            'TableName': 'aquachain-ledger',
            'KeySchema': [
                {
                    'AttributeName': 'partition_key',
                    'KeyType': 'HASH'  # Fixed value: GLOBAL_SEQUENCE
                },
                {
                    'AttributeName': 'sequenceNumber',
                    'KeyType': 'RANGE'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'partition_key',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sequenceNumber',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'deviceId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'DeviceLedgerIndex',
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
                    'Key': 'DataClassification',
                    'Value': 'immutable-ledger'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created ledger table: {response['TableDescription']['TableName']}")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Ledger table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-ledger')
    
    def create_sequence_table(self) -> Dict[str, Any]:
        """
        Create sequence generator table for atomic sequence number generation
        """
        table_definition = {
            'TableName': 'aquachain-sequence',
            'KeySchema': [
                {
                    'AttributeName': 'sequenceType',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'sequenceType',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Environment',
                    'Value': 'production'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created sequence table: {response['TableDescription']['TableName']}")
            
            # Initialize sequence counter
            self._initialize_sequence_counter()
            
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Sequence table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-sequence')
    
    def create_users_table(self) -> Dict[str, Any]:
        """
        Create users table for profile management
        """
        table_definition = {
            'TableName': 'aquachain-users',
            'KeySchema': [
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'EmailIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Environment',
                    'Value': 'production'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created users table: {response['TableDescription']['TableName']}")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Users table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-users')
    
    def create_service_requests_table(self) -> Dict[str, Any]:
        """
        Create service requests table for technician assignment
        """
        table_definition = {
            'TableName': 'aquachain-service-requests',
            'KeySchema': [
                {
                    'AttributeName': 'requestId',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'requestId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'consumerId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'technicianId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'ConsumerIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'consumerId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'TechnicianIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'technicianId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
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
            'Tags': [
                {
                    'Key': 'Project',
                    'Value': 'AquaChain'
                },
                {
                    'Key': 'Environment',
                    'Value': 'production'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created service requests table: {response['TableDescription']['TableName']}")
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Service requests table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-service-requests')
    
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
    
    def _initialize_sequence_counter(self):
        """Initialize the sequence counter for ledger entries"""
        try:
            dynamodb_resource = boto3.resource('dynamodb', region_name=self.region_name)
            table = dynamodb_resource.Table('aquachain-sequence')
            
            table.put_item(
                Item={
                    'sequenceType': 'LEDGER',
                    'currentSequence': 0,
                    'lastUpdated': datetime.utcnow().isoformat()
                },
                ConditionExpression='attribute_not_exists(sequenceType)'
            )
            print("Initialized sequence counter")
        except Exception as e:
            print(f"Sequence counter already initialized or error: {e}")
    
    def create_all_tables(self):
        """Create all DynamoDB tables for AquaChain system"""
        print("Creating DynamoDB tables for AquaChain system...")
        
        tables = [
            self.create_readings_table,
            self.create_ledger_table,
            self.create_sequence_table,
            self.create_users_table,
            self.create_service_requests_table
        ]
        
        for create_table_func in tables:
            try:
                create_table_func()
            except Exception as e:
                print(f"Error creating table: {e}")
        
        print("DynamoDB table creation completed")

def generate_time_windowed_partition_key(device_id: str, timestamp: Optional[str] = None) -> str:
    """
    Generate time-windowed partition key for readings table
    Format: deviceId#YYYYMM
    """
    if timestamp:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    else:
        dt = datetime.utcnow()
    
    return f"{device_id}#{dt.strftime('%Y%m')}"

def calculate_ttl_timestamp(days: int = 90) -> int:
    """
    Calculate TTL timestamp for DynamoDB items
    Default: 90 days from now
    """
    expiry_date = datetime.utcnow() + timedelta(days=days)
    return int(expiry_date.timestamp())

if __name__ == "__main__":
    # Example usage
    manager = DynamoDBTableManager()
    manager.create_all_tables()