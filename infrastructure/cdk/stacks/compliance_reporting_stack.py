"""
AquaChain Compliance Reporting Stack
S3 bucket for compliance reports with encryption and lifecycle policies
"""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_kms as kms,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
import os


class ComplianceReportingStack(Stack):
    """
    Stack for compliance reporting infrastructure
    Includes S3 bucket for storing monthly compliance reports
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict[str, Any],
        kms_key: kms.Key,
        audit_logs_table: dynamodb.Table,
        gdpr_requests_table: dynamodb.Table,
        devices_table: dynamodb.Table,
        users_table: dynamodb.Table,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.kms_key = kms_key
        self.audit_logs_table = audit_logs_table
        self.gdpr_requests_table = gdpr_requests_table
        self.devices_table = devices_table
        self.users_table = users_table
        
        # Create S3 bucket for compliance reports
        self._create_compliance_reports_bucket()
        
        # Create SNS topic for compliance alerts
        self._create_compliance_alerts_topic()
        
        # Create Lambda function for report generation
        self._create_report_generator_lambda()
        
        # Create EventBridge schedule for monthly reports
        self._create_monthly_schedule()
        
        # Create CloudWatch alarms for compliance violations
        self._create_compliance_alarms()
    
    def _create_compliance_reports_bucket(self) -> None:
        """
        Create S3 bucket for compliance report storage with encryption and lifecycle policies
        """
        from config.environment_config import get_resource_name
        
        # Create bucket with encryption and versioning
        self.compliance_reports_bucket = s3.Bucket(
            self,
            "ComplianceReportsBucket",
            bucket_name=get_resource_name(
                self.config,
                "bucket",
                f"compliance-reports-{self.account}"
            ),
            # Encryption with KMS
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            # Enable versioning for audit trail
            versioned=True,
            # Block all public access
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            # Retain compliance reports
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            # Lifecycle rules for long-term retention and cost optimization
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        )
                    ],
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="TransitionToGlacier",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ],
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="TransitionToDeepArchive",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(1825)  # 5 years
                        )
                    ],
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(365)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="ExpireOldVersions",
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(2555)  # 7 years
                )
            ]
        )
        
        # Add bucket policy to enforce encryption
        self.compliance_reports_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyUnencryptedObjectUploads",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:PutObject"],
                resources=[f"{self.compliance_reports_bucket.bucket_arn}/*"],
                conditions={
                    "StringNotEquals": {
                        "s3:x-amz-server-side-encryption": "aws:kms"
                    }
                }
            )
        )
        
        # Add bucket policy to enforce secure transport
        self.compliance_reports_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyInsecureTransport",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[
                    self.compliance_reports_bucket.bucket_arn,
                    f"{self.compliance_reports_bucket.bucket_arn}/*"
                ],
                conditions={
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            )
        )
    
    def _create_compliance_alerts_topic(self) -> None:
        """
        Create SNS topic for compliance violation alerts
        """
        from config.environment_config import get_resource_name
        
        # Create SNS topic
        self.compliance_alerts_topic = sns.Topic(
            self,
            "ComplianceAlertsTopic",
            topic_name=get_resource_name(
                self.config,
                "topic",
                "compliance-alerts"
            ),
            display_name="AquaChain Compliance Alerts",
            master_key=self.kms_key
        )
        
        # Add email subscription (configure via environment or parameter)
        compliance_email = self.config.get('compliance_email', 'compliance@aquachain.com')
        self.compliance_alerts_topic.add_subscription(
            subscriptions.EmailSubscription(compliance_email)
        )
    
    def _create_report_generator_lambda(self) -> None:
        """
        Create Lambda function for generating compliance reports
        """
        from config.environment_config import get_resource_name
        
        # Create Lambda execution role
        lambda_role = iam.Role(
            self,
            "ReportGeneratorRole",
            role_name=get_resource_name(self.config, "role", "compliance-report-generator"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant permissions to read from DynamoDB tables
        self.audit_logs_table.grant_read_data(lambda_role)
        self.gdpr_requests_table.grant_read_data(lambda_role)
        self.devices_table.grant_read_data(lambda_role)
        self.users_table.grant_read_data(lambda_role)
        
        # Grant permissions to write to S3 bucket
        self.compliance_reports_bucket.grant_write(lambda_role)
        
        # Grant KMS permissions
        self.kms_key.grant_encrypt_decrypt(lambda_role)
        
        # Grant SNS publish permissions
        self.compliance_alerts_topic.grant_publish(lambda_role)
        
        # Grant CloudWatch metrics permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )
        
        # Get Lambda code path
        lambda_code_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "lambda",
            "compliance_service"
        )
        
        # Create Lambda function
        self.report_generator_function = lambda_.Function(
            self,
            "ReportGeneratorFunction",
            function_name=get_resource_name(
                self.config,
                "function",
                "compliance-report-generator"
            ),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="scheduled_report_handler.lambda_handler",
            code=lambda_.Code.from_asset(lambda_code_path),
            role=lambda_role,
            timeout=Duration.minutes(15),
            memory_size=512,
            environment={
                "COMPLIANCE_REPORTS_BUCKET": self.compliance_reports_bucket.bucket_name,
                "AUDIT_LOGS_TABLE": self.audit_logs_table.table_name,
                "GDPR_REQUESTS_TABLE": self.gdpr_requests_table.table_name,
                "DEVICES_TABLE": self.devices_table.table_name,
                "USERS_TABLE": self.users_table.table_name,
                "COMPLIANCE_ALERTS_TOPIC_ARN": self.compliance_alerts_topic.topic_arn
            },
            description="Generate monthly compliance reports"
        )
    
    def _create_monthly_schedule(self) -> None:
        """
        Create EventBridge rule to trigger report generation monthly
        """
        from config.environment_config import get_resource_name
        
        # Create EventBridge rule for monthly execution
        # Runs on the 1st day of each month at 2:00 AM UTC
        self.monthly_rule = events.Rule(
            self,
            "MonthlyReportRule",
            rule_name=get_resource_name(
                self.config,
                "rule",
                "compliance-monthly-report"
            ),
            description="Trigger monthly compliance report generation",
            schedule=events.Schedule.cron(
                minute="0",
                hour="2",
                day="1",
                month="*",
                year="*"
            ),
            enabled=True
        )
        
        # Add Lambda function as target
        self.monthly_rule.add_target(
            targets.LambdaFunction(self.report_generator_function)
        )
    
    def _create_compliance_alarms(self) -> None:
        """
        Create CloudWatch alarms for compliance violations
        """
        from config.environment_config import get_resource_name
        
        # Alarm for any compliance violations
        self.violations_alarm = cloudwatch.Alarm(
            self,
            "ComplianceViolationsAlarm",
            alarm_name=get_resource_name(
                self.config,
                "alarm",
                "compliance-violations"
            ),
            alarm_description="Alert when compliance violations are detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Compliance",
                metric_name="ComplianceViolations",
                statistic="Sum",
                period=Duration.minutes(15)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Add SNS action to alarm
        self.violations_alarm.add_alarm_action(
            cw_actions.SnsAction(self.compliance_alerts_topic)
        )
        
        # Alarm for high severity violations
        self.high_severity_alarm = cloudwatch.Alarm(
            self,
            "HighSeverityViolationsAlarm",
            alarm_name=get_resource_name(
                self.config,
                "alarm",
                "compliance-high-severity"
            ),
            alarm_description="Alert when high severity compliance violations are detected",
            metric=cloudwatch.Metric(
                namespace="AquaChain/Compliance",
                metric_name="ComplianceViolations",
                dimensions_map={"Severity": "HIGH"},
                statistic="Sum",
                period=Duration.minutes(15)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Add SNS action to high severity alarm
        self.high_severity_alarm.add_alarm_action(
            cw_actions.SnsAction(self.compliance_alerts_topic)
        )
    
    @property
    def outputs(self) -> Dict[str, Any]:
        """
        Return stack outputs
        """
        # Create CloudFormation outputs
        CfnOutput(
            self,
            "ComplianceReportsBucketName",
            value=self.compliance_reports_bucket.bucket_name,
            description="S3 bucket for compliance reports with encryption and lifecycle policies"
        )
        
        CfnOutput(
            self,
            "ComplianceReportsBucketArn",
            value=self.compliance_reports_bucket.bucket_arn,
            description="ARN of compliance reports S3 bucket"
        )
        
        CfnOutput(
            self,
            "ReportGeneratorFunctionName",
            value=self.report_generator_function.function_name,
            description="Lambda function for generating compliance reports"
        )
        
        CfnOutput(
            self,
            "ReportGeneratorFunctionArn",
            value=self.report_generator_function.function_arn,
            description="ARN of compliance report generator Lambda function"
        )
        
        CfnOutput(
            self,
            "MonthlyReportSchedule",
            value=self.monthly_rule.rule_name,
            description="EventBridge rule for monthly report generation"
        )
        
        CfnOutput(
            self,
            "ComplianceAlertsTopicArn",
            value=self.compliance_alerts_topic.topic_arn,
            description="SNS topic for compliance violation alerts"
        )
        
        CfnOutput(
            self,
            "ComplianceViolationsAlarmName",
            value=self.violations_alarm.alarm_name,
            description="CloudWatch alarm for compliance violations"
        )
        
        return {
            "compliance_reports_bucket": self.compliance_reports_bucket,
            "report_generator_function": self.report_generator_function,
            "monthly_rule": self.monthly_rule,
            "compliance_alerts_topic": self.compliance_alerts_topic,
            "violations_alarm": self.violations_alarm,
            "high_severity_alarm": self.high_severity_alarm
        }
