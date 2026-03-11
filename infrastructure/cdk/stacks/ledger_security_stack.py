"""
CDK Stack for Ledger Security Infrastructure
Creates S3 bucket with Object Lock, KMS keys, and security policies
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_kms as kms,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns
)
from constructs import Construct
from typing import Dict, Any

class LedgerSecurityStack(Stack):
    """
    Stack for ledger security infrastructure including immutable S3 storage
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Environment
        env = kwargs.get('env_name', 'dev')
        
        # Create KMS key for ledger encryption
        self.ledger_kms_key = self._create_ledger_kms_key(env)
        
        # Create S3 bucket with Object Lock
        self.audit_archive_bucket = self._create_audit_archive_bucket(env)
        
        # Create ledger backup Lambda function
        self.backup_function = self._create_backup_function(env)
        
        # Create CloudWatch alarms for security monitoring
        self._create_security_alarms(env)
        
        # Create IAM policies for ledger immutability
        self._create_ledger_security_policies(env)
    
    def _create_ledger_kms_key(self, env: str) -> kms.Key:
        """
        Create KMS key for ledger encryption and signing
        """
        key_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="EnableIAMUserPermissions",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.AccountRootPrincipal()],
                    actions=["kms:*"],
                    resources=["*"]
                ),
                iam.PolicyStatement(
                    sid="AllowLedgerServiceAccess",
                    effect=iam.Effect.ALLOW,
                    principals=[
                        iam.ServicePrincipal("lambda.amazonaws.com")
                    ],
                    actions=[
                        "kms:Sign",
                        "kms:Verify",
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": f"dynamodb.{self.region}.amazonaws.com"
                        }
                    }
                )
            ]
        )
        
        ledger_key = kms.Key(
            self, f"LedgerKMSKey-{env}",
            description=f"KMS key for AquaChain ledger encryption and signing ({env})",
            key_policy=key_policy,
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN  # Never delete encryption keys
        )
        
        # Create alias
        kms.Alias(
            self, f"LedgerKMSKeyAlias-{env}",
            alias_name=f"alias/aquachain-ledger-key-{env}",
            target_key=ledger_key
        )
        
        return ledger_key
    
    def _create_audit_archive_bucket(self, env: str) -> s3.Bucket:
        """
        Create S3 bucket with Object Lock for immutable audit storage
        """
        bucket = s3.Bucket(
            self, f"AuditArchiveBucket-{env}",
            bucket_name=f"aquachain-audit-archive-{env}",
            
            # Enable Object Lock for immutability
            object_lock_enabled=True,
            object_lock_default_retention=s3.ObjectLockRetention.compliance(
                duration=Duration.days(365 * 7)  # 7 years retention
            ),
            
            # Encryption
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.ledger_kms_key,
            
            # Versioning (required for Object Lock)
            versioned=True,
            
            # Lifecycle management
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveOldVersions",
                    enabled=True,
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        ),
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            
            # Security
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            
            # Compliance
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Add bucket policy to prevent unauthorized access
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyInsecureConnections",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[
                    bucket.bucket_arn,
                    f"{bucket.bucket_arn}/*"
                ],
                conditions={
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            )
        )
        
        return bucket
    
    def _create_backup_function(self, env: str) -> lambda_.Function:
        """
        Create Lambda function for ledger backup service
        """
        backup_function = lambda_.Function(
            self, f"LedgerBackupFunction-{env}",
            function_name=f"aquachain-function-ledger-backup-service-{env}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/ledger_backup_service"),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "BACKUP_BUCKET": self.audit_archive_bucket.bucket_name,
                "LEDGER_TABLE": f"aquachain-ledger-{env}",
                "KMS_KEY_ID": self.ledger_kms_key.key_id
            }
        )
        
        # Grant permissions
        self.audit_archive_bucket.grant_read_write(backup_function)
        self.ledger_kms_key.grant_encrypt_decrypt(backup_function)
        
        # Grant DynamoDB access
        backup_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-ledger-{env}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-ledger-{env}/*"
                ]
            )
        )
        
        return backup_function
    
    def _create_security_alarms(self, env: str) -> None:
        """
        Create CloudWatch alarms for ledger security monitoring
        """
        # Create SNS topic for security alerts
        security_topic = sns.Topic(
            self, f"LedgerSecurityAlerts-{env}",
            topic_name=f"aquachain-ledger-security-alerts-{env}",
            display_name="AquaChain Ledger Security Alerts"
        )
        
        # Alarm for unauthorized ledger modifications
        ledger_modification_alarm = cloudwatch.Alarm(
            self, f"LedgerModificationAlarm-{env}",
            alarm_name=f"AquaChain-Ledger-Unauthorized-Modifications-{env}",
            alarm_description="Detects unauthorized modifications to ledger table",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ConditionalCheckFailedRequests",
                dimensions_map={
                    "TableName": f"aquachain-ledger-{env}"
                },
                statistic="Sum"
            ),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        ledger_modification_alarm.add_alarm_action(
            cw_actions.SnsAction(security_topic)
        )
        
        # Alarm for backup failures
        backup_failure_alarm = cloudwatch.Alarm(
            self, f"BackupFailureAlarm-{env}",
            alarm_name=f"AquaChain-Ledger-Backup-Failures-{env}",
            alarm_description="Detects failures in ledger backup process",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={
                    "FunctionName": f"aquachain-function-ledger-backup-service-{env}"
                },
                statistic="Sum"
            ),
            threshold=1,
            evaluation_periods=2,
            datapoints_to_alarm=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        backup_failure_alarm.add_alarm_action(
            cw_actions.SnsAction(security_topic)
        )
        
        # Alarm for high ledger creation rate (potential attack)
        high_creation_rate_alarm = cloudwatch.Alarm(
            self, f"HighLedgerCreationRateAlarm-{env}",
            alarm_name=f"AquaChain-Ledger-High-Creation-Rate-{env}",
            alarm_description="Detects unusually high ledger entry creation rate",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ConsumedWriteCapacityUnits",
                dimensions_map={
                    "TableName": f"aquachain-ledger-{env}"
                },
                statistic="Sum"
            ),
            threshold=1000,  # Adjust based on normal usage patterns
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        high_creation_rate_alarm.add_alarm_action(
            cw_actions.SnsAction(security_topic)
        )
    
    def _create_ledger_security_policies(self, env: str) -> None:
        """
        Create IAM policies for ledger security
        """
        # Policy to deny ledger modifications
        ledger_immutability_policy = iam.ManagedPolicy(
            self, f"LedgerImmutabilityPolicy-{env}",
            managed_policy_name=f"AquaChain-Ledger-Immutability-Policy-{env}",
            description="Prevents modifications to AquaChain ledger entries",
            statements=[
                iam.PolicyStatement(
                    sid="DenyLedgerModifications",
                    effect=iam.Effect.DENY,
                    actions=[
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem"
                    ],
                    resources=[
                        f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-ledger-{env}",
                        f"arn:aws:dynamodb:{self.region}:{self.account}:table/aquachain-ledger-{env}/*"
                    ]
                )
            ]
        )
        
        # Policy for audit archive access
        audit_archive_policy = iam.ManagedPolicy(
            self, f"AuditArchivePolicy-{env}",
            managed_policy_name=f"AquaChain-Audit-Archive-Policy-{env}",
            description="Controls access to audit archive bucket",
            statements=[
                iam.PolicyStatement(
                    sid="AllowAuditArchiveRead",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:GetObjectRetention",
                        "s3:GetObjectLegalHold"
                    ],
                    resources=[f"{self.audit_archive_bucket.bucket_arn}/*"]
                ),
                iam.PolicyStatement(
                    sid="AllowAuditArchiveList",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:ListBucket",
                        "s3:ListBucketVersions"
                    ],
                    resources=[self.audit_archive_bucket.bucket_arn]
                ),
                iam.PolicyStatement(
                    sid="DenyAuditArchiveModification",
                    effect=iam.Effect.DENY,
                    actions=[
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion",
                        "s3:PutObjectRetention",
                        "s3:PutObjectLegalHold"
                    ],
                    resources=[f"{self.audit_archive_bucket.bucket_arn}/*"]
                )
            ]
        )