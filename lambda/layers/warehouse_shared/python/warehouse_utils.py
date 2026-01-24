"""
Warehouse Shared Utilities Layer
Optimized for Lambda performance and cost efficiency
"""

import boto3
import json
from typing import Dict, List, Optional
from functools import lru_cache
import os

# Singleton pattern for AWS clients to reduce cold start
class AWSClientManager:
    _instance = None
    _clients = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @lru_cache(maxsize=10)
    def get_client(self, service_name: str):
        """Get cached AWS client"""
        if service_name not in self._clients:
            self._clients[service_name] = boto3.client(service_name)
        return self._clients[service_name]
    
    @lru_cache(maxsize=10)
    def get_resource(self, service_name: str):
        """Get cached AWS resource"""
        if f"{service_name}_resource" not in self._clients:
            self._clients[f"{service_name}_resource"] = boto3.resource(service_name)
        return self._clients[f"{service_name}_resource"]

# Global client manager instance
aws_clients = AWSClientManager()

class OptimizedDynamoDBManager:
    """Optimized DynamoDB operations with connection reuse"""
    
    def __init__(self):
        self.dynamodb = aws_clients.get_resource('dynamodb')
        self._tables = {}
    
    @lru_cache(maxsize=20)
    def get_table(self, table_name: str):
        """Get cached table reference"""
        if table_name not in self._tables:
            self._tables[table_name] = self.dynamodb.Table(table_name)
        return self._tables[table_name]

# Performance optimized utilities
def batch_get_items(table_name: str, keys: List[Dict], max_batch_size: int = 100) -> List[Dict]:
    """Optimized batch get with automatic batching"""
    db_manager = OptimizedDynamoDBManager()
    table = db_manager.get_table(table_name)
    
    results = []
    for i in range(0, len(keys), max_batch_size):
        batch_keys = keys[i:i + max_batch_size]
        
        response = table.batch_get_item(
            RequestItems={
                table_name: {
                    'Keys': batch_keys
                }
            }
        )
        
        results.extend(response.get('Responses', {}).get(table_name, []))
    
    return results

def paginated_scan(table_name: str, filter_expression=None, limit: int = 1000) -> List[Dict]:
    """Memory-efficient paginated scan"""
    db_manager = OptimizedDynamoDBManager()
    table = db_manager.get_table(table_name)
    
    scan_params = {'Limit': min(limit, 1000)}
    if filter_expression:
        scan_params['FilterExpression'] = filter_expression
    
    results = []
    last_key = None
    
    while len(results) < limit:
        if last_key:
            scan_params['ExclusiveStartKey'] = last_key
        
        response = table.scan(**scan_params)
        items = response.get('Items', [])
        results.extend(items)
        
        last_key = response.get('LastEvaluatedKey')
        if not last_key or len(items) == 0:
            break
    
    return results[:limit]