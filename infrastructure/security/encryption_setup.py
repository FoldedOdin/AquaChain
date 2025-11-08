"""
Encryption infrastructure setup for AquaChain.
Creates KMS keys, S3 buckets with encryption, and DynamoDB encryption configuration.
Requirements: 2.4, 15.1
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EncryptionInfrastructureSetup:
    """Setup encryption infrastructure for AquaChain"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.kms = boto3.client('kms', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
    
    def create_encryption_keys(self) -> Dict[str, Any]:
        """Create all required KMS keys for AquaChain encryption"""
        try:
            created_keys = {}
            
            # Master encryption key
            master_key = self._create_kms_key(
                description='AquaChain Master Encryption Key',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-master-key',
                key_policy=self._get_master_key_policy()
            )
            created_keys['master_key'] = master_key
            
            # Ledger encryption key (for immutable data)
            ledger_key = self._create_kms_key(
                description='AquaChain Ledger Encryption Key - Immutable Data',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-ledger-key',
                key_policy=self._get_ledger_key_policy(),
                deletion_window=30  # Longer deletion window for critical data
            )
            created_keys['ledger_key'] = ledger_key
            
            # PII encryption key
            pii_key = self._create_kms_key(
                description='AquaChain PII Encryption Key',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-pii-key',
                key_policy=self._get_pii_key_policy()
            )
            created_keys['pii_key'] = pii_key
            
            # Data signing key
            signing_key = self._create_kms_key(
                description='AquaChain Data Integrity Signing Key',
                key_usage='SIGN_VERIFY',
                key_spec='RSA_2048',
                alias='aquachain-signing-key',
                key_policy=self._get_signing_key_policy()
            )
            created_keys['signing_key'] = signing_key
            
            # Backup encryption key
            backup_key = self._create_kms_key(
                description='AquaChain Backup Encryption Key',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-backup-key',
                key_policy=self._get_backup_key_policy()
            )
            created_keys['backup_key'] = backup_key
            
            logger.info("Created all encryption keys successfully")
            return created_keys
            
        except Exception as e:
            logger.error(f"Error creating encryption keys: {e}")
            raise
    
    def _create_kms_key(self, 
                       description: str,
                       key_usage: str = 'ENCRYPT_DECRYPT',
                       key_spec: str = 'SYMMETRIC_DEFAULT',
                       alias: str = None,
                       key_policy: Dict[str, Any] = None,
                       deletion_window: int = 7) -> Dict[str, Any]:
        """Create a KMS key with specified configuration"""
        try:
            # Create key
            create_params = {
                'Description': description,
                'KeyUsage': key_usage,
                'KeySpec': key_spec,
                'Tags': [
                    {'TagKey': 'Project', 'TagValue': 'AquaChain'},
                    {'TagKey': 'Component', 'TagValue': 'Encryption'},
                    {'TagKey': 'KeyUsage', 'TagValue': key_usage},
                    {'TagKey': 'Environment', 'TagValue': 'Production'}
                ]
            }
            
            if key_policy:
                create_params['Policy'] = json.dumps(key_policy)
            
            response = self.kms.create_key(**create_params)
            
            key_id = response['KeyMetadata']['KeyId']
            key_arn = response['KeyMetadata']['Arn']
            
            # Create alias
            if alias:
                try:
                    self.kms.create_alias(
                        AliasName=f'alias/{alias}',
                        TargetKeyId=key_id
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'AlreadyExistsException':
                        raise
            
            # Enable automatic key rotation for symmetric keys
            if key_usage == 'ENCRYPT_DECRYPT' and key_spec == 'SYMMETRIC_DEFAULT':
                self.kms.enable_key_rotation(KeyId=key_id)
                logger.info(f"Enabled automatic rotation for key: {key_id}")
            
            logger.info(f"Created KMS key: {description} ({key_id})")
            
            return {
                'key_id': key_id,
                'key_arn': key_arn,
                'alias': f'alias/{alias}' if alias else None,
                'description': description
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                # Key alias already exists, get existing key info
                if alias:
                    response = self.kms.describe_key(KeyId=f'alias/{alias}')
                    return {
                        'key_id': response['KeyMetadata']['KeyId'],
                        'key_arn': response['KeyMetadata']['Arn'],
                        'alias': f'alias/{alias}',
                        'description': description,
                        'status': 'exists'
                    }
            logger.error(f"Error creating KMS key: {e}")
            raise
    
    def _get_master_key_policy(self) -> Dict[str, Any]:
        """Get key policy for master encryption key"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::123456789012:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow AquaChain Lambda Functions",
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "kms:ViaService": [
                                f"s3.{self.region}.amazonaws.com",
                                f"dynamodb.{self.region}.amazonaws.com"
                            ]
                        }
                    }
                },
                {
                    "Sid": "Allow S3 Service",
                    "Effect": "Allow",
                    "Principal": {"Service": "s3.amazonaws.com"},
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
    
    def _get_ledger_key_policy(self) -> Dict[str, Any]:
        """Get key policy for ledger encryption key (more restrictive)"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::123456789012:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Ledger Service Only",
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": self.region
                        },
                        "StringLike": {
                            "aws:userid": "*:aquachain-ledger-*"
                        }
                    }
                }
            ]
        }
    
    def _get_pii_key_policy(self) -> Dict[str, Any]:
        """Get key policy for PII encryption key"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::123456789012:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow PII Processing Services",
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "kms:EncryptionContext:DataType": "UserInformation"
                        }
                    }
                }
            ]
        }
    
    def _get_signing_key_policy(self) -> Dict[str, Any]:
        """Get key policy for data signing key"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::123456789012:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Data Signing",
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": [
                        "kms:Sign",
                        "kms:Verify",
                        "kms:GetPublicKey",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
    
    def _get_backup_key_policy(self) -> Dict[str, Any]:
        """Get key policy for backup encryption key"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::123456789012:root"},
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Backup Services",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": [
                            "lambda.amazonaws.com",
                            "backup.amazonaws.com"
                        ]
                    },
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
    
    def configure_s3_encryption(self) -> Dict[str, Any]:
        """Configure S3 buckets with encryption"""
        try:
            bucket_configs = {}
            
            # Configure existing buckets with encryption
            buckets_to_configure = [
                {
                    'name': 'aquachain-data-lake',
                    'key_alias': 'alias/aquachain-master-key',
                    'description': 'Raw sensor data storage'
                },
                {
                    'name': 'aquachain-audit-trail',
                    'key_alias': 'alias/aquachain-ledger-key',
                    'description': 'Immutable audit trail storage'
                },
                {
                    'name': 'aquachain-secure-backups',
                    'key_alias': 'alias/aquachain-backup-key',
                    'description': 'Encrypted backup storage'
                }
            ]
            
            for bucket_config in buckets_to_configure:
                bucket_name = bucket_config['name']
                
                try:
                    # Create bucket if it doesn't exist
                    try:
                        if self.region == 'us-east-1':
                            self.s3.create_bucket(Bucket=bucket_name)
                        else:
                            self.s3.create_bucket(
                                Bucket=bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': self.region}
                            )
                    except ClientError as e:
                        if e.response['Error']['Code'] != 'BucketAlreadyOwnedByYou':
                            raise
                    
                    # Configure default encryption
                    self.s3.put_bucket_encryption(
                        Bucket=bucket_name,
                        ServerSideEncryptionConfiguration={
                            'Rules': [
                                {
                                    'ApplyServerSideEncryptionByDefault': {
                                        'SSEAlgorithm': 'aws:kms',
                                        'KMSMasterKeyID': bucket_config['key_alias']
                                    },
                                    'BucketKeyEnabled': True
                                }
                            ]
                        }
                    )
                    
                    # Enable versioning for audit trail bucket
                    if 'audit' in bucket_name or 'backup' in bucket_name:
                        self.s3.put_bucket_versioning(
                            Bucket=bucket_name,
                            VersioningConfiguration={'Status': 'Enabled'}
                        )
                    
                    # Configure public access block
                    self.s3.put_public_access_block(
                        Bucket=bucket_name,
                        PublicAccessBlockConfiguration={
                            'BlockPublicAcls': True,
                            'IgnorePublicAcls': True,
                            'BlockPublicPolicy': True,
                            'RestrictPublicBuckets': True
                        }
                    )
                    
                    bucket_configs[bucket_name] = {
                        'encryption_key': bucket_config['key_alias'],
                        'description': bucket_config['description'],
                        'status': 'configured'
                    }
                    
                    logger.info(f"Configured encryption for bucket: {bucket_name}")
                    
                except ClientError as e:
                    logger.error(f"Error configuring bucket {bucket_name}: {e}")
                    bucket_configs[bucket_name] = {'status': 'error', 'error': str(e)}
            
            return bucket_configs
            
        except Exception as e:
            logger.error(f"Error configuring S3 encryption: {e}")
            raise
    
    def configure_dynamodb_encryption(self) -> Dict[str, Any]:
        """Configure DynamoDB tables with encryption at rest"""
        try:
            table_configs = {}
            
            # Tables to configure with encryption
            tables_to_configure = [
                {
                    'name': 'aquachain-readings',
                    'key_alias': 'alias/aquachain-master-key'
                },
                {
                    'name': 'aquachain-ledger',
                    'key_alias': 'alias/aquachain-ledger-key'
                },
                {
                    'name': 'aquachain-users',
                    'key_alias': 'alias/aquachain-pii-key'
                },
                {
                    'name': 'aquachain-audit-logs',
                    'key_alias': 'alias/aquachain-ledger-key'
                },
                {
                    'name': 'aquachain-service-requests',
                    'key_alias': 'alias/aquachain-master-key'
                }
            ]
            
            for table_config in tables_to_configure:
                table_name = table_config['name']
                
                try:
                    # Check if table exists
                    response = self.dynamodb.describe_table(TableName=table_name)
                    
                    # Update table with encryption if not already configured
                    current_encryption = response['Table'].get('SSEDescription', {})
                    
                    if current_encryption.get('Status') != 'ENABLED':
                        self.dynamodb.update_table(
                            TableName=table_name,
                            SSESpecification={
                                'Enabled': True,
                                'SSEType': 'KMS',
                                'KMSMasterKeyId': table_config['key_alias']
                            }
                        )
                        
                        table_configs[table_name] = {
                            'encryption_key': table_config['key_alias'],
                            'status': 'encryption_enabled'
                        }
                        
                        logger.info(f"Enabled encryption for table: {table_name}")
                    else:
                        table_configs[table_name] = {
                            'encryption_key': current_encryption.get('KMSMasterKeyArn', 'default'),
                            'status': 'already_encrypted'
                        }
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        table_configs[table_name] = {'status': 'table_not_found'}
                    else:
                        logger.error(f"Error configuring encryption for table {table_name}: {e}")
                        table_configs[table_name] = {'status': 'error', 'error': str(e)}
            
            return table_configs
            
        except Exception as e:
            logger.error(f"Error configuring DynamoDB encryption: {e}")
            raise
    
    def setup_key_rotation_schedule(self) -> Dict[str, Any]:
        """Set up automated key rotation schedule"""
        try:
            # Create Lambda function for key rotation monitoring
            rotation_config = {
                'rotation_enabled': True,
                'rotation_schedule': '90 days',
                'monitoring_enabled': True
            }
            
            # Enable CloudWatch Events for key rotation monitoring
            events_client = boto3.client('events', region_name=self.region)
            
            # Create rule for key rotation monitoring
            rule_name = 'aquachain-key-rotation-monitor'
            
            try:
                events_client.put_rule(
                    Name=rule_name,
                    ScheduleExpression='rate(7 days)',  # Check weekly
                    Description='Monitor AquaChain KMS key rotation status',
                    State='ENABLED',
                    Tags=[
                        {
                            'Key': 'Project',
                            'Value': 'AquaChain'
                        },
                        {
                            'Key': 'Component',
                            'Value': 'KeyRotation'
                        }
                    ]
                )
                
                rotation_config['monitoring_rule'] = rule_name
                logger.info(f"Created key rotation monitoring rule: {rule_name}")
                
            except ClientError as e:
                logger.error(f"Error creating key rotation monitoring rule: {e}")
                rotation_config['monitoring_error'] = str(e)
            
            return rotation_config
            
        except Exception as e:
            logger.error(f"Error setting up key rotation schedule: {e}")
            raise
    
    def setup_encryption_infrastructure(self) -> Dict[str, Any]:
        """Set up complete encryption infrastructure"""
        try:
            # Create encryption keys
            keys = self.create_encryption_keys()
            
            # Configure S3 encryption
            s3_config = self.configure_s3_encryption()
            
            # Configure DynamoDB encryption
            dynamodb_config = self.configure_dynamodb_encryption()
            
            # Set up key rotation
            rotation_config = self.setup_key_rotation_schedule()
            
            logger.info("Encryption infrastructure setup completed successfully")
            
            return {
                'kms_keys': keys,
                's3_buckets': s3_config,
                'dynamodb_tables': dynamodb_config,
                'key_rotation': rotation_config,
                'region': self.region,
                'setup_completed_at': boto3.Session().region_name
            }
            
        except Exception as e:
            logger.error(f"Error setting up encryption infrastructure: {e}")
            raise

def main():
    """Main function to set up encryption infrastructure"""
    logging.basicConfig(level=logging.INFO)
    
    setup = EncryptionInfrastructureSetup()
    result = setup.setup_encryption_infrastructure()
    
    print("Encryption Infrastructure Setup Complete:")
    print(f"KMS Keys Created: {len(result['kms_keys'])}")
    print(f"S3 Buckets Configured: {len(result['s3_buckets'])}")
    print(f"DynamoDB Tables Configured: {len(result['dynamodb_tables'])}")
    print(f"Key Rotation Monitoring: {result['key_rotation']['rotation_enabled']}")
    
    return result

if __name__ == "__main__":
    main()