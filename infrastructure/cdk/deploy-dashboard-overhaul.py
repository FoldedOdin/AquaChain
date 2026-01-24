#!/usr/bin/env python3
"""
Dashboard Overhaul Infrastructure Deployment Script
Deploys the dashboard overhaul stack with proper validation and error handling
"""

import subprocess
import sys
import os
import json
import time
from typing import Dict, Any

def run_command(command: str, cwd: str = None) -> tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, stderr
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 30 minutes"
    except Exception as e:
        return 1, "", str(e)

def check_prerequisites() -> bool:
    """
    Check that all prerequisites are met for deployment
    """
    print("Checking prerequisites...")
    
    # Check AWS CLI
    exit_code, stdout, stderr = run_command("aws --version")
    if exit_code != 0:
        print("❌ AWS CLI not found. Please install AWS CLI.")
        return False
    print(f"✅ AWS CLI: {stdout.strip()}")
    
    # Check AWS credentials
    exit_code, stdout, stderr = run_command("aws sts get-caller-identity")
    if exit_code != 0:
        print("❌ AWS credentials not configured. Please run 'aws configure'.")
        return False
    
    identity = json.loads(stdout)
    print(f"✅ AWS Identity: {identity.get('Arn', 'Unknown')}")
    
    # Check CDK CLI
    exit_code, stdout, stderr = run_command("cdk --version")
    if exit_code != 0:
        print("❌ CDK CLI not found. Please install CDK CLI: npm install -g aws-cdk")
        return False
    print(f"✅ CDK CLI: {stdout.strip()}")
    
    # Check Python dependencies
    try:
        import aws_cdk
        print(f"✅ AWS CDK Python: {aws_cdk.__version__}")
    except ImportError:
        print("❌ AWS CDK Python library not found. Please run: pip install aws-cdk-lib")
        return False
    
    return True

def bootstrap_cdk(environment: str) -> bool:
    """
    Bootstrap CDK for the target environment
    """
    print(f"\nBootstrapping CDK for environment: {environment}")
    
    # Get AWS account and region
    exit_code, stdout, stderr = run_command("aws sts get-caller-identity")
    if exit_code != 0:
        print(f"❌ Failed to get AWS account: {stderr}")
        return False
    
    identity = json.loads(stdout)
    account = identity["Account"]
    
    exit_code, stdout, stderr = run_command("aws configure get region")
    if exit_code != 0:
        print("❌ AWS region not configured. Please set default region.")
        return False
    
    region = stdout.strip()
    
    print(f"Bootstrapping CDK for account {account} in region {region}")
    
    bootstrap_command = f"cdk bootstrap aws://{account}/{region}"
    exit_code, stdout, stderr = run_command(bootstrap_command, cwd="infrastructure/cdk")
    
    if exit_code != 0:
        print(f"❌ CDK bootstrap failed: {stderr}")
        return False
    
    print("✅ CDK bootstrap completed")
    return True

def deploy_stack(environment: str, stack_name: str) -> bool:
    """
    Deploy the dashboard overhaul stack
    """
    print(f"\nDeploying {stack_name} for environment: {environment}")
    
    deploy_command = f"cdk deploy {stack_name} --context environment={environment} --require-approval never"
    
    print(f"Running: {deploy_command}")
    exit_code, stdout, stderr = run_command(deploy_command, cwd="infrastructure/cdk")
    
    if exit_code != 0:
        print(f"❌ Deployment failed: {stderr}")
        print(f"Stdout: {stdout}")
        return False
    
    print("✅ Deployment completed successfully")
    print(stdout)
    return True

def validate_deployment(environment: str) -> bool:
    """
    Validate that the deployment was successful
    """
    print(f"\nValidating deployment for environment: {environment}")
    
    # List stacks to verify deployment
    list_command = "cdk list --context environment=" + environment
    exit_code, stdout, stderr = run_command(list_command, cwd="infrastructure/cdk")
    
    if exit_code != 0:
        print(f"❌ Failed to list stacks: {stderr}")
        return False
    
    stack_name = f"AquaChain-DashboardOverhaul-{environment}"
    if stack_name not in stdout:
        print(f"❌ Stack {stack_name} not found in CDK list")
        return False
    
    print(f"✅ Stack {stack_name} found in CDK list")
    
    # Check AWS CloudFormation stack status
    cf_command = f"aws cloudformation describe-stacks --stack-name {stack_name}"
    exit_code, stdout, stderr = run_command(cf_command)
    
    if exit_code != 0:
        print(f"❌ Failed to describe CloudFormation stack: {stderr}")
        return False
    
    stack_info = json.loads(stdout)
    stack_status = stack_info["Stacks"][0]["StackStatus"]
    
    if stack_status not in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
        print(f"❌ Stack status is {stack_status}, expected CREATE_COMPLETE or UPDATE_COMPLETE")
        return False
    
    print(f"✅ CloudFormation stack status: {stack_status}")
    return True

def main():
    """
    Main deployment function
    """
    print("=== AquaChain Dashboard Overhaul Infrastructure Deployment ===\n")
    
    # Parse command line arguments
    if len(sys.argv) != 2:
        print("Usage: python deploy-dashboard-overhaul.py <environment>")
        print("Environment: dev, staging, or prod")
        sys.exit(1)
    
    environment = sys.argv[1]
    if environment not in ["dev", "staging", "prod"]:
        print("❌ Invalid environment. Must be dev, staging, or prod")
        sys.exit(1)
    
    print(f"Deploying Dashboard Overhaul infrastructure for environment: {environment}")
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Step 2: Bootstrap CDK (if needed)
    if not bootstrap_cdk(environment):
        print("\n❌ CDK bootstrap failed.")
        sys.exit(1)
    
    # Step 3: Deploy the stack
    stack_name = f"AquaChain-DashboardOverhaul-{environment}"
    if not deploy_stack(environment, stack_name):
        print(f"\n❌ Deployment of {stack_name} failed.")
        sys.exit(1)
    
    # Step 4: Validate deployment
    if not validate_deployment(environment):
        print(f"\n❌ Deployment validation failed.")
        sys.exit(1)
    
    print(f"\n🎉 Dashboard Overhaul infrastructure successfully deployed for {environment}!")
    print("\nNext steps:")
    print("1. Deploy Lambda functions for the dashboard services")
    print("2. Configure Cognito user groups and initial users")
    print("3. Test API endpoints and authentication")
    print("4. Deploy frontend applications")

if __name__ == "__main__":
    main()