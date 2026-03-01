"""
ML Model Registry Stack
DynamoDB table and S3 bucket for model versioning
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class AquaChainMLModelRegistryStack(Stack):
    """
    ML Model Registry infrastructure
    """
    
    def __init__(self, scope: Construct, construct_id: str,
                 config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        
        # Create S3 bucket for model storage
        self.model_bucket = self._create_model_bucket()
        
        # Create DynamoDB table for model registry
        self.registry_table = self._create_registry_table()
        
        # Create IAM role for model management
        self.model_manager_role = self._create_model_manager_role()
        
        # Create outputs
        self._create_outputs()
    
    def _create_model_bucket(self) -> s3.Bucket:
        """
        Create S3 bucket for ML model storage
        """
        bucket = s3.Bucket(
            self, "ModelBucket",
            bucket_name=f"aquachain-ml-models-{self.config['environment']}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN  # Always retain models
        )
        
        return bucket
    
    def _create_registry_table(self) -> dynamodb.Table:
        """
        Create DynamoDB table for model registry
        """
        table = dynamodb.Table(
            self, "ModelRegistryTable",
            table_name=f"aquachain-model-registry-{self.config['environment']}",
            partition_key=dynamodb.Attribute(
                name="model_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,  # Always retain registry
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # Add GSI for querying by status
        table.add_global_secondary_index(
            index_name="StatusIndex",
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
        
        return table
    
    def _create_model_manager_role(self) -> iam.Role:
        """
        Create IAM role for model management Lambda functions
        """
        role = iam.Role(
            self, "ModelManagerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for ML model management Lambda functions"
        )
        
        # CloudWatch Logs permissions
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )
        
        # S3 permissions for model bucket
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                    "s3:GetObjectVersion",
                    "s3:ListBucketVersions"
                ],
                resources=[
                    self.model_bucket.bucket_arn,
                    f"{self.model_bucket.bucket_arn}/*"
                ]
            )
        )
        
        # DynamoDB permissions for registry table
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.registry_table.table_arn,
                    f"{self.registry_table.table_arn}/index/*"
                ]
            )
        )
        
        return role
    
    def _create_outputs(self):
        """
        Export model registry resources
        """
        CfnOutput(
            self, "ModelBucketName",
            value=self.model_bucket.bucket_name,
            export_name=f"{Stack.of(self).stack_name}-ModelBucketName",
            description="S3 bucket for ML models"
        )
        
        CfnOutput(
            self, "ModelBucketArn",
            value=self.model_bucket.bucket_arn,
            export_name=f"{Stack.of(self).stack_name}-ModelBucketArn",
            description="S3 bucket ARN"
        )
        
        CfnOutput(
            self, "RegistryTableName",
            value=self.registry_table.table_name,
            export_name=f"{Stack.of(self).stack_name}-RegistryTableName",
            description="DynamoDB table for model registry"
        )
        
        CfnOutput(
            self, "RegistryTableArn",
            value=self.registry_table.table_arn,
            export_name=f"{Stack.of(self).stack_name}-RegistryTableArn",
            description="DynamoDB table ARN"
        )
        
        CfnOutput(
            self, "ModelManagerRoleArn",
            value=self.model_manager_role.role_arn,
            export_name=f"{Stack.of(self).stack_name}-ModelManagerRoleArn",
            description="IAM role for model management"
        )
