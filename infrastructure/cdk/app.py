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
from stacks.cache_stack import AquaChainCacheStack
from stacks.lambda_layers_stack import LambdaLayersStack
from stacks.lambda_performance_stack import LambdaPerformanceStack
from stacks.data_classification_stack import DataClassificationStack
from stacks.audit_logging_stack import AuditLoggingStack
from stacks.gdpr_compliance_stack import GDPRComplianceStack
from stacks.dashboard_overhaul_stack import DashboardOverhaulStack
from stacks.deployment_pipeline_stack import DeploymentPipelineStack
from stacks.production_monitoring_stack import ProductionMonitoringStack
from stacks.enhanced_consumer_ordering_stack import EnhancedConsumerOrderingStack
from stacks.websocket_stack import WebSocketStack
from stacks.security_audit_stack import SecurityAuditStack
from stacks.auto_technician_assignment_stack import AutoTechnicianAssignmentStack
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
    
    # 9a. Cache Stack (ElastiCache Redis for caching)
    # DISABLED: Not used - code uses Lambda memory cache instead to save ~$12/month
    # cache_stack = AquaChainCacheStack(
    #     app,
    #     f"AquaChain-Cache-{env_name}",
    #     config=config,
    #     vpc=vpc_stack.vpc,
    #     lambda_security_group=vpc_stack.lambda_security_group,
    #     env=aws_env,
    #     description=f"AquaChain Cache Layer - {env_name}"
    # )
    # cache_stack.add_dependency(vpc_stack)
    
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
        rest_api_id=api_stack.api_resources.get('rest_api').rest_api_id,
        rest_api_stage_name=config['environment'],
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
    # DISABLED: Requires services that may not be available in AWS Educate/limited accounts
    # ml_registry_stack = AquaChainMLModelRegistryStack(
    #     app,
    #     f"AquaChain-MLRegistry-{env_name}",
    #     config=config,
    #     env=aws_env,
    #     description=f"AquaChain ML Model Registry - {env_name}"
    # )
    
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
    
    # ===== Phase 4 Infrastructure Stacks =====
    
    # 17. Data Classification Stack (KMS keys for PII and Sensitive data)
    data_classification_stack = DataClassificationStack(
        app,
        f"AquaChain-DataClassification-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Data Classification and Encryption - {env_name}"
    )
    data_classification_stack.add_dependency(security_stack)
    
    # 18. Audit Logging Stack (Kinesis Firehose and S3 for audit logs)
    audit_logging_stack = AuditLoggingStack(
        app,
        f"AquaChain-AuditLogging-{env_name}",
        config=config,
        kms_key=data_classification_stack.pii_key,  # Use PII key for audit logs
        env=aws_env,
        description=f"AquaChain Audit Logging Infrastructure - {env_name}"
    )
    audit_logging_stack.add_dependency(data_classification_stack)
    
    # 19. GDPR Compliance Stack (S3 buckets and DynamoDB tables for GDPR)
    gdpr_compliance_stack = GDPRComplianceStack(
        app,
        f"AquaChain-GDPRCompliance-{env_name}",
        config=config,
        kms_key=data_classification_stack.pii_key,
        env=aws_env,
        description=f"AquaChain GDPR Compliance Infrastructure - {env_name}"
    )
    gdpr_compliance_stack.add_dependency(data_classification_stack)
    
    # 20. Lambda Layers Stack (Shared dependencies for Lambda functions)
    lambda_layers_stack = LambdaLayersStack(
        app,
        f"AquaChain-LambdaLayers-{env_name}",
        env=aws_env,
        description=f"AquaChain Lambda Layers - {env_name}"
    )
    
    # 21. Lambda Performance Stack (Provisioned concurrency and optimizations)
    lambda_performance_stack = LambdaPerformanceStack(
        app,
        f"AquaChain-LambdaPerformance-{env_name}",
        common_layer=lambda_layers_stack.get_common_layer(),
        ml_layer=lambda_layers_stack.get_ml_layer(),
        alarm_topic=monitoring_stack.alarm_topic if hasattr(monitoring_stack, 'alarm_topic') else None,
        env=aws_env,
        description=f"AquaChain Lambda Performance Optimizations - {env_name}"
    )
    lambda_performance_stack.add_dependency(lambda_layers_stack)
    lambda_performance_stack.add_dependency(monitoring_stack)
    
    # 22. Dashboard Overhaul Stack (New role-based dashboard system)
    dashboard_overhaul_stack = DashboardOverhaulStack(
        app,
        f"AquaChain-DashboardOverhaul-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Dashboard Overhaul Infrastructure - {env_name}"
    )
    # Dashboard overhaul is independent but benefits from security stack
    dashboard_overhaul_stack.add_dependency(security_stack)
    
    # 23. Deployment Pipeline Stack (Blue-green deployment, feature flags, canary deployment)
    # DISABLED: Requires AWS CodeDeploy which is not available in AWS Educate/limited accounts
    # deployment_pipeline_stack = DeploymentPipelineStack(
    #     app,
    #     f"AquaChain-DeploymentPipeline-{env_name}",
    #     config=config,
    #     env=aws_env,
    #     description=f"AquaChain Dashboard Deployment Pipeline - {env_name}"
    # )
    # Deployment pipeline is independent infrastructure
    
    # 24. Production Monitoring Stack (Comprehensive monitoring, alerting, and incident response)
    production_monitoring_stack = ProductionMonitoringStack(
        app,
        f"AquaChain-ProductionMonitoring-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain Dashboard Production Monitoring - {env_name}"
    )
    # Production monitoring is independent but benefits from other stacks being deployed
    
    # 25. Enhanced Consumer Ordering Stack (New ordering system with dual payments)
    enhanced_ordering_stack = EnhancedConsumerOrderingStack(
        app,
        f"AquaChain-EnhancedOrdering-{env_name}",
        config=config,
        kms_key=security_stack.data_key,
        common_layer=lambda_layers_stack.get_common_layer(),
        env=aws_env,
        description=f"AquaChain Enhanced Consumer Ordering System - {env_name}"
    )
    enhanced_ordering_stack.add_dependency(security_stack)
    enhanced_ordering_stack.add_dependency(lambda_layers_stack)
    
    # 26. WebSocket Stack (Real-time updates via WebSocket API)
    websocket_stack = WebSocketStack(
        app,
        f"AquaChain-WebSocket-{env_name}",
        config=config,
        env=aws_env,
        description=f"AquaChain WebSocket API for Real-time Updates - {env_name}"
    )
    # WebSocket is independent infrastructure
    
    # 27. Security Audit Stack (Enhanced audit logging with real-time capture)
    security_audit_stack = SecurityAuditStack(
        app,
        f"AquaChain-SecurityAudit-{env_name}",
        config=config,
        kms_key=security_stack.data_key,
        env=aws_env,
        description=f"AquaChain Security Audit Logging - {env_name}"
    )
    security_audit_stack.add_dependency(security_stack)
    
    # 28. Auto Technician Assignment Stack (Automatic assignment with profile validation)
    auto_assignment_stack = AutoTechnicianAssignmentStack(
        app,
        f"AquaChain-AutoTechnicianAssignment-{env_name}",
        config=config,
        core_resources=data_stack.data_resources,
        env=aws_env,
        description=f"AquaChain Automatic Technician Assignment - {env_name}"
    )
    auto_assignment_stack.add_dependency(enhanced_ordering_stack)
    auto_assignment_stack.add_dependency(data_stack)
    
    # Synthesize the app
    app.synth()

if __name__ == "__main__":
    main()