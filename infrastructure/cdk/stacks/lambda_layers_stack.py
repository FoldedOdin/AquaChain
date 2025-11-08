"""
Lambda Layers Stack for AquaChain

This stack defines Lambda layers for shared dependencies across Lambda functions.
Layers reduce deployment package sizes and improve cold start times.
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    CfnOutput,
)
from constructs import Construct


class LambdaLayersStack(Stack):
    """Stack for Lambda layers with shared dependencies"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Common dependencies layer
        self.common_layer = lambda_.LayerVersion(
            self,
            "CommonLayer",
            code=lambda_.Code.from_asset("../../lambda/layers/common"),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_10,
            ],
            description="Common dependencies: boto3, requests, pydantic, jsonschema, aws-xray-sdk, PyJWT",
            layer_version_name=f"aquachain-common-layer-{self.stack_name}",
        )

        # ML dependencies layer
        self.ml_layer = lambda_.LayerVersion(
            self,
            "MLLayer",
            code=lambda_.Code.from_asset("../../lambda/layers/ml"),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_10,
            ],
            description="ML dependencies: scikit-learn, numpy, pandas, scipy, sagemaker",
            layer_version_name=f"aquachain-ml-layer-{self.stack_name}",
        )

        # Outputs for cross-stack references
        CfnOutput(
            self,
            "CommonLayerArn",
            value=self.common_layer.layer_version_arn,
            description="ARN of the common dependencies layer",
            export_name=f"{self.stack_name}-CommonLayerArn",
        )

        CfnOutput(
            self,
            "MLLayerArn",
            value=self.ml_layer.layer_version_arn,
            description="ARN of the ML dependencies layer",
            export_name=f"{self.stack_name}-MLLayerArn",
        )

    def get_common_layer(self) -> lambda_.ILayerVersion:
        """Get the common dependencies layer"""
        return self.common_layer

    def get_ml_layer(self) -> lambda_.ILayerVersion:
        """Get the ML dependencies layer"""
        return self.ml_layer
