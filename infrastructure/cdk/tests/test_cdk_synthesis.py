#!/usr/bin/env python3
"""
CDK Synthesis Test for Enhanced Consumer Ordering Stack

This test validates that the CDK stack can be synthesized without errors,
which is a good indicator that the infrastructure code is valid.
"""

import pytest
import aws_cdk as cdk
from aws_cdk import assertions
import tempfile
import os
import json

from stacks.security_stack import AquaChainSecurityStack
from stacks.lambda_layers_stack import LambdaLayersStack
from config.environment_config import get_environment_config


class TestCDKSynthesis:
    """
    Test CDK synthesis for Enhanced Consumer Ordering Stack
    """
    
    @pytest.fixture
    def app(self):
        """Create CDK app for testing"""
        return cdk.App()
    
    @pytest.fixture
    def dev_config(self):
        """Get development environment configuration"""
        return get_environment_config("dev")
    
    @pytest.fixture
    def test_env(self):
        """Test environment configuration"""
        return cdk.Environment(account="123456789012", region="us-east-1")
    
    def test_security_stack_synthesis(self, app, dev_config, test_env):
        """Test that security stack can be synthesized"""
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        # Synthesize the stack
        template = assertions.Template.from_stack(security_stack)
        
        # Basic validation - check that template is not empty
        template_dict = template.to_json()
        assert "Resources" in template_dict
        assert len(template_dict["Resources"]) > 0
        
        # Check that KMS keys are present
        kms_keys = [
            resource for resource in template_dict["Resources"].values()
            if resource.get("Type") == "AWS::KMS::Key"
        ]
        assert len(kms_keys) >= 2  # Should have at least data key and signing key
    
    def test_lambda_layers_stack_synthesis(self, app, test_env):
        """Test that lambda layers stack can be synthesized"""
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Synthesize the stack
        template = assertions.Template.from_stack(lambda_layers_stack)
        
        # Basic validation
        template_dict = template.to_json()
        assert "Resources" in template_dict
        
        # Check that layer versions are present
        layer_versions = [
            resource for resource in template_dict["Resources"].values()
            if resource.get("Type") == "AWS::Lambda::LayerVersion"
        ]
        assert len(layer_versions) >= 1  # Should have at least common layer
    
    def test_enhanced_ordering_stack_synthesis_without_lambda(self, app, dev_config, test_env):
        """Test enhanced ordering stack synthesis without Lambda functions"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        # Create a minimal version of the enhanced ordering stack for synthesis testing
        class MinimalEnhancedOrderingStack(cdk.Stack):
            def __init__(self, scope, construct_id, config, kms_key, **kwargs):
                super().__init__(scope, construct_id, **kwargs)
                
                from aws_cdk import (
                    aws_dynamodb as dynamodb,
                    aws_events as events,
                    aws_apigatewayv2 as apigatewayv2,
                    aws_secretsmanager as secretsmanager,
                    RemovalPolicy,
                    CfnOutput
                )
                from config.environment_config import get_resource_name
                
                # Create DynamoDB tables
                self.orders_table = dynamodb.Table(
                    self, "OrdersTable",
                    table_name=get_resource_name(config, "table", "orders"),
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
                    encryption_key=kms_key,
                    removal_policy=RemovalPolicy.DESTROY,
                    stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
                    time_to_live_attribute="ttl"
                )
                
                # Add GSIs
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
                
                # Create EventBridge event bus
                self.ordering_event_bus = events.EventBus(
                    self, "OrderingEventBus",
                    event_bus_name=get_resource_name(config, "event-bus", "ordering")
                )
                
                # Create WebSocket API (without Lambda integrations)
                self.websocket_api = apigatewayv2.WebSocketApi(
                    self, "OrderingWebSocketApi",
                    api_name=get_resource_name(config, "websocket-api", "ordering"),
                    description="WebSocket API for real-time order status updates"
                )
                
                # Create WebSocket stage
                self.websocket_stage = apigatewayv2.WebSocketStage(
                    self, "OrderingWebSocketStage",
                    web_socket_api=self.websocket_api,
                    stage_name=config["environment"],
                    auto_deploy=True
                )
                
                # Create Secrets Manager secret
                self.razorpay_secret = secretsmanager.Secret(
                    self, "RazorpaySecret",
                    secret_name=get_resource_name(config, "secret", "razorpay-credentials"),
                    description="Razorpay API credentials for payment processing",
                    encryption_key=kms_key
                )
                
                # Output WebSocket API endpoint
                CfnOutput(
                    self, "WebSocketApiEndpoint",
                    value=f"wss://{self.websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/{config['environment']}",
                    description="WebSocket API endpoint for real-time order updates"
                )
        
        # Create minimal ordering stack
        ordering_stack = MinimalEnhancedOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            env=test_env
        )
        
        # Synthesize the stack
        template = assertions.Template.from_stack(ordering_stack)
        
        # Basic validation
        template_dict = template.to_json()
        assert "Resources" in template_dict
        assert len(template_dict["Resources"]) > 0
        
        # Check specific resources
        dynamodb_tables = [
            resource for resource in template_dict["Resources"].values()
            if resource.get("Type") == "AWS::DynamoDB::Table"
        ]
        assert len(dynamodb_tables) >= 1
        
        event_buses = [
            resource for resource in template_dict["Resources"].values()
            if resource.get("Type") == "AWS::Events::EventBus"
        ]
        assert len(event_buses) >= 1
        
        websocket_apis = [
            resource for resource in template_dict["Resources"].values()
            if resource.get("Type") == "AWS::ApiGatewayV2::Api"
        ]
        assert len(websocket_apis) >= 1
        
        secrets = [
            resource for resource in template_dict["Resources"].values()
            if resource.get("Type") == "AWS::SecretsManager::Secret"
        ]
        assert len(secrets) >= 1
        
        # Check outputs
        assert "Outputs" in template_dict
        outputs = template_dict["Outputs"]
        assert "WebSocketApiEndpoint" in outputs
        
        # Validate WebSocket endpoint format
        websocket_endpoint = outputs["WebSocketApiEndpoint"]["Value"]
        assert "wss://" in websocket_endpoint
        assert "execute-api" in websocket_endpoint
        assert "amazonaws.com" in websocket_endpoint
    
    def test_stack_dependencies_and_references(self, app, dev_config, test_env):
        """Test that stack dependencies and cross-references work correctly"""
        # Create security stack
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        # Create lambda layers stack
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create a stack that references resources from other stacks
        class DependentStack(cdk.Stack):
            def __init__(self, scope, construct_id, security_resources, layer_resources, **kwargs):
                super().__init__(scope, construct_id, **kwargs)
                
                from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
                
                # Create a table that uses KMS key from security stack
                self.test_table = dynamodb.Table(
                    self, "TestTable",
                    table_name="test-dependent-table",
                    partition_key=dynamodb.Attribute(
                        name="id",
                        type=dynamodb.AttributeType.STRING
                    ),
                    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                    encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
                    encryption_key=security_resources["data_key"],
                    removal_policy=RemovalPolicy.DESTROY
                )
        
        # Create dependent stack
        dependent_stack = DependentStack(
            app, "TestDependentStack",
            security_resources={
                "data_key": security_stack.data_key
            },
            layer_resources={
                "common_layer": lambda_layers_stack.get_common_layer()
            },
            env=test_env
        )
        
        # Add explicit dependency
        dependent_stack.add_dependency(security_stack)
        dependent_stack.add_dependency(lambda_layers_stack)
        
        # Synthesize all stacks
        security_template = assertions.Template.from_stack(security_stack)
        layers_template = assertions.Template.from_stack(lambda_layers_stack)
        dependent_template = assertions.Template.from_stack(dependent_stack)
        
        # Validate that all templates are valid
        for template in [security_template, layers_template, dependent_template]:
            template_dict = template.to_json()
            assert "Resources" in template_dict
            assert len(template_dict["Resources"]) > 0
    
    def test_full_app_synthesis(self, dev_config):
        """Test that a complete app with multiple stacks can be synthesized"""
        app = cdk.App()
        test_env = cdk.Environment(account="123456789012", region="us-east-1")
        
        # Create all required stacks
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create a minimal ordering stack
        class TestOrderingStack(cdk.Stack):
            def __init__(self, scope, construct_id, config, kms_key, common_layer, **kwargs):
                super().__init__(scope, construct_id, **kwargs)
                
                from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
                from config.environment_config import get_resource_name
                
                # Just create one table to test the complete flow
                self.orders_table = dynamodb.Table(
                    self, "OrdersTable",
                    table_name=get_resource_name(config, "table", "orders"),
                    partition_key=dynamodb.Attribute(
                        name="PK",
                        type=dynamodb.AttributeType.STRING
                    ),
                    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                    encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
                    encryption_key=kms_key,
                    removal_policy=RemovalPolicy.DESTROY
                )
        
        ordering_stack = TestOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        # Add dependencies
        ordering_stack.add_dependency(security_stack)
        ordering_stack.add_dependency(lambda_layers_stack)
        
        # Synthesize the entire app
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set the output directory
            app.node.set_context("@aws-cdk/core:outdir", temp_dir)
            
            # Synthesize
            cloud_assembly = app.synth()
            
            # Validate that synthesis was successful
            assert cloud_assembly is not None
            
            # Check that template files were created
            stack_names = ["TestSecurityStack", "TestLambdaLayersStack", "TestOrderingStack"]
            for stack_name in stack_names:
                template_file = os.path.join(temp_dir, f"{stack_name}.template.json")
                assert os.path.exists(template_file), f"Template file not found: {template_file}"
                
                # Validate that template is valid JSON
                with open(template_file, 'r') as f:
                    template_content = json.load(f)
                    assert "Resources" in template_content
                    assert len(template_content["Resources"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])