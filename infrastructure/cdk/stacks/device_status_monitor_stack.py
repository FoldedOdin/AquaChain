"""
Device Status Monitor Stack
Creates Lambda function and CloudWatch Events for monitoring device online/offline status
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_cloudwatch as cloudwatch,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class DeviceStatusMonitorStack(Stack):
    """
    Stack for device status monitoring infrastructure
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], 
                 devices_table: dynamodb.Table, readings_table: dynamodb.Table, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.devices_table = devices_table
        self.readings_table = readings_table
        
        # Create Lambda function
        self._create_status_monitor_lambda()
        
        # Create CloudWatch Events rule
        self._create_scheduled_rule()
        
        # Create CloudWatch dashboard
        self._create_monitoring_dashboard()
        
        # Create alarms
        self._create_alarms()
    
    def _create_status_monitor_lambda(self) -> None:
        """
        Create Lambda function for device status monitoring
        """
        
        # Create Lambda function
        self.status_monitor_lambda = _lambda.Function(
            self, "DeviceStatusMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("../../lambda/device_status_monitor"),
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                "DEVICES_TABLE": self.devices_table.table_name,
                "READINGS_TABLE": self.readings_table.table_name,
                "OFFLINE_THRESHOLD_MINUTES": "5",  # 5 minutes threshold
                "LOG_LEVEL": "INFO"
            },
            description="Monitors device online/offline status based on data transmission"
        )
        
        # Grant permissions to DynamoDB tables
        self.devices_table.grant_read_write_data(self.status_monitor_lambda)
        self.readings_table.grant_read_data(self.status_monitor_lambda)
        
        # Grant CloudWatch permissions
        self.status_monitor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )
        
        # Add tags
        from aws_cdk import Tags
        Tags.of(self.status_monitor_lambda).add("Project", "AquaChain")
        Tags.of(self.status_monitor_lambda).add("Service", "DeviceStatusMonitor")
        Tags.of(self.status_monitor_lambda).add("Environment", self.config.get("environment", "dev"))
    
    def _create_scheduled_rule(self) -> None:
        """
        Create CloudWatch Events rule to trigger status monitoring every 2 minutes
        """
        
        # Create rule that runs every 2 minutes
        self.status_check_rule = events.Rule(
            self, "DeviceStatusCheckRule",
            schedule=events.Schedule.rate(Duration.minutes(2)),
            description="Triggers device status monitoring every 2 minutes"
        )
        
        # Add Lambda as target
        self.status_check_rule.add_target(
            targets.LambdaFunction(self.status_monitor_lambda)
        )
    
    def _create_monitoring_dashboard(self) -> None:
        """
        Create CloudWatch dashboard for device status monitoring
        """
        
        self.dashboard = cloudwatch.Dashboard(
            self, "DeviceStatusDashboard",
            dashboard_name="AquaChain-DeviceStatus",
            widgets=[
                [
                    # Device status counts
                    cloudwatch.GraphWidget(
                        title="Device Status Overview",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/DeviceStatus",
                                metric_name="DevicesCountOnline",
                                statistic="Average"
                            ),
                            cloudwatch.Metric(
                                namespace="AquaChain/DeviceStatus", 
                                metric_name="DevicesCountOffline",
                                statistic="Average"
                            ),
                            cloudwatch.Metric(
                                namespace="AquaChain/DeviceStatus",
                                metric_name="DevicesCountUnknown", 
                                statistic="Average"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    # Status changes over time
                    cloudwatch.GraphWidget(
                        title="Device Status Changes",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/DeviceStatus",
                                metric_name="DeviceStatusChanges",
                                statistic="Sum"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    # Lambda function metrics
                    cloudwatch.GraphWidget(
                        title="Status Monitor Lambda Performance",
                        left=[
                            self.status_monitor_lambda.metric_duration(),
                            self.status_monitor_lambda.metric_errors()
                        ],
                        width=12,
                        height=6
                    )
                ]
            ]
        )
    
    def _create_alarms(self) -> None:
        """
        Create CloudWatch alarms for device status monitoring
        """
        
        # Alarm for high number of offline devices
        self.offline_devices_alarm = cloudwatch.Alarm(
            self, "HighOfflineDevicesAlarm",
            metric=cloudwatch.Metric(
                namespace="AquaChain/DeviceStatus",
                metric_name="DevicesCountOffline",
                statistic="Average"
            ),
            threshold=10,  # Alert if more than 10 devices are offline
            evaluation_periods=2,
            datapoints_to_alarm=2,
            alarm_description="Alert when more than 10 devices are offline",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Alarm for Lambda function errors
        self.lambda_error_alarm = cloudwatch.Alarm(
            self, "StatusMonitorLambdaErrorAlarm",
            metric=self.status_monitor_lambda.metric_errors(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alert when device status monitor Lambda has errors"
        )
        
        # Alarm for Lambda function duration
        self.lambda_duration_alarm = cloudwatch.Alarm(
            self, "StatusMonitorLambdaDurationAlarm",
            metric=self.status_monitor_lambda.metric_duration(),
            threshold=30000,  # 30 seconds
            evaluation_periods=2,
            alarm_description="Alert when device status monitor Lambda takes too long"
        )
    
    @property
    def outputs(self) -> Dict[str, CfnOutput]:
        """Stack outputs"""
        return {
            "StatusMonitorLambdaArn": CfnOutput(
                self, "StatusMonitorLambdaArn",
                value=self.status_monitor_lambda.function_arn,
                description="Device Status Monitor Lambda ARN"
            ),
            "DashboardUrl": CfnOutput(
                self, "DashboardUrl", 
                value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=AquaChain-DeviceStatus",
                description="CloudWatch Dashboard URL"
            )
        }