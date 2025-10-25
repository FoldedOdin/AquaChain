"""
Environment-specific configuration for AquaChain CDK stacks
"""

from typing import Dict, Any

def get_environment_config(environment: str) -> Dict[str, Any]:
    """
    Get configuration for specific environment
    
    Args:
        environment: Environment name (dev, staging, prod)
        
    Returns:
        Configuration dictionary for the environment
    """
    
    # Base configuration
    base_config = {
        "project_name": "aquachain",
        "region": "us-east-1",
        "replica_region": "us-west-2",
        "retention_days": 2555,  # 7 years
        "alert_latency_seconds": 30,
        "uptime_target": 99.5,
        "max_concurrent_devices": 1000,
    }
    
    # Environment-specific configurations
    configs = {
        "dev": {
            **base_config,
            "environment": "dev",
            "domain_name": "dev.aquachain.io",
            "certificate_arn": None,  # Use default certificate
            "enable_deletion_protection": False,
            "enable_point_in_time_recovery": False,
            "dynamodb_billing_mode": "PAY_PER_REQUEST",
            "lambda_reserved_concurrency": 10,
            "api_throttle_rate_limit": 100,
            "api_throttle_burst_limit": 200,
            "enable_xray_tracing": True,
            "log_retention_days": 7,
            "enable_detailed_monitoring": False,
            "replica_account_id": None,  # No cross-account replication in dev
            "notification_channels": {
                "email": ["dev-team@aquachain.io"],
                "slack_webhook": None,
                "pagerduty_integration_key": None
            },
            "ml_model_config": {
                "instance_type": "ml.t3.medium",
                "enable_auto_scaling": False,
                "max_capacity": 1
            },
            "backup_config": {
                "enable_continuous_backup": False,
                "backup_retention_days": 7,
                "enable_cross_region_backup": False,
                "enable_automated_failover": False,
                "failover_rto_minutes": 480,  # 8 hours (relaxed for dev)
                "failover_rpo_minutes": 240,  # 4 hours (relaxed for dev)
                "enable_automated_dr_testing": False,
                "backup_window_start": "02:00",
                "backup_window_duration_hours": 1
            },
            "redis_node_type": "cache.t3.micro",
            "redis_num_nodes": 1,
            "redis_snapshot_retention": 0
        },
        
        "staging": {
            **base_config,
            "environment": "staging",
            "domain_name": "staging.aquachain.io",
            "certificate_arn": "arn:aws:acm:us-east-1:ACCOUNT:certificate/staging-cert-id",
            "enable_deletion_protection": True,
            "enable_point_in_time_recovery": True,
            "dynamodb_billing_mode": "PAY_PER_REQUEST",
            "lambda_reserved_concurrency": 50,
            "api_throttle_rate_limit": 500,
            "api_throttle_burst_limit": 1000,
            "enable_xray_tracing": True,
            "log_retention_days": 30,
            "enable_detailed_monitoring": True,
            "replica_account_id": "123456789012",  # Staging replica account
            "notification_channels": {
                "email": ["staging-alerts@aquachain.io"],
                "slack_webhook": "https://hooks.slack.com/services/staging",
                "pagerduty_integration_key": "staging-pagerduty-key"
            },
            "ml_model_config": {
                "instance_type": "ml.m5.large",
                "enable_auto_scaling": True,
                "max_capacity": 3
            },
            "backup_config": {
                "enable_continuous_backup": False,
                "backup_retention_days": 30,
                "enable_cross_region_backup": True,
                "enable_automated_failover": True,
                "failover_rto_minutes": 240,  # 4 hours
                "failover_rpo_minutes": 60    # 1 hour
            },
            "redis_node_type": "cache.t3.small",
            "redis_num_nodes": 1,
            "redis_snapshot_retention": 7
        },
        
        "prod": {
            **base_config,
            "environment": "prod",
            "domain_name": "api.aquachain.io",
            "certificate_arn": "arn:aws:acm:us-east-1:ACCOUNT:certificate/prod-cert-id",
            "enable_deletion_protection": True,
            "enable_point_in_time_recovery": True,
            "dynamodb_billing_mode": "PROVISIONED",
            "dynamodb_read_capacity": 100,
            "dynamodb_write_capacity": 100,
            "lambda_reserved_concurrency": 100,
            "api_throttle_rate_limit": 1000,
            "api_throttle_burst_limit": 2000,
            "enable_xray_tracing": True,
            "log_retention_days": 90,
            "enable_detailed_monitoring": True,
            "replica_account_id": "987654321098",  # Production replica account
            "notification_channels": {
                "email": ["alerts@aquachain.io", "oncall@aquachain.io"],
                "slack_webhook": "https://hooks.slack.com/services/production",
                "pagerduty_integration_key": "prod-pagerduty-key"
            },
            "ml_model_config": {
                "instance_type": "ml.m5.xlarge",
                "enable_auto_scaling": True,
                "max_capacity": 10
            },
            "backup_config": {
                "enable_continuous_backup": True,
                "backup_retention_days": 35,
                "enable_cross_region_backup": True,
                "enable_automated_failover": True,
                "failover_rto_minutes": 240,  # 4 hours
                "failover_rpo_minutes": 60,   # 1 hour
                "enable_global_tables": True,
                "enable_automated_dr_testing": True,
                "dr_test_schedule": "cron(0 4 ? * SAT *)",  # Weekly Saturday 4 AM
                "backup_window_start": "02:00",
                "backup_window_duration_hours": 2
            },
            "redis_node_type": "cache.m5.large",
            "redis_num_nodes": 2,
            "redis_snapshot_retention": 14
        }
    }
    
    if environment not in configs:
        raise ValueError(f"Unknown environment: {environment}. Available: {list(configs.keys())}")
    
    return configs[environment]

def get_resource_name(config: Dict[str, Any], resource_type: str, resource_name: str) -> str:
    """
    Generate standardized resource name
    
    Args:
        config: Environment configuration
        resource_type: Type of resource (table, bucket, function, etc.)
        resource_name: Base name of resource
        
    Returns:
        Standardized resource name
    """
    project = config["project_name"]
    env = config["environment"]
    
    return f"{project}-{resource_type}-{resource_name}-{env}"

def get_stack_name(config: Dict[str, Any], stack_type: str) -> str:
    """
    Generate standardized stack name
    
    Args:
        config: Environment configuration
        stack_type: Type of stack (core, data, compute, etc.)
        
    Returns:
        Standardized stack name
    """
    project = config["project_name"].title()
    env = config["environment"].title()
    stack = stack_type.title()
    
    return f"{project}-{stack}-{env}"