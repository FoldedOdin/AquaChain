"""
AquaChain Global Monitoring Dashboard Stack
Creates DynamoDB tables and infrastructure for the Global Monitoring Dashboard upgrade
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct
from typing import Dict, Any


class GlobalMonitoringDashboardStack(Stack):
    """
    Infrastructure stack for Global Monitoring Dashboard
    Creates:
    - Pre_Aggregated_Summary_Table with region-based partition keys
    - Audit_Log table with date-based partition keys
    - Enables DynamoDB Streams on existing tables
    
    Cost Optimization: Uses Lambda memory cache instead of ElastiCache Redis
    to save ~$105/month while maintaining acceptable performance for admin dashboard.
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        config: Dict[str, Any],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.env_name = config.get("environment", "dev")
        
        # Create Pre-Aggregated Summary Table
        self.pre_aggregated_table = self._create_pre_aggregated_summary_table()
        
        # Create Audit Log Table
        self.audit_log_table = self._create_audit_log_table()
        
        # Import existing tables to enable streams
        self._enable_streams_on_existing_tables()
        
        # Create outputs
        self._create_outputs()
    
    def _create_pre_aggregated_summary_table(self) -> dynamodb.Table:
        """
        Create Pre_Aggregated_Summary_Table with region-based partition keys
        
        Requirements: 15.1, 15.2, 15.3, 19.1
        """
        table_name = f"AquaChain-PreAggregatedSummary-{self.env_name}"
        
        table = dynamodb.Table(
            self,
            "PreAggregatedSummaryTable",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="region_date",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="time_bucket",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_IMAGE,
        )
        
        # Create TimeBucketRegionIndex GSI
        table.add_global_secondary_index(
            index_name="TimeBucketRegionIndex",
            partition_key=dynamodb.Attribute(
                name="time_bucket",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="region",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        return table
    
    def _create_audit_log_table(self) -> dynamodb.Table:
        """
        Create Audit_Log table with date-based partition keys
        
        Requirements: 17.2, 17.7
        """
        table_name = f"AquaChain-AuditLog-{self.env_name}"
        
        table = dynamodb.Table(
            self,
            "AuditLogTable",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="date",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="user_timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_IMAGE,
        )
        
        # Create UserTimestampIndex GSI
        table.add_global_secondary_index(
            index_name="UserTimestampIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        # Create IAM policy to deny UpdateItem and DeleteItem (immutability)
        # This will be attached to Lambda execution roles that access this table
        self.audit_log_immutability_policy = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            actions=[
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            resources=[table.table_arn]
        )
        
        return table
    
    def _enable_streams_on_existing_tables(self) -> None:
        """
        Enable DynamoDB Streams on existing tables
        
        Requirements: 15.8, 19.8, 3.2
        
        Note: This imports existing tables and documents the stream configuration.
        Streams must be enabled manually via AWS Console or CLI for existing tables.
        """
        # Import existing Readings table
        self.readings_table = dynamodb.Table.from_table_name(
            self,
            "ReadingsTableRef",
            table_name="AquaChain-Readings"
        )
        
        # Import existing Alerts table
        self.alerts_table = dynamodb.Table.from_table_name(
            self,
            "AlertsTableRef",
            table_name="AquaChain-Alerts"
        )
        
        # Note: For existing tables, streams must be enabled manually:
        # aws dynamodb update-table --table-name AquaChain-Readings \
        #   --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE
        # 
        # aws dynamodb update-table --table-name AquaChain-Alerts \
        #   --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for table names and ARNs"""
        """Create CloudFormation outputs for table names and ARNs"""
        
        CfnOutput(
            self,
            "PreAggregatedSummaryTableName",
            value=self.pre_aggregated_table.table_name,
            description="Pre-Aggregated Summary Table Name"
        )
        
        CfnOutput(
            self,
            "PreAggregatedSummaryTableArn",
            value=self.pre_aggregated_table.table_arn,
            description="Pre-Aggregated Summary Table ARN"
        )
        
        CfnOutput(
            self,
            "PreAggregatedSummaryTableStreamArn",
            value=self.pre_aggregated_table.table_stream_arn or "N/A",
            description="Pre-Aggregated Summary Table Stream ARN"
        )
        
        CfnOutput(
            self,
            "AuditLogTableName",
            value=self.audit_log_table.table_name,
            description="Audit Log Table Name"
        )
        
        CfnOutput(
            self,
            "AuditLogTableArn",
            value=self.audit_log_table.table_arn,
            description="Audit Log Table ARN"
        )
        
        CfnOutput(
            self,
            "AuditLogTableStreamArn",
            value=self.audit_log_table.table_stream_arn or "N/A",
            description="Audit Log Table Stream ARN"
        )
