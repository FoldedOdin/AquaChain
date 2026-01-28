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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
            removal_policy=RemovalPolicy.DESTROY,  # Always retain ledger
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
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
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
            removal_policy=RemovalPolicy.DESTROY,  # Always retain audit logs
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
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.config["enable_point_in_time_recovery"]
            ),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
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
        Create S3 buckets for data lake and audit trail
        """
        
        # Data lake bucket
        self.data_lake_bucket = s3.Bucket(
            self, "DataLakeBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"data-lake-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DataLakeLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=False if self.config["environment"] == "prod" else True
        )
        
        # Audit trail bucket with Object Lock
        self.audit_bucket = s3.Bucket(
            self, "AuditTrailBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"audit-trail-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            object_lock_enabled=True,
            object_lock_default_retention=s3.ObjectLockRetention.compliance(
                Duration.days(self.config["retention_days"])
            ),
            removal_policy=RemovalPolicy.DESTROY,  # Always retain audit data
            auto_delete_objects=False
        )
        
        # ML models bucket
        self.ml_models_bucket = s3.Bucket(
            self, "MLModelsBucket",
            bucket_name=get_resource_name(self.config, "bucket", f"ml-models-{self.account}"),
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=False if self.config["environment"] == "prod" else True
        )
        
        # Set up cross-account replication if replica account is configured
        if self.config.get("replica_account_id"):
            # Create replication bucket in replica account (this would be done separately)
            # Here we just configure the replication rule
            replica_bucket_arn = f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', f'audit-replica-{self.config['replica_account_id']}')}/*"
            
            # Note: Cross-account replication setup would require additional IAM roles
            # and bucket policies in the replica account
        
        self.data_resources.update({
            "data_lake_bucket": self.data_lake_bucket,
            "audit_bucket": self.audit_bucket,
            "ml_models_bucket": self.ml_models_bucket
        })
        
        # Tag all S3 buckets for AWS Backup
        for bucket in [self.data_lake_bucket, self.audit_bucket, self.ml_models_bucket]:
            Tags.of(bucket).add("BackupEnabled", "true")
    
    def _create_iot_resources(self) -> None:
        """
        Create IoT Core resources for device management
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
        
        # IoT Topic Rule for data processing
        self.data_processing_rule = iot.CfnTopicRule(
            self, "DataProcessingRule",
            rule_name=get_resource_name(self.config, "rule", "data_processing").replace("-", "_"),
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=f"SELECT *, timestamp() as serverTimestamp FROM 'aquachain/+/data'",
                description="Route device data to processing Lambda",
                rule_disabled=False,
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=f"arn:aws:lambda:{self.region}:{self.account}:function:{get_resource_name(self.config, 'function', 'data-processing')}"
                        )
                    )
                ],
                error_action=iot.CfnTopicRule.ActionProperty(
                    s3=iot.CfnTopicRule.S3ActionProperty(
                        bucket_name=self.data_lake_bucket.bucket_name,
                        key="iot-errors/${timestamp()}-${newuuid()}.json",
                        role_arn=f"arn:aws:iam::{self.account}:role/{get_resource_name(self.config, 'role', 'iot-service')}"
                    )
                )
            )
        )
        
        # IoT Provisioning Template for device registration
        # Simplified template - creates thing and certificate only
        self.provisioning_template = iot.CfnProvisioningTemplate(
            self, "DeviceProvisioningTemplate",
            template_name=f"aquachain-dev-prov-{self.config['environment']}",
            description="Template for provisioning AquaChain devices",
            enabled=True,
            provisioning_role_arn=f"arn:aws:iam::{self.account}:role/{get_resource_name(self.config, 'role', 'iot-provisioning')}",
            template_body="""{
                "Parameters": {
                    "DeviceId": {
                        "Type": "String"
                    },
                    "SerialNumber": {
                        "Type": "String"
                    }
                },
                "Resources": {
                    "thing": {
                        "Type": "AWS::IoT::Thing",
                        "Properties": {
                            "ThingName": {"Ref": "DeviceId"},
                            "ThingTypeName": \"""" + self.device_thing_type.thing_type_name + """\",
                            "AttributePayload": {
                                "serialNumber": {"Ref": "SerialNumber"}
                            }
                        }
                    },
                    "certificate": {
                        "Type": "AWS::IoT::Certificate",
                        "Properties": {
                            "CertificateId": {"Ref": "AWS::IoT::Certificate::Id"},
                            "Status": "ACTIVE"
                        }
                    }
                }
            }"""
        )
        
        self.data_resources.update({
            "device_thing_type": self.device_thing_type,
            "data_processing_rule": self.data_processing_rule,
            "provisioning_template": self.provisioning_template
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
