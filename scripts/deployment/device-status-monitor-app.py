#!/usr/bin/env python3
"""
Standalone CDK App for Device Status Monitor
Deploys only the device status monitoring infrastructure
"""

import os
import sys
import boto3

# Add the infrastructure directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure', 'cdk'))

from aws_cdk import (
    App, Environment, Stack, Duration,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam
)
from stacks.device_status_monitor_stack import DeviceStatusMonitorStack


class DeviceStatusMonitorApp(Stack):
    """Direct deployment stack for device status monitor"""
    
    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Import existing DynamoDB tables
        devices_table = dynamodb.Table.from_table_name(
            self, "ImportedDevicesTable",
            table_name="AquaChain-Devices"
        )
        
        readings_table = dynamodb.Table.from_table_name(
            self, "ImportedReadingsTable", 
            table_name="AquaChain-Readings"
        )
        
        # Create device status monitor resources directly
        config = {"environment": "dev", "region": "ap-south-1"}
        
        # Create the monitor stack directly (not as nested stack)
        from stacks.device_status_monitor_stack import DeviceStatusMonitorStack
        
        # Create Lambda function
        self.status_monitor_lambda = _lambda.Function(
            self, "DeviceStatusMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("../../lambda/device_status_monitor"),
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                "DEVICES_TABLE": devices_table.table_name,
                "READINGS_TABLE": readings_table.table_name,
                "OFFLINE_THRESHOLD_MINUTES": "5",
                "LOG_LEVEL": "INFO"
            },
            description="Monitors device online/offline status based on data transmission"
        )
        
        # Grant permissions to DynamoDB tables
        devices_table.grant_read_write_data(self.status_monitor_lambda)
        readings_table.grant_read_data(self.status_monitor_lambda)
        
        # Grant CloudWatch permissions
        self.status_monitor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )
        
        # Create CloudWatch Events rule
        self.status_check_rule = events.Rule(
            self, "DeviceStatusCheckRule",
            schedule=events.Schedule.rate(Duration.minutes(2)),
            description="Triggers device status monitoring every 2 minutes"
        )
        
        # Add Lambda as target
        self.status_check_rule.add_target(
            targets.LambdaFunction(self.status_monitor_lambda)
        )
        
        # Add tags
        from aws_cdk import Tags
        Tags.of(self.status_monitor_lambda).add("Project", "AquaChain")
        Tags.of(self.status_monitor_lambda).add("Service", "DeviceStatusMonitor")
        Tags.of(self.status_monitor_lambda).add("Environment", "dev")


def main():
    """Deploy device status monitor as standalone stack"""
    
    print("🚀 Deploying Device Status Monitor (Standalone)")
    print("=" * 50)
    
    # Get environment
    environment = os.environ.get('ENVIRONMENT', 'dev')
    
    # Get AWS account and region
    try:
        sts = boto3.client('sts')
        account = sts.get_caller_identity()['Account']
        region = boto3.Session().region_name or 'ap-south-1'
    except Exception as e:
        print(f"❌ Could not get AWS credentials: {e}")
        sys.exit(1)
    
    print(f"Environment: {environment}")
    print(f"Account: {account}")
    print(f"Region: {region}")
    print()
    
    # Initialize CDK app
    app = App()
    env = Environment(account=account, region=region)
    
    # Create the wrapper stack
    print("📱 Creating device status monitor stack...")
    DeviceStatusMonitorApp(
        app, f"AquaChain-DeviceStatusMonitor-{environment}",
        env=env
    )
    
    print("✅ CDK app configured successfully")
    print()
    
    # Synthesize the app
    app.synth()
    
    print("✅ Ready to deploy!")
    print()
    print("To deploy, run:")
    print(f"  cdk deploy AquaChain-DeviceStatusMonitor-{environment}")
    print()


if __name__ == "__main__":
    main()