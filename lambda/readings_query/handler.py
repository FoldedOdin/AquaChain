"""
Sensor readings query service using optimized GSI queries (Phase 4)
Demonstrates efficient querying of readings by metric type and alert level
"""

import json
import boto3
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import error handling
from errors import ValidationError, DatabaseError
from error_handler import handle_errors

# Import structured logging
from structured_logger import get_logger

# Import optimized queries
from dynamodb_queries import (
    query_readings_by_device_and_metric,
    query_readings_by_alert_level
)

# Import cache service
from cache_service import get_cache_service

logger = get_logger(__name__, service='readings-query')


class ReadingsQueryService:
    """
    Service for querying sensor readings with optimized GSI patterns
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.readings_table = self.dynamodb.Table('aquachain-readings')
        self.cache = get_cache_service()
    
    def query_by_metric_type(self, device_id: str, metric_type: str,
                            limit: int = 100, last_key: Optional[Dict] = None) -> Dict:
        """
        Query readings for a specific device and metric type
        Uses device_id-metric_type-index GSI for efficient queries
        """
        try:
            # Validate metric type
            valid_metrics = ['pH', 'turbidity', 'temperature', 'dissolved_oxygen', 
                           'conductivity', 'chlorine', 'tds']
            if metric_type not in valid_metrics:
                raise ValidationError(
                    f"Invalid metric type. Must be one of: {', '.join(valid_metrics)}",
                    details={'metric_type': metric_type}
                )
            
            result = query_readings_by_device_and_metric(
                device_id=device_id,
                metric_type=metric_type,
                limit=limit,
                last_key=last_key,
                table_name='aquachain-readings'
            )
            
            logger.info(f"Queried {len(result['items'])} readings for device {device_id}",
                device_id=device_id,
                metric_type=metric_type,
                item_count=len(result['items']),
                duration_ms=result.get('duration_ms')
            )
            
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error querying readings by metric: {e}",
                device_id=device_id,
                metric_type=metric_type
            )
            raise DatabaseError("Failed to query readings", details={
                'device_id': device_id,
                'metric_type': metric_type
            })
    
    def query_by_alert_level(self, alert_level: str, start_time: Optional[str] = None,
                            end_time: Optional[str] = None, limit: int = 100,
                            last_key: Optional[Dict] = None) -> Dict:
        """
        Query readings by alert level with optional time range
        Uses alert_level-timestamp-index GSI for efficient queries
        """
        try:
            # Validate alert level
            valid_levels = ['critical', 'warning', 'normal', 'info']
            if alert_level not in valid_levels:
                raise ValidationError(
                    f"Invalid alert level. Must be one of: {', '.join(valid_levels)}",
                    details={'alert_level': alert_level}
                )
            
            # Validate time range if provided
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    if start_dt > end_dt:
                        raise ValidationError("start_time must be before end_time")
                except ValueError as e:
                    raise ValidationError(f"Invalid timestamp format: {e}")
            
            result = query_readings_by_alert_level(
                alert_level=alert_level,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                last_key=last_key,
                table_name='aquachain-readings'
            )
            
            logger.info(f"Queried {len(result['items'])} readings with alert level {alert_level}",
                alert_level=alert_level,
                item_count=len(result['items']),
                duration_ms=result.get('duration_ms')
            )
            
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error querying readings by alert level: {e}",
                alert_level=alert_level
            )
            raise DatabaseError("Failed to query readings", details={
                'alert_level': alert_level
            })
    
    def get_latest_reading(self, device_id: str) -> Optional[Dict]:
        """
        Get the most recent reading for a device with caching
        Cached for 1 minute to reduce database load for frequently accessed devices
        """
        cache_key = f"reading:latest:{device_id}"
        
        try:
            # Try cache first
            cached_reading = self.cache.get(cache_key)
            if cached_reading:
                logger.info(f"Latest reading found in cache: {device_id}",
                           device_id=device_id, cache_hit=True)
                return cached_reading
            
            # Cache miss - query DynamoDB
            response = self.readings_table.query(
                IndexName='DeviceIndex',
                KeyConditionExpression='deviceId = :device_id',
                ExpressionAttributeValues={':device_id': device_id},
                ScanIndexForward=False,  # Descending order (newest first)
                Limit=1
            )
            
            reading = response['Items'][0] if response['Items'] else None
            
            if reading:
                # Cache for 1 minute (short TTL for near real-time data)
                self.cache.set(cache_key, reading, ttl=60)
                logger.info(f"Latest reading found: {device_id}",
                           device_id=device_id, cache_hit=False)
            
            return reading
            
        except Exception as e:
            logger.error(f"Error getting latest reading: {e}", device_id=device_id)
            raise DatabaseError("Failed to get latest reading", 
                              details={'device_id': device_id})
    
    def get_critical_alerts(self, hours: int = 24, limit: int = 100) -> Dict:
        """
        Get all critical alerts from the last N hours
        Convenience method for monitoring dashboards
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            result = self.query_by_alert_level(
                alert_level='critical',
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                limit=limit
            )
            
            logger.info(f"Retrieved {len(result['items'])} critical alerts from last {hours} hours",
                hours=hours,
                item_count=len(result['items'])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting critical alerts: {e}", hours=hours)
            raise DatabaseError("Failed to get critical alerts", details={'hours': hours})


@handle_errors
def lambda_handler(event, context):
    """
    Main Lambda handler for readings query operations
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    query_service = ReadingsQueryService(region)
    
    # Route based on HTTP method and path
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    query_params = event.get('queryStringParameters', {}) or {}
    
    if http_method == 'GET' and '/readings/by-metric' in path:
        # Query readings by device and metric type using GSI
        device_id = query_params.get('deviceId')
        metric_type = query_params.get('metricType')
        limit = int(query_params.get('limit', 100))
        last_key_encoded = query_params.get('lastKey')
        
        if not device_id:
            raise ValidationError('deviceId parameter required')
        if not metric_type:
            raise ValidationError('metricType parameter required')
        
        # Decode last_key if provided
        last_key = None
        if last_key_encoded:
            try:
                last_key = json.loads(base64.b64decode(last_key_encoded))
            except Exception as e:
                raise ValidationError('Invalid lastKey parameter')
        
        result = query_service.query_by_metric_type(
            device_id=device_id,
            metric_type=metric_type,
            limit=limit,
            last_key=last_key
        )
        
        # Encode last_key for response
        if result.get('last_key'):
            result['last_key'] = base64.b64encode(
                json.dumps(result['last_key']).encode()
            ).decode()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    elif http_method == 'GET' and '/readings/by-alert-level' in path:
        # Query readings by alert level using GSI
        alert_level = query_params.get('alertLevel')
        start_time = query_params.get('startTime')
        end_time = query_params.get('endTime')
        limit = int(query_params.get('limit', 100))
        last_key_encoded = query_params.get('lastKey')
        
        if not alert_level:
            raise ValidationError('alertLevel parameter required')
        
        # Decode last_key if provided
        last_key = None
        if last_key_encoded:
            try:
                last_key = json.loads(base64.b64decode(last_key_encoded))
            except Exception as e:
                raise ValidationError('Invalid lastKey parameter')
        
        result = query_service.query_by_alert_level(
            alert_level=alert_level,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            last_key=last_key
        )
        
        # Encode last_key for response
        if result.get('last_key'):
            result['last_key'] = base64.b64encode(
                json.dumps(result['last_key']).encode()
            ).decode()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    elif http_method == 'GET' and '/readings/critical-alerts' in path:
        # Get critical alerts from last N hours
        hours = int(query_params.get('hours', 24))
        limit = int(query_params.get('limit', 100))
        
        result = query_service.get_critical_alerts(hours=hours, limit=limit)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    else:
        raise ValidationError('Endpoint not found', error_code='ENDPOINT_NOT_FOUND')
