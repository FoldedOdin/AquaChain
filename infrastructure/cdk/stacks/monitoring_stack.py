"""
AquaChain Monitoring Stack
CloudWatch dashboards, alarms, X-Ray tracing, and PagerDuty integration
"""

from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_logs as logs,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_xray as xray,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any, List
from config.environment_config import get_resource_name

class AquaChainMonitoringStack(Stack):
    """
    Monitoring stack containing CloudWatch, X-Ray, and alerting infrastructure
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 data_resources: Dict[str, Any], compute_resources: Dict[str, Any], 
                 api_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.data_resources = data_resources
        self.compute_resources = compute_resources
        self.api_resources = api_resources
        self.monitoring_resources = {}
        
        # Create CloudWatch dashboards
        self._create_dashboards()
        
        # Create CloudWatch alarms
        self._create_alarms()
        
        # Create SNS topics for alerting
        self._create_alerting_topics()
        
        # Create X-Ray sampling rules
        self._create_xray_resources()
        
        # Create custom metrics
        self._create_custom_metrics()
    
    def _create_dashboards(self) -> None:
        """
        Create CloudWatch dashboards for system monitoring
        """
        
        # Main system dashboard
        self.system_dashboard = cloudwatch.Dashboard(
            self, "SystemDashboard",
            dashboard_name=get_resource_name(self.config, "dashboard", "system"),
            widgets=[
                [
                    # API Gateway metrics
                    cloudwatch.GraphWidget(
                        title="API Gateway Requests",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Count",
                                dimensions_map={
                                    "ApiName": self.api_resources["rest_api"].rest_api_name
                                },
                                statistic="Sum"
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Latency",
                                dimensions_map={
                                    "ApiName": self.api_resources["rest_api"].rest_api_name
                                },
                                statistic="Average"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    # Lambda function metrics
                    cloudwatch.GraphWidget(
                        title="Lambda Function Performance",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations",
                                dimensions_map={
                                    "FunctionName": self.compute_resources.get("data_processing_function", {}).get("function_name", "placeholder-function")
                                },
                                statistic="Sum"
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Duration",
                                dimensions_map={
                                    "FunctionName": self.compute_resources.get("data_processing_function", {}).get("function_name", "placeholder-function")
                                },
                                statistic="Average"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    # DynamoDB metrics
                    cloudwatch.GraphWidget(
                        title="DynamoDB Operations",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ConsumedReadCapacityUnits",
                                dimensions_map={
                                    "TableName": get_resource_name(self.config, "table", "readings")
                                },
                                statistic="Sum"
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ConsumedWriteCapacityUnits",
                                dimensions_map={
                                    "TableName": get_resource_name(self.config, "table", "readings")
                                },
                                statistic="Sum"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    # Custom business metrics
                    cloudwatch.GraphWidget(
                        title="Water Quality Alerts",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Alerts",
                                metric_name="CriticalAlerts",
                                statistic="Sum"
                            ),
                            cloudwatch.Metric(
                                namespace="AquaChain/Alerts",
                                metric_name="WarningAlerts",
                                statistic="Sum"
                            )
                        ],
                        width=6,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="Device Status",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Devices",
                                metric_name="ActiveDevices",
                                statistic="Average"
                            ),
                            cloudwatch.Metric(
                                namespace="AquaChain/Devices",
                                metric_name="OfflineDevices",
                                statistic="Average"
                            )
                        ],
                        width=6,
                        height=6
                    )
                ]
            ]
        )
        
        # Performance dashboard
        self.performance_dashboard = cloudwatch.Dashboard(
            self, "PerformanceDashboard",
            dashboard_name=get_resource_name(self.config, "dashboard", "performance"),
            widgets=[
                [
                    # Alert latency tracking
                    cloudwatch.GraphWidget(
                        title="Alert Latency (Target: <30s)",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Performance",
                                metric_name="AlertLatency",
                                statistic="Average"
                            ),
                            cloudwatch.Metric(
                                namespace="AquaChain/Performance",
                                metric_name="AlertLatency",
                                statistic="p95"
                            )
                        ],
                        width=12,
                        height=6,
                        left_y_axis=cloudwatch.YAxisProps(
                            min=0,
                            max=60
                        )
                    )
                ],
                [
                    # System uptime
                    cloudwatch.GraphWidget(
                        title="System Uptime (Target: 99.5%)",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/SLI",
                                metric_name="DataIngestionUptime",
                                statistic="Average"
                            ),
                            cloudwatch.Metric(
                                namespace="AquaChain/SLI",
                                metric_name="APIUptime",
                                statistic="Average"
                            )
                        ],
                        width=12,
                        height=6,
                        left_y_axis=cloudwatch.YAxisProps(
                            min=95,
                            max=100
                        )
                    )
                ]
            ]
        )
        
        self.monitoring_resources.update({
            "system_dashboard": self.system_dashboard,
            "performance_dashboard": self.performance_dashboard
        })
    
    def _create_alarms(self) -> None:
        """
        Create CloudWatch alarms for system monitoring
        """
        
        # API Gateway error rate alarm
        self.api_error_alarm = cloudwatch.Alarm(
            self, "APIErrorAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "api-errors"),
            alarm_description="API Gateway error rate exceeds threshold",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={
                    "ApiName": self.api_resources["rest_api"].rest_api_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # Lambda function error alarm
        self.lambda_error_alarm = cloudwatch.Alarm(
            self, "LambdaErrorAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "lambda-errors"),
            alarm_description="Lambda function error rate exceeds threshold",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=5,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # DynamoDB throttling alarm
        self.dynamodb_throttle_alarm = cloudwatch.Alarm(
            self, "DynamoDBThrottleAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "dynamodb-throttles"),
            alarm_description="DynamoDB throttling detected",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ThrottledRequests",
                dimensions_map={
                    "TableName": get_resource_name(self.config, "table", "readings")
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        # Alert latency alarm (custom metric)
        self.alert_latency_alarm = cloudwatch.Alarm(
            self, "AlertLatencyAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "alert-latency"),
            alarm_description="Alert delivery latency exceeds 30 seconds",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Performance",
                metric_name="AlertLatency",
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=30,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # System uptime alarm
        self.uptime_alarm = cloudwatch.Alarm(
            self, "UptimeAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "system-uptime"),
            alarm_description="System uptime below 99.5%",
            metric=cloudwatch.Metric(
                namespace="AquaChain/SLI",
                metric_name="DataIngestionUptime",
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=99.5,
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
        )
        
        # Device offline alarm
        self.device_offline_alarm = cloudwatch.Alarm(
            self, "DeviceOfflineAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "devices-offline"),
            alarm_description="High number of offline devices detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Devices",
                metric_name="OfflineDevices",
                statistic="Average",
                period=Duration.minutes(10)
            ),
            threshold=10,  # More than 10 devices offline
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        self.monitoring_resources.update({
            "api_error_alarm": self.api_error_alarm,
            "lambda_error_alarm": self.lambda_error_alarm,
            "dynamodb_throttle_alarm": self.dynamodb_throttle_alarm,
            "alert_latency_alarm": self.alert_latency_alarm,
            "uptime_alarm": self.uptime_alarm,
            "device_offline_alarm": self.device_offline_alarm
        })
    
    def _create_alerting_topics(self) -> None:
        """
        Create SNS topics for different types of alerts
        """
        
        # Critical alerts topic (P1 incidents)
        self.critical_alerts_topic = sns.Topic(
            self, "CriticalAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "critical-alerts"),
            display_name="AquaChain Critical System Alerts"
        )
        
        # Warning alerts topic (P2 incidents)
        self.warning_alerts_topic = sns.Topic(
            self, "WarningAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "warning-alerts"),
            display_name="AquaChain Warning Alerts"
        )
        
        # Add email subscriptions
        for email in self.config["notification_channels"]["email"]:
            self.critical_alerts_topic.add_subscription(
                subscriptions.EmailSubscription(email)
            )
            self.warning_alerts_topic.add_subscription(
                subscriptions.EmailSubscription(email)
            )
        
        # Add PagerDuty integration if configured
        if self.config["notification_channels"].get("pagerduty_integration_key"):
            # PagerDuty integration would be handled via HTTPS endpoint
            # This is a placeholder for the actual PagerDuty webhook
            pass
        
        # Connect alarms to appropriate topics
        self.api_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.warning_alerts_topic)
        )
        
        self.lambda_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.warning_alerts_topic)
        )
        
        self.dynamodb_throttle_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.critical_alerts_topic)
        )
        
        self.alert_latency_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.critical_alerts_topic)
        )
        
        self.uptime_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.critical_alerts_topic)
        )
        
        self.device_offline_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.warning_alerts_topic)
        )
        
        self.monitoring_resources.update({
            "critical_alerts_topic": self.critical_alerts_topic,
            "warning_alerts_topic": self.warning_alerts_topic
        })
    
    def _create_xray_resources(self) -> None:
        """
        Create X-Ray sampling rules for distributed tracing
        """
        
        # X-Ray sampling rule for AquaChain services
        self.xray_sampling_rule = xray.CfnSamplingRule(
            self, "XRaySamplingRule",
            sampling_rule=xray.CfnSamplingRule.SamplingRuleProperty(
                rule_name=get_resource_name(self.config, "xray", "sampling-rule"),
                priority=9000,
                fixed_rate=0.1,  # 10% sampling rate
                reservoir_size=1,
                service_name="AquaChain*",
                service_type="*",
                host="*",
                http_method="*",
                url_path="*",
                resource_arn="*",
                version=1
            )
        )
        
        # Higher sampling for critical paths
        self.xray_critical_sampling_rule = xray.CfnSamplingRule(
            self, "XRayCriticalSamplingRule",
            sampling_rule=xray.CfnSamplingRule.SamplingRuleProperty(
                rule_name=get_resource_name(self.config, "xray", "critical-sampling"),
                priority=1000,
                fixed_rate=0.5,  # 50% sampling rate for critical paths
                reservoir_size=2,
                service_name="AquaChain*",
                service_type="*",
                host="*",
                http_method="*",
                url_path="/api/v1/readings*",  # Critical data path
                resource_arn="*",
                version=1
            )
        )
        
        self.monitoring_resources.update({
            "xray_sampling_rule": self.xray_sampling_rule,
            "xray_critical_sampling_rule": self.xray_critical_sampling_rule
        })
    
    def _create_custom_metrics(self) -> None:
        """
        Create custom CloudWatch metrics for business KPIs
        """
        
        # Custom metric filters for application logs
        
        # Alert latency metric filter
        self.alert_latency_filter = logs.MetricFilter(
            self, "AlertLatencyFilter",
            log_group=logs.LogGroup.from_log_group_name(
                self, "AppLogGroup",
                f"/aws/lambda/{get_resource_name(self.config, 'app', 'logs')}"
            ),
            metric_namespace="AquaChain/Performance",
            metric_name="AlertLatency",
            filter_pattern=logs.FilterPattern.literal("[timestamp, requestId, level=\"INFO\", message=\"ALERT_DELIVERED\", latency]"),
            metric_value="$latency"
        )
        
        # Device status metric filters
        self.active_devices_filter = logs.MetricFilter(
            self, "ActiveDevicesFilter",
            log_group=logs.LogGroup.from_log_group_name(
                self, "IoTLogGroup",
                f"/aws/iot/{get_resource_name(self.config, 'iot', 'logs')}"
            ),
            metric_namespace="AquaChain/Devices",
            metric_name="ActiveDevices",
            filter_pattern=logs.FilterPattern.literal("[timestamp, level=\"INFO\", message=\"DEVICE_HEARTBEAT\", deviceId]"),
            metric_value="1"
        )
        
        # Water quality alerts metric
        self.critical_alerts_filter = logs.MetricFilter(
            self, "CriticalAlertsFilter",
            log_group=logs.LogGroup.from_log_group_name(
                self, "AlertLogGroup",
                f"/aws/lambda/{get_resource_name(self.config, 'app', 'logs')}"
            ),
            metric_namespace="AquaChain/Alerts",
            metric_name="CriticalAlerts",
            filter_pattern=logs.FilterPattern.literal("[timestamp, requestId, level=\"WARN\", message=\"CRITICAL_WATER_QUALITY_ALERT\"]"),
            metric_value="1"
        )
        
        self.monitoring_resources.update({
            "alert_latency_filter": self.alert_latency_filter,
            "active_devices_filter": self.active_devices_filter,
            "critical_alerts_filter": self.critical_alerts_filter
        })
        
        # Outputs
        CfnOutput(
            self, "SystemDashboardURL",
            value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.system_dashboard.dashboard_name}",
            description="URL to system monitoring dashboard"
        )
        
        CfnOutput(
            self, "PerformanceDashboardURL",
            value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.performance_dashboard.dashboard_name}",
            description="URL to performance monitoring dashboard"
        )