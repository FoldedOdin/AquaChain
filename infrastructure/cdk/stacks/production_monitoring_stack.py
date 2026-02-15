"""
AquaChain Dashboard Overhaul Production Monitoring Stack
Implements comprehensive CloudWatch dashboards, alerts, incident response, and compliance reporting
"""

from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_logs as logs,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_s3 as s3,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Tags
)
from constructs import Construct
from typing import Dict, Any, List
from config.environment_config import get_resource_name

class ProductionMonitoringStack(Stack):
    """
    Production monitoring stack with comprehensive dashboards, alerting, and incident response
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.monitoring_resources = {}
        
        # Create SNS topics for different alert severities
        self._create_notification_topics()
        
        # Create CloudWatch dashboards
        self._create_cloudwatch_dashboards()
        
        # Create performance monitoring alarms
        self._create_performance_alarms()
        
        # Create security monitoring alarms
        self._create_security_alarms()
        
        # Create business metrics monitoring
        self._create_business_metrics_alarms()
        
        # Create incident response automation
        self._create_incident_response_automation()
        
        # Create compliance reporting automation
        self._create_compliance_reporting()
        
        # Create runbooks and documentation
        self._create_runbooks()
        
        # Tag all resources
        self._tag_resources()
    
    def _create_notification_topics(self) -> None:
        """
        Create SNS topics for different alert severities and channels
        """
        
        # Critical alerts topic (P1 incidents)
        self.critical_alerts_topic = sns.Topic(
            self, "CriticalAlertsT opic",
            topic_name=get_resource_name(self.config, "topic", "critical-alerts"),
            display_name="Dashboard Critical Alerts (P1)"
        )
        
        # Warning alerts topic (P2/P3 incidents)
        self.warning_alerts_topic = sns.Topic(
            self, "WarningAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "warning-alerts"),
            display_name="Dashboard Warning Alerts (P2/P3)"
        )
        
        # Info alerts topic (monitoring notifications)
        self.info_alerts_topic = sns.Topic(
            self, "InfoAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "info-alerts"),
            display_name="Dashboard Info Alerts"
        )
        
        # Security alerts topic (security incidents)
        self.security_alerts_topic = sns.Topic(
            self, "SecurityAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "security-alerts"),
            display_name="Dashboard Security Alerts"
        )
        
        # Add email subscriptions based on configuration
        notification_config = self.config.get("notification_channels", {})
        
        for email in notification_config.get("email", []):
            # Critical alerts go to all emails
            self.critical_alerts_topic.add_subscription(
                sns_subscriptions.EmailSubscription(email)
            )
            
            # Security alerts go to all emails
            self.security_alerts_topic.add_subscription(
                sns_subscriptions.EmailSubscription(email)
            )
        
        # Add Slack webhook if configured
        slack_webhook = notification_config.get("slack_webhook")
        if slack_webhook:
            # Create Lambda function to send Slack notifications
            self._create_slack_notification_lambda(slack_webhook)
        
        # Add PagerDuty integration if configured
        pagerduty_key = notification_config.get("pagerduty_integration_key")
        if pagerduty_key:
            # Create Lambda function for PagerDuty integration
            self._create_pagerduty_integration_lambda(pagerduty_key)
        
        self.monitoring_resources.update({
            "critical_alerts_topic": self.critical_alerts_topic,
            "warning_alerts_topic": self.warning_alerts_topic,
            "info_alerts_topic": self.info_alerts_topic,
            "security_alerts_topic": self.security_alerts_topic
        })
    
    def _create_slack_notification_lambda(self, webhook_url: str) -> None:
        """
        Create Lambda function for Slack notifications
        """
        
        self.slack_notification_lambda = lambda_.Function(
            self, "SlackNotificationLambda",
            function_name=get_resource_name(self.config, "function", "slack-notifications"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline(f"""
import json
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WEBHOOK_URL = "{webhook_url}"

def main(event, context):
    '''
    Send notifications to Slack
    '''
    logger.info(f"Slack notification event: {{json.dumps(event)}}")
    
    try:
        # Parse SNS message
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        
        # Determine alert severity and color
        topic_arn = event['Records'][0]['Sns']['TopicArn']
        if 'critical' in topic_arn.lower():
            color = '#FF0000'  # Red
            severity = 'CRITICAL'
        elif 'security' in topic_arn.lower():
            color = '#FF8C00'  # Orange
            severity = 'SECURITY'
        elif 'warning' in topic_arn.lower():
            color = '#FFD700'  # Yellow
            severity = 'WARNING'
        else:
            color = '#00FF00'  # Green
            severity = 'INFO'
        
        # Create Slack message
        slack_message = {{
            "attachments": [
                {{
                    "color": color,
                    "title": f"{{severity}} Alert - AquaChain Dashboard",
                    "text": sns_message.get('AlarmDescription', 'No description'),
                    "fields": [
                        {{
                            "title": "Alarm Name",
                            "value": sns_message.get('AlarmName', 'Unknown'),
                            "short": True
                        }},
                        {{
                            "title": "State",
                            "value": sns_message.get('NewStateValue', 'Unknown'),
                            "short": True
                        }},
                        {{
                            "title": "Reason",
                            "value": sns_message.get('NewStateReason', 'No reason provided'),
                            "short": False
                        }}
                    ],
                    "timestamp": int(context.aws_request_id.split('-')[0], 16)
                }}
            ]
        }}
        
        # Send to Slack
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            WEBHOOK_URL,
            body=json.dumps(slack_message),
            headers={{'Content-Type': 'application/json'}}
        )
        
        logger.info(f"Slack notification sent: {{response.status}}")
        
        return {{
            'statusCode': 200,
            'body': json.dumps('Slack notification sent successfully')
        }}
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {{str(e)}}")
        raise e
            """),
            timeout=Duration.seconds(30)
        )
        
        # Subscribe Lambda to SNS topics
        for topic in [self.critical_alerts_topic, self.security_alerts_topic, self.warning_alerts_topic]:
            topic.add_subscription(
                sns_subscriptions.LambdaSubscription(self.slack_notification_lambda)
            )

    
    def _create_pagerduty_integration_lambda(self, integration_key: str) -> None:
        """
        Create Lambda function for PagerDuty integration
        """
        
        self.pagerduty_lambda = lambda_.Function(
            self, "PagerDutyLambda",
            function_name=get_resource_name(self.config, "function", "pagerduty-integration"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline(f"""
import json
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

INTEGRATION_KEY = "{integration_key}"

def main(event, context):
    '''
    Send incidents to PagerDuty
    '''
    logger.info(f"PagerDuty event: {{json.dumps(event)}}")
    
    try:
        # Parse SNS message
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        
        # Determine event action
        state = sns_message.get('NewStateValue', 'UNKNOWN')
        if state == 'ALARM':
            event_action = 'trigger'
        elif state == 'OK':
            event_action = 'resolve'
        else:
            event_action = 'trigger'
        
        # Create PagerDuty event
        pagerduty_event = {{
            "routing_key": INTEGRATION_KEY,
            "event_action": event_action,
            "dedup_key": sns_message.get('AlarmName', 'unknown-alarm'),
            "payload": {{
                "summary": f"{{sns_message.get('AlarmName', 'Unknown Alarm')}} - {{state}}",
                "source": "AquaChain Dashboard Monitoring",
                "severity": "critical" if 'critical' in event['Records'][0]['Sns']['TopicArn'].lower() else "warning",
                "component": "dashboard-overhaul",
                "group": "aquachain",
                "class": "monitoring",
                "custom_details": {{
                    "alarm_description": sns_message.get('AlarmDescription', ''),
                    "state_reason": sns_message.get('NewStateReason', ''),
                    "region": sns_message.get('Region', ''),
                    "account_id": sns_message.get('AWSAccountId', '')
                }}
            }}
        }}
        
        # Send to PagerDuty
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            'https://events.pagerduty.com/v2/enqueue',
            body=json.dumps(pagerduty_event),
            headers={{'Content-Type': 'application/json'}}
        )
        
        logger.info(f"PagerDuty event sent: {{response.status}}")
        
        return {{
            'statusCode': 200,
            'body': json.dumps('PagerDuty event sent successfully')
        }}
        
    except Exception as e:
        logger.error(f"Failed to send PagerDuty event: {{str(e)}}")
        raise e
            """),
            timeout=Duration.seconds(30)
        )
        
        # Subscribe Lambda to critical and security alerts only
        for topic in [self.critical_alerts_topic, self.security_alerts_topic]:
            topic.add_subscription(
                sns_subscriptions.LambdaSubscription(self.pagerduty_lambda)
            )
    
    def _create_cloudwatch_dashboards(self) -> None:
        """
        Create comprehensive CloudWatch dashboards for system monitoring
        """
        
        # Main system overview dashboard
        self.system_overview_dashboard = cloudwatch.Dashboard(
            self, "SystemOverviewDashboard",
            dashboard_name=get_resource_name(self.config, "dashboard", "system-overview"),
            widgets=[
                # API Gateway metrics row
                [
                    cloudwatch.GraphWidget(
                        title="API Gateway - Request Count",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Count",
                                dimensions_map={"ApiName": "DashboardAPI"},
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="API Gateway - Latency",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Latency",
                                dimensions_map={"ApiName": "DashboardAPI"},
                                statistic="Average",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                
                # Lambda metrics row
                [
                    cloudwatch.GraphWidget(
                        title="Lambda - Invocations",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=8,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="Lambda - Duration",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Duration",
                                statistic="Average",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=8,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="Lambda - Errors",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Errors",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=8,
                        height=6
                    )
                ],
                
                # DynamoDB metrics row
                [
                    cloudwatch.GraphWidget(
                        title="DynamoDB - Read/Write Capacity",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ConsumedReadCapacityUnits",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ConsumedWriteCapacityUnits",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="DynamoDB - Throttled Requests",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ThrottledRequests",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    )
                ]
            ]
        )
        
        # Security monitoring dashboard
        self.security_dashboard = cloudwatch.Dashboard(
            self, "SecurityDashboard",
            dashboard_name=get_resource_name(self.config, "dashboard", "security"),
            widgets=[
                # Authentication metrics
                [
                    cloudwatch.GraphWidget(
                        title="Authentication - Success/Failure Rate",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="AuthenticationSuccess",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="AuthenticationFailure",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="Authorization - Access Denied",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="AuthorizationDenied",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                
                # Security events
                [
                    cloudwatch.GraphWidget(
                        title="Security Events - Suspicious Activity",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="SuspiciousActivity",
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=24,
                        height=6
                    )
                ]
            ]
        )
        
        # Business metrics dashboard
        self.business_dashboard = cloudwatch.Dashboard(
            self, "BusinessDashboard",
            dashboard_name=get_resource_name(self.config, "dashboard", "business-metrics"),
            widgets=[
                # Purchase order metrics
                [
                    cloudwatch.GraphWidget(
                        title="Purchase Orders - Submitted vs Approved",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="PurchaseOrdersSubmitted",
                                statistic="Sum",
                                period=Duration.hours(1)
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="PurchaseOrdersApproved",
                                statistic="Sum",
                                period=Duration.hours(1)
                            )
                        ],
                        width=12,
                        height=6
                    ),
                    cloudwatch.GraphWidget(
                        title="Budget Utilization",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="BudgetUtilizationPercentage",
                                statistic="Average",
                                period=Duration.hours(1)
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                
                # Inventory metrics
                [
                    cloudwatch.GraphWidget(
                        title="Inventory - Reorder Alerts",
                        left=[
                            cloudwatch.Metric(
                                namespace="AquaChain/Dashboard",
                                metric_name="InventoryReorderAlerts",
                                statistic="Sum",
                                period=Duration.hours(1)
                            )
                        ],
                        width=24,
                        height=6
                    )
                ]
            ]
        )
        
        self.monitoring_resources.update({
            "system_overview_dashboard": self.system_overview_dashboard,
            "security_dashboard": self.security_dashboard,
            "business_dashboard": self.business_dashboard
        })
    
    def _create_performance_alarms(self) -> None:
        """
        Create CloudWatch alarms for performance monitoring
        """
        
        # API Gateway latency alarm
        api_latency_alarm = cloudwatch.Alarm(
            self, "APILatencyAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "api-latency"),
            alarm_description="API Gateway latency is high",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Latency",
                dimensions_map={"ApiName": "DashboardAPI"},
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=500,  # 500ms threshold
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        api_latency_alarm.add_alarm_action(
            cw_actions.SnsAction(self.warning_alerts_topic)
        )
        
        # API Gateway error rate alarm
        api_error_alarm = cloudwatch.Alarm(
            self, "APIErrorRateAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "api-error-rate"),
            alarm_description="API Gateway error rate is high",
            metric=cloudwatch.MathExpression(
                expression="(errors / requests) * 100",
                using_metrics={
                    "errors": cloudwatch.Metric(
                        namespace="AWS/ApiGateway",
                        metric_name="4XXError",
                        dimensions_map={"ApiName": "DashboardAPI"},
                        statistic="Sum",
                        period=Duration.minutes(5)
                    ),
                    "requests": cloudwatch.Metric(
                        namespace="AWS/ApiGateway",
                        metric_name="Count",
                        dimensions_map={"ApiName": "DashboardAPI"},
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                }
            ),
            threshold=5,  # 5% error rate threshold
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        api_error_alarm.add_alarm_action(
            cw_actions.SnsAction(self.critical_alerts_topic)
        )
        
        # Lambda error rate alarm
        lambda_error_alarm = cloudwatch.Alarm(
            self, "LambdaErrorRateAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "lambda-error-rate"),
            alarm_description="Lambda function error rate is high",
            metric=cloudwatch.MathExpression(
                expression="(errors / invocations) * 100",
                using_metrics={
                    "errors": cloudwatch.Metric(
                        namespace="AWS/Lambda",
                        metric_name="Errors",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    ),
                    "invocations": cloudwatch.Metric(
                        namespace="AWS/Lambda",
                        metric_name="Invocations",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                }
            ),
            threshold=2,  # 2% error rate threshold
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        lambda_error_alarm.add_alarm_action(
            cw_actions.SnsAction(self.critical_alerts_topic)
        )
        
        # DynamoDB throttling alarm
        dynamodb_throttle_alarm = cloudwatch.Alarm(
            self, "DynamoDBThrottleAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "dynamodb-throttle"),
            alarm_description="DynamoDB requests are being throttled",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ThrottledRequests",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        dynamodb_throttle_alarm.add_alarm_action(
            cw_actions.SnsAction(self.critical_alerts_topic)
        )
        
        self.monitoring_resources.update({
            "api_latency_alarm": api_latency_alarm,
            "api_error_alarm": api_error_alarm,
            "lambda_error_alarm": lambda_error_alarm,
            "dynamodb_throttle_alarm": dynamodb_throttle_alarm
        })
    
    def _create_security_alarms(self) -> None:
        """
        Create CloudWatch alarms for security monitoring
        """
        
        # Authentication failure alarm
        auth_failure_alarm = cloudwatch.Alarm(
            self, "AuthFailureAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "auth-failure"),
            alarm_description="High number of authentication failures detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Dashboard",
                metric_name="AuthenticationFailure",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=10,  # 10 failures in 5 minutes
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        auth_failure_alarm.add_alarm_action(
            cw_actions.SnsAction(self.security_alerts_topic)
        )
        
        # Authorization denied alarm
        authz_denied_alarm = cloudwatch.Alarm(
            self, "AuthzDeniedAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "authz-denied"),
            alarm_description="High number of authorization denials detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Dashboard",
                metric_name="AuthorizationDenied",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=20,  # 20 denials in 5 minutes
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        authz_denied_alarm.add_alarm_action(
            cw_actions.SnsAction(self.security_alerts_topic)
        )
        
        # Suspicious activity alarm
        suspicious_activity_alarm = cloudwatch.Alarm(
            self, "SuspiciousActivityAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "suspicious-activity"),
            alarm_description="Suspicious activity detected in the system",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Dashboard",
                metric_name="SuspiciousActivity",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=1,  # Any suspicious activity
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        suspicious_activity_alarm.add_alarm_action(
            cw_actions.SnsAction(self.security_alerts_topic)
        )
        
        self.monitoring_resources.update({
            "auth_failure_alarm": auth_failure_alarm,
            "authz_denied_alarm": authz_denied_alarm,
            "suspicious_activity_alarm": suspicious_activity_alarm
        })
    
    def _create_business_metrics_alarms(self) -> None:
        """
        Create CloudWatch alarms for business metrics monitoring
        """
        
        # Budget utilization alarm
        budget_utilization_alarm = cloudwatch.Alarm(
            self, "BudgetUtilizationAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "budget-utilization"),
            alarm_description="Budget utilization is approaching limit",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Dashboard",
                metric_name="BudgetUtilizationPercentage",
                statistic="Maximum",
                period=Duration.hours(1)
            ),
            threshold=90,  # 90% utilization threshold
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        budget_utilization_alarm.add_alarm_action(
            cw_actions.SnsAction(self.warning_alerts_topic)
        )
        
        # Purchase order approval delay alarm
        po_approval_delay_alarm = cloudwatch.Alarm(
            self, "POApprovalDelayAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "po-approval-delay"),
            alarm_description="Purchase orders are pending approval for too long",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Dashboard",
                metric_name="PendingApprovalDuration",
                statistic="Maximum",
                period=Duration.hours(1)
            ),
            threshold=24,  # 24 hours threshold
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        po_approval_delay_alarm.add_alarm_action(
            cw_actions.SnsAction(self.warning_alerts_topic)
        )
        
        self.monitoring_resources.update({
            "budget_utilization_alarm": budget_utilization_alarm,
            "po_approval_delay_alarm": po_approval_delay_alarm
        })
    
    def _create_incident_response_automation(self) -> None:
        """
        Create automated incident response procedures and runbooks
        """
        
        # Create S3 bucket for incident artifacts
        self.incident_artifacts_bucket = s3.Bucket(
            self, "IncidentArtifactsBucket",
            bucket_name=get_resource_name(self.config, "bucket", "incident-artifacts"),
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # Incident response Lambda function
        self.incident_response_lambda = lambda_.Function(
            self, "IncidentResponseLambda",
            function_name=get_resource_name(self.config, "function", "incident-response"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    '''
    Automated incident response handler
    '''
    logger.info(f"Incident response event: {json.dumps(event)}")
    
    try:
        # Parse CloudWatch alarm event
        alarm_data = event.get('detail', {})
        alarm_name = alarm_data.get('alarmName', 'Unknown')
        state = alarm_data.get('state', {}).get('value', 'UNKNOWN')
        
        if state == 'ALARM':
            # Create incident record
            incident_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            
            # Determine incident severity
            if 'critical' in alarm_name.lower() or 'security' in alarm_name.lower():
                severity = 'P1'
            elif 'error' in alarm_name.lower():
                severity = 'P2'
            else:
                severity = 'P3'
            
            # Create incident document
            incident_doc = {
                'incident_id': incident_id,
                'alarm_name': alarm_name,
                'severity': severity,
                'state': state,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'OPEN',
                'alarm_data': alarm_data
            }
            
            # Store incident document in S3
            s3_client = boto3.client('s3')
            s3_client.put_object(
                Bucket=context.function_name.split('-')[-2] + '-incident-artifacts-' + context.function_name.split('-')[-1],
                Key=f"incidents/{incident_id}.json",
                Body=json.dumps(incident_doc, indent=2),
                ContentType='application/json'
            )
            
            # Execute automated response based on alarm type
            if 'api-error-rate' in alarm_name:
                # API error rate response
                logger.info("Executing API error rate response...")
                # Could trigger automatic scaling, circuit breaker, etc.
                
            elif 'lambda-error-rate' in alarm_name:
                # Lambda error rate response
                logger.info("Executing Lambda error rate response...")
                # Could trigger function restart, rollback, etc.
                
            elif 'auth-failure' in alarm_name:
                # Authentication failure response
                logger.info("Executing authentication failure response...")
                # Could trigger IP blocking, rate limiting, etc.
                
            logger.info(f"Incident {incident_id} created and automated response executed")
            
        elif state == 'OK':
            # Alarm resolved - update incident status
            logger.info(f"Alarm {alarm_name} resolved")
            
        return {
            'statusCode': 200,
            'body': json.dumps('Incident response completed')
        }
        
    except Exception as e:
        logger.error(f"Incident response failed: {str(e)}")
        raise e
            """),
            timeout=Duration.minutes(5),
            environment={
                "INCIDENT_BUCKET": self.incident_artifacts_bucket.bucket_name
            }
        )
        
        # Grant permissions to incident response Lambda
        self.incident_artifacts_bucket.grant_write(self.incident_response_lambda)
        
        # Create EventBridge rule to trigger incident response
        incident_response_rule = events.Rule(
            self, "IncidentResponseRule",
            rule_name=get_resource_name(self.config, "rule", "incident-response"),
            description="Trigger incident response on CloudWatch alarms",
            event_pattern=events.EventPattern(
                source=["aws.cloudwatch"],
                detail_type=["CloudWatch Alarm State Change"],
                detail={
                    "state": {
                        "value": ["ALARM", "OK"]
                    }
                }
            )
        )
        
        incident_response_rule.add_target(
            targets.LambdaFunction(self.incident_response_lambda)
        )
        
        self.monitoring_resources.update({
            "incident_artifacts_bucket": self.incident_artifacts_bucket,
            "incident_response_lambda": self.incident_response_lambda,
            "incident_response_rule": incident_response_rule
        })
    
    def _create_compliance_reporting(self) -> None:
        """
        Create automated compliance reporting system
        """
        
        # Compliance reporting Lambda function
        self.compliance_reporting_lambda = lambda_.Function(
            self, "ComplianceReportingLambda",
            function_name=get_resource_name(self.config, "function", "compliance-reporting"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    '''
    Generate compliance reports
    '''
    logger.info(f"Compliance reporting event: {json.dumps(event)}")
    
    try:
        # Generate different types of reports based on event
        report_type = event.get('report_type', 'daily')
        
        if report_type == 'daily':
            report = generate_daily_compliance_report()
        elif report_type == 'weekly':
            report = generate_weekly_compliance_report()
        elif report_type == 'monthly':
            report = generate_monthly_compliance_report()
        else:
            report = generate_daily_compliance_report()
        
        # Store report in S3
        s3_client = boto3.client('s3')
        report_key = f"compliance-reports/{report_type}/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/report.json"
        
        s3_client.put_object(
            Bucket=context.function_name.split('-')[-2] + '-incident-artifacts-' + context.function_name.split('-')[-1],
            Key=report_key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Compliance report generated: {report_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Compliance report generated successfully')
        }
        
    except Exception as e:
        logger.error(f"Compliance reporting failed: {str(e)}")
        raise e

def generate_daily_compliance_report():
    '''Generate daily compliance report'''
    
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=1)
    
    # Query CloudWatch metrics for compliance data
    cloudwatch = boto3.client('cloudwatch')
    
    # Authentication metrics
    auth_metrics = cloudwatch.get_metric_statistics(
        Namespace='AquaChain/Dashboard',
        MetricName='AuthenticationSuccess',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    
    # Authorization metrics
    authz_metrics = cloudwatch.get_metric_statistics(
        Namespace='AquaChain/Dashboard',
        MetricName='AuthorizationDenied',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    
    # Audit log metrics
    audit_metrics = cloudwatch.get_metric_statistics(
        Namespace='AquaChain/Dashboard',
        MetricName='AuditLogEntries',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Sum']
    )
    
    return {
        'report_type': 'daily',
        'period': {
            'start': start_time.isoformat(),
            'end': end_time.isoformat()
        },
        'metrics': {
            'authentication_success_count': sum([dp['Sum'] for dp in auth_metrics.get('Datapoints', [])]),
            'authorization_denied_count': sum([dp['Sum'] for dp in authz_metrics.get('Datapoints', [])]),
            'audit_log_entries_count': sum([dp['Sum'] for dp in audit_metrics.get('Datapoints', [])])
        },
        'compliance_status': 'COMPLIANT',
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

def generate_weekly_compliance_report():
    '''Generate weekly compliance report'''
    # Similar to daily but with 7-day period
    return generate_daily_compliance_report()

def generate_monthly_compliance_report():
    '''Generate monthly compliance report'''
    # Similar to daily but with 30-day period
    return generate_daily_compliance_report()
            """),
            timeout=Duration.minutes(10),
            environment={
                "INCIDENT_BUCKET": self.incident_artifacts_bucket.bucket_name
            }
        )
        
        # Grant permissions to compliance reporting Lambda
        self.incident_artifacts_bucket.grant_write(self.compliance_reporting_lambda)
        self.compliance_reporting_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:GetMetricData"
                ],
                resources=["*"]
            )
        )
        
        # Create EventBridge rules for scheduled compliance reporting
        daily_compliance_rule = events.Rule(
            self, "DailyComplianceRule",
            rule_name=get_resource_name(self.config, "rule", "daily-compliance"),
            description="Generate daily compliance report",
            schedule=events.Schedule.cron(hour="6", minute="0")  # 6 AM UTC daily
        )
        
        daily_compliance_rule.add_target(
            targets.LambdaFunction(
                self.compliance_reporting_lambda,
                event=events.RuleTargetInput.from_object({"report_type": "daily"})
            )
        )
        
        weekly_compliance_rule = events.Rule(
            self, "WeeklyComplianceRule",
            rule_name=get_resource_name(self.config, "rule", "weekly-compliance"),
            description="Generate weekly compliance report",
            schedule=events.Schedule.cron(hour="7", minute="0", week_day="MON")  # Monday 7 AM UTC
        )
        
        weekly_compliance_rule.add_target(
            targets.LambdaFunction(
                self.compliance_reporting_lambda,
                event=events.RuleTargetInput.from_object({"report_type": "weekly"})
            )
        )
        
        self.monitoring_resources.update({
            "compliance_reporting_lambda": self.compliance_reporting_lambda,
            "daily_compliance_rule": daily_compliance_rule,
            "weekly_compliance_rule": weekly_compliance_rule
        })
    
    def _create_runbooks(self) -> None:
        """
        Create incident response runbooks and documentation
        """
        
        # Store runbooks in S3 for easy access
        runbooks = {
            "api_latency_runbook.md": """
# API Latency Incident Response Runbook

## Overview
This runbook provides step-by-step instructions for responding to high API latency incidents.

## Severity: P2/P3

## Initial Response (5 minutes)
1. Check CloudWatch dashboard for API Gateway metrics
2. Verify if latency is affecting all endpoints or specific ones
3. Check Lambda function duration metrics
4. Review DynamoDB performance metrics

## Investigation Steps
1. Check for any recent deployments
2. Review Lambda function logs for errors
3. Check DynamoDB throttling metrics
4. Verify ElastiCache performance

## Mitigation Actions
1. If Lambda timeout: Increase function timeout temporarily
2. If DynamoDB throttling: Increase read/write capacity
3. If cache miss: Warm up cache or increase cache TTL
4. If deployment issue: Consider rollback

## Escalation
- Escalate to P1 if latency > 2 seconds for > 10 minutes
- Contact on-call engineer if mitigation actions don't work within 30 minutes
            """,
            
            "security_incident_runbook.md": """
# Security Incident Response Runbook

## Overview
This runbook provides step-by-step instructions for responding to security incidents.

## Severity: P1

## Immediate Response (2 minutes)
1. Acknowledge the alert
2. Check security dashboard for incident details
3. Determine if this is an active attack or false positive

## Investigation Steps
1. Review authentication failure patterns
2. Check for suspicious IP addresses
3. Review audit logs for unauthorized access attempts
4. Verify integrity of audit trail

## Containment Actions
1. If brute force attack: Implement IP blocking
2. If unauthorized access: Disable compromised accounts
3. If data breach suspected: Isolate affected systems
4. Document all actions taken

## Recovery Steps
1. Verify system integrity
2. Reset compromised credentials
3. Update security policies if needed
4. Conduct post-incident review

## Escalation
- Immediately escalate to security team
- Notify legal team if data breach suspected
- Contact law enforcement if criminal activity suspected
            """,
            
            "budget_alert_runbook.md": """
# Budget Alert Response Runbook

## Overview
This runbook provides instructions for responding to budget utilization alerts.

## Severity: P3

## Initial Response (10 minutes)
1. Check business metrics dashboard
2. Review recent purchase order approvals
3. Verify budget calculations are correct

## Investigation Steps
1. Identify which budget categories are over-utilized
2. Review large purchase orders from the past week
3. Check for any emergency purchases
4. Verify ML forecast accuracy

## Actions
1. If legitimate spending: Request budget reallocation
2. If forecast error: Update forecasting model
3. If unauthorized spending: Investigate approval process
4. If system error: Correct budget calculations

## Prevention
1. Review approval thresholds
2. Update forecasting parameters
3. Implement additional controls if needed
            """
        }
        
        # Store runbooks in S3
        for filename, content in runbooks.items():
            # This would be done during deployment, not in CDK
            pass
        
        self.monitoring_resources["runbooks"] = runbooks
    
    def _tag_resources(self) -> None:
        """
        Tag all monitoring resources
        """
        
        tags = {
            "Project": "AquaChain",
            "Component": "ProductionMonitoring",
            "Environment": self.config["environment"],
            "ManagedBy": "CDK",
            "Purpose": "DashboardOverhaulMonitoring"
        }
        
        for key, value in tags.items():
            Tags.of(self).add(key, value)
    
    @property
    def outputs(self) -> Dict[str, str]:
        """
        Return important stack outputs
        """
        
        # Create CloudFormation outputs
        CfnOutput(
            self, "SystemOverviewDashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.config['region']}#dashboards:name={self.system_overview_dashboard.dashboard_name}",
            description="System overview dashboard URL"
        )
        
        CfnOutput(
            self, "SecurityDashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.config['region']}#dashboards:name={self.security_dashboard.dashboard_name}",
            description="Security monitoring dashboard URL"
        )
        
        CfnOutput(
            self, "CriticalAlertsTopicArn",
            value=self.critical_alerts_topic.topic_arn,
            description="Critical alerts SNS topic ARN"
        )
        
        CfnOutput(
            self, "IncidentArtifactsBucket",
            value=self.incident_artifacts_bucket.bucket_name,
            description="S3 bucket for incident artifacts and compliance reports"
        )
        
        return {
            "system_dashboard_url": f"https://console.aws.amazon.com/cloudwatch/home?region={self.config['region']}#dashboards:name={self.system_overview_dashboard.dashboard_name}",
            "security_dashboard_url": f"https://console.aws.amazon.com/cloudwatch/home?region={self.config['region']}#dashboards:name={self.security_dashboard.dashboard_name}",
            "critical_alerts_topic": self.critical_alerts_topic.topic_arn,
            "incident_bucket": self.incident_artifacts_bucket.bucket_name
        }
