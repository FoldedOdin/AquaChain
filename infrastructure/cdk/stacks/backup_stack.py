"""
Backup Stack for AquaChain
Automated DynamoDB backups with verification and retention
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class AquaChainBackupStack(Stack):
    """
    Automated backup stack with scheduling and monitoring
    """
    
    def __init__(self, scope: Construct, construct_id: str, 
                 config: Dict[str, Any], 
                 data_resources: Dict[str, Any] = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.data_resources = data_resources or {}
        
        self.config = config
        
        # Create SNS topic for notifications
        self.backup_notifications_topic = self._create_notification_topic()
        
        # Create backup Lambda function
        self.backup_function = self._create_backup_function()
        
        # Create EventBridge rules for scheduling
        self._create_backup_schedules()
        
        # Create outputs
        self._create_outputs()
    
    def _create_notification_topic(self) -> sns.Topic:
        """
        Create SNS topic for backup notifications
        """
        topic = sns.Topic(
            self, "BackupNotificationsTopic",
            topic_name=f"aquachain-backup-notifications-{self.config['environment']}",
            display_name="AquaChain Backup Notifications"
        )
        
        # Subscribe email if configured
        if self.config.get('alert_email'):
            topic.add_subscription(
                subscriptions.EmailSubscription(self.config['alert_email'])
            )
        
        return topic
    
    def _create_backup_function(self) -> _lambda.Function:
        """
        Create Lambda function for backup management
        """
        # Create IAM role
        backup_role = iam.Role(
            self, "BackupFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Add DynamoDB backup permissions
        backup_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:CreateBackup",
                    "dynamodb:DescribeBackup",
                    "dynamodb:ListBackups",
                    "dynamodb:DeleteBackup",
                    "dynamodb:RestoreTableFromBackup",
                    "dynamodb:DescribeTable",
                    "dynamodb:DeleteTable"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-*",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-*/backup/*"
                ]
            )
        )
        
        # Add SNS publish permissions
        backup_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sns:Publish"],
                resources=[self.backup_notifications_topic.topic_arn]
            )
        )
        
        # Create Lambda function
        backup_function = _lambda.Function(
            self, "BackupFunction",
            function_name=f"aquachain-backup-{self.config['environment']}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="automated_backup_handler.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/backup"),
            role=backup_role,
            timeout=Duration.minutes(15),
            memory_size=512,
            environment={
                "ENVIRONMENT": self.config['environment'],
                "BACKUP_RETENTION_DAYS": "30",
                "SNS_TOPIC_ARN": self.backup_notifications_topic.topic_arn
            },
            description="Automated DynamoDB backup management"
        )
        
        return backup_function
    
    def _create_backup_schedules(self):
        """
        Create EventBridge rules for backup scheduling
        """
        # Daily backup at 2 AM UTC
        daily_backup_rule = events.Rule(
            self, "DailyBackupRule",
            rule_name=f"aquachain-daily-backup-{self.config['environment']}",
            schedule=events.Schedule.cron(
                hour="2",
                minute="0"
            ),
            description="Daily DynamoDB backup at 2 AM UTC"
        )
        
        daily_backup_rule.add_target(
            targets.LambdaFunction(
                self.backup_function,
                event=events.RuleTargetInput.from_object({
                    "action": "create_backups"
                })
            )
        )
        
        # Backup verification at 3 AM UTC (after backups complete)
        verification_rule = events.Rule(
            self, "BackupVerificationRule",
            rule_name=f"aquachain-backup-verification-{self.config['environment']}",
            schedule=events.Schedule.cron(
                hour="3",
                minute="0"
            ),
            description="Verify backups after creation"
        )
        
        verification_rule.add_target(
            targets.LambdaFunction(
                self.backup_function,
                event=events.RuleTargetInput.from_object({
                    "action": "verify_backups"
                })
            )
        )
        
        # Weekly cleanup on Sundays at 4 AM UTC
        cleanup_rule = events.Rule(
            self, "BackupCleanupRule",
            rule_name=f"aquachain-backup-cleanup-{self.config['environment']}",
            schedule=events.Schedule.cron(
                hour="4",
                minute="0",
                week_day="SUN"
            ),
            description="Weekly cleanup of old backups"
        )
        
        cleanup_rule.add_target(
            targets.LambdaFunction(
                self.backup_function,
                event=events.RuleTargetInput.from_object({
                    "action": "cleanup_old_backups"
                })
            )
        )
        
        # Monthly restore test on 1st of month at 5 AM UTC
        restore_test_rule = events.Rule(
            self, "RestoreTestRule",
            rule_name=f"aquachain-restore-test-{self.config['environment']}",
            schedule=events.Schedule.cron(
                hour="5",
                minute="0",
                day="1"
            ),
            description="Monthly backup restore test"
        )
        
        restore_test_rule.add_target(
            targets.LambdaFunction(
                self.backup_function,
                event=events.RuleTargetInput.from_object({
                    "action": "test_restore",
                    "table_name": "aquachain-readings"
                })
            )
        )
    
    def _create_outputs(self):
        """
        Export backup stack information
        """
        CfnOutput(
            self, "BackupFunctionArn",
            value=self.backup_function.function_arn,
            export_name=f"{Stack.of(self).stack_name}-BackupFunctionArn",
            description="Backup Lambda function ARN"
        )
        
        CfnOutput(
            self, "BackupNotificationsTopicArn",
            value=self.backup_notifications_topic.topic_arn,
            export_name=f"{Stack.of(self).stack_name}-BackupNotificationsTopicArn",
            description="Backup notifications SNS topic ARN"
        )
