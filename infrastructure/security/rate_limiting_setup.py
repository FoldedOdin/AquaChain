"""
Rate limiting infrastructure setup for AquaChain security.
Creates DynamoDB table for rate limiting with TTL.
Requirements: 8.5
"""

import boto3
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RateLimitingSetup:
    """Setup rate limiting infrastructure"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.client('dynamodb', region_name=region)
    
    def create_rate_limit_table(self) -> Dict[str, Any]:
        """
        Create DynamoDB table for rate limiting with TTL.
        """
        try:
            table_name = 'aquachain-rate-limits'
            
            # Create table
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'identifier',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'identifier',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'AquaChain'
                    },
                    {
                        'Key': 'Component',
                        'Value': 'Security'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'RateLimiting'
                    }
                ]
            )
            
            table_arn = response['TableDescription']['TableArn']
            logger.info(f"Created rate limiting table: {table_name}")
            
            # Wait for table to be active
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            # Enable TTL on the table
            self.dynamodb.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                }
            )
            
            logger.info(f"Enabled TTL for table: {table_name}")
            
            return {
                'tableName': table_name,
                'tableArn': table_arn,
                'status': 'created'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Rate limiting table already exists: {table_name}")
                
                # Get existing table info
                response = self.dynamodb.describe_table(TableName=table_name)
                table_arn = response['Table']['TableArn']
                
                return {
                    'tableName': table_name,
                    'tableArn': table_arn,
                    'status': 'exists'
                }
            else:
                logger.error(f"Error creating rate limiting table: {e}")
                raise
    
    def create_waf_ip_set(self) -> Dict[str, Any]:
        """
        Create WAF IP set for blocking malicious IPs.
        """
        try:
            wafv2 = boto3.client('wafv2', region_name=self.region)
            
            ip_set_name = 'aquachain-blocked-ips'
            
            response = wafv2.create_ip_set(
                Scope='REGIONAL',
                Name=ip_set_name,
                Description='Blocked IP addresses for AquaChain API',
                IPAddressVersion='IPV4',
                Addresses=[],  # Start with empty set
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'AquaChain'
                    },
                    {
                        'Key': 'Component',
                        'Value': 'Security'
                    }
                ]
            )
            
            ip_set_arn = response['Summary']['ARN']
            logger.info(f"Created WAF IP set: {ip_set_name}")
            
            return {
                'ipSetName': ip_set_name,
                'ipSetArn': ip_set_arn,
                'ipSetId': response['Summary']['Id']
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'WAFDuplicateItemException':
                logger.info(f"WAF IP set already exists: {ip_set_name}")
                
                # List existing IP sets to get ARN
                response = wafv2.list_ip_sets(Scope='REGIONAL')
                for ip_set in response['IPSets']:
                    if ip_set['Name'] == ip_set_name:
                        return {
                            'ipSetName': ip_set_name,
                            'ipSetArn': ip_set['ARN'],
                            'ipSetId': ip_set['Id'],
                            'status': 'exists'
                        }
            else:
                logger.error(f"Error creating WAF IP set: {e}")
                raise
    
    def setup_security_infrastructure(self) -> Dict[str, Any]:
        """
        Set up complete security infrastructure.
        """
        try:
            # Create rate limiting table
            rate_limit_info = self.create_rate_limit_table()
            
            # Create WAF IP set
            waf_info = self.create_waf_ip_set()
            
            logger.info("Security infrastructure setup completed")
            
            return {
                'rateLimiting': rate_limit_info,
                'waf': waf_info,
                'region': self.region
            }
            
        except Exception as e:
            logger.error(f"Error setting up security infrastructure: {e}")
            raise

def main():
    """Main function to set up security infrastructure"""
    logging.basicConfig(level=logging.INFO)
    
    setup = RateLimitingSetup()
    result = setup.setup_security_infrastructure()
    
    print("Security Infrastructure Setup Complete:")
    print(f"Rate Limiting Table: {result['rateLimiting']['tableName']}")
    print(f"WAF IP Set: {result['waf']['ipSetName']}")
    
    return result

if __name__ == "__main__":
    main()