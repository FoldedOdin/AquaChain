"""
Unit tests for AquaChain CDK stacks
"""

import pytest
import aws_cdk as cdk
from aws_cdk import assertions

from stacks.security_stack import AquaChainSecurityStack
from stacks.core_stack import AquaChainCoreStack
from stacks.data_stack import AquaChainDataStack
from stacks.compute_stack import AquaChainComputeStack
from stacks.api_stack import AquaChainApiStack
from stacks.monitoring_stack import AquaChainMonitoringStack
from config.environment_config import get_environment_config

class TestAquaChainStacks:
    """
    Test suite for AquaChain CDK stacks
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
    
    def test_security_stack_creation(self, app, dev_config):
        """Test security stack creates required resources"""
        stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        template = assertions.Template.from_stack(stack)
        
        # Check KMS keys are created
        template.has_resource_properties("AWS::KMS::Key", {
            "KeyUsage": "ENCRYPT_DECRYPT"
        })
        
        template.has_resource_properties("AWS::KMS::Key", {
            "KeyUsage": "SIGN_VERIFY"
        })
        
        # Check IAM roles are created
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumedBy": {
                "Service": "lambda.amazonaws.com"
            }
        })
    
    def test_data_stack_creation(self, app, dev_config):
        """Test data stack creates required resources"""
        # Create security stack first
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        # Create data stack
        data_stack = AquaChainDataStack(
            app, "TestDataStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            ledger_signing_key=security_stack.ledger_signing_key,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        template = assertions.Template.from_stack(data_stack)
        
        # Check DynamoDB tables are created
        template.resource_count_is("AWS::DynamoDB::Table", 5)
        
        # Check S3 buckets are created
        template.resource_count_is("AWS::S3::Bucket", 3)
        
        # Check IoT resources are created
        template.has_resource_properties("AWS::IoT::ThingType", {
            "ThingTypeName": assertions.Match.string_like_regexp(".*device.*")
        })
        
        template.has_resource_properties("AWS::IoT::TopicRule", {
            "TopicRulePayload": {
                "Sql": assertions.Match.string_like_regexp(".*aquachain.*")
            }
        })
    
    def test_api_stack_creation(self, app, dev_config):
        """Test API stack creates required resources"""
        # Create dependencies
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        data_stack = AquaChainDataStack(
            app, "TestDataStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            ledger_signing_key=security_stack.ledger_signing_key,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        compute_stack = AquaChainComputeStack(
            app, "TestComputeStack",
            config=dev_config,
            data_resources=data_stack.data_resources,
            security_resources=security_stack.security_resources,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        # Create API stack
        api_stack = AquaChainApiStack(
            app, "TestAPIStack",
            config=dev_config,
            lambda_functions=compute_stack.lambda_functions,
            security_resources=security_stack.security_resources,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        template = assertions.Template.from_stack(api_stack)
        
        # Check Cognito User Pool is created
        template.has_resource_properties("AWS::Cognito::UserPool", {
            "UserPoolName": assertions.Match.string_like_regexp(".*users.*")
        })
        
        # Check API Gateway is created
        template.has_resource_properties("AWS::ApiGateway::RestApi", {
            "Name": assertions.Match.string_like_regexp(".*rest.*")
        })
        
        # Check WAF Web ACL is created
        template.has_resource_properties("AWS::WAFv2::WebACL", {
            "Scope": "REGIONAL"
        })
    
    def test_monitoring_stack_creation(self, app, dev_config):
        """Test monitoring stack creates required resources"""
        # Create all dependencies (simplified for testing)
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=dev_config,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        data_stack = AquaChainDataStack(
            app, "TestDataStack",
            config=dev_config,
            kms_key=security_stack.data_key,
            ledger_signing_key=security_stack.ledger_signing_key,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        compute_stack = AquaChainComputeStack(
            app, "TestComputeStack",
            config=dev_config,
            data_resources=data_stack.data_resources,
            security_resources=security_stack.security_resources,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        api_stack = AquaChainApiStack(
            app, "TestAPIStack",
            config=dev_config,
            lambda_functions=compute_stack.lambda_functions,
            security_resources=security_stack.security_resources,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        # Create monitoring stack
        monitoring_stack = AquaChainMonitoringStack(
            app, "TestMonitoringStack",
            config=dev_config,
            data_resources=data_stack.data_resources,
            compute_resources=compute_stack.compute_resources,
            api_resources=api_stack.api_resources,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        template = assertions.Template.from_stack(monitoring_stack)
        
        # Check CloudWatch dashboards are created
        template.has_resource_properties("AWS::CloudWatch::Dashboard", {
            "DashboardName": assertions.Match.string_like_regexp(".*system.*")
        })
        
        # Check CloudWatch alarms are created
        template.resource_count_is("AWS::CloudWatch::Alarm", 6)
        
        # Check SNS topics are created
        template.resource_count_is("AWS::SNS::Topic", 2)
        
        # Check X-Ray sampling rules are created
        template.resource_count_is("AWS::XRay::SamplingRule", 2)
    
    def test_environment_specific_configuration(self, app):
        """Test that different environments have different configurations"""
        dev_config = get_environment_config("dev")
        prod_config = get_environment_config("prod")
        
        # Test dev configuration
        assert dev_config["environment"] == "dev"
        assert dev_config["enable_deletion_protection"] == False
        assert dev_config["lambda_reserved_concurrency"] == 10
        
        # Test prod configuration
        assert prod_config["environment"] == "prod"
        assert prod_config["enable_deletion_protection"] == True
        assert prod_config["lambda_reserved_concurrency"] == 100
        
        # Test that prod has additional features
        assert "backup_config" in prod_config
        assert "backup_config" not in dev_config
    
    def test_resource_naming_consistency(self, app, dev_config):
        """Test that resource names follow consistent patterns"""
        from config.environment_config import get_resource_name
        
        # Test resource naming
        table_name = get_resource_name(dev_config, "table", "readings")
        assert table_name == "aquachain-table-readings-dev"
        
        bucket_name = get_resource_name(dev_config, "bucket", "data-lake")
        assert bucket_name == "aquachain-bucket-data-lake-dev"
        
        function_name = get_resource_name(dev_config, "function", "data-processing")
        assert function_name == "aquachain-function-data-processing-dev"
    
    def test_security_best_practices(self, app, prod_config):
        """Test that security best practices are implemented"""
        security_stack = AquaChainSecurityStack(
            app, "TestSecurityStack",
            config=prod_config,
            env=cdk.Environment(account="123456789012", region="us-east-1")
        )
        
        template = assertions.Template.from_stack(security_stack)
        
        # Check KMS key rotation is enabled for production
        template.has_resource_properties("AWS::KMS::Key", {
            "EnableKeyRotation": True
        })
        
        # Check IAM roles follow least privilege
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": assertions.Match.any_value()
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        })

if __name__ == "__main__":
    pytest.main([__file__])