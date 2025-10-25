"""
Performance Monitoring Dashboard Stack
Centralized CloudWatch dashboard for system performance
"""

from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
    aws_iot as iot,
    Duration
)
from constructs import Construct
from typing import List, Dict, Any


class PerformanceDashboardStack(Stack):
    """CloudWatch dashboard for performance monitoring"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.environment = environment
        
        # Create main dashboard
        self.dashboard = cloudwatch.Dashboard(
            self, 'PerformanceDashboard',
            dashboard_name=f'AquaChain-Performance-{environment}'
        )
        
        # Add widgets
        self._add_api_metrics()
        self._add_lambda_metrics()
        self._add_dynamodb_metrics()
        self._add_iot_metrics()
        self._add_ml_metrics()
        
        # Create alarms
        self._create_performance_alarms()
    
    def _add_api_metrics(self):
        """Add API Gateway metrics"""
        # API response times
        api_latency_widget = cloudwatch.GraphWidget(
            title='API Response Times',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Latency',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                    statistic='Average',
                    label='Average',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Latency',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                    statistic='p95',
                    label='p95',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Latency',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                    statistic='p99',
                    label='p99',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # API request count and errors
        api_requests_widget = cloudwatch.GraphWidget(
            title='API Requests & Errors',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Count',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                    statistic='Sum',
                    label='Total Requests',
                    color=cloudwatch.Color.GREEN
                )
            ],
            right=[
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='4XXError',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                    statistic='Sum',
                    label='4XX Errors',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='5XXError',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                    statistic='Sum',
                    label='5XX Errors',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        self.dashboard.add_widgets(api_latency_widget, api_requests_widget)
    
    def _add_lambda_metrics(self):
        """Add Lambda function metrics"""
        # Lambda duration
        lambda_duration_widget = cloudwatch.GraphWidget(
            title='Lambda Function Duration',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/Lambda',
                    metric_name='Duration',
                    statistic='Average',
                    label='Average Duration',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/Lambda',
                    metric_name='Duration',
                    statistic='Maximum',
                    label='Max Duration',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # Lambda errors and throttles
        lambda_errors_widget = cloudwatch.GraphWidget(
            title='Lambda Errors & Throttles',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/Lambda',
                    metric_name='Errors',
                    statistic='Sum',
                    label='Errors',
                    color=cloudwatch.Color.RED
                ),
                cloudwatch.Metric(
                    namespace='AWS/Lambda',
                    metric_name='Throttles',
                    statistic='Sum',
                    label='Throttles',
                    color=cloudwatch.Color.ORANGE
                )
            ],
            right=[
                cloudwatch.Metric(
                    namespace='AWS/Lambda',
                    metric_name='ConcurrentExecutions',
                    statistic='Maximum',
                    label='Concurrent Executions',
                    color=cloudwatch.Color.PURPLE
                )
            ],
            width=12,
            height=6
        )
        
        self.dashboard.add_widgets(lambda_duration_widget, lambda_errors_widget)
    
    def _add_dynamodb_metrics(self):
        """Add DynamoDB metrics"""
        # DynamoDB capacity utilization
        dynamodb_capacity_widget = cloudwatch.GraphWidget(
            title='DynamoDB Capacity Utilization',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='ConsumedReadCapacityUnits',
                    statistic='Sum',
                    label='Read Capacity',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='ConsumedWriteCapacityUnits',
                    statistic='Sum',
                    label='Write Capacity',
                    color=cloudwatch.Color.GREEN
                )
            ],
            width=12,
            height=6
        )
        
        # DynamoDB latency
        dynamodb_latency_widget = cloudwatch.GraphWidget(
            title='DynamoDB Operation Latency',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='SuccessfulRequestLatency',
                    dimensions_map={'Operation': 'GetItem'},
                    statistic='Average',
                    label='GetItem Latency',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='SuccessfulRequestLatency',
                    dimensions_map={'Operation': 'PutItem'},
                    statistic='Average',
                    label='PutItem Latency',
                    color=cloudwatch.Color.GREEN
                ),
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='SuccessfulRequestLatency',
                    dimensions_map={'Operation': 'Query'},
                    statistic='Average',
                    label='Query Latency',
                    color=cloudwatch.Color.ORANGE
                )
            ],
            width=12,
            height=6
        )
        
        self.dashboard.add_widgets(dynamodb_capacity_widget, dynamodb_latency_widget)
    
    def _add_iot_metrics(self):
        """Add IoT Core metrics"""
        # IoT device connections
        iot_connections_widget = cloudwatch.GraphWidget(
            title='IoT Device Connections',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='Connect.Success',
                    statistic='Sum',
                    label='Successful Connections',
                    color=cloudwatch.Color.GREEN
                ),
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='Connect.ClientError',
                    statistic='Sum',
                    label='Connection Errors',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # IoT message rates
        iot_messages_widget = cloudwatch.GraphWidget(
            title='IoT Message Rates',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='PublishIn.Success',
                    statistic='Sum',
                    label='Messages Published',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='PublishOut.Success',
                    statistic='Sum',
                    label='Messages Delivered',
                    color=cloudwatch.Color.GREEN
                )
            ],
            width=12,
            height=6
        )
        
        self.dashboard.add_widgets(iot_connections_widget, iot_messages_widget)
    
    def _add_ml_metrics(self):
        """Add ML model performance metrics"""
        # ML prediction confidence
        ml_confidence_widget = cloudwatch.GraphWidget(
            title='ML Model Prediction Confidence',
            left=[
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='PredictionConfidence',
                    statistic='Average',
                    label='Average Confidence',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='PredictionConfidence',
                    statistic='Minimum',
                    label='Min Confidence',
                    color=cloudwatch.Color.ORANGE
                )
            ],
            width=12,
            height=6
        )
        
        # ML prediction latency
        ml_latency_widget = cloudwatch.GraphWidget(
            title='ML Prediction Latency',
            left=[
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='PredictionLatency',
                    statistic='Average',
                    label='Average Latency',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='PredictionLatency',
                    statistic='p95',
                    label='p95 Latency',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='PredictionLatency',
                    statistic='p99',
                    label='p99 Latency',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        self.dashboard.add_widgets(ml_confidence_widget, ml_latency_widget)

    
    def _create_performance_alarms(self):
        """Create CloudWatch alarms for performance thresholds"""
        # API latency alarm
        api_latency_alarm = cloudwatch.Alarm(
            self, 'APILatencyAlarm',
            alarm_name=f'AquaChain-API-HighLatency-{self.environment}',
            metric=cloudwatch.Metric(
                namespace='AWS/ApiGateway',
                metric_name='Latency',
                dimensions_map={'ApiName': f'AquaChain-API-{self.environment}'},
                statistic='p95'
            ),
            threshold=2000,  # 2 seconds
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Lambda error rate alarm
        lambda_error_alarm = cloudwatch.Alarm(
            self, 'LambdaErrorAlarm',
            alarm_name=f'AquaChain-Lambda-HighErrors-{self.environment}',
            metric=cloudwatch.Metric(
                namespace='AWS/Lambda',
                metric_name='Errors',
                statistic='Sum'
            ),
            threshold=10,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # DynamoDB throttle alarm
        dynamodb_throttle_alarm = cloudwatch.Alarm(
            self, 'DynamoDBThrottleAlarm',
            alarm_name=f'AquaChain-DynamoDB-Throttles-{self.environment}',
            metric=cloudwatch.Metric(
                namespace='AWS/DynamoDB',
                metric_name='UserErrors',
                statistic='Sum'
            ),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # IoT connection failure alarm
        iot_connection_alarm = cloudwatch.Alarm(
            self, 'IoTConnectionAlarm',
            alarm_name=f'AquaChain-IoT-ConnectionFailures-{self.environment}',
            metric=cloudwatch.Metric(
                namespace='AWS/IoT',
                metric_name='Connect.ClientError',
                statistic='Sum'
            ),
            threshold=10,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # ML model confidence alarm
        ml_confidence_alarm = cloudwatch.Alarm(
            self, 'MLConfidenceAlarm',
            alarm_name=f'AquaChain-ML-LowConfidence-{self.environment}',
            metric=cloudwatch.Metric(
                namespace='AquaChain/ML',
                metric_name='PredictionConfidence',
                statistic='Average'
            ),
            threshold=0.7,  # 70% confidence
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Store alarms for reference
        self.alarms = {
            'api_latency': api_latency_alarm,
            'lambda_errors': lambda_error_alarm,
            'dynamodb_throttles': dynamodb_throttle_alarm,
            'iot_connections': iot_connection_alarm,
            'ml_confidence': ml_confidence_alarm
        }
