"""
X-Ray Tracing Utilities for AquaChain Lambda Functions
Provides common tracing functionality and performance monitoring
"""

import json
import time
import boto3
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models import http


# Patch AWS SDK calls for automatic tracing
patch_all()

# Initialize CloudWatch client for custom metrics
cloudwatch = boto3.client('cloudwatch')


class AquaChainTracer:
    """AquaChain-specific X-Ray tracing utilities"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
    def trace_critical_path(self, operation_name: str):
        """Decorator for tracing critical path operations"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with xray_recorder.in_subsegment(f'{self.service_name}.{operation_name}') as subsegment:
                    start_time = time.time()
                    
                    try:
                        # Add metadata
                        subsegment.put_metadata('service', self.service_name)
                        subsegment.put_metadata('operation', operation_name)
                        subsegment.put_metadata('timestamp', datetime.utcnow().isoformat())
                        
                        # Execute function
                        result = func(*args, **kwargs)
                        
                        # Calculate and record latency
                        latency = time.time() - start_time
                        subsegment.put_metadata('latency_seconds', latency)
                        
                        # Send custom metric to CloudWatch
                        self._send_latency_metric(operation_name, latency)
                        
                        # Mark as successful
                        subsegment.put_annotation('success', True)
                        
                        return result
                        
                    except Exception as e:
                        # Record error details
                        subsegment.add_exception(e)
                        subsegment.put_annotation('success', False)
                        subsegment.put_metadata('error_type', type(e).__name__)
                        subsegment.put_metadata('error_message', str(e))
                        
                        # Send error metric
                        self._send_error_metric(operation_name, str(e))
                        
                        raise
                        
            return wrapper
        return decorator
    
    def trace_data_flow(self, data_type: str, record_count: int = 1):
        """Trace data flow through the system"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with xray_recorder.in_subsegment(f'{self.service_name}.data_flow') as subsegment:
                    # Add data flow annotations
                    subsegment.put_annotation('data_type', data_type)
                    subsegment.put_annotation('record_count', record_count)
                    subsegment.put_metadata('processing_stage', self.service_name)
                    
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    processing_time = time.time() - start_time
                    
                    # Calculate throughput
                    throughput = record_count / processing_time if processing_time > 0 else 0
                    subsegment.put_metadata('throughput_per_second', throughput)
                    subsegment.put_metadata('processing_time', processing_time)
                    
                    # Send throughput metric
                    self._send_throughput_metric(data_type, throughput)
                    
                    return result
                    
            return wrapper
        return decorator
    
    def trace_external_call(self, service_name: str, operation: str):
        """Trace external service calls"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with xray_recorder.in_subsegment(f'external.{service_name}') as subsegment:
                    subsegment.put_annotation('external_service', service_name)
                    subsegment.put_annotation('operation', operation)
                    
                    start_time = time.time()
                    
                    try:
                        result = func(*args, **kwargs)
                        
                        # Record successful external call
                        latency = time.time() - start_time
                        subsegment.put_metadata('latency_seconds', latency)
                        subsegment.put_annotation('success', True)
                        
                        # Send external service latency metric
                        self._send_external_service_metric(service_name, operation, latency, True)
                        
                        return result
                        
                    except Exception as e:
                        # Record failed external call
                        subsegment.add_exception(e)
                        subsegment.put_annotation('success', False)
                        
                        # Send failure metric
                        latency = time.time() - start_time
                        self._send_external_service_metric(service_name, operation, latency, False)
                        
                        raise
                        
            return wrapper
        return decorator
    
    def _send_latency_metric(self, operation: str, latency: float):
        """Send latency metric to CloudWatch"""
        try:
            cloudwatch.put_metric_data(
                Namespace='AquaChain/Performance',
                MetricData=[
                    {
                        'MetricName': f'{operation}Latency',
                        'Value': latency,
                        'Unit': 'Seconds',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': self.service_name
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Error sending latency metric: {e}")
    
    def _send_error_metric(self, operation: str, error_message: str):
        """Send error metric to CloudWatch"""
        try:
            cloudwatch.put_metric_data(
                Namespace='AquaChain/Reliability',
                MetricData=[
                    {
                        'MetricName': f'{operation}Errors',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': self.service_name
                            },
                            {
                                'Name': 'Operation',
                                'Value': operation
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Error sending error metric: {e}")
    
    def _send_throughput_metric(self, data_type: str, throughput: float):
        """Send throughput metric to CloudWatch"""
        try:
            cloudwatch.put_metric_data(
                Namespace='AquaChain/Throughput',
                MetricData=[
                    {
                        'MetricName': 'MessagesPerSecond',
                        'Value': throughput,
                        'Unit': 'Count/Second',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': self.service_name
                            },
                            {
                                'Name': 'DataType',
                                'Value': data_type
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Error sending throughput metric: {e}")
    
    def _send_external_service_metric(self, service: str, operation: str, latency: float, success: bool):
        """Send external service performance metric"""
        try:
            cloudwatch.put_metric_data(
                Namespace='AquaChain/ExternalServices',
                MetricData=[
                    {
                        'MetricName': f'{service}Latency',
                        'Value': latency,
                        'Unit': 'Seconds',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': service
                            },
                            {
                                'Name': 'Operation',
                                'Value': operation
                            }
                        ]
                    },
                    {
                        'MetricName': f'{service}Success',
                        'Value': 1 if success else 0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': service
                            },
                            {
                                'Name': 'Operation',
                                'Value': operation
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Error sending external service metric: {e}")


class EndToEndTracer:
    """Trace end-to-end request flows"""
    
    @staticmethod
    def start_trace(trace_id: str, source: str, event_type: str):
        """Start an end-to-end trace"""
        with xray_recorder.in_subsegment('end_to_end_start') as subsegment:
            subsegment.put_annotation('trace_id', trace_id)
            subsegment.put_annotation('source', source)
            subsegment.put_annotation('event_type', event_type)
            subsegment.put_metadata('start_timestamp', datetime.utcnow().isoformat())
            
            # Store trace start time in X-Ray context
            xray_recorder.current_subsegment().put_metadata('e2e_start_time', time.time())
    
    @staticmethod
    def end_trace(trace_id: str, destination: str, success: bool = True):
        """End an end-to-end trace and calculate total latency"""
        with xray_recorder.in_subsegment('end_to_end_complete') as subsegment:
            subsegment.put_annotation('trace_id', trace_id)
            subsegment.put_annotation('destination', destination)
            subsegment.put_annotation('success', success)
            subsegment.put_metadata('end_timestamp', datetime.utcnow().isoformat())
            
            # Calculate end-to-end latency
            try:
                start_time = xray_recorder.current_subsegment().get_metadata().get('e2e_start_time')
                if start_time:
                    end_to_end_latency = time.time() - start_time
                    subsegment.put_metadata('end_to_end_latency', end_to_end_latency)
                    
                    # Send end-to-end latency metric
                    cloudwatch.put_metric_data(
                        Namespace='AquaChain/Performance',
                        MetricData=[
                            {
                                'MetricName': 'EndToEndLatency',
                                'Value': end_to_end_latency,
                                'Unit': 'Seconds',
                                'Dimensions': [
                                    {
                                        'Name': 'TraceType',
                                        'Value': f'{subsegment.get_annotation("source")}_to_{destination}'
                                    }
                                ]
                            }
                        ]
                    )
            except Exception as e:
                print(f"Error calculating end-to-end latency: {e}")


def create_custom_segment(name: str, metadata: Dict[str, Any] = None):
    """Create a custom X-Ray segment with metadata"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with xray_recorder.in_subsegment(name) as subsegment:
                # Add custom metadata
                if metadata:
                    for key, value in metadata.items():
                        subsegment.put_metadata(key, value)
                
                # Add function metadata
                subsegment.put_metadata('function_name', func.__name__)
                subsegment.put_metadata('timestamp', datetime.utcnow().isoformat())
                
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


def trace_lambda_handler(service_name: str):
    """Decorator for Lambda handlers to add comprehensive tracing"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(event, context):
            # Set service name for X-Ray
            xray_recorder.configure(service=service_name)
            
            with xray_recorder.in_subsegment(f'{service_name}.handler') as subsegment:
                # Add Lambda context metadata
                subsegment.put_metadata('aws_request_id', context.aws_request_id)
                subsegment.put_metadata('function_name', context.function_name)
                subsegment.put_metadata('function_version', context.function_version)
                subsegment.put_metadata('memory_limit', context.memory_limit_in_mb)
                subsegment.put_metadata('remaining_time', context.get_remaining_time_in_millis())
                
                # Add event metadata (sanitized)
                event_type = event.get('Records', [{}])[0].get('eventSource', 'unknown') if 'Records' in event else 'api_gateway'
                subsegment.put_annotation('event_type', event_type)
                subsegment.put_annotation('service', service_name)
                
                start_time = time.time()
                
                try:
                    result = func(event, context)
                    
                    # Record successful execution
                    execution_time = time.time() - start_time
                    subsegment.put_metadata('execution_time', execution_time)
                    subsegment.put_annotation('success', True)
                    
                    # Send execution time metric
                    cloudwatch.put_metric_data(
                        Namespace='AquaChain/Lambda',
                        MetricData=[
                            {
                                'MetricName': 'ExecutionTime',
                                'Value': execution_time,
                                'Unit': 'Seconds',
                                'Dimensions': [
                                    {
                                        'Name': 'FunctionName',
                                        'Value': service_name
                                    }
                                ]
                            }
                        ]
                    )
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    subsegment.add_exception(e)
                    subsegment.put_annotation('success', False)
                    
                    # Send error metric
                    cloudwatch.put_metric_data(
                        Namespace='AquaChain/Lambda',
                        MetricData=[
                            {
                                'MetricName': 'Errors',
                                'Value': 1,
                                'Unit': 'Count',
                                'Dimensions': [
                                    {
                                        'Name': 'FunctionName',
                                        'Value': service_name
                                    }
                                ]
                            }
                        ]
                    )
                    
                    raise
                    
        return wrapper
    return decorator


# Example usage patterns
if __name__ == "__main__":
    # Example of how to use the tracing utilities
    tracer = AquaChainTracer('data-processing')
    
    @tracer.trace_critical_path('validate_sensor_data')
    def validate_sensor_data(data):
        # Validation logic here
        return True
    
    @tracer.trace_data_flow('sensor_readings', 100)
    def process_sensor_batch(readings):
        # Processing logic here
        return readings
    
    @tracer.trace_external_call('dynamodb', 'put_item')
    def store_reading(reading):
        # DynamoDB storage logic here
        return True
    
    print("X-Ray tracing utilities configured successfully!")