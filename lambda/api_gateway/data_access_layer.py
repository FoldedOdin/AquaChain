"""
Data Access Layer with optimized queries for DynamoDB operations
Provides efficient data access patterns for time-series data and analytics
"""
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from botocore.exceptions import ClientError
import json
import hashlib

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
elasticache = boto3.client('elasticache')

# Table references
readings_table = dynamodb.Table('aquachain-readings')
ledger_table = dynamodb.Table('aquachain-ledger')
service_requests_table = dynamodb.Table('aquachain-service-requests')
users_table = dynamodb.Table('aquachain-users')

# Cache configuration
CACHE_TTL = 300  # 5 minutes
CACHE_CLUSTER_ENDPOINT = 'aquachain-cache.abc123.cache.amazonaws.com:6379'


class DataAccessLayer:
    """Optimized data access layer for AquaChain system"""
    
    def __init__(self):
        self.cache = None
        try:
            import redis
            self.cache = redis.Redis(
                host=CACHE_CLUSTER_ENDPOINT.split(':')[0],
                port=int(CACHE_CLUSTER_ENDPOINT.split(':')[1]),
                decode_responses=True
            )
        except ImportError:
            logger.warning("Redis not available, caching disabled")
        except Exception as e:
            logger.warning(f"Cache connection failed: {e}")
    
    def get_device_readings_optimized(self, device_id: str, start_date: datetime, 
                                    end_date: datetime, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Optimized query for device readings using time-windowed partition keys
        """
        try:
            # Check cache first
            cache_key = f"readings:{device_id}:{start_date.isoformat()}:{end_date.isoformat()}:{limit}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            readings = []
            current_month = start_date.replace(day=1)
            
            # Query each month partition
            while current_month <= end_date and len(readings) < limit:
                partition_key = f"{device_id}#{current_month.strftime('%Y%m')}"
                
                # Use parallel scan for large date ranges
                if (end_date - start_date).days > 30:
                    month_readings = self._parallel_query_month(
                        partition_key, start_date, end_date, limit - len(readings)
                    )
                else:
                    month_readings = self._query_month(
                        partition_key, start_date, end_date, limit - len(readings)
                    )
                
                readings.extend(month_readings)
                
                # Move to next month
                if current_month.month == 12:
                    current_month = current_month.replace(year=current_month.year + 1, month=1)
                else:
                    current_month = current_month.replace(month=current_month.month + 1)
            
            # Sort by timestamp (most recent first) and limit
            readings.sort(key=lambda x: x['timestamp'], reverse=True)
            readings = readings[:limit]
            
            # Cache result
            self._set_cache(cache_key, json.dumps(readings), ttl=CACHE_TTL)
            
            return readings
            
        except Exception as e:
            logger.error(f"Error in optimized readings query: {str(e)}")
            raise
    
    def _query_month(self, partition_key: str, start_date: datetime, 
                    end_date: datetime, limit: int) -> List[Dict[str, Any]]:
        """Query single month partition"""
        try:
            response = readings_table.query(
                KeyConditionExpression='#pk = :pk AND #sk BETWEEN :start AND :end',
                ExpressionAttributeNames={
                    '#pk': 'deviceId#YYYYMM',
                    '#sk': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':pk': partition_key,
                    ':start': start_date.isoformat(),
                    ':end': end_date.isoformat()
                },
                Limit=limit,
                ScanIndexForward=False,
                Select='ALL_ATTRIBUTES'
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Error querying month partition {partition_key}: {str(e)}")
            return []
    
    def _parallel_query_month(self, partition_key: str, start_date: datetime, 
                             end_date: datetime, limit: int) -> List[Dict[str, Any]]:
        """Parallel query for large month partitions"""
        try:
            # Use parallel scan with segments for large partitions
            segments = 4
            all_items = []
            
            for segment in range(segments):
                response = readings_table.query(
                    KeyConditionExpression='#pk = :pk AND #sk BETWEEN :start AND :end',
                    ExpressionAttributeNames={
                        '#pk': 'deviceId#YYYYMM',
                        '#sk': 'timestamp'
                    },
                    ExpressionAttributeValues={
                        ':pk': partition_key,
                        ':start': start_date.isoformat(),
                        ':end': end_date.isoformat()
                    },
                    Limit=limit // segments,
                    ScanIndexForward=False,
                    Select='ALL_ATTRIBUTES'
                )
                
                all_items.extend(response.get('Items', []))
            
            return all_items
            
        except ClientError as e:
            logger.error(f"Error in parallel query for {partition_key}: {str(e)}")
            return []
    
    def get_aggregated_readings(self, device_ids: List[str], start_date: datetime, 
                               end_date: datetime, aggregation: str = 'hourly') -> Dict[str, Any]:
        """
        Get aggregated readings for multiple devices with time-based grouping
        """
        try:
            cache_key = f"aggregated:{':'.join(device_ids)}:{start_date.isoformat()}:{end_date.isoformat()}:{aggregation}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            aggregated_data = {}
            
            for device_id in device_ids:
                device_readings = self.get_device_readings_optimized(
                    device_id, start_date, end_date, limit=10000
                )
                
                # Aggregate by time period
                device_aggregated = self._aggregate_by_time_period(
                    device_readings, aggregation
                )
                
                aggregated_data[device_id] = device_aggregated
            
            # Calculate cross-device statistics
            summary = self._calculate_cross_device_summary(aggregated_data)
            
            result = {
                'devices': aggregated_data,
                'summary': summary,
                'aggregation': aggregation,
                'timeRange': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
            
            # Cache result
            self._set_cache(cache_key, json.dumps(result), ttl=CACHE_TTL * 2)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting aggregated readings: {str(e)}")
            raise
    
    def _aggregate_by_time_period(self, readings: List[Dict[str, Any]], 
                                 aggregation: str) -> Dict[str, Any]:
        """Aggregate readings by time period"""
        try:
            if aggregation == 'hourly':
                time_format = '%Y-%m-%dT%H:00:00'
            elif aggregation == 'daily':
                time_format = '%Y-%m-%d'
            elif aggregation == 'weekly':
                time_format = '%Y-W%U'
            else:
                time_format = '%Y-%m-%dT%H:00:00'
            
            aggregated = {}
            
            for reading in readings:
                timestamp = datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00'))
                time_key = timestamp.strftime(time_format)
                
                if time_key not in aggregated:
                    aggregated[time_key] = {
                        'timestamp': time_key,
                        'count': 0,
                        'wqi_sum': 0,
                        'wqi_values': [],
                        'ph_values': [],
                        'turbidity_values': [],
                        'anomalies': {'normal': 0, 'sensor_fault': 0, 'contamination': 0}
                    }
                
                agg_data = aggregated[time_key]
                agg_data['count'] += 1
                
                # Aggregate WQI
                wqi = float(reading.get('wqi', 0))
                agg_data['wqi_sum'] += wqi
                agg_data['wqi_values'].append(wqi)
                
                # Aggregate sensor readings
                readings_data = reading.get('readings', {})
                if 'pH' in readings_data:
                    agg_data['ph_values'].append(float(readings_data['pH']))
                if 'turbidity' in readings_data:
                    agg_data['turbidity_values'].append(float(readings_data['turbidity']))
                
                # Count anomalies
                anomaly_type = reading.get('anomalyType', 'normal')
                agg_data['anomalies'][anomaly_type] += 1
            
            # Calculate final aggregated values
            for time_key, data in aggregated.items():
                data['wqi_avg'] = data['wqi_sum'] / data['count'] if data['count'] > 0 else 0
                data['ph_avg'] = sum(data['ph_values']) / len(data['ph_values']) if data['ph_values'] else 0
                data['turbidity_avg'] = sum(data['turbidity_values']) / len(data['turbidity_values']) if data['turbidity_values'] else 0
                
                # Remove intermediate values to save space
                del data['wqi_sum']
                del data['wqi_values']
                del data['ph_values']
                del data['turbidity_values']
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating by time period: {str(e)}")
            return {}
    
    def _calculate_cross_device_summary(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics across devices"""
        try:
            total_readings = 0
            total_anomalies = 0
            wqi_values = []
            
            for device_id, device_data in aggregated_data.items():
                for time_key, time_data in device_data.items():
                    total_readings += time_data['count']
                    total_anomalies += sum(time_data['anomalies'].values()) - time_data['anomalies']['normal']
                    wqi_values.append(time_data['wqi_avg'])
            
            avg_wqi = sum(wqi_values) / len(wqi_values) if wqi_values else 0
            anomaly_rate = (total_anomalies / total_readings * 100) if total_readings > 0 else 0
            
            return {
                'totalReadings': total_readings,
                'totalAnomalies': total_anomalies,
                'anomalyRate': round(anomaly_rate, 2),
                'averageWQI': round(avg_wqi, 2),
                'deviceCount': len(aggregated_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating cross-device summary: {str(e)}")
            return {}
    
    def get_paginated_service_requests(self, user_id: str, user_role: str, 
                                     filters: Dict[str, Any], 
                                     page_size: int = 50, 
                                     last_evaluated_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Efficient pagination for service requests with filtering
        """
        try:
            # Build query parameters based on user role
            if user_role == 'administrator':
                # Administrators can see all requests
                query_params = self._build_admin_service_query(filters, page_size, last_evaluated_key)
            elif user_role == 'technician':
                # Technicians see assigned requests
                query_params = self._build_technician_service_query(user_id, filters, page_size, last_evaluated_key)
            else:
                # Consumers see their own requests
                query_params = self._build_consumer_service_query(user_id, filters, page_size, last_evaluated_key)
            
            # Execute query
            if 'IndexName' in query_params:
                response = service_requests_table.query(**query_params)
            else:
                response = service_requests_table.scan(**query_params)
            
            items = response.get('Items', [])
            next_key = response.get('LastEvaluatedKey')
            
            return {
                'items': items,
                'count': len(items),
                'nextPageKey': next_key,
                'hasMore': next_key is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting paginated service requests: {str(e)}")
            raise
    
    def _build_consumer_service_query(self, consumer_id: str, filters: Dict[str, Any], 
                                    page_size: int, last_key: Optional[str]) -> Dict[str, Any]:
        """Build query for consumer service requests"""
        query_params = {
            'IndexName': 'ConsumerIndex',
            'KeyConditionExpression': 'consumerId = :consumerId',
            'ExpressionAttributeValues': {':consumerId': consumer_id},
            'Limit': page_size,
            'ScanIndexForward': False
        }
        
        # Add filters
        filter_expressions = []
        
        if filters.get('status'):
            filter_expressions.append('#status = :status')
            query_params['ExpressionAttributeNames'] = {'#status': 'status'}
            query_params['ExpressionAttributeValues'][':status'] = filters['status']
        
        if filters.get('deviceId'):
            filter_expressions.append('deviceId = :deviceId')
            query_params['ExpressionAttributeValues'][':deviceId'] = filters['deviceId']
        
        if filter_expressions:
            query_params['FilterExpression'] = ' AND '.join(filter_expressions)
        
        if last_key:
            query_params['ExclusiveStartKey'] = json.loads(last_key)
        
        return query_params
    
    def _build_technician_service_query(self, technician_id: str, filters: Dict[str, Any], 
                                       page_size: int, last_key: Optional[str]) -> Dict[str, Any]:
        """Build query for technician service requests"""
        query_params = {
            'IndexName': 'TechnicianIndex',
            'KeyConditionExpression': 'technicianId = :technicianId',
            'ExpressionAttributeValues': {':technicianId': technician_id},
            'Limit': page_size,
            'ScanIndexForward': False
        }
        
        # Add filters
        filter_expressions = []
        
        if filters.get('status'):
            filter_expressions.append('#status = :status')
            query_params['ExpressionAttributeNames'] = {'#status': 'status'}
            query_params['ExpressionAttributeValues'][':status'] = filters['status']
        
        if filter_expressions:
            query_params['FilterExpression'] = ' AND '.join(filter_expressions)
        
        if last_key:
            query_params['ExclusiveStartKey'] = json.loads(last_key)
        
        return query_params
    
    def _build_admin_service_query(self, filters: Dict[str, Any], 
                                  page_size: int, last_key: Optional[str]) -> Dict[str, Any]:
        """Build scan for admin service requests"""
        scan_params = {
            'Limit': page_size,
            'Select': 'ALL_ATTRIBUTES'
        }
        
        # Add filters
        filter_expressions = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        if filters.get('status'):
            filter_expressions.append('#status = :status')
            expression_attribute_names['#status'] = 'status'
            expression_attribute_values[':status'] = filters['status']
        
        if filters.get('priority'):
            filter_expressions.append('priority = :priority')
            expression_attribute_values[':priority'] = filters['priority']
        
        if filters.get('technicianId'):
            filter_expressions.append('technicianId = :technicianId')
            expression_attribute_values[':technicianId'] = filters['technicianId']
        
        if filter_expressions:
            scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
        
        if expression_attribute_names:
            scan_params['ExpressionAttributeNames'] = expression_attribute_names
        
        if expression_attribute_values:
            scan_params['ExpressionAttributeValues'] = expression_attribute_values
        
        if last_key:
            scan_params['ExclusiveStartKey'] = json.loads(last_key)
        
        return scan_params
    
    def get_analytics_data_optimized(self, query_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimized analytics queries with caching and aggregation
        """
        try:
            cache_key = f"analytics:{query_type}:{hashlib.md5(json.dumps(parameters, sort_keys=True).encode()).hexdigest()}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            if query_type == 'device_performance':
                result = self._get_device_performance_analytics(parameters)
            elif query_type == 'water_quality_trends':
                result = self._get_water_quality_trends_analytics(parameters)
            elif query_type == 'service_metrics':
                result = self._get_service_metrics_analytics(parameters)
            elif query_type == 'system_health':
                result = self._get_system_health_analytics(parameters)
            else:
                raise ValueError(f"Unknown analytics query type: {query_type}")
            
            # Cache result with longer TTL for analytics
            self._set_cache(cache_key, json.dumps(result), ttl=CACHE_TTL * 4)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {str(e)}")
            raise
    
    def _get_device_performance_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get device performance analytics"""
        try:
            device_ids = parameters.get('deviceIds', [])
            start_date = datetime.fromisoformat(parameters['startDate'])
            end_date = datetime.fromisoformat(parameters['endDate'])
            
            performance_data = {}
            
            for device_id in device_ids:
                readings = self.get_device_readings_optimized(device_id, start_date, end_date, limit=5000)
                
                # Calculate performance metrics
                total_readings = len(readings)
                uptime_percentage = self._calculate_device_uptime(readings, start_date, end_date)
                avg_wqi = sum(float(r.get('wqi', 0)) for r in readings) / total_readings if total_readings > 0 else 0
                anomaly_count = sum(1 for r in readings if r.get('anomalyType') != 'normal')
                
                performance_data[device_id] = {
                    'totalReadings': total_readings,
                    'uptimePercentage': uptime_percentage,
                    'averageWQI': round(avg_wqi, 2),
                    'anomalyCount': anomaly_count,
                    'anomalyRate': round((anomaly_count / total_readings * 100) if total_readings > 0 else 0, 2)
                }
            
            return {
                'devicePerformance': performance_data,
                'timeRange': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting device performance analytics: {str(e)}")
            return {}
    
    def _calculate_device_uptime(self, readings: List[Dict[str, Any]], 
                                start_date: datetime, end_date: datetime) -> float:
        """Calculate device uptime percentage"""
        try:
            if not readings:
                return 0.0
            
            # Expected readings (every 30 seconds)
            total_duration = (end_date - start_date).total_seconds()
            expected_readings = int(total_duration / 30)
            actual_readings = len(readings)
            
            uptime = min(100.0, (actual_readings / expected_readings * 100)) if expected_readings > 0 else 0
            return round(uptime, 2)
            
        except Exception as e:
            logger.error(f"Error calculating device uptime: {str(e)}")
            return 0.0
    
    def batch_write_readings(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimized batch write for readings with automatic partitioning
        """
        try:
            success_count = 0
            error_count = 0
            
            # Group readings by partition key for efficient batch writes
            partitioned_readings = {}
            
            for reading in readings:
                device_id = reading['deviceId']
                timestamp = datetime.fromisoformat(reading['timestamp'])
                partition_key = f"{device_id}#{timestamp.strftime('%Y%m')}"
                
                if partition_key not in partitioned_readings:
                    partitioned_readings[partition_key] = []
                
                # Prepare item for DynamoDB
                item = {
                    'deviceId#YYYYMM': partition_key,
                    'timestamp': reading['timestamp'],
                    **reading
                }
                
                partitioned_readings[partition_key].append(item)
            
            # Batch write each partition
            for partition_key, partition_readings in partitioned_readings.items():
                # Process in batches of 25 (DynamoDB limit)
                for i in range(0, len(partition_readings), 25):
                    batch = partition_readings[i:i+25]
                    
                    try:
                        with readings_table.batch_writer() as batch_writer:
                            for item in batch:
                                batch_writer.put_item(Item=item)
                        
                        success_count += len(batch)
                        
                    except ClientError as e:
                        logger.error(f"Batch write error for partition {partition_key}: {str(e)}")
                        error_count += len(batch)
            
            return {
                'successCount': success_count,
                'errorCount': error_count,
                'totalProcessed': success_count + error_count
            }
            
        except Exception as e:
            logger.error(f"Error in batch write readings: {str(e)}")
            raise
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            if self.cache:
                return self.cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    def _set_cache(self, key: str, value: str, ttl: int = CACHE_TTL):
        """Set value in cache"""
        try:
            if self.cache:
                self.cache.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        try:
            if self.cache:
                keys = self.cache.keys(pattern)
                if keys:
                    self.cache.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")


# Global instance
dal = DataAccessLayer()


def get_data_access_layer() -> DataAccessLayer:
    """Get global data access layer instance"""
    return dal