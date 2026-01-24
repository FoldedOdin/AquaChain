"""
CloudWatch dashboard for shipment tracking monitoring

This module creates a comprehensive CloudWatch dashboard for monitoring
shipment operations with real-time metrics and visualizations.

Requirements: 14.1, 14.2
"""
import boto3
import json
from typing import Dict, Any

cloudwatch = boto3.client('cloudwatch')

NAMESPACE = 'AquaChain/Shipments'
DASHBOARD_NAME = 'AquaChain-Shipments-Dashboard'


def create_shipment_dashboard() -> str:
    """
    Create CloudWatch dashboard for shipment tracking
    
    Dashboard includes:
    - Shipment metrics (created, delivered, failed)
    - Webhook processing metrics
    - Average delivery time by courier
    - Error rates and alarm status
    
    Requirements: 14.1, 14.2
    
    Returns:
        Dashboard name
    """
    dashboard_body = {
        "widgets": [
            # Row 1: Overview metrics
            create_shipments_created_widget(0, 0),
            create_shipments_delivered_widget(0, 6),
            create_failed_deliveries_widget(0, 12),
            create_stale_shipments_widget(0, 18),
            
            # Row 2: Webhook metrics
            create_webhooks_processed_widget(6, 0),
            create_webhook_errors_widget(6, 6),
            create_webhook_success_rate_widget(6, 12),
            
            # Row 3: Delivery time by courier
            create_delivery_time_widget(12, 0),
            
            # Row 4: Lambda errors
            create_lambda_errors_widget(18, 0),
            
            # Row 5: Alarm status
            create_alarm_status_widget(24, 0)
        ]
    }
    
    try:
        cloudwatch.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Created CloudWatch dashboard: {DASHBOARD_NAME}")
        print(f"View at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name={DASHBOARD_NAME}")
        
        return DASHBOARD_NAME
        
    except Exception as e:
        print(f"ERROR: Failed to create dashboard: {str(e)}")
        raise


def create_shipments_created_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing total shipments created over time
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "ShipmentsCreated", {"stat": "Sum", "label": "Total Created"}],
                ["...", {"stat": "Sum", "label": "By Courier"}]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-east-1",
            "title": "Shipments Created",
            "period": 300,
            "yAxis": {
                "left": {
                    "label": "Count",
                    "showUnits": False
                }
            }
        }
    }


def create_shipments_delivered_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing successful deliveries
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "DeliveryTime", {"stat": "SampleCount", "label": "Delivered"}]
            ],
            "view": "singleValue",
            "region": "us-east-1",
            "title": "Total Deliveries",
            "period": 86400
        }
    }


def create_failed_deliveries_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing failed deliveries
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "FailedDeliveries", {"stat": "Sum", "label": "Failed"}]
            ],
            "view": "singleValue",
            "region": "us-east-1",
            "title": "Failed Deliveries (24h)",
            "period": 86400
        }
    }


def create_stale_shipments_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing stale shipments count
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "StaleShipments", {"stat": "Maximum", "label": "Stale"}]
            ],
            "view": "singleValue",
            "region": "us-east-1",
            "title": "Stale Shipments",
            "period": 3600
        }
    }


def create_webhooks_processed_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing webhooks processed over time
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "WebhooksProcessed", {"stat": "Sum", "label": "Processed"}]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-east-1",
            "title": "Webhooks Processed",
            "period": 300,
            "yAxis": {
                "left": {
                    "label": "Count",
                    "showUnits": False
                }
            }
        }
    }


def create_webhook_errors_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing webhook errors
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "WebhookErrors", {"stat": "Sum", "label": "Errors"}]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-east-1",
            "title": "Webhook Errors",
            "period": 300,
            "yAxis": {
                "left": {
                    "label": "Count",
                    "showUnits": False
                }
            },
            "annotations": {
                "horizontal": [
                    {
                        "label": "Threshold",
                        "value": 10,
                        "fill": "above",
                        "color": "#d62728"
                    }
                ]
            }
        }
    }


def create_webhook_success_rate_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing webhook success rate
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 6,
        "height": 6,
        "properties": {
            "metrics": [
                [{"expression": "(processed - errors) / processed * 100", "label": "Success Rate (%)", "id": "rate"}],
                [NAMESPACE, "WebhooksProcessed", {"stat": "Sum", "id": "processed", "visible": False}],
                [NAMESPACE, "WebhookErrors", {"stat": "Sum", "id": "errors", "visible": False}]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-east-1",
            "title": "Webhook Success Rate",
            "period": 300,
            "yAxis": {
                "left": {
                    "label": "%",
                    "showUnits": False,
                    "min": 0,
                    "max": 100
                }
            }
        }
    }


def create_delivery_time_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing average delivery time by courier
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 24,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "DeliveryTime", {"stat": "Average", "label": "Avg Delivery Time (hours)"}],
                ["...", {"stat": "p50", "label": "p50"}],
                ["...", {"stat": "p90", "label": "p90"}],
                ["...", {"stat": "p99", "label": "p99"}]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-east-1",
            "title": "Delivery Time by Courier",
            "period": 3600,
            "yAxis": {
                "left": {
                    "label": "Hours",
                    "showUnits": False
                }
            }
        }
    }


def create_lambda_errors_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing Lambda function errors
    """
    return {
        "type": "metric",
        "x": x,
        "y": y,
        "width": 24,
        "height": 6,
        "properties": {
            "metrics": [
                [NAMESPACE, "LambdaErrors", {"stat": "Sum"}]
            ],
            "view": "timeSeries",
            "stacked": True,
            "region": "us-east-1",
            "title": "Lambda Errors by Function",
            "period": 300,
            "yAxis": {
                "left": {
                    "label": "Count",
                    "showUnits": False
                }
            }
        }
    }


def create_alarm_status_widget(x: int, y: int) -> Dict[str, Any]:
    """
    Widget showing alarm status
    """
    return {
        "type": "alarm",
        "x": x,
        "y": y,
        "width": 24,
        "height": 6,
        "properties": {
            "title": "Alarm Status",
            "alarms": [
                "arn:aws:cloudwatch:us-east-1:123456789012:alarm:AquaChain-Shipments-HighFailedDeliveryRate",
                "arn:aws:cloudwatch:us-east-1:123456789012:alarm:AquaChain-Shipments-HighWebhookErrors",
                "arn:aws:cloudwatch:us-east-1:123456789012:alarm:AquaChain-Shipments-HighStaleShipments",
                "arn:aws:cloudwatch:us-east-1:123456789012:alarm:AquaChain-Shipments-create_shipment-Errors",
                "arn:aws:cloudwatch:us-east-1:123456789012:alarm:AquaChain-Shipments-webhook_handler-Errors"
            ]
        }
    }


def delete_shipment_dashboard() -> None:
    """
    Delete the shipment tracking dashboard
    """
    try:
        cloudwatch.delete_dashboards(
            DashboardNames=[DASHBOARD_NAME]
        )
        
        print(f"Deleted dashboard: {DASHBOARD_NAME}")
        
    except Exception as e:
        print(f"ERROR: Failed to delete dashboard: {str(e)}")
        raise


def get_dashboard_url(region: str = 'us-east-1') -> str:
    """
    Get the URL to view the dashboard
    
    Args:
        region: AWS region
        
    Returns:
        Dashboard URL
    """
    return f"https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={DASHBOARD_NAME}"


if __name__ == '__main__':
    """
    Setup script for CloudWatch dashboard
    
    Usage:
        python shipment_dashboard.py
    """
    print("Creating CloudWatch dashboard for shipment tracking...")
    
    dashboard_name = create_shipment_dashboard()
    
    print("\n" + "="*60)
    print("CloudWatch Dashboard Created!")
    print("="*60)
    print(f"\nDashboard Name: {dashboard_name}")
    print(f"\nView Dashboard:")
    print(get_dashboard_url())
    print("\nThe dashboard displays:")
    print("  - Shipment creation and delivery metrics")
    print("  - Webhook processing statistics")
    print("  - Average delivery time by courier")
    print("  - Error rates and alarm status")
    print("\nRefresh the dashboard to see real-time metrics.")
