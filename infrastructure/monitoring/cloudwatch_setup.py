"""
CloudWatch Monitoring Setup for AquaChain System
Implements comprehensive monitoring, dashboards, and alerting
"""

import boto3
import json
from typing import Dict, List, Any
from botocore.exceptions import ClientError


class CloudWatchMonitoringSetup:
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        
    def create_custom_metrics_namespace(self):
        """Create custom metrics namespace for AquaChain business metrics"""
        # Custom metrics are created when first data point is published
        # This method defines the metric structure
        self.custom_metrics = {
            'AquaChain/DataIngestion': [
                'DeviceDataReceived',
                'ProcessingLatency',
                'ValidationErrors',
                'DuplicateReadings'
            ],
            'AquaChain/Alerts': [
                'AlertLatency',
                'CriticalAlerts',
                'NotificationDeliveryRate',
                'AlertVolumePerHour'
            ],
            'AquaChain/ServiceRequests': [
                'AssignmentLatency',
                'TechnicianUtilization',
                'ServiceCompletionRate',
                'CustomerSatisfactionScore'
            ],
            'AquaChain/SystemHealth': [
                'DeviceUptime',
                'APIResponseTime',
                'ErrorRate',
                'ThroughputPerSecond'
            ]
        }
        return self.custom_metrics
    
    def create_system_health_dashboard(self):
        """Create comprehensive system health dashboard"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/DataIngestion", "DeviceDataReceived"],
                            [".", "ProcessingLatency"],
                            ["AquaChain/SystemHealth", "ErrorRate"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Data Ingestion Overview",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/Alerts", "AlertLatency"],
                            [".", "CriticalAlerts"],
                            [".", "NotificationDeliveryRate"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Alert System Performance",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Duration", "FunctionName", "aquachain-data-processing"],
                            [".", "Errors", ".", "."],
                            [".", "Throttles", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Data Processing Lambda",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 8,
                    "y": 6,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Duration", "FunctionName", "aquachain-ml-inference"],
                            [".", "Errors", ".", "."],
                            [".", "ConcurrentExecutions", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "ML Inference Lambda",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 16,
                    "y": 6,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "aquachain-readings"],
                            [".", "ConsumedWriteCapacityUnits", ".", "."],
                            [".", "ThrottledRequests", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "DynamoDB Performance",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 12,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ApiGateway", "Count", "ApiName", "aquachain-api"],
                            [".", "Latency", ".", "."],
                            [".", "4XXError", ".", "."],
                            [".", "5XXError", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "API Gateway Performance",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 12,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/SystemHealth", "DeviceUptime"],
                            ["AquaChain/ServiceRequests", "TechnicianUtilization"],
                            [".", "ServiceCompletionRate"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Business KPIs",
                        "period": 300
                    }
                }
            ]
        }
        
        try:
            response = self.cloudwatch.put_dashboard(
                DashboardName='AquaChain-SystemHealth',
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"Created system health dashboard: {response}")
            return response
        except ClientError as e:
            print(f"Error creating dashboard: {e}")
            raise
    
    def create_alert_latency_dashboard(self):
        """Create specialized dashboard for alert latency monitoring"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/Alerts", "AlertLatency", {"stat": "Average"}],
                            [".", ".", {"stat": "p95"}],
                            [".", ".", {"stat": "p99"}]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Alert Latency Distribution (30-second SLA)",
                        "period": 60,
                        "yAxis": {
                            "left": {
                                "min": 0,
                                "max": 60
                            }
                        },
                        "annotations": {
                            "horizontal": [
                                {
                                    "label": "30s SLA Threshold",
                                    "value": 30
                                }
                            ]
                        }
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/Alerts", "CriticalAlerts"],
                            [".", "AlertVolumePerHour"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Alert Volume",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/Alerts", "NotificationDeliveryRate", {"stat": "Average"}]
                        ],
                        "view": "singleValue",
                        "region": self.region,
                        "title": "Notification Delivery Success Rate",
                        "period": 300
                    }
                }
            ]
        }
        
        try:
            response = self.cloudwatch.put_dashboard(
                DashboardName='AquaChain-AlertLatency',
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"Created alert latency dashboard: {response}")
            return response
        except ClientError as e:
            print(f"Error creating alert dashboard: {e}")
            raise
    
    def create_sns_topics_for_alerts(self):
        """Create SNS topics for different alert types"""
        topics = {
            'aquachain-critical-system-alerts': 'Critical system issues requiring immediate attention',
            'aquachain-sla-breach-alerts': 'SLA breaches and performance degradation',
            'aquachain-operational-alerts': 'Operational issues and warnings'
        }
        
        created_topics = {}
        
        for topic_name, description in topics.items():
            try:
                response = self.sns.create_topic(
                    Name=topic_name,
                    Attributes={
                        'DisplayName': topic_name,
                        'Description': description
                    }
                )
                created_topics[topic_name] = response['TopicArn']
                print(f"Created SNS topic: {topic_name} - {response['TopicArn']}")
            except ClientError as e:
                print(f"Error creating SNS topic {topic_name}: {e}")
                
        return created_topics
    
    def create_cloudwatch_alarms(self, sns_topic_arns: Dict[str, str]):
        """Create CloudWatch alarms for system monitoring"""
        alarms = [
            {
                'AlarmName': 'AquaChain-AlertLatency-SLA-Breach',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'AlertLatency',
                'Namespace': 'AquaChain/Alerts',
                'Period': 60,
                'Statistic': 'Average',
                'Threshold': 30.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arns['aquachain-sla-breach-alerts']],
                'AlarmDescription': 'Alert when notification latency exceeds 30 seconds',
                'Unit': 'Seconds'
            },
            {
                'AlarmName': 'AquaChain-DataProcessing-ErrorRate',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 3,
                'MetricName': 'ErrorRate',
                'Namespace': 'AquaChain/SystemHealth',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 5.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arns['aquachain-critical-system-alerts']],
                'AlarmDescription': 'Alert when error rate exceeds 5% for 15 minutes',
                'Unit': 'Percent'
            },
            {
                'AlarmName': 'AquaChain-DeviceUptime-Low',
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'DeviceUptime',
                'Namespace': 'AquaChain/SystemHealth',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 95.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arns['aquachain-operational-alerts']],
                'AlarmDescription': 'Alert when device uptime falls below 95%',
                'Unit': 'Percent'
            },
            {
                'AlarmName': 'AquaChain-Lambda-DataProcessing-Errors',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'Errors',
                'Namespace': 'AWS/Lambda',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 10.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arns['aquachain-critical-system-alerts']],
                'AlarmDescription': 'Alert when data processing Lambda has >10 errors in 5 minutes',
                'Dimensions': [
                    {
                        'Name': 'FunctionName',
                        'Value': 'aquachain-data-processing'
                    }
                ]
            },
            {
                'AlarmName': 'AquaChain-DynamoDB-Throttling',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 1,
                'MetricName': 'ThrottledRequests',
                'Namespace': 'AWS/DynamoDB',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 0.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arns['aquachain-critical-system-alerts']],
                'AlarmDescription': 'Alert on any DynamoDB throttling',
                'Dimensions': [
                    {
                        'Name': 'TableName',
                        'Value': 'aquachain-readings'
                    }
                ]
            }
        ]
        
        created_alarms = []
        for alarm in alarms:
            try:
                response = self.cloudwatch.put_metric_alarm(**alarm)
                created_alarms.append(alarm['AlarmName'])
                print(f"Created alarm: {alarm['AlarmName']}")
            except ClientError as e:
                print(f"Error creating alarm {alarm['AlarmName']}: {e}")
                
        return created_alarms
    
    def create_log_groups(self):
        """Create CloudWatch log groups for Lambda functions"""
        log_groups = [
            '/aws/lambda/aquachain-data-processing',
            '/aws/lambda/aquachain-ml-inference',
            '/aws/lambda/aquachain-alert-detection',
            '/aws/lambda/aquachain-notification-service',
            '/aws/lambda/aquachain-technician-service',
            '/aws/lambda/aquachain-auth-service',
            '/aws/lambda/aquachain-user-management',
            '/aws/lambda/aquachain-audit-trail-processor',
            '/aws/lambda/aquachain-websocket-api',
            '/aws/apigateway/aquachain-api'
        ]
        
        created_groups = []
        for log_group in log_groups:
            try:
                response = self.logs.create_log_group(
                    logGroupName=log_group,
                    retentionInDays=30  # 30 days retention for cost optimization
                )
                created_groups.append(log_group)
                print(f"Created log group: {log_group}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                    print(f"Log group already exists: {log_group}")
                    created_groups.append(log_group)
                else:
                    print(f"Error creating log group {log_group}: {e}")
                    
        return created_groups
    
    def setup_complete_monitoring(self):
        """Set up complete monitoring infrastructure"""
        print("Setting up AquaChain monitoring infrastructure...")
        
        # Create custom metrics namespace
        metrics = self.create_custom_metrics_namespace()
        print(f"Defined custom metrics: {list(metrics.keys())}")
        
        # Create SNS topics
        sns_topics = self.create_sns_topics_for_alerts()
        
        # Create CloudWatch alarms
        alarms = self.create_cloudwatch_alarms(sns_topics)
        
        # Create dashboards
        self.create_system_health_dashboard()
        self.create_alert_latency_dashboard()
        
        # Create log groups
        log_groups = self.create_log_groups()
        
        return {
            'custom_metrics': metrics,
            'sns_topics': sns_topics,
            'alarms': alarms,
            'log_groups': log_groups
        }


if __name__ == "__main__":
    # Example usage
    monitoring = CloudWatchMonitoringSetup()
    result = monitoring.setup_complete_monitoring()
    print("Monitoring setup complete!")
    print(json.dumps(result, indent=2, default=str))