#!/usr/bin/env python3
"""
Deploy Global Monitoring Dashboard Infrastructure
Creates DynamoDB tables and enables streams for the dashboard upgrade
"""

import aws_cdk as cdk
from stacks.global_monitoring_dashboard_stack import GlobalMonitoringDashboardStack
from config.environment_config import get_environment_config

app = cdk.App()

# Get environment from context or default to 'dev'
env_name = app.node.try_get_context("environment") or "dev"
config = get_environment_config(env_name)

# Create the Global Monitoring Dashboard stack
GlobalMonitoringDashboardStack(
    app,
    f"AquaChain-GlobalMonitoringDashboard-{env_name}",
    config=config,
    env=cdk.Environment(
        account=config.get("account"),
        region=config.get("region", "us-east-1")
    ),
    description=f"Global Monitoring Dashboard Infrastructure ({env_name})"
)

app.synth()
