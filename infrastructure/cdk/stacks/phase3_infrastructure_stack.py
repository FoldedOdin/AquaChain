"""
AquaChain Phase 3 Infrastructure Stack
DynamoDB tables and EventBridge schedules for ML monitoring, certificate rotation, and automation
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name


class AquaChainPhase3InfrastructureStack(Stack):
    """
    Phase 3 infrastructure stack containing DynamoDB tables and EventBridge schedules
    for ML monitoring, certificate rotation, and security automation
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.phase3_resources = {}
        
        # Create SNS topic for alerts
        self._create_alert_topic()
        
        # Create DynamoDB tables
        self._create_model_metrics_table()
        self._create_certificate_lifecycle_table()
        self._create_data_validation_table()
        
        # Create EventBridge schedules (placeholders for now, will be connected to Lambda functions later)
        self._create_eventbridge_schedules()
        
        # Create CloudWatch alarms for ML model monitoring
        self._create_ml_monitoring_alarms()
    
    def _create_model_metrics_table(self) -> None:
        """
        Create ModelMetrics DynamoDB table for ML model performance tracking
        
        Schema:
        - model_name (PK): Name of the ML model
        - timestamp (SK): ISO 8601 timestamp of the metric
        - version: Model version
        - accuracy: Model accuracy metric
        - latency_ms: Prediction latency in milliseconds
        - drift_score: Model drift score (0-1)
        - prediction_count: Number of predictions
        - confidence_avg: Average confidence score
        - ttl: Time-to-live for automatic expiration (90 days)
        """
        
        self.model_metrics_table = dynamodb.Table(
            self, "ModelMetricsTable",
            table_name=get_resource_name(self.config, "table", "model-metrics"),
            partition_key=dynamodb.Attribute(
                name="model_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN if self.config.get("enable_deletion_protection", False) else RemovalPolicy.DESTROY,
            point_in_time_recovery=self.config.get("enable_point_in_time_recovery", False),
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # Add GSI for querying by drift_score
        self.model_metrics_table.add_global_secondary_index(
            index_name="DriftScoreIndex",
            partition_key=dynamodb.Attribute(
                name="model_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="drift_score",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.phase3_resources["model_metrics_table"] = self.model_metrics_table
        
        # Output
        CfnOutput(
            self, "ModelMetricsTableName",
            value=self.model_metrics_table.table_name,
            description="DynamoDB table for ML model performance metrics"
        )
        
        CfnOutput(
            self, "ModelMetricsTableArn",
            value=self.model_metrics_table.table_arn,
            description="ARN of ModelMetrics table"
        )

    def _create_certificate_lifecycle_table(self) -> None:
        """
        Create CertificateLifecycle DynamoDB table for IoT device certificate tracking
        
        Schema:
        - device_id (PK): IoT device identifier
        - certificate_id (SK): Certificate identifier
        - expiration_date: Certificate expiration date (ISO 8601)
        - status: Certificate status (active, rotating, deactivated)
        - created_at: Certificate creation timestamp
        - rotated_at: Last rotation timestamp
        - rotation_history: JSON array of rotation events
        """
        
        self.certificate_lifecycle_table = dynamodb.Table(
            self, "CertificateLifecycleTable",
            table_name=get_resource_name(self.config, "table", "certificate-lifecycle"),
            partition_key=dynamodb.Attribute(
                name="device_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="certificate_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN if self.config.get("enable_deletion_protection", False) else RemovalPolicy.DESTROY,
            point_in_time_recovery=self.config.get("enable_point_in_time_recovery", False),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # Add GSI for querying by expiration_date
        self.certificate_lifecycle_table.add_global_secondary_index(
            index_name="ExpirationDateIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="expiration_date",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by status
        self.certificate_lifecycle_table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="device_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.phase3_resources["certificate_lifecycle_table"] = self.certificate_lifecycle_table
        
        # Output
        CfnOutput(
            self, "CertificateLifecycleTableName",
            value=self.certificate_lifecycle_table.table_name,
            description="DynamoDB table for IoT certificate lifecycle management"
        )
        
        CfnOutput(
            self, "CertificateLifecycleTableArn",
            value=self.certificate_lifecycle_table.table_arn,
            description="ARN of CertificateLifecycle table"
        )
    
    def _create_data_validation_table(self) -> None:
        """
        Create DataValidation DynamoDB table for training data validation results
        
        Schema:
        - validation_id (PK): Unique validation identifier
        - timestamp: ISO 8601 timestamp of validation
        - total_rows: Number of rows validated
        - feature_count: Number of features
        - passed: Boolean validation result
        - checks: JSON object with detailed check results
        - errors: List of error messages
        - warnings: List of warning messages
        - recommendations: List of recommendations
        """
        
        self.data_validation_table = dynamodb.Table(
            self, "DataValidationTable",
            table_name=get_resource_name(self.config, "table", "data-validation"),
            partition_key=dynamodb.Attribute(
                name="validation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN if self.config.get("enable_deletion_protection", False) else RemovalPolicy.DESTROY,
            point_in_time_recovery=self.config.get("enable_point_in_time_recovery", False),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # Add GSI for querying by timestamp
        self.data_validation_table.add_global_secondary_index(
            index_name="TimestampIndex",
            partition_key=dynamodb.Attribute(
                name="passed",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.phase3_resources["data_validation_table"] = self.data_validation_table
        
        # Output
        CfnOutput(
            self, "DataValidationTableName",
            value=self.data_validation_table.table_name,
            description="DynamoDB table for training data validation results"
        )
        
        CfnOutput(
            self, "DataValidationTableArn",
            value=self.data_validation_table.table_arn,
            description="ARN of DataValidation table"
        )

    def _create_eventbridge_schedules(self) -> None:
        """
        Create EventBridge schedules for automated tasks
        
        Schedules:
        - Daily: Certificate expiration checks
        - Weekly: Dependency scanning
        - Weekly: SBOM generation
        """
        
        # Daily schedule for certificate expiration checks (runs at 2 AM UTC)
        self.certificate_check_rule = events.Rule(
            self, "CertificateExpirationCheckRule",
            rule_name=get_resource_name(self.config, "rule", "cert-expiration-check"),
            description="Daily check for expiring IoT device certificates",
            schedule=events.Schedule.cron(
                minute="0",
                hour="2",
                month="*",
                week_day="*",
                year="*"
            ),
            enabled=True
        )
        
        # Weekly schedule for dependency scanning (runs every Monday at 3 AM UTC)
        self.dependency_scan_rule = events.Rule(
            self, "DependencyScanRule",
            rule_name=get_resource_name(self.config, "rule", "dependency-scan"),
            description="Weekly dependency vulnerability scanning",
            schedule=events.Schedule.cron(
                minute="0",
                hour="3",
                month="*",
                week_day="MON",
                year="*"
            ),
            enabled=True
        )
        
        # Weekly schedule for SBOM generation (runs every Monday at 4 AM UTC)
        self.sbom_generation_rule = events.Rule(
            self, "SBOMGenerationRule",
            rule_name=get_resource_name(self.config, "rule", "sbom-generation"),
            description="Weekly Software Bill of Materials generation",
            schedule=events.Schedule.cron(
                minute="0",
                hour="4",
                month="*",
                week_day="MON",
                year="*"
            ),
            enabled=True
        )
        
        # Store rules in resources for later Lambda function attachment
        self.phase3_resources.update({
            "certificate_check_rule": self.certificate_check_rule,
            "dependency_scan_rule": self.dependency_scan_rule,
            "sbom_generation_rule": self.sbom_generation_rule
        })
        
        # Outputs
        CfnOutput(
            self, "CertificateCheckRuleName",
            value=self.certificate_check_rule.rule_name,
            description="EventBridge rule for certificate expiration checks"
        )
        
        CfnOutput(
            self, "DependencyScanRuleName",
            value=self.dependency_scan_rule.rule_name,
            description="EventBridge rule for dependency scanning"
        )
        
        CfnOutput(
            self, "SBOMGenerationRuleName",
            value=self.sbom_generation_rule.rule_name,
            description="EventBridge rule for SBOM generation"
        )
    
    def add_certificate_rotation_target(self, lambda_function: lambda_.IFunction) -> None:
        """
        Add Lambda function as target for certificate rotation schedule
        
        Args:
            lambda_function: Lambda function to invoke
        """
        self.certificate_check_rule.add_target(
            targets.LambdaFunction(
                lambda_function,
                retry_attempts=2,
                max_event_age=Duration.hours(2)
            )
        )
    
    def add_dependency_scan_target(self, lambda_function: lambda_.IFunction) -> None:
        """
        Add Lambda function as target for dependency scanning schedule
        
        Args:
            lambda_function: Lambda function to invoke
        """
        self.dependency_scan_rule.add_target(
            targets.LambdaFunction(
                lambda_function,
                retry_attempts=2,
                max_event_age=Duration.hours(4)
            )
        )
    
    def add_sbom_generation_target(self, lambda_function: lambda_.IFunction) -> None:
        """
        Add Lambda function as target for SBOM generation schedule
        
        Args:
            lambda_function: Lambda function to invoke
        """
        self.sbom_generation_rule.add_target(
            targets.LambdaFunction(
                lambda_function,
                retry_attempts=2,
                max_event_age=Duration.hours(4)
            )
        )
    
    def _create_alert_topic(self) -> None:
        """Create SNS topic for Phase 3 alerts"""
        self.alert_topic = sns.Topic(
            self, "Phase3AlertTopic",
            topic_name=get_resource_name(self.config, "topic", "phase3-alerts"),
            display_name="AquaChain Phase 3 Alerts"
        )
        
        self.phase3_resources["alert_topic"] = self.alert_topic
        
        CfnOutput(
            self, "AlertTopicArn",
            value=self.alert_topic.topic_arn,
            description="SNS topic ARN for Phase 3 alerts"
        )
    
    def _create_ml_monitoring_alarms(self) -> None:
        """
        Create CloudWatch alarms for ML model drift detection
        """
        # Alarm for high drift score (> 0.15 for 10 minutes)
        self.drift_alarm = cloudwatch.Alarm(
            self, "ModelDriftAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "model-drift"),
            alarm_description="Alert when ML model drift score exceeds threshold",
            metric=cloudwatch.Metric(
                namespace="AquaChain/ML",
                metric_name="DriftScore",
                dimensions_map={"ModelName": "wqi-model"},
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=0.15,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Add SNS action
        self.drift_alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))
        
        # Alarm for high prediction latency (> 500ms)
        self.latency_alarm = cloudwatch.Alarm(
            self, "PredictionLatencyAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "prediction-latency"),
            alarm_description="Alert when prediction latency exceeds 500ms",
            metric=cloudwatch.Metric(
                namespace="AquaChain/ML",
                metric_name="PredictionLatency",
                dimensions_map={"ModelName": "wqi-model"},
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=500,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        self.latency_alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))
        
        # Alarm for low prediction confidence (< 0.7)
        self.confidence_alarm = cloudwatch.Alarm(
            self, "PredictionConfidenceAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "prediction-confidence"),
            alarm_description="Alert when prediction confidence drops below 0.7",
            metric=cloudwatch.Metric(
                namespace="AquaChain/ML",
                metric_name="PredictionConfidence",
                dimensions_map={"ModelName": "wqi-model"},
                statistic="Average",
                period=Duration.minutes(10)
            ),
            threshold=0.7,
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        self.confidence_alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))
        
        self.phase3_resources.update({
            "drift_alarm": self.drift_alarm,
            "latency_alarm": self.latency_alarm,
            "confidence_alarm": self.confidence_alarm
        })
        
        # Outputs
        CfnOutput(
            self, "DriftAlarmName",
            value=self.drift_alarm.alarm_name,
            description="CloudWatch alarm for model drift detection"
        )
        
        CfnOutput(
            self, "LatencyAlarmName",
            value=self.latency_alarm.alarm_name,
            description="CloudWatch alarm for prediction latency"
        )
        
        CfnOutput(
            self, "ConfidenceAlarmName",
            value=self.confidence_alarm.alarm_name,
            description="CloudWatch alarm for prediction confidence"
        )
