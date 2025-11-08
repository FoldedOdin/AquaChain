"""
AWS IoT Code Signing Stack
Sets up code signing profile and certificates for secure firmware updates
"""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_signer as signer,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct


class IoTCodeSigningStack(Stack):
    """Stack for AWS IoT firmware code signing"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # S3 bucket for firmware storage
        self.firmware_bucket = s3.Bucket(
            self, "FirmwareBucket",
            bucket_name=f"aquachain-firmware-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(90)
                )
            ]
        )
        
        # Create signing profile for firmware
        # Note: AWS CDK L2 construct for Signer is limited, using CfnSigningProfile
        signing_profile = signer.CfnSigningProfile(
            self, "FirmwareSigningProfile",
            platform_id="AWSIoTDeviceManagement-SHA256-ECDSA",
            signature_validity_period=signer.CfnSigningProfile.SignatureValidityPeriodProperty(
                type="YEARS",
                value=5
            ),
            tags=[
                {
                    "key": "Project",
                    "value": "AquaChain"
                },
                {
                    "key": "Purpose",
                    "value": "FirmwareSigning"
                }
            ]
        )
        
        # IAM role for code signing
        signing_role = iam.Role(
            self, "CodeSigningRole",
            assumed_by=iam.ServicePrincipal("signer.amazonaws.com"),
            description="Role for AWS Signer to access firmware bucket"
        )
        
        # Grant signing role access to firmware bucket
        self.firmware_bucket.grant_read_write(signing_role)
        
        # IAM role for Lambda to use code signing
        lambda_signing_role = iam.Role(
            self, "LambdaSigningRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant Lambda permissions for signing operations
        lambda_signing_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "signer:StartSigningJob",
                    "signer:DescribeSigningJob",
                    "signer:GetSigningProfile",
                    "signer:ListSigningJobs"
                ],
                resources=[signing_profile.attr_arn]
            )
        )
        
        # Grant Lambda access to firmware bucket
        self.firmware_bucket.grant_read_write(lambda_signing_role)
        
        # Store attributes for cross-stack references
        self.signing_profile_name = signing_profile.attr_profile_name
        self.signing_profile_arn = signing_profile.attr_arn
        
        # Outputs
        CfnOutput(
            self, "FirmwareBucketName",
            value=self.firmware_bucket.bucket_name,
            description="S3 bucket for firmware storage",
            export_name="AquaChain-FirmwareBucket"
        )
        
        CfnOutput(
            self, "SigningProfileName",
            value=self.signing_profile_name,
            description="Code signing profile name",
            export_name="AquaChain-SigningProfile"
        )
        
        CfnOutput(
            self, "SigningProfileArn",
            value=self.signing_profile_arn,
            description="Code signing profile ARN"
        )
        
        CfnOutput(
            self, "LambdaSigningRoleArn",
            value=lambda_signing_role.role_arn,
            description="IAM role for Lambda signing operations"
        )
