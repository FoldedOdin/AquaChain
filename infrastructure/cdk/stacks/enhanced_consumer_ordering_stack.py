"""
Enhanced Consumer Ordering System Stack
DynamoDB tables, EventBridge rules, and WebSocket API for the ordering system
"""

from aws_cdk import (
    Stack,
    Tags,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_apigatewayv2 as apigatewayv2,
    aws_kms as kms,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class EnhancedConsumerOrderingStack(Stack):
    """
    Enhanced Consumer Ordering System infrastructure stack
    Contains DynamoDB tables, EventBridge rules, and WebSocket API
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], 
                 kms_key: kms.Key, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.kms_key = kms_key
        self.ordering_resources = {}
        
        # Create DynamoDB tables
        self._create_dynamodb_tables()
        
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
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
        
        # Note: Lambda targets will be added when Lambda functions are created
        
        self.ordering_resources.update({
            "ordering_event_bus": self.ordering_event_bus,
            "status_simulation_rule": self.status_simulation_rule
        })
    
    def _create_websocket_api(self) -> None:
        """
        Create WebSocket API for real-time order updates
        """
        
        # WebSocket API for real-time updates
        self.websocket_api = apigatewayv2.WebSocketApi(
            self, "OrderingWebSocketApi",
            api_name=get_resource_name(self.config, "websocket-api", "ordering"),
            description="WebSocket API for real-time order status updates",
            # Routes will be added when Lambda functions are created
        )
        
        # WebSocket API stage
        self.websocket_stage = apigatewayv2.WebSocketStage(
            self, "OrderingWebSocketStage",
            web_socket_api=self.websocket_api,
            stage_name=self.config["environment"],
            auto_deploy=True
        )
        
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
        return self.ordering_resources
    
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