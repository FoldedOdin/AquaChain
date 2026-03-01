"""
Encrypted DynamoDB Helper for AquaChain System.
Provides transparent field-level encryption for DynamoDB operations.
Requirements: 11.4
"""

import boto3
from typing import Any, Dict, List, Optional
from boto3.dynamodb.conditions import Key, Attr

from data_encryption_service import get_encryption_service, DataEncryptionError
from data_classification import requires_encryption
from structured_logger import get_logger

logger = get_logger(__name__, service='encrypted-dynamodb')


class EncryptedDynamoDBClient:
    """
    DynamoDB client wrapper that automatically encrypts/decrypts fields
    based on data classification schema.
    """
    
    def __init__(self, table_name: str, region: str = None):
        """
        Initialize the encrypted DynamoDB client.
        
        Args:
            table_name: Name of the DynamoDB table
            region: AWS region (optional)
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.encryption_service = get_encryption_service()
    
    def put_item(self, item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Put an item into DynamoDB with automatic field encryption.
        
        Args:
            item: Item to store
            **kwargs: Additional arguments for put_item
            
        Returns:
            Response from DynamoDB
        """
        try:
            # Encrypt fields that require encryption
            encrypted_item = self.encryption_service.encrypt_fields_in_record(item)
            
            # Store in DynamoDB
            response = self.table.put_item(Item=encrypted_item, **kwargs)
            
            logger.debug(
                f"Stored encrypted item in {self.table_name}",
                extra={'item_keys': list(item.keys())}
            )
            
            return response
            
        except DataEncryptionError as e:
            logger.error(f"Encryption failed during put_item: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to put item: {e}")
            raise
    
    def get_item(self, key: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB with automatic field decryption.
        
        Args:
            key: Primary key of the item
            **kwargs: Additional arguments for get_item
            
        Returns:
            Decrypted item or None if not found
        """
        try:
            # Get from DynamoDB
            response = self.table.get_item(Key=key, **kwargs)
            
            if 'Item' not in response:
                return None
            
            # Decrypt fields that were encrypted
            decrypted_item = self.encryption_service.decrypt_fields_in_record(response['Item'])
            
            logger.debug(
                f"Retrieved and decrypted item from {self.table_name}",
                extra={'key': key}
            )
            
            return decrypted_item
            
        except DataEncryptionError as e:
            logger.error(f"Decryption failed during get_item: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get item: {e}")
            raise
    
    def update_item(
        self, 
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an item in DynamoDB with automatic field encryption.
        
        Args:
            key: Primary key of the item
            update_expression: DynamoDB update expression
            expression_attribute_values: Values for the update expression
            **kwargs: Additional arguments for update_item
            
        Returns:
            Response from DynamoDB
        """
        try:
            # Encrypt values that require encryption
            encrypted_values = {}
            for attr_name, value in expression_attribute_values.items():
                # Extract field name from attribute placeholder (e.g., ':email' -> 'email')
                field_name = attr_name.lstrip(':')
                
                if requires_encryption(field_name):
                    encrypted_values[attr_name] = self.encryption_service.encrypt_field(
                        field_name, value
                    )
                else:
                    encrypted_values[attr_name] = value
            
            # Update in DynamoDB
            response = self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=encrypted_values,
                **kwargs
            )
            
            logger.debug(
                f"Updated item in {self.table_name}",
                extra={'key': key, 'updated_fields': list(expression_attribute_values.keys())}
            )
            
            return response
            
        except DataEncryptionError as e:
            logger.error(f"Encryption failed during update_item: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update item: {e}")
            raise
    
    def query(
        self,
        key_condition_expression: Any,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query DynamoDB with automatic field decryption.
        
        Args:
            key_condition_expression: Key condition for the query
            **kwargs: Additional arguments for query
            
        Returns:
            List of decrypted items
        """
        try:
            # Query DynamoDB
            response = self.table.query(
                KeyConditionExpression=key_condition_expression,
                **kwargs
            )
            
            # Decrypt all items
            decrypted_items = []
            for item in response.get('Items', []):
                decrypted_item = self.encryption_service.decrypt_fields_in_record(item)
                decrypted_items.append(decrypted_item)
            
            logger.debug(
                f"Queried and decrypted {len(decrypted_items)} items from {self.table_name}"
            )
            
            return decrypted_items
            
        except DataEncryptionError as e:
            logger.error(f"Decryption failed during query: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to query items: {e}")
            raise
    
    def scan(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scan DynamoDB with automatic field decryption.
        
        Args:
            **kwargs: Arguments for scan
            
        Returns:
            List of decrypted items
        """
        try:
            # Scan DynamoDB
            response = self.table.scan(**kwargs)
            
            # Decrypt all items
            decrypted_items = []
            for item in response.get('Items', []):
                decrypted_item = self.encryption_service.decrypt_fields_in_record(item)
                decrypted_items.append(decrypted_item)
            
            logger.debug(
                f"Scanned and decrypted {len(decrypted_items)} items from {self.table_name}"
            )
            
            return decrypted_items
            
        except DataEncryptionError as e:
            logger.error(f"Decryption failed during scan: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to scan items: {e}")
            raise
    
    def batch_write_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch write items to DynamoDB with automatic field encryption.
        
        Args:
            items: List of items to write
            
        Returns:
            Response from batch write
        """
        try:
            # Encrypt all items
            encrypted_items = []
            for item in items:
                encrypted_item = self.encryption_service.encrypt_fields_in_record(item)
                encrypted_items.append(encrypted_item)
            
            # Batch write to DynamoDB
            with self.table.batch_writer() as batch:
                for encrypted_item in encrypted_items:
                    batch.put_item(Item=encrypted_item)
            
            logger.info(
                f"Batch wrote {len(items)} encrypted items to {self.table_name}"
            )
            
            return {'success': True, 'count': len(items)}
            
        except DataEncryptionError as e:
            logger.error(f"Encryption failed during batch_write: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to batch write items: {e}")
            raise
    
    def delete_item(self, key: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Delete an item from DynamoDB.
        
        Args:
            key: Primary key of the item
            **kwargs: Additional arguments for delete_item
            
        Returns:
            Response from DynamoDB
        """
        try:
            response = self.table.delete_item(Key=key, **kwargs)
            
            logger.debug(
                f"Deleted item from {self.table_name}",
                extra={'key': key}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to delete item: {e}")
            raise


def create_encrypted_table_client(table_name: str, region: str = None) -> EncryptedDynamoDBClient:
    """
    Factory function to create an encrypted DynamoDB client.
    
    Args:
        table_name: Name of the DynamoDB table
        region: AWS region (optional)
        
    Returns:
        EncryptedDynamoDBClient instance
    """
    return EncryptedDynamoDBClient(table_name, region)


# Example usage patterns
"""
# Example 1: Storing user data with PII encryption
users_table = create_encrypted_table_client('Users')

user_data = {
    'user_id': 'user-123',
    'email': 'john.doe@example.com',  # Will be encrypted (PII)
    'name': 'John Doe',  # Will be encrypted (PII)
    'phone': '+1234567890',  # Will be encrypted (PII)
    'role': 'admin',  # Will NOT be encrypted (INTERNAL)
    'created_at': '2025-10-25T12:00:00Z'  # Will NOT be encrypted (INTERNAL)
}

# Put item - email, name, phone will be automatically encrypted
users_table.put_item(user_data)

# Get item - encrypted fields will be automatically decrypted
retrieved_user = users_table.get_item({'user_id': 'user-123'})
print(retrieved_user['email'])  # Decrypted value


# Example 2: Storing device data with SENSITIVE encryption
devices_table = create_encrypted_table_client('Devices')

device_data = {
    'device_id': 'device-456',
    'device_name': 'Water Sensor #1',  # Will NOT be encrypted (INTERNAL)
    'serial_number': 'SN123456789',  # Will be encrypted (SENSITIVE)
    'mac_address': '00:11:22:33:44:55',  # Will be encrypted (SENSITIVE)
    'location': {'lat': 37.7749, 'lon': -122.4194},  # Will be encrypted (SENSITIVE)
    'status': 'active'  # Will NOT be encrypted (INTERNAL)
}

# Put item - serial_number, mac_address, location will be automatically encrypted
devices_table.put_item(device_data)


# Example 3: Updating encrypted fields
users_table.update_item(
    key={'user_id': 'user-123'},
    update_expression='SET email = :email, phone = :phone',
    expression_attribute_values={
        ':email': 'new.email@example.com',  # Will be automatically encrypted
        ':phone': '+9876543210'  # Will be automatically encrypted
    }
)


# Example 4: Querying with decryption
users = users_table.query(
    key_condition_expression=Key('organization_id').eq('org-789')
)
# All returned users will have their PII fields decrypted
for user in users:
    print(f"User: {user['name']}, Email: {user['email']}")
"""
