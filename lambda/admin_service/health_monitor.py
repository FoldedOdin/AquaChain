"""
System Health Monitoring Module
Provides health check functions for AWS services used by AquaChain.

This module implements centralized health monitoring for all critical AWS services
with caching, timeout protection, and graceful error handling.
"""

import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients (initialized once at module load)
cloudwatch = boto3.client('cloudwatch')
iot = boto3.client('iot')
lambda_client = boto3.client('lambda')
dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

# Cache for health status (30 seconds)
_health_cache = {}
_cache_timestamp = None
CACHE_DURATION_SECONDS = 30
CHECK_TIMEOUT_SECONDS = 2


def get_system_health(force_refresh: bool = False) -> Dict:
    """
    Get health status for all monitored services.
    
    Implements 30-second caching to prevent excessive AWS API calls.
    Uses ThreadPoolExecutor for parallel health checks with 2-second timeout per check.
    
    Args:
        force_refresh: If True, bypass cache and fetch fresh data
    
    Returns:
        Dict with structure:
        {
            'services': [ServiceHealth, ...],
            'overallStatus': 'healthy' | 'degraded' | 'down',
            'checkedAt': 'ISO8601 timestamp',
            'cacheHit': bool
        }
    """
    global _health_cache, _cache_timestamp
    
    # Check cache
    if not force_refresh and _cache_timestamp:
        age = (datetime.utcnow() - _cache_timestamp).total_seconds()
        if age < CACHE_DURATION_SECONDS:
            logger.info(f"Returning cached health status (age: {age:.1f}s)")
            return {**_health_cache, 'cacheHit': True}
    
    # Fetch fresh health data
    logger.info("Fetching fresh health status for all services")
    start_time = time.time()
    
    # Execute health checks in parallel with timeout protection
    services = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_check_iot_core_health): 'IoT Core',
            executor.submit(_check_lambda_health): 'Lambda',
            executor.submit(_check_dynamodb_health): 'DynamoDB',
            executor.submit(_check_sns_health): 'SNS',
            executor.submit(_check_ml_inference_health): 'ML Inference'
        }
        
        for future in futures:
            service_name = futures[future]
            try:
                # Wait for result with timeout
                result = future.result(timeout=CHECK_TIMEOUT_SECONDS)
                services.append(result)
            except FuturesTimeoutError:
                logger.warning(f"{service_name} health check timed out after {CHECK_TIMEOUT_SECONDS}s")
                services.append({
                    'name': service_name,
                    'status': 'unknown',
                    'lastCheck': datetime.utcnow().isoformat() + 'Z',
                    'message': 'Health check timed out'
                })
            except Exception as e:
                logger.error(f"{service_name} health check failed: {str(e)}")
                services.append({
                    'name': service_name,
                    'status': 'unknown',
                    'lastCheck': datetime.utcnow().isoformat() + 'Z',
                    'message': 'Health check failed'
                })
    
    # Determine overall status
    statuses = [s['status'] for s in services]
    if 'down' in statuses:
        overall = 'down'
    elif 'degraded' in statuses:
        overall = 'degraded'
    elif 'unknown' in statuses:
        overall = 'degraded'  # Treat unknown as degraded
    else:
        overall = 'healthy'
    
    elapsed = time.time() - start_time
    logger.info(f"Health check completed in {elapsed:.2f}s, overall status: {overall}")
    
    result = {
        'services': services,
        'overallStatus': overall,
        'checkedAt': datetime.utcnow().isoformat() + 'Z',
        'cacheHit': False
    }
    
    # Update cache
    _health_cache = result
    _cache_timestamp = datetime.utcnow()
    
    return result


def _check_iot_core_health() -> Dict:
    """
    Check IoT Core health via CloudWatch metrics.
    
    Monitors MQTT message throughput over the last 5 minutes.
    Status: healthy if metrics are available, unknown on error.
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # Query CloudWatch for IoT Core PublishIn.Success metric
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/IoT',
            MetricName='PublishIn.Success',
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        # If we have data points, IoT Core is operational
        if response['Datapoints']:
            message_count = sum(dp['Sum'] for dp in response['Datapoints'])
            return {
                'name': 'IoT Core',
                'status': 'healthy',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'messagesLast5Min': int(message_count)
                }
            }
        else:
            # No data points might mean no traffic (not necessarily down)
            return {
                'name': 'IoT Core',
                'status': 'healthy',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'messagesLast5Min': 0
                },
                'message': 'No recent MQTT traffic'
            }
    
    except Exception as e:
        logger.error(f"IoT Core health check failed: {str(e)}")
        return {
            'name': 'IoT Core',
            'status': 'unknown',
            'lastCheck': datetime.utcnow().isoformat() + 'Z',
            'message': 'Health check failed'
        }


def _check_lambda_health() -> Dict:
    """
    Check Lambda health via CloudWatch metrics.
    
    Monitors invocation success rate over the last 5 minutes.
    Status: healthy (>=95%), degraded (>=90%), down (<90%)
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # Get invocation count
        invocations = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        # Get error count
        errors = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        total_invocations = sum(dp['Sum'] for dp in invocations['Datapoints'])
        total_errors = sum(dp['Sum'] for dp in errors['Datapoints'])
        
        if total_invocations > 0:
            success_rate = ((total_invocations - total_errors) / total_invocations) * 100
            
            if success_rate >= 95:
                status = 'healthy'
            elif success_rate >= 90:
                status = 'degraded'
            else:
                status = 'down'
            
            return {
                'name': 'Lambda',
                'status': status,
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'successRate': round(success_rate, 2),
                    'invocations': int(total_invocations),
                    'errors': int(total_errors)
                }
            }
        else:
            # No invocations in last 5 minutes - not necessarily a problem
            return {
                'name': 'Lambda',
                'status': 'healthy',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'invocations': 0
                },
                'message': 'No recent invocations'
            }
    
    except Exception as e:
        logger.error(f"Lambda health check failed: {str(e)}")
        return {
            'name': 'Lambda',
            'status': 'unknown',
            'lastCheck': datetime.utcnow().isoformat() + 'Z',
            'message': 'Health check failed'
        }


def _check_dynamodb_health() -> Dict:
    """
    Check DynamoDB health via table status.
    
    Verifies that critical tables are in ACTIVE state.
    Status: healthy (all active), degraded (some not active), unknown (check failed)
    """
    try:
        # Check main tables
        tables_to_check = [
            'AquaChain-SystemConfig',
            'AquaChain-Users',
            'AquaChain-Devices'
        ]
        
        all_active = True
        checked_count = 0
        
        for table_name in tables_to_check:
            try:
                response = dynamodb.describe_table(TableName=table_name)
                if response['Table']['TableStatus'] != 'ACTIVE':
                    all_active = False
                    logger.warning(f"Table {table_name} status: {response['Table']['TableStatus']}")
                checked_count += 1
            except dynamodb.exceptions.ResourceNotFoundException:
                logger.warning(f"Table {table_name} not found")
                all_active = False
            except Exception as e:
                logger.error(f"Failed to check table {table_name}: {str(e)}")
                all_active = False
        
        if all_active and checked_count == len(tables_to_check):
            return {
                'name': 'DynamoDB',
                'status': 'healthy',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'tablesChecked': checked_count
                }
            }
        else:
            return {
                'name': 'DynamoDB',
                'status': 'degraded',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'tablesChecked': checked_count
                },
                'message': 'One or more tables not active'
            }
    
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {str(e)}")
        return {
            'name': 'DynamoDB',
            'status': 'unknown',
            'lastCheck': datetime.utcnow().isoformat() + 'Z',
            'message': 'Health check failed'
        }


def _check_sns_health() -> Dict:
    """
    Check SNS health via CloudWatch metrics.
    
    Monitors message delivery rate over the last 5 minutes.
    Status: healthy (>=98%), degraded (>=95%), down (<95%)
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # Get published messages
        published = cloudwatch.get_metric_statistics(
            Namespace='AWS/SNS',
            MetricName='NumberOfMessagesPublished',
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        # Get delivery failures
        failed = cloudwatch.get_metric_statistics(
            Namespace='AWS/SNS',
            MetricName='NumberOfNotificationsFailed',
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum']
        )
        
        total_published = sum(dp['Sum'] for dp in published['Datapoints'])
        total_failed = sum(dp['Sum'] for dp in failed['Datapoints'])
        
        if total_published > 0:
            delivery_rate = ((total_published - total_failed) / total_published) * 100
            
            if delivery_rate >= 98:
                status = 'healthy'
            elif delivery_rate >= 95:
                status = 'degraded'
            else:
                status = 'down'
            
            return {
                'name': 'SNS',
                'status': status,
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'deliveryRate': round(delivery_rate, 2),
                    'published': int(total_published),
                    'failed': int(total_failed)
                }
            }
        else:
            # No notifications in last 5 minutes - not necessarily a problem
            return {
                'name': 'SNS',
                'status': 'healthy',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'published': 0
                },
                'message': 'No recent notifications'
            }
    
    except Exception as e:
        logger.error(f"SNS health check failed: {str(e)}")
        return {
            'name': 'SNS',
            'status': 'unknown',
            'lastCheck': datetime.utcnow().isoformat() + 'Z',
            'message': 'Health check failed'
        }


def _check_ml_inference_health() -> Dict:
    """
    Check ML Inference Lambda health via CloudWatch metrics.
    
    Monitors prediction latency over the last 5 minutes.
    Status: healthy (<500ms), degraded (<1000ms), down (>=1000ms)
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # Get ML inference Lambda duration metrics
        duration = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': 'aquachain-ml-inference'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )
        
        if duration['Datapoints']:
            avg_latency = duration['Datapoints'][0]['Average']
            
            if avg_latency < 500:
                status = 'healthy'
            elif avg_latency < 1000:
                status = 'degraded'
            else:
                status = 'down'
            
            return {
                'name': 'ML Inference',
                'status': status,
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'metrics': {
                    'avgLatency': round(avg_latency, 2)
                }
            }
        else:
            # No predictions in last 5 minutes - not necessarily a problem
            return {
                'name': 'ML Inference',
                'status': 'healthy',
                'lastCheck': datetime.utcnow().isoformat() + 'Z',
                'message': 'No recent predictions'
            }
    
    except Exception as e:
        logger.error(f"ML Inference health check failed: {str(e)}")
        return {
            'name': 'ML Inference',
            'status': 'unknown',
            'lastCheck': datetime.utcnow().isoformat() + 'Z',
            'message': 'Health check failed'
        }
