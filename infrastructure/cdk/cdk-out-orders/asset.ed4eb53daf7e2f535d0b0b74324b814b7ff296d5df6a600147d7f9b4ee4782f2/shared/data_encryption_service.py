"""
Data Encryption Service for AquaChain System.
Implements field-level encryption based on data classification schema.
Requirements: 11.4
"""

import boto3
import base64
import json
import os
from typing import Any, Dict, Optional, Union
from botocore.exceptions import ClientError

from data_classification import (
    DataClassification,
    get_field_classification,
    requires_encryption,
    FIELD_CLASSIFICATIONS
)
from structured_logger import get_logger

logger = get_logger(__name__, service='data-encryption-service')


class DataEncryptionError(Exception):
    """Exception raised for data encryption errors."""
    pass


class DataEncryptionService:
    """
    Service for encrypting and decrypting data based on classification levels.
    
    Uses AWS KMS with separate keys for PII and SENSITIVE data.
    PUBLIC and INTERNAL data are not encrypted.
    """
    
    def __init__(self, region: str = None):
        """
        Initialize the DataEncryptionService.
        
        Args:
            region: AWS region (defaults to environment variable or us-east-1)
        """
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.kms = boto3.client('kms', region_name=self.region)
        
        # Get KMS key IDs from environment variables
        self.pii_key_id = os.environ.get('PII_KMS_KEY_ID')
        self.sensitive_key_id = os.environ.get('SENSITIVE_KMS_KEY_ID')
        
        # Validate key configuration
        if not self.pii_key_id:
            logger.warning("PII_KMS_KEY_ID not configured - PII encryption will fail")
        if not self.sensitive_key_id:
            logger.warning("SENSITIVE_KMS_KEY_ID not configured - SENSITIVE encryption will fail")
        
        # Cache for encryption contexts
        self._encryption_contexts = {
            DataClassification.PII: {
                'DataClassification': 'PII',
                'ComplianceRequirement': 'GDPR',
                'Service': 'AquaChain'
            },
            DataClassification.SENSITIVE: {
                'DataClassification': 'SENSITIVE',
                'ComplianceRequirement': 'BusinessCritical',
                'Service': 'AquaChain'
            }
        }
    
    def encrypt_field(self, field_name: str, value: Any) -> Union[str, Any]:
        """
        Encrypt a field value based on its classification.
        
        Args:
            field_name: Name of the field to encrypt
            value: Value to encrypt
            
        Returns:
            Encrypted value (base64 encoded) if encryption required, original value otherwise
            
        Raises:
            DataEncryptionError: If encryption fails
        """
        # Handle None values
        if value is None:
            return None
        
        # Get field classification
        classification = get_field_classification(field_name)
        
        # Only encrypt PII and SENSITIVE data
        if classification not in [DataClassification.PII, DataClassification.SENSITIVE]:
            return value
        
        try:
            # Convert value to string if necessary
            if isinstance(value, (dict, list)):
                plaintext = json.dumps(value)
            else:
                plaintext = str(value)
            
            # Get appropriate KMS key
            key_id = self._get_key_id_for_classification(classification)
            if not key_id:
                logger.error(f"No KMS key configured for {classification.value} data")
                raise DataEncryptionError(f"KMS key not configured for {classification.value}")
            
            # Get encryption context
            encryption_context = self._encryption_contexts[classification].copy()
            encryption_context['FieldName'] = field_name
            
            # Encrypt with KMS
            response = self.kms.encrypt(
                KeyId=key_id,
                Plaintext=plaintext.encode('utf-8'),
                EncryptionContext=encryption_context
            )
            
            # Return base64 encoded ciphertext
            encrypted_value = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
            
            logger.debug(
                f"Encrypted field",
                extra={
                    'field_name': field_name,
                    'classification': classification.value,
                    'key_id': key_id
                }
            )
            
            return encrypted_value
            
        except ClientError as e:
            logger.error(
                f"KMS encryption failed for field {field_name}",
                extra={'error': str(e), 'classification': classification.value}
            )
            raise DataEncryptionError(f"Failed to encrypt {field_name}: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error encrypting field {field_name}",
                extra={'error': str(e)}
            )
            raise DataEncryptionError(f"Unexpected encryption error for {field_name}: {str(e)}")
    
    def decrypt_field(self, field_name: str, encrypted_value: Any) -> Union[str, Any]:
        """
        Decrypt a field value based on its classification.
        
        Args:
            field_name: Name of the field to decrypt
            encrypted_value: Encrypted value (base64 encoded)
            
        Returns:
            Decrypted value if encryption was used, original value otherwise
            
        Raises:
            DataEncryptionError: If decryption fails
        """
        # Handle None values
        if encrypted_value is None:
            return None
        
        # Get field classification
        classification = get_field_classification(field_name)
        
        # Only decrypt PII and SENSITIVE data
        if classification not in [DataClassification.PII, DataClassification.SENSITIVE]:
            return encrypted_value
        
        try:
            # Decode base64
            ciphertext_blob = base64.b64decode(encrypted_value)
            
            # Get encryption context for validation
            encryption_context = self._encryption_contexts[classification].copy()
            encryption_context['FieldName'] = field_name
            
            # Decrypt with KMS
            response = self.kms.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionContext=encryption_context
            )
            
            # Decode plaintext
            plaintext = response['Plaintext'].decode('utf-8')
            
            # Try to parse as JSON if it looks like JSON
            if plaintext.startswith('{') or plaintext.startswith('['):
                try:
                    return json.loads(plaintext)
                except json.JSONDecodeError:
                    pass
            
            logger.debug(
                f"Decrypted field",
                extra={
                    'field_name': field_name,
                    'classification': classification.value
                }
            )
            
            return plaintext
            
        except ClientError as e:
            logger.error(
                f"KMS decryption failed for field {field_name}",
                extra={'error': str(e), 'classification': classification.value}
            )
            raise DataEncryptionError(f"Failed to decrypt {field_name}: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error decrypting field {field_name}",
                extra={'error': str(e)}
            )
            raise DataEncryptionError(f"Unexpected decryption error for {field_name}: {str(e)}")
    
    def encrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt all fields in a record that require encryption.
        
        Args:
            record: Dictionary containing field names and values
            
        Returns:
            Dictionary with encrypted fields
            
        Raises:
            DataEncryptionError: If encryption fails for any field
        """
        encrypted_record = {}
        
        for field_name, value in record.items():
            try:
                encrypted_record[field_name] = self.encrypt_field(field_name, value)
            except DataEncryptionError as e:
                logger.error(f"Failed to encrypt record field {field_name}: {e}")
                raise
        
        return encrypted_record
    
    def decrypt_record(self, encrypted_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt all encrypted fields in a record.
        
        Args:
            encrypted_record: Dictionary containing field names and encrypted values
            
        Returns:
            Dictionary with decrypted fields
            
        Raises:
            DataEncryptionError: If decryption fails for any field
        """
        decrypted_record = {}
        
        for field_name, encrypted_value in encrypted_record.items():
            try:
                decrypted_record[field_name] = self.decrypt_field(field_name, encrypted_value)
            except DataEncryptionError as e:
                logger.error(f"Failed to decrypt record field {field_name}: {e}")
                raise
        
        return decrypted_record
    
    def encrypt_fields_in_record(
        self, 
        record: Dict[str, Any], 
        fields_to_encrypt: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in a record, leaving others unchanged.
        
        Args:
            record: Dictionary containing field names and values
            fields_to_encrypt: List of field names to encrypt (if None, encrypts all that require it)
            
        Returns:
            Dictionary with specified fields encrypted
        """
        result = record.copy()
        
        # Determine which fields to encrypt
        if fields_to_encrypt is None:
            # Encrypt all fields that require encryption
            fields_to_encrypt = [
                field for field in record.keys()
                if requires_encryption(field)
            ]
        
        # Encrypt specified fields
        for field_name in fields_to_encrypt:
            if field_name in result:
                try:
                    result[field_name] = self.encrypt_field(field_name, result[field_name])
                except DataEncryptionError as e:
                    logger.warning(f"Failed to encrypt field {field_name}: {e}")
                    # Continue with other fields
        
        return result
    
    def decrypt_fields_in_record(
        self, 
        record: Dict[str, Any], 
        fields_to_decrypt: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Decrypt specific fields in a record, leaving others unchanged.
        
        Args:
            record: Dictionary containing field names and encrypted values
            fields_to_decrypt: List of field names to decrypt (if None, decrypts all that require it)
            
        Returns:
            Dictionary with specified fields decrypted
        """
        result = record.copy()
        
        # Determine which fields to decrypt
        if fields_to_decrypt is None:
            # Decrypt all fields that require encryption
            fields_to_decrypt = [
                field for field in record.keys()
                if requires_encryption(field)
            ]
        
        # Decrypt specified fields
        for field_name in fields_to_decrypt:
            if field_name in result:
                try:
                    result[field_name] = self.decrypt_field(field_name, result[field_name])
                except DataEncryptionError as e:
                    logger.warning(f"Failed to decrypt field {field_name}: {e}")
                    # Continue with other fields
        
        return result
    
    def _get_key_id_for_classification(self, classification: DataClassification) -> Optional[str]:
        """
        Get the appropriate KMS key ID for a data classification.
        
        Args:
            classification: Data classification level
            
        Returns:
            KMS key ID or None if not configured
        """
        if classification == DataClassification.PII:
            return self.pii_key_id
        elif classification == DataClassification.SENSITIVE:
            return self.sensitive_key_id
        else:
            return None
    
    def get_encryption_metadata(self, field_name: str) -> Dict[str, Any]:
        """
        Get encryption metadata for a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Dictionary containing encryption metadata
        """
        classification = get_field_classification(field_name)
        needs_encryption = requires_encryption(field_name)
        
        metadata = {
            'field_name': field_name,
            'classification': classification.value,
            'requires_encryption': needs_encryption,
            'encryption_algorithm': 'AES-256-GCM' if needs_encryption else None,
            'key_type': None
        }
        
        if needs_encryption:
            if classification == DataClassification.PII:
                metadata['key_type'] = 'PII_KMS_KEY'
                metadata['key_id'] = self.pii_key_id
            elif classification == DataClassification.SENSITIVE:
                metadata['key_type'] = 'SENSITIVE_KMS_KEY'
                metadata['key_id'] = self.sensitive_key_id
        
        return metadata
    
    def validate_encryption_configuration(self) -> Dict[str, Any]:
        """
        Validate that encryption is properly configured.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check PII key configuration
        if not self.pii_key_id:
            validation_results['valid'] = False
            validation_results['errors'].append('PII_KMS_KEY_ID not configured')
        else:
            try:
                # Test key access
                self.kms.describe_key(KeyId=self.pii_key_id)
            except ClientError as e:
                validation_results['valid'] = False
                validation_results['errors'].append(f'PII key not accessible: {str(e)}')
        
        # Check SENSITIVE key configuration
        if not self.sensitive_key_id:
            validation_results['valid'] = False
            validation_results['errors'].append('SENSITIVE_KMS_KEY_ID not configured')
        else:
            try:
                # Test key access
                self.kms.describe_key(KeyId=self.sensitive_key_id)
            except ClientError as e:
                validation_results['valid'] = False
                validation_results['errors'].append(f'SENSITIVE key not accessible: {str(e)}')
        
        # Check for fields requiring encryption
        pii_fields = [f for f, c in FIELD_CLASSIFICATIONS.items() if c == DataClassification.PII]
        sensitive_fields = [f for f, c in FIELD_CLASSIFICATIONS.items() if c == DataClassification.SENSITIVE]
        
        validation_results['pii_fields_count'] = len(pii_fields)
        validation_results['sensitive_fields_count'] = len(sensitive_fields)
        
        if len(pii_fields) == 0:
            validation_results['warnings'].append('No PII fields defined')
        
        if len(sensitive_fields) == 0:
            validation_results['warnings'].append('No SENSITIVE fields defined')
        
        return validation_results


# Global instance for convenience
_encryption_service: Optional[DataEncryptionService] = None


def get_encryption_service() -> DataEncryptionService:
    """
    Get or create the global DataEncryptionService instance.
    
    Returns:
        DataEncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = DataEncryptionService()
    return _encryption_service


# Convenience functions
def encrypt_field(field_name: str, value: Any) -> Union[str, Any]:
    """Encrypt a field value based on its classification."""
    return get_encryption_service().encrypt_field(field_name, value)


def decrypt_field(field_name: str, encrypted_value: Any) -> Union[str, Any]:
    """Decrypt a field value based on its classification."""
    return get_encryption_service().decrypt_field(field_name, encrypted_value)


def encrypt_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt all fields in a record that require encryption."""
    return get_encryption_service().encrypt_record(record)


def decrypt_record(encrypted_record: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt all encrypted fields in a record."""
    return get_encryption_service().decrypt_record(encrypted_record)
