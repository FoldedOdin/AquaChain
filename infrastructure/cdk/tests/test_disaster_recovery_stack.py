"""
Tests for AquaChain Disaster Recovery Stack
"""

import pytest
from aws_cdk import App, Environment
from aws_cdk.assertions import Template, Match
from stacks.disaster_recovery_stack import AquaChainDisasterRecoveryStack
from stacks.security_stack import AquaChainSecurityStack
from stacks.data_stack import AquaChainDataStack
from config.environment_config import get_environment_config

@pytest.fixture
def app():
    """Create CDK app for testing"""
    return App()

@pytest.fixture
def config():
    """Get test configuration"""
    return get_environment_config("dev")

@pytest.fixture
def aws_env():
    """Create AWS environment for testing"""
    return Environment(account="123456789012", region="us-east-1")

@pytest.fixture
def security_stack(app, config, aws_env):
    """Create security stack for testing"""
    return AquaChainSecurityStack(
        app, "TestSecurityStack", config=config, env=aws_env
    )

@pytest.fixture
def data_stack(app, config, aws_env, security_stack):
    """Create data stack for testing"""
    return AquaChainDataStack(
        app, "TestDataStack", 
        config=config,
        kms_key=security_stack.data_key,
        ledger_signing_key=security_stack.ledger_signing_key,
        env=aws_env
    )

@pytest.fixture
def dr_stack(app, config, aws_env, data_stack, security_stack):
    """Create disaster recovery stack for testing"""
    return AquaChainDisasterRecoveryStack(
        app, "TestDRStack",
        config=config,
        data_resources=data_stack.data_resources,
        security_resources=security_stack.security_resources,
        env=aws_env
    )

class TestDisasterRecoveryStack:
    """Test cases for disaster recovery stack"""
    
    def test_backup_vault_created(self, dr_stack):
        """Test that backup vault is created with proper configuration"""
        template = Template.from_stack(dr_stack)
        
        template.has_resource_properties("AWS::Backup::BackupVault", {
            "BackupVaultName": Match.string_like_regexp(r"aquachain-vault-main-dev"),
            "EncryptionKeyArn": Match.any_value()
        })
    
    def test_backup_plans_created(self, dr_stack):
        """Test that backup plans are created for DynamoDB and S3"""
        template = Template.from_stack(dr_stack)
        
        # DynamoDB backup plan
        template.has_resource_properties("AWS::Backup::BackupPlan", {
            "BackupPlan": {
                "BackupPlanName": Match.string_like_regexp(r"aquachain-plan-dynamodb-dev")
            }
        })
        
        # S3 backup plan
        template.has_resource_properties("AWS::Backup::BackupPlan", {
            "BackupPlan": {
                "BackupPlanName": Match.string_like_regexp(r"aquachain-plan-s3-dev")
            }
        })
    
    def test_backup_selections_created(self, dr_stack):
        """Test that backup selections are created for critical resources"""
        template = Template.from_stack(dr_stack)
        
        # DynamoDB backup selection
        template.has_resource_properties("AWS::Backup::BackupSelection", {
            "BackupSelectionName": "CriticalDynamoDBTables"
        })
        
        # S3 backup selection
        template.has_resource_properties("AWS::Backup::BackupSelection", {
            "BackupSelectionName": "CriticalS3Buckets"
        })
    
    def test_dr_lambda_created(self, dr_stack):
        """Test that disaster recovery Lambda function is created"""
        template = Template.from_stack(dr_stack)
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": Match.string_like_regexp(r"aquachain-function-disaster-recovery-dev"),
            "Runtime": "python3.11",
            "Handler": "handler.lambda_handler",
            "Timeout": 900,  # 15 minutes
            "MemorySize": 512
        })
    
    def test_step_function_created(self, dr_stack):
        """Test that Step Function state machine is created"""
        template = Template.from_stack(dr_stack)
        
        template.has_resource_properties("AWS::StepFunctions::StateMachine", {
            "StateMachineName": Match.string_like_regexp(r"aquachain-statemachine-disaster-recovery-dev")
        })
    
    def test_sns_topic_created(self, dr_stack):
        """Test that SNS topic for DR notifications is created"""
        template = Template.from_stack(dr_stack)
        
        template.has_resource_properties("AWS::SNS::Topic", {
            "TopicName": Match.string_like_regexp(r"aquachain-topic-dr-notifications-dev"),
            "DisplayName": "AquaChain Disaster Recovery Notifications"
        })
    
    def test_cloudwatch_alarms_created(self, dr_stack):
        """Test that CloudWatch alarms are created for DR monitoring"""
        template = Template.from_stack(dr_stack)
        
        # Backup failure alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmName": Match.string_like_regexp(r"aquachain-alarm-backup-failures-dev"),
            "AlarmDescription": "Alert when backup jobs fail"
        })
        
        # DR test failure alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmName": Match.string_like_regexp(r"aquachain-alarm-dr-test-failures-dev"),
            "AlarmDescription": "Alert when DR tests fail"
        })
    
    def test_iam_roles_created(self, dr_stack):
        """Test that necessary IAM roles are created"""
        template = Template.from_stack(dr_stack)
        
        # Backup service role
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": Match.string_like_regexp(r"aquachain-role-backup-service-dev"),
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "backup.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        })
        
        # DR Lambda role
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": Match.string_like_regexp(r"aquachain-role-dr-lambda-dev"),
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
    
    def test_backup_schedule_dev_environment(self, dr_stack):
        """Test that dev environment has weekly backup schedule"""
        template = Template.from_stack(dr_stack)
        
        # Should have weekly backup rule for dev
        template.has_resource_properties("AWS::Backup::BackupPlan", {
            "BackupPlan": {
                "BackupPlanRules": [
                    {
                        "RuleName": "WeeklyBackups",
                        "ScheduleExpression": "cron(0 2 ? * SUN *)"  # Weekly on Sunday
                    }
                ]
            }
        })
    
    def test_outputs_created(self, dr_stack):
        """Test that stack outputs are created"""
        template = Template.from_stack(dr_stack)
        
        # Check for expected outputs
        outputs = template.find_outputs("*")
        
        assert "BackupVaultName" in outputs
        assert "DRStateMachineArn" in outputs
        assert "DRNotificationsTopicArn" in outputs

class TestDisasterRecoveryStackProduction:
    """Test cases specific to production environment"""
    
    @pytest.fixture
    def prod_config(self):
        """Get production configuration"""
        config = get_environment_config("prod")
        # Override replica account for testing
        config["replica_account_id"] = "987654321098"
        config["backup_config"] = {
            "enable_continuous_backup": True,
            "backup_retention_days": 35,
            "enable_cross_region_backup": True
        }
        return config
    
    @pytest.fixture
    def prod_dr_stack(self, app, prod_config, aws_env, data_stack, security_stack):
        """Create production disaster recovery stack"""
        return AquaChainDisasterRecoveryStack(
            app, "TestProdDRStack",
            config=prod_config,
            data_resources=data_stack.data_resources,
            security_resources=security_stack.security_resources,
            env=aws_env
        )
    
    def test_production_backup_schedule(self, prod_dr_stack):
        """Test that production has daily and continuous backup schedules"""
        template = Template.from_stack(prod_dr_stack)
        
        # Should have daily backup rule
        template.has_resource_properties("AWS::Backup::BackupPlan", {
            "BackupPlan": {
                "BackupPlanRules": Match.array_with([
                    {
                        "RuleName": "DailyBackups",
                        "ScheduleExpression": "cron(0 2 * * ? *)"  # Daily at 2 AM
                    }
                ])
            }
        })
        
        # Should have continuous backup rule
        template.has_resource_properties("AWS::Backup::BackupPlan", {
            "BackupPlan": {
                "BackupPlanRules": Match.array_with([
                    {
                        "RuleName": "ContinuousBackups",
                        "ScheduleExpression": "cron(0 * * * ? *)"  # Hourly
                    }
                ])
            }
        })
    
    def test_cross_region_replication_role(self, prod_dr_stack):
        """Test that cross-region replication role is created for production"""
        template = Template.from_stack(prod_dr_stack)
        
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": Match.string_like_regexp(r"aquachain-role-s3-replication-prod"),
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "s3.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        })

class TestDisasterRecoveryIntegration:
    """Integration tests for disaster recovery functionality"""
    
    def test_stack_dependencies(self, dr_stack, data_stack, security_stack):
        """Test that DR stack has proper dependencies"""
        # DR stack should depend on data and security stacks
        assert data_stack in dr_stack.dependencies
        # Note: In actual CDK, dependencies are managed differently
        # This is a conceptual test
    
    def test_resource_references(self, dr_stack):
        """Test that DR stack properly references other stack resources"""
        template = Template.from_stack(dr_stack)
        
        # Backup selections should reference DynamoDB tables and S3 buckets
        template.has_resource_properties("AWS::Backup::BackupSelection", {
            "Resources": Match.array_with([
                Match.string_like_regexp(r"arn:aws:dynamodb:.*:table/.*")
            ])
        })
        
        template.has_resource_properties("AWS::Backup::BackupSelection", {
            "Resources": Match.array_with([
                Match.string_like_regexp(r"arn:aws:s3:::.*")
            ])
        })
    
    def test_lambda_environment_variables(self, dr_stack):
        """Test that Lambda function has proper environment variables"""
        template = Template.from_stack(dr_stack)
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "Environment": {
                "Variables": {
                    "ENVIRONMENT": "dev",
                    "BACKUP_VAULT_NAME": Match.string_like_regexp(r"aquachain-vault-main-dev"),
                    "REPLICA_REGION": "us-west-2",
                    "SNS_TOPIC_ARN": Match.any_value()
                }
            }
        })

if __name__ == "__main__":
    pytest.main([__file__])