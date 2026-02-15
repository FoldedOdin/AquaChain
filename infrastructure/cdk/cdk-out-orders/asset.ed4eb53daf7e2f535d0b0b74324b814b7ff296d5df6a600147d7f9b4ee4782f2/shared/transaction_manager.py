"""
AquaChain Transaction Manager - Dashboard Overhaul
Provides transactional consistency for multi-table operations using DynamoDB transactions,
optimistic concurrency control, and proper rollback mechanisms.

Requirements: 8.5, 8.7
"""

import boto3
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import logging
from contextlib import contextmanager

# Initialize logger
logger = logging.getLogger(__name__)

# AWS clients
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')


class TransactionError(Exception):
    """Custom exception for transaction errors"""
    pass


class ConcurrencyError(TransactionError):
    """Exception for concurrent access conflicts"""
    pass


class TransactionManager:
    """
    Manages DynamoDB transactions with optimistic concurrency control and rollback capabilities.
    
    Features:
    - Atomic multi-table operations using DynamoDB transactions
    - Optimistic concurrency control with version checking
    - Automatic retry with exponential backoff for transient failures
    - Comprehensive audit logging for all transaction operations
    - Rollback mechanisms for failed operations
    - Transaction isolation and consistency guarantees
    """
    
    def __init__(self, correlation_id: Optional[str] = None):
        """
        Initialize transaction manager
        
        Args:
            correlation_id: Optional correlation ID for audit logging
        """
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.max_retries = 3
        self.base_delay = 0.1  # 100ms base delay for exponential backoff
        
    def execute_transaction(self, operations: List[Dict], idempotency_key: Optional[str] = None) -> Dict:
        """
        Execute a DynamoDB transaction with multiple operations atomically
        
        Args:
            operations: List of transaction operations (Put, Update, Delete, ConditionCheck)
            idempotency_key: Optional idempotency key to prevent duplicate transactions
            
        Returns:
            Transaction result with operation details
            
        Raises:
            TransactionError: If transaction fails
            ConcurrencyError: If concurrent access conflict occurs
        """
        try:
            # Validate operations
            self._validate_operations(operations)
            
            # Check idempotency if key provided
            if idempotency_key and self._is_duplicate_transaction(idempotency_key):
                logger.info(
                    "Duplicate transaction detected, returning cached result",
                    idempotency_key=idempotency_key,
                    correlation_id=self.correlation_id
                )
                return self._get_cached_transaction_result(idempotency_key)
            
            # Prepare transaction items
            transaction_items = self._prepare_transaction_items(operations)
            
            # Execute transaction with retry logic
            result = self._execute_with_retry(transaction_items)
            
            # Cache result if idempotency key provided
            if idempotency_key:
                self._cache_transaction_result(idempotency_key, result)
            
            logger.info(
                "Transaction executed successfully",
                operation_count=len(operations),
                correlation_id=self.correlation_id,
                idempotency_key=idempotency_key
            )
            
            return result
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'TransactionCanceledException':
                # Handle specific cancellation reasons
                cancellation_reasons = e.response['Error'].get('CancellationReasons', [])
                self._handle_transaction_cancellation(cancellation_reasons)
                
            elif error_code == 'ValidationException':
                raise TransactionError(f"Transaction validation failed: {e.response['Error']['Message']}")
                
            else:
                raise TransactionError(f"Transaction failed: {e.response['Error']['Message']}")
                
        except Exception as e:
            logger.error(
                "Unexpected error during transaction execution",
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise TransactionError(f"Transaction execution failed: {str(e)}")
    
    def create_put_operation(self, table_name: str, item: Dict, condition_expression: Optional[str] = None) -> Dict:
        """
        Create a Put operation for transaction
        
        Args:
            table_name: DynamoDB table name
            item: Item to put
            condition_expression: Optional condition for the put operation
            
        Returns:
            Put operation dictionary
        """
        # Add version and timestamp for optimistic concurrency
        enhanced_item = item.copy()
        enhanced_item['version'] = enhanced_item.get('version', 0) + 1
        enhanced_item['lastModified'] = datetime.utcnow().isoformat() + 'Z'
        enhanced_item['transactionId'] = self.correlation_id
        
        operation = {
            'Put': {
                'TableName': table_name,
                'Item': self._serialize_item(enhanced_item)
            }
        }
        
        if condition_expression:
            operation['Put']['ConditionExpression'] = condition_expression
            
        return operation
    
    def create_update_operation(self, table_name: str, key: Dict, update_expression: str, 
                              expression_attribute_values: Dict, expression_attribute_names: Optional[Dict] = None,
                              condition_expression: Optional[str] = None, expected_version: Optional[int] = None) -> Dict:
        """
        Create an Update operation for transaction with optimistic concurrency control
        
        Args:
            table_name: DynamoDB table name
            key: Primary key of item to update
            update_expression: DynamoDB update expression
            expression_attribute_values: Values for update expression
            expression_attribute_names: Optional names for update expression
            condition_expression: Optional condition for the update
            expected_version: Expected version for optimistic concurrency control
            
        Returns:
            Update operation dictionary
        """
        # Add version increment and timestamp to update expression
        enhanced_update_expression = f"{update_expression}, #version = #version + :version_inc, #lastModified = :timestamp, #transactionId = :txn_id"
        
        enhanced_values = expression_attribute_values.copy()
        enhanced_values[':version_inc'] = 1
        enhanced_values[':timestamp'] = datetime.utcnow().isoformat() + 'Z'
        enhanced_values[':txn_id'] = self.correlation_id
        
        enhanced_names = expression_attribute_names.copy() if expression_attribute_names else {}
        enhanced_names['#version'] = 'version'
        enhanced_names['#lastModified'] = 'lastModified'
        enhanced_names['#transactionId'] = 'transactionId'
        
        # Add version check for optimistic concurrency
        if expected_version is not None:
            version_condition = "#version = :expected_version"
            enhanced_values[':expected_version'] = expected_version
            
            if condition_expression:
                condition_expression = f"({condition_expression}) AND {version_condition}"
            else:
                condition_expression = version_condition
        
        operation = {
            'Update': {
                'TableName': table_name,
                'Key': self._serialize_item(key),
                'UpdateExpression': enhanced_update_expression,
                'ExpressionAttributeValues': self._serialize_item(enhanced_values),
                'ExpressionAttributeNames': enhanced_names
            }
        }
        
        if condition_expression:
            operation['Update']['ConditionExpression'] = condition_expression
            
        return operation
    
    def create_delete_operation(self, table_name: str, key: Dict, condition_expression: Optional[str] = None,
                              expected_version: Optional[int] = None) -> Dict:
        """
        Create a Delete operation for transaction
        
        Args:
            table_name: DynamoDB table name
            key: Primary key of item to delete
            condition_expression: Optional condition for the delete
            expected_version: Expected version for optimistic concurrency control
            
        Returns:
            Delete operation dictionary
        """
        operation = {
            'Delete': {
                'TableName': table_name,
                'Key': self._serialize_item(key)
            }
        }
        
        # Add version check for optimistic concurrency
        if expected_version is not None:
            version_condition = "#version = :expected_version"
            
            if condition_expression:
                condition_expression = f"({condition_expression}) AND {version_condition}"
            else:
                condition_expression = version_condition
                
            operation['Delete']['ConditionExpression'] = condition_expression
            operation['Delete']['ExpressionAttributeNames'] = {'#version': 'version'}
            operation['Delete']['ExpressionAttributeValues'] = self._serialize_item({':expected_version': expected_version})
        elif condition_expression:
            operation['Delete']['ConditionExpression'] = condition_expression
            
        return operation
    
    def create_condition_check(self, table_name: str, key: Dict, condition_expression: str,
                             expression_attribute_values: Optional[Dict] = None,
                             expression_attribute_names: Optional[Dict] = None) -> Dict:
        """
        Create a ConditionCheck operation for transaction
        
        Args:
            table_name: DynamoDB table name
            key: Primary key of item to check
            condition_expression: Condition expression to evaluate
            expression_attribute_values: Optional values for condition expression
            expression_attribute_names: Optional names for condition expression
            
        Returns:
            ConditionCheck operation dictionary
        """
        operation = {
            'ConditionCheck': {
                'TableName': table_name,
                'Key': self._serialize_item(key),
                'ConditionExpression': condition_expression
            }
        }
        
        if expression_attribute_values:
            operation['ConditionCheck']['ExpressionAttributeValues'] = self._serialize_item(expression_attribute_values)
            
        if expression_attribute_names:
            operation['ConditionCheck']['ExpressionAttributeNames'] = expression_attribute_names
            
        return operation
    
    @contextmanager
    def transaction_context(self, idempotency_key: Optional[str] = None):
        """
        Context manager for building and executing transactions
        
        Args:
            idempotency_key: Optional idempotency key
            
        Yields:
            Transaction builder instance
        """
        builder = TransactionBuilder(self, idempotency_key)
        try:
            yield builder
            # Execute transaction when context exits
            if builder.operations:
                result = self.execute_transaction(builder.operations, idempotency_key)
                builder.result = result
        except Exception as e:
            logger.error(
                "Transaction context failed",
                error=str(e),
                correlation_id=self.correlation_id
            )
            raise
    
    def _validate_operations(self, operations: List[Dict]) -> None:
        """Validate transaction operations"""
        if not operations:
            raise TransactionError("Transaction must contain at least one operation")
            
        if len(operations) > 25:  # DynamoDB transaction limit
            raise TransactionError("Transaction cannot contain more than 25 operations")
            
        for i, operation in enumerate(operations):
            if not any(key in operation for key in ['Put', 'Update', 'Delete', 'ConditionCheck']):
                raise TransactionError(f"Invalid operation at index {i}: must be Put, Update, Delete, or ConditionCheck")
    
    def _prepare_transaction_items(self, operations: List[Dict]) -> List[Dict]:
        """Prepare transaction items for DynamoDB"""
        return operations
    
    def _execute_with_retry(self, transaction_items: List[Dict]) -> Dict:
        """Execute transaction with exponential backoff retry"""
        import time
        import random
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = dynamodb_client.transact_write_items(TransactItems=transaction_items)
                
                return {
                    'success': True,
                    'response': response,
                    'attempts': attempt + 1,
                    'correlation_id': self.correlation_id
                }
                
            except ClientError as e:
                last_exception = e
                error_code = e.response['Error']['Code']
                
                # Don't retry certain errors
                if error_code in ['ValidationException', 'TransactionCanceledException']:
                    raise
                
                # Retry transient errors
                if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException', 'InternalServerError']:
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                        logger.warning(
                            f"Transaction attempt {attempt + 1} failed, retrying in {delay:.2f}s",
                            error_code=error_code,
                            correlation_id=self.correlation_id
                        )
                        time.sleep(delay)
                        continue
                
                raise
        
        # If we get here, all retries failed
        raise last_exception
    
    def _handle_transaction_cancellation(self, cancellation_reasons: List[Dict]) -> None:
        """Handle transaction cancellation reasons"""
        for i, reason in enumerate(cancellation_reasons):
            code = reason.get('Code')
            message = reason.get('Message', '')
            
            if code == 'ConditionalCheckFailed':
                raise ConcurrencyError(f"Concurrent modification detected at operation {i}: {message}")
            elif code == 'ValidationError':
                raise TransactionError(f"Validation error at operation {i}: {message}")
            elif code == 'DuplicateTransaction':
                raise TransactionError(f"Duplicate transaction detected at operation {i}")
            else:
                raise TransactionError(f"Transaction cancelled at operation {i}: {code} - {message}")
    
    def _serialize_item(self, item: Dict) -> Dict:
        """Serialize item for DynamoDB, handling Decimal conversion"""
        def convert_value(value):
            if isinstance(value, Decimal):
                return value
            elif isinstance(value, float):
                return Decimal(str(value))
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(v) for v in value]
            else:
                return value
        
        return {k: convert_value(v) for k, v in item.items()}
    
    def _is_duplicate_transaction(self, idempotency_key: str) -> bool:
        """Check if transaction with idempotency key already exists"""
        # Implementation would check a dedicated idempotency table
        # For now, return False (no duplicate detection)
        return False
    
    def _get_cached_transaction_result(self, idempotency_key: str) -> Dict:
        """Get cached transaction result for idempotency"""
        # Implementation would retrieve from idempotency table
        # For now, return empty result
        return {'success': True, 'cached': True}
    
    def _cache_transaction_result(self, idempotency_key: str, result: Dict) -> None:
        """Cache transaction result for idempotency"""
        # Implementation would store in idempotency table
        pass


class TransactionBuilder:
    """Helper class for building transactions using context manager"""
    
    def __init__(self, transaction_manager: TransactionManager, idempotency_key: Optional[str] = None):
        self.transaction_manager = transaction_manager
        self.idempotency_key = idempotency_key
        self.operations = []
        self.result = None
    
    def put(self, table_name: str, item: Dict, condition_expression: Optional[str] = None) -> 'TransactionBuilder':
        """Add a Put operation to the transaction"""
        operation = self.transaction_manager.create_put_operation(table_name, item, condition_expression)
        self.operations.append(operation)
        return self
    
    def update(self, table_name: str, key: Dict, update_expression: str, 
               expression_attribute_values: Dict, expression_attribute_names: Optional[Dict] = None,
               condition_expression: Optional[str] = None, expected_version: Optional[int] = None) -> 'TransactionBuilder':
        """Add an Update operation to the transaction"""
        operation = self.transaction_manager.create_update_operation(
            table_name, key, update_expression, expression_attribute_values,
            expression_attribute_names, condition_expression, expected_version
        )
        self.operations.append(operation)
        return self
    
    def delete(self, table_name: str, key: Dict, condition_expression: Optional[str] = None,
               expected_version: Optional[int] = None) -> 'TransactionBuilder':
        """Add a Delete operation to the transaction"""
        operation = self.transaction_manager.create_delete_operation(table_name, key, condition_expression, expected_version)
        self.operations.append(operation)
        return self
    
    def condition_check(self, table_name: str, key: Dict, condition_expression: str,
                       expression_attribute_values: Optional[Dict] = None,
                       expression_attribute_names: Optional[Dict] = None) -> 'TransactionBuilder':
        """Add a ConditionCheck operation to the transaction"""
        operation = self.transaction_manager.create_condition_check(
            table_name, key, condition_expression, expression_attribute_values, expression_attribute_names
        )
        self.operations.append(operation)
        return self


# Convenience functions for common transaction patterns
def execute_atomic_update(table_name: str, key: Dict, updates: Dict, expected_version: Optional[int] = None,
                         correlation_id: Optional[str] = None) -> Dict:
    """
    Execute an atomic update with optimistic concurrency control
    
    Args:
        table_name: DynamoDB table name
        key: Primary key of item to update
        updates: Dictionary of field updates
        expected_version: Expected version for concurrency control
        correlation_id: Optional correlation ID
        
    Returns:
        Update result
    """
    tm = TransactionManager(correlation_id)
    
    # Build update expression from updates dictionary
    update_parts = []
    expression_values = {}
    expression_names = {}
    
    for field, value in updates.items():
        safe_field = f"#{field}"
        safe_value = f":{field}"
        update_parts.append(f"{safe_field} = {safe_value}")
        expression_names[safe_field] = field
        expression_values[safe_value] = value
    
    update_expression = "SET " + ", ".join(update_parts)
    
    operation = tm.create_update_operation(
        table_name, key, update_expression, expression_values, expression_names,
        expected_version=expected_version
    )
    
    return tm.execute_transaction([operation])


def execute_atomic_put_with_condition(table_name: str, item: Dict, condition_expression: str,
                                    correlation_id: Optional[str] = None) -> Dict:
    """
    Execute an atomic put with condition check
    
    Args:
        table_name: DynamoDB table name
        item: Item to put
        condition_expression: Condition that must be met
        correlation_id: Optional correlation ID
        
    Returns:
        Put result
    """
    tm = TransactionManager(correlation_id)
    operation = tm.create_put_operation(table_name, item, condition_expression)
    return tm.execute_transaction([operation])