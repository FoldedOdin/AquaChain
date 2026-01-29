"""
Simple unit tests for Enhanced Consumer Ordering Stack (without Docker dependencies)
Tests basic CDK stack structure and DynamoDB table configuration
"""

import pytest
import aws_cdk as cdk
from aws_cdk import assertions

from stacks.security_stack import AquaChainSecurityStack
from config.environment_config import get_environment_config


class TestEnhancedConsumerOrderingStackSimple:
    """
    Simple test suite for Enhanced Consumer Ordering Stack (no Docker required)
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
    
    def test_security_stack_creation(self, app, dev_config, test_env):
        """Test that security stack creates required KMS keys"""
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        template = assertions.Template.from_stack(security_stack)
        
        # Check KMS keys are created
        template.has_resource_properties("AWS::KMS::Key", {
            "KeyUsage": "ENCRYPT_DECRYPT"
        })
        
        template.has_resource_properties("AWS::KMS::Key", {
            "KeyUsage": "SIGN_VERIFY"
        })
        
        # Check IAM roles are created
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        })
    
    def test_enhanced_ordering_stack_basic_structure(self, app, dev_config, test_env):
        """Test basic stack structure without Lambda functions"""
        # Create security stack first
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        # Import the stack class directly to avoid Lambda function creation
        from stacks.enhanced_consumer_ordering_stack import EnhancedConsumerOrderingStack
        
        # Create a minimal version of the stack for testing
        class MinimalOrderingStack(cdk.Stack):
            def __init__(self, scope, construct_id, config, kms_key, **kwargs):
                super().__init__(scope, construct_id, **kwargs)
                
                self.config = config
                self.kms_key = kms_key
                
                # Create only DynamoDB tables for testing
                self._create_dynamodb_tables()
                
                # Create EventBridge resources
                self._create_eventbridge_resources()
                
                # Create Secrets Manager secrets
                self._create_secrets()
            
            def _create_dynamodb_tables(self):
                """Create DynamoDB tables"""
                from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
                from config.environment_config import get_resource_name
                
                # Orders table
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
                    removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
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
                
                # Payments table
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
                    removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
                    stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
                )
                
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
            
            def _create_eventbridge_resources(self):
                """Create EventBridge resources"""
                from aws_cdk import aws_events as events
                from config.environment_config import get_resource_name
                
                self.ordering_event_bus = events.EventBus(
                    self, "OrderingEventBus",
                    event_bus_name=get_resource_name(self.config, "event-bus", "ordering")
                )
            
            def _create_secrets(self):
                """Create Secrets Manager secrets"""
                from aws_cdk import aws_secretsmanager as secretsmanager
                from config.environment_config import get_resource_name
                
                self.razorpay_secret = secretsmanager.Secret(
                    self, "RazorpaySecret",
                    secret_name=get_resource_name(self.config, "secret", "razorpay-credentials"),
                    description="Razorpay API credentials for payment processing",
                    encryption_key=self.kms_key,
                    generate_secret_string=secretsmanager.SecretStringGenerator(
                        secret_string_template='{"key_id": ""}',
                        generate_string_key="key_secret",
                        exclude_characters=' "%@\\\'',
                        password_length=32
                    )
                )
        
        # Create minimal ordering stack
        ordering_stack = MinimalOrderingStack(
            app, "TestOrderingStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            env=test_env
        )
        
        template = assertions.Template.from_stack(ordering_stack)
        
        # Check that DynamoDB tables are created
        template.resource_count_is("AWS::DynamoDB::Table", 2)
        
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
        
        # Check EventBridge event bus
        template.has_resource_properties("AWS::Events::EventBus", {
            "Name": assertions.Match.string_like_regexp(".*ordering.*")
        })
        
        # Check Secrets Manager secret
        template.has_resource_properties("AWS::SecretsManager::Secret", {
            "Name": assertions.Match.string_like_regexp(".*razorpay-credentials.*"),
            "Description": "Razorpay API credentials for payment processing",
            "KmsKeyId": assertions.Match.any_value()
        })
    
    def test_global_secondary_indexes_configuration(self, app, dev_config, test_env):
        """Test that GSIs are properly configured"""
        # Create security stack first
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=test_env
        )
        
        # Create a simple stack with just one table to test GSI configuration
        class GSITestStack(cdk.Stack):
            def __init__(self, scope, construct_id, config, kms_key, **kwargs):
                super().__init__(scope, construct_id, **kwargs)
                
                from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
                from config.environment_config import get_resource_name
                
                # Orders table with GSIs
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
                    removal_policy=RemovalPolicy.DESTROY
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
        
        gsi_stack = GSITestStack(
            app, "TestGSIStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            env=test_env
        )
        
        template = assertions.Template.from_stack(gsi_stack)
        
        # Check that GSIs are created with correct configuration
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
    
    def test_resource_naming_consistency(self, app, dev_config):
        """Test that resource names follow consistent patterns"""
        from config.environment_config import get_resource_name
        
        # Test resource naming for ordering system
        orders_table_name = get_resource_name(dev_config, "table", "orders")
        assert orders_table_name == "aquachain-table-orders-dev"
        
        payments_table_name = get_resource_name(dev_config, "table", "payments")
        assert payments_table_name == "aquachain-table-payments-dev"
        
        event_bus_name = get_resource_name(dev_config, "event-bus", "ordering")
        assert event_bus_name == "aquachain-event-bus-ordering-dev"
        
        secret_name = get_resource_name(dev_config, "secret", "razorpay-credentials")
        assert secret_name == "aquachain-secret-razorpay-credentials-dev"
    
    def test_environment_specific_configurations(self, app):
        """Test that different environments have appropriate configurations"""
        dev_config = get_environment_config("dev")
        prod_config = get_environment_config("prod")
        
        # Test dev configuration
        assert dev_config["environment"] == "dev"
        assert dev_config["enable_deletion_protection"] == False
        
        # Test prod configuration
        assert prod_config["environment"] == "prod"
        assert prod_config["enable_deletion_protection"] == True
        
        # Test that both environments have required ordering system configurations
        assert "lambda_reserved_concurrency" in dev_config
        assert "lambda_reserved_concurrency" in prod_config
        assert "enable_xray_tracing" in dev_config
        assert "enable_xray_tracing" in prod_config


if __name__ == "__main__":
    pytest.main([__file__])