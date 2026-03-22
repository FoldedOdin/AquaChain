"""
AquaChain Compute Stack
Lambda functions, SageMaker resources, and compute infrastructure
"""

import os
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_location as location,
    Duration,
    Size
)
from constructs import Construct
from typing import Dict, Any, Optional
from config.environment_config import get_resource_name

class AquaChainComputeStack(Stack):
    """
    Compute layer stack containing Lambda functions and ML infrastructure
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 data_resources: Dict[str, Any], security_resources: Dict[str, Any],
                 common_layer: Optional[lambda_.ILayerVersion] = None,
                 ml_layer: Optional[lambda_.ILayerVersion] = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.data_resources = data_resources
        self.security_resources = security_resources
        self.common_layer = common_layer
        self.ml_layer = ml_layer
        self.lambda_functions = {}
        self.compute_resources = {}
        
        # Create Lambda functions
        self._create_lambda_functions()
        
        # Create SNS topics for notifications
        self._create_sns_topics()
        
        # Create SageMaker resources (optional - only if model exists)
        if self.config.get("enable_sagemaker", True):  # Enabled by default
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
                "READINGS_TABLE": get_resource_name(self.config, "table", "readings"),
                "LEDGER_TABLE": get_resource_name(self.config, "table", "ledger"),
                "SEQUENCE_TABLE": get_resource_name(self.config, "table", "sequence"),
                "USERS_TABLE": get_resource_name(self.config, "table", "users"),
                "SERVICE_REQUESTS_TABLE": get_resource_name(self.config, "table", "service-requests"),
                "ORDERS_TABLE": "aquachain-orders",
                "DATA_LAKE_BUCKET": get_resource_name(self.config, "bucket", f"data-lake-{self.account}"),
                "AUDIT_BUCKET": get_resource_name(self.config, "bucket", f"audit-trail-{self.account}"),
                "ML_MODELS_BUCKET": get_resource_name(self.config, "bucket", f"ml-models-{self.account}"),
                "DATA_KEY_ID": self.security_resources["data_key"].key_id,
                "SIGNING_KEY_ID": self.security_resources["ledger_signing_key"].key_id,
                "REDIS_ENDPOINT": os.environ.get("REDIS_ENDPOINT", ""),  # Will be set after cache stack deployment
                "WEBSOCKET_CONNECTIONS_TABLE": "AquaChain-WebSocketConnections-dev",
                "WEBSOCKET_ENDPOINT": "https://p2lgfqqy50.execute-api.ap-south-1.amazonaws.com/dev",
                "COGNITO_USER_POOL_ID": os.environ.get("COGNITO_USER_POOL_ID", "ap-south-1_QUDl7hG8u")
            },
            "tracing": lambda_.Tracing.ACTIVE if self.config["enable_xray_tracing"] else lambda_.Tracing.DISABLED,
            "reserved_concurrent_executions": self.config.get("lambda_reserved_concurrency")
        }
        
        # Prepare layers list
        layers = [self.common_layer] if self.common_layer else []
        
        # Data Processing Lambda
        self.data_processing_function = lambda_python.PythonFunction(
            self, "DataProcessingFunction",
            function_name=get_resource_name(self.config, "function", "data-processing"),
            entry="../../lambda/data_processing",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=layers,
            **common_lambda_config
        )
        
        # Grant permissions to DynamoDB tables using IAM policies
        self.data_processing_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem", 
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'readings')}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'ledger')}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'sequence')}"
                ]
            )
        )
        
        # Grant permissions to S3 buckets using IAM policies
        self.data_processing_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                resources=[
                    f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'data-lake-{self.account}')}/*",
                    f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'audit-trail-{self.account}')}/*"
                ]
            )
        )

        # Grant permissions to push WebSocket messages and read connections table
        self.data_processing_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["execute-api:ManageConnections"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:p2lgfqqy50/dev/POST/@connections/*"
                ]
            )
        )
        self.data_processing_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:Query",
                    "dynamodb:DeleteItem"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/AquaChain-WebSocketConnections-dev",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/AquaChain-WebSocketConnections-dev/index/topic-index"
                ]
            )
        )
        
        # ML Inference Lambda (with ML layer)
        ml_layers = [self.common_layer, self.ml_layer] if (self.common_layer and self.ml_layer) else layers
        self.ml_inference_function = lambda_python.PythonFunction(
            self, "MLInferenceFunction",
            function_name=get_resource_name(self.config, "function", "ml-inference"),
            entry="../../lambda/ml_inference",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=ml_layers,
            memory_size=256,
            timeout=Duration.seconds(30),
            **{k: v for k, v in common_lambda_config.items() if k not in ["memory_size", "timeout"]}
        )
        
        # Grant ML models bucket access using IAM policy
        self.ml_inference_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                resources=[f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'ml-models-{self.account}')}/*"]
            )
        )
        
        # Alert Detection Lambda
        self.alert_detection_function = lambda_python.PythonFunction(
            self, "AlertDetectionFunction",
            function_name=get_resource_name(self.config, "function", "alert-detection"),
            entry="../../lambda/alert_detection",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=layers,
            **{k: v for k, v in common_lambda_config.items() if k != "environment"},
            environment={
                **common_lambda_config.get("environment", {}),
                "CRITICAL_ALERTS_TOPIC_ARN": self.security_resources["critical_alerts_topic"].topic_arn,
                "WARNING_ALERTS_TOPIC_ARN": self.security_resources["service_updates_topic"].topic_arn,
                "NOTIFICATION_LAMBDA_NAME": get_resource_name(self.config, "function", "notification"),
            }
        )
        
        # User Management Lambda
        self.user_management_function = lambda_python.PythonFunction(
            self, "UserManagementFunction",
            function_name=get_resource_name(self.config, "function", "user-management"),
            entry="../../lambda/user_management",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=layers,
            **common_lambda_config
        )
        
        # Grant users table access using IAM policy
        self.user_management_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'users')}"]
            )
        )
        
        # Grant SES permissions for sending OTP emails
        self.user_management_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail"
                ],
                resources=["*"]  # SES doesn't support resource-level permissions for SendEmail
            )
        )
        
        # Device Management Lambda (import existing)
        self.device_management_function = lambda_.Function.from_function_name(
            self, "DeviceManagementFunction",
            function_name=get_resource_name(self.config, "function", "device-management")
        )
        
        # Service Request Management Lambda
        self.service_request_function = lambda_python.PythonFunction(
            self, "ServiceRequestFunction",
            function_name=get_resource_name(self.config, "function", "service-request"),
            entry="../../lambda/technician_service",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=layers,
            **{k: v for k, v in common_lambda_config.items() if k != "environment"},
            environment={
                **common_lambda_config.get("environment", {}),
                "NOTIFICATION_TOPIC_ARN": self.security_resources["service_updates_topic"].topic_arn,
            }
        )
        
        # Grant service requests table access using IAM policy
        self.service_request_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'service-requests')}"]
            )
        )
        
        # Grant orders table read access for technician order queries
        self.service_request_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-orders",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-orders/index/*"
                ]
            )
        )
        
        # Audit Trail Processor Lambda
        self.audit_processor_function = lambda_python.PythonFunction(
            self, "AuditProcessorFunction",
            function_name=get_resource_name(self.config, "function", "audit-processor"),
            entry="../../lambda/audit_trail_processor",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=layers,
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
            layers=layers,
            **common_lambda_config
        )
        
        # Grant API Gateway permission to invoke WebSocket Lambda
        # Using resource-based policy to allow API Gateway service to invoke
        self.websocket_function.add_permission(
            "AllowAPIGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:*/*/*"
        )
        
        # Notification Service Lambda — dedicated role with SES + SNS permissions
        notification_role = iam.Role(
            self, "NotificationRole",
            role_name=get_resource_name(self.config, "role", "notification"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess"),
            ],
            description="AquaChain notification service Lambda execution role"
        )

        # SES — send emails (SES does not support resource-level restrictions on SendEmail)
        notification_role.add_to_policy(iam.PolicyStatement(
            sid="SESProduction",
            effect=iam.Effect.ALLOW,
            actions=["ses:SendEmail", "ses:SendRawEmail", "ses:GetSendQuota", "ses:GetSendStatistics"],
            resources=["*"]
        ))

        # SNS — publish to notification topics + direct SMS
        notification_role.add_to_policy(iam.PolicyStatement(
            sid="SNSPublish",
            effect=iam.Effect.ALLOW,
            actions=["sns:Publish", "sns:GetTopicAttributes", "sns:ListSubscriptionsByTopic"],
            resources=[
                self.security_resources["critical_alerts_topic"].topic_arn,
                self.security_resources["service_updates_topic"].topic_arn,
                self.security_resources["system_alerts_topic"].topic_arn,
            ]
        ))

        # SNS — direct SMS (phone number target, no topic ARN)
        notification_role.add_to_policy(iam.PolicyStatement(
            sid="SNSSMSDirect",
            effect=iam.Effect.ALLOW,
            actions=["sns:Publish"],
            resources=["*"],
            conditions={"StringEquals": {"sns:Protocol": "sms"}}
        ))

        # DynamoDB — notification tracking tables
        notification_role.add_to_policy(iam.PolicyStatement(
            sid="DynamoDBNotifications",
            effect=iam.Effect.ALLOW,
            actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem",
                     "dynamodb:Query", "dynamodb:Scan", "dynamodb:DeleteItem"],
            resources=[
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'users')}",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'users')}/index/*",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-notifications",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-notifications/index/*",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-rate-limits",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', 'alerts')}",
            ]
        ))

        notification_env = {
            **common_lambda_config["environment"],
            "USERS_TABLE": get_resource_name(self.config, "table", "users"),
            "NOTIFICATIONS_TABLE": "aquachain-notifications",
            "RATE_LIMIT_TABLE": "aquachain-rate-limits",
            "ALERTS_TABLE": get_resource_name(self.config, "table", "alerts"),
            "SES_FROM_EMAIL": self.config.get("ses_from_email", "alerts@aquachain.io"),
            "SES_CONFIGURATION_SET": "aquachain-notifications",
            "APP_URL": self.config.get("app_url", "https://app.aquachain.io"),
            "CRITICAL_ALERTS_TOPIC_ARN": self.security_resources["critical_alerts_topic"].topic_arn,
            "SERVICE_UPDATES_TOPIC_ARN": self.security_resources["service_updates_topic"].topic_arn,
            "SYSTEM_ALERTS_TOPIC_ARN": self.security_resources["system_alerts_topic"].topic_arn,
        }

        # SNS/multi-channel notification processor (triggered by SNS/EventBridge)
        self.notification_function = lambda_python.PythonFunction(
            self, "NotificationFunction",
            function_name=get_resource_name(self.config, "function", "notification"),
            entry="../../lambda/notification_service",
            index="handler.py",
            handler="lambda_handler",
            role=notification_role,
            layers=layers,
            environment=notification_env,
            **{k: v for k, v in common_lambda_config.items() if k != "environment"}
        )

        # REST API handler for /api/notifications (triggered by API Gateway)
        self.notification_api_function = lambda_python.PythonFunction(
            self, "NotificationApiFunction",
            function_name=get_resource_name(self.config, "function", "notification-api"),
            entry="../../lambda/notification_service",
            index="api_handler.py",
            handler="lambda_handler",
            role=notification_role,
            layers=layers,
            environment=notification_env,
            **{k: v for k, v in common_lambda_config.items() if k != "environment"}
        )
        
        # Admin Service Lambda
        self.admin_service_function = lambda_python.PythonFunction(
            self, "AdminServiceFunction",
            function_name=get_resource_name(self.config, "function", "admin-service"),
            entry="../../lambda/admin_service",
            index="handler.py",
            handler="lambda_handler",
            role=self.security_resources["data_processing_role"],
            layers=layers,
            memory_size=1024,  # Higher memory for admin operations
            timeout=Duration.seconds(60),  # Longer timeout for complex operations
            environment={
                **common_lambda_config["environment"],
                "COGNITO_USER_POOL_ID": os.environ.get("COGNITO_USER_POOL_ID", ""),
                "COGNITO_CLIENT_ID": os.environ.get("COGNITO_CLIENT_ID", ""),
                "CONFIG_TABLE": get_resource_name(self.config, "table", "system-config"),
                "AUDIT_TABLE": get_resource_name(self.config, "table", "audit-logs"),
                "DEVICES_TABLE": get_resource_name(self.config, "table", "devices"),
                "ALERTS_TABLE": get_resource_name(self.config, "table", "alerts"),
                # API Gateway ID will be imported from API stack export after deployment
                # Use Fn.importValue to reference the exported value
                "API_STAGE": self.config["environment"]
            },
            **{k: v for k, v in common_lambda_config.items() if k not in ["memory_size", "timeout", "environment"]}
        )
        
        # API Gateway ID will be added via environment variable update after API stack deployment
        # For now, set a placeholder that will be updated by the API stack
        # This avoids circular dependency issues during initial deployment
        self.admin_service_function.add_environment("API_GATEWAY_ID", "PENDING_API_DEPLOYMENT")
        
        # Grant admin service comprehensive permissions
        self.admin_service_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    # Cognito permissions for user management
                    "cognito-idp:ListUsers",
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminDeleteUser",
                    "cognito-idp:AdminEnableUser",
                    "cognito-idp:AdminDisableUser",
                    "cognito-idp:AdminListGroupsForUser",
                    "cognito-idp:AdminAddUserToGroup",
                    "cognito-idp:AdminRemoveUserFromGroup",
                    # CloudWatch permissions for system health monitoring
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:ListMetrics",
                    # CloudFormation permissions to read exports (for API Gateway ID)
                    "cloudformation:ListExports",
                    # DynamoDB permissions for all admin operations
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    # DynamoDB DescribeTable for health checks (Phase 3c)
                    "dynamodb:DescribeTable",
                    # IoT permissions for health checks (Phase 3c)
                    "iot:DescribeEndpoint"
                ],
                resources=["*"]  # Admin needs broad access
            )
        )
        
        self.lambda_functions.update({
            "data_processing": self.data_processing_function,
            "ml_inference": self.ml_inference_function,
            "alert_detection": self.alert_detection_function,
            "user_management": self.user_management_function,
            "device_management": self.device_management_function,
            "service_request": self.service_request_function,
            "audit_processor": self.audit_processor_function,
            "websocket": self.websocket_function,
            "notification": self.notification_function,
            "notification_api": self.notification_api_function,
            "admin_service": self.admin_service_function
        })
        
        # Also add to compute_resources for API stack compatibility
        self.compute_resources.update(self.lambda_functions)
    
    def _create_sns_topics(self) -> None:
        """
        Create SNS topics for notifications
        """
        
        # Use critical alerts topic from security stack
        self.critical_alerts_topic = self.security_resources["critical_alerts_topic"]
        
        # Use service updates topic from security stack
        self.service_updates_topic = self.security_resources["service_updates_topic"]
        
        # Use system alerts topic from security stack
        self.system_alerts_topic = self.security_resources["system_alerts_topic"]
        
        # Permissions for SNS publish and Lambda invoke are granted via data_processing_role
        # in security_stack.py using wildcard ARN patterns (aquachain-*) to avoid cross-stack
        # cyclic references. Any add_to_role_policy on functions using data_processing_role
        # would modify DataProcessingRole/DefaultPolicy in Security stack, and if those
        # statements reference Compute-stack ARNs (like notification_function.function_arn),
        # CDK creates a Security→Compute dependency that cycles back.
        
        # Subscribe notification Lambda to service_updates_topic.
        # Use Topic.from_topic_arn to avoid cross-stack object reference — this creates
        # a local proxy that doesn't add a resource policy on the Security-stack topic.
        local_service_updates_topic = sns.Topic.from_topic_arn(
            self, "ServiceUpdatesTopicRef",
            self.service_updates_topic.topic_arn
        )
        local_service_updates_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(self.notification_function)
        )
        
        # SNS publish for data_processing_function granted via data_processing_role in security_stack
        
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
                # SageMaker SKLearn inference container for ap-south-1 (Mumbai)
                image="720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3",
                model_data_url=f"s3://{get_resource_name(self.config, 'bucket', f'ml-models-{self.account}')}/models/wqi-model.tar.gz",
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
        
        # Use location services from security stack
        self.location_map = self.security_resources["location_map"]
        self.route_calculator = self.security_resources["route_calculator"]
        
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