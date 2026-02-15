"""
AuditLogger - Comprehensive audit logging for compliance
Logs all user actions, data access, and administrative operations
"""

import os
import json
import uuid
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


class AuditLogger:
    """
    Comprehensive audit logger for tracking all system actions
    Logs to DynamoDB and streams to Kinesis Firehose for S3 archival
    """
    
    def __init__(self):
        """Initialize AuditLogger with DynamoDB and Firehose clients"""
        self.dynamodb = boto3.resource('dynamodb')
        self.firehose = boto3.client('firehose')
        
        # Get table and stream names from environment
        self.table_name = os.environ.get('AUDIT_LOGS_TABLE', 'aquachain-dev-audit-logs')
        self.stream_name = os.environ.get('AUDIT_LOG_STREAM', 'AuditLogStream')
        
        self.table = self.dynamodb.Table(self.table_name)
        
        # TTL for 7 years (2555 days)
        self.ttl_days = 2555
    
    def log_action(
        self,
        action_type: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any],
        request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Log an auditable action
        
        Args:
            action_type: Type of action (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
            user_id: ID of user performing the action
            resource_type: Type of resource (USER, DEVICE, READING, ALERT, etc.)
            resource_id: ID of the resource being acted upon
            details: Additional details about the action
            request_context: Request context (IP, user agent, request ID, etc.)
        
        Returns:
            The created audit log entry
        
        Raises:
            ClientError: If DynamoDB or Firehose operations fail
        """
        timestamp = datetime.utcnow().isoformat()
        log_id = str(uuid.uuid4())
        
        # Calculate TTL (7 years from now)
        ttl_timestamp = int((datetime.utcnow() + timedelta(days=self.ttl_days)).timestamp())
        
        # Create structured log entry
        log_entry = {
            'log_id': log_id,
            'timestamp': timestamp,
            'action_type': action_type,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details,
            'request_context': {
                'ip_address': request_context.get('ip_address', 'unknown'),
                'user_agent': request_context.get('user_agent', 'unknown'),
                'request_id': request_context.get('request_id', 'unknown'),
                'source': request_context.get('source', 'api')
            },
            'ttl': ttl_timestamp
        }
        
        try:
            # Write to DynamoDB for queryable audit trail
            self.table.put_item(Item=log_entry)
            
            # Stream to Kinesis Firehose for long-term S3 archival
            self._stream_to_firehose(log_entry)
            
            return log_entry
            
        except ClientError as e:
            # Log error but don't fail the operation
            print(f"Error logging audit entry: {e}")
            # Re-raise to allow caller to handle
            raise
    
    def log_authentication_event(
        self,
        event_type: str,
        user_id: str,
        success: bool,
        request_context: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log authentication events (login, logout, password reset, etc.)
        
        Args:
            event_type: Type of auth event (LOGIN, LOGOUT, PASSWORD_RESET, etc.)
            user_id: ID of user
            success: Whether the authentication was successful
            request_context: Request context
            details: Additional details
        
        Returns:
            The created audit log entry
        """
        action_details = details or {}
        action_details['success'] = success
        
        return self.log_action(
            action_type=f'AUTH_{event_type}',
            user_id=user_id,
            resource_type='USER',
            resource_id=user_id,
            details=action_details,
            request_context=request_context
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
        request_context: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log data access events (read operations)
        
        Args:
            user_id: ID of user accessing data
            resource_type: Type of resource being accessed
            resource_id: ID of resource
            operation: Specific operation (GET, LIST, QUERY, etc.)
            request_context: Request context
            details: Additional details
        
        Returns:
            The created audit log entry
        """
        action_details = details or {}
        action_details['operation'] = operation
        
        return self.log_action(
            action_type='READ',
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=action_details,
            request_context=request_context
        )
    
    def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        modification_type: str,
        previous_values: Optional[Dict[str, Any]],
        new_values: Dict[str, Any],
        request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Log data modification events (create, update, delete)
        
        Args:
            user_id: ID of user modifying data
            resource_type: Type of resource being modified
            resource_id: ID of resource
            modification_type: Type of modification (CREATE, UPDATE, DELETE)
            previous_values: Previous values (for UPDATE/DELETE)
            new_values: New values (for CREATE/UPDATE)
            request_context: Request context
        
        Returns:
            The created audit log entry
        """
        details = {
            'modification_type': modification_type,
            'previous_values': previous_values,
            'new_values': new_values,
            'changed_fields': list(new_values.keys()) if new_values else []
        }
        
        return self.log_action(
            action_type=modification_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            request_context=request_context
        )
    
    def log_administrative_action(
        self,
        user_id: str,
        action: str,
        target_resource_type: str,
        target_resource_id: str,
        request_context: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log administrative actions (user management, config changes, etc.)
        
        Args:
            user_id: ID of admin user
            action: Administrative action performed
            target_resource_type: Type of resource being administered
            target_resource_id: ID of target resource
            request_context: Request context
            details: Additional details
        
        Returns:
            The created audit log entry
        """
        action_details = details or {}
        action_details['administrative_action'] = action
        
        return self.log_action(
            action_type=f'ADMIN_{action}',
            user_id=user_id,
            resource_type=target_resource_type,
            resource_id=target_resource_id,
            details=action_details,
            request_context=request_context
        )
    
    def _stream_to_firehose(self, log_entry: Dict[str, Any]) -> None:
        """
        Stream audit log to Kinesis Firehose for S3 archival
        
        Args:
            log_entry: The audit log entry to stream
        """
        try:
            # Convert to JSON with newline for Firehose
            record_data = json.dumps(log_entry) + '\n'
            
            self.firehose.put_record(
                DeliveryStreamName=self.stream_name,
                Record={'Data': record_data.encode('utf-8')}
            )
        except ClientError as e:
            # Log error but don't fail the audit logging
            print(f"Error streaming to Firehose: {e}")
            # Don't re-raise - DynamoDB write is primary, Firehose is backup
    
    def query_logs_by_user(
        self,
        user_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query audit logs for a specific user
        
        Args:
            user_id: ID of user to query logs for
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
            limit: Maximum number of results
        
        Returns:
            Dictionary with items and pagination info
        """
        from boto3.dynamodb.conditions import Key
        
        query_params = {
            'IndexName': 'user_id-timestamp-index',
            'KeyConditionExpression': Key('user_id').eq(user_id),
            'Limit': limit,
            'ScanIndexForward': False  # Newest first
        }
        
        # Add time range if specified
        if start_time and end_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').between(start_time, end_time)
        elif start_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').gte(start_time)
        elif end_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').lte(end_time)
        
        response = self.table.query(**query_params)
        
        return {
            'items': response.get('Items', []),
            'count': len(response.get('Items', [])),
            'last_evaluated_key': response.get('LastEvaluatedKey')
        }
    
    def query_logs_by_resource(
        self,
        resource_type: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query audit logs for a specific resource type
        
        Args:
            resource_type: Type of resource to query logs for
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
            limit: Maximum number of results
        
        Returns:
            Dictionary with items and pagination info
        """
        from boto3.dynamodb.conditions import Key
        
        query_params = {
            'IndexName': 'resource_type-timestamp-index',
            'KeyConditionExpression': Key('resource_type').eq(resource_type),
            'Limit': limit,
            'ScanIndexForward': False  # Newest first
        }
        
        # Add time range if specified
        if start_time and end_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').between(start_time, end_time)
        elif start_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').gte(start_time)
        elif end_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').lte(end_time)
        
        response = self.table.query(**query_params)
        
        return {
            'items': response.get('Items', []),
            'count': len(response.get('Items', [])),
            'last_evaluated_key': response.get('LastEvaluatedKey')
        }
    
    def query_logs_by_action_type(
        self,
        action_type: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query audit logs for a specific action type
        
        Args:
            action_type: Type of action to query logs for
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
            limit: Maximum number of results
        
        Returns:
            Dictionary with items and pagination info
        """
        from boto3.dynamodb.conditions import Key
        
        query_params = {
            'IndexName': 'action_type-timestamp-index',
            'KeyConditionExpression': Key('action_type').eq(action_type),
            'Limit': limit,
            'ScanIndexForward': False  # Newest first
        }
        
        # Add time range if specified
        if start_time and end_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').between(start_time, end_time)
        elif start_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').gte(start_time)
        elif end_time:
            query_params['KeyConditionExpression'] &= Key('timestamp').lte(end_time)
        
        response = self.table.query(**query_params)
        
        return {
            'items': response.get('Items', []),
            'count': len(response.get('Items', [])),
            'last_evaluated_key': response.get('LastEvaluatedKey')
        }


# Singleton instance for easy import
audit_logger = AuditLogger()
