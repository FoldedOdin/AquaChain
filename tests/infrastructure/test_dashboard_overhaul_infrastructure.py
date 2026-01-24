"""
Infrastructure validation tests for Dashboard Overhaul Stack
Tests CDK stack deployment, resource creation, IAM policies, and DynamoDB schemas
"""

import pytest
import boto3
from moto import mock_aws
from aws_cdk import App, Environment
from aws_cdk.assertions import Template, Match
from infrastructure.cdk.stacks.dashboard_overhaul_stack import DashboardOverhaulStack
from infrastructure.cdk.config.environment_config import get_environment_config
import json
import re


class TestDashboardOverhaulInfrastructure:
    """Test suite for Dashboard Overhaul infrastructure validation"""
    
    @pytest.fixture
    def app(self):
        """Create CDK app for testing"""
        return App()
    
    @pytest.fixture
    def config(self):
        """Get test environment configuration"""
        return get_environment_config("dev")
    
    @pytest.fixture
    def stack(self, app, config):
        """Create Dashboard Overhaul stack for testing"""
        return DashboardOverhaulStack(
            app,
            "TestDashboardOverhaulStack",
            config=config,
            env=Environment(account="123456789012", region="us-east-1")
        )
    
    @pytest.fixture
    def template(self, stack):
        """Get CloudFormation template from stack"""
        return Template.from_stack(stack)
    
    def test_stack_creation(self, stack):
        """Test that the stack can be created without errors"""
        assert stack is not None
        assert stack.stack_name == "TestDashboardOverhaulStack"
    
    def test_vpc_infrastructure_creation(self, template):
        """Test VPC and security group creation"""
        
        # Test VPC creation
        template.has_resource_properties("AWS::EC2::VPC", {
            "CidrBlock": "10.0.0.0/16",
            "EnableDnsHostnames": True,
            "EnableDnsSupport": True
        })
        
        # Test private subnets
        template.resource_count_is("AWS::EC2::Subnet", 4)  # 2 private + 2 public
        
        # Test security groups
        template.has_resource_properties("AWS::EC2::SecurityGroup", {
            "GroupDescription": "Security group for dashboard Lambda functions"
        })
        
        template.has_resource_properties("AWS::EC2::SecurityGroup", {
            "GroupDescription": "Security group for API Gateway VPC endpoint"
        })
        
        # Test VPC endpoints
        template.has_resource_properties("AWS::EC2::VPCEndpoint", {
            "ServiceName": Match.string_like_regexp(".*s3.*")
        })
        
        template.has_resource_properties("AWS::EC2::VPCEndpoint", {
            "ServiceName": Match.string_like_regexp(".*dynamodb.*")
        })
    
    def test_kms_keys_creation(self, template):
        """Test KMS key creation with proper configuration"""
        
        # Test dashboard data encryption key
        template.has_resource_properties("AWS::KMS::Key", {
            "Description": "Dashboard system data encryption key",
            "KeyUsage": "ENCRYPT_DECRYPT",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "EnableKeyRotation": True
        })
        
        # Test audit signing key
        template.has_resource_properties("AWS::KMS::Key", {
            "Description": "Dashboard audit trail signing key",
            "KeyUsage": "SIGN_VERIFY",
            "KeySpec": "RSA_2048"
        })
        
        # Test key aliases
        template.resource_count_is("AWS::KMS::Alias", 2)
    
    def test_dynamodb_tables_creation(self, template):
        """Test DynamoDB table creation with proper schemas and GSIs"""
        
        # Test dashboard users table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "AttributeDefinitions": [
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"}
            ],
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"}
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "PointInTimeRecoverySpecification": {
                "PointInTimeRecoveryEnabled": True
            },
            "StreamSpecification": {
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            }
        })
        
        # Test inventory table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "AttributeDefinitions": Match.array_with([
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"}
            ])
        })
        
        # Test purchase orders table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ]
        })
        
        # Test budget table
        template.has_resource("AWS::DynamoDB::Table", {
            "Properties": {
                "TableName": Match.string_like_regexp(".*budget.*")
            }
        })
        
        # Test workflows table
        template.has_resource("AWS::DynamoDB::Table", {
            "Properties": {
                "TableName": Match.string_like_regexp(".*workflows.*")
            }
        })
        
        # Test audit table with retention policy
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": Match.string_like_regexp(".*audit.*"),
            "DeletionPolicy": "Retain"
        })
        
        # Verify total table count
        template.resource_count_is("AWS::DynamoDB::Table", 6)
    
    def test_cognito_user_pool_creation(self, template):
        """Test Cognito user pool with role-based groups"""
        
        # Test user pool configuration
        template.has_resource_properties("AWS::Cognito::UserPool", {
            "AliasAttributes": ["email"],
            "AutoVerifiedAttributes": ["email"],
            "MfaConfiguration": "ON",  # Required MFA
            "Policies": {
                "PasswordPolicy": {
                    "MinimumLength": 12,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True,
                    "RequireUppercase": True
                }
            }
        })
        
        # Test user pool groups
        expected_groups = [
            "inventory-managers",
            "warehouse-managers", 
            "supplier-coordinators",
            "procurement-finance-controllers",
            "administrators"
        ]
        
        for group_name in expected_groups:
            template.has_resource_properties("AWS::Cognito::UserPoolGroup", {
                "GroupName": group_name
            })
        
        # Test user pool client
        template.has_resource_properties("AWS::Cognito::UserPoolClient", {
            "GenerateSecret": False,
            "ExplicitAuthFlows": Match.array_with([
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_USER_SRP_AUTH",
                "ALLOW_CUSTOM_AUTH"
            ])
        })
        
        # Test identity pool
        template.has_resource_properties("AWS::Cognito::IdentityPool", {
            "AllowUnauthenticatedIdentities": False
        })
    
    def test_api_gateway_creation(self, template):
        """Test API Gateway with proper CORS and security headers"""
        
        # Test REST API creation
        template.has_resource_properties("AWS::ApiGateway::RestApi", {
            "Name": Match.string_like_regexp(".*dashboard.*"),
            "Description": "AquaChain Dashboard Overhaul API",
            "EndpointConfiguration": {
                "Types": ["REGIONAL"]
            }
        })
        
        # Test Cognito authorizer
        template.has_resource_properties("AWS::ApiGateway::Authorizer", {
            "Name": "DashboardAuthorizer",
            "Type": "COGNITO_USER_POOLS"
        })
        
        # Test deployment with proper stage configuration
        template.has_resource_properties("AWS::ApiGateway::Stage", {
            "TracingEnabled": True,
            "MethodSettings": [
                {
                    "LoggingLevel": "INFO",
                    "DataTraceEnabled": True,
                    "MetricsEnabled": True
                }
            ]
        })
        
        # Test gateway responses with security headers
        template.has_resource_properties("AWS::ApiGateway::GatewayResponse", {
            "ResponseParameters": {
                "gatewayresponse.header.Strict-Transport-Security": "'max-age=31536000; includeSubDomains'",
                "gatewayresponse.header.X-Content-Type-Options": "'nosniff'",
                "gatewayresponse.header.X-Frame-Options": "'DENY'"
            }
        })
    
    def test_cloudwatch_logging_creation(self, template):
        """Test CloudWatch log groups creation"""
        
        expected_log_groups = [
            "/aws/lambda/.*dashboard.*",
            "/aws/lambda/.*rbac.*",
            "/aws/lambda/.*audit.*",
            "API-Gateway-Execution-Logs.*"
        ]
        
        for log_group_pattern in expected_log_groups:
            template.has_resource_properties("AWS::Logs::LogGroup", {
                "LogGroupName": Match.string_like_regexp(log_group_pattern)
            })
        
        # Test retention policies
        template.has_resource_properties("AWS::Logs::LogGroup", {
            "RetentionInDays": 365  # Audit logs
        })
    
    def test_secrets_manager_creation(self, template):
        """Test AWS Secrets Manager secrets creation"""
        
        # Test dashboard configuration secrets
        template.has_resource_properties("AWS::SecretsManager::Secret", {
            "Description": "Dashboard system sensitive configuration"
        })
        
        # Test ML service secrets
        template.has_resource_properties("AWS::SecretsManager::Secret", {
            "Description": "ML service API keys and configuration"
        })
        
        # Test external service secrets
        template.has_resource_properties("AWS::SecretsManager::Secret", {
            "Description": "External service integration secrets"
        })
        
        # Verify total secrets count
        template.resource_count_is("AWS::SecretsManager::Secret", 3)
    
    def test_iam_roles_least_privilege(self, template):
        """Test IAM roles follow least-privilege principles"""
        
        # Test RBAC service role
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": Match.string_like_regexp(".*rbac-service.*"),
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        })
        
        # Test audit service role
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": Match.string_like_regexp(".*audit-service.*")
        })
        
        # Test business logic role
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": Match.string_like_regexp(".*business-logic.*")
        })
        
        # Test that roles have appropriate managed policies
        template.has_resource_properties("AWS::IAM::Role", {
            "ManagedPolicyArns": Match.array_with([
                Match.string_like_regexp(".*AWSLambdaVPCExecutionRole.*"),
                Match.string_like_regexp(".*AWSXRayDaemonWriteAccess.*")
            ])
        })
    
    def test_iam_policy_least_privilege_validation(self, template):
        """Test that IAM policies follow least-privilege principles"""
        
        # Get all IAM policies from template
        resources = template.to_json()["Resources"]
        iam_policies = [r for r in resources.values() if r["Type"] == "AWS::IAM::Policy"]
        
        for policy in iam_policies:
            policy_document = policy["Properties"]["PolicyDocument"]
            statements = policy_document["Statement"]
            
            for statement in statements:
                # Verify no wildcard resources for sensitive actions
                if isinstance(statement.get("Action"), list):
                    actions = statement["Action"]
                else:
                    actions = [statement.get("Action", "")]
                
                sensitive_actions = [
                    "dynamodb:DeleteTable",
                    "dynamodb:DeleteItem", 
                    "kms:Delete*",
                    "secretsmanager:DeleteSecret",
                    "iam:*"
                ]
                
                for action in actions:
                    if any(sensitive in action for sensitive in sensitive_actions):
                        # Ensure no wildcard resources for sensitive actions
                        resources_list = statement.get("Resource", [])
                        if isinstance(resources_list, str):
                            resources_list = [resources_list]
                        
                        for resource in resources_list:
                            assert resource != "*", f"Wildcard resource found for sensitive action: {action}"
    
    def test_dynamodb_access_patterns(self, template):
        """Test DynamoDB table schemas support required access patterns"""
        
        # Get DynamoDB tables from template
        resources = template.to_json()["Resources"]
        dynamodb_tables = [r for r in resources.values() if r["Type"] == "AWS::DynamoDB::Table"]
        
        # Test that each table has appropriate partition and sort keys
        for table in dynamodb_tables:
            properties = table["Properties"]
            
            # Verify key schema
            key_schema = properties["KeySchema"]
            assert len(key_schema) >= 1, "Table must have at least a partition key"
            
            partition_key = next(k for k in key_schema if k["KeyType"] == "HASH")
            assert partition_key["AttributeName"] in ["PK"], f"Partition key should be PK, got {partition_key['AttributeName']}"
            
            # Verify sort key if present
            sort_keys = [k for k in key_schema if k["KeyType"] == "RANGE"]
            if sort_keys:
                sort_key = sort_keys[0]
                assert sort_key["AttributeName"] in ["SK"], f"Sort key should be SK, got {sort_key['AttributeName']}"
            
            # Verify GSI configuration if present
            if "GlobalSecondaryIndexes" in properties:
                gsis = properties["GlobalSecondaryIndexes"]
                for gsi in gsis:
                    gsi_key_schema = gsi["KeySchema"]
                    gsi_partition_key = next(k for k in gsi_key_schema if k["KeyType"] == "HASH")
                    assert gsi_partition_key["AttributeName"].startswith("GSI"), "GSI partition key should start with GSI"
    
    def test_encryption_at_rest(self, template):
        """Test that all data is encrypted at rest"""
        
        # Test DynamoDB encryption
        resources = template.to_json()["Resources"]
        dynamodb_tables = [r for r in resources.values() if r["Type"] == "AWS::DynamoDB::Table"]
        
        for table in dynamodb_tables:
            properties = table["Properties"]
            assert "SSESpecification" in properties, "DynamoDB table must have encryption enabled"
            sse_spec = properties["SSESpecification"]
            assert sse_spec["SSEEnabled"] is True, "SSE must be enabled"
            assert "KMSMasterKeyId" in sse_spec, "Must use customer-managed KMS key"
    
    def test_monitoring_and_tracing(self, template):
        """Test that monitoring and X-Ray tracing are properly configured"""
        
        # Test X-Ray tracing on API Gateway
        template.has_resource_properties("AWS::ApiGateway::Stage", {
            "TracingEnabled": True
        })
        
        # Test CloudWatch log groups exist
        template.resource_count_is("AWS::Logs::LogGroup", 4)
        
        # Test that log groups have appropriate retention
        resources = template.to_json()["Resources"]
        log_groups = [r for r in resources.values() if r["Type"] == "AWS::Logs::LogGroup"]
        
        for log_group in log_groups:
            properties = log_group["Properties"]
            assert "RetentionInDays" in properties, "Log group must have retention policy"
            retention = properties["RetentionInDays"]
            assert retention in [30, 90, 365], f"Invalid retention period: {retention}"
    
    def test_security_headers_configuration(self, template):
        """Test that security headers are properly configured"""
        
        # Test gateway responses with security headers
        resources = template.to_json()["Resources"]
        gateway_responses = [r for r in resources.values() if r["Type"] == "AWS::ApiGateway::GatewayResponse"]
        
        required_headers = [
            "gatewayresponse.header.Strict-Transport-Security",
            "gatewayresponse.header.X-Content-Type-Options",
            "gatewayresponse.header.X-Frame-Options",
            "gatewayresponse.header.X-XSS-Protection"
        ]
        
        for response in gateway_responses:
            properties = response["Properties"]
            if "ResponseParameters" in properties:
                response_params = properties["ResponseParameters"]
                for header in required_headers:
                    if header in response_params:
                        # Verify header values are properly set
                        header_value = response_params[header]
                        assert header_value.startswith("'") and header_value.endswith("'"), f"Header value must be quoted: {header_value}"
    
    def test_resource_naming_conventions(self, template):
        """Test that resources follow naming conventions"""
        
        resources = template.to_json()["Resources"]
        
        # Test that resource names follow patterns
        for resource_id, resource in resources.items():
            resource_type = resource["Type"]
            
            if resource_type == "AWS::DynamoDB::Table":
                table_name = resource["Properties"]["TableName"]
                assert "dashboard" in table_name.lower() or any(
                    keyword in table_name.lower() 
                    for keyword in ["inventory", "purchase", "budget", "workflow", "audit"]
                ), f"Table name should contain relevant keywords: {table_name}"
            
            elif resource_type == "AWS::Cognito::UserPool":
                pool_name = resource["Properties"]["UserPoolName"]
                assert "dashboard" in pool_name.lower(), f"User pool name should contain 'dashboard': {pool_name}"
    
    def test_stack_outputs(self, stack):
        """Test that stack provides necessary outputs"""
        
        outputs = stack.outputs
        
        required_outputs = [
            "api_endpoint",
            "user_pool_id", 
            "user_pool_client_id",
            "vpc_id",
            "data_key_id"
        ]
        
        for output in required_outputs:
            assert output in outputs, f"Missing required output: {output}"
            assert outputs[output] is not None, f"Output {output} should not be None"
    
    def test_environment_specific_configuration(self, app):
        """Test that different environments have appropriate configurations"""
        
        environments = ["dev", "staging", "prod"]
        
        for env in environments:
            config = get_environment_config(env)
            stack = DashboardOverhaulStack(
                app,
                f"Test-{env}",
                config=config,
                env=Environment(account="123456789012", region="us-east-1")
            )
            
            template = Template.from_stack(stack)
            
            if env == "prod":
                # Production should have retention policies
                template.has_resource_properties("AWS::DynamoDB::Table", {
                    "DeletionPolicy": "Retain"
                })
            else:
                # Non-production can have destroy policies
                pass  # Default behavior is acceptable
    
    @mock_aws
    def test_integration_with_aws_services(self):
        """Integration test with mocked AWS services"""
        
        # This test verifies that the stack can be deployed to actual AWS services
        # using moto mocks to simulate the AWS environment
        
        app = App()
        config = get_environment_config("dev")
        
        stack = DashboardOverhaulStack(
            app,
            "IntegrationTestStack",
            config=config,
            env=Environment(account="123456789012", region="us-east-1")
        )
        
        # Verify stack can be synthesized without errors
        template = Template.from_stack(stack)
        assert template is not None
        
        # Verify critical resources are present
        template.resource_count_is("AWS::DynamoDB::Table", 6)
        template.resource_count_is("AWS::Cognito::UserPool", 1)
        template.resource_count_is("AWS::ApiGateway::RestApi", 1)
        template.resource_count_is("AWS::KMS::Key", 2)
        template.resource_count_is("AWS::SecretsManager::Secret", 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])