#!/usr/bin/env python3
"""
AquaChain CDK Application
Main entry point for AWS CDK infrastructure deployment
"""

import os
from aws_cdk import App, Environment, Tags
from stacks.core_stack import AquaChainCoreStack
from stacks.data_stack import AquaChainDataStack
from stacks.compute_stack import AquaChainComputeStack
from stacks.api_stack import AquaChainApiStack
from stacks.monitoring_stack import AquaChainMonitoringStack
from stacks.security_stack import AquaChainSecurityStack
from config.environment_config import get_environment_config

def main():
    """
    Main CDK application entry point
    """
    app = App()
    
    # Get environment configuration
    env_name = app.node.try_get_context("environment") or "dev"
    config = get_environment_config(env_name)
    
    # Define AWS environment
    aws_env = Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", config["region"])
    )
    
    # Add global tags
    Tags.of(app).add("Project", "AquaChain")
    Tags.of(app).add("Environment", env_name)
    Tags.of(app).add("ManagedBy", "CDK")
    
    # Create stacks in dependency order
    
    # 1. Security Stack (KMS keys, IAM roles)
    security_stack = AquaChainSecurityStack(
        app, 
        f"AquaChain-Security-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Security Stack - {env_name}"
    )
    
    # 2. Core Stack (VPC, networking if needed)
    core_stack = AquaChainCoreStack(
        app, 
        f"AquaChain-Core-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Core Infrastructure - {env_name}"
    )
    
    # 3. Data Stack (DynamoDB, S3, IoT Core)
    data_stack = AquaChainDataStack(
        app, 
        f"AquaChain-Data-{env_name}",
        config=config,
        kms_key=security_stack.data_key,
        ledger_signing_key=security_stack.ledger_signing_key,
        env=aws_env,
        description=f"AquaChain Data Layer - {env_name}"
    )
    data_stack.add_dependency(security_stack)
    
    # 4. Compute Stack (Lambda functions, SageMaker)
    compute_stack = AquaChainComputeStack(
        app, 
        f"AquaChain-Compute-{env_name}",
        config=config,
        data_resources=data_stack.data_resources,
        security_resources=security_stack.security_resources,
        env=aws_env,
        description=f"AquaChain Compute Layer - {env_name}"
    )
    compute_stack.add_dependency(data_stack)
    
    # 5. API Stack (API Gateway, Cognito)
    api_stack = AquaChainApiStack(
        app, 
        f"AquaChain-API-{env_name}",
        config=config,
        lambda_functions=compute_stack.lambda_functions,
        security_resources=security_stack.security_resources,
        env=aws_env,
        description=f"AquaChain API Layer - {env_name}"
    )
    api_stack.add_dependency(compute_stack)
    
    # 6. Monitoring Stack (CloudWatch, X-Ray, PagerDuty)
    monitoring_stack = AquaChainMonitoringStack(
        app, 
        f"AquaChain-Monitoring-{env_name}",
        config=config,
        data_resources=data_stack.data_resources,
        compute_resources=compute_stack.compute_resources,
        api_resources=api_stack.api_resources,
        env=aws_env,
        description=f"AquaChain Monitoring Layer - {env_name}"
    )
    monitoring_stack.add_dependency(api_stack)
    
    # Synthesize the app
    app.synth()

if __name__ == "__main__":
    main()