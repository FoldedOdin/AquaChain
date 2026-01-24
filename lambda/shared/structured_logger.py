"""
Structured logging module for AquaChain Lambda functions.

This module provides JSON-formatted logging with standard fields for
consistent log aggregation and analysis across all Lambda functions.
Enhanced for dashboard overhaul with correlation IDs, performance metrics,
and monitoring capabilities.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
import os
import boto3
from botocore.exceptions import ClientError


class PerformanceMetrics:
    """
    Performance metrics collection for structured logging
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {}
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = os.environ.get('CLOUDWATCH_NAMESPACE', 'AquaChain/Dashboard')
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation"""
        self.metrics[f"{operation}_start"] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration"""
        start_key = f"{operation}_start"
        if start_key in self.metrics:
            duration = time.time() - self.metrics[start_key]
            self.metrics[f"{operation}_duration_ms"] = duration * 1000
            del self.metrics[start_key]
            return duration
        return 0.0
    
    def add_metric(self, name: str, value: Union[int, float], unit: str = 'Count') -> None:
        """Add a custom metric"""
        self.metrics[name] = {'value': value, 'unit': unit}
    
    def get_execution_duration(self) -> float:
        """Get total execution duration"""
        return (time.time() - self.start_time) * 1000
    
    def publish_to_cloudwatch(self, service_name: str, additional_dimensions: Optional[Dict[str, str]] = None) -> None:
        """Publish metrics to CloudWatch"""
        try:
            dimensions = [
                {'Name': 'Service', 'Value': service_name},
                {'Name': 'Environment', 'Value': os.environ.get('ENVIRONMENT', 'dev')}
            ]
            
            if additional_dimensions:
                for key, value in additional_dimensions.items():
                    dimensions.append({'Name': key, 'Value': value})
            
            metric_data = []
            
            # Add execution duration
            metric_data.append({
                'MetricName': 'ExecutionDuration',
                'Value': self.get_execution_duration(),
                'Unit': 'Milliseconds',
                'Dimensions': dimensions
            })
            
            # Add custom metrics
            for name, metric in self.metrics.items():
                if isinstance(metric, dict) and 'value' in metric:
                    metric_data.append({
                        'MetricName': name,
                        'Value': metric['value'],
                        'Unit': metric.get('unit', 'Count'),
                        'Dimensions': dimensions
                    })
                elif name.endswith('_duration_ms'):
                    metric_data.append({
                        'MetricName': name.replace('_duration_ms', 'Duration'),
                        'Value': metric,
                        'Unit': 'Milliseconds',
                        'Dimensions': dimensions
                    })
            
            # Publish in batches of 20 (CloudWatch limit)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
        
        except Exception as e:
            # Don't fail the main operation if metrics publishing fails
            print(f"Failed to publish metrics to CloudWatch: {e}")


class StructuredLogger:
    """
    Enhanced structured logger that outputs JSON-formatted logs with standard fields.
    
    Standard fields included in every log entry:
    - timestamp: ISO 8601 formatted UTC timestamp
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - message: Human-readable log message
    - service: Name of the service/Lambda function
    - request_id: AWS request ID for tracing
    - correlation_id: Correlation ID for request tracing
    - user_id: User identifier (if available)
    - performance_metrics: Performance data for the operation
    
    Additional custom fields can be passed via kwargs.
    """
    
    def __init__(self, name: str, service: str = "unknown"):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name (typically __name__)
            service: Service/Lambda function name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.service = service
        self.performance_metrics = PerformanceMetrics()
        
        # Remove existing handlers to avoid duplicate logs
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
    
    def _format_log_entry(
        self,
        level: str,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Format a log entry as JSON with standard fields.
        
        Args:
            level: Log level
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields
            
        Returns:
            JSON-formatted log string
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.upper(),
            'message': message,
            'service': self.service,
        }
        
        # Add optional standard fields
        if request_id:
            log_entry['request_id'] = request_id
        if correlation_id:
            log_entry['correlation_id'] = correlation_id
        if user_id:
            log_entry['user_id'] = user_id
        if operation:
            log_entry['operation'] = operation
        if duration_ms is not None:
            log_entry['duration_ms'] = duration_ms
        
        # Add performance metrics if available
        if hasattr(self, 'performance_metrics') and self.performance_metrics.metrics:
            log_entry['performance_metrics'] = {
                'execution_duration_ms': self.performance_metrics.get_execution_duration(),
                'custom_metrics': self.performance_metrics.metrics
            }
        
        # Add custom fields
        for key, value in kwargs.items():
            if key not in log_entry:
                log_entry[key] = value
        
        return json.dumps(log_entry)
    
    def log(
        self,
        level: str,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log a message with the specified level.
        
        Args:
            level: Log level (info, warning, error, debug, critical)
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields (e.g., device_id, error_code)
        """
        log_entry = self._format_log_entry(
            level, message, request_id, correlation_id, user_id, 
            operation, duration_ms, **kwargs
        )
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, log_entry)
    
    def info(
        self,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log an info-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields
        """
        self.log('info', message, request_id, correlation_id, user_id, operation, duration_ms, **kwargs)
    
    def warning(
        self,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log a warning-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields
        """
        self.log('warning', message, request_id, correlation_id, user_id, operation, duration_ms, **kwargs)
    
    def error(
        self,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log an error-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields (e.g., error_code, stack_trace)
        """
        self.log('error', message, request_id, correlation_id, user_id, operation, duration_ms, **kwargs)
    
    def debug(
        self,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log a debug-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields
        """
        self.log('debug', message, request_id, correlation_id, user_id, operation, duration_ms, **kwargs)
    
    def critical(
        self,
        message: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log a critical-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            correlation_id: Correlation ID for request tracing
            user_id: User identifier
            operation: Operation being performed
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional custom fields
        """
        self.log('critical', message, request_id, correlation_id, user_id, operation, duration_ms, **kwargs)
    
    def start_operation(self, operation: str) -> None:
        """Start timing an operation"""
        self.performance_metrics.start_timer(operation)
    
    def end_operation(self, operation: str, success: bool = True, **kwargs) -> float:
        """End timing an operation and log the result"""
        duration = self.performance_metrics.end_timer(operation)
        
        if success:
            self.info(
                f"Operation {operation} completed successfully",
                operation=operation,
                duration_ms=duration * 1000,
                **kwargs
            )
        else:
            self.warning(
                f"Operation {operation} completed with issues",
                operation=operation,
                duration_ms=duration * 1000,
                **kwargs
            )
        
        return duration
    
    def add_metric(self, name: str, value: Union[int, float], unit: str = 'Count') -> None:
        """Add a custom performance metric"""
        self.performance_metrics.add_metric(name, value, unit)
    
    def publish_metrics(self, additional_dimensions: Optional[Dict[str, str]] = None) -> None:
        """Publish collected metrics to CloudWatch"""
        self.performance_metrics.publish_to_cloudwatch(self.service, additional_dimensions)


class SystemHealthMonitor:
    """
    System health monitoring and alerting for dashboard services
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        self.namespace = os.environ.get('CLOUDWATCH_NAMESPACE', 'AquaChain/Dashboard')
        self.alert_topic_arn = os.environ.get('ALERT_TOPIC_ARN')
        self.logger = get_logger(__name__, service_name)
    
    def check_service_health(self) -> Dict[str, Any]:
        """
        Check the health of the service and its dependencies
        
        Returns:
            Health check results
        """
        health_status = {
            'service': self.service_name,
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {}
        }
        
        try:
            # Check DynamoDB connectivity
            health_status['checks']['dynamodb'] = self._check_dynamodb_health()
            
            # Check S3 connectivity
            health_status['checks']['s3'] = self._check_s3_health()
            
            # Check KMS connectivity
            health_status['checks']['kms'] = self._check_kms_health()
            
            # Determine overall health
            failed_checks = [name for name, check in health_status['checks'].items() if not check['healthy']]
            
            if failed_checks:
                health_status['status'] = 'degraded' if len(failed_checks) == 1 else 'unhealthy'
                health_status['failed_checks'] = failed_checks
            
            # Log health status
            if health_status['status'] == 'healthy':
                self.logger.info("Service health check passed", health_status=health_status)
            else:
                self.logger.warning("Service health check failed", health_status=health_status)
                
                # Send alert for unhealthy status
                if health_status['status'] == 'unhealthy':
                    self._send_health_alert(health_status)
            
            return health_status
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['error'] = str(e)
            self.logger.error("Health check failed with exception", error=str(e))
            return health_status
    
    def _check_dynamodb_health(self) -> Dict[str, Any]:
        """Check DynamoDB connectivity"""
        try:
            dynamodb = boto3.client('dynamodb')
            dynamodb.list_tables()
            return {'healthy': True, 'response_time_ms': 0}  # Simplified
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_s3_health(self) -> Dict[str, Any]:
        """Check S3 connectivity"""
        try:
            s3 = boto3.client('s3')
            s3.list_buckets()
            return {'healthy': True, 'response_time_ms': 0}  # Simplified
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_kms_health(self) -> Dict[str, Any]:
        """Check KMS connectivity"""
        try:
            kms = boto3.client('kms')
            kms.list_keys(Limit=1)
            return {'healthy': True, 'response_time_ms': 0}  # Simplified
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _send_health_alert(self, health_status: Dict[str, Any]) -> None:
        """Send health alert via SNS"""
        if not self.alert_topic_arn:
            return
        
        try:
            message = {
                'service': self.service_name,
                'status': health_status['status'],
                'failed_checks': health_status.get('failed_checks', []),
                'timestamp': health_status['timestamp']
            }
            
            self.sns.publish(
                TopicArn=self.alert_topic_arn,
                Subject=f"Service Health Alert: {self.service_name}",
                Message=json.dumps(message, indent=2)
            )
            
        except Exception as e:
            self.logger.error("Failed to send health alert", error=str(e))
    
    def publish_health_metrics(self, health_status: Dict[str, Any]) -> None:
        """Publish health metrics to CloudWatch"""
        try:
            dimensions = [
                {'Name': 'Service', 'Value': self.service_name},
                {'Name': 'Environment', 'Value': os.environ.get('ENVIRONMENT', 'dev')}
            ]
            
            # Overall health metric
            health_value = 1 if health_status['status'] == 'healthy' else 0
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'ServiceHealth',
                        'Value': health_value,
                        'Unit': 'Count',
                        'Dimensions': dimensions
                    }
                ]
            )
            
            # Individual check metrics
            for check_name, check_result in health_status.get('checks', {}).items():
                check_value = 1 if check_result.get('healthy', False) else 0
                check_dimensions = dimensions + [{'Name': 'Check', 'Value': check_name}]
                
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'DependencyHealth',
                            'Value': check_value,
                            'Unit': 'Count',
                            'Dimensions': check_dimensions
                        }
                    ]
                )
                
        except Exception as e:
            self.logger.error("Failed to publish health metrics", error=str(e))


def get_logger(name: str, service: str = "unknown") -> StructuredLogger:
    """
    Factory function to create a StructuredLogger instance.
    
    Args:
        name: Logger name (typically __name__)
        service: Service/Lambda function name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, service)


def create_health_monitor(service_name: str) -> SystemHealthMonitor:
    """
    Factory function to create a SystemHealthMonitor instance.
    
    Args:
        service_name: Name of the service to monitor
        
    Returns:
        SystemHealthMonitor instance
    """
    return SystemHealthMonitor(service_name)


# Context manager for operation timing
class TimedOperation:
    """Context manager for timing operations with structured logging"""
    
    def __init__(self, logger: StructuredLogger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.start_operation(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        duration = self.logger.end_operation(self.operation, success, **self.kwargs)
        
        if not success:
            self.logger.error(
                f"Operation {self.operation} failed",
                operation=self.operation,
                error_type=exc_type.__name__ if exc_type else None,
                error_message=str(exc_val) if exc_val else None,
                **self.kwargs
            )
