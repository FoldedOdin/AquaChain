"""
AquaChain Data Stack
DynamoDB tables, S3 buckets, and IoT Core configuration
"""

from aws_cdk import (
    Stack,
    Tags,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iot as iot,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class AquaChainDataStack(Stack):
    """
    Data layer stack containing DynamoDB, S3, and IoT Core resources
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], 
                 kms_key: kms.Key, ledger_signing_key: kms.Key, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.kms_key = kms_key
        self.ledger_signing_key = ledger_signing_key
        self.data_resources = {}
        
        # Create DynamoDB tables
        self._create_dynamodb_tables()
        
        # Create S3 buckets
        self._create_s3_buckets()
        
        # Create IoT Core resources
        self._create_iot_resources()
    
    def _create_dynamodb_tables(self) -> None:
        """
        Create DynamoDB tables for readings, ledger, and metadata
        """
        
        # Readings table with time-windowed partitions
        self.readings_table = dynamodb.Table(
            self, "ReadingsTable",
            table_name=get_resource_name(self.config, "table", "readings"),
            partition_key=dynamodb.Attribute(
                name="deviceId_month",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: Protect IoT data from accidental deletion
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute="ttl"
        )
        
        # Add GSI for device queries
        self.readings_table.add_global_secondary_index(
            index_name="DeviceIndex",
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
        
        # GSI for querying by device and metric type (Phase 4 optimization)
        self.readings_table.add_global_secondary_index(
            index_name="device_id-metric_type-index",
            partition_key=dynamodb.Attribute(
                name="deviceId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="metric_type",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for querying by alert level and timestamp (Phase 4 optimization)
        self.readings_table.add_global_secondary_index(
            index_name="alert_level-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="alert_level",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Ledger table for immutable records
        self.ledger_table = dynamodb.Table(
            self, "LedgerTable",
            table_name=get_resource_name(self.config, "table", "ledger"),
            partition_key=dynamodb.Attribute(
                name="GLOBAL_SEQUENCE",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="sequenceNumber",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: CRITICAL - Ledger must never be deleted
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # Sequence generator table
        self.sequence_table = dynamodb.Table(
            self, "SequenceTable",
            table_name=get_resource_name(self.config, "table", "sequence"),
            partition_key=dynamodb.Attribute(
                name="sequenceType",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
        read_capacity=5,
        write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN  # ✅ SECURITY FIX: Protect sequence numbers
        )
        
        # Users table
        self.users_table = dynamodb.Table(
            self, "UsersTable",
            table_name=get_resource_name(self.config, "table", "users"),
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
        read_capacity=5,
        write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN  # ✅ SECURITY FIX: Protect user PII data
        )
        
        # GSI for email lookup (Phase 4 optimization)
        self.users_table.add_global_secondary_index(
            index_name="email-index",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for organization and role queries (Phase 4 optimization)
        self.users_table.add_global_secondary_index(
            index_name="organization_id-role-index",
            partition_key=dynamodb.Attribute(
                name="organization_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="role",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Service requests table
        self.service_requests_table = dynamodb.Table(
            self, "ServiceRequestsTable",
            table_name=get_resource_name(self.config, "table", "service-requests"),
            partition_key=dynamodb.Attribute(
                name="requestId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
        read_capacity=5,
        write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN  # ✅ SECURITY FIX: Protect service history
        )
        
        # Add GSI for technician queries
        self.service_requests_table.add_global_secondary_index(
            index_name="TechnicianIndex",
            partition_key=dynamodb.Attribute(
                name="technicianId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Devices table with GSIs for Phase 4 optimization
        self.devices_table = dynamodb.Table(
            self, "DevicesTable",
            table_name=get_resource_name(self.config, "table", "devices"),
            partition_key=dynamodb.Attribute(
                name="device_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
        read_capacity=5,
        write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: Protect device registry
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI 1: user_id-created_at-index for querying devices by user
        self.devices_table.add_global_secondary_index(
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
        
        # GSI 2: status-last_seen-index for querying devices by status
        self.devices_table.add_global_secondary_index(
            index_name="status-last_seen-index",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="last_seen",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # AuditLogs table for comprehensive audit trail (Phase 4 compliance)
        self.audit_logs_table = dynamodb.Table(
            self, "AuditLogsTable",
            table_name=get_resource_name(self.config, "table", "audit-logs"),
            partition_key=dynamodb.Attribute(
                name="log_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
        read_capacity=5,
        write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True  # Always enabled for audit logs
            ),
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: CRITICAL - Audit logs must never be deleted
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute="ttl"  # 7-year retention via TTL
        )
        
        # GSI 1: user_id-timestamp-index for querying audit logs by user
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
        
        # GSI 2: resource_type-timestamp-index for querying by resource
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
        
        # GSI 3: action_type-timestamp-index for querying by action type
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
        
        # System Configuration table for admin settings
        self.system_config_table = dynamodb.Table(
            self, "SystemConfigTable",
            table_name=get_resource_name(self.config, "table", "system-config"),
            partition_key=dynamodb.Attribute(
                name="config_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=self.config["enable_point_in_time_recovery"],
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: Protect system configuration
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        self.data_resources.update({
            "readings_table": self.readings_table,
            "ledger_table": self.ledger_table,
            "sequence_table": self.sequence_table,
            "users_table": self.users_table,
            "service_requests_table": self.service_requests_table,
            "devices_table": self.devices_table,
            "audit_logs_table": self.audit_logs_table,
            "system_config_table": self.system_config_table
        })
        
        # Tag all tables for AWS Backup
        for table in [self.readings_table, self.ledger_table, self.sequence_table, 
                      self.users_table, self.service_requests_table, self.devices_table, 
                      self.audit_logs_table, self.system_config_table]:
            Tags.of(table).add("BackupEnabled", "true")
    
    def _create_s3_buckets(self) -> None:
        """
        Create S3 buckets for data lake and audit trail with security hardening
        """
        
        # ✅ SECURITY FIX: Create access logs bucket first
        self.access_logs_bucket = s3.Bucket(
            self, "AccessLogsBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"access-logs-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # ✅ SECURITY FIX
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: Protect access logs
            auto_delete_objects=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="AccessLogsLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(0)
                        )
                    ],
                    expiration=Duration.days(90)  # Keep access logs for 90 days
                )
            ]
        )
        
        # Data lake bucket with Intelligent-Tiering
        self.data_lake_bucket = s3.Bucket(
            self, "DataLakeBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"data-lake-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # ✅ SECURITY FIX
            server_access_logs_bucket=self.access_logs_bucket,  # ✅ SECURITY FIX
            server_access_logs_prefix="data-lake/",
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DataLakeIntelligentTiering",  # ✅ SECURITY FIX: Use Intelligent-Tiering
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(0)
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: Protect IoT data
            auto_delete_objects=False
        )
        
        # Audit trail bucket with Object Lock and cross-region replication
        self.audit_bucket = s3.Bucket(
            self, "AuditTrailBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"audit-trail-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # ✅ SECURITY FIX
            server_access_logs_bucket=self.access_logs_bucket,  # ✅ SECURITY FIX
            server_access_logs_prefix="audit-trail/",
            object_lock_enabled=True,
            object_lock_default_retention=s3.ObjectLockRetention.compliance(
                Duration.days(self.config["retention_days"])
            ),
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: CRITICAL - Never delete audit data
            auto_delete_objects=False
        )
        
        # ✅ SECURITY FIX: Add cross-region replication for audit bucket (DR requirement)
        if self.config.get("replica_region"):
            # Create replication role
            replication_role = iam.Role(
                self, "AuditBucketReplicationRole",
                assumed_by=iam.ServicePrincipal("s3.amazonaws.com"),
                description="Role for S3 cross-region replication of audit logs"
            )
            
            # Grant read permissions on source bucket
            self.audit_bucket.grant_read(replication_role)
            
            # Grant KMS permissions for replication
            self.kms_key.grant_encrypt_decrypt(replication_role)
            
            # Note: Destination bucket must be created in replica region separately
            # This is a placeholder for the replication configuration
            # In production, you would create the replica bucket in a separate stack
            replica_bucket_arn = f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'audit-replica-{self.account}')}"
            
            # Add replication configuration (requires CfnBucket for full control)
            cfn_audit_bucket = self.audit_bucket.node.default_child
            cfn_audit_bucket.replication_configuration = s3.CfnBucket.ReplicationConfigurationProperty(
                role=replication_role.role_arn,
                rules=[
                    s3.CfnBucket.ReplicationRuleProperty(
                        destination=s3.CfnBucket.ReplicationDestinationProperty(
                            bucket=replica_bucket_arn,
                            replication_time=s3.CfnBucket.ReplicationTimeProperty(
                                status="Enabled",
                                time=s3.CfnBucket.ReplicationTimeValueProperty(
                                    minutes=15
                                )
                            ),
                            metrics=s3.CfnBucket.MetricsProperty(
                                status="Enabled",
                                event_threshold=s3.CfnBucket.ReplicationTimeValueProperty(
                                    minutes=15
                                )
                            )
                        ),
                        status="Enabled",
                        priority=1,
                        filter=s3.CfnBucket.ReplicationRuleFilterProperty(
                            prefix=""
                        )
                    )
                ]
            )
        
        # ML models bucket
        self.ml_models_bucket = s3.Bucket(
            self, "MLModelsBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"ml-models-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # ✅ SECURITY FIX
            server_access_logs_bucket=self.access_logs_bucket,  # ✅ SECURITY FIX
            server_access_logs_prefix="ml-models/",
            removal_policy=RemovalPolicy.RETAIN,  # ✅ SECURITY FIX: Protect ML models
            auto_delete_objects=False
        )
        
        self.data_resources.update({
            "access_logs_bucket": self.access_logs_bucket,
            "data_lake_bucket": self.data_lake_bucket,
            "audit_bucket": self.audit_bucket,
            "ml_models_bucket": self.ml_models_bucket
        })
        
        # Tag all S3 buckets for AWS Backup
        for bucket in [self.access_logs_bucket, self.data_lake_bucket, self.audit_bucket, self.ml_models_bucket]:
            Tags.of(bucket).add("BackupEnabled", "true")
            Tags.of(bucket).add("DataClassification", "Confidential")
            Tags.of(bucket).add("ComplianceScope", "GDPR")
    
    def _create_iot_resources(self) -> None:
        """
        Create IoT Core resources for device management
        NOTE: IoT Topic Rules and Provisioning Templates will be created in Compute Stack
        after Lambda functions exist to avoid circular dependencies
        """
        
        # IoT Thing Type for AquaChain devices
        self.device_thing_type = iot.CfnThingType(
            self, "DeviceThingType",
            thing_type_name=get_resource_name(self.config, "thing-type", "device"),
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                thing_type_description="ESP32-based water quality sensor",
                searchable_attributes=["deviceModel", "firmwareVersion", "location"]
            )
        )
        
        self.data_resources.update({
            "device_thing_type": self.device_thing_type
        })
        
        # Output important values
        CfnOutput(
            self, "IoTEndpoint",
            value=f"https://iot.{self.region}.amazonaws.com",
            description="IoT Core endpoint for device connections"
        )
        
        CfnOutput(
            self, "DataLakeBucketName",
            value=self.data_lake_bucket.bucket_name,
            description="S3 bucket for raw data storage"
        )
        
        CfnOutput(
            self, "AuditBucket",
            value=self.audit_bucket.bucket_name,
            description="S3 bucket for audit trail with Object Lock"
        )
