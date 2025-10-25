"""
Lambda Performance Stack for AquaChain

This stack optimizes Lambda function performance through:
- Provisioned concurrency for high-traffic functions
- Optimized memory allocation
- Cold start monitoring
- Lambda layers for shared dependencies
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    CfnOutput,
)
from constructs import Construct
from typing import Optional


class LambdaPerformanceStack(Stack):
    """Stack for Lambda performance optimizations"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        common_layer: lambda_.ILayerVersion,
        ml_layer: lambda_.ILayerVersion,
        alarm_topic: Optional[sns.ITopic] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.common_layer = common_layer
        self.ml_layer = ml_layer
        self.alarm_topic = alarm_topic

        # Create optimized Lambda functions
        self._create_data_processing_function()
        self._create_ml_inference_function()
        self._create_cold_start_monitoring()

    def _create_data_processing_function(self) -> None:
        """Create data processing Lambda with provisioned concurrency"""

        # Data processing function with optimized settings
        self.data_processing_fn = lambda_.Function(
            self,
            "DataProcessingOptimized",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/data_processing"),
            layers=[self.common_layer],
            memory_size=1024,  # Optimized based on profiling
            timeout=Duration.seconds(30),
            reserved_concurrent_executions=100,
            environment={
                "POWERTOOLS_SERVICE_NAME": "data-processing",
                "LOG_LEVEL": "INFO",
                "ENABLE_XRAY": "true",
            },
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Create version for provisioned concurrency
        version = self.data_processing_fn.current_version

        # Create alias pointing to version
        alias = lambda_.Alias(
            self,
            "DataProcessingAlias",
            alias_name="live",
            version=version,
        )

        # Configure auto-scaling for provisioned concurrency
        auto_scaling = alias.add_auto_scaling(
            max_capacity=50,
            min_capacity=5,  # Always keep 5 warm instances
        )

        # Scale based on utilization (70% target)
        auto_scaling.scale_on_utilization(utilization_target=0.7)

        # Output alias ARN
        CfnOutput(
            self,
            "DataProcessingAliasArn",
            value=alias.function_arn,
            description="ARN of data processing function alias with provisioned concurrency",
        )

    def _create_ml_inference_function(self) -> None:
        """Create ML inference Lambda with provisioned concurrency"""

        # ML inference function with optimized settings
        self.ml_inference_fn = lambda_.Function(
            self,
            "MLInferenceOptimized",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/ml_inference"),
            layers=[self.common_layer, self.ml_layer],
            memory_size=2048,  # Higher memory for ML workloads
            timeout=Duration.seconds(60),
            reserved_concurrent_executions=50,
            environment={
                "POWERTOOLS_SERVICE_NAME": "ml-inference",
                "LOG_LEVEL": "INFO",
                "ENABLE_XRAY": "true",
            },
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Create version for provisioned concurrency
        version = self.ml_inference_fn.current_version

        # Create alias pointing to version
        alias = lambda_.Alias(
            self,
            "MLInferenceAlias",
            alias_name="live",
            version=version,
        )

        # Configure auto-scaling for provisioned concurrency
        auto_scaling = alias.add_auto_scaling(
            max_capacity=30,
            min_capacity=3,  # Always keep 3 warm instances
        )

        # Scale based on utilization (70% target)
        auto_scaling.scale_on_utilization(utilization_target=0.7)

        # Output alias ARN
        CfnOutput(
            self,
            "MLInferenceAliasArn",
            value=alias.function_arn,
            description="ARN of ML inference function alias with provisioned concurrency",
        )

    def _create_cold_start_monitoring(self) -> None:
        """Create CloudWatch alarms for cold start monitoring"""

        # Cold start alarm for data processing
        data_processing_cold_start_alarm = cloudwatch.Alarm(
            self,
            "DataProcessingColdStartAlarm",
            metric=self.data_processing_fn.metric_duration(
                statistic="Maximum",
                period=Duration.minutes(5),
            ),
            threshold=2000,  # 2 seconds in milliseconds
            evaluation_periods=2,
            datapoints_to_alarm=2,
            alarm_description="Alert when data processing Lambda cold start exceeds 2 seconds",
            alarm_name=f"{self.stack_name}-DataProcessing-ColdStart",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Cold start alarm for ML inference
        ml_inference_cold_start_alarm = cloudwatch.Alarm(
            self,
            "MLInferenceColdStartAlarm",
            metric=self.ml_inference_fn.metric_duration(
                statistic="Maximum",
                period=Duration.minutes(5),
            ),
            threshold=2000,  # 2 seconds in milliseconds
            evaluation_periods=2,
            datapoints_to_alarm=2,
            alarm_description="Alert when ML inference Lambda cold start exceeds 2 seconds",
            alarm_name=f"{self.stack_name}-MLInference-ColdStart",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # Add SNS action if topic provided
        if self.alarm_topic:
            data_processing_cold_start_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )
            ml_inference_cold_start_alarm.add_alarm_action(
                cw_actions.SnsAction(self.alarm_topic)
            )

        # Create custom metric filter for cold start detection
        self._create_cold_start_metric_filter(
            self.data_processing_fn, "DataProcessing"
        )
        self._create_cold_start_metric_filter(self.ml_inference_fn, "MLInference")

    def _create_cold_start_metric_filter(
        self, function: lambda_.Function, function_name: str
    ) -> None:
        """Create metric filter to detect cold starts from logs"""

        # Metric filter to detect cold starts
        logs.MetricFilter(
            self,
            f"{function_name}ColdStartFilter",
            log_group=function.log_group,
            metric_namespace="AquaChain/Lambda",
            metric_name=f"{function_name}ColdStarts",
            filter_pattern=logs.FilterPattern.literal("REPORT RequestId"),
            metric_value="1",
            default_value=0,
        )

        # Metric filter for init duration (cold start indicator)
        logs.MetricFilter(
            self,
            f"{function_name}InitDurationFilter",
            log_group=function.log_group,
            metric_namespace="AquaChain/Lambda",
            metric_name=f"{function_name}InitDuration",
            filter_pattern=logs.FilterPattern.literal("Init Duration"),
            metric_value="$init_duration",
            default_value=0,
        )

    def create_optimized_function(
        self,
        function_id: str,
        handler_path: str,
        memory_size: int = 512,
        timeout_seconds: int = 30,
        use_ml_layer: bool = False,
        environment: Optional[dict] = None,
    ) -> lambda_.Function:
        """
        Helper method to create an optimized Lambda function with layers

        Args:
            function_id: CDK construct ID
            handler_path: Path to Lambda handler code
            memory_size: Memory allocation in MB
            timeout_seconds: Function timeout in seconds
            use_ml_layer: Whether to include ML layer
            environment: Environment variables

        Returns:
            Configured Lambda function
        """
        layers = [self.common_layer]
        if use_ml_layer:
            layers.append(self.ml_layer)

        env_vars = environment or {}
        env_vars.update(
            {
                "LOG_LEVEL": "INFO",
                "ENABLE_XRAY": "true",
            }
        )

        return lambda_.Function(
            self,
            function_id,
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(handler_path),
            layers=layers,
            memory_size=memory_size,
            timeout=Duration.seconds(timeout_seconds),
            environment=env_vars,
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
