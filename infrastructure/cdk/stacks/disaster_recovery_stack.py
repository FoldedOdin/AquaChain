"""
AquaChain Disaster Recovery Stack
Automated backup, cross-region replication, and disaster recovery procedures
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_backup as backup,
    aws_sns as sns,
    aws_cloudformation as cfn,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class AquaChainDisasterRecoveryStack(Stack):
    """
    Disaster Recovery stack for automated backup and cross-region replication
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 data_resources: Dict[str, Any], security_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.data_resources = data_resources
        self.security_resources = security_resources
        self.dr_resources = {}
        
        # Create backup vault and policies
        self._create_backup_infrastructure()
        
        # Set up cross-region replication
        self._create_cross_region_replication()
        
        # Create disaster recovery automation
        self._create_dr_automation()
        
        # Set up monitoring and testing
        self._create_dr_monitoring()
    
    def _create_backup_infrastructure(self) -> None:
        """
        Create AWS Backup vault and backup plans for all data stores
        """
        
        # Create backup vault with KMS encryption
        self.backup_vault = backup.BackupVault(
            self, "AquaChainBackupVault",
            backup_vault_name=get_resource_name(self.config, "vault", "main"),
            encryption_key=self.security_resources["data_key"],
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # Create backup role
        self.backup_role = iam.Role(
            self, "BackupServiceRole",
            role_name=get_resource_name(self.config, "role", "backup-service"),
            assumed_by=iam.ServicePrincipal("backup.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBackupServiceRolePolicyForBackup"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBackupServiceRolePolicyForRestores")
            ]
        )
        
        # Create backup plan for DynamoDB tables
        self.dynamodb_backup_plan = backup.BackupPlan(
            self, "DynamoDBBackupPlan",
            backup_plan_name=get_resource_name(self.config, "plan", "dynamodb"),
            backup_vault=self.backup_vault
        )
        
        # Add backup rules based on environment
        if self.config["environment"] == "prod":
            # Production: Daily backups with 35-day retention
            self.dynamodb_backup_plan.add_rule(backup.BackupPlanRule(
                backup_vault=self.backup_vault,
                rule_name="DailyBackups",
                schedule_expression=events.Schedule.cron(hour="2", minute="0"),  # 2 AM daily
                start_window=Duration.hours(1),
                completion_window=Duration.hours(2),
                delete_after=Duration.days(self.config.get("backup_config", {}).get("backup_retention_days", 35)),
                copy_actions=[
                    backup.BackupPlanCopyActionProps(
                        destination_backup_vault=backup.BackupVault.from_backup_vault_name(
                            self, "CrossRegionVault",
                            f"{get_resource_name(self.config, 'vault', 'main')}-{self.config['replica_region']}"
                        ),
                        delete_after=Duration.days(35)
                    )
                ] if self.config.get("backup_config", {}).get("enable_cross_region_backup") else None
            ))
            
            # Continuous backup for critical tables
            if self.config.get("backup_config", {}).get("enable_continuous_backup"):
                self.dynamodb_backup_plan.add_rule(backup.BackupPlanRule(
                    backup_vault=self.backup_vault,
                    rule_name="ContinuousBackups",
                    schedule_expression=events.Schedule.cron(minute="0"),  # Hourly
                    start_window=Duration.minutes(30),
                    completion_window=Duration.hours(1),
                    delete_after=Duration.days(7)  # Keep hourly backups for 7 days
                ))
        else:
            # Dev/Staging: Weekly backups with 7-day retention
            self.dynamodb_backup_plan.add_rule(backup.BackupPlanRule(
                backup_vault=self.backup_vault,
                rule_name="WeeklyBackups",
                schedule_expression=events.Schedule.cron(hour="2", minute="0", week_day="SUN"),
                start_window=Duration.hours(1),
                completion_window=Duration.hours(2),
                delete_after=Duration.days(7)
            ))
        
        # Create backup selections for DynamoDB tables
        critical_tables = [
            self.data_resources["ledger_table"].table_arn,
            self.data_resources["readings_table"].table_arn,
            self.data_resources["users_table"].table_arn,
            self.data_resources["service_requests_table"].table_arn
        ]
        
        backup.BackupSelection(
            self, "DynamoDBBackupSelection",
            backup_plan=self.dynamodb_backup_plan,
            resources=[backup.BackupResource.from_arns(critical_tables)],
            backup_selection_name="CriticalDynamoDBTables",
            role=self.backup_role
        )
        
        # Create S3 backup plan for critical buckets
        self.s3_backup_plan = backup.BackupPlan(
            self, "S3BackupPlan",
            backup_plan_name=get_resource_name(self.config, "plan", "s3"),
            backup_vault=self.backup_vault
        )
        
        self.s3_backup_plan.add_rule(backup.BackupPlanRule(
            backup_vault=self.backup_vault,
            rule_name="S3DailyBackups",
            schedule_expression=events.Schedule.cron(hour="3", minute="0"),  # 3 AM daily
            start_window=Duration.hours(1),
            completion_window=Duration.hours(3),
            delete_after=Duration.days(30)
        ))
        
        # Backup selection for S3 buckets
        critical_buckets = [
            self.data_resources["audit_bucket"].bucket_arn,
            self.data_resources["ml_models_bucket"].bucket_arn
        ]
        
        backup.BackupSelection(
            self, "S3BackupSelection",
            backup_plan=self.s3_backup_plan,
            resources=[backup.BackupResource.from_arns(critical_buckets)],
            backup_selection_name="CriticalS3Buckets",
            role=self.backup_role
        )
        
        self.dr_resources.update({
            "backup_vault": self.backup_vault,
            "backup_role": self.backup_role,
            "dynamodb_backup_plan": self.dynamodb_backup_plan,
            "s3_backup_plan": self.s3_backup_plan
        })
    
    def _create_cross_region_replication(self) -> None:
        """
        Set up cross-region replication for critical data
        """
        
        # Create replication bucket in secondary region (conceptual - would be deployed separately)
        replica_region = self.config.get("replica_region", "us-west-2")
        
        # S3 Cross-Region Replication for audit trail
        if self.config.get("replica_account_id"):
            # Create replication role
            self.replication_role = iam.Role(
                self, "S3ReplicationRole",
                role_name=get_resource_name(self.config, "role", "s3-replication"),
                assumed_by=iam.ServicePrincipal("s3.amazonaws.com"),
                inline_policies={
                    "ReplicationPolicy": iam.PolicyDocument(
                        statements=[
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "s3:GetObjectVersionForReplication",
                                    "s3:GetObjectVersionAcl",
                                    "s3:GetObjectVersionTagging"
                                ],
                                resources=[f"{self.data_resources['audit_bucket'].bucket_arn}/*"]
                            ),
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "s3:ListBucket"
                                ],
                                resources=[self.data_resources["audit_bucket"].bucket_arn]
                            ),
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "s3:ReplicateObject",
                                    "s3:ReplicateDelete",
                                    "s3:ReplicateTags"
                                ],
                                resources=[
                                    f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'audit-replica-{self.config['replica_account_id']}')}/*"
                                ]
                            ),
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "kms:Decrypt",
                                    "kms:GenerateDataKey"
                                ],
                                resources=[
                                    self.security_resources["data_key"].key_arn,
                                    f"arn:aws:kms:{replica_region}:{self.config['replica_account_id']}:key/*"
                                ]
                            )
                        ]
                    )
                }
            )
            
            # Configure replication on audit bucket
            audit_bucket = self.data_resources["audit_bucket"]
            cfn_bucket = audit_bucket.node.default_child
            cfn_bucket.replication_configuration = {
                "Role": self.replication_role.role_arn,
                "Rules": [
                    {
                        "Id": "ReplicateToSecondaryRegion",
                        "Status": "Enabled",
                        "Prefix": "",
                        "Destination": {
                            "Bucket": f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'audit-replica-{self.config['replica_account_id']}')}",
                            "StorageClass": "STANDARD_IA",
                            "EncryptionConfiguration": {
                                "ReplicaKmsKeyID": f"arn:aws:kms:{replica_region}:{self.config['replica_account_id']}:key/replica-key-id"
                            }
                        }
                    }
                ]
            }
            
            self.dr_resources["replication_role"] = self.replication_role
        
        # DynamoDB Global Tables for critical data (if enabled)
        if self.config["environment"] == "prod" and self.config.get("enable_global_tables"):
            # Note: Global Tables would be configured through separate deployment
            # This is a placeholder for the configuration
            pass
    
    def _create_dr_automation(self) -> None:
        """
        Create disaster recovery automation using Step Functions
        """
        
        # Create Lambda function for DR operations
        self.dr_lambda = lambda_.Function(
            self, "DisasterRecoveryFunction",
            function_name=get_resource_name(self.config, "function", "disaster-recovery"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/disaster_recovery"),
            timeout=Duration.minutes(15),
            memory_size=512,
            environment={
                "ENVIRONMENT": self.config["environment"],
                "BACKUP_VAULT_NAME": self.backup_vault.backup_vault_name,
                "REPLICA_REGION": self.config.get("replica_region", "us-west-2"),
                "SNS_TOPIC_ARN": self._create_dr_notifications().topic_arn
            },
            role=self._create_dr_lambda_role()
        )
        
        # Create Step Function for DR workflow
        self.dr_state_machine = self._create_dr_state_machine()
        
        # Schedule regular DR tests
        if self.config["environment"] in ["staging", "prod"]:
            self.dr_test_rule = events.Rule(
                self, "DRTestSchedule",
                rule_name=get_resource_name(self.config, "rule", "dr-test"),
                description="Schedule regular disaster recovery tests",
                schedule=events.Schedule.cron(
                    hour="4",  # 4 AM
                    minute="0",
                    week_day="SAT"  # Weekly on Saturday
                ),
                targets=[
                    targets.SfnStateMachine(
                        self.dr_state_machine,
                        input=events.RuleTargetInput.from_object({
                            "operation": "test",
                            "environment": self.config["environment"]
                        })
                    )
                ]
            )
        
        self.dr_resources.update({
            "dr_lambda": self.dr_lambda,
            "dr_state_machine": self.dr_state_machine
        })
    
    def _create_dr_lambda_role(self) -> iam.Role:
        """
        Create IAM role for disaster recovery Lambda function
        """
        return iam.Role(
            self, "DRLambdaRole",
            role_name=get_resource_name(self.config, "role", "dr-lambda"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "DROperations": iam.PolicyDocument(
                    statements=[
                        # Backup operations
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "backup:StartBackupJob",
                                "backup:StartRestoreJob",
                                "backup:DescribeBackupJob",
                                "backup:DescribeRestoreJob",
                                "backup:ListBackupJobs",
                                "backup:ListRestoreJobs"
                            ],
                            resources=["*"]
                        ),
                        # DynamoDB operations
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:CreateBackup",
                                "dynamodb:DescribeBackup",
                                "dynamodb:ListBackups",
                                "dynamodb:RestoreTableFromBackup",
                                "dynamodb:DescribeTable",
                                "dynamodb:CreateTable",
                                "dynamodb:UpdateTable"
                            ],
                            resources=["*"]
                        ),
                        # S3 operations
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:ListBucket",
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:GetBucketVersioning",
                                "s3:GetBucketReplication"
                            ],
                            resources=["*"]
                        ),
                        # SNS for notifications
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sns:Publish"
                            ],
                            resources=["*"]
                        ),
                        # CloudFormation for stack operations
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "cloudformation:DescribeStacks",
                                "cloudformation:DescribeStackResources",
                                "cloudformation:CreateStack",
                                "cloudformation:UpdateStack"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
    
    def _create_dr_notifications(self) -> sns.Topic:
        """
        Create SNS topic for disaster recovery notifications
        """
        dr_topic = sns.Topic(
            self, "DRNotificationsTopic",
            topic_name=get_resource_name(self.config, "topic", "dr-notifications"),
            display_name="AquaChain Disaster Recovery Notifications"
        )
        
        # Add email subscriptions
        for email in self.config.get("notification_channels", {}).get("email", []):
            sns.Subscription(
                self, f"DREmailSubscription-{email.replace('@', '-').replace('.', '-')}",
                topic=dr_topic,
                endpoint=email,
                protocol=sns.SubscriptionProtocol.EMAIL
            )
        
        return dr_topic
    
    def _create_dr_state_machine(self) -> sfn.StateMachine:
        """
        Create Step Function state machine for disaster recovery workflow
        """
        
        # Define tasks
        validate_backups_task = sfn_tasks.LambdaInvoke(
            self, "ValidateBackups",
            lambda_function=self.dr_lambda,
            payload=sfn.TaskInput.from_object({
                "operation": "validate_backups",
                "environment": self.config["environment"]
            }),
            result_path="$.validateResult"
        )
        
        test_restore_task = sfn_tasks.LambdaInvoke(
            self, "TestRestore",
            lambda_function=self.dr_lambda,
            payload=sfn.TaskInput.from_object({
                "operation": "test_restore",
                "environment": self.config["environment"]
            }),
            result_path="$.restoreResult"
        )
        
        cleanup_test_task = sfn_tasks.LambdaInvoke(
            self, "CleanupTest",
            lambda_function=self.dr_lambda,
            payload=sfn.TaskInput.from_object({
                "operation": "cleanup_test",
                "environment": self.config["environment"]
            }),
            result_path="$.cleanupResult"
        )
        
        notify_success_task = sfn_tasks.SnsPublish(
            self, "NotifySuccess",
            topic=self._create_dr_notifications(),
            message=sfn.TaskInput.from_json_path_at("$.successMessage")
        )
        
        notify_failure_task = sfn_tasks.SnsPublish(
            self, "NotifyFailure",
            topic=self._create_dr_notifications(),
            message=sfn.TaskInput.from_json_path_at("$.errorMessage")
        )
        
        # Define workflow
        success_state = sfn.Succeed(self, "DRTestSuccess")
        failure_state = sfn.Fail(self, "DRTestFailure")
        
        # Chain the tasks
        definition = validate_backups_task.next(
            sfn.Choice(self, "BackupsValid")
            .when(
                sfn.Condition.string_equals("$.validateResult.Payload.status", "success"),
                test_restore_task.next(
                    sfn.Choice(self, "RestoreSuccessful")
                    .when(
                        sfn.Condition.string_equals("$.restoreResult.Payload.status", "success"),
                        cleanup_test_task.next(
                            notify_success_task.next(success_state)
                        )
                    )
                    .otherwise(
                        notify_failure_task.next(failure_state)
                    )
                )
            )
            .otherwise(
                notify_failure_task.next(failure_state)
            )
        )
        
        return sfn.StateMachine(
            self, "DRStateMachine",
            state_machine_name=get_resource_name(self.config, "statemachine", "disaster-recovery"),
            definition=definition,
            timeout=Duration.hours(2)
        )
    
    def _create_dr_monitoring(self) -> None:
        """
        Create monitoring and alerting for disaster recovery operations
        """
        
        # CloudWatch alarms for backup failures
        backup_failure_alarm = self.backup_vault.metric_number_of_backup_jobs_failed().create_alarm(
            self, "BackupFailureAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "backup-failures"),
            alarm_description="Alert when backup jobs fail",
            threshold=1,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        # Add alarm action to notify DR team
        dr_topic = self._create_dr_notifications()
        backup_failure_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(dr_topic)
        )
        
        # Custom metrics for DR test results
        self.dr_test_metric = cloudwatch.Metric(
            namespace="AquaChain/DisasterRecovery",
            metric_name="TestResults",
            dimensions_map={
                "Environment": self.config["environment"]
            }
        )
        
        # Alarm for DR test failures
        dr_test_alarm = self.dr_test_metric.create_alarm(
            self, "DRTestFailureAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "dr-test-failures"),
            alarm_description="Alert when DR tests fail",
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        dr_test_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(dr_topic)
        )
        
        self.dr_resources.update({
            "backup_failure_alarm": backup_failure_alarm,
            "dr_test_alarm": dr_test_alarm,
            "dr_notifications_topic": dr_topic
        })
        
        # Output important values
        CfnOutput(
            self, "BackupVaultName",
            value=self.backup_vault.backup_vault_name,
            description="AWS Backup vault for AquaChain data"
        )
        
        CfnOutput(
            self, "DRStateMachineArn",
            value=self.dr_state_machine.state_machine_arn,
            description="Step Function for disaster recovery automation"
        )
        
        CfnOutput(
            self, "DRNotificationsTopicArn",
            value=dr_topic.topic_arn,
            description="SNS topic for disaster recovery notifications"
        )