"""
S3 bucket configuration for AquaChain system
Implements data lake, audit trail with Object Lock, and cross-account replication
"""

import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional

class S3BucketManager:
    def __init__(self, region_name: str = 'us-east-1', account_id: str = None):
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.s3_resource = boto3.resource('s3', region_name=region_name)
        self.region_name = region_name
        self.account_id = account_id or boto3.client('sts').get_caller_identity()['Account']
    
    def create_data_lake_bucket(self, bucket_name: str = None) -> Dict[str, Any]:
        """
        Create data lake bucket with proper partitioning structure
        """
        if not bucket_name:
            bucket_name = f'aquachain-data-lake-{self.account_id}'
        
        try:
            # Create bucket
            if self.region_name == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region_name}
                )
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure server-side encryption with KMS
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': f'arn:aws:kms:{self.region_name}:{self.account_id}:alias/aquachain-s3-key'
                            },
                            'BucketKeyEnabled': True
                        }
                    ]
                }
            )
            
            # Set lifecycle policy for cost optimization
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'DataLakeLifecycle',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'raw-readings/'},
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
                        'ID': 'MLModelLifecycle',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'ml-models/archive/'},
                        'Transitions': [
                            {
                                'Days': 90,
                                'StorageClass': 'GLACIER'
                            }
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            
            # Set bucket policy for secure access
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
                        "Sid": "AllowAquaChainServices",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": [
                                f"arn:aws:iam::{self.account_id}:role/AquaChainDataProcessingRole",
                                f"arn:aws:iam::{self.account_id}:role/AquaChainMLRole"
                            ]
                        },
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            # Create folder structure
            self._create_folder_structure(bucket_name)
            
            print(f"Created data lake bucket: {bucket_name}")
            return {'bucket_name': bucket_name, 'region': self.region_name}
            
        except Exception as e:
            print(f"Error creating data lake bucket: {e}")
            raise
    
    def create_audit_trail_bucket(self, bucket_name: str = None, 
                                 replica_account_id: str = None) -> Dict[str, Any]:
        """
        Create audit trail bucket with Object Lock (7-year retention)
        """
        if not bucket_name:
            bucket_name = f'aquachain-audit-trail-{self.account_id}'
        
        try:
            # Create bucket with Object Lock enabled
            if self.region_name == 'us-east-1':
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    ObjectLockEnabledForBucket=True
                )
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region_name},
                    ObjectLockEnabledForBucket=True
                )
            
            # Enable versioning (required for Object Lock)
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure Object Lock with 7-year retention
            self.s3_client.put_object_lock_configuration(
                Bucket=bucket_name,
                ObjectLockConfiguration={
                    'ObjectLockEnabled': 'Enabled',
                    'Rule': {
                        'DefaultRetention': {
                            'Mode': 'COMPLIANCE',
                            'Years': 7
                        }
                    }
                }
            )
            
            # Configure server-side encryption with KMS
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': f'arn:aws:kms:{self.region_name}:{self.account_id}:alias/aquachain-audit-key'
                            },
                            'BucketKeyEnabled': True
                        }
                    ]
                }
            )
            
            # Set bucket policy for audit trail security
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
                        "Sid": "AllowAuditWriteOnly",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{self.account_id}:role/AquaChainAuditRole"
                        },
                        "Action": [
                            "s3:PutObject",
                            "s3:PutObjectLegalHold",
                            "s3:PutObjectRetention"
                        ],
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    },
                    {
                        "Sid": "AllowAuditRead",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": [
                                f"arn:aws:iam::{self.account_id}:role/AquaChainAuditRole",
                                f"arn:aws:iam::{self.account_id}:role/AquaChainAdminRole"
                            ]
                        },
                        "Action": [
                            "s3:GetObject",
                            "s3:GetObjectVersion",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}",
                            f"arn:aws:s3:::{bucket_name}/*"
                        ]
                    }
                ]
            }
            
            # Add cross-account replication permissions if replica account specified
            if replica_account_id:
                bucket_policy["Statement"].append({
                    "Sid": "AllowCrossAccountReplication",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.account_id}:role/AquaChainReplicationRole"
                    },
                    "Action": [
                        "s3:GetObjectVersionForReplication",
                        "s3:GetObjectVersionAcl"
                    ],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                })
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            # Configure cross-account replication if specified
            if replica_account_id:
                self._setup_cross_account_replication(bucket_name, replica_account_id)
            
            print(f"Created audit trail bucket: {bucket_name}")
            return {'bucket_name': bucket_name, 'region': self.region_name}
            
        except Exception as e:
            print(f"Error creating audit trail bucket: {e}")
            raise
    
    def create_replica_bucket(self, bucket_name: str = None, 
                            source_account_id: str = None) -> Dict[str, Any]:
        """
        Create read-only replica bucket for cross-account audit trail
        """
        if not bucket_name:
            bucket_name = f'aquachain-audit-replica-{self.account_id}'
        
        try:
            # Create bucket
            if self.region_name == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region_name}
                )
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure server-side encryption
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': f'arn:aws:kms:{self.region_name}:{self.account_id}:alias/aquachain-replica-key'
                            },
                            'BucketKeyEnabled': True
                        }
                    ]
                }
            )
            
            # Set bucket policy for cross-account replication
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
                    }
                ]
            }
            
            if source_account_id:
                bucket_policy["Statement"].extend([
                    {
                        "Sid": "AllowCrossAccountReplication",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{source_account_id}:role/AquaChainReplicationRole"
                        },
                        "Action": [
                            "s3:PutObject",
                            "s3:PutObjectAcl",
                            "s3:PutObjectVersionAcl"
                        ],
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    },
                    {
                        "Sid": "AllowReadOnlyAccess",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{self.account_id}:role/AquaChainAuditorRole"
                        },
                        "Action": [
                            "s3:GetObject",
                            "s3:GetObjectVersion",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}",
                            f"arn:aws:s3:::{bucket_name}/*"
                        ]
                    }
                ])
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            print(f"Created replica bucket: {bucket_name}")
            return {'bucket_name': bucket_name, 'region': self.region_name}
            
        except Exception as e:
            print(f"Error creating replica bucket: {e}")
            raise
    
    def _create_folder_structure(self, bucket_name: str):
        """Create logical folder structure in data lake bucket"""
        folders = [
            'raw-readings/',
            'ml-models/current/',
            'ml-models/archive/',
            'hash-chain-verification/',
            'processed-data/',
            'analytics-reports/'
        ]
        
        for folder in folders:
            try:
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=folder,
                    Body=b'',
                    ServerSideEncryption='aws:kms',
                    SSEKMSKeyId=f'arn:aws:kms:{self.region_name}:{self.account_id}:alias/aquachain-s3-key'
                )
            except Exception as e:
                print(f"Warning: Could not create folder {folder}: {e}")
    
    def _setup_cross_account_replication(self, source_bucket: str, replica_account_id: str):
        """Configure cross-account replication for audit trail"""
        replication_config = {
            'Role': f'arn:aws:iam::{self.account_id}:role/AquaChainReplicationRole',
            'Rules': [
                {
                    'ID': 'AuditTrailReplication',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'hash-chains/'},
                    'Destination': {
                        'Bucket': f'arn:aws:s3:::aquachain-audit-replica-{replica_account_id}',
                        'StorageClass': 'STANDARD_IA',
                        'EncryptionConfiguration': {
                            'ReplicaKmsKeyID': f'arn:aws:kms:{self.region_name}:{replica_account_id}:alias/aquachain-replica-key'
                        }
                    },
                    'DeleteMarkerReplication': {'Status': 'Disabled'},
                    'ExistingObjectReplication': {'Status': 'Enabled'}
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_replication(
                Bucket=source_bucket,
                ReplicationConfiguration=replication_config
            )
            print(f"Configured cross-account replication for {source_bucket}")
        except Exception as e:
            print(f"Error setting up replication: {e}")
    
    def upload_hash_chain_verification(self, bucket_name: str, date: str, 
                                     chain_data: Dict[str, Any]) -> str:
        """
        Upload hash chain verification data with Object Lock
        """
        key = f"hash-chains/{date}-chain.json"
        
        try:
            response = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json.dumps(chain_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=f'arn:aws:kms:{self.region_name}:{self.account_id}:alias/aquachain-audit-key',
                ObjectLockMode='COMPLIANCE',
                ObjectLockRetainUntilDate=datetime(2032, 1, 1),  # 7+ years
                Metadata={
                    'project': 'aquachain',
                    'data-type': 'hash-chain-verification',
                    'created-date': datetime.utcnow().isoformat()
                }
            )
            
            print(f"Uploaded hash chain verification: {key}")
            return key
            
        except Exception as e:
            print(f"Error uploading hash chain verification: {e}")
            raise
    
    def create_all_buckets(self, replica_account_id: str = None):
        """Create all S3 buckets for AquaChain system"""
        print("Creating S3 buckets for AquaChain system...")
        
        try:
            # Create data lake bucket
            data_lake = self.create_data_lake_bucket()
            
            # Create audit trail bucket
            audit_trail = self.create_audit_trail_bucket(
                replica_account_id=replica_account_id
            )
            
            # Create replica bucket if replica account specified
            if replica_account_id:
                replica = self.create_replica_bucket(
                    source_account_id=self.account_id
                )
                print(f"Created replica bucket in account {replica_account_id}")
            
            print("S3 bucket creation completed")
            return {
                'data_lake': data_lake,
                'audit_trail': audit_trail
            }
            
        except Exception as e:
            print(f"Error creating S3 buckets: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    manager = S3BucketManager()
    manager.create_all_buckets()