"""
AquaChain Audit Logging Stack
Kinesis Firehose for streaming audit logs to S3 with immutability
"""

from aws_cdk import (
    Stack,
    aws_kinesisfirehose as firehose,
    aws_s3 as s3,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class AuditLoggingStack(Stack):
    """
    Stack for audit logging infrastructure
    Includes Kinesis Firehose delivery stream and S3 bucket with Object Lock
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Dict[str, Any],
        kms_key: kms.Key,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.kms_key = kms_key
        
        # Create S3 bucket for audit log archival
        self._create_audit_archive_bucket()
        
        # Create IAM role for Firehose
        self._create_firehose_role()
        
        # Create Kinesis Firehose delivery stream
        self._create_firehose_stream()
        
        # Create CloudWatch log group for Firehose errors
        self._create_log_group()
    
    def _create_audit_archive_bucket(self) -> None:
        """
        Create S3 bucket for long-term audit log storage with Object Lock
        """
        from config.environment_config import get_resource_name
        
        # Create bucket with Object Lock enabled for immutability
        self.audit_archive_bucket = s3.Bucket(
            self,
            "AuditArchiveBucket",
            bucket_name=get_resource_name(
                self.config,
                "bucket",
                f"audit-archive-{self.account}"
            ),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            object_lock_enabled=True,
            # Set default retention to 7 years in compliance mode
            object_lock_default_retention=s3.ObjectLockRetention.compliance(
                Duration.days(2555)  # 7 years
            ),
            # Block all public access
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            # Always retain audit logs
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            # Lifecycle rules for cost optimization
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="TransitionToGlacier",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="TransitionToDeepArchive",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(730)  # 2 years
                        )
                    ]
                )
            ]
        )
        
        # Add bucket policy to enforce encryption
        self.audit_archive_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyUnencryptedObjectUploads",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:PutObject"],
                resources=[f"{self.audit_archive_bucket.bucket_arn}/*"],
                conditions={
                    "StringNotEquals": {
                        "s3:x-amz-server-side-encryption": "aws:kms"
                    }
                }
            )
        )
    
    def _create_firehose_role(self) -> None:
        """
        Create IAM role for Kinesis Firehose with necessary permissions
        """
        from config.environment_config import get_resource_name
        
        self.firehose_role = iam.Role(
            self,
            "FirehoseRole",
            role_name=get_resource_name(self.config, "role", "audit-firehose"),
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            description="Role for Kinesis Firehose to write audit logs to S3"
        )
        
        # Grant S3 write permissions
        self.audit_archive_bucket.grant_write(self.firehose_role)
        
        # Grant KMS permissions for encryption
        self.kms_key.grant_encrypt_decrypt(self.firehose_role)
        
        # Grant CloudWatch Logs permissions
        self.firehose_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/kinesisfirehose/*"
                ]
            )
        )
    
    def _create_firehose_stream(self) -> None:
        """
        Create Kinesis Firehose delivery stream for audit logs
        """
        from config.environment_config import get_resource_name
        
        # Create Firehose delivery stream
        self.firehose_stream = firehose.CfnDeliveryStream(
            self,
            "AuditLogStream",
            delivery_stream_name=get_resource_name(
                self.config,
                "stream",
                "audit-logs"
            ),
            delivery_stream_type="DirectPut",
            extended_s3_destination_configuration=firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=self.audit_archive_bucket.bucket_arn,
                role_arn=self.firehose_role.role_arn,
                # Partition logs by date for efficient querying
                prefix="audit-logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
                error_output_prefix="audit-logs-errors/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/!{firehose:error-output-type}/",
                # Buffer configuration
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=300,  # 5 minutes
                    size_in_m_bs=5  # 5 MB
                ),
                # Compression for cost savings
                compression_format="GZIP",
                # Encryption configuration
                encryption_configuration=firehose.CfnDeliveryStream.EncryptionConfigurationProperty(
                    kms_encryption_config=firehose.CfnDeliveryStream.KMSEncryptionConfigProperty(
                        awskms_key_arn=self.kms_key.key_arn
                    )
                ),
                # CloudWatch logging
                cloud_watch_logging_options=firehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                    enabled=True,
                    log_group_name="/aws/kinesisfirehose/audit-logs",
                    log_stream_name="S3Delivery"
                ),
                # Data format conversion (optional - keep as JSON)
                data_format_conversion_configuration=None,
                # S3 backup mode - disabled since we're already writing to S3
                s3_backup_mode="Disabled"
            )
        )
    
    def _create_log_group(self) -> None:
        """
        Create CloudWatch log group for Firehose delivery errors
        """
        self.log_group = logs.LogGroup(
            self,
            "FirehoseLogGroup",
            log_group_name="/aws/kinesisfirehose/audit-logs",
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create log stream
        logs.LogStream(
            self,
            "FirehoseLogStream",
            log_group=self.log_group,
            log_stream_name="S3Delivery",
            removal_policy=RemovalPolicy.DESTROY
        )
    
    @property
    def outputs(self) -> Dict[str, Any]:
        """
        Return stack outputs
        """
        # Create CloudFormation outputs
        CfnOutput(
            self,
            "AuditArchiveBucketName",
            value=self.audit_archive_bucket.bucket_name,
            description="S3 bucket for audit log archival with Object Lock"
        )
        
        CfnOutput(
            self,
            "FirehoseStreamName",
            value=self.firehose_stream.delivery_stream_name or "AuditLogStream",
            description="Kinesis Firehose delivery stream for audit logs"
        )
        
        CfnOutput(
            self,
            "FirehoseStreamArn",
            value=self.firehose_stream.attr_arn,
            description="ARN of Kinesis Firehose delivery stream"
        )
        
        return {
            "audit_archive_bucket": self.audit_archive_bucket,
            "firehose_stream": self.firehose_stream,
            "firehose_role": self.firehose_role,
            "log_group": self.log_group
        }
