"""
CDK Stack for Dependency Security Scanner
Includes Lambda function, S3 storage, SNS alerts, EventBridge schedule, and CloudWatch dashboard
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_logs as logs,
)
from constructs import Construct


class DependencyScannerStack(Stack):
    """Stack for automated dependency security scanning"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # S3 bucket for scan results with versioning
        self.results_bucket = s3.Bucket(
            self, "DependencyScanResults",
            bucket_name=f"aquachain-dependency-scans-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldReports",
                    enabled=True,
                    expiration=Duration.days(365),  # Keep reports for 1 year
                    noncurrent_version_expiration=Duration.days(90)
                )
            ],
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # S3 bucket for source code snapshots
        self.source_bucket = s3.Bucket(
            self, "SourceCodeSnapshots",
            bucket_name=f"aquachain-source-snapshots-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldSnapshots",
                    enabled=True,
                    expiration=Duration.days(90),
                    noncurrent_version_expiration=Duration.days(30)
                )
            ],
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # SNS topic for security alerts
        self.alert_topic = sns.Topic(
            self, "DependencyAlertTopic",
            topic_name="aquachain-dependency-alerts",
            display_name="AquaChain Dependency Security Alerts"
        )
        
        # Add email subscription (configure via environment or parameter)
        # self.alert_topic.add_subscription(
        #     sns_subs.EmailSubscription("security@example.com")
        # )
        
        # Lambda function for dependency scanning
        self.scanner_function = lambda_.Function(
            self, "DependencyScannerFunction",
            function_name="aquachain-dependency-scanner",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="dependency_scanner.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/dependency_scanner"),
            timeout=Duration.minutes(15),  # Scanning can take time
            memory_size=1024,
            environment={
                "ALERT_TOPIC_ARN": self.alert_topic.topic_arn,
                "RESULTS_BUCKET": self.results_bucket.bucket_name,
                "SOURCE_BUCKET": self.source_bucket.bucket_name,
                "CRITICAL_THRESHOLD": "0",
                "HIGH_THRESHOLD": "5"
            },
            log_retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Grant permissions
        self.results_bucket.grant_read_write(self.scanner_function)
        self.source_bucket.grant_read(self.scanner_function)
        self.alert_topic.grant_publish(self.scanner_function)
        
        # Grant CloudWatch metrics permissions
        self.scanner_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "AquaChain/Security"
                    }
                }
            )
        )
        
        # EventBridge rule for weekly scanning
        weekly_scan_rule = events.Rule(
            self, "WeeklyScanSchedule",
            rule_name="aquachain-weekly-dependency-scan",
            description="Trigger dependency scan every week",
            schedule=events.Schedule.cron(
                minute="0",
                hour="2",  # 2 AM UTC
                week_day="MON"  # Every Monday
            )
        )
        
        # Add Lambda as target with event payload
        weekly_scan_rule.add_target(
            targets.LambdaFunction(
                self.scanner_function,
                event=events.RuleTargetInput.from_object({
                    "scan_type": "all",
                    "source_paths": {
                        "npm": f"s3://{self.source_bucket.bucket_name}/frontend/package.json",
                        "python": [
                            f"s3://{self.source_bucket.bucket_name}/lambda/requirements.txt",
                            f"s3://{self.source_bucket.bucket_name}/infrastructure/requirements.txt"
                        ]
                    }
                })
            )
        )
        
        # CloudWatch dashboard for vulnerability tracking
        self.dashboard = cloudwatch.Dashboard(
            self, "DependencySecurityDashboard",
            dashboard_name="AquaChain-Dependency-Security"
        )
        
        # Add widgets to dashboard
        self._create_dashboard_widgets()
        
        # CloudWatch alarms
        self._create_alarms()
    
    def _create_dashboard_widgets(self):
        """Create CloudWatch dashboard widgets"""
        
        # Vulnerability count widget
        vuln_widget = cloudwatch.GraphWidget(
            title="Vulnerability Trends",
            left=[
                cloudwatch.Metric(
                    namespace="AquaChain/Security",
                    metric_name="Vulnerabilities_Critical",
                    statistic="Maximum",
                    label="Critical",
                    color=cloudwatch.Color.RED
                ),
                cloudwatch.Metric(
                    namespace="AquaChain/Security",
                    metric_name="Vulnerabilities_High",
                    statistic="Maximum",
                    label="High",
                    color=cloudwatch.Color.ORANGE
                ),
                cloudwatch.Metric(
                    namespace="AquaChain/Security",
                    metric_name="Vulnerabilities_Moderate",
                    statistic="Maximum",
                    label="Moderate",
                    color=cloudwatch.Color.YELLOW
                ),
                cloudwatch.Metric(
                    namespace="AquaChain/Security",
                    metric_name="Vulnerabilities_Low",
                    statistic="Maximum",
                    label="Low",
                    color=cloudwatch.Color.BLUE
                )
            ],
            width=12,
            height=6
        )
        
        # Total vulnerabilities widget
        total_widget = cloudwatch.SingleValueWidget(
            title="Total Vulnerabilities",
            metrics=[
                cloudwatch.Metric(
                    namespace="AquaChain/Security",
                    metric_name="Vulnerabilities_Total",
                    statistic="Maximum"
                )
            ],
            width=6,
            height=6
        )
        
        # Scanner function metrics
        scanner_widget = cloudwatch.GraphWidget(
            title="Scanner Function Performance",
            left=[
                self.scanner_function.metric_invocations(label="Invocations"),
                self.scanner_function.metric_errors(label="Errors", color=cloudwatch.Color.RED)
            ],
            right=[
                self.scanner_function.metric_duration(label="Duration")
            ],
            width=12,
            height=6
        )
        
        # Add widgets to dashboard
        self.dashboard.add_widgets(vuln_widget, total_widget)
        self.dashboard.add_widgets(scanner_widget)
    
    def _create_alarms(self):
        """Create CloudWatch alarms for critical vulnerabilities"""
        
        # Alarm for critical vulnerabilities
        critical_alarm = cloudwatch.Alarm(
            self, "CriticalVulnerabilitiesAlarm",
            alarm_name="aquachain-critical-vulnerabilities",
            alarm_description="Alert when critical vulnerabilities are detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Security",
                metric_name="Vulnerabilities_Critical",
                statistic="Maximum"
            ),
            threshold=0,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        critical_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
        
        # Alarm for high vulnerabilities
        high_alarm = cloudwatch.Alarm(
            self, "HighVulnerabilitiesAlarm",
            alarm_name="aquachain-high-vulnerabilities",
            alarm_description="Alert when more than 5 high vulnerabilities are detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Security",
                metric_name="Vulnerabilities_High",
                statistic="Maximum"
            ),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        high_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
        
        # Alarm for scanner function errors
        error_alarm = cloudwatch.Alarm(
            self, "ScannerErrorAlarm",
            alarm_name="aquachain-dependency-scanner-errors",
            alarm_description="Alert when dependency scanner fails",
            metric=self.scanner_function.metric_errors(),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
