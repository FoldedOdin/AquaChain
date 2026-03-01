"""
WebSocket API Stack for AquaChain Real-Time Updates
Implements WebSocket API Gateway with Lambda handlers for real-time data streaming
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct
from typing import Dict


class WebSocketStack(Stack):
    """
    Stack for WebSocket API with connection management and real-time updates
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: Dict,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.config = config
        self.env_name = config.get("environment", "dev")

        # Create DynamoDB table for connection management
        self.connections_table = self._create_connections_table()

        # Create Lambda functions
        self.connect_handler = self._create_connect_handler()
        self.disconnect_handler = self._create_disconnect_handler()
        self.message_handler = self._create_message_handler()
        self.broadcast_handler = self._create_broadcast_handler()

        # Create WebSocket API
        self.websocket_api = self._create_websocket_api()

        # Grant permissions
        self._grant_permissions()

        # Create outputs
        self._create_outputs()

    def _create_connections_table(self) -> dynamodb.Table:
        """
        Create DynamoDB table to store WebSocket connection IDs
        """
        table = dynamodb.Table(
            self,
            "WebSocketConnectionsTable",
            table_name=f"AquaChain-WebSocketConnections-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="connectionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if self.env_name == "dev" else RemovalPolicy.RETAIN,
            point_in_time_recovery=True if self.env_name == "prod" else False,
            time_to_live_attribute="ttl",
        )

        # Add GSI for querying by topic
        table.add_global_secondary_index(
            index_name="topic-index",
            partition_key=dynamodb.Attribute(
                name="topic",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Add GSI for querying by userId
        table.add_global_secondary_index(
            index_name="userId-index",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        return table

    def _create_connect_handler(self) -> lambda_.Function:
        """
        Create Lambda function to handle WebSocket connections
        """
        handler = lambda_.Function(
            self,
            "WebSocketConnectHandler",
            function_name=f"aquachain-websocket-connect-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="connect.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/websocket"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONNECTIONS_TABLE": self.connections_table.table_name,
                "ENVIRONMENT": self.env_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH,
        )

        return handler

    def _create_disconnect_handler(self) -> lambda_.Function:
        """
        Create Lambda function to handle WebSocket disconnections
        """
        handler = lambda_.Function(
            self,
            "WebSocketDisconnectHandler",
            function_name=f"aquachain-websocket-disconnect-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="disconnect.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/websocket"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONNECTIONS_TABLE": self.connections_table.table_name,
                "ENVIRONMENT": self.env_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH,
        )

        return handler

    def _create_message_handler(self) -> lambda_.Function:
        """
        Create Lambda function to handle WebSocket messages
        """
        handler = lambda_.Function(
            self,
            "WebSocketMessageHandler",
            function_name=f"aquachain-websocket-message-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="message.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/websocket"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONNECTIONS_TABLE": self.connections_table.table_name,
                "ENVIRONMENT": self.env_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH,
        )

        return handler

    def _create_broadcast_handler(self) -> lambda_.Function:
        """
        Create Lambda function to broadcast messages to connected clients
        """
        handler = lambda_.Function(
            self,
            "WebSocketBroadcastHandler",
            function_name=f"aquachain-websocket-broadcast-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="broadcast.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/websocket"),
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "CONNECTIONS_TABLE": self.connections_table.table_name,
                "ENVIRONMENT": self.env_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH,
        )

        return handler

    def _create_websocket_api(self) -> apigwv2.WebSocketApi:
        """
        Create WebSocket API Gateway
        """
        # Create WebSocket API
        websocket_api = apigwv2.WebSocketApi(
            self,
            "WebSocketApi",
            api_name=f"aquachain-websocket-{self.env_name}",
            description=f"AquaChain WebSocket API for real-time updates ({self.env_name})",
            connect_route_options=apigwv2.WebSocketRouteOptions(
                integration=integrations.WebSocketLambdaIntegration(
                    "ConnectIntegration",
                    self.connect_handler
                )
            ),
            disconnect_route_options=apigwv2.WebSocketRouteOptions(
                integration=integrations.WebSocketLambdaIntegration(
                    "DisconnectIntegration",
                    self.disconnect_handler
                )
            ),
            default_route_options=apigwv2.WebSocketRouteOptions(
                integration=integrations.WebSocketLambdaIntegration(
                    "DefaultIntegration",
                    self.message_handler
                )
            ),
        )

        # Create stage
        stage = apigwv2.WebSocketStage(
            self,
            "WebSocketStage",
            web_socket_api=websocket_api,
            stage_name=self.env_name,
            auto_deploy=True,
        )

        return websocket_api

    def _grant_permissions(self) -> None:
        """
        Grant necessary permissions to Lambda functions
        """
        # Grant DynamoDB permissions
        self.connections_table.grant_read_write_data(self.connect_handler)
        self.connections_table.grant_read_write_data(self.disconnect_handler)
        self.connections_table.grant_read_write_data(self.message_handler)
        self.connections_table.grant_read_write_data(self.broadcast_handler)

        # Grant API Gateway management permissions for posting messages
        api_management_policy = iam.PolicyStatement(
            actions=["execute-api:ManageConnections"],
            resources=[
                f"arn:aws:execute-api:{self.region}:{self.account}:{self.websocket_api.api_id}/*"
            ]
        )

        self.message_handler.add_to_role_policy(api_management_policy)
        self.broadcast_handler.add_to_role_policy(api_management_policy)

    def _create_outputs(self) -> None:
        """
        Create CloudFormation outputs
        """
        CfnOutput(
            self,
            "WebSocketApiId",
            value=self.websocket_api.api_id,
            description="WebSocket API ID"
        )

        CfnOutput(
            self,
            "WebSocketApiEndpoint",
            value=self.websocket_api.api_endpoint,
            description="WebSocket API endpoint"
        )

        CfnOutput(
            self,
            "WebSocketUrl",
            value=f"{self.websocket_api.api_endpoint}/{self.env_name}",
            description="WebSocket connection URL"
        )

        CfnOutput(
            self,
            "ConnectionsTableName",
            value=self.connections_table.table_name,
            description="DynamoDB table for WebSocket connections"
        )

