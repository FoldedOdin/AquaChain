"""
GDPR Compliance Stack
S3 buckets, DynamoDB tables, and Lambda functions for GDPR compliance
"""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class GDPRComplianceStack(Stack):
    """
    Stack for GDPR compliance resources including data export,
    deletion, consent management, and audit logging.
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
        self.gdpr_resources = {}
        
        # Create S3 buckets for GDPR operations
        self._create_gdpr_buckets()
        
        # Create DynamoDB tables for GDPR tracking
        self._create_gdpr_tables()
        
        # Output important values
        self._create_outputs()
    
    def _create_gdpr_buckets(self) -> None:
        """
        Create S3 buckets for GDPR data exports and compliance reports.
        """
        
        # GDPR Data Export Bucket
        self.export_bucket = s3.Bucket(
            self, "GDPRExportBucket",
            bucket_name=f"aquachain-gdpr-exports-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldExports",
                    enabled=True,
                    expiration=Duration.days(30),  # Auto-delete after 30 days
                    noncurrent_version_expiration=Duration.days(7)
                )
            ],
            removal_policy=RemovalPolicy.RETAIN if self.config.get("environment") == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=False if self.config.get("environment") == "prod" else True
        )
        
        # Add CORS configuration for frontend access
        self.export_bucket.add_cors_rule(
            allowed_methods=[s3.HttpMethods.GET],
            allowed_origins=["*"],  # Should be restricted to your domain in production
            allowed_headers=["*"],
            max_age=3000
        )
        
        # Compliance Reports Bucket
        self.compliance_bucket = s3.Bucket(
            self, "ComplianceReportsBucket",
            bucket_name=f"aquachain-compliance-reports-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveOldReports",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.RETAIN,  # Always retain compliance reports
            auto_delete_objects=False
        )
        
        self.gdpr_resources.update({
            "export_bucket": self.export_bucket,
            "compliance_bucket": self.compliance_bucket
        })
    
    def _create_gdpr_tables(self) -> None:
        """
        Create DynamoDB tables for GDPR request tracking and consent management.
        """
        
        # GDPR Requests Table
        self.gdpr_requests_table = dynamodb.Table(
            self, "GDPRRequestsTable",
            table_name=f"aquachain-gdpr-requests-{self.config.get('environment', 'dev')}",
            partition_key=dynamodb.Attribute(
                name="request_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config.get("environment") == "prod" else RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for querying by user
        self.gdpr_requests_table.add_global_secondary_index(
            index_name="user_id-created_at-index",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for querying by status
        self.gdpr_requests_table.add_global_secondary_index(
            index_name="status-created_at-index",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # User Consents Table
        self.user_consents_table = dynamodb.Table(
            self, "UserConsentsTable",
            table_name=f"aquachain-user-consents-{self.config.get('environment', 'dev')}",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config.get("environment") == "prod" else RemovalPolicy.DESTROY
        )
        
        # GSI for querying consents by type and timestamp
        self.user_consents_table.add_global_secondary_index(
            index_name="consent_type-updated_at-index",
            partition_key=dynamodb.Attribute(
                name="consent_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Audit Logs Table (for comprehensive audit trail)
        self.audit_logs_table = dynamodb.Table(
            self, "AuditLogsTable",
            table_name=f"aquachain-audit-logs-{self.config.get('environment', 'dev')}",
            partition_key=dynamodb.Attribute(
                name="log_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN,  # Always retain audit logs
            time_to_live_attribute="ttl"  # 7 years retention via TTL
        )
        
        # GSI for querying by user
        self.audit_logs_table.add_global_secondary_index(
            index_name="user_id-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for querying by action type
        self.audit_logs_table.add_global_secondary_index(
            index_name="action_type-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="action_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for querying by resource
        self.audit_logs_table.add_global_secondary_index(
            index_name="resource_type-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="resource_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.gdpr_resources.update({
            "gdpr_requests_table": self.gdpr_requests_table,
            "user_consents_table": self.user_consents_table,
            "audit_logs_table": self.audit_logs_table
        })
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for important resources."""
        
        CfnOutput(
            self, "ExportBucketName",
            value=self.export_bucket.bucket_name,
            description="S3 bucket for GDPR data exports",
            export_name=f"GDPRExportBucket-{self.config.get('environment', 'dev')}"
        )
        
        CfnOutput(
            self, "ExportBucketArn",
            value=self.export_bucket.bucket_arn,
            description="ARN of GDPR export bucket"
        )
        
        CfnOutput(
            self, "ComplianceBucketName",
            value=self.compliance_bucket.bucket_name,
            description="S3 bucket for compliance reports",
            export_name=f"ComplianceBucket-{self.config.get('environment', 'dev')}"
        )
        
        CfnOutput(
            self, "GDPRRequestsTableName",
            value=self.gdpr_requests_table.table_name,
            description="DynamoDB table for GDPR requests",
            export_name=f"GDPRRequestsTable-{self.config.get('environment', 'dev')}"
        )
        
        CfnOutput(
            self, "UserConsentsTableName",
            value=self.user_consents_table.table_name,
            description="DynamoDB table for user consents",
            export_name=f"UserConsentsTable-{self.config.get('environment', 'dev')}"
        )
        
        CfnOutput(
            self, "AuditLogsTableName",
            value=self.audit_logs_table.table_name,
            description="DynamoDB table for audit logs",
            export_name=f"AuditLogsTable-{self.config.get('environment', 'dev')}"
        )
    
    def grant_export_access(self, grantee: iam.IGrantable) -> None:
        """
        Grant Lambda function access to export bucket and GDPR tables.
        
        Args:
            grantee: The IAM principal to grant access to
        """
        # Grant S3 permissions
        self.export_bucket.grant_read_write(grantee)
        
        # Grant DynamoDB permissions
        self.gdpr_requests_table.grant_read_write_data(grantee)
        self.user_consents_table.grant_read_data(grantee)
        self.audit_logs_table.grant_read_data(grantee)
    
    def grant_compliance_access(self, grantee: iam.IGrantable) -> None:
        """
        Grant Lambda function access to compliance bucket.
        
        Args:
            grantee: The IAM principal to grant access to
        """
        self.compliance_bucket.grant_read_write(grantee)
        self.audit_logs_table.grant_read_data(grantee)
        self.gdpr_requests_table.grant_read_data(grantee)
