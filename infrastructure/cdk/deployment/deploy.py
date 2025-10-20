#!/usr/bin/env python3
"""
CDK deployment script with environment-specific configuration
"""

import os
import sys
import subprocess
import argparse
import json
from typing import Dict, Any, List

class AquaChainCDKDeployer:
    """
    CDK deployment manager for AquaChain infrastructure
    """
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.account_id = self._get_account_id()
        
        # Stack deployment order
        self.stack_order = [
            "Security",
            "Core", 
            "Data",
            "Compute",
            "API",
            "Monitoring"
        ]
    
    def _get_account_id(self) -> str:
        """Get current AWS account ID"""
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting account ID: {e}")
            sys.exit(1)
    
    def bootstrap_cdk(self) -> bool:
        """
        Bootstrap CDK in the target account/region
        """
        print(f"Bootstrapping CDK in account {self.account_id}, region {self.region}...")
        
        try:
            subprocess.run([
                "cdk", "bootstrap",
                f"aws://{self.account_id}/{self.region}",
                "--context", f"environment={self.environment}"
            ], check=True)
            
            print("✓ CDK bootstrap completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ CDK bootstrap failed: {e}")
            return False
    
    def synthesize_stacks(self) -> bool:
        """
        Synthesize CDK stacks to CloudFormation templates
        """
        print("Synthesizing CDK stacks...")
        
        try:
            subprocess.run([
                "cdk", "synth",
                "--context", f"environment={self.environment}",
                "--output", f"cdk.out.{self.environment}"
            ], check=True)
            
            print("✓ Stack synthesis completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Stack synthesis failed: {e}")
            return False
    
    def deploy_stack(self, stack_type: str, require_approval: bool = True) -> bool:
        """
        Deploy a specific stack
        """
        stack_name = f"AquaChain-{stack_type}-{self.environment.title()}"
        
        print(f"Deploying stack: {stack_name}")
        
        cmd = [
            "cdk", "deploy", stack_name,
            "--context", f"environment={self.environment}",
            "--outputs-file", f"outputs-{stack_type.lower()}-{self.environment}.json"
        ]
        
        if not require_approval:
            cmd.append("--require-approval=never")
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✓ Stack {stack_name} deployed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Stack {stack_name} deployment failed: {e}")
            return False
    
    def deploy_all_stacks(self, require_approval: bool = True) -> bool:
        """
        Deploy all stacks in the correct order
        """
        print(f"Deploying all AquaChain stacks for environment: {self.environment}")
        print("=" * 60)
        
        failed_stacks = []
        
        for stack_type in self.stack_order:
            if not self.deploy_stack(stack_type, require_approval):
                failed_stacks.append(stack_type)
                
                # Ask if we should continue with remaining stacks
                if input(f"Stack {stack_type} failed. Continue with remaining stacks? (y/n): ").lower() != 'y':
                    break
        
        if failed_stacks:
            print(f"\n✗ Deployment completed with failures: {failed_stacks}")
            return False
        else:
            print(f"\n✓ All stacks deployed successfully for environment: {self.environment}")
            return True
    
    def destroy_stacks(self, stack_types: List[str] = None) -> bool:
        """
        Destroy specified stacks or all stacks
        """
        if stack_types is None:
            stack_types = list(reversed(self.stack_order))  # Reverse order for destruction
        
        print(f"Destroying stacks: {stack_types}")
        
        # Confirmation for production
        if self.environment == "prod":
            confirmation = input("You are about to destroy PRODUCTION infrastructure. Type 'DELETE' to confirm: ")
            if confirmation != "DELETE":
                print("Destruction cancelled")
                return False
        
        failed_stacks = []
        
        for stack_type in stack_types:
            stack_name = f"AquaChain-{stack_type}-{self.environment.title()}"
            
            try:
                subprocess.run([
                    "cdk", "destroy", stack_name,
                    "--context", f"environment={self.environment}",
                    "--force"
                ], check=True)
                
                print(f"✓ Stack {stack_name} destroyed successfully")
                
            except subprocess.CalledProcessError as e:
                print(f"✗ Stack {stack_name} destruction failed: {e}")
                failed_stacks.append(stack_type)
        
        if failed_stacks:
            print(f"\n✗ Destruction completed with failures: {failed_stacks}")
            return False
        else:
            print(f"\n✓ All specified stacks destroyed successfully")
            return True
    
    def diff_stacks(self) -> bool:
        """
        Show differences between deployed and local stacks
        """
        print(f"Showing stack differences for environment: {self.environment}")
        
        try:
            subprocess.run([
                "cdk", "diff",
                "--context", f"environment={self.environment}"
            ], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Stack diff failed: {e}")
            return False
    
    def list_stacks(self) -> bool:
        """
        List all stacks for the environment
        """
        print(f"Listing stacks for environment: {self.environment}")
        
        try:
            subprocess.run([
                "cdk", "list",
                "--context", f"environment={self.environment}"
            ], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Stack listing failed: {e}")
            return False
    
    def validate_environment(self) -> bool:
        """
        Validate that the environment is properly configured
        """
        print(f"Validating environment configuration for: {self.environment}")
        
        # Check AWS credentials
        try:
            subprocess.run(["aws", "sts", "get-caller-identity"], 
                         capture_output=True, check=True)
            print("✓ AWS credentials configured")
        except subprocess.CalledProcessError:
            print("✗ AWS credentials not configured")
            return False
        
        # Check CDK installation
        try:
            subprocess.run(["cdk", "--version"], 
                         capture_output=True, check=True)
            print("✓ CDK CLI installed")
        except subprocess.CalledProcessError:
            print("✗ CDK CLI not installed")
            return False
        
        # Check Python dependencies
        try:
            import aws_cdk_lib
            print("✓ CDK Python libraries installed")
        except ImportError:
            print("✗ CDK Python libraries not installed")
            return False
        
        return True

def main():
    """
    Main deployment script
    """
    parser = argparse.ArgumentParser(description="Deploy AquaChain CDK infrastructure")
    parser.add_argument("--environment", "-e", required=True, 
                       choices=["dev", "staging", "prod"],
                       help="Target environment")
    parser.add_argument("--region", "-r", default="us-east-1",
                       help="AWS region")
    parser.add_argument("--action", "-a", required=True,
                       choices=["bootstrap", "synth", "deploy", "destroy", "diff", "list"],
                       help="Action to perform")
    parser.add_argument("--stack", "-s", 
                       choices=["Security", "Core", "Data", "Compute", "API", "Monitoring"],
                       help="Specific stack to operate on")
    parser.add_argument("--auto-approve", action="store_true",
                       help="Skip approval prompts")
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["CDK_DEFAULT_REGION"] = args.region
    
    # Create deployer
    deployer = AquaChainCDKDeployer(args.environment, args.region)
    
    # Validate environment
    if not deployer.validate_environment():
        print("Environment validation failed")
        sys.exit(1)
    
    # Execute requested action
    success = False
    
    if args.action == "bootstrap":
        success = deployer.bootstrap_cdk()
    
    elif args.action == "synth":
        success = deployer.synthesize_stacks()
    
    elif args.action == "deploy":
        if args.stack:
            success = deployer.deploy_stack(args.stack, not args.auto_approve)
        else:
            success = deployer.deploy_all_stacks(not args.auto_approve)
    
    elif args.action == "destroy":
        if args.stack:
            success = deployer.destroy_stacks([args.stack])
        else:
            success = deployer.destroy_stacks()
    
    elif args.action == "diff":
        success = deployer.diff_stacks()
    
    elif args.action == "list":
        success = deployer.list_stacks()
    
    if success:
        print(f"\n✓ Action '{args.action}' completed successfully")
        sys.exit(0)
    else:
        print(f"\n✗ Action '{args.action}' failed")
        sys.exit(1)

if __name__ == "__main__":
    main()