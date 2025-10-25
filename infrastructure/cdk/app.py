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
from stacks.disaster_recovery_stack import AquaChainDisasterRecoveryStack
from stacks.landing_page_stack import AquaChainLandingPageStack
from stacks.vpc_stack import AquaChainVPCStack
from stacks.backup_stack import AquaChainBackupStack
from stacks.api_throttling_stack import AquaChainAPIThrottlingStack
from stacks.cloudfront_stack import AquaChainCloudFrontStack
from stacks.iot_security_stack import AquaChainIoTSecurityStack
from stacks.ml_model_registry_stack import AquaChainMLModelRegistryStack
from stacks.phase3_infrastructure_stack import AquaChainPhase3InfrastructureStack
from stacks.performance_dashboard_stack import PerformanceDashboardStack
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
    # Fixed: Pass compute_resources instead of lambda_functions to avoid circular reference
    api_stack = AquaChainApiStack(
        app, 
        f"AquaChain-API-{env_name}",
        config=config,
        compute_resources=compute_stack.compute_resources,
        security_resources=security_stack.security_resources,
        env=aws_env,
        description=f"AquaChain API Layer - {env_name}"
    )
    api_stack.add_dependency(compute_stack)
    
    # 6. Monitoring Stack (CloudWatch, X-Ray, PagerDuty)
    # Fixed: Use CfnOutput exports instead of direct references
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
    
    # 7. Disaster Recovery Stack (Backup, Cross-region replication, DR automation)
    dr_stack = AquaChainDisasterRecoveryStack(
        app,
        f"AquaChain-DR-{env_name}",
        config=config,
        data_resources=data_stack.data_resources,
        security_resources=security_stack.security_resources,
        env=aws_env,
        description=f"AquaChain Disaster Recovery Layer - {env_name}"
    )
    dr_stack.add_dependency(data_stack)
    
    # 8. Landing Page Stack (Static website hosting with CloudFront, S3, Route 53, WAF)
    landing_page_stack = AquaChainLandingPageStack(
        app,
        f"AquaChain-LandingPage-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Landing Page - {env_name}"
    )
    # Landing page is independent of other stacks
    
    # 9. VPC Stack (Enhanced networking with private subnets and VPC endpoints)
    vpc_stack = AquaChainVPCStack(
        app,
        f"AquaChain-VPC-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain VPC Infrastructure - {env_name}"
    )
    
    # 10. Backup Stack (Automated backup and restore for DynamoDB)
    backup_stack = AquaChainBackupStack(
        app,
        f"AquaChain-Backup-{env_name}",
        config=config,
        data_resources=data_stack.data_resources,
        env=aws_env,
        description=f"AquaChain Backup Automation - {env_name}"
    )
    backup_stack.add_dependency(data_stack)
    
    # 11. API Throttling Stack (Rate limiting and usage plans)
    api_throttling_stack = AquaChainAPIThrottlingStack(
        app,
        f"AquaChain-APIThrottling-{env_name}",
        config=config,
        rest_api=api_stack.api_resources.get('rest_api'),
        env=aws_env,
        description=f"AquaChain API Throttling - {env_name}"
    )
    api_throttling_stack.add_dependency(api_stack)
    
    # 12. CloudFront Stack (Global CDN for frontend)
    cloudfront_stack = AquaChainCloudFrontStack(
        app,
        f"AquaChain-CloudFront-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain CloudFront Distribution - {env_name}"
    )
    
    # 13. IoT Security Stack (Enhanced IoT device policies)
    iot_security_stack = AquaChainIoTSecurityStack(
        app,
        f"AquaChain-IoTSecurity-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain IoT Security - {env_name}"
    )
    iot_security_stack.add_dependency(security_stack)
    
    # 14. ML Model Registry Stack (Model versioning and A/B testing)
    ml_registry_stack = AquaChainMLModelRegistryStack(
        app,
        f"AquaChain-MLRegistry-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain ML Model Registry - {env_name}"
    )
    
    # 15. Phase 3 Infrastructure Stack (ML monitoring, certificate rotation, automation)
    phase3_stack = AquaChainPhase3InfrastructureStack(
        app,
        f"AquaChain-Phase3-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Phase 3 Infrastructure - {env_name}"
    )
    phase3_stack.add_dependency(security_stack)
    
    # 16. Performance Dashboard Stack (CloudWatch dashboard for system monitoring)
    performance_dashboard_stack = PerformanceDashboardStack(
        app,
        f"AquaChain-PerformanceDashboard-{env_name}",
        environment=env_name,
        env=aws_env,
        description=f"AquaChain Performance Monitoring Dashboard - {env_name}"
    )
    # Dashboard can be deployed independently but benefits from other stacks being deployed first
    performance_dashboard_stack.add_dependency(api_stack)
    performance_dashboard_stack.add_dependency(data_stack)
    performance_dashboard_stack.add_dependency(compute_stack)
    
    # Synthesize the app
    app.synth()

if __name__ == "__main__":
    main()