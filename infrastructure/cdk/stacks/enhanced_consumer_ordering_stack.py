"""
Enhanced Consumer Ordering System Stack
DynamoDB tables, Lambda functions, EventBridge rules, and WebSocket API for the ordering system
"""

from aws_cdk import (
    Stack,
    Tags,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_apigatewayv2 as apigatewayv2,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from aws_cdk.aws_apigatewayv2_integrations import WebSocketLambdaIntegration
from constructs import Construct
from typing import Dict, Any, Optional
from config.environment_config import get_resource_name

class EnhancedConsumerOrderingStack(Stack):
    """
    Enhanced Consumer Ordering System infrastructure stack
    Contains DynamoDB tables, EventBridge rules, and WebSocket API
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], 
                 kms_key: kms.Key, common_layer: Optional[lambda_.ILayerVersion] = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.kms_key = kms_key
        self.common_layer = common_layer
        self.ordering_resources = {}
        self.lambda_functions = {}
        
        # Create DynamoDB tables
        self._create_dynamodb_tables()
        
        # Create Secrets Manager secrets
        self._create_secrets()
        
        # Create Lambda functions
        self._create_lambda_functions()
        
        # Create EventBridge resources
        self._create_eventbridge_resources()
        
        # Create WebSocket API
        self._create_websocket_api()
    
    def _create_dynamodb_tables(self) -> None:
        """
        Create DynamoDB tables for the enhanced consumer ordering system
        """
        
        # Orders table with GSIs for consumer and status queries
        self.orders_table = dynamodb.Table(
            self, "OrdersTable",
            table_name=get_resource_name(self.config, "table", "orders"),
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute="ttl"
        )
        
        # GSI1: Consumer Orders Index
        self.orders_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI2: Status Index
        self.orders_table.add_global_secondary_index(
            index_name="GSI2",
            partition_key=dynamodb.Attribute(
                name="GSI2PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI2SK",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Payments table with GSI for order payments lookup
        self.payments_table = dynamodb.Table(
            self, "PaymentsTable",
            table_name=get_resource_name(self.config, "table", "payments"),
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI1: Order Payments Index
        self.payments_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Technicians table with GSI for location-based queries
        self.technicians_table = dynamodb.Table(
            self, "TechniciansTable",
            table_name=get_resource_name(self.config, "table", "technicians"),
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI1: Location Index
        self.technicians_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Order Status Simulation table for demo purposes
        self.order_simulations_table = dynamodb.Table(
            self, "OrderSimulationsTable",
            table_name=get_resource_name(self.config, "table", "order-simulations"),
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,  # Demo data can be destroyed
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute="ttl"
        )
        
        self.ordering_resources.update({
            "orders_table": self.orders_table,
            "payments_table": self.payments_table,
            "technicians_table": self.technicians_table,
            "order_simulations_table": self.order_simulations_table
        })
        
        # Tag all tables for AWS Backup and feature identification
        for table in [self.orders_table, self.payments_table, self.technicians_table, self.order_simulations_table]:
            Tags.of(table).add("BackupEnabled", "true")
            Tags.of(table).add("Feature", "enhanced-consumer-ordering-system")
    
    def _create_secrets(self) -> None:
        """
        Import existing Secrets Manager secrets for external service credentials
        """
        
        # Import existing Razorpay API credentials secret
        # The secret was created manually or by a previous deployment
        secret_name = get_resource_name(self.config, "secret", "razorpay-credentials")
        
        self.razorpay_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "RazorpaySecret",
            secret_name=secret_name
        )
        
        # Update Lambda environment variables with secret ARN
        for function in self.lambda_functions.values():
            function.add_environment("RAZORPAY_SECRET_ARN", self.razorpay_secret.secret_arn)
    
    def _create_lambda_functions(self) -> None:
        """
        Create Lambda functions for the enhanced consumer ordering system
        """
        
        # Common Lambda configuration
        common_lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_11,
            "timeout": Duration.seconds(30),
            "memory_size": 512,
            "environment": {
                "ENVIRONMENT": self.config["environment"],
                "REGION": self.region,
                "ORDERS_TABLE_NAME": self.orders_table.table_name,
                "PAYMENTS_TABLE_NAME": self.payments_table.table_name,
                "TECHNICIANS_TABLE_NAME": self.technicians_table.table_name,
                "ORDER_SIMULATIONS_TABLE_NAME": self.order_simulations_table.table_name,
                "WEBSOCKET_CONNECTIONS_TABLE_NAME": "",  # Will be set after WebSocket table creation
                "RAZORPAY_SECRET_ARN": "",  # Will be set after secret creation
                "ORDERING_EVENT_BUS_NAME": "",  # Will be set after EventBridge creation
                "DATA_KEY_ID": self.kms_key.key_id
            },
            "tracing": lambda_.Tracing.ACTIVE if self.config.get("enable_xray_tracing", True) else lambda_.Tracing.DISABLED,
            "reserved_concurrent_executions": self.config.get("lambda_reserved_concurrency")
        }
        
        # Prepare layers list
        layers = [self.common_layer] if self.common_layer else []
        
        # Order Management Service Lambda
        # Create Lambda with shared modules bundled
        self.order_management_function = lambda_.Function(
            self, "OrderManagementFunction",
            function_name=get_resource_name(self.config, "function", "order-management"),
            handler="orders/enhanced_order_management.lambda_handler",
            code=lambda_.Code.from_asset(
                "../../lambda",
                bundling={
                    "image": lambda_.Runtime.PYTHON_3_11.bundling_image,
                    "command": [
                        "bash", "-c",
                        "pip install -r orders/requirements.txt -t /asset-output && " +
                        "cp -r orders/* /asset-output/ && " +
                        "cp -r shared /asset-output/shared"
                    ]
                }
            ),
            layers=layers,
            **common_lambda_config
        )
        
        # Payment Service Lambda
        self.payment_service_function = lambda_python.PythonFunction(
            self, "PaymentServiceFunction",
            function_name=get_resource_name(self.config, "function", "payment-service"),
            entry="../../lambda/payment_service",
            index="payment_service.py",
            handler="lambda_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # Technician Assignment Service Lambda
        self.technician_assignment_function = lambda_python.PythonFunction(
            self, "TechnicianAssignmentFunction",
            function_name=get_resource_name(self.config, "function", "technician-assignment"),
            entry="../../lambda/technician_assignment",
            index="technician_assignment_service.py",
            handler="lambda_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # Status Simulator Service Lambda
        self.status_simulator_function = lambda_python.PythonFunction(
            self, "StatusSimulatorFunction",
            function_name=get_resource_name(self.config, "function", "status-simulator"),
            entry="../../lambda/status_simulator",
            index="status_simulator_service.py",
            handler="lambda_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # WebSocket Connection Handler Lambda
        self.websocket_connect_function = lambda_python.PythonFunction(
            self, "WebSocketConnectFunction",
            function_name=get_resource_name(self.config, "function", "websocket-connect"),
            entry="../../lambda/websocket_ordering",
            index="handler.py",
            handler="connect_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # WebSocket Disconnect Handler Lambda
        self.websocket_disconnect_function = lambda_python.PythonFunction(
            self, "WebSocketDisconnectFunction",
            function_name=get_resource_name(self.config, "function", "websocket-disconnect"),
            entry="../../lambda/websocket_ordering",
            index="handler.py",
            handler="disconnect_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # WebSocket Broadcast Handler Lambda
        self.websocket_broadcast_function = lambda_python.PythonFunction(
            self, "WebSocketBroadcastFunction",
            function_name=get_resource_name(self.config, "function", "websocket-broadcast"),
            entry="../../lambda/websocket_ordering",
            index="broadcast_handler.py",
            handler="lambda_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # Razorpay Webhook Handler Lambda
        self.razorpay_webhook_function = lambda_python.PythonFunction(
            self, "RazorpayWebhookFunction",
            function_name=get_resource_name(self.config, "function", "razorpay-webhook"),
            entry="../../lambda/payment_service",
            index="webhook_handler.py",
            handler="lambda_handler",
            layers=layers,
            **common_lambda_config
        )
        
        # Store Lambda functions
        self.lambda_functions.update({
            "order_management": self.order_management_function,
            "payment_service": self.payment_service_function,
            "technician_assignment": self.technician_assignment_function,
            "status_simulator": self.status_simulator_function,
            "websocket_connect": self.websocket_connect_function,
            "websocket_disconnect": self.websocket_disconnect_function,
            "websocket_broadcast": self.websocket_broadcast_function,
            "razorpay_webhook": self.razorpay_webhook_function
        })
        
        # Grant DynamoDB permissions to all Lambda functions
        self._grant_dynamodb_permissions()
        
        # Grant Secrets Manager permissions
        self._grant_secrets_permissions()
        
        # Grant EventBridge permissions
        self._grant_eventbridge_permissions()
    
    def _grant_dynamodb_permissions(self) -> None:
        """
        Grant DynamoDB permissions to Lambda functions
        """
        
        # Define table ARNs
        table_arns = [
            self.orders_table.table_arn,
            self.payments_table.table_arn,
            self.technicians_table.table_arn,
            self.order_simulations_table.table_arn,
            f"{self.orders_table.table_arn}/index/*",
            f"{self.payments_table.table_arn}/index/*",
            f"{self.technicians_table.table_arn}/index/*"
        ]
        
        # Grant permissions to all Lambda functions
        for function in self.lambda_functions.values():
            function.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem"
                    ],
                    resources=table_arns
                )
            )
            
            # Grant KMS permissions for DynamoDB encryption
            function.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:DescribeKey"
                    ],
                    resources=[self.kms_key.key_arn]
                )
            )
    
    def _grant_secrets_permissions(self) -> None:
        """
        Grant Secrets Manager permissions to payment service and webhook handler
        """
        
        # Grant to payment service
        self.payment_service_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[self.razorpay_secret.secret_arn]
            )
        )
        
        # Grant to webhook handler
        self.razorpay_webhook_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[self.razorpay_secret.secret_arn]
            )
        )
    
    def _grant_eventbridge_permissions(self) -> None:
        """
        Grant EventBridge permissions to Lambda functions
        """
        
        # Status simulator needs to put events
        self.status_simulator_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "events:PutEvents"
                ],
                resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/*"]
            )
        )
    
    def _create_eventbridge_resources(self) -> None:
        """
        Create EventBridge resources for order status simulation
        """
        
        # Custom event bus for ordering system events
        self.ordering_event_bus = events.EventBus(
            self, "OrderingEventBus",
            event_bus_name=get_resource_name(self.config, "event-bus", "ordering")
        )
        
        # EventBridge rule for status simulation scheduling
        # This will be used by the Status Simulator Lambda to schedule status transitions
        self.status_simulation_rule = events.Rule(
            self, "StatusSimulationRule",
            rule_name=get_resource_name(self.config, "rule", "status-simulation"),
            description="Rule for scheduling order status transitions in demo mode",
            event_bus=self.ordering_event_bus,
            event_pattern=events.EventPattern(
                source=["aquachain.ordering"],
                detail_type=["Order Status Simulation"],
                detail={
                    "action": ["schedule_transition"]
                }
            ),
            enabled=True
        )
        
        # Add Lambda target to the rule
        self.status_simulation_rule.add_target(
            targets.LambdaFunction(
                handler=self.status_simulator_function,
                retry_attempts=3
            )
        )
        
        # EventBridge rule for order status updates (triggers WebSocket broadcasts)
        self.order_status_update_rule = events.Rule(
            self, "OrderStatusUpdateRule",
            rule_name=get_resource_name(self.config, "rule", "order-status-update"),
            description="Rule for broadcasting order status updates via WebSocket",
            event_bus=self.ordering_event_bus,
            event_pattern=events.EventPattern(
                source=["aquachain.ordering"],
                detail_type=["Order Status Update"],
                detail={
                    "action": ["status_changed"]
                }
            ),
            enabled=True
        )
        
        # Add WebSocket broadcast Lambda target
        self.order_status_update_rule.add_target(
            targets.LambdaFunction(
                handler=self.websocket_broadcast_function,
                retry_attempts=3
            )
        )
        
        # Update Lambda environment variables with EventBridge details
        for function in self.lambda_functions.values():
            function.add_environment("ORDERING_EVENT_BUS_NAME", self.ordering_event_bus.event_bus_name)
        
        self.ordering_resources.update({
            "ordering_event_bus": self.ordering_event_bus,
            "status_simulation_rule": self.status_simulation_rule,
            "order_status_update_rule": self.order_status_update_rule
        })
    
    def _create_websocket_api(self) -> None:
        """
        Create WebSocket API for real-time order updates
        """
        
        # WebSocket connections table (reuse existing from data stack if available)
        # This table stores active WebSocket connections for broadcasting updates
        self.websocket_connections_table = dynamodb.Table(
            self, "WebSocketConnectionsTable",
            table_name=get_resource_name(self.config, "table", "websocket-connections"),
            partition_key=dynamodb.Attribute(
                name="connectionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl"  # Connections expire after 24 hours
        )
        
        # GSI for user connections lookup
        self.websocket_connections_table.add_global_secondary_index(
            index_name="UserConnections",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="connectedAt",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Update Lambda environment variables with WebSocket connections table
        for function in self.lambda_functions.values():
            function.add_environment("WEBSOCKET_CONNECTIONS_TABLE_NAME", self.websocket_connections_table.table_name)
        
        # Grant WebSocket connections table permissions
        websocket_table_arns = [
            self.websocket_connections_table.table_arn,
            f"{self.websocket_connections_table.table_arn}/index/*"
        ]
        
        for function in [self.websocket_connect_function, self.websocket_disconnect_function, self.websocket_broadcast_function]:
            function.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    resources=websocket_table_arns
                )
            )
        
        # WebSocket API for real-time updates
        self.websocket_api = apigatewayv2.WebSocketApi(
            self, "OrderingWebSocketApi",
            api_name=get_resource_name(self.config, "websocket-api", "ordering"),
            description="WebSocket API for real-time order status updates",
            connect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration(
                    "ConnectIntegration",
                    self.websocket_connect_function
                )
            ),
            disconnect_route_options=apigatewayv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration(
                    "DisconnectIntegration", 
                    self.websocket_disconnect_function
                )
            )
        )
        
        # WebSocket API stage
        self.websocket_stage = apigatewayv2.WebSocketStage(
            self, "OrderingWebSocketStage",
            web_socket_api=self.websocket_api,
            stage_name=self.config["environment"],
            auto_deploy=True
        )
        
        # Grant WebSocket API management permissions to broadcast function
        self.websocket_broadcast_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "execute-api:ManageConnections"
                ],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:{self.websocket_api.api_id}/*"
                ]
            )
        )
        
        # Update Lambda environment variables with WebSocket API details
        websocket_endpoint = f"https://{self.websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{self.config['environment']}"
        for function in [self.websocket_connect_function, self.websocket_disconnect_function, self.websocket_broadcast_function]:
            function.add_environment("WEBSOCKET_API_ENDPOINT", websocket_endpoint)
        
        self.ordering_resources.update({
            "websocket_api": self.websocket_api,
            "websocket_stage": self.websocket_stage,
            "websocket_connections_table": self.websocket_connections_table
        })
        
        # Output WebSocket API endpoint
        CfnOutput(
            self, "WebSocketApiEndpoint",
            value=f"wss://{self.websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{self.config['environment']}",
            description="WebSocket API endpoint for real-time order updates"
        )
    
    def get_ordering_resources(self) -> Dict[str, Any]:
        """
        Get all ordering system resources for use in other stacks
        """
        return {
            **self.ordering_resources,
            "lambda_functions": self.lambda_functions
        }
    
    def get_lambda_functions(self) -> Dict[str, lambda_.Function]:
        """
        Get Lambda functions for API Gateway integration
        """
        return self.lambda_functions
    
    def get_table_arns(self) -> Dict[str, str]:
        """
        Get table ARNs for IAM policy creation
        """
        return {
            "orders_table_arn": self.orders_table.table_arn,
            "payments_table_arn": self.payments_table.table_arn,
            "technicians_table_arn": self.technicians_table.table_arn,
            "order_simulations_table_arn": self.order_simulations_table.table_arn,
            "websocket_connections_table_arn": self.websocket_connections_table.table_arn
        }
    
    def get_table_names(self) -> Dict[str, str]:
        """
        Get table names for Lambda environment variables
        """
        return {
            "ORDERS_TABLE_NAME": self.orders_table.table_name,
            "PAYMENTS_TABLE_NAME": self.payments_table.table_name,
            "TECHNICIANS_TABLE_NAME": self.technicians_table.table_name,
            "ORDER_SIMULATIONS_TABLE_NAME": self.order_simulations_table.table_name,
            "WEBSOCKET_CONNECTIONS_TABLE_NAME": self.websocket_connections_table.table_name
        }
    
    def get_secret_arns(self) -> Dict[str, str]:
        """
        Get secret ARNs for Lambda environment variables
        """
        return {
            "RAZORPAY_SECRET_ARN": self.razorpay_secret.secret_arn
        }
    
    def get_eventbridge_resources(self) -> Dict[str, Any]:
        """
        Get EventBridge resources for external integrations
        """
        return {
            "ordering_event_bus": self.ordering_event_bus,
            "status_simulation_rule": self.status_simulation_rule,
            "order_status_update_rule": self.order_status_update_rule
        }
    
    def get_websocket_resources(self) -> Dict[str, Any]:
        """
        Get WebSocket API resources for frontend integration
        """
        return {
            "websocket_api": self.websocket_api,
            "websocket_stage": self.websocket_stage,
            "websocket_endpoint": f"wss://{self.websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{self.config['environment']}"
        }