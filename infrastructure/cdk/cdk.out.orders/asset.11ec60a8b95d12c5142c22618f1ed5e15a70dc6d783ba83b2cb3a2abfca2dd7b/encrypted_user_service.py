"""
Encrypted User Management Service Example
Demonstrates integration of field-level encryption for user data.
Requirements: 11.4
"""

import json
import boto3
import os
import sys
from typing import Dict, Optional, Any
from datetime import datetime

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from encrypted_dynamodb import create_encrypted_table_client
from data_encryption_service import get_encryption_service, DataEncryptionError
from data_classification import get_field_classification, requires_encryption
from structured_logger import get_logger
from errors import ValidationError, DatabaseError

logger = get_logger(__name__, service='encrypted-user-management')


class EncryptedUserService:
    """
    User management service with automatic PII encryption.
    
    This service demonstrates how to integrate field-level encryption
    for user data containing PII (email, name, phone, address).
    """
    
    def __init__(self):
        """Initialize the encrypted user service."""
        # Use encrypted DynamoDB client for automatic encryption/decryption
        self.users_table = create_encrypted_table_client(
            os.environ.get('USERS_TABLE', 'aquachain-users')
        )
        
        # Get encryption service for validation
        self.encryption_service = get_encryption_service()
        
        # Validate encryption configuration on startup
        validation = self.encryption_service.validate_encryption_configuration()
        if not validation['valid']:
            logger.error(
                "Encryption configuration invalid",
                extra={'errors': validation['errors']}
            )
            raise Exception("Encryption not properly configured")
        
        logger.info("Encrypted user service initialized successfully")
    
    def create_user(
        self,
        user_id: str,
        email: str,
        name: str,
        phone: str,
        role: str,
        address: Optional[Dict[str, str]] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new user with automatic PII encryption.
        
        PII fields (email, name, phone, address) are automatically encrypted
        before storage using the PII KMS key.
        
        Args:
            user_id: Unique user identifier
            email: User email address (PII - will be encrypted)
            name: User full name (PII - will be encrypted)
            phone: User phone number (PII - will be encrypted)
            role: User role (INTERNAL - not encrypted)
            address: User address (PII - will be encrypted)
            organization_id: Organization ID (INTERNAL - not encrypted)
            
        Returns:
            Created user data (with PII fields encrypted in storage)
            
        Raises:
            ValidationError: If input validation fails
            DataEncryptionError: If encryption fails
            DatabaseError: If database operation fails
        """
        try:
            # Validate inputs
            if not email or '@' not in email:
                raise ValidationError("Invalid email address")
            
            if not name or len(name) < 2:
                raise ValidationError("Invalid name")
            
            if role not in ['consumer', 'technician', 'administrator']:
                raise ValidationError(f"Invalid role: {role}")
            
            # Prepare user data
            user_data = {
                'user_id': user_id,
                'email': email,  # Will be encrypted (PII)
                'name': name,  # Will be encrypted (PII)
                'phone': phone,  # Will be encrypted (PII)
                'role': role,  # Will NOT be encrypted (INTERNAL)
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Add optional fields
            if address:
                user_data['address'] = address  # Will be encrypted (PII)
            
            if organization_id:
                user_data['organization_id'] = organization_id  # Not encrypted
            
            # Store user - PII fields automatically encrypted
            self.users_table.put_item(user_data)
            
            logger.info(
                "Created user with encrypted PII",
                extra={
                    'user_id': user_id,
                    'role': role,
                    'has_address': address is not None,
                    'encrypted_fields': ['email', 'name', 'phone', 'address']
                }
            )
            
            return {
                'user_id': user_id,
                'status': 'created',
                'encrypted_fields': ['email', 'name', 'phone', 'address']
            }
            
        except ValidationError:
            raise
        except DataEncryptionError as e:
            logger.error(f"Failed to encrypt user data: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user with automatic PII decryption.
        
        PII fields are automatically decrypted when retrieved from storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data with decrypted PII fields, or None if not found
        """
        try:
            # Get user - PII fields automatically decrypted
            user = self.users_table.get_item({'user_id': user_id})
            
            if not user:
                logger.info(f"User not found: {user_id}")
                return None
            
            logger.info(
                "Retrieved user with decrypted PII",
                extra={
                    'user_id': user_id,
                    'role': user.get('role'),
                    'decrypted_fields': ['email', 'name', 'phone', 'address']
                }
            )
            
            return user
            
        except DataEncryptionError as e:
            logger.error(f"Failed to decrypt user data: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user fields with automatic encryption for PII.
        
        Args:
            user_id: User identifier
            updates: Dictionary of fields to update
            
        Returns:
            Update result
        """
        try:
            # Build update expression
            update_parts = []
            expression_values = {}
            
            for field, value in updates.items():
                update_parts.append(f"{field} = :{field}")
                expression_values[f":{field}"] = value
            
            # Add updated_at timestamp
            update_parts.append("updated_at = :updated_at")
            expression_values[":updated_at"] = datetime.utcnow().isoformat()
            
            update_expression = "SET " + ", ".join(update_parts)
            
            # Update user - PII fields automatically encrypted
            self.users_table.update_item(
                key={'user_id': user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_values
            )
            
            # Determine which fields were encrypted
            encrypted_fields = [
                field for field in updates.keys()
                if requires_encryption(field)
            ]
            
            logger.info(
                "Updated user with encrypted PII",
                extra={
                    'user_id': user_id,
                    'updated_fields': list(updates.keys()),
                    'encrypted_fields': encrypted_fields
                }
            )
            
            return {
                'user_id': user_id,
                'status': 'updated',
                'updated_fields': list(updates.keys()),
                'encrypted_fields': encrypted_fields
            }
            
        except DataEncryptionError as e:
            logger.error(f"Failed to encrypt update data: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def list_users_by_organization(
        self,
        organization_id: str
    ) -> list[Dict[str, Any]]:
        """
        List users in an organization with automatic PII decryption.
        
        Args:
            organization_id: Organization identifier
            
        Returns:
            List of users with decrypted PII fields
        """
        try:
            from boto3.dynamodb.conditions import Key
            
            # Query users - PII fields automatically decrypted
            users = self.users_table.query(
                key_condition_expression=Key('organization_id').eq(organization_id)
            )
            
            logger.info(
                "Listed users with decrypted PII",
                extra={
                    'organization_id': organization_id,
                    'user_count': len(users)
                }
            )
            
            return users
            
        except DataEncryptionError as e:
            logger.error(f"Failed to decrypt user data: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete user (for GDPR compliance).
        
        Args:
            user_id: User identifier
            
        Returns:
            Deletion result
        """
        try:
            # Delete user
            self.users_table.delete_item({'user_id': user_id})
            
            logger.info(
                "Deleted user",
                extra={'user_id': user_id}
            )
            
            return {
                'user_id': user_id,
                'status': 'deleted'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def get_encryption_metadata(self, field_name: str) -> Dict[str, Any]:
        """
        Get encryption metadata for a field (for debugging/auditing).
        
        Args:
            field_name: Name of the field
            
        Returns:
            Encryption metadata
        """
        return self.encryption_service.get_encryption_metadata(field_name)


# Lambda handler example
def lambda_handler(event, context):
    """
    Lambda handler for user management operations with encryption.
    """
    try:
        # Initialize service
        service = EncryptedUserService()
        
        # Parse request
        http_method = event.get('httpMethod')
        path = event.get('path')
        body = json.loads(event.get('body', '{}'))
        
        # Route to appropriate handler
        if http_method == 'POST' and path == '/users':
            # Create user
            result = service.create_user(
                user_id=body['user_id'],
                email=body['email'],
                name=body['name'],
                phone=body['phone'],
                role=body['role'],
                address=body.get('address'),
                organization_id=body.get('organization_id')
            )
            
            return {
                'statusCode': 201,
                'body': json.dumps(result)
            }
        
        elif http_method == 'GET' and '/users/' in path:
            # Get user
            user_id = path.split('/')[-1]
            user = service.get_user(user_id)
            
            if not user:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'User not found'})
                }
            
            return {
                'statusCode': 200,
                'body': json.dumps(user)
            }
        
        elif http_method == 'PUT' and '/users/' in path:
            # Update user
            user_id = path.split('/')[-1]
            result = service.update_user(user_id, body)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        elif http_method == 'DELETE' and '/users/' in path:
            # Delete user
            user_id = path.split('/')[-1]
            result = service.delete_user(user_id)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    
    except DataEncryptionError as e:
        logger.error(f"Encryption error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Encryption error'})
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
