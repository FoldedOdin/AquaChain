"""
AquaChain Security Audit Stack
Enhanced audit logging infrastructure with DynamoDB tables and Lambda services
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_kms as kms,
    aws_apigateway as apigw,
)
from constructs import Construct
from typing import Dict, Any


class SecurityAuditStack(Stack):
    """
    Stack for enhanced security audit logging infrastructure
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
        
        # Create DynamoDB tables
        self._create_security_audit_logs_table()
        self._create_integrity_hashes_table()
        self._create_sessions_table()
        self._create_session_blacklist_table()
        
        # Create S3 bucket for exports
        self._create_export_bucket()
        
        # Create Lambda function
        self._create_security_audit_lambda()
    
    def _create_security_audit_logs_table(self) -> None:
        """
        Create DynamoDB table for security audit logs with partition sharding
        """
        self.security_audit_logs_table = dynamodb.Table(
            self,
            "SecurityAuditLogsTable",
            table_name=f"AquaChain-SecurityAuditLogs-{self.config['environment']}",
            partition_key=dynamodb.Attribute(
                name="logId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for device ID queries
        self.security_audit_logs_table.add_global_secondary_index(
            index_name="DeviceIdIndex",
            partition_key=dynamodb.Attribute(
                name="deviceId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for anomaly type queries
        self.security_audit_logs_table.add_global_secondary_index(
            index_name="AnomalyTypeIndex",
            partition_key=dynamodb.Attribute(
                name="anomalyType",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
    
    def _create_integrity_hashes_table(self) -> None:
        """
        Create DynamoDB table for daily hash chain storage
        """
        self.integrity_hashes_table = dynamodb.Table(
            self,
            "IntegrityHashesTable",
            table_name=f"AquaChain-IntegrityHashes-{self.config['environment']}",
            partition_key=dynamodb.Attribute(
                name="date",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN
        )
    
    def _create_sessions_table(self) -> None:
        """
        Create DynamoDB table for session tracking
        """
        self.sessions_table = dynamodb.Table(
            self,
            "SessionsTable",
            table_name=f"AquaChain-Sessions-{self.config['environment']}",
            partition_key=dynamodb.Attribute(
                name="sessionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            time_to_live_attribute="expiryTimestamp",
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Add GSI for user session queries
        self.sessions_table.add_global_secondary_index(
            index_name="UserSessionsIndex",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="createdAt",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
    
    def _create_session_blacklist_table(self) -> None:
        """
        Create DynamoDB table for session blacklist (Redis fallback)
        """
        self.session_blacklist_table = dynamodb.Table(
            self,
            "SessionBlacklistTable",
            table_name=f"AquaChain-SessionBlacklist-{self.config['environment']}",
            partition_key=dynamodb.Attribute(
                name="tokenHash",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY
        )
    
    def _create_export_bucket(self) -> None:
        """
        Create S3 bucket for audit log exports
        """
        self.export_bucket = s3.Bucket(
            self,
            "AuditExportBucket",
            bucket_name=f"aquachain-audit-exports-{self.config['environment']}-{self.account}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldExports",
                    enabled=True,
                    expiration=Duration.days(7)
                )
            ]
        )
    
    def _create_security_audit_lambda(self) -> None:
        """
        Create Lambda function for security audit operations
        """
        self.security_audit_lambda = lambda_.Function(
            self,
            "SecurityAuditLambda",
            function_name=f"AquaChain-SecurityAudit-{self.config['environment']}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda/security_audit_service"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "AUDIT_LOGS_TABLE": self.security_audit_logs_table.table_name,
                "INTEGRITY_HASHES_TABLE": self.integrity_hashes_table.table_name,
                "SESSIONS_TABLE": self.sessions_table.table_name,
                "SESSION_BLACKLIST_TABLE": self.session_blacklist_table.table_name,
                "EXPORT_BUCKET": self.export_bucket.bucket_name,
                "ENVIRONMENT": self.config['environment']
            }
        )
        
        # Grant permissions
        self.security_audit_logs_table.grant_read_write_data(self.security_audit_lambda)
        self.integrity_hashes_table.grant_read_write_data(self.security_audit_lambda)
        self.sessions_table.grant_read_write_data(self.security_audit_lambda)
        self.session_blacklist_table.grant_read_write_data(self.security_audit_lambda)
        self.export_bucket.grant_read_write(self.security_audit_lambda)
        self.kms_key.grant_encrypt_decrypt(self.security_audit_lambda)
    
    @property
    def outputs(self) -> Dict[str, Any]:
        """
        Return stack outputs
        """
        CfnOutput(
            self,
            "SecurityAuditLogsTableName",
            value=self.security_audit_logs_table.table_name,
            description="Security audit logs DynamoDB table"
        )
        
        CfnOutput(
            self,
            "IntegrityHashesTableName",
            value=self.integrity_hashes_table.table_name,
            description="Integrity hashes DynamoDB table"
        )
        
        CfnOutput(
            self,
            "SecurityAuditLambdaArn",
            value=self.security_audit_lambda.function_arn,
            description="Security audit Lambda function ARN"
        )
        
        return {
            "security_audit_logs_table": self.security_audit_logs_table,
            "integrity_hashes_table": self.integrity_hashes_table,
            "sessions_table": self.sessions_table,
            "session_blacklist_table": self.session_blacklist_table,
            "export_bucket": self.export_bucket,
            "security_audit_lambda": self.security_audit_lambda
        }
