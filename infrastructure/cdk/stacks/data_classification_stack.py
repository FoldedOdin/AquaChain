"""
AquaChain Data Classification and Encryption Stack
KMS keys for PII and Sensitive data encryption based on data classification schema
Requirements: 11.4
"""

from aws_cdk import (
    Stack,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    Tags
)
from constructs import Construct
from typing import Dict, Any


class DataClassificationStack(Stack):
    """
    Stack for data classification encryption infrastructure.
    Creates separate KMS keys for PII and SENSITIVE data classifications.
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.encryption_resources = {}
        
        # Create KMS keys for different data classifications
        self._create_pii_encryption_key()
        self._create_sensitive_encryption_key()
        
        # Create IAM policies for key access
        self._create_key_access_policies()
    
    def _create_pii_encryption_key(self) -> None:
        """
        Create dedicated KMS key for PII (Personally Identifiable Information) data.
        
        This key is used to encrypt fields classified as PII including:
        - email, name, phone, address
        - payment information
        - security questions/answers
        
        Key features:
        - Automatic key rotation enabled
        - Strict access controls
        - Audit logging enabled
        - Retained in production for compliance
        """
        
        # Create key policy for PII key
        pii_key_policy = iam.PolicyDocument(
            statements=[
                # Root account permissions
                iam.PolicyStatement(
                    sid="Enable IAM User Permissions",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.AccountRootPrincipal()],
                    actions=["kms:*"],
                    resources=["*"]
                ),
                
                # Lambda service permissions for encryption/decryption
                iam.PolicyStatement(
                    sid="Allow Lambda Services",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"lambda.{self.region}.amazonaws.com"
                            ]
                        }
                    }
                ),
                
                # DynamoDB service permissions for encryption at rest
                iam.PolicyStatement(
                    sid="Allow DynamoDB Service",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("dynamodb.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:CreateGrant",
                        "kms:DescribeKey"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"dynamodb.{self.region}.amazonaws.com"
                            ]
                        }
                    }
                ),
                
                # S3 service permissions for GDPR exports
                iam.PolicyStatement(
                    sid="Allow S3 Service",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("s3.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"s3.{self.region}.amazonaws.com"
                            ]
                        }
                    }
                ),
                
                # CloudWatch Logs permissions for audit logging
                iam.PolicyStatement(
                    sid="Allow CloudWatch Logs",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("logs.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:CreateGrant",
                        "kms:DescribeKey"
                    ],
                    resources=["*"],
                    conditions={
                        "ArnLike": {
                            "kms:EncryptionContext:aws:logs:arn": 
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:*"
                        }
                    }
                )
            ]
        )
        
        # Create PII encryption key
        self.pii_key = kms.Key(
            self, "PIIEncryptionKey",
            description="AquaChain PII Data Encryption Key - GDPR Compliant",
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            removal_policy=RemovalPolicy.RETAIN if self.config.get("environment") == "prod" else RemovalPolicy.DESTROY,
            enable_key_rotation=True,
            rotation_period=Duration.days(365),  # Annual rotation
            policy=pii_key_policy
        )
        
        # Add alias for PII key
        self.pii_key_alias = kms.Alias(
            self, "PIIKeyAlias",
            alias_name=f"alias/aquachain-{self.config.get('environment', 'dev')}-pii-key",
            target_key=self.pii_key
        )
        
        # Add tags for compliance and tracking
        Tags.of(self.pii_key).add("DataClassification", "PII")
        Tags.of(self.pii_key).add("Compliance", "GDPR")
        Tags.of(self.pii_key).add("Project", "AquaChain")
        Tags.of(self.pii_key).add("Component", "DataEncryption")
        Tags.of(self.pii_key).add("CriticalityLevel", "High")
        
        self.encryption_resources["pii_key"] = self.pii_key
        self.encryption_resources["pii_key_alias"] = self.pii_key_alias
    
    def _create_sensitive_encryption_key(self) -> None:
        """
        Create dedicated KMS key for SENSITIVE data.
        
        This key is used to encrypt fields classified as SENSITIVE including:
        - device serial numbers, MAC addresses
        - IP addresses, location data
        - API keys, access tokens
        - password hashes
        
        Key features:
        - Automatic key rotation enabled
        - Access controls for authorized services
        - Audit logging enabled
        - Retained in production for business continuity
        """
        
        # Create key policy for SENSITIVE key
        sensitive_key_policy = iam.PolicyDocument(
            statements=[
                # Root account permissions
                iam.PolicyStatement(
                    sid="Enable IAM User Permissions",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.AccountRootPrincipal()],
                    actions=["kms:*"],
                    resources=["*"]
                ),
                
                # Lambda service permissions
                iam.PolicyStatement(
                    sid="Allow Lambda Services",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"lambda.{self.region}.amazonaws.com"
                            ]
                        }
                    }
                ),
                
                # DynamoDB service permissions
                iam.PolicyStatement(
                    sid="Allow DynamoDB Service",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("dynamodb.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:CreateGrant",
                        "kms:DescribeKey"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"dynamodb.{self.region}.amazonaws.com"
                            ]
                        }
                    }
                ),
                
                # Secrets Manager permissions for API keys
                iam.PolicyStatement(
                    sid="Allow Secrets Manager",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("secretsmanager.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:CreateGrant",
                        "kms:DescribeKey"
                    ],
                    resources=["*"]
                ),
                
                # IoT Core permissions for device credentials
                iam.PolicyStatement(
                    sid="Allow IoT Core",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ServicePrincipal("iot.amazonaws.com")],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=["*"]
                )
            ]
        )
        
        # Create SENSITIVE encryption key
        self.sensitive_key = kms.Key(
            self, "SensitiveEncryptionKey",
            description="AquaChain Sensitive Data Encryption Key - Business Critical",
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            removal_policy=RemovalPolicy.RETAIN if self.config.get("environment") == "prod" else RemovalPolicy.DESTROY,
            enable_key_rotation=True,
            rotation_period=Duration.days(365),  # Annual rotation
            policy=sensitive_key_policy
        )
        
        # Add alias for SENSITIVE key
        self.sensitive_key_alias = kms.Alias(
            self, "SensitiveKeyAlias",
            alias_name=f"alias/aquachain-{self.config.get('environment', 'dev')}-sensitive-key",
            target_key=self.sensitive_key
        )
        
        # Add tags for compliance and tracking
        Tags.of(self.sensitive_key).add("DataClassification", "SENSITIVE")
        Tags.of(self.sensitive_key).add("Compliance", "BusinessCritical")
        Tags.of(self.sensitive_key).add("Project", "AquaChain")
        Tags.of(self.sensitive_key).add("Component", "DataEncryption")
        Tags.of(self.sensitive_key).add("CriticalityLevel", "Medium")
        
        self.encryption_resources["sensitive_key"] = self.sensitive_key
        self.encryption_resources["sensitive_key_alias"] = self.sensitive_key_alias
    
    def _create_key_access_policies(self) -> None:
        """
        Create IAM policies for accessing encryption keys.
        These policies can be attached to Lambda execution roles.
        """
        
        # Policy for PII data access
        self.pii_access_policy = iam.ManagedPolicy(
            self, "PIIDataAccessPolicy",
            managed_policy_name=f"AquaChain-{self.config.get('environment', 'dev')}-PII-Access",
            description="Policy for accessing PII encrypted data",
            statements=[
                iam.PolicyStatement(
                    sid="AllowPIIKeyUsage",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=[self.pii_key.key_arn]
                )
            ]
        )
        
        # Policy for SENSITIVE data access
        self.sensitive_access_policy = iam.ManagedPolicy(
            self, "SensitiveDataAccessPolicy",
            managed_policy_name=f"AquaChain-{self.config.get('environment', 'dev')}-Sensitive-Access",
            description="Policy for accessing SENSITIVE encrypted data",
            statements=[
                iam.PolicyStatement(
                    sid="AllowSensitiveKeyUsage",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=[self.sensitive_key.key_arn]
                )
            ]
        )
        
        # Combined policy for services that need both
        self.full_encryption_access_policy = iam.ManagedPolicy(
            self, "FullEncryptionAccessPolicy",
            managed_policy_name=f"AquaChain-{self.config.get('environment', 'dev')}-Full-Encryption-Access",
            description="Policy for accessing all encrypted data classifications",
            statements=[
                iam.PolicyStatement(
                    sid="AllowAllEncryptionKeys",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    resources=[
                        self.pii_key.key_arn,
                        self.sensitive_key.key_arn
                    ]
                )
            ]
        )
        
        self.encryption_resources.update({
            "pii_access_policy": self.pii_access_policy,
            "sensitive_access_policy": self.sensitive_access_policy,
            "full_encryption_access_policy": self.full_encryption_access_policy
        })
    
    def grant_pii_access(self, grantee: iam.IGrantable) -> None:
        """
        Grant PII key access to a principal (e.g., Lambda function).
        
        Args:
            grantee: The principal to grant access to
        """
        self.pii_key.grant_encrypt_decrypt(grantee)
    
    def grant_sensitive_access(self, grantee: iam.IGrantable) -> None:
        """
        Grant SENSITIVE key access to a principal (e.g., Lambda function).
        
        Args:
            grantee: The principal to grant access to
        """
        self.sensitive_key.grant_encrypt_decrypt(grantee)
    
    def grant_full_encryption_access(self, grantee: iam.IGrantable) -> None:
        """
        Grant access to both PII and SENSITIVE keys to a principal.
        
        Args:
            grantee: The principal to grant access to
        """
        self.pii_key.grant_encrypt_decrypt(grantee)
        self.sensitive_key.grant_encrypt_decrypt(grantee)
