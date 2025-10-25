"""
Multi-Region WebSocket Stack for AquaChain System
Configures WebSocket APIs across multiple regions with Route53 health checks
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_cloudwatch_actions as cw_actions,
)
from constructs import Construct
from typing import Dict, List


class WebSocketMultiRegionStack(Stack):
    """
    Stack for multi-region WebSocket API deployment with health checks and failover
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: Dict,
        primary_websocket_api: any,
        secondary_websocket_api: any = None,
        tertiary_websocket_api: any = None,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.config = config
        self.primary_api = primary_websocket_api
        self.secondary_api = secondary_websocket_api
        self.tertiary_api = tertiary_websocket_api

        # Create health checks and alarms
        self._create_health_checks()

        # Create Route53 routing if multi-region is enabled
        if config.get("enable_multi_region", False):
            self._create_route53_routing()

    def _create_health_checks(self) -> None:
        """
        Create CloudWatch alarms for WebSocket API health monitoring
        """
        # SNS topic for health check alerts
        self.health_alert_topic = sns.Topic(
            self,
            "WebSocketHealthAlertTopic",
            display_name="WebSocket API Health Alerts",
            topic_name=f"aquachain-websocket-health-{self.config['environment']}"
        )

        # Primary region health check
        primary_error_metric = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="5XXError",
            dimensions_map={
                "ApiId": self.primary_api.ref
            },
            statistic="Sum",
            period=Duration.minutes(1)
        )

        primary_health_alarm = cloudwatch.Alarm(
            self,
            "PrimaryWebSocketHealthAlarm",
            alarm_name=f"aquachain-websocket-primary-health-{self.config['environment']}",
            metric=primary_error_metric,
            threshold=10,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="Primary WebSocket API experiencing high error rate"
        )

        primary_health_alarm.add_alarm_action(
            cw_actions.SnsAction(self.health_alert_topic)
        )

        # Connection count metric for monitoring
        connection_metric = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="ConnectCount",
            dimensions_map={
                "ApiId": self.primary_api.ref
            },
            statistic="Sum",
            period=Duration.minutes(5)
        )

        # Create dashboard for monitoring
        dashboard = cloudwatch.Dashboard(
            self,
            "WebSocketHealthDashboard",
            dashboard_name=f"aquachain-websocket-health-{self.config['environment']}"
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="WebSocket Connections",
                left=[connection_metric],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="WebSocket Errors",
                left=[primary_error_metric],
                width=12
            )
        )

        # Secondary region health check if available
        if self.secondary_api:
            secondary_error_metric = cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                dimensions_map={
                    "ApiId": self.secondary_api.ref
                },
                statistic="Sum",
                period=Duration.minutes(1)
            )

            secondary_health_alarm = cloudwatch.Alarm(
                self,
                "SecondaryWebSocketHealthAlarm",
                alarm_name=f"aquachain-websocket-secondary-health-{self.config['environment']}",
                metric=secondary_error_metric,
                threshold=10,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
                alarm_description="Secondary WebSocket API experiencing high error rate"
            )

            secondary_health_alarm.add_alarm_action(
                cw_actions.SnsAction(self.health_alert_topic)
            )

    def _create_route53_routing(self) -> None:
        """
        Create Route53 health checks and geographic routing for multi-region setup
        """
        # Note: This requires a hosted zone to be created separately
        # The hosted zone should be passed in the config
        
        hosted_zone_id = self.config.get("hosted_zone_id")
        domain_name = self.config.get("domain_name")

        if not hosted_zone_id or not domain_name:
            print("Warning: hosted_zone_id and domain_name required for Route53 routing")
            return

        # Import existing hosted zone
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=hosted_zone_id,
            zone_name=domain_name
        )

        # Create health checks for each region
        primary_health_check = route53.CfnHealthCheck(
            self,
            "PrimaryHealthCheck",
            health_check_config=route53.CfnHealthCheck.HealthCheckConfigProperty(
                type="HTTPS",
                resource_path="/health",
                fully_qualified_domain_name=f"{self.primary_api.ref}.execute-api.{self.region}.amazonaws.com",
                port=443,
                request_interval=30,
                failure_threshold=3
            ),
            health_check_tags=[
                route53.CfnHealthCheck.HealthCheckTagProperty(
                    key="Name",
                    value=f"aquachain-websocket-primary-{self.config['environment']}"
                )
            ]
        )

        # Create weighted routing records
        # Primary region (highest weight)
        route53.CfnRecordSet(
            self,
            "PrimaryWebSocketRecord",
            hosted_zone_id=hosted_zone.hosted_zone_id,
            name=f"ws.{domain_name}",
            type="CNAME",
            ttl="60",
            resource_records=[
                f"{self.primary_api.ref}.execute-api.{self.region}.amazonaws.com"
            ],
            set_identifier="primary",
            weight=100,
            health_check_id=primary_health_check.attr_health_check_id
        )

        # Secondary region if available
        if self.secondary_api:
            secondary_region = self.config.get("secondary_region", "us-west-2")
            
            secondary_health_check = route53.CfnHealthCheck(
                self,
                "SecondaryHealthCheck",
                health_check_config=route53.CfnHealthCheck.HealthCheckConfigProperty(
                    type="HTTPS",
                    resource_path="/health",
                    fully_qualified_domain_name=f"{self.secondary_api.ref}.execute-api.{secondary_region}.amazonaws.com",
                    port=443,
                    request_interval=30,
                    failure_threshold=3
                ),
                health_check_tags=[
                    route53.CfnHealthCheck.HealthCheckTagProperty(
                        key="Name",
                        value=f"aquachain-websocket-secondary-{self.config['environment']}"
                    )
                ]
            )

            route53.CfnRecordSet(
                self,
                "SecondaryWebSocketRecord",
                hosted_zone_id=hosted_zone.hosted_zone_id,
                name=f"ws.{domain_name}",
                type="CNAME",
                ttl="60",
                resource_records=[
                    f"{self.secondary_api.ref}.execute-api.{secondary_region}.amazonaws.com"
                ],
                set_identifier="secondary",
                weight=50,
                health_check_id=secondary_health_check.attr_health_check_id
            )

        # Tertiary region if available
        if self.tertiary_api:
            tertiary_region = self.config.get("tertiary_region", "eu-west-1")
            
            tertiary_health_check = route53.CfnHealthCheck(
                self,
                "TertiaryHealthCheck",
                health_check_config=route53.CfnHealthCheck.HealthCheckConfigProperty(
                    type="HTTPS",
                    resource_path="/health",
                    fully_qualified_domain_name=f"{self.tertiary_api.ref}.execute-api.{tertiary_region}.amazonaws.com",
                    port=443,
                    request_interval=30,
                    failure_threshold=3
                ),
                health_check_tags=[
                    route53.CfnHealthCheck.HealthCheckTagProperty(
                        key="Name",
                        value=f"aquachain-websocket-tertiary-{self.config['environment']}"
                    )
                ]
            )

            route53.CfnRecordSet(
                self,
                "TertiaryWebSocketRecord",
                hosted_zone_id=hosted_zone.hosted_zone_id,
                name=f"ws.{domain_name}",
                type="CNAME",
                ttl="60",
                resource_records=[
                    f"{self.tertiary_api.ref}.execute-api.{tertiary_region}.amazonaws.com"
                ],
                set_identifier="tertiary",
                weight=25,
                health_check_id=tertiary_health_check.attr_health_check_id
            )

        # Output the Route53 endpoint
        CfnOutput(
            self,
            "WebSocketDomainEndpoint",
            value=f"wss://ws.{domain_name}",
            description="Multi-region WebSocket endpoint with automatic failover"
        )

        CfnOutput(
            self,
            "HealthAlertTopicArn",
            value=self.health_alert_topic.topic_arn,
            description="SNS topic for WebSocket health alerts"
        )
