"""
AquaChain Data Stack - Import Existing Resources
This version imports existing DynamoDB tables instead of creating new ones
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
    Data layer stack - imports existing DynamoDB tables
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], 
                 kms_key: kms.Key, ledger_signing_key: kms.Key, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.kms_key = kms_key
        self.ledger_signing_key = ledger_signing_key
        self.data_resources = {}
        
        # Import existing DynamoDB tables
        self._import_dynamodb_tables()
        
        # Create S3 buckets (if they don't exist)
        self._create_s3_buckets()
        
        # Create IoT Core resources (if they don't exist)
        self._create_iot_resources()
    
    def _import_dynamodb_tables(self) -> None:
        """
        Import existing DynamoDB tables by reference
        """
        
        # Import Readings table
        self.readings_table = dynamodb.Table.from_table_name(
            self, "ReadingsTable",
            table_name="AquaChain-Readings"
        )
        
        # Import Ledger table
        self.ledger_table = dynamodb.Table.from_table_name(
            self, "LedgerTable",
            table_name="AquaChain-Ledger"
        )
        
        # Import Sequence table
        self.sequence_table = dynamodb.Table.from_table_name(
            self, "SequenceTable",
            table_name="AquaChain-Sequence"
        )
        
        # Import Users table
        self.users_table = dynamodb.Table.from_table_name(
            self, "UsersTable",
            table_name="AquaChain-Users"
        )
        
        # Import Service Requests table
        self.service_requests_table = dynamodb.Table.from_table_name(
            self, "ServiceRequestsTable",
            table_name="AquaChain-ServiceRequests"
        )
        
        # Import Devices table
        self.devices_table = dynamodb.Table.from_table_name(
            self, "DevicesTable",
            table_name="AquaChain-Devices"
        )
        
        # Import Audit Logs table
        self.audit_logs_table = dynamodb.Table.from_table_name(
            self, "AuditLogsTable",
            table_name="AquaChain-AuditLogs"
        )
        
        # Import System Config table
        self.system_config_table = dynamodb.Table.from_table_name(
            self, "SystemConfigTable",
            table_name="AquaChain-SystemConfig"
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
    
    def _create_s3_buckets(self) -> None:
        """
        Create S3 buckets for data lake, ML models, and audit trail
        Note: Check if buckets exist first, import if they do
        """
        
        # For now, we'll skip S3 bucket creation to avoid conflicts
        # These can be added later once we verify they don't exist
        pass
    
    def _create_iot_resources(self) -> None:
        """
        Create IoT Core resources
        Note: Check if resources exist first, import if they do
        """
        
        # For now, we'll skip IoT resource creation to avoid conflicts
        # These can be added later once we verify they don't exist
        pass
