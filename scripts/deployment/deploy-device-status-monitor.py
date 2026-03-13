#!/usr/bin/env python3
"""
Deploy Device Status Monitor Infrastructure
Creates Lambda function and CloudWatch Events for monitoring device online/offline status
"""

import os
import sys
import boto3
import json
from datetime import datetime

# Add the infrastructure directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure', 'cdk'))

from aws_cdk import App, Environment
from stacks.device_status_monitor_stack import DeviceStatusMonitorStack
from stacks.data_stack import AquaChainDataStack
from config.environment_config import get_environment_config


def main():
    """Deploy device status monitor infrastructure"""
    
    print("🚀 Deploying Device Status Monitor Infrastructure")
    print("=" * 60)
    
    # Get environment
    environment = os.environ.get('ENVIRONMENT', 'dev')
    print(f"Environment: {environment}")
    
    # Get AWS account and region
    account = os.environ.get('CDK_DEFAULT_ACCOUNT')
    region = os.environ.get('CDK_DEFAULT_REGION', 'ap-south-1')
    
    if not account:
        print("❌ CDK_DEFAULT_ACCOUNT environment variable not set")
        print("Getting account from AWS CLI...")
        try:
            sts = boto3.client('sts')
            account = sts.get_caller_identity()['Account']
            print(f"✅ Found account: {account}")
        except Exception as e:
            print(f"❌ Could not get AWS account: {e}")
            sys.exit(1)
    
    print(f"Account: {account}")
    print(f"Region: {region}")
    print()
    
    # Initialize CDK app
    app = App()
    
    # Get environment config
    config = get_environment_config(environment)
    
    # Create environment object
    env = Environment(account=account, region=region)
    
    try:
        # Import existing data stack resources
        print("📊 Importing existing data stack resources...")
        data_stack = AquaChainDataStack(
            app, f"AquaChain-Data-Import-{environment}",
            config=config,
            kms_key=None,  # Will be imported
            ledger_signing_key=None,  # Will be imported
            env=env
        )
        
        # Create device status monitor stack
        print("📱 Creating device status monitor stack...")
        monitor_stack = DeviceStatusMonitorStack(
            app, f"AquaChain-DeviceStatusMonitor-{environment}",
            config=config,
            devices_table=data_stack.devices_table,
            readings_table=data_stack.readings_table,
            env=env
        )
        
        # Add dependency
        monitor_stack.add_dependency(data_stack)
        
        print("✅ CDK stacks configured successfully")
        print()
        
        # Synthesize the app
        print("🔨 Synthesizing CDK stacks...")
        app.synth()
        
        print("✅ Device Status Monitor infrastructure ready for deployment")
        print()
        print("To deploy, run:")
        print(f"  cdk deploy AquaChain-DeviceStatusMonitor-{environment}")
        print()
        print("📊 Monitoring Features:")
        print("  • Device online/offline status tracking")
        print("  • Scheduled status checks every 2 minutes")
        print("  • CloudWatch metrics and alarms")
        print("  • Dashboard for device connectivity")
        print()
        
    except Exception as e:
        print(f"❌ Error deploying device status monitor: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()