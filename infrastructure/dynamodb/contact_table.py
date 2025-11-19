"""
DynamoDB table definition for contact form submissions
"""

import boto3
from typing import Dict, Any


class ContactTableManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.region_name = region_name
    
    def create_contact_submissions_table(self) -> Dict[str, Any]:
        """
        Create contact submissions table for storing contact form data
        """
        table_definition = {
            'TableName': 'aquachain-contact-submissions',
            'KeySchema': [
                {
                    'AttributeName': 'submissionId',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'submissionId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'createdAt',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'inquiryType',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'email-createdAt-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
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
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'inquiryType-createdAt-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'inquiryType',
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
                    'BillingMode': 'PAY_PER_REQUEST'
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
                },
                {
                    'Key': 'Purpose',
                    'Value': 'contact-form'
                }
            ]
        }
        
        try:
            response = self.dynamodb.create_table(**table_definition)
            print(f"Created contact submissions table: {response['TableDescription']['TableName']}")
            
            # Enable TTL for automatic cleanup after 1 year
            self._enable_ttl('aquachain-contact-submissions', 'ttl')
            
            return response
        except self.dynamodb.exceptions.ResourceInUseException:
            print("Contact submissions table already exists")
            return self.dynamodb.describe_table(TableName='aquachain-contact-submissions')
    
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


if __name__ == '__main__':
    # Create the table
    manager = ContactTableManager()
    manager.create_contact_submissions_table()
