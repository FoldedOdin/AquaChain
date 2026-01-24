"""
CloudWatch custom metrics for shipment tracking

This module provides utilities for emitting CloudWatch custom metrics
for monitoring shipment operations.

Requirements: 14.1
"""
import boto3
from datetime import datetime
from typing import Dict, Any, Optional, List

cloudwatch = boto3.client('cloudwatch')

# Namespace for all shipment metrics
NAMESPACE = 'AquaChain/Shipments'


def emit_shipment_created(shipment_id: str, order_id: str, courier_name: str):
    """
    Emit ShipmentsCreated metric when a shipment is created
    
    Args:
        shipment_id: Shipment ID
        order_id: Order ID
        courier_name: Courier service name
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'ShipmentsCreated',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Courier', 'Value': courier_name}
                    ]
                }
            ]
        )
        print(f"INFO: Emitted ShipmentsCreated metric for {shipment_id}")
    except Exception as e:
        # Don't fail the operation if metrics fail
        print(f"WARNING: Failed to emit ShipmentsCreated metric: {str(e)}")


def emit_webhook_processed(tracking_number: str, courier_name: str, status: str, success: bool = True):
    """
    Emit WebhooksProcessed metric when a webhook is handled
    
    Args:
        tracking_number: Tracking number
        courier_name: Courier service name
        status: Internal status
        success: Whether webhook processing succeeded
    """
    try:
        metrics = [
            {
                'MetricName': 'WebhooksProcessed',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'Courier', 'Value': courier_name},
                    {'Name': 'Status', 'Value': status},
                    {'Name': 'Success', 'Value': 'true' if success else 'false'}
                ]
            }
        ]
        
        # Also emit error metric if processing failed
        if not success:
            metrics.append({
                'MetricName': 'WebhookErrors',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'Courier', 'Value': courier_name}
                ]
            })
        
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=metrics
        )
        print(f"INFO: Emitted WebhooksProcessed metric for {tracking_number}")
    except Exception as e:
        print(f"WARNING: Failed to emit WebhooksProcessed metric: {str(e)}")


def emit_delivery_time(shipment_id: str, courier_name: str, hours: float):
    """
    Emit DeliveryTime metric when delivery is confirmed
    
    Calculates time from shipment creation to delivery in hours.
    
    Args:
        shipment_id: Shipment ID
        courier_name: Courier service name
        hours: Delivery time in hours
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'DeliveryTime',
                    'Value': hours,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Courier', 'Value': courier_name}
                    ]
                }
            ]
        )
        print(f"INFO: Emitted DeliveryTime metric for {shipment_id}: {hours} hours")
    except Exception as e:
        print(f"WARNING: Failed to emit DeliveryTime metric: {str(e)}")


def emit_failed_delivery(shipment_id: str, courier_name: str, retry_count: int):
    """
    Emit FailedDeliveries metric when delivery fails
    
    Args:
        shipment_id: Shipment ID
        courier_name: Courier service name
        retry_count: Number of failed attempts
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'FailedDeliveries',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Courier', 'Value': courier_name},
                        {'Name': 'RetryCount', 'Value': str(retry_count)}
                    ]
                }
            ]
        )
        print(f"INFO: Emitted FailedDeliveries metric for {shipment_id}")
    except Exception as e:
        print(f"WARNING: Failed to emit FailedDeliveries metric: {str(e)}")


def emit_stale_shipments(count: int):
    """
    Emit StaleShipments metric for monitoring
    
    Args:
        count: Number of stale shipments detected
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'StaleShipments',
                    'Value': count,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        print(f"INFO: Emitted StaleShipments metric: {count}")
    except Exception as e:
        print(f"WARNING: Failed to emit StaleShipments metric: {str(e)}")


def emit_lambda_error(function_name: str, error_type: str):
    """
    Emit LambdaErrors metric for error tracking
    
    Args:
        function_name: Name of the Lambda function
        error_type: Type of error that occurred
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'LambdaErrors',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': function_name},
                        {'Name': 'ErrorType', 'Value': error_type}
                    ]
                }
            ]
        )
        print(f"INFO: Emitted LambdaErrors metric for {function_name}")
    except Exception as e:
        print(f"WARNING: Failed to emit LambdaErrors metric: {str(e)}")


def emit_processing_latency(function_name: str, latency_ms: float):
    """
    Emit ProcessingLatency metric for performance monitoring
    
    Args:
        function_name: Name of the Lambda function
        latency_ms: Processing time in milliseconds
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'ProcessingLatency',
                    'Value': latency_ms,
                    'Unit': 'Milliseconds',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': function_name}
                    ]
                }
            ]
        )
        print(f"INFO: Emitted ProcessingLatency metric for {function_name}: {latency_ms}ms")
    except Exception as e:
        print(f"WARNING: Failed to emit ProcessingLatency metric: {str(e)}")
