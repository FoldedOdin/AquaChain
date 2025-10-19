"""
KMS key management for AquaChain system
Implements encryption keys for S3, ledger signing, and cross-account access
"""

import boto3
import json
from typing import Dict, Any, List

class KMSKeyManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.kms_client = boto3.client('kms', region_name=region_name)
        self.region_name = region_name
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
    
    def create_s3_encryption_key(self) -> Dict[str, Any]:
        """
        Create KMS key for S3 data lake encryption
        """
        key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.account_id}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow S3 Service",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "s3.amazonaws.com"
                    },
                    "Action": [
                        "kms:Decrypt",
                        "kms:GenerateDataKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Allow AquaChain Services",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            f"arn:aws:iam::{self.account_id}:role/AquaChainDataProcessingRole",
                            f"arn:aws:iam::{self.account_id}:role/AquaChainMLRole"
                        ]
                    },
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
        
        try:
            response = self.kms_client.create_key(
                Policy=json.dumps(key_policy),
                Description='AquaChain S3 Data Lake Encryption Key',
                Usage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Origin='AWS_KMS',
                Tags=[
                    {'TagKey': 'Project', 'TagValue': 'AquaChain'},
                    {'TagKey': 'Purpose', 'TagValue': 'S3-Encryption'},
                    {'TagKey': 'Environment', 'TagValue': 'production'}
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias
            self.kms_client.create_alias(
                AliasName='alias/aquachain-s3-key',
                TargetKeyId=key_id
            )
            
            print(f"Created S3 encryption key: {key_id}")
            return response
            
        except Exception as e:
            print(f"Error creating S3 encryption key: {e}")
            raise
    
    def create_audit_encryption_key(self) -> Dict[str, Any]:
        """
        Create KMS key for audit trail encryption with stricter access
        """
        key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.account_id}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow S3 Service",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "s3.amazonaws.com"
                    },
                    "Action": [
                        "kms:Decrypt",
                        "kms:GenerateDataKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Audit Services Only",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            f"arn:aws:iam::{self.account_id}:role/AquaChainAuditRole",
                            f"arn:aws:iam::{self.account_id}:role/AquaChainAdminRole"
                        ]
                    },
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Deny Delete Operations",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": [
                        "kms:ScheduleKeyDeletion",
                        "kms:CancelKeyDeletion"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            response = self.kms_client.create_key(
                Policy=json.dumps(key_policy),
                Description='AquaChain Audit Trail Encryption Key',
                Usage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Origin='AWS_KMS',
                Tags=[
                    {'TagKey': 'Project', 'TagValue': 'AquaChain'},
                    {'TagKey': 'Purpose', 'TagValue': 'Audit-Encryption'},
                    {'TagKey': 'Environment', 'TagValue': 'production'},
                    {'TagKey': 'Compliance', 'TagValue': 'required'}
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias
            self.kms_client.create_alias(
                AliasName='alias/aquachain-audit-key',
                TargetKeyId=key_id
            )
            
            print(f"Created audit encryption key: {key_id}")
            return response
            
        except Exception as e:
            print(f"Error creating audit encryption key: {e}")
            raise
    
    def create_ledger_signing_key(self) -> Dict[str, Any]:
        """
        Create asymmetric KMS key for ledger entry signing
        """
        key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.account_id}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Ledger Signing",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            f"arn:aws:iam::{self.account_id}:role/AquaChainDataProcessingRole",
                            f"arn:aws:iam::{self.account_id}:role/AquaChainLedgerRole"
                        ]
                    },
                    "Action": [
                        "kms:Sign",
                        "kms:GetPublicKey",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Signature Verification",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            f"arn:aws:iam::{self.account_id}:role/AquaChainAuditRole",
                            f"arn:aws:iam::{self.account_id}:role/AquaChainAdminRole"
                        ]
                    },
                    "Action": [
                        "kms:Verify",
                        "kms:GetPublicKey",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Deny Delete Operations",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": [
                        "kms:ScheduleKeyDeletion",
                        "kms:CancelKeyDeletion"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            response = self.kms_client.create_key(
                Policy=json.dumps(key_policy),
                Description='AquaChain Ledger Signing Key',
                Usage='SIGN_VERIFY',
                KeySpec='RSA_2048',
                Origin='AWS_KMS',
                Tags=[
                    {'TagKey': 'Project', 'TagValue': 'AquaChain'},
                    {'TagKey': 'Purpose', 'TagValue': 'Ledger-Signing'},
                    {'TagKey': 'Environment', 'TagValue': 'production'},
                    {'TagKey': 'Compliance', 'TagValue': 'required'}
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias
            self.kms_client.create_alias(
                AliasName='alias/aquachain-ledger-signing-key',
                TargetKeyId=key_id
            )
            
            print(f"Created ledger signing key: {key_id}")
            return response
            
        except Exception as e:
            print(f"Error creating ledger signing key: {e}")
            raise
    
    def create_replica_encryption_key(self, replica_account_id: str) -> Dict[str, Any]:
        """
        Create KMS key for cross-account replica bucket encryption
        """
        key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.account_id}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow S3 Service",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "s3.amazonaws.com"
                    },
                    "Action": [
                        "kms:Decrypt",
                        "kms:GenerateDataKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Cross Account Replication",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{replica_account_id}:role/AquaChainReplicationRole"
                    },
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Replica Access",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.account_id}:role/AquaChainAuditorRole"
                    },
                    "Action": [
                        "kms:Decrypt",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            response = self.kms_client.create_key(
                Policy=json.dumps(key_policy),
                Description='AquaChain Replica Bucket Encryption Key',
                Usage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Origin='AWS_KMS',
                Tags=[
                    {'TagKey': 'Project', 'TagValue': 'AquaChain'},
                    {'TagKey': 'Purpose', 'TagValue': 'Replica-Encryption'},
                    {'TagKey': 'Environment', 'TagValue': 'production'},
                    {'TagKey': 'ReplicaAccount', 'TagValue': replica_account_id}
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias
            self.kms_client.create_alias(
                AliasName='alias/aquachain-replica-key',
                TargetKeyId=key_id
            )
            
            print(f"Created replica encryption key: {key_id}")
            return response
            
        except Exception as e:
            print(f"Error creating replica encryption key: {e}")
            raise
    
    def get_public_key(self, key_id: str) -> Dict[str, Any]:
        """
        Get public key for signature verification
        """
        try:
            response = self.kms_client.get_public_key(KeyId=key_id)
            return response
        except Exception as e:
            print(f"Error getting public key: {e}")
            raise
    
    def sign_data(self, key_id: str, data: bytes, signing_algorithm: str = 'RSASSA_PSS_SHA_256') -> bytes:
        """
        Sign data using KMS asymmetric key
        """
        try:
            response = self.kms_client.sign(
                KeyId=key_id,
                Message=data,
                MessageType='RAW',
                SigningAlgorithm=signing_algorithm
            )
            return response['Signature']
        except Exception as e:
            print(f"Error signing data: {e}")
            raise
    
    def verify_signature(self, key_id: str, data: bytes, signature: bytes, 
                        signing_algorithm: str = 'RSASSA_PSS_SHA_256') -> bool:
        """
        Verify signature using KMS asymmetric key
        """
        try:
            response = self.kms_client.verify(
                KeyId=key_id,
                Message=data,
                MessageType='RAW',
                Signature=signature,
                SigningAlgorithm=signing_algorithm
            )
            return response['SignatureValid']
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False
    
    def create_all_keys(self, replica_account_id: str = None):
        """Create all KMS keys for AquaChain system"""
        print("Creating KMS keys for AquaChain system...")
        
        keys = {}
        
        try:
            # Create S3 encryption key
            keys['s3_key'] = self.create_s3_encryption_key()
            
            # Create audit encryption key
            keys['audit_key'] = self.create_audit_encryption_key()
            
            # Create ledger signing key
            keys['signing_key'] = self.create_ledger_signing_key()
            
            # Create replica encryption key if needed
            if replica_account_id:
                keys['replica_key'] = self.create_replica_encryption_key(replica_account_id)
            
            print("KMS key creation completed")
            return keys
            
        except Exception as e:
            print(f"Error creating KMS keys: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    manager = KMSKeyManager()
    manager.create_all_keys()