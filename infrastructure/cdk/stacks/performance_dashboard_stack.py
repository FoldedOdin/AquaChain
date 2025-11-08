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
        
        self.env_name = environment  # Use different variable name to avoid conflict
        
        # Create main dashboard with auto-refresh
        self.dashboard = cloudwatch.Dashboard(
            self, 'PerformanceDashboard',
            dashboard_name=f'AquaChain-Performance-{environment}',
            period_override=cloudwatch.PeriodOverride.AUTO
        )
        
        # Dashboard will auto-refresh every 60 seconds in the console
        
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
        # API response times (p50, p95, p99)
        api_latency_widget = cloudwatch.GraphWidget(
            title='API Response Times',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Latency',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                    statistic='p50',
                    label='p50 (Median)',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Latency',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                    statistic='p95',
                    label='p95',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Latency',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
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
                    dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                    statistic='Sum',
                    label='Total Requests',
                    color=cloudwatch.Color.GREEN
                )
            ],
            right=[
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='4XXError',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                    statistic='Sum',
                    label='4XX Errors',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='5XXError',
                    dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                    statistic='Sum',
                    label='5XX Errors',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # API throttling events
        api_throttle_widget = cloudwatch.SingleValueWidget(
            title='API Throttling Events',
            metrics=[
                cloudwatch.Metric(
                    namespace='AWS/ApiGateway',
                    metric_name='Count',
                    dimensions_map={
                        'ApiName': f'AquaChain-API-{self.env_name}',
                        'Stage': 'prod'
                    },
                    statistic='Sum',
                    label='Throttled Requests'
                )
            ],
            width=6,
            height=6
        )
        
        # API error rate
        api_error_rate_widget = cloudwatch.SingleValueWidget(
            title='API Error Rate',
            metrics=[
                cloudwatch.MathExpression(
                    expression='(m1 + m2) / m3 * 100',
                    using_metrics={
                        'm1': cloudwatch.Metric(
                            namespace='AWS/ApiGateway',
                            metric_name='4XXError',
                            dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                            statistic='Sum'
                        ),
                        'm2': cloudwatch.Metric(
                            namespace='AWS/ApiGateway',
                            metric_name='5XXError',
                            dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                            statistic='Sum'
                        ),
                        'm3': cloudwatch.Metric(
                            namespace='AWS/ApiGateway',
                            metric_name='Count',
                            dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                            statistic='Sum'
                        )
                    },
                    label='Error Rate %'
                )
            ],
            width=6,
            height=6
        )
        
        self.dashboard.add_widgets(
            api_latency_widget, 
            api_requests_widget,
            api_throttle_widget,
            api_error_rate_widget
        )
    
    def _add_lambda_metrics(self):
        """Add Lambda function metrics"""
        # Lambda duration (average and p95)
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
                    statistic='p95',
                    label='p95 Duration',
                    color=cloudwatch.Color.ORANGE
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
        
        # Lambda invocations and error rate
        lambda_invocations_widget = cloudwatch.GraphWidget(
            title='Lambda Invocations',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/Lambda',
                    metric_name='Invocations',
                    statistic='Sum',
                    label='Total Invocations',
                    color=cloudwatch.Color.GREEN
                )
            ],
            right=[
                cloudwatch.MathExpression(
                    expression='errors / invocations * 100',
                    using_metrics={
                        'errors': cloudwatch.Metric(
                            namespace='AWS/Lambda',
                            metric_name='Errors',
                            statistic='Sum'
                        ),
                        'invocations': cloudwatch.Metric(
                            namespace='AWS/Lambda',
                            metric_name='Invocations',
                            statistic='Sum'
                        )
                    },
                    label='Error Rate %',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # Cold starts tracking (using custom metric)
        lambda_cold_starts_widget = cloudwatch.SingleValueWidget(
            title='Lambda Cold Starts',
            metrics=[
                cloudwatch.Metric(
                    namespace='AquaChain/Lambda',
                    metric_name='ColdStarts',
                    statistic='Sum',
                    label='Cold Starts (Last Hour)'
                )
            ],
            width=6,
            height=6
        )
        
        self.dashboard.add_widgets(
            lambda_duration_widget, 
            lambda_errors_widget,
            lambda_invocations_widget,
            lambda_cold_starts_widget
        )
    
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
                    label='Read Capacity Consumed',
                    color=cloudwatch.Color.BLUE
                ),
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='ConsumedWriteCapacityUnits',
                    statistic='Sum',
                    label='Write Capacity Consumed',
                    color=cloudwatch.Color.GREEN
                )
            ],
            width=12,
            height=6
        )
        
        # DynamoDB throttled requests
        dynamodb_throttles_widget = cloudwatch.GraphWidget(
            title='DynamoDB Throttled Requests',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='ReadThrottleEvents',
                    statistic='Sum',
                    label='Read Throttles',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='WriteThrottleEvents',
                    statistic='Sum',
                    label='Write Throttles',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        # DynamoDB query latency
        dynamodb_latency_widget = cloudwatch.GraphWidget(
            title='DynamoDB Query Latency',
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
        
        # DynamoDB system errors
        dynamodb_errors_widget = cloudwatch.SingleValueWidget(
            title='DynamoDB System Errors',
            metrics=[
                cloudwatch.Metric(
                    namespace='AWS/DynamoDB',
                    metric_name='SystemErrors',
                    statistic='Sum',
                    label='System Errors'
                )
            ],
            width=6,
            height=6
        )
        
        self.dashboard.add_widgets(
            dynamodb_capacity_widget, 
            dynamodb_throttles_widget,
            dynamodb_latency_widget,
            dynamodb_errors_widget
        )
    
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
                ),
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='Connect.AuthError',
                    statistic='Sum',
                    label='Authentication Failures',
                    color=cloudwatch.Color.ORANGE
                )
            ],
            width=12,
            height=6
        )
        
        # Connected device count
        iot_device_count_widget = cloudwatch.SingleValueWidget(
            title='Connected Devices',
            metrics=[
                cloudwatch.Metric(
                    namespace='AquaChain/IoT',
                    metric_name='ConnectedDevices',
                    statistic='Maximum',
                    label='Active Devices'
                )
            ],
            width=6,
            height=6
        )
        
        # IoT message rates (publish and receive)
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
        
        # IoT rule execution errors
        iot_rule_errors_widget = cloudwatch.GraphWidget(
            title='IoT Rule Execution',
            left=[
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='RuleMessageThrottled',
                    statistic='Sum',
                    label='Throttled Messages',
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace='AWS/IoT',
                    metric_name='RuleNotFound',
                    statistic='Sum',
                    label='Rule Not Found',
                    color=cloudwatch.Color.RED
                )
            ],
            width=12,
            height=6
        )
        
        self.dashboard.add_widgets(
            iot_connections_widget, 
            iot_device_count_widget,
            iot_messages_widget,
            iot_rule_errors_widget
        )
    
    def _add_ml_metrics(self):
        """Add ML model performance metrics"""
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
        
        # ML drift score
        ml_drift_widget = cloudwatch.GraphWidget(
            title='ML Model Drift Score',
            left=[
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='DriftScore',
                    statistic='Average',
                    label='Drift Score',
                    color=cloudwatch.Color.ORANGE
                )
            ],
            left_y_axis=cloudwatch.YAxisProps(
                min=0,
                max=1,
                label='Drift Score (0-1)'
            ),
            width=12,
            height=6
        )
        
        # ML prediction count
        ml_prediction_count_widget = cloudwatch.GraphWidget(
            title='ML Prediction Count',
            left=[
                cloudwatch.Metric(
                    namespace='AquaChain/ML',
                    metric_name='PredictionCount',
                    statistic='Sum',
                    label='Total Predictions',
                    color=cloudwatch.Color.GREEN
                )
            ],
            width=12,
            height=6
        )
        
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
        
        # ML error rate
        ml_error_rate_widget = cloudwatch.SingleValueWidget(
            title='ML Prediction Error Rate',
            metrics=[
                cloudwatch.MathExpression(
                    expression='errors / predictions * 100',
                    using_metrics={
                        'errors': cloudwatch.Metric(
                            namespace='AquaChain/ML',
                            metric_name='PredictionErrors',
                            statistic='Sum'
                        ),
                        'predictions': cloudwatch.Metric(
                            namespace='AquaChain/ML',
                            metric_name='PredictionCount',
                            statistic='Sum'
                        )
                    },
                    label='Error Rate %'
                )
            ],
            width=6,
            height=6
        )
        
        self.dashboard.add_widgets(
            ml_latency_widget, 
            ml_drift_widget,
            ml_prediction_count_widget,
            ml_confidence_widget,
            ml_error_rate_widget
        )

    
    def _create_performance_alarms(self):
        """Create CloudWatch alarms for performance thresholds"""
        # API response time > 1 second (p95)
        api_latency_alarm = cloudwatch.Alarm(
            self, 'APILatencyAlarm',
            alarm_name=f'AquaChain-API-HighLatency-{self.env_name}',
            alarm_description='API response time exceeds 1 second at p95',
            metric=cloudwatch.Metric(
                namespace='AWS/ApiGateway',
                metric_name='Latency',
                dimensions_map={'ApiName': f'AquaChain-API-{self.env_name}'},
                statistic='p95'
            ),
            threshold=1000,  # 1 second in milliseconds
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Lambda error rate > 1%
        lambda_error_rate_alarm = cloudwatch.Alarm(
            self, 'LambdaErrorRateAlarm',
            alarm_name=f'AquaChain-Lambda-HighErrorRate-{self.env_name}',
            alarm_description='Lambda error rate exceeds 1%',
            metric=cloudwatch.MathExpression(
                expression='errors / invocations * 100',
                using_metrics={
                    'errors': cloudwatch.Metric(
                        namespace='AWS/Lambda',
                        metric_name='Errors',
                        statistic='Sum'
                    ),
                    'invocations': cloudwatch.Metric(
                        namespace='AWS/Lambda',
                        metric_name='Invocations',
                        statistic='Sum'
                    )
                }
            ),
            threshold=1,  # 1%
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # DynamoDB throttling events
        dynamodb_throttle_alarm = cloudwatch.Alarm(
            self, 'DynamoDBThrottleAlarm',
            alarm_name=f'AquaChain-DynamoDB-Throttles-{self.env_name}',
            alarm_description='DynamoDB throttling events detected',
            metric=cloudwatch.MathExpression(
                expression='read_throttles + write_throttles',
                using_metrics={
                    'read_throttles': cloudwatch.Metric(
                        namespace='AWS/DynamoDB',
                        metric_name='ReadThrottleEvents',
                        statistic='Sum'
                    ),
                    'write_throttles': cloudwatch.Metric(
                        namespace='AWS/DynamoDB',
                        metric_name='WriteThrottleEvents',
                        statistic='Sum'
                    )
                }
            ),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # IoT connection failures
        iot_connection_alarm = cloudwatch.Alarm(
            self, 'IoTConnectionAlarm',
            alarm_name=f'AquaChain-IoT-ConnectionFailures-{self.env_name}',
            alarm_description='IoT device connection failures detected',
            metric=cloudwatch.MathExpression(
                expression='client_errors + auth_errors',
                using_metrics={
                    'client_errors': cloudwatch.Metric(
                        namespace='AWS/IoT',
                        metric_name='Connect.ClientError',
                        statistic='Sum'
                    ),
                    'auth_errors': cloudwatch.Metric(
                        namespace='AWS/IoT',
                        metric_name='Connect.AuthError',
                        statistic='Sum'
                    )
                }
            ),
            threshold=10,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # ML drift score > 0.15
        ml_drift_alarm = cloudwatch.Alarm(
            self, 'MLDriftAlarm',
            alarm_name=f'AquaChain-ML-HighDrift-{self.env_name}',
            alarm_description='ML model drift score exceeds 0.15 threshold',
            metric=cloudwatch.Metric(
                namespace='AquaChain/ML',
                metric_name='DriftScore',
                statistic='Average'
            ),
            threshold=0.15,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # ML model low confidence alarm
        ml_confidence_alarm = cloudwatch.Alarm(
            self, 'MLConfidenceAlarm',
            alarm_name=f'AquaChain-ML-LowConfidence-{self.env_name}',
            alarm_description='ML model prediction confidence is low',
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
            'lambda_error_rate': lambda_error_rate_alarm,
            'dynamodb_throttles': dynamodb_throttle_alarm,
            'iot_connections': iot_connection_alarm,
            'ml_drift': ml_drift_alarm,
            'ml_confidence': ml_confidence_alarm
        }
