"""
AquaChain Security Stack
KMS keys, IAM roles, and security policies
"""

from aws_cdk import (
    Stack,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class AquaChainSecurityStack(Stack):
    """
    Security stack containing KMS keys, IAM roles, and security policies
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.security_resources = {}
        
        # Create KMS keys
        self._create_kms_keys()
        
        # Create IAM roles
        self._create_iam_roles()
        
        # Create security policies
        self._create_security_policies()
    
    def _create_kms_keys(self) -> None:
        """
        Create KMS keys for encryption and signing
        """
        
        # Data encryption key
        self.data_key = kms.Key(
            self, "DataEncryptionKey",
            description="AquaChain data encryption key",
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            enable_key_rotation=True,
            rotation_schedule=Duration.days(365) if self.config["environment"] == "prod" else Duration.days(90)
        )
        
        # Add alias for data key
        kms.Alias(
            self, "DataKeyAlias",
            alias_name=f"alias/{get_resource_name(self.config, 'kms', 'data')}",
            target_key=self.data_key
        )
        
        # Ledger signing key (asymmetric for digital signatures)
        self.ledger_signing_key = kms.Key(
            self, "LedgerSigningKey",
            description="AquaChain ledger signing key",
            key_usage=kms.KeyUsage.SIGN_VERIFY,
            key_spec=kms.KeySpec.RSA_2048,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # Add alias for signing key
        kms.Alias(
            self, "SigningKeyAlias",
            alias_name=f"alias/{get_resource_name(self.config, 'kms', 'signing')}",
            target_key=self.ledger_signing_key
        )
        
        # IoT device key for device certificates
        self.iot_key = kms.Key(
            self, "IoTDeviceKey",
            description="AquaChain IoT device encryption key",
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            enable_key_rotation=True
        )
        
        # Add alias for IoT key
        kms.Alias(
            self, "IoTKeyAlias",
            alias_name=f"alias/{get_resource_name(self.config, 'kms', 'iot')}",
            target_key=self.iot_key
        )
        
        self.security_resources.update({
            "data_key": self.data_key,
            "ledger_signing_key": self.ledger_signing_key,
            "iot_key": self.iot_key
        })
    
    def _create_iam_roles(self) -> None:
        """
        Create IAM roles for various services
        """
        
        # Lambda execution role for data processing
        self.data_processing_role = iam.Role(
            self, "DataProcessingRole",
            role_name=get_resource_name(self.config, "role", "data-processing"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ]
        )
        
        # Add inline policy for data processing
        self.data_processing_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{get_resource_name(self.config, 'table', '*')}"
                ]
            )
        )
        
        self.data_processing_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:PutObjectLegalHold",
                    "s3:PutObjectRetention"
                ],
                resources=[
                    f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', '*')}/*"
                ]
            )
        )
        
        self.data_processing_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                    "kms:Sign",
                    "kms:Verify"
                ],
                resources=[
                    self.data_key.key_arn,
                    self.ledger_signing_key.key_arn
                ]
            )
        )
        
        # IoT Core service role
        self.iot_service_role = iam.Role(
            self, "IoTServiceRole",
            role_name=get_resource_name(self.config, "role", "iot-service"),
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
        )
        
        self.iot_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    f"arn:aws:lambda:{self.region}:{self.account}:function:{get_resource_name(self.config, 'function', '*')}"
                ]
            )
        )
        
        # API Gateway execution role
        self.api_gateway_role = iam.Role(
            self, "ApiGatewayRole",
            role_name=get_resource_name(self.config, "role", "api-gateway"),
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs")
            ]
        )
        
        # SageMaker execution role
        self.sagemaker_role = iam.Role(
            self, "SageMakerRole",
            role_name=get_resource_name(self.config, "role", "sagemaker"),
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            ]
        )
        
        self.sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                resources=[
                    f"arn:aws:s3:::{get_resource_name(self.config, 'bucket', 'ml-models')}/*"
                ]
            )
        )
        
        self.security_resources.update({
            "data_processing_role": self.data_processing_role,
            "iot_service_role": self.iot_service_role,
            "api_gateway_role": self.api_gateway_role,
            "sagemaker_role": self.sagemaker_role
        })
    
    def _create_security_policies(self) -> None:
        """
        Create custom security policies
        """
        
        # Device policy template for IoT devices
        self.device_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["iot:Connect"],
                    resources=[f"arn:aws:iot:{self.region}:{self.account}:client/${{iot:Connection.Thing.ThingName}}"]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["iot:Publish"],
                    resources=[f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/data"]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["iot:Subscribe"],
                    resources=[f"arn:aws:iot:{self.region}:{self.account}:topicfilter/aquachain/${{iot:Connection.Thing.ThingName}}/commands"]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["iot:Receive"],
                    resources=[f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/commands"]
                )
            ]
        )
        
        # Create the device policy
        self.device_policy = iam.CfnPolicy(
            self, "DevicePolicy",
            policy_name=get_resource_name(self.config, "policy", "device"),
            policy_document=self.device_policy_document.to_json()
        )
        
        self.security_resources.update({
            "device_policy": self.device_policy,
            "device_policy_document": self.device_policy_document
        })