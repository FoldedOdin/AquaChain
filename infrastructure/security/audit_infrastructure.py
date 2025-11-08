"""
Audit infrastructure setup for AquaChain compliance tracking.
Creates DynamoDB tables, S3 buckets, and CloudWatch resources for audit logging.
Requirements: 15.5
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AuditInfrastructureSetup:
    """Setup audit logging infrastructure"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
    
    def create_audit_tables(self) -> Dict[str, Any]:
        """Create DynamoDB tables for audit logging"""
        tables_created = {}
        
        # Audit logs table
        try:
            audit_table_name = 'aquachain-audit-logs'
            
            response = self.dynamodb.create_table(
                TableName=audit_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'event_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'event_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'event_type',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'user-events-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
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
                        'IndexName': 'event-type-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'event_type',
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
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                },
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'AquaChain'
                    },
                    {
                        'Key': 'Component',
                        'Value': 'Audit'
                    },
                    {
                        'Key': 'DataClassification',
                        'Value': 'Confidential'
                    }
                ]
            )
            
            tables_created['audit_logs'] = {
                'name': audit_table_name,
                'arn': response['TableDescription']['TableArn']
            }
            
            # Wait for table to be active
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=audit_table_name)
            
            # Enable TTL
            self.dynamodb.update_time_to_live(
                TableName=audit_table_name,
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                }
            )
            
            logger.info(f"Created audit logs table: {audit_table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Audit logs table already exists: {audit_table_name}")
                response = self.dynamodb.describe_table(TableName=audit_table_name)
                tables_created['audit_logs'] = {
                    'name': audit_table_name,
                    'arn': response['Table']['TableArn'],
                    'status': 'exists'
                }
            else:
                logger.error(f"Error creating audit logs table: {e}")
                raise
        
        # Compliance tracking table
        try:
            compliance_table_name = 'aquachain-compliance-tracking'
            
            response = self.dynamodb.create_table(
                TableName=compliance_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'metric_type',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'date',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'metric_type',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'date',
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
                        'Value': 'Compliance'
                    }
                ]
            )
            
            tables_created['compliance_tracking'] = {
                'name': compliance_table_name,
                'arn': response['TableDescription']['TableArn']
            }
            
            # Wait for table to be active
            waiter.wait(TableName=compliance_table_name)
            
            logger.info(f"Created compliance tracking table: {compliance_table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Compliance tracking table already exists: {compliance_table_name}")
                response = self.dynamodb.describe_table(TableName=compliance_table_name)
                tables_created['compliance_tracking'] = {
                    'name': compliance_table_name,
                    'arn': response['Table']['TableArn'],
                    'status': 'exists'
                }
            else:
                logger.error(f"Error creating compliance tracking table: {e}")
                raise
        
        return tables_created
    
    def create_audit_bucket(self) -> Dict[str, Any]:
        """Create S3 bucket for audit log archival"""
        try:
            bucket_name = 'aquachain-audit-archive'
            
            # Create bucket
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Enable versioning
            self.s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure lifecycle policy
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'AuditLogArchival',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'audit-logs/'},
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': 90,
                                'StorageClass': 'GLACIER'
                            },
                            {
                                'Days': 365,
                                'StorageClass': 'DEEP_ARCHIVE'
                            }
                        ]
                    },
                    {
                        'ID': 'ComplianceReports',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'compliance-reports/'},
                        'Transitions': [
                            {
                                'Days': 90,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': 365,
                                'StorageClass': 'GLACIER'
                            }
                        ]
                    }
                ]
            }
            
            self.s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            
            # Configure bucket policy for audit integrity
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyInsecureConnections",
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:*",
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}",
                            f"arn:aws:s3:::{bucket_name}/*"
                        ],
                        "Condition": {
                            "Bool": {
                                "aws:SecureTransport": "false"
                            }
                        }
                    },
                    {
                        "Sid": "DenyUnencryptedObjectUploads",
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:PutObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*",
                        "Condition": {
                            "StringNotEquals": {
                                "s3:x-amz-server-side-encryption": "aws:kms"
                            }
                        }
                    }
                ]
            }
            
            self.s3.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            # Enable public access block
            self.s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            logger.info(f"Created audit archive bucket: {bucket_name}")
            
            return {
                'bucket_name': bucket_name,
                'bucket_arn': f"arn:aws:s3:::{bucket_name}"
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"Audit archive bucket already exists: {bucket_name}")
                return {
                    'bucket_name': bucket_name,
                    'bucket_arn': f"arn:aws:s3:::{bucket_name}",
                    'status': 'exists'
                }
            else:
                logger.error(f"Error creating audit archive bucket: {e}")
                raise
    
    def create_audit_kms_key(self) -> Dict[str, Any]:
        """Create KMS key for audit log signing"""
        try:
            key_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "Enable IAM User Permissions",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::123456789012:root"
                        },
                        "Action": "kms:*",
                        "Resource": "*"
                    },
                    {
                        "Sid": "Allow audit logging service",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": [
                            "kms:GenerateMac",
                            "kms:VerifyMac",
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:GenerateDataKey"
                        ],
                        "Resource": "*",
                        "Condition": {
                            "StringEquals": {
                                "kms:ViaService": f"s3.{self.region}.amazonaws.com"
                            }
                        }
                    }
                ]
            }
            
            response = self.kms.create_key(
                Description='AquaChain Audit Log Signing Key',
                KeyUsage='SIGN_VERIFY',
                KeySpec='HMAC_256',
                Policy=json.dumps(key_policy),
                Tags=[
                    {
                        'TagKey': 'Project',
                        'TagValue': 'AquaChain'
                    },
                    {
                        'TagKey': 'Component',
                        'TagValue': 'Audit'
                    },
                    {
                        'TagKey': 'Purpose',
                        'TagValue': 'LogSigning'
                    }
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            key_arn = response['KeyMetadata']['Arn']
            
            # Create alias
            self.kms.create_alias(
                AliasName='alias/aquachain-audit-signing',
                TargetKeyId=key_id
            )
            
            logger.info(f"Created audit signing KMS key: {key_id}")
            
            return {
                'key_id': key_id,
                'key_arn': key_arn,
                'alias': 'alias/aquachain-audit-signing'
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info("Audit signing KMS key alias already exists")
                # Get existing key info
                response = self.kms.describe_key(KeyId='alias/aquachain-audit-signing')
                return {
                    'key_id': response['KeyMetadata']['KeyId'],
                    'key_arn': response['KeyMetadata']['Arn'],
                    'alias': 'alias/aquachain-audit-signing',
                    'status': 'exists'
                }
            else:
                logger.error(f"Error creating audit signing KMS key: {e}")
                raise
    
    def create_cloudwatch_log_group(self) -> Dict[str, Any]:
        """Create CloudWatch log group for audit logs"""
        try:
            log_group_name = '/aws/lambda/aquachain-audit'
            
            self.logs.create_log_group(
                logGroupName=log_group_name,
                tags={
                    'Project': 'AquaChain',
                    'Component': 'Audit',
                    'DataClassification': 'Confidential'
                }
            )
            
            # Set retention policy (7 years)
            self.logs.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=2555  # 7 years
            )
            
            logger.info(f"Created audit log group: {log_group_name}")
            
            return {
                'log_group_name': log_group_name,
                'log_group_arn': f"arn:aws:logs:{self.region}:123456789012:log-group:{log_group_name}"
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info(f"Audit log group already exists: {log_group_name}")
                return {
                    'log_group_name': log_group_name,
                    'log_group_arn': f"arn:aws:logs:{self.region}:123456789012:log-group:{log_group_name}",
                    'status': 'exists'
                }
            else:
                logger.error(f"Error creating audit log group: {e}")
                raise
    
    def setup_audit_infrastructure(self) -> Dict[str, Any]:
        """Set up complete audit infrastructure"""
        try:
            # Create DynamoDB tables
            tables = self.create_audit_tables()
            
            # Create S3 bucket
            bucket = self.create_audit_bucket()
            
            # Create KMS key
            kms_key = self.create_audit_kms_key()
            
            # Create CloudWatch log group
            log_group = self.create_cloudwatch_log_group()
            
            logger.info("Audit infrastructure setup completed")
            
            return {
                'tables': tables,
                'bucket': bucket,
                'kms_key': kms_key,
                'log_group': log_group,
                'region': self.region
            }
            
        except Exception as e:
            logger.error(f"Error setting up audit infrastructure: {e}")
            raise

def main():
    """Main function to set up audit infrastructure"""
    logging.basicConfig(level=logging.INFO)
    
    setup = AuditInfrastructureSetup()
    result = setup.setup_audit_infrastructure()
    
    print("Audit Infrastructure Setup Complete:")
    print(f"Audit Logs Table: {result['tables']['audit_logs']['name']}")
    print(f"Compliance Table: {result['tables']['compliance_tracking']['name']}")
    print(f"Audit Bucket: {result['bucket']['bucket_name']}")
    print(f"KMS Key: {result['kms_key']['key_id']}")
    print(f"Log Group: {result['log_group']['log_group_name']}")
    
    return result

if __name__ == "__main__":
    main()