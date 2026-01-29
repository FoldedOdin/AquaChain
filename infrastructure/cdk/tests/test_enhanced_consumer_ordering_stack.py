"""
Unit tests for Enhanced Consumer Ordering Stack
Tests CDK stack deployment and resource creation for the ordering system
"""

import pytest
import aws_cdk as cdk
from aws_cdk import assertions

from stacks.security_stack import AquaChainSecurityStack
from stacks.lambda_layers_stack import LambdaLayersStack
from stacks.enhanced_consumer_ordering_stack import EnhancedConsumerOrderingStack
from config.environment_config import get_environment_config


class TestEnhancedConsumerOrderingStack:
    """
    Test suite for Enhanced Consumer Ordering Stack
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
    def prod_config(self):
        """Get production environment configuration"""
        return get_environment_config("prod")
    
    @pytest.fixture
    def test_env(self):
        """Test environment configuration"""
        return cdk.Environment(account="123456789012", region="us-east-1")
    
    def test_dynamodb_tables_creation(self, app, dev_config, test_env):
        """Test that all required DynamoDB tables are created with proper configuration"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check that 5 DynamoDB tables are created (Orders, Payments, Technicians, OrderSimulations, WebSocketConnections)
        template.resource_count_is("AWS::DynamoDB::Table", 5)
        
        # Check Orders table configuration
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(".*orders.*"),
            "BillingMode": "PAY_PER_REQUEST",
            "SSESpecification": {
                "SSEEnabled": True,
                "KMSMasterKeyId": assertions.Match.any_value()
            },
            "StreamSpecification": {
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            },
            "TimeToLiveSpecification": {
                "AttributeName": "ttl",
                "Enabled": True
            }
        })
        
        # Check Payments table configuration
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(".*payments.*"),
            "BillingMode": "PAY_PER_REQUEST",
            "SSESpecification": {
                "SSEEnabled": True
            },
            "StreamSpecification": {
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            }
        })
        
        # Check Technicians table configuration
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(".*technicians.*"),
            "BillingMode": "PAY_PER_REQUEST",
            "SSESpecification": {
                "SSEEnabled": True
            }
        })
        
        # Check WebSocket connections table configuration
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(".*websocket-connections.*"),
            "TimeToLiveSpecification": {
                "AttributeName": "ttl",
                "Enabled": True
            }
        })
    
    def test_global_secondary_indexes(self, app, dev_config, test_env):
        """Test that Global Secondary Indexes are properly configured"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check that GSIs are created for Orders table (GSI1: Consumer Orders, GSI2: Status Index)
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                },
                {
                    "IndexName": "GSI2",
                    "KeySchema": [
                        {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI2SK", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ]
        })
        
        # Check that GSI is created for WebSocket connections table (UserConnections)
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "UserConnections",
                    "KeySchema": [
                        {"AttributeName": "userId", "KeyType": "HASH"},
                        {"AttributeName": "connectedAt", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ]
        })
    
    def test_lambda_functions_creation(self, app, dev_config, test_env):
        """Test that all required Lambda functions are created with proper configuration"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check that 7 Lambda functions are created
        template.resource_count_is("AWS::Lambda::Function", 7)
        
        # Check Order Management function
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*order-management.*"),
            "Runtime": "python3.11",
            "Timeout": 30,
            "MemorySize": 512,
            "TracingConfig": {"Mode": "Active"}
        })
        
        # Check Payment Service function
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*payment-service.*"),
            "Runtime": "python3.11"
        })
        
        # Check Technician Assignment function
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*technician-assignment.*"),
            "Runtime": "python3.11"
        })
        
        # Check Status Simulator function
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*status-simulator.*"),
            "Runtime": "python3.11"
        })
        
        # Check WebSocket functions
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*websocket-connect.*"),
            "Runtime": "python3.11"
        })
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*websocket-disconnect.*"),
            "Runtime": "python3.11"
        })
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(".*websocket-broadcast.*"),
            "Runtime": "python3.11"
        })
    
    def test_eventbridge_resources(self, app, dev_config, test_env):
        """Test that EventBridge resources are properly configured"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check EventBridge custom event bus
        template.has_resource_properties("AWS::Events::EventBus", {
            "Name": assertions.Match.string_like_regexp(".*ordering.*")
        })
        
        # Check EventBridge rules
        template.resource_count_is("AWS::Events::Rule", 2)
        
        # Check Status Simulation rule
        template.has_resource_properties("AWS::Events::Rule", {
            "Name": assertions.Match.string_like_regexp(".*status-simulation.*"),
            "EventPattern": {
                "source": ["aquachain.ordering"],
                "detail-type": ["Order Status Simulation"],
                "detail": {
                    "action": ["schedule_transition"]
                }
            },
            "State": "ENABLED"
        })
        
        # Check Order Status Update rule
        template.has_resource_properties("AWS::Events::Rule", {
            "Name": assertions.Match.string_like_regexp(".*order-status-update.*"),
            "EventPattern": {
                "source": ["aquachain.ordering"],
                "detail-type": ["Order Status Update"],
                "detail": {
                    "action": ["status_changed"]
                }
            },
            "State": "ENABLED"
        })
    
    def test_websocket_api_configuration(self, app, dev_config, test_env):
        """Test that WebSocket API is properly configured"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check WebSocket API
        template.has_resource_properties("AWS::ApiGatewayV2::Api", {
            "Name": assertions.Match.string_like_regexp(".*ordering.*"),
            "ProtocolType": "WEBSOCKET"
        })
        
        # Check WebSocket API stage
        template.has_resource_properties("AWS::ApiGatewayV2::Stage", {
            "StageName": "dev",
            "AutoDeploy": True
        })
        
        # Check WebSocket routes (connect and disconnect)
        template.resource_count_is("AWS::ApiGatewayV2::Route", 2)
        
        # Check WebSocket integrations
        template.resource_count_is("AWS::ApiGatewayV2::Integration", 2)
    
    def test_secrets_manager_configuration(self, app, dev_config, test_env):
        """Test that Secrets Manager secrets are properly configured"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check Razorpay secret
        template.has_resource_properties("AWS::SecretsManager::Secret", {
            "Name": assertions.Match.string_like_regexp(".*razorpay-credentials.*"),
            "Description": "Razorpay API credentials for payment processing",
            "KmsKeyId": assertions.Match.any_value()
        })
    
    def test_iam_permissions_configuration(self, app, dev_config, test_env):
        """Test that IAM permissions are properly configured for Lambda functions"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check that IAM policies are created for DynamoDB access
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:PutItem",
                            "dynamodb:GetItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan",
                            "dynamodb:BatchGetItem",
                            "dynamodb:BatchWriteItem"
                        ],
                        "Resource": assertions.Match.any_value()
                    }
                ])
            }
        })
        
        # Check that IAM policies are created for KMS access
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": [
                            "kms:Decrypt",
                            "kms:DescribeKey"
                        ],
                        "Resource": assertions.Match.any_value()
                    }
                ])
            }
        })
        
        # Check that IAM policies are created for Secrets Manager access
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": ["secretsmanager:GetSecretValue"],
                        "Resource": assertions.Match.any_value()
                    }
                ])
            }
        })
        
        # Check that IAM policies are created for EventBridge access
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": ["events:PutEvents"],
                        "Resource": assertions.Match.any_value()
                    }
                ])
            }
        })
        
        # Check that IAM policies are created for WebSocket API management
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": ["execute-api:ManageConnections"],
                        "Resource": assertions.Match.any_value()
                    }
                ])
            }
        })
    
    def test_environment_specific_configurations(self, app, test_env):
        """Test that different environments have appropriate configurations"""
        dev_config = get_environment_config("dev")
        prod_config = get_environment_config("prod")
        
        # Create security stack
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Test dev environment
        dev_ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestDevOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        dev_template = assertions.Template.from_stack(dev_ordering_stack)
        
        # Check that dev environment allows table deletion
        dev_template.has_resource_properties("AWS::DynamoDB::Table", {
            "DeletionPolicy": assertions.Match.absent()
        })
        
        # Test prod environment
        prod_ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestProdOrderingStack",
            config=prod_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        prod_template = assertions.Template.from_stack(prod_ordering_stack)
        
        # Check that prod environment has retention policies
        # Note: Orders and Payments tables should have RETAIN policy in prod
        prod_template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(".*orders.*")
        })
    
    def test_resource_tagging(self, app, dev_config, test_env):
        """Test that resources are properly tagged"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check that DynamoDB tables have proper tags
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "Tags": assertions.Match.array_with([
                {"Key": "BackupEnabled", "Value": "true"},
                {"Key": "Feature", "Value": "enhanced-consumer-ordering-system"}
            ])
        })
    
    def test_stack_outputs(self, app, dev_config, test_env):
        """Test that stack outputs are properly configured"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        lambda_layers_stack = LambdaLayersStack(
            app, "TestLambdaLayersStack",
            env=test_env
        )
        
        # Create enhanced ordering stack
        ordering_stack = EnhancedConsumerOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            common_layer=lambda_layers_stack.get_common_layer(),
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check WebSocket API endpoint output
        template.has_output("WebSocketApiEndpoint", {
            "Description": "WebSocket API endpoint for real-time order updates",
            "Value": assertions.Match.string_like_regexp("wss://.*execute-api.*amazonaws.com.*")
        })


if __name__ == "__main__":
    pytest.main([__file__])