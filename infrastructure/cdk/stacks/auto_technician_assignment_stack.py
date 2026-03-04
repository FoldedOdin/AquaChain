"""
Auto Technician Assignment Stack

Creates Lambda function and EventBridge rule for automatic technician assignment
when orders reach ORDER_PLACED status.
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sns as sns,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name


class AutoTechnicianAssignmentStack(Stack):
    """
    Stack for automatic technician assignment functionality
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 core_resources: Dict[str, Any] = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.core_resources = core_resources or {}
        
        # Create SNS topic for technician alerts
        self._create_sns_topic()
        
        # Create Lambda function
        self._create_lambda_function()
        
        # Create EventBridge rule
        self._create_eventbridge_rule()
        
        # Outputs
        self._create_outputs()
    
    def _create_sns_topic(self) -> None:
        """Create SNS topic for technician profile completion alerts"""
        self.technician_alerts_topic = sns.Topic(
            self, "TechnicianAlertsTopic",
            topic_name=get_resource_name(self.config, "topic", "technician-alerts"),
            display_name="AquaChain Technician Alerts"
        )
    
    def _create_lambda_function(self) -> None:
        """Create Lambda function for automatic technician assignment"""
        
        # Create Lambda execution role
        lambda_role = iam.Role(
            self, "AutoAssignmentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=get_resource_name(self.config, "role", "auto-assignment-lambda"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant DynamoDB permissions
        orders_table_name = get_resource_name(self.config, "table", "orders")
        technicians_table_name = get_resource_name(self.config, "table", "technicians")
        users_table_name = get_resource_name(self.config, "table", "users")
        
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            resources=[
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{orders_table_name}",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{orders_table_name}/index/*",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{technicians_table_name}",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{technicians_table_name}/index/*",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{users_table_name}",
                f"arn:aws:dynamodb:{self.region}:{self.account}:table/{users_table_name}/index/*"
            ]
        ))
        
        # Grant SNS publish permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sns:Publish"],
            resources=[self.technician_alerts_topic.topic_arn]
        ))
        
        # Grant SES send email permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            resources=["*"]  # SES doesn't support resource-level permissions
        ))
        
        # Grant EventBridge permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["events:PutEvents"],
            resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/default"]
        ))
        
        # Create Lambda function
        self.auto_assignment_lambda = lambda_.Function(
            self, "AutoAssignmentLambda",
            function_name=get_resource_name(self.config, "function", "auto-technician-assignment"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="auto_technician_assignment.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/orders"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "ENHANCED_ORDERS_TABLE": orders_table_name,
                "ENHANCED_TECHNICIANS_TABLE": technicians_table_name,
                "USERS_TABLE": users_table_name,
                "TECHNICIAN_ALERTS_TOPIC_ARN": self.technician_alerts_topic.topic_arn,
                "FROM_EMAIL": self.config.get("from_email", "noreply@aquachain.com"),
                "EVENTBRIDGE_BUS": "default",
                "LOG_LEVEL": "INFO"
            },
            log_retention=logs.RetentionDays.ONE_WEEK
        )
    
    def _create_eventbridge_rule(self) -> None:
        """Create EventBridge rule to trigger Lambda on ORDER_PLACED status"""
        
        # Create rule that matches ORDER_STATUS_UPDATED events with status=ORDER_PLACED
        self.order_placed_rule = events.Rule(
            self, "OrderPlacedRule",
            rule_name=get_resource_name(self.config, "rule", "order-placed-assignment"),
            description="Trigger automatic technician assignment when order is placed",
            event_pattern=events.EventPattern(
                source=["aquachain.orders"],
                detail_type=["ORDER_STATUS_UPDATED"],
                detail={
                    "status": ["ORDER_PLACED"]
                }
            )
        )
        
        # Add Lambda as target
        self.order_placed_rule.add_target(
            targets.LambdaFunction(self.auto_assignment_lambda)
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self, "AutoAssignmentLambdaArn",
            value=self.auto_assignment_lambda.function_arn,
            description="Auto Technician Assignment Lambda ARN"
        )
        
        CfnOutput(
            self, "TechnicianAlertsTopicArn",
            value=self.technician_alerts_topic.topic_arn,
            description="Technician Alerts SNS Topic ARN"
        )
        
        CfnOutput(
            self, "OrderPlacedRuleName",
            value=self.order_placed_rule.rule_name,
            description="EventBridge Rule Name for Order Placed Events"
        )
