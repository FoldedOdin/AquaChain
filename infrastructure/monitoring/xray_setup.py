"""
AWS X-Ray Setup for AquaChain System
Implements distributed tracing and performance monitoring
"""

import boto3
import json
from typing import Dict, List, Any
from botocore.exceptions import ClientError


class XRaySetup:
    def __init__(self, region='us-east-1'):
        self.xray = boto3.client('xray', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.region = region
        
    def enable_xray_tracing_for_lambda(self, function_names: List[str]):
        """Enable X-Ray tracing for Lambda functions"""
        results = {}
        
        for function_name in function_names:
            try:
                response = self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    TracingConfig={
                        'Mode': 'Active'
                    }
                )
                results[function_name] = {
                    'status': 'success',
                    'tracing_mode': response['TracingConfig']['Mode']
                }
                print(f"Enabled X-Ray tracing for Lambda: {function_name}")
            except ClientError as e:
                results[function_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"Error enabling X-Ray for {function_name}: {e}")
                
        return results
    
    def enable_xray_tracing_for_api_gateway(self, api_id: str, stage_name: str = 'prod'):
        """Enable X-Ray tracing for API Gateway"""
        try:
            response = self.apigateway.update_stage(
                restApiId=api_id,
                stageName=stage_name,
                patchOps=[
                    {
                        'op': 'replace',
                        'path': '/tracingEnabled',
                        'value': 'true'
                    }
                ]
            )
            print(f"Enabled X-Ray tracing for API Gateway: {api_id}/{stage_name}")
            return response
        except ClientError as e:
            print(f"Error enabling X-Ray for API Gateway: {e}")
            raise
    
    def create_sampling_rule(self):
        """Create X-Ray sampling rule for AquaChain system"""
        sampling_rule = {
            'rule_name': 'AquaChainSamplingRule',
            'priority': 9000,
            'fixed_rate': 0.1,  # 10% sampling rate
            'reservoir_size': 1,
            'service_name': 'aquachain-*',
            'service_type': '*',
            'host': '*',
            'method': '*',
            'url_path': '*',
            'version': 1
        }
        
        try:
            response = self.xray.create_sampling_rule(SamplingRule=sampling_rule)
            print(f"Created X-Ray sampling rule: {response}")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'RuleAlreadyExistsException':
                print("Sampling rule already exists")
                return None
            else:
                print(f"Error creating sampling rule: {e}")
                raise
    
    def create_service_map_filters(self):
        """Create service map filters for better visualization"""
        filters = [
            {
                'FilterName': 'AquaChain-CriticalPath',
                'FilterExpression': 'service("aquachain-data-processing") OR service("aquachain-ml-inference") OR service("aquachain-alert-detection")'
            },
            {
                'FilterName': 'AquaChain-UserFacing',
                'FilterExpression': 'service("aquachain-api") OR service("aquachain-websocket-api") OR service("aquachain-auth-service")'
            },
            {
                'FilterName': 'AquaChain-HighLatency',
                'FilterExpression': 'responsetime > 5'
            },
            {
                'FilterName': 'AquaChain-Errors',
                'FilterExpression': 'error = true OR fault = true'
            }
        ]
        
        created_filters = []
        for filter_config in filters:
            try:
                # Note: X-Ray doesn't have a direct API for creating service map filters
                # These would typically be created through the console or CloudFormation
                created_filters.append(filter_config)
                print(f"Filter configuration prepared: {filter_config['FilterName']}")
            except Exception as e:
                print(f"Error preparing filter {filter_config['FilterName']}: {e}")
                
        return created_filters
    
    def setup_complete_xray_tracing(self):
        """Set up complete X-Ray tracing for AquaChain system"""
        print("Setting up X-Ray distributed tracing...")
        
        # Lambda functions to enable tracing for
        lambda_functions = [
            'aquachain-data-processing',
            'aquachain-ml-inference',
            'aquachain-alert-detection',
            'aquachain-notification-service',
            'aquachain-technician-service',
            'aquachain-auth-service',
            'aquachain-user-management',
            'aquachain-audit-trail-processor',
            'aquachain-websocket-api',
            'aquachain-pagerduty-integration'
        ]
        
        # Enable Lambda tracing
        lambda_results = self.enable_xray_tracing_for_lambda(lambda_functions)
        
        # Create sampling rule
        sampling_rule = self.create_sampling_rule()
        
        # Create service map filters
        service_filters = self.create_service_map_filters()
        
        return {
            'lambda_tracing': lambda_results,
            'sampling_rule': sampling_rule,
            'service_filters': service_filters
        }


class PerformanceMonitoring:
    """Performance monitoring and baseline establishment"""
    
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.xray = boto3.client('xray', region_name=region)
        self.region = region
        
    def create_performance_metrics(self):
        """Create custom performance metrics"""
        performance_metrics = {
            'AquaChain/Performance': [
                'EndToEndLatency',  # IoT to notification
                'DataProcessingLatency',
                'MLInferenceLatency',
                'APIResponseTime',
                'DatabaseQueryTime',
                'NotificationDeliveryTime'
            ],
            'AquaChain/Throughput': [
                'MessagesPerSecond',
                'RequestsPerSecond',
                'AlertsPerMinute',
                'ServiceRequestsPerHour'
            ],
            'AquaChain/Reliability': [
                'SuccessRate',
                'RetryRate',
                'CircuitBreakerTrips',
                'DeadLetterQueueMessages'
            ]
        }
        
        return performance_metrics
    
    def create_performance_dashboard(self):
        """Create performance monitoring dashboard"""
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
                            ["AquaChain/Performance", "EndToEndLatency", {"stat": "Average"}],
                            [".", ".", {"stat": "p95"}],
                            [".", ".", {"stat": "p99"}]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "End-to-End Latency (IoT to Notification)",
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
                                    "label": "30s SLA Target",
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
                            ["AquaChain/Performance", "DataProcessingLatency"],
                            [".", "MLInferenceLatency"],
                            [".", "APIResponseTime"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Component Latencies",
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
                            ["AquaChain/Throughput", "MessagesPerSecond"],
                            [".", "RequestsPerSecond"],
                            [".", "AlertsPerMinute"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "System Throughput",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 12,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "view": "timeSeries",
                        "stacked": False,
                        "metrics": [
                            ["AWS/X-Ray", "TracesReceived"],
                            [".", "TracesProcessed"]
                        ],
                        "region": self.region,
                        "title": "X-Ray Trace Volume",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 8,
                    "y": 12,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "view": "timeSeries",
                        "stacked": False,
                        "metrics": [
                            ["AquaChain/Reliability", "SuccessRate"],
                            [".", "RetryRate"]
                        ],
                        "region": self.region,
                        "title": "Reliability Metrics",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 16,
                    "y": 12,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "view": "number",
                        "metrics": [
                            ["AquaChain/Reliability", "DeadLetterQueueMessages"]
                        ],
                        "region": self.region,
                        "title": "Failed Messages",
                        "period": 300
                    }
                }
            ]
        }
        
        try:
            response = self.cloudwatch.put_dashboard(
                DashboardName='AquaChain-Performance',
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"Created performance dashboard: {response}")
            return response
        except ClientError as e:
            print(f"Error creating performance dashboard: {e}")
            raise
    
    def create_performance_alarms(self, sns_topic_arn: str):
        """Create performance-based alarms"""
        alarms = [
            {
                'AlarmName': 'AquaChain-EndToEnd-Latency-High',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 3,
                'MetricName': 'EndToEndLatency',
                'Namespace': 'AquaChain/Performance',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 25.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Alert when end-to-end latency approaches 30s SLA',
                'Unit': 'Seconds'
            },
            {
                'AlarmName': 'AquaChain-API-ResponseTime-High',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'APIResponseTime',
                'Namespace': 'AquaChain/Performance',
                'Period': 300,
                'Statistic': 'p95',
                'Threshold': 2.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Alert when API p95 response time exceeds 2 seconds',
                'Unit': 'Seconds'
            },
            {
                'AlarmName': 'AquaChain-DeadLetterQueue-Messages',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 1,
                'MetricName': 'DeadLetterQueueMessages',
                'Namespace': 'AquaChain/Reliability',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 5.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Alert when messages accumulate in dead letter queue',
                'Unit': 'Count'
            }
        ]
        
        created_alarms = []
        for alarm in alarms:
            try:
                response = self.cloudwatch.put_metric_alarm(**alarm)
                created_alarms.append(alarm['AlarmName'])
                print(f"Created performance alarm: {alarm['AlarmName']}")
            except ClientError as e:
                print(f"Error creating alarm {alarm['AlarmName']}: {e}")
                
        return created_alarms
    
    def establish_performance_baselines(self):
        """Establish performance baselines for anomaly detection"""
        baselines = {
            'data_processing_latency': {
                'target': 5.0,  # seconds
                'warning_threshold': 8.0,
                'critical_threshold': 15.0
            },
            'ml_inference_latency': {
                'target': 2.0,  # seconds
                'warning_threshold': 5.0,
                'critical_threshold': 10.0
            },
            'api_response_time': {
                'target': 0.5,  # seconds
                'warning_threshold': 1.0,
                'critical_threshold': 2.0
            },
            'end_to_end_latency': {
                'target': 15.0,  # seconds
                'warning_threshold': 25.0,
                'critical_threshold': 30.0
            },
            'throughput_messages_per_second': {
                'target': 100,
                'warning_threshold': 50,
                'critical_threshold': 10
            }
        }
        
        print("Performance baselines established:")
        for metric, thresholds in baselines.items():
            print(f"  {metric}: target={thresholds['target']}, warning={thresholds['warning_threshold']}, critical={thresholds['critical_threshold']}")
            
        return baselines


if __name__ == "__main__":
    # Example usage
    xray_setup = XRaySetup()
    performance_monitoring = PerformanceMonitoring()
    
    # Set up X-Ray tracing
    xray_result = xray_setup.setup_complete_xray_tracing()
    
    # Set up performance monitoring
    performance_metrics = performance_monitoring.create_performance_metrics()
    performance_monitoring.create_performance_dashboard()
    baselines = performance_monitoring.establish_performance_baselines()
    
    print("X-Ray and performance monitoring setup complete!")
    print(json.dumps({
        'xray_setup': xray_result,
        'performance_metrics': performance_metrics,
        'baselines': baselines
    }, indent=2, default=str))