"""
Shared utilities for workflow operations
Optimized for Lambda layer usage
"""

import boto3
from typing import Dict, Optional
import os
from functools import lru_cache


class OptimizedAWSClients:
    """
    Lazy-loaded AWS clients to reduce cold start time
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clients = {}
        return cls._instance
    
    @lru_cache(maxsize=None)
    def get_dynamodb_resource(self):
        """Get DynamoDB resource with connection pooling"""
        if 'dynamodb' not in self._clients:
            self._clients['dynamodb'] = boto3.resource(
                'dynamodb',
                config=boto3.session.Config(
                    max_pool_connections=10,
                    retries={'max_attempts': 3}
                )
            )
        return self._clients['dynamodb']
    
    @lru_cache(maxsize=None)
    def get_sns_client(self):
        """Get SNS client with optimized config"""
        if 'sns' not in self._clients:
            self._clients['sns'] = boto3.client(
                'sns',
                config=boto3.session.Config(
                    max_pool_connections=5,
                    retries={'max_attempts': 2}
                )
            )
        return self._clients['sns']
    
    @lru_cache(maxsize=None)
    def get_eventbridge_client(self):
        """Get EventBridge client"""
        if 'eventbridge' not in self._clients:
            self._clients['eventbridge'] = boto3.client('events')
        return self._clients['eventbridge']


# Global instance
aws_clients = OptimizedAWSClients()


class WorkflowConstants:
    """
    Workflow constants to avoid repeated string operations
    """
    STATES = {
        'PENDING_APPROVAL': 'PENDING_APPROVAL',
        'APPROVED': 'APPROVED',
        'REJECTED': 'REJECTED',
        'TIMEOUT_ESCALATED': 'TIMEOUT_ESCALATED',
        'CANCELLED': 'CANCELLED',
        'COMPLETED': 'COMPLETED',
        'FAILED': 'FAILED'
    }
    
    ACTIONS = {
        'APPROVE': 'APPROVE',
        'REJECT': 'REJECT',
        'ESCALATE': 'ESCALATE',
        'CANCEL': 'CANCEL',
        'TIMEOUT': 'TIMEOUT',
        'COMPLETE': 'COMPLETE'
    }
    
    WORKFLOW_TYPES = {
        'PURCHASE_APPROVAL': 'PURCHASE_APPROVAL',
        'EMERGENCY_PURCHASE_APPROVAL': 'EMERGENCY_PURCHASE_APPROVAL',
        'BUDGET_ALLOCATION': 'BUDGET_ALLOCATION',
        'SUPPLIER_APPROVAL': 'SUPPLIER_APPROVAL'
    }


def optimize_dynamodb_item(item: Dict) -> Dict:
    """
    Optimize DynamoDB item for storage and retrieval
    Remove None values and optimize data types
    """
    optimized = {}
    for key, value in item.items():
        if value is not None:
            if isinstance(value, dict):
                optimized_nested = optimize_dynamodb_item(value)
                if optimized_nested:  # Only add if not empty
                    optimized[key] = optimized_nested
            elif isinstance(value, list) and value:  # Only add non-empty lists
                optimized[key] = value
            elif not isinstance(value, (dict, list)):  # Add primitive types
                optimized[key] = value
    return optimized


def batch_write_with_retry(table, items: list, max_retries: int = 3):
    """
    Batch write items with exponential backoff retry
    """
    import time
    import random
    
    for attempt in range(max_retries):
        try:
            with table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=optimize_dynamodb_item(item))
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    
    return False