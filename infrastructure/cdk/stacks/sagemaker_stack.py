"""
SageMaker Stack for AquaChain ML Infrastructure

This stack creates:
- SageMaker model endpoints for real-time inference
- Model training jobs and pipelines
- S3 buckets for model artifacts
- IAM roles and policies for SageMaker
- CloudWatch monitoring for ML endpoints
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnTag,
    Tags,
    aws_sagemaker as sagemaker,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_logs as logs,
    CfnOutput,
)
from constructs import Construct
from typing import Dict, Any, Optional


class AquaChainSageMakerStack(Stack):
    """Stack for SageMaker ML infrastructure"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict[str, Any],
        alarm_topic: Optional[sns.ITopic] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.config = config
        self.env_name = config["environment"]
        self.alarm_topic = alarm_topic

        # Create S3 bucket for model artifacts
        self._create_model_bucket()
        
        # Create IAM roles for SageMaker
        self._create_sagemaker_roles()
        
        # Create SageMaker model and endpoint
        self._create_sagemaker_model()
        self._create_sagemaker_endpoint()
        
        # Create training job Lambda function
        self.training_lambda = self.create_training_lambda()
        
        # Create monitoring and alarms
        self._create_monitoring()

    def _create_model_bucket(self) -> None:
        """Import existing S3 bucket for storing ML model artifacts"""
        
        bucket_name = f"aquachain-ml-models-{self.env_name}-{self.account}"
        
        # Import existing bucket
        self.model_bucket = s3.Bucket.from_bucket_name(
            self,
            "ModelArtifactsBucket",
            bucket_name=bucket_name
        )

        CfnOutput(
            self,
            "ModelBucketName",
            value=self.model_bucket.bucket_name,
            description="S3 bucket for ML model artifacts",
        )

    def _create_sagemaker_roles(self) -> None:
        """Create IAM roles for SageMaker execution"""
        
        # SageMaker execution role
        self.sagemaker_role = iam.Role(
            self,
            "SageMakerExecutionRole",
            role_name=f"AquaChain-SageMaker-ExecutionRole-{self.env_name}",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
            inline_policies={
                "ModelBucketAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket",
                            ],
                            resources=[
                                self.model_bucket.bucket_arn,
                                f"{self.model_bucket.bucket_arn}/*",
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:DescribeLogStreams",
                            ],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*",
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "cloudwatch:PutMetricData",
                            ],
                            resources=["*"],
                        ),
                    ]
                )
            },
        )

        # Lambda role for invoking SageMaker endpoints
        self.lambda_sagemaker_role = iam.Role(
            self,
            "LambdaSageMakerRole",
            role_name=f"AquaChain-Lambda-SageMaker-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
            inline_policies={
                "SageMakerInvokeEndpoint": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sagemaker:InvokeEndpoint",
                            ],
                            resources=[
                                f"arn:aws:sagemaker:{self.region}:{self.account}:endpoint/aquachain-*",
                            ],
                        ),
                    ]
                )
            },
        )

    def _create_sagemaker_model(self) -> None:
        """Create SageMaker model for water quality inference"""
        
        # XGBoost container image URI (AWS managed) - correct URI for ap-south-1
        container_image_uri = f"720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-xgboost:1.7-1"

        # Create SageMaker model with explicit short name to avoid length limits
        # Note: Model data now points to real trained model
        self.model_name = f"aquachain-wqi-v2-{self.env_name}"
        
        self.sagemaker_model = sagemaker.CfnModel(
            self,
            "WQIModel",
            model_name=self.model_name,  # Use explicit short name
            execution_role_arn=self.sagemaker_role.role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image=container_image_uri,
                # Use the real trained model path
                model_data_url=f"s3://{self.model_bucket.bucket_name}/models/wqi-model/latest/model.tar.gz",
                environment={
                    "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
                    "SAGEMAKER_REGION": self.region,
                },
            ),
            tags=[
                CfnTag(key="Project", value="AquaChain"),
                CfnTag(key="Environment", value=self.env_name),
                CfnTag(key="ModelType", value="WaterQualityIndex"),
            ],
        )

        CfnOutput(
            self,
            "SageMakerModelName",
            value=self.model_name,  # Use the explicit model name
            description="SageMaker model name for WQI inference",
        )

    def _create_sagemaker_endpoint(self) -> None:
        """Create SageMaker endpoint for real-time inference"""
        
        # Use explicit short names to avoid length limits - v2 to allow CloudFormation updates
        self.endpoint_config_name = f"aquachain-wqi-config-v2-{self.env_name}"
        self.endpoint_name = f"aquachain-wqi-endpoint-v2-{self.env_name}"
        
        # Endpoint configuration
        self.endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            "WQIEndpointConfig",
            endpoint_config_name=self.endpoint_config_name,
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    variant_name="primary",
                    model_name=self.model_name,  # Use the explicit model name
                    initial_instance_count=1,
                    instance_type="ml.t2.medium",  # Cost-effective for low traffic
                    initial_variant_weight=1.0,
                )
            ],
            tags=[
                CfnTag(key="Project", value="AquaChain"),
                CfnTag(key="Environment", value=self.env_name),
            ],
        )

        # Create endpoint
        self.endpoint = sagemaker.CfnEndpoint(
            self,
            "WQIEndpoint",
            endpoint_name=self.endpoint_name,
            endpoint_config_name=self.endpoint_config_name,
            tags=[
                CfnTag(key="Project", value="AquaChain"),
                CfnTag(key="Environment", value=self.env_name),
            ],
        )

        # Add dependency
        self.endpoint.add_dependency(self.endpoint_config)
        self.endpoint_config.add_dependency(self.sagemaker_model)

        CfnOutput(
            self,
            "SageMakerEndpointName",
            value=self.endpoint_name,  # Use the explicit endpoint name
            description="SageMaker endpoint name for real-time WQI inference",
        )

    def _create_monitoring(self) -> None:
        """Create CloudWatch monitoring for SageMaker endpoints"""
        
        # Endpoint invocation metrics
        invocation_metric = cloudwatch.Metric(
            namespace="AWS/SageMaker",
            metric_name="Invocations",
            dimensions_map={
                "EndpointName": self.endpoint_name,  # Use the instance variable
                "VariantName": "primary",
            },
            statistic="Sum",
            period=Duration.minutes(5),
        )

        # Model latency metrics
        latency_metric = cloudwatch.Metric(
            namespace="AWS/SageMaker",
            metric_name="ModelLatency",
            dimensions_map={
                "EndpointName": self.endpoint_name,  # Use the instance variable
                "VariantName": "primary",
            },
            statistic="Average",
            period=Duration.minutes(5),
        )

        # Invocation errors
        error_metric = cloudwatch.Metric(
            namespace="AWS/SageMaker",
            metric_name="Invocation4XXErrors",
            dimensions_map={
                "EndpointName": self.endpoint_name,  # Use the instance variable
                "VariantName": "primary",
            },
            statistic="Sum",
            period=Duration.minutes(5),
        )

        # Create alarms
        high_latency_alarm = cloudwatch.Alarm(
            self,
            "HighLatencyAlarm",
            metric=latency_metric,
            threshold=2000,  # 2 seconds
            evaluation_periods=2,
            datapoints_to_alarm=2,
            alarm_description="SageMaker endpoint latency is too high",
            alarm_name=f"AquaChain-SageMaker-HighLatency-{self.env_name}",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        error_rate_alarm = cloudwatch.Alarm(
            self,
            "ErrorRateAlarm",
            metric=error_metric,
            threshold=5,  # 5 errors in 5 minutes
            evaluation_periods=1,
            datapoints_to_alarm=1,
            alarm_description="SageMaker endpoint error rate is too high",
            alarm_name=f"AquaChain-SageMaker-ErrorRate-{self.env_name}",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Add SNS actions if topic provided
        if self.alarm_topic:
            high_latency_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )
            error_rate_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )

        # Create CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(
            self,
            "SageMakerDashboard",
            dashboard_name=f"AquaChain-SageMaker-{self.env_name}",
            widgets=[
                [
                    cloudwatch.GraphWidget(
                        title="SageMaker Endpoint Invocations",
                        left=[invocation_metric],
                        width=12,
                        height=6,
                    ),
                ],
                [
                    cloudwatch.GraphWidget(
                        title="Model Latency",
                        left=[latency_metric],
                        width=12,
                        height=6,
                    ),
                ],
                [
                    cloudwatch.GraphWidget(
                        title="Invocation Errors",
                        left=[error_metric],
                        width=12,
                        height=6,
                    ),
                ],
            ],
        )

    def create_training_lambda(self) -> lambda_.Function:
        """
        Create a Lambda function to trigger SageMaker training jobs programmatically

        Returns:
            Lambda function for training job management
        """

        # Create Lambda function for training job management
        training_lambda = lambda_.Function(
            self,
            "TrainingJobLambda",
            function_name=f"AquaChain-Function-TrainingJob-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/training_job_service"),
            timeout=Duration.minutes(15),
            memory_size=512,
            environment={
                "MODEL_BUCKET": self.model_bucket.bucket_name,
                "SAGEMAKER_ROLE_ARN": self.sagemaker_role.role_arn,
                "ENVIRONMENT": self.env_name,
                "LOG_LEVEL": "INFO",
            },
            layers=[],
        )

        # Grant permissions to create training jobs
        training_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:CreateTrainingJob",
                    "sagemaker:DescribeTrainingJob",
                    "sagemaker:StopTrainingJob",
                    "sagemaker:ListTrainingJobs",
                ],
                resources=[
                    f"arn:aws:sagemaker:{self.region}:{self.account}:training-job/aquachain-*"
                ],
            )
        )

        # Grant S3 permissions
        self.model_bucket.grant_read_write(training_lambda)

        # Add tags
        Tags.of(training_lambda).add("Project", "AquaChain")
        Tags.of(training_lambda).add("Environment", self.env_name)
        Tags.of(training_lambda).add("Service", "TrainingJob")

        return training_lambda
