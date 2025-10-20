"""
AquaChain Compute Stack
Lambda functions, SageMaker resources, and compute infrastructure
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_sns as sns,
    aws_location as location,
    Duration,
    Size
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class AquaChainComputeStack(Stack):
    """
    Compute layer stack containing Lambda functions and ML infrastructure
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 data_resources: Dict[str, Any], security_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.data_resources = data_resources
        self.security_resources = security_resources
        self.lambda_functions = {}
        self.compute_resources = {}
        
        # Create Lambda functions
        self._create_lambda_functions()
        
        # Create SNS topics for notifications
        self._create_sns_topics()
        
        # Create SageMaker resources
        self._create_sagemaker_resources()
        
        # Create Location Service resources
        self._create_location_resources()
    
    def _create_lambda_functions(self) -> None:
        """
        Create Lambda functions for data processing and business logic
        """
        
        # Common Lambda configuration
        common_lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_11,
            "timeout": Duration.seconds(30),
            "memory_size": 512,
            "environment": {
                "ENVIRONMENT": self.config["environment"],
                "REGION": self.region,
                "READINGS_TABLE": self.data_resources["readings_table"].table_name,
                "LEDGER_TABLE": self.data_resources["ledger_table"].table_name,
                "SEQUENCE_TABLE": self.data_resources["sequence_table"].table_name,
                "USERS_TABLE": self.data_resources["users_table"].table_name,
                "SERVICE_REQUESTS_TABLE": self.data_resources["service_requests_table"].table_name,
                "DATA_LAKE_BUCKET": self.data_resources["data_lake_bucket"].bucket_name,
                "AUDIT_BUCKET": self.data_resources["audit_bucket"].bucket_name,
                "ML_MODELS_BUCKET": self.data_resources["ml_models_bucket"].bucket_name,
                "DATA_KEY_ID": self.security_resources["data_key"].key_id,
                "SIGNING_KEY_ID": self.security_resources["ledger_signing_key"].key_id
            },
            "tracing": lambda_.Tracing.ACTIVE if self.config["enable_xray_tracing"] else lambda_.Tracing.DISABLED,
            "reserved_concurrent_executions": self.config.get("lambda_reserved_concurrency")
        }
        
        # Data Processing Lambda
        self.data_processing_function = lambda_python.PythonFunction(
            self, "DataProcessingFunction",
            function_name=get_resource_name(self.config, "function", "data-processing"),
            entry="../../lambda/data_processing",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        # Grant permissions to DynamoDB tables
        self.data_resources["readings_table"].grant_read_write_data(self.data_processing_function)
        self.data_resources["ledger_table"].grant_read_write_data(self.data_processing_function)
        self.data_resources["sequence_table"].grant_read_write_data(self.data_processing_function)
        
        # Grant permissions to S3 buckets
        self.data_resources["data_lake_bucket"].grant_read_write(self.data_processing_function)
        self.data_resources["audit_bucket"].grant_read_write(self.data_processing_function)
        
        # ML Inference Lambda
        self.ml_inference_function = lambda_python.PythonFunction(
            self, "MLInferenceFunction",
            function_name=get_resource_name(self.config, "function", "ml-inference"),
            entry="../../lambda/ml_inference",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            memory_size=1024,
            timeout=Duration.seconds(15),
            **{k: v for k, v in common_lambda_config.items() if k not in ["memory_size", "timeout"]}
        )
        
        # Grant ML models bucket access
        self.data_resources["ml_models_bucket"].grant_read(self.ml_inference_function)
        
        # Alert Detection Lambda
        self.alert_detection_function = lambda_python.PythonFunction(
            self, "AlertDetectionFunction",
            function_name=get_resource_name(self.config, "function", "alert-detection"),
            entry="../../lambda/alert_detection",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        # User Management Lambda
        self.user_management_function = lambda_python.PythonFunction(
            self, "UserManagementFunction",
            function_name=get_resource_name(self.config, "function", "user-management"),
            entry="../../lambda/user_management",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        # Grant users table access
        self.data_resources["users_table"].grant_read_write_data(self.user_management_function)
        
        # Service Request Management Lambda
        self.service_request_function = lambda_python.PythonFunction(
            self, "ServiceRequestFunction",
            function_name=get_resource_name(self.config, "function", "service-request"),
            entry="../../lambda/technician_service",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        # Grant service requests table access
        self.data_resources["service_requests_table"].grant_read_write_data(self.service_request_function)
        
        # Audit Trail Processor Lambda
        self.audit_processor_function = lambda_python.PythonFunction(
            self, "AuditProcessorFunction",
            function_name=get_resource_name(self.config, "function", "audit-processor"),
            entry="../../lambda/audit_trail_processor",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        # WebSocket API Lambda
        self.websocket_function = lambda_python.PythonFunction(
            self, "WebSocketFunction",
            function_name=get_resource_name(self.config, "function", "websocket"),
            entry="../../lambda/websocket_api",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        # Notification Service Lambda
        self.notification_function = lambda_python.PythonFunction(
            self, "NotificationFunction",
            function_name=get_resource_name(self.config, "function", "notification"),
            entry="../../lambda/notification_service",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            **common_lambda_config
        )
        
        self.lambda_functions.update({
            "data_processing": self.data_processing_function,
            "ml_inference": self.ml_inference_function,
            "alert_detection": self.alert_detection_function,
            "user_management": self.user_management_function,
            "service_request": self.service_request_function,
            "audit_processor": self.audit_processor_function,
            "websocket": self.websocket_function,
            "notification": self.notification_function
        })
    
    def _create_sns_topics(self) -> None:
        """
        Create SNS topics for notifications
        """
        
        # Critical alerts topic
        self.critical_alerts_topic = sns.Topic(
            self, "CriticalAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "critical-alerts"),
            display_name="AquaChain Critical Water Quality Alerts"
        )
        
        # Service updates topic
        self.service_updates_topic = sns.Topic(
            self, "ServiceUpdatesTopic",
            topic_name=get_resource_name(self.config, "topic", "service-updates"),
            display_name="AquaChain Service Request Updates"
        )
        
        # System alerts topic
        self.system_alerts_topic = sns.Topic(
            self, "SystemAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "system-alerts"),
            display_name="AquaChain System Alerts"
        )
        
        # Grant publish permissions to Lambda functions
        self.critical_alerts_topic.grant_publish(self.alert_detection_function)
        self.critical_alerts_topic.grant_publish(self.notification_function)
        
        self.service_updates_topic.grant_publish(self.service_request_function)
        self.service_updates_topic.grant_publish(self.notification_function)
        
        self.system_alerts_topic.grant_publish(self.data_processing_function)
        
        self.compute_resources.update({
            "critical_alerts_topic": self.critical_alerts_topic,
            "service_updates_topic": self.service_updates_topic,
            "system_alerts_topic": self.system_alerts_topic
        })
    
    def _create_sagemaker_resources(self) -> None:
        """
        Create SageMaker resources for ML model training and deployment
        """
        
        # SageMaker Model for WQI calculation
        self.wqi_model = sagemaker.CfnModel(
            self, "WQIModel",
            model_name=get_resource_name(self.config, "model", "wqi-calculator"),
            execution_role_arn=self.security_resources["sagemaker_role"].role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image="382416733822.dkr.ecr.us-east-1.amazonaws.com/sklearn_inference:0.23-1-cpu-py3",
                model_data_url=f"s3://{self.data_resources['ml_models_bucket'].bucket_name}/models/wqi-model.tar.gz",
                environment={
                    "SAGEMAKER_PROGRAM": "inference.py",
                    "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/code"
                }
            )
        )
        
        # SageMaker Endpoint Configuration
        self.wqi_endpoint_config = sagemaker.CfnEndpointConfig(
            self, "WQIEndpointConfig",
            endpoint_config_name=get_resource_name(self.config, "endpoint-config", "wqi"),
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    variant_name="primary",
                    model_name=self.wqi_model.model_name,
                    initial_instance_count=1,
                    instance_type=self.config["ml_model_config"]["instance_type"],
                    initial_variant_weight=1.0
                )
            ]
        )
        
        # SageMaker Endpoint
        self.wqi_endpoint = sagemaker.CfnEndpoint(
            self, "WQIEndpoint",
            endpoint_name=get_resource_name(self.config, "endpoint", "wqi"),
            endpoint_config_name=self.wqi_endpoint_config.endpoint_config_name
        )
        
        # Add dependencies
        self.wqi_endpoint_config.add_dependency(self.wqi_model)
        self.wqi_endpoint.add_dependency(self.wqi_endpoint_config)
        
        self.compute_resources.update({
            "wqi_model": self.wqi_model,
            "wqi_endpoint_config": self.wqi_endpoint_config,
            "wqi_endpoint": self.wqi_endpoint
        })
    
    def _create_location_resources(self) -> None:
        """
        Create AWS Location Service resources for routing and ETA calculation
        """
        
        # Location Service Map
        self.location_map = location.CfnMap(
            self, "LocationMap",
            map_name=get_resource_name(self.config, "map", "service-areas"),
            configuration=location.CfnMap.MapConfigurationProperty(
                style="VectorEsriStreets"
            ),
            description="Map for AquaChain service area routing",
            pricing_plan="RequestBasedUsage"
        )
        
        # Location Service Route Calculator
        self.route_calculator = location.CfnRouteCalculator(
            self, "RouteCalculator",
            calculator_name=get_resource_name(self.config, "route-calc", "service-routing"),
            data_source="Esri",
            description="Route calculator for technician ETA calculation",
            pricing_plan="RequestBasedUsage"
        )
        
        # Grant Location Service permissions to service request Lambda
        self.service_request_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "geo:CalculateRoute",
                    "geo:GetMap*"
                ],
                resources=[
                    self.location_map.attr_arn,
                    self.route_calculator.attr_arn
                ]
            )
        )
        
        self.compute_resources.update({
            "location_map": self.location_map,
            "route_calculator": self.route_calculator
        })