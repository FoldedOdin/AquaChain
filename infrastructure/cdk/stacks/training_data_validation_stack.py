"""
AquaChain Training Data Validation Stack
S3 event triggers and Lambda function for automated training data validation
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_iam as iam,
    aws_sns as sns,
    aws_cloudwatch as cloudwatch,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name


class TrainingDataValidationStack(Stack):
    """
    Stack for training data validation with S3 event triggers
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict[str, Any],
        phase3_stack,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.phase3_stack = phase3_stack
        
        # Create or reference S3 bucket for training data
        self._create_training_data_bucket()
        
        # Create Lambda function for data validation
        self._create_validation_lambda()
        
        # Set up S3 event trigger
        self._setup_s3_event_trigger()
        
        # Create CloudWatch dashboard for validation metrics
        self._create_validation_dashboard()
    
    def _create_training_data_bucket(self) -> None:
        """Create S3 bucket for training data uploads"""
        self.training_data_bucket = s3.Bucket(
            self, "TrainingDataBucket",
            bucket_name=get_resource_name(self.config, "bucket", "ml-training-data"),
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )
        
        CfnOutput(
            self, "TrainingDataBucketName",
            value=self.training_data_bucket.bucket_name,
            description="S3 bucket for ML training data"
        )
    
    def _create_validation_lambda(self) -> None:
        """Create Lambda function for training data validation"""
        
        # Create Lambda execution role
        validation_role = iam.Role(
            self, "ValidationLambdaRole",
            role_name=get_resource_name(self.config, "role", "data-validation-lambda"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant permissions to read from S3
        self.training_data_bucket.grant_read(validation_role)
        
        # Grant permissions to write to DynamoDB validation results table
        validation_table_name = get_resource_name(self.config, "table", "data-validation")
        validation_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{validation_table_name}"
                ]
            )
        )
        
        # Grant permissions to publish to SNS alert topic
        if hasattr(self.phase3_stack, 'alert_topic'):
            self.phase3_stack.alert_topic.grant_publish(validation_role)
        
        # Create Lambda function
        self.validation_lambda = lambda_.Function(
            self, "DataValidationLambda",
            function_name=get_resource_name(self.config, "function", "data-validation"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="training_data_validator.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/ml_training"),
            role=validation_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "VALIDATION_RESULTS_TABLE": validation_table_name,
                "ALERT_TOPIC_ARN": self.phase3_stack.alert_topic.topic_arn if hasattr(self.phase3_stack, 'alert_topic') else "",
                "MIN_CLASS_REPRESENTATION": "0.05",
                "TRAINING_DATA_BUCKET": self.training_data_bucket.bucket_name
            },
            description="Validates training data quality for ML models"
        )
        
        CfnOutput(
            self, "ValidationLambdaArn",
            value=self.validation_lambda.function_arn,
            description="ARN of data validation Lambda function"
        )
    
    def _setup_s3_event_trigger(self) -> None:
        """Configure S3 bucket notification for new training data"""
        
        # Add S3 event notification for new CSV files
        self.training_data_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.validation_lambda),
            s3.NotificationKeyFilter(
                prefix="training-data/",
                suffix=".csv"
            )
        )
        
        # Add S3 event notification for new Parquet files
        self.training_data_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.validation_lambda),
            s3.NotificationKeyFilter(
                prefix="training-data/",
                suffix=".parquet"
            )
        )
        
        CfnOutput(
            self, "S3EventTrigger",
            value="Configured",
            description="S3 event trigger for training data validation"
        )
    
    def _create_validation_dashboard(self) -> None:
        """Create CloudWatch dashboard for validation metrics"""
        
        self.validation_dashboard = cloudwatch.Dashboard(
            self, "ValidationDashboard",
            dashboard_name=get_resource_name(self.config, "dashboard", "data-validation")
        )
        
        # Add widgets for validation metrics
        self.validation_dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Validation Success Rate",
                left=[
                    cloudwatch.Metric(
                        namespace="AquaChain/DataValidation",
                        metric_name="ValidationSuccess",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    ),
                    cloudwatch.Metric(
                        namespace="AquaChain/DataValidation",
                        metric_name="ValidationFailure",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            )
        )
        
        self.validation_dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Execution Metrics",
                left=[
                    self.validation_lambda.metric_invocations(
                        statistic="Sum",
                        period=Duration.minutes(5)
                    ),
                    self.validation_lambda.metric_errors(
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                right=[
                    self.validation_lambda.metric_duration(
                        statistic="Average",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            )
        )
        
        self.validation_dashboard.add_widgets(
            cloudwatch.SingleValueWidget(
                title="Total Validations (24h)",
                metrics=[
                    cloudwatch.Metric(
                        namespace="AquaChain/DataValidation",
                        metric_name="ValidationSuccess",
                        statistic="Sum",
                        period=Duration.hours(24)
                    )
                ],
                width=6
            ),
            cloudwatch.SingleValueWidget(
                title="Failed Validations (24h)",
                metrics=[
                    cloudwatch.Metric(
                        namespace="AquaChain/DataValidation",
                        metric_name="ValidationFailure",
                        statistic="Sum",
                        period=Duration.hours(24)
                    )
                ],
                width=6
            )
        )
        
        CfnOutput(
            self, "ValidationDashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.validation_dashboard.dashboard_name}",
            description="CloudWatch dashboard for data validation metrics"
        )

