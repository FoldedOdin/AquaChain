"""
Comprehensive encryption and key management for AquaChain.
Implements encryption at rest and in transit with proper key rotation.
Requirements: 2.4, 15.1
"""

import json
import boto3
import base64
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from botocore.exceptions import ClientError
import os
import secrets

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Base exception for encryption-related errors"""
    pass

class KeyManagementError(EncryptionError):
    """Exception for key management errors"""
    pass

class EncryptionManager:
    """
    Comprehensive encryption and key management system.
    Implements requirements 2.4 and 15.1 for data encryption and key management.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.kms = boto3.client('kms', region_name=region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Key management configuration
        self.master_key_alias = 'alias/aquachain-master-key'
        self.data_key_spec = 'AES_256'
        self.key_rotation_days = 90
        
        # Encryption contexts for different data types
        self.encryption_contexts = {
            'sensor_data': {'DataType': 'SensorReadings', 'Classification': 'Confidential'},
            'user_data': {'DataType': 'UserInformation', 'Classification': 'PII'},
            'audit_logs': {'DataType': 'AuditLogs', 'Classification': 'Restricted'},
            'ledger_data': {'DataType': 'LedgerEntries', 'Classification': 'Immutable'},
            'backup_data': {'DataType': 'BackupData', 'Classification': 'Archive'}
        }
    
    def create_master_keys(self) -> Dict[str, Any]:
        """
        Create master encryption keys for different data types.
        """
        try:
            created_keys = {}
            
            # Master key for general data encryption
            master_key = self._create_kms_key(
                description='AquaChain Master Encryption Key',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-master-key'
            )
            created_keys['master_key'] = master_key
            
            # Dedicated key for ledger data (immutable)
            ledger_key = self._create_kms_key(
                description='AquaChain Ledger Encryption Key',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-ledger-key',
                deletion_window=30  # Longer deletion window for critical data
            )
            created_keys['ledger_key'] = ledger_key
            
            # Key for user PII data
            pii_key = self._create_kms_key(
                description='AquaChain PII Encryption Key',
                key_usage='ENCRYPT_DECRYPT',
                alias='aquachain-pii-key'
            )
            created_keys['pii_key'] = pii_key
            
            # Signing key for data integrity
            signing_key = self._create_kms_key(
                description='AquaChain Data Signing Key',
                key_usage='SIGN_VERIFY',
                key_spec='RSA_2048',
                alias='aquachain-signing-key'
            )
            created_keys['signing_key'] = signing_key
            
            logger.info("Created master encryption keys")
            return created_keys
            
        except Exception as e:
            logger.error(f"Error creating master keys: {e}")
            raise KeyManagementError(f"Failed to create master keys: {e}")
    
    def _create_kms_key(self, 
                       description: str,
                       key_usage: str = 'ENCRYPT_DECRYPT',
                       key_spec: str = 'SYMMETRIC_DEFAULT',
                       alias: str = None,
                       deletion_window: int = 7) -> Dict[str, Any]:
        """Create a KMS key with specified configuration"""
        try:
            # Key policy
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
                        "Sid": "Allow AquaChain services",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": [
                                "lambda.amazonaws.com",
                                "s3.amazonaws.com",
                                "dynamodb.amazonaws.com"
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
            
            # Create key
            response = self.kms.create_key(
                Description=description,
                KeyUsage=key_usage,
                KeySpec=key_spec,
                Policy=json.dumps(key_policy),
                Tags=[
                    {
                        'TagKey': 'Project',
                        'TagValue': 'AquaChain'
                    },
                    {
                        'TagKey': 'Component',
                        'TagValue': 'Encryption'
                    },
                    {
                        'TagKey': 'KeyUsage',
                        'TagValue': key_usage
                    }
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            key_arn = response['KeyMetadata']['Arn']
            
            # Create alias if specified
            if alias:
                try:
                    self.kms.create_alias(
                        AliasName=f'alias/{alias}',
                        TargetKeyId=key_id
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'AlreadyExistsException':
                        raise
            
            # Enable automatic key rotation
            if key_usage == 'ENCRYPT_DECRYPT' and key_spec == 'SYMMETRIC_DEFAULT':
                self.kms.enable_key_rotation(KeyId=key_id)
            
            return {
                'key_id': key_id,
                'key_arn': key_arn,
                'alias': f'alias/{alias}' if alias else None
            }
            
        except ClientError as e:
            logger.error(f"Error creating KMS key: {e}")
            raise
    
    def encrypt_data(self, 
                    data: Union[str, bytes, Dict[str, Any]], 
                    data_type: str = 'sensor_data',
                    key_alias: Optional[str] = None) -> Dict[str, Any]:
        """
        Encrypt data using KMS with appropriate encryption context.
        """
        try:
            # Convert data to bytes if necessary
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Get encryption context
            encryption_context = self.encryption_contexts.get(data_type, {})
            encryption_context['Timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Use specified key or default master key
            key_id = key_alias or self.master_key_alias
            
            # Encrypt with KMS
            response = self.kms.encrypt(
                KeyId=key_id,
                Plaintext=data_bytes,
                EncryptionContext=encryption_context
            )
            
            # Return encrypted data with metadata
            return {
                'ciphertext': base64.b64encode(response['CiphertextBlob']).decode('utf-8'),
                'key_id': response['KeyId'],
                'encryption_context': encryption_context,
                'algorithm': 'AES-256-GCM',
                'encrypted_at': encryption_context['Timestamp']
            }
            
        except ClientError as e:
            logger.error(f"Error encrypting data: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt_data(self, 
                    encrypted_data: Dict[str, Any],
                    expected_data_type: Optional[str] = None) -> Union[str, bytes, Dict[str, Any]]:
        """
        Decrypt data using KMS with context validation.
        """
        try:
            # Decode ciphertext
            ciphertext_blob = base64.b64decode(encrypted_data['ciphertext'])
            
            # Get encryption context
            encryption_context = encrypted_data.get('encryption_context', {})
            
            # Validate data type if specified
            if expected_data_type:
                context_data_type = encryption_context.get('DataType')
                expected_context = self.encryption_contexts.get(expected_data_type, {})
                if context_data_type != expected_context.get('DataType'):
                    raise EncryptionError(f"Data type mismatch: expected {expected_data_type}")
            
            # Decrypt with KMS
            response = self.kms.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionContext=encryption_context
            )
            
            # Return decrypted data
            plaintext = response['Plaintext']
            
            # Try to parse as JSON first
            try:
                return json.loads(plaintext.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return plaintext
            
        except ClientError as e:
            logger.error(f"Error decrypting data: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")
    
    def generate_data_key(self, 
                         key_spec: str = 'AES_256',
                         encryption_context: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Generate a data encryption key for envelope encryption.
        """
        try:
            response = self.kms.generate_data_key(
                KeyId=self.master_key_alias,
                KeySpec=key_spec,
                EncryptionContext=encryption_context or {}
            )
            
            return {
                'plaintext_key': response['Plaintext'],
                'encrypted_key': base64.b64encode(response['CiphertextBlob']).decode('utf-8'),
                'key_id': response['KeyId']
            }
            
        except ClientError as e:
            logger.error(f"Error generating data key: {e}")
            raise EncryptionError(f"Failed to generate data key: {e}")
    
    def encrypt_large_data(self, 
                          data: bytes,
                          data_type: str = 'sensor_data') -> Dict[str, Any]:
        """
        Encrypt large data using envelope encryption.
        """
        try:
            # Generate data encryption key
            encryption_context = self.encryption_contexts.get(data_type, {})
            encryption_context['Timestamp'] = datetime.now(timezone.utc).isoformat()
            
            data_key = self.generate_data_key(encryption_context=encryption_context)
            
            # Encrypt data with data key using Fernet
            fernet = Fernet(base64.urlsafe_b64encode(data_key['plaintext_key'][:32]))
            encrypted_data = fernet.encrypt(data)
            
            # Clear plaintext key from memory
            data_key['plaintext_key'] = None
            
            return {
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'encrypted_key': data_key['encrypted_key'],
                'key_id': data_key['key_id'],
                'encryption_context': encryption_context,
                'algorithm': 'Fernet',
                'encrypted_at': encryption_context['Timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error encrypting large data: {e}")
            raise EncryptionError(f"Failed to encrypt large data: {e}")
    
    def decrypt_large_data(self, encrypted_package: Dict[str, Any]) -> bytes:
        """
        Decrypt large data using envelope encryption.
        """
        try:
            # Decrypt the data key
            encrypted_key_blob = base64.b64decode(encrypted_package['encrypted_key'])
            encryption_context = encrypted_package.get('encryption_context', {})
            
            response = self.kms.decrypt(
                CiphertextBlob=encrypted_key_blob,
                EncryptionContext=encryption_context
            )
            
            plaintext_key = response['Plaintext']
            
            # Decrypt data with the data key
            fernet = Fernet(base64.urlsafe_b64encode(plaintext_key[:32]))
            encrypted_data = base64.b64decode(encrypted_package['encrypted_data'])
            
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting large data: {e}")
            raise EncryptionError(f"Failed to decrypt large data: {e}")
    
    def sign_data(self, data: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create digital signature for data integrity.
        """
        try:
            # Convert data to bytes if necessary
            if isinstance(data, dict):
                data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Create hash of data
            data_hash = hashlib.sha256(data_bytes).digest()
            
            # Sign with KMS
            response = self.kms.sign(
                KeyId='alias/aquachain-signing-key',
                Message=data_hash,
                MessageType='DIGEST',
                SigningAlgorithm='RSASSA_PSS_SHA_256'
            )
            
            return {
                'signature': base64.b64encode(response['Signature']).decode('utf-8'),
                'signing_algorithm': 'RSASSA_PSS_SHA_256',
                'key_id': response['KeyId'],
                'data_hash': base64.b64encode(data_hash).decode('utf-8'),
                'signed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Error signing data: {e}")
            raise EncryptionError(f"Failed to sign data: {e}")
    
    def verify_signature(self, 
                        data: Union[str, bytes, Dict[str, Any]], 
                        signature_info: Dict[str, Any]) -> bool:
        """
        Verify digital signature for data integrity.
        """
        try:
            # Convert data to bytes if necessary
            if isinstance(data, dict):
                data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Create hash of data
            data_hash = hashlib.sha256(data_bytes).digest()
            
            # Verify hash matches
            expected_hash = base64.b64decode(signature_info['data_hash'])
            if data_hash != expected_hash:
                return False
            
            # Verify signature with KMS
            signature = base64.b64decode(signature_info['signature'])
            
            response = self.kms.verify(
                KeyId=signature_info['key_id'],
                Message=data_hash,
                MessageType='DIGEST',
                Signature=signature,
                SigningAlgorithm=signature_info['signing_algorithm']
            )
            
            return response['SignatureValid']
            
        except ClientError as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def rotate_keys(self) -> Dict[str, Any]:
        """
        Rotate encryption keys based on policy.
        """
        try:
            rotation_results = {}
            
            # Get all AquaChain KMS keys
            response = self.kms.list_keys()
            
            for key in response['Keys']:
                key_id = key['KeyId']
                
                try:
                    # Get key details
                    key_details = self.kms.describe_key(KeyId=key_id)
                    key_metadata = key_details['KeyMetadata']
                    
                    # Check if it's an AquaChain key
                    tags_response = self.kms.list_resource_tags(KeyId=key_id)
                    tags = {tag['TagKey']: tag['TagValue'] for tag in tags_response['Tags']}
                    
                    if tags.get('Project') != 'AquaChain':
                        continue
                    
                    # Check if rotation is needed
                    creation_date = key_metadata['CreationDate']
                    days_since_creation = (datetime.now(timezone.utc) - creation_date).days
                    
                    if days_since_creation >= self.key_rotation_days:
                        # Enable automatic rotation if not already enabled
                        if key_metadata['KeyUsage'] == 'ENCRYPT_DECRYPT':
                            try:
                                self.kms.enable_key_rotation(KeyId=key_id)
                                rotation_results[key_id] = 'rotation_enabled'
                            except ClientError as e:
                                if 'UnsupportedOperationException' not in str(e):
                                    raise
                                rotation_results[key_id] = 'rotation_not_supported'
                        else:
                            rotation_results[key_id] = 'manual_rotation_required'
                    else:
                        rotation_results[key_id] = 'rotation_not_needed'
                        
                except ClientError as e:
                    logger.error(f"Error processing key {key_id}: {e}")
                    rotation_results[key_id] = f'error: {e}'
            
            logger.info(f"Key rotation check completed: {rotation_results}")
            return rotation_results
            
        except Exception as e:
            logger.error(f"Error during key rotation: {e}")
            raise KeyManagementError(f"Key rotation failed: {e}")
    
    def create_secure_backup(self, 
                           data: Dict[str, Any],
                           backup_name: str) -> Dict[str, Any]:
        """
        Create encrypted backup with integrity verification.
        """
        try:
            # Serialize data
            backup_data = json.dumps(data, sort_keys=True).encode('utf-8')
            
            # Encrypt backup data
            encrypted_backup = self.encrypt_large_data(backup_data, 'backup_data')
            
            # Create digital signature
            signature_info = self.sign_data(backup_data)
            
            # Combine encrypted data and signature
            backup_package = {
                'backup_name': backup_name,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'encrypted_data': encrypted_backup,
                'signature': signature_info,
                'metadata': {
                    'original_size': len(backup_data),
                    'compression': 'none',
                    'checksum': hashlib.sha256(backup_data).hexdigest()
                }
            }
            
            # Store backup in S3
            backup_key = f"secure-backups/{backup_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            
            self.s3.put_object(
                Bucket='aquachain-secure-backups',
                Key=backup_key,
                Body=json.dumps(backup_package),
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId='alias/aquachain-master-key',
                Metadata={
                    'backup-name': backup_name,
                    'created-at': backup_package['created_at'],
                    'data-classification': 'restricted'
                }
            )
            
            logger.info(f"Created secure backup: {backup_key}")
            
            return {
                'backup_key': backup_key,
                'backup_name': backup_name,
                'created_at': backup_package['created_at'],
                'size': len(json.dumps(backup_package))
            }
            
        except Exception as e:
            logger.error(f"Error creating secure backup: {e}")
            raise EncryptionError(f"Failed to create secure backup: {e}")
    
    def restore_secure_backup(self, backup_key: str) -> Dict[str, Any]:
        """
        Restore and verify encrypted backup.
        """
        try:
            # Retrieve backup from S3
            response = self.s3.get_object(
                Bucket='aquachain-secure-backups',
                Key=backup_key
            )
            
            backup_package = json.loads(response['Body'].read())
            
            # Decrypt backup data
            decrypted_data = self.decrypt_large_data(backup_package['encrypted_data'])
            
            # Verify signature
            signature_valid = self.verify_signature(decrypted_data, backup_package['signature'])
            
            if not signature_valid:
                raise EncryptionError("Backup signature verification failed")
            
            # Verify checksum
            actual_checksum = hashlib.sha256(decrypted_data).hexdigest()
            expected_checksum = backup_package['metadata']['checksum']
            
            if actual_checksum != expected_checksum:
                raise EncryptionError("Backup checksum verification failed")
            
            # Parse restored data
            restored_data = json.loads(decrypted_data.decode('utf-8'))
            
            logger.info(f"Successfully restored backup: {backup_key}")
            
            return {
                'data': restored_data,
                'backup_name': backup_package['backup_name'],
                'created_at': backup_package['created_at'],
                'verified': True
            }
            
        except Exception as e:
            logger.error(f"Error restoring secure backup: {e}")
            raise EncryptionError(f"Failed to restore secure backup: {e}")

class TransitEncryption:
    """
    Encryption in transit utilities.
    """
    
    @staticmethod
    def create_tls_context():
        """Create secure TLS context for HTTPS connections"""
        import ssl
        
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Disable weak ciphers
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        return context
    
    @staticmethod
    def validate_certificate_chain(hostname: str, port: int = 443) -> bool:
        """Validate SSL certificate chain"""
        import ssl
        import socket
        
        try:
            context = TransitEncryption.create_tls_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Basic certificate validation
                    if not cert:
                        return False
                    
                    # Check expiration
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    if not_after <= datetime.now():
                        return False
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Certificate validation failed for {hostname}: {e}")
            return False

# Global encryption manager instance
encryption_manager = EncryptionManager()

# Convenience functions
def encrypt_sensitive_data(data: Union[str, Dict[str, Any]], data_type: str = 'user_data') -> Dict[str, Any]:
    """Encrypt sensitive data with appropriate context"""
    return encryption_manager.encrypt_data(data, data_type)

def decrypt_sensitive_data(encrypted_data: Dict[str, Any], expected_type: str = None) -> Union[str, Dict[str, Any]]:
    """Decrypt sensitive data with type validation"""
    return encryption_manager.decrypt_data(encrypted_data, expected_type)

def create_data_signature(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Create digital signature for data integrity"""
    return encryption_manager.sign_data(data)

def verify_data_signature(data: Union[str, Dict[str, Any]], signature_info: Dict[str, Any]) -> bool:
    """Verify digital signature"""
    return encryption_manager.verify_signature(data, signature_info)