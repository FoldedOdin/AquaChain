"""
IoT Core Stack
Complete IoT Core infrastructure for pluggable device management
Supports device provisioning, user association, and lifecycle management
"""

import json
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_iot as iot,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class AquaChainIoTCoreStack(Stack):
    """
    IoT Core infrastructure for device provisioning and management
    """
    
    def __init__(self, scope: Construct, construct_id: str,
                 config: Dict[str, Any],
                 data_resources: Dict[str, Any],
                 security_resources: Dict[str, Any],
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.data_resources = data_resources
        self.security_resources = security_resources
        self.iot_resources = {}
        
        # Create Thing Type for AquaChain devices
        self._create_thing_type()
        
        # Create Thing Groups for device organization
        self._create_thing_groups()
        
        # NOTE: IoT Rules commented out due to CloudFormation Early Validation issues
        # Will be created manually via AWS Console or CLI after stack deployment
        # self._create_iot_rules()
        
        # Create device provisioning resources
        self._create_provisioning_resources()
        
        # Create outputs
        self._create_outputs()
    
    def _create_thing_type(self):
        """
        Create Thing Type for AquaChain water quality sensors
        """
        self.thing_type = iot.CfnThingType(
            self, "AquaChainDeviceType",
            thing_type_name=f"aquachain-sensor-{self.config['environment']}",
            thing_type_properties=iot.CfnThingType.ThingTypePropertiesProperty(
                searchable_attributes=["deviceId", "userId", "status", "firmwareVersion"],
                thing_type_description="AquaChain Water Quality Sensor Device"
            )
        )
        
        self.iot_resources['thing_type'] = self.thing_type
    
    def _create_thing_groups(self):
        """
        Create Thing Groups for device organization
        """
        # Active devices group
        self.active_group = iot.CfnThingGroup(
            self, "ActiveDevicesGroup",
            thing_group_name=f"aquachain-active-{self.config['environment']}",
            thing_group_properties=iot.CfnThingGroup.ThingGroupPropertiesProperty(
                thing_group_description="Active AquaChain devices sending data"
            )
        )
        
        # Maintenance devices group
        self.maintenance_group = iot.CfnThingGroup(
            self, "MaintenanceDevicesGroup",
            thing_group_name=f"aquachain-maintenance-{self.config['environment']}",
            thing_group_properties=iot.CfnThingGroup.ThingGroupPropertiesProperty(
                thing_group_description="Devices under maintenance"
            )
        )
        
        # Offline devices group
        self.offline_group = iot.CfnThingGroup(
            self, "OfflineDevicesGroup",
            thing_group_name=f"aquachain-offline-{self.config['environment']}",
            thing_group_properties=iot.CfnThingGroup.ThingGroupPropertiesProperty(
                thing_group_description="Devices that haven't reported in >10 minutes"
            )
        )
        
        self.iot_resources['active_group'] = self.active_group
        self.iot_resources['maintenance_group'] = self.maintenance_group
        self.iot_resources['offline_group'] = self.offline_group
    
    def _create_iot_rules(self):
        """
        Create IoT Rules for data ingestion and processing
        """
        # Create IAM role for IoT Rules
        iot_rule_role = iam.Role(
            self, "IoTRuleRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role for IoT Rules to invoke Lambda and write to DynamoDB"
        )
        
        # Grant permissions to invoke data processing Lambda
        # Note: Lambda function will be created in compute stack
        iot_rule_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[f"arn:aws:lambda:{self.region}:{self.account}:function:aquachain-data-processing-*"]
            )
        )
        
        # Grant permissions to write to CloudWatch Logs for error handling
        iot_rule_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/iot/errors/aquachain-{self.config['environment']}:*"]
            )
        )
        
        # Rule 1: Sensor data ingestion
        self.data_ingestion_rule = iot.CfnTopicRule(
            self, "DataIngestionRule",
            rule_name=f"aquachain_data_ingestion_{self.config['environment']}",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=f"SELECT * FROM 'aquachain/+/data'",
                description="Route sensor data to processing Lambda",
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=f"arn:aws:lambda:{self.region}:{self.account}:function:aquachain-data-processing-{self.config['environment']}"
                        )
                    )
                ],
                aws_iot_sql_version="2016-03-23"
            )
        )
        
        # Rule 2: Device telemetry (battery, signal strength, etc.)
        # Note: Telemetry will be processed by the same Lambda as sensor data
        # This simplifies the architecture and avoids DynamoDB direct write issues
        self.telemetry_rule = iot.CfnTopicRule(
            self, "TelemetryRule",
            rule_name=f"aquachain_telemetry_{self.config['environment']}",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=f"SELECT * FROM 'aquachain/+/telemetry'",
                description="Route device telemetry to processing Lambda",
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=f"arn:aws:lambda:{self.region}:{self.account}:function:aquachain-data-processing-{self.config['environment']}"
                        )
                    )
                ],
                aws_iot_sql_version="2016-03-23"
            )
        )
        
        self.iot_resources['data_ingestion_rule'] = self.data_ingestion_rule
        self.iot_resources['telemetry_rule'] = self.telemetry_rule
        self.iot_resources['iot_rule_role'] = iot_rule_role
    
    def _create_provisioning_resources(self):
        """
        Create resources for device provisioning and user association
        Note: Provisioning template commented out due to validation issues
        Will be added manually via AWS Console or CLI after stack deployment
        """
        # Create provisioning template role
        provisioning_role = iam.Role(
            self, "ProvisioningRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role for IoT provisioning template"
        )
        
        provisioning_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "iot:CreateThing",
                    "iot:CreateCertificateFromCsr",
                    "iot:AttachThingPrincipal",
                    "iot:AttachPolicy",
                    "iot:DescribeCertificate",
                    "iot:UpdateCertificate"
                ],
                resources=["*"]
            )
        )
        
        # Note: Provisioning template creation via CDK has validation issues
        # Create it manually using AWS CLI after stack deployment:
        # aws iot create-provisioning-template \
        #   --template-name aquachain-device-provisioning-dev \
        #   --provisioning-role-arn <role-arn> \
        #   --template-body file://provisioning-template.json \
        #   --enabled
        
        self.iot_resources['provisioning_role'] = provisioning_role
        
        CfnOutput(
            self, "ProvisioningRoleArn",
            value=provisioning_role.role_arn,
            description="IAM Role ARN for IoT provisioning (use with AWS CLI to create template)"
        )
    
    def _create_outputs(self):
        """
        Export IoT Core resources
        """
        CfnOutput(
            self, "ThingTypeName",
            value=self.thing_type.thing_type_name,
            export_name=f"{Stack.of(self).stack_name}-ThingTypeName",
            description="IoT Thing Type for AquaChain devices"
        )
        
        CfnOutput(
            self, "ActiveGroupName",
            value=self.active_group.thing_group_name,
            export_name=f"{Stack.of(self).stack_name}-ActiveGroupName",
            description="Thing Group for active devices"
        )
        
        # NOTE: IoT Rules outputs commented out since rules are created manually
        # CfnOutput(
        #     self, "DataIngestionRuleName",
        #     value=self.data_ingestion_rule.rule_name,
        #     export_name=f"{Stack.of(self).stack_name}-DataIngestionRuleName",
        #     description="IoT Rule for data ingestion"
        # )
        
        CfnOutput(
            self, "IoTEndpoint",
            value=f"https://iot.{self.region}.amazonaws.com",
            description="IoT Core endpoint for device connections"
        )
