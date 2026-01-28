"""
WebSocket Connection Manager for Enhanced Consumer Ordering System
Handles connection persistence, reconnection logic, and connection health monitoring
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import os

# Add shared utilities to path
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='websocket-connection-manager')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway_client = boto3.client('apigatewaymanagementapi')

# Environment variables
WEBSOCKET_CONNECTIONS_TABLE = os.environ.get('WEBSOCKET_CONNECTIONS_TABLE_NAME', 'aquachain-websocket-connections-dev')

class ConnectionManager:
    """
    Manages WebSocket connections for the ordering system
    """
    
    def __init__(self, websocket_endpoint: str = None):
        self.websocket_endpoint = websocket_endpoint
        if websocket_endpoint:
            apigateway_client.meta.config.endpoint_url = websocket_endpoint
        
        self.connections_table = dynamodb.Table(WEBSOCKET_CONNECTIONS_TABLE)
    
    def store_connection(self, connection_data: Dict[str, Any]) -> bool:
        """
        Store connection information with automatic TTL
        """
        try:
            # Add TTL for automatic cleanup (24 hours)
            connection_data['ttl'] = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            
            self.connections_table.put_item(Item=connection_data)
            
            logger.info(f"Stored connection: {connection_data['connectionId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing connection: {e}")
            return False
    
    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get connection information
        """
        try:
            response = self.connections_table.get_item(Key={'connectionId': connection_id})
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Error getting connection {connection_id}: {e}")
            return None
    
    def update_connection_activity(self, connection_id: str) -> bool:
        """
        Update connection last activity timestamp
        """
        try:
            self.connections_table.update_item(
                Key={'connectionId': connection_id},
                UpdateExpression='SET lastPing = :timestamp',
                ExpressionAttributeValues={':timestamp': datetime.utcnow().isoformat()}
            )
            return True
            
        except Exception as e:
            logger.warning(f"Error updating connection activity: {e}")
            return False
    
    def remove_connection(self, connection_id: str) -> bool:
        """
        Remove connection from storage
        """
        try:
            self.connections_table.delete_item(Key={'connectionId': connection_id})
            logger.info(f"Removed connection: {connection_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Error removing connection {connection_id}: {e}")
            return False
    
    def add_order_subscription(self, connection_id: str, order_id: str) -> bool:
        """
        Add order subscription to connection
        """
        try:
            connection = self.get_connection(connection_id)
            if not connection:
                logger.error(f"Connection {connection_id} not found")
                return False
            
            current_subscriptions = connection.get('orderSubscriptions', [])
            if order_id not in current_subscriptions:
                current_subscriptions.append(order_id)
                
                self.connections_table.update_item(
                    Key={'connectionId': connection_id},
                    UpdateExpression='SET orderSubscriptions = :subscriptions',
                    ExpressionAttributeValues={':subscriptions': current_subscriptions}
                )
                
                logger.info(f"Added order subscription {order_id} to connection {connection_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding order subscription: {e}")
            return False
    
    def remove_order_subscription(self, connection_id: str, order_id: str) -> bool:
        """
        Remove order subscription from connection
        """
        try:
            connection = self.get_connection(connection_id)
            if not connection:
                return True  # Connection doesn't exist, consider it successful
            
            current_subscriptions = connection.get('orderSubscriptions', [])
            if order_id in current_subscriptions:
                current_subscriptions.remove(order_id)
                
                self.connections_table.update_item(
                    Key={'connectionId': connection_id},
                    UpdateExpression='SET orderSubscriptions = :subscriptions',
                    ExpressionAttributeValues={':subscriptions': current_subscriptions}
                )
                
                logger.info(f"Removed order subscription {order_id} from connection {connection_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing order subscription: {e}")
            return False
    
    def get_connections_for_order(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get all connections subscribed to a specific order
        """
        try:
            response = self.connections_table.scan(
                FilterExpression='contains(orderSubscriptions, :order_id) AND connectionType = :conn_type',
                ExpressionAttributeValues={
                    ':order_id': order_id,
                    ':conn_type': 'order_updates'
                }
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error getting connections for order {order_id}: {e}")
            return []
    
    def get_connections_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active connections for a specific user
        """
        try:
            response = self.connections_table.query(
                IndexName='UserConnections',
                KeyConditionExpression='userId = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error getting connections for user {user_id}: {e}")
            return []
    
    def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to a specific connection
        """
        try:
            apigateway_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message)
            )
            return True
            
        except apigateway_client.exceptions.GoneException:
            # Connection is stale, remove it
            logger.info(f"Connection {connection_id} is gone, removing")
            self.remove_connection(connection_id)
            return False
            
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {e}")
            return False
    
    def broadcast_to_connections(self, connections: List[Dict[str, Any]], 
                               message: Dict[str, Any]) -> Dict[str, int]:
        """
        Broadcast message to multiple connections
        """
        successful = 0
        failed = 0
        
        for connection in connections:
            if self.send_message(connection['connectionId'], message):
                successful += 1
            else:
                failed += 1
        
        return {'successful': successful, 'failed': failed}
    
    def cleanup_stale_connections(self, max_age_hours: int = 24) -> int:
        """
        Clean up connections that haven't pinged recently
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cutoff_iso = cutoff_time.isoformat()
            
            # Scan for stale connections
            response = self.connections_table.scan(
                FilterExpression='lastPing < :cutoff',
                ExpressionAttributeValues={':cutoff': cutoff_iso}
            )
            
            stale_connections = response.get('Items', [])
            cleaned_count = 0
            
            for connection in stale_connections:
                if self.remove_connection(connection['connectionId']):
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} stale connections")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up stale connections: {e}")
            return 0
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics
        """
        try:
            # Get total connections
            response = self.connections_table.scan(
                Select='COUNT'
            )
            total_connections = response.get('Count', 0)
            
            # Get connections by type
            response = self.connections_table.scan(
                FilterExpression='connectionType = :conn_type',
                ExpressionAttributeValues={':conn_type': 'order_updates'},
                Select='COUNT'
            )
            order_connections = response.get('Count', 0)
            
            # Get active connections (pinged in last hour)
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            response = self.connections_table.scan(
                FilterExpression='lastPing > :cutoff',
                ExpressionAttributeValues={':cutoff': one_hour_ago},
                Select='COUNT'
            )
            active_connections = response.get('Count', 0)
            
            return {
                'total_connections': total_connections,
                'order_connections': order_connections,
                'active_connections': active_connections,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {
                'total_connections': 0,
                'order_connections': 0,
                'active_connections': 0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def validate_connection_permissions(self, connection: Dict[str, Any], 
                                      order_id: str) -> bool:
        """
        Validate that a connection has permission to subscribe to an order
        """
        try:
            user_role = connection.get('userRole', 'consumer')
            user_id = connection.get('userId')
            
            # Get order information to check permissions
            orders_table = dynamodb.Table(os.environ.get('ORDERS_TABLE_NAME', 'aquachain-orders-dev'))
            response = orders_table.get_item(
                Key={
                    'PK': f'ORDER#{order_id}',
                    'SK': f'ORDER#{order_id}'
                }
            )
            
            order = response.get('Item')
            if not order:
                logger.warning(f"Order {order_id} not found for permission check")
                return False
            
            # Permission logic
            if user_role == 'consumer':
                # Consumers can only subscribe to their own orders
                return order.get('consumerId') == user_id
            elif user_role == 'technician':
                # Technicians can subscribe to orders assigned to them or their own orders
                return (order.get('consumerId') == user_id or 
                       order.get('assignedTechnician') == user_id)
            elif user_role == 'administrator':
                # Administrators can subscribe to any order
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating connection permissions: {e}")
            return False
    
    def send_connection_health_check(self, connection_id: str) -> bool:
        """
        Send health check message to connection
        """
        health_check_message = {
            'type': 'health_check',
            'timestamp': datetime.utcnow().isoformat(),
            'connectionId': connection_id
        }
        
        return self.send_message(connection_id, health_check_message)
    
    def handle_reconnection(self, connection_id: str, user_id: str) -> Dict[str, Any]:
        """
        Handle connection reconnection and restore subscriptions
        """
        try:
            # Get user's previous connections to restore subscriptions
            previous_connections = self.get_connections_for_user(user_id)
            
            # Collect all order subscriptions from previous connections
            all_subscriptions = set()
            for conn in previous_connections:
                if conn['connectionId'] != connection_id:  # Exclude current connection
                    subscriptions = conn.get('orderSubscriptions', [])
                    all_subscriptions.update(subscriptions)
            
            # Update current connection with restored subscriptions
            if all_subscriptions:
                self.connections_table.update_item(
                    Key={'connectionId': connection_id},
                    UpdateExpression='SET orderSubscriptions = :subscriptions',
                    ExpressionAttributeValues={':subscriptions': list(all_subscriptions)}
                )
            
            # Send reconnection confirmation
            reconnection_message = {
                'type': 'reconnection_complete',
                'restoredSubscriptions': list(all_subscriptions),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.send_message(connection_id, reconnection_message)
            
            logger.info(f"Handled reconnection for user {user_id}, restored {len(all_subscriptions)} subscriptions")
            
            return {
                'success': True,
                'restoredSubscriptions': list(all_subscriptions)
            }
            
        except Exception as e:
            logger.error(f"Error handling reconnection: {e}")
            return {
                'success': False,
                'error': str(e)
            }