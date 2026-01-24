"""
Basic infrastructure validation tests for Dashboard Overhaul Stack
Tests core CDK functionality and resource validation
"""

import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from aws_cdk import App, Environment
    from aws_cdk.assertions import Template, Match
    from infrastructure.cdk.stacks.dashboard_overhaul_stack import DashboardOverhaulStack
    from infrastructure.cdk.config.environment_config import get_environment_config
    CDK_AVAILABLE = True
except ImportError as e:
    CDK_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestBasicInfrastructure:
    """Basic infrastructure validation tests"""
    
    def test_environment_config_loading(self):
        """Test that environment configuration can be loaded"""
        if not CDK_AVAILABLE:
            pytest.skip(f"CDK not available: {IMPORT_ERROR}")
        
        config = get_environment_config("dev")
        assert config is not None
        assert config["environment"] == "dev"
        assert "project_name" in config
        assert "region" in config
    
    def test_stack_creation_basic(self):
        """Test basic stack creation without complex validation"""
        if not CDK_AVAILABLE:
            pytest.skip(f"CDK not available: {IMPORT_ERROR}")
        
        app = App()
        config = get_environment_config("dev")
        
        try:
            stack = DashboardOverhaulStack(
                app,
                "TestBasicStack",
                config=config,
                env=Environment(account="123456789012", region="us-east-1")
            )
            assert stack is not None
            assert stack.stack_name == "TestBasicStack"
        except Exception as e:
            pytest.fail(f"Stack creation failed: {e}")
    
    def test_template_generation(self):
        """Test that CloudFormation template can be generated"""
        if not CDK_AVAILABLE:
            pytest.skip(f"CDK not available: {IMPORT_ERROR}")
        
        app = App()
        config = get_environment_config("dev")
        
        try:
            stack = DashboardOverhaulStack(
                app,
                "TestTemplateStack",
                config=config,
                env=Environment(account="123456789012", region="us-east-1")
            )
            
            template = Template.from_stack(stack)
            assert template is not None
            
            # Basic resource count validation
            template_json = template.to_json()
            resources = template_json.get("Resources", {})
            assert len(resources) > 0, "Template should contain resources"
            
        except Exception as e:
            pytest.fail(f"Template generation failed: {e}")
    
    def test_required_resources_present(self):
        """Test that required resource types are present in template"""
        if not CDK_AVAILABLE:
            pytest.skip(f"CDK not available: {IMPORT_ERROR}")
        
        app = App()
        config = get_environment_config("dev")
        
        try:
            stack = DashboardOverhaulStack(
                app,
                "TestResourcesStack",
                config=config,
                env=Environment(account="123456789012", region="us-east-1")
            )
            
            template = Template.from_stack(stack)
            template_json = template.to_json()
            resources = template_json.get("Resources", {})
            
            # Check for required resource types
            resource_types = [resource["Type"] for resource in resources.values()]
            
            required_types = [
                "AWS::DynamoDB::Table",
                "AWS::Cognito::UserPool",
                "AWS::ApiGateway::RestApi",
                "AWS::KMS::Key",
                "AWS::SecretsManager::Secret",
                "AWS::EC2::VPC"
            ]
            
            for required_type in required_types:
                assert required_type in resource_types, f"Missing required resource type: {required_type}"
                
        except Exception as e:
            pytest.fail(f"Resource validation failed: {e}")
    
    def test_dynamodb_tables_basic_structure(self):
        """Test basic DynamoDB table structure"""
        if not CDK_AVAILABLE:
            pytest.skip(f"CDK not available: {IMPORT_ERROR}")
        
        app = App()
        config = get_environment_config("dev")
        
        try:
            stack = DashboardOverhaulStack(
                app,
                "TestDynamoDBStack",
                config=config,
                env=Environment(account="123456789012", region="us-east-1")
            )
            
            template = Template.from_stack(stack)
            template_json = template.to_json()
            resources = template_json.get("Resources", {})
            
            # Find DynamoDB tables
            dynamodb_tables = [
                resource for resource in resources.values() 
                if resource["Type"] == "AWS::DynamoDB::Table"
            ]
            
            assert len(dynamodb_tables) >= 6, "Should have at least 6 DynamoDB tables"
            
            # Verify each table has required properties
            for table in dynamodb_tables:
                properties = table["Properties"]
                assert "AttributeDefinitions" in properties
                assert "KeySchema" in properties
                assert "BillingMode" in properties
                assert properties["BillingMode"] == "PAY_PER_REQUEST"
                
        except Exception as e:
            pytest.fail(f"DynamoDB validation failed: {e}")
    
    def test_cognito_user_pool_basic_config(self):
        """Test basic Cognito user pool configuration"""
        if not CDK_AVAILABLE:
            pytest.skip(f"CDK not available: {IMPORT_ERROR}")
        
        app = App()
        config = get_environment_config("dev")
        
        try:
            stack = DashboardOverhaulStack(
                app,
                "TestCognitoStack",
                config=config,
                env=Environment(account="123456789012", region="us-east-1")
            )
            
            template = Template.from_stack(stack)
            template_json = template.to_json()
            resources = template_json.get("Resources", {})
            
            # Find Cognito user pool
            user_pools = [
                resource for resource in resources.values() 
                if resource["Type"] == "AWS::Cognito::UserPool"
            ]
            
            assert len(user_pools) >= 1, "Should have at least 1 Cognito user pool"
            
            user_pool = user_pools[0]
            properties = user_pool["Properties"]
            
            # Verify MFA is enabled
            assert properties.get("MfaConfiguration") == "ON"
            
            # Verify password policy exists
            assert "Policies" in properties
            assert "PasswordPolicy" in properties["Policies"]
            
        except Exception as e:
            pytest.fail(f"Cognito validation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])