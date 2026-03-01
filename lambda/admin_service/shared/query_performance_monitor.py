"""
Query performance monitoring for DynamoDB GSI queries (Phase 4)
Publishes performance metrics to CloudWatch for monitoring and alerting
"""

import boto3
from typing import Dict, List, Optional
from datetime import datetime
from structured_logger import StructuredLogger

cloudwatch = boto3.client('cloudwatch')
logger = StructuredLogger(__name__)

# Performance threshold for warnings (500ms)
QUERY_PERFORMANCE_THRESHOLD_MS = 500


class QueryPerformanceMonitor:
    """
    Monitor and publish DynamoDB query performance metrics to CloudWatch
    """
    
    def __init__(self, namespace: str = 'AquaChain/DynamoDB'):
        self.namespace = namespace
    
    def publish_query_metrics(self, operation: str, duration_ms: float,
                             item_count: int, dimensions: Optional[Dict] = None):
        """
        Publish query performance metrics to CloudWatch
        
        Args:
            operation: Query operation name (e.g., 'query_devices_by_user')
            duration_ms: Query duration in milliseconds
            item_count: Number of items returned
            dimensions: Additional dimensions for the metric
        """
        try:
            # Build metric dimensions
            metric_dimensions = [
                {'Name': 'Operation', 'Value': operation}
            ]
            
            if dimensions:
                for key, value in dimensions.items():
                    metric_dimensions.append({'Name': key, 'Value': str(value)})
            
            # Publish metrics
            cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'QueryDuration',
                        'Value': duration_ms,
                        'Unit': 'Milliseconds',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': metric_dimensions
                    },
                    {
                        'MetricName': 'ItemCount',
                        'Value': item_count,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': metric_dimensions
                    }
                ]
            )
            
            # Log warning if query exceeds threshold
            if duration_ms > QUERY_PERFORMANCE_THRESHOLD_MS:
                logger.log('warning', f'Query exceeded performance threshold',
                    service='query_performance_monitor',
                    operation=operation,
                    duration_ms=duration_ms,
                    threshold_ms=QUERY_PERFORMANCE_THRESHOLD_MS,
                    item_count=item_count
                )
                
                # Publish threshold violation metric
                cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'SlowQueryCount',
                            'Value': 1,
                            'Unit': 'Count',
                            'Timestamp': datetime.utcnow(),
                            'Dimensions': metric_dimensions
                        }
                    ]
                )
            
        except Exception as e:
            # Don't fail the query if metrics publishing fails
            logger.log('error', f'Failed to publish query metrics: {e}',
                service='query_performance_monitor',
                operation=operation,
                error=str(e)
            )
    
    def publish_gsi_usage_metrics(self, table_name: str, index_name: str,
                                  read_capacity_units: float):
        """
        Publish GSI usage metrics to CloudWatch
        
        Args:
            table_name: DynamoDB table name
            index_name: GSI name
            read_capacity_units: RCUs consumed by the query
        """
        try:
            cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'GSIReadCapacityUnits',
                        'Value': read_capacity_units,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {'Name': 'TableName', 'Value': table_name},
                            {'Name': 'IndexName', 'Value': index_name}
                        ]
                    }
                ]
            )
            
        except Exception as e:
            logger.log('error', f'Failed to publish GSI usage metrics: {e}',
                service='query_performance_monitor',
                table_name=table_name,
                index_name=index_name,
                error=str(e)
            )
    
    def create_performance_alarm(self, alarm_name: str, operation: str,
                                threshold_ms: float = 500,
                                evaluation_periods: int = 2,
                                sns_topic_arn: Optional[str] = None):
        """
        Create CloudWatch alarm for query performance
        
        Args:
            alarm_name: Name for the alarm
            operation: Query operation to monitor
            threshold_ms: Threshold in milliseconds
            evaluation_periods: Number of periods to evaluate
            sns_topic_arn: Optional SNS topic for notifications
        """
        try:
            alarm_config = {
                'AlarmName': alarm_name,
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': evaluation_periods,
                'MetricName': 'QueryDuration',
                'Namespace': self.namespace,
                'Period': 60,  # 1 minute
                'Statistic': 'Average',
                'Threshold': threshold_ms,
                'ActionsEnabled': True,
                'AlarmDescription': f'Alert when {operation} query duration exceeds {threshold_ms}ms',
                'Dimensions': [
                    {'Name': 'Operation', 'Value': operation}
                ],
                'TreatMissingData': 'notBreaching'
            }
            
            if sns_topic_arn:
                alarm_config['AlarmActions'] = [sns_topic_arn]
            
            cloudwatch.put_metric_alarm(**alarm_config)
            
            logger.log('info', f'Created performance alarm: {alarm_name}',
                service='query_performance_monitor',
                alarm_name=alarm_name,
                operation=operation,
                threshold_ms=threshold_ms
            )
            
        except Exception as e:
            logger.log('error', f'Failed to create performance alarm: {e}',
                service='query_performance_monitor',
                alarm_name=alarm_name,
                error=str(e)
            )


# Global monitor instance
performance_monitor = QueryPerformanceMonitor()


def track_query_performance(operation: str):
    """
    Decorator to track query performance metrics
    
    Usage:
        @track_query_performance('query_devices_by_user')
        def my_query_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract item count from result if available
                item_count = 0
                if isinstance(result, dict):
                    if 'items' in result:
                        item_count = len(result['items'])
                    elif 'Items' in result:
                        item_count = len(result['Items'])
                
                # Publish metrics
                performance_monitor.publish_query_metrics(
                    operation=operation,
                    duration_ms=duration_ms,
                    item_count=item_count
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Log error with duration
                logger.log('error', f'Query failed: {operation}',
                    service='query_performance_monitor',
                    operation=operation,
                    duration_ms=duration_ms,
                    error=str(e)
                )
                
                raise
        
        return wrapper
    return decorator
