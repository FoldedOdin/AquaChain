"""
SageMaker Stack for AquaChain ML Model Training and Inference
Provides SageMaker training jobs, endpoints, and model registry
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct
from typing import Dict, Any


class AquaChainSageMakerStack(Stack):
    """
    SageMaker infrastructure for ML model training and inference
    """
    
    def __init__(self, scope: Construct, construct_id: str, 
                 config: Dict[str, Any],
                 data_resources: Dict[str, Any],
                 security_resources: Dict[str, Any],
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.env_name = config['environment']
        
        # Create SageMaker execution role
        self.sagemaker_role = self._create_sagemaker_role(
            data_resources,
            security_resources
        )
        
        # Create model package group for model registry
        self.model_package_group = self._create_model_package_group()
        
        # Create SageMaker model for inference
        self.wqi_model = self._create_sagemaker_model(data_resources)
        
        # Create SageMaker endpoint configuration
        self.endpoint_config = self._create_endpoint_config()
        
        # Create SageMaker endpoint
        self.endpoint = self._create_endpoint()
        
        # Store resources for other stacks
        self.sagemaker_resources = {
            'execution_role': self.sagemaker_role,
            'model_package_group': self.model_package_group,
            'endpoint_name': self.endpoint.attr_endpoint_name,
            'model': self.wqi_model
        }
        
        # Outputs
        self._create_outputs()
    
    def _create_sagemaker_role(self, data_resources: Dict[str, Any],
                               security_resources: Dict[str, Any]) -> iam.Role:
        """Create IAM role for SageMaker execution"""
        
        role = iam.Role(
            self, "SageMakerExecutionRole",
            role_name=f"AquaChain-SageMaker-ExecutionRole-{self.env_name}",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="Execution role for AquaChain SageMaker training and inference"
        )
        
        # Add SageMaker managed policies
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSageMakerFullAccess"
            )
        )
        
        # Grant access to S3 data bucket
        data_bucket = data_resources.get('data_bucket')
        if data_bucket:
            data_bucket.grant_read_write(role)
        
        # Grant access to KMS key for encryption
        kms_key = security_resources.get('data_key')
        if kms_key:
            kms_key.grant_encrypt_decrypt(role)
        
        # Create inline policy for additional permissions
        self.sagemaker_policy = iam.Policy(
            self, "SageMakerAdditionalPermissions",
            policy_name=f"AquaChain-SageMaker-AdditionalPermissions-{self.env_name}",
            statements=[
                # CloudWatch Logs permissions
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogStreams"
                    ],
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*"
                    ]
                ),
                # ECR permissions for SageMaker managed containers
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:DescribeImages"
                    ],
                    resources=["*"]  # Required for AWS-managed SageMaker containers
                ),
                # S3 permissions for ML models bucket
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    resources=[
                        f"arn:aws:s3:::aquachain-ml-models-{self.env_name}-{self.account}",
                        f"arn:aws:s3:::aquachain-ml-models-{self.env_name}-{self.account}/*"
                    ]
                )
            ]
        )
        
        # Attach policy to role
        self.sagemaker_policy.attach_to_role(role)
        
        return role
    
    def _create_model_package_group(self) -> sagemaker.CfnModelPackageGroup:
        """Create model package group for model registry"""
        
        model_package_group = sagemaker.CfnModelPackageGroup(
            self, "WQIModelPackageGroup",
            model_package_group_name=f"aquachain-wqi-models-{self.env_name}",
            model_package_group_description="AquaChain Water Quality Index prediction models",
            tags=[
                {
                    "key": "Project",
                    "value": "AquaChain"
                },
                {
                    "key": "Environment",
                    "value": self.env_name
                },
                {
                    "key": "ModelType",
                    "value": "WQI-Prediction"
                }
            ]
        )
        
        return model_package_group
    
    def _create_sagemaker_model(self, data_resources: Dict[str, Any]) -> sagemaker.CfnModel:
        """Create SageMaker model from trained artifacts"""
        
        # Use existing ML models bucket
        bucket_name = f"aquachain-ml-models-{self.env_name}-{self.account}"
        model_data_url = f"s3://{bucket_name}/ml-models/current/model.tar.gz"
        
        # Use scikit-learn inference container from SageMaker's region-specific registry
        # Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/pre-built-containers-frameworks-deep-learning.html
        # Map of regions to SageMaker ECR account IDs
        sagemaker_ecr_accounts = {
            'us-east-1': '683313688378',
            'us-east-2': '257758044811',
            'us-west-1': '746614075791',
            'us-west-2': '246618743249',
            'ap-south-1': '720646828776',  # Mumbai region
            'ap-northeast-1': '354813040037',
            'ap-northeast-2': '366743142698',
            'ap-southeast-1': '121021644041',
            'ap-southeast-2': '783357654285',
            'eu-central-1': '492215442770',
            'eu-west-1': '141502667606',
            'eu-west-2': '764974769150',
        }
        
        # Get the correct account ID for the current region
        ecr_account = sagemaker_ecr_accounts.get(self.region, '246618743249')
        container_image_uri = f"{ecr_account}.dkr.ecr.{self.region}.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3"
        
        model = sagemaker.CfnModel(
            self, "WQIModel",
            model_name=f"aquachain-wqi-model-{self.env_name}",
            execution_role_arn=self.sagemaker_role.role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image=container_image_uri,
                model_data_url=model_data_url,
                environment={
                    "SAGEMAKER_PROGRAM": "inference.py",
                    "SAGEMAKER_SUBMIT_DIRECTORY": model_data_url,
                    "SAGEMAKER_REGION": self.region
                }
            ),
            tags=[
                {
                    "key": "Project",
                    "value": "AquaChain"
                },
                {
                    "key": "Environment",
                    "value": self.env_name
                }
            ]
        )
        
        # Add dependency to ensure IAM role and policies are fully created before model
        model.node.add_dependency(self.sagemaker_role)
        model.node.add_dependency(self.sagemaker_policy)
        
        return model
    
    def _create_endpoint_config(self) -> sagemaker.CfnEndpointConfig:
        """Create SageMaker endpoint configuration"""
        
        # Choose instance type based on environment
        instance_type = {
            'dev': 'ml.t2.medium',      # Cost-effective for dev
            'staging': 'ml.m5.large',    # Balanced for staging
            'prod': 'ml.m5.xlarge'       # Performance for prod
        }.get(self.env_name, 'ml.t2.medium')
        
        endpoint_config = sagemaker.CfnEndpointConfig(
            self, "WQIEndpointConfig",
            endpoint_config_name=f"aquachain-wqi-endpoint-config-{self.env_name}",
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    variant_name="AllTraffic",
                    model_name=self.wqi_model.model_name,
                    initial_instance_count=1,
                    instance_type=instance_type,
                    initial_variant_weight=1.0
                )
            ],
            tags=[
                {
                    "key": "Project",
                    "value": "AquaChain"
                },
                {
                    "key": "Environment",
                    "value": self.env_name
                }
            ]
        )
        
        endpoint_config.add_dependency(self.wqi_model)
        
        return endpoint_config
    
    def _create_endpoint(self) -> sagemaker.CfnEndpoint:
        """Create SageMaker endpoint for real-time inference"""
        
        endpoint = sagemaker.CfnEndpoint(
            self, "WQIEndpoint",
            endpoint_name=f"aquachain-wqi-endpoint-{self.env_name}",
            endpoint_config_name=self.endpoint_config.endpoint_config_name,
            tags=[
                {
                    "key": "Project",
                    "value": "AquaChain"
                },
                {
                    "key": "Environment",
                    "value": self.env_name
                }
            ]
        )
        
        endpoint.add_dependency(self.endpoint_config)
        
        return endpoint
    
    def _create_outputs(self):
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self, "SageMakerRoleArn",
            value=self.sagemaker_role.role_arn,
            description="SageMaker execution role ARN",
            export_name=f"AquaChain-SageMaker-RoleArn-{self.env_name}"
        )
        
        CfnOutput(
            self, "ModelPackageGroupName",
            value=self.model_package_group.model_package_group_name,
            description="Model package group name for model registry",
            export_name=f"AquaChain-SageMaker-ModelPackageGroup-{self.env_name}"
        )
        
        CfnOutput(
            self, "EndpointName",
            value=self.endpoint.endpoint_name,
            description="SageMaker endpoint name for inference",
            export_name=f"AquaChain-SageMaker-EndpointName-{self.env_name}"
        )
        
        CfnOutput(
            self, "ModelName",
            value=self.wqi_model.model_name,
            description="SageMaker model name",
            export_name=f"AquaChain-SageMaker-ModelName-{self.env_name}"
        )
