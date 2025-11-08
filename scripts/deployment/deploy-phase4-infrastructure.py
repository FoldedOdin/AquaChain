#!/usr/bin/env python3
"""
Phase 4 Infrastructure Deployment Script

This script deploys all Phase 4 infrastructure components including:
- Data Classification Stack (KMS keys for PII and Sensitive data)
- Audit Logging Stack (Kinesis Firehose, S3 with Object Lock)
- GDPR Compliance Stack (S3 buckets, DynamoDB tables)
- Lambda Layers Stack (Shared dependencies)
- Lambda Performance Stack (Provisioned concurrency)
- Cache Stack (ElastiCache Redis)
- CloudFront Stack (CDN for frontend)

The script uses AWS CDK to deploy infrastructure as code.
"""

import argparse
import boto3
import json
import sys
import time
import subprocess
import os
from typing import Dict, List, Optional
from pathlib import Path


class Phase4InfrastructureDeployer:
    """Deploys Phase 4 infrastructure components using CDK"""
    
    def __init__(self, region: str, environment: str, dry_run: bool = False):
        self.region = region
        self.environment = environment
        self.dry_run = dry_run
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        
        # Get account ID
        self.account_id = self.sts.get_caller_identity()['Account']
        
        # CDK stacks to deploy for Phase 4
        self.phase4_stacks = [
            'AquaChain-DataClassification',
            'AquaChain-AuditLogging',
            'AquaChain-GDPRCompliance',
            'AquaChain-LambdaLayers',
            'AquaChain-LambdaPerformance',
            'AquaChain-Cache',
            'AquaChain-CloudFront'
        ]
        
    def deploy_all(self) -> bool:
        """Deploy all Phase 4 infrastructure components using CDK"""
        print(f"🚀 Deploying Phase 4 infrastructure to {self.environment} in {self.region}")
        print(f"   Account: {self.account_id}")
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
            return self._dry_run_deployment()
        
        # Step 1: Verify CDK is installed
        if not self._verify_cdk_installed():
            return False
        
        # Step 2: Bootstrap CDK (if needed)
        if not self._bootstrap_cdk():
            return False
        
        # Step 3: Build Lambda layers
        if not self._build_lambda_layers():
            return False
        
        # Step 4: Deploy CDK stacks
        if not self._deploy_cdk_stacks():
            return False
        
        # Step 5: Verify deployment
        if not self._verify_deployment():
            return False
        
        # Step 6: Display outputs
        self._display_outputs()
        
        print("\n🎉 Phase 4 infrastructure deployment completed successfully!")
        return True
    
    def _verify_cdk_installed(self) -> bool:
        """Verify AWS CDK is installed"""
        print("\n📋 Verifying AWS CDK installation...")
        try:
            result = subprocess.run(
                ['cdk', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"   ✅ CDK version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ❌ AWS CDK not found. Please install it:")
            print("      npm install -g aws-cdk")
            return False
    
    def _bootstrap_cdk(self) -> bool:
        """Bootstrap CDK in the target account/region"""
        print(f"\n📋 Checking CDK bootstrap status...")
        
        # Check if bootstrap stack exists
        try:
            self.cloudformation.describe_stacks(
                StackName='CDKToolkit'
            )
            print("   ✅ CDK already bootstrapped")
            return True
        except self.cloudformation.exceptions.ClientError:
            print("   ⚠️  CDK not bootstrapped, bootstrapping now...")
            
            try:
                cdk_dir = Path(__file__).parent.parent / 'infrastructure' / 'cdk'
                result = subprocess.run(
                    ['cdk', 'bootstrap', f'aws://{self.account_id}/{self.region}'],
                    cwd=str(cdk_dir),
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("   ✅ CDK bootstrapped successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to bootstrap CDK: {e.stderr}")
                return False
    
    def _build_lambda_layers(self) -> bool:
        """Build Lambda layers before deployment"""
        print("\n📦 Building Lambda layers...")
        
        layers_dir = Path(__file__).parent.parent / 'lambda' / 'layers'
        
        # Check if build script exists
        build_script = layers_dir / 'build-layers.sh'
        if not build_script.exists():
            print("   ⚠️  Build script not found, skipping layer build")
            return True
        
        try:
            # Make script executable
            os.chmod(build_script, 0o755)
            
            # Run build script
            result = subprocess.run(
                [str(build_script)],
                cwd=str(layers_dir),
                capture_output=True,
                text=True,
                check=True
            )
            print("   ✅ Lambda layers built successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Failed to build layers: {e.stderr}")
            print("   Continuing with deployment...")
            return True  # Don't fail deployment if layers can't be built
    
    def _deploy_cdk_stacks(self) -> bool:
        """Deploy CDK stacks for Phase 4"""
        print("\n📦 Deploying CDK stacks...")
        
        cdk_dir = Path(__file__).parent.parent / 'infrastructure' / 'cdk'
        
        # Deploy each stack
        for stack_name in self.phase4_stacks:
            full_stack_name = f"{stack_name}-{self.environment}"
            print(f"\n   Deploying {full_stack_name}...")
            
            try:
                result = subprocess.run(
                    [
                        'cdk', 'deploy', full_stack_name,
                        '--require-approval', 'never',
                        '--context', f'environment={self.environment}',
                        '--outputs-file', f'cdk-outputs-{self.environment}.json'
                    ],
                    cwd=str(cdk_dir),
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"   ✅ {full_stack_name} deployed successfully")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to deploy {full_stack_name}")
                print(f"   Error: {e.stderr}")
                return False
        
        return True
    
    def _verify_deployment(self) -> bool:
        """Verify all stacks were deployed successfully"""
        print("\n🔍 Verifying deployment...")
        
        all_deployed = True
        for stack_name in self.phase4_stacks:
            full_stack_name = f"{stack_name}-{self.environment}"
            
            try:
                response = self.cloudformation.describe_stacks(
                    StackName=full_stack_name
                )
                
                stack = response['Stacks'][0]
                status = stack['StackStatus']
                
                if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                    print(f"   ✅ {full_stack_name}: {status}")
                else:
                    print(f"   ⚠️  {full_stack_name}: {status}")
                    all_deployed = False
                    
            except self.cloudformation.exceptions.ClientError as e:
                print(f"   ❌ {full_stack_name}: Not found")
                all_deployed = False
        
        return all_deployed
    
    def _display_outputs(self) -> None:
        """Display important outputs from deployed stacks"""
        print("\n📊 Deployment Outputs:")
        print("=" * 80)
        
        for stack_name in self.phase4_stacks:
            full_stack_name = f"{stack_name}-{self.environment}"
            
            try:
                response = self.cloudformation.describe_stacks(
                    StackName=full_stack_name
                )
                
                stack = response['Stacks'][0]
                outputs = stack.get('Outputs', [])
                
                if outputs:
                    print(f"\n{full_stack_name}:")
                    for output in outputs:
                        key = output['OutputKey']
                        value = output['OutputValue']
                        description = output.get('Description', '')
                        print(f"  • {key}: {value}")
                        if description:
                            print(f"    {description}")
                            
            except self.cloudformation.exceptions.ClientError:
                continue
        
        print("\n" + "=" * 80)
    
    def _dry_run_deployment(self) -> bool:
        """Perform a dry run to show what would be deployed"""
        print("\n📋 Phase 4 Stacks to Deploy:")
        for i, stack_name in enumerate(self.phase4_stacks, 1):
            full_stack_name = f"{stack_name}-{self.environment}"
            print(f"   {i}. {full_stack_name}")
        
        print("\n📋 Components:")
        print("   • KMS Keys (PII and Sensitive data encryption)")
        print("   • Kinesis Firehose (Audit log streaming)")
        print("   • S3 Buckets (GDPR exports, compliance reports, audit logs)")
        print("   • DynamoDB Tables (GDPRRequests, UserConsents, AuditLogs)")
        print("   • Lambda Layers (Common and ML dependencies)")
        print("   • Lambda Functions (Optimized with provisioned concurrency)")
        print("   • ElastiCache Redis (Caching layer)")
        print("   • CloudFront Distribution (CDN for frontend)")
        
        print("\n✅ Dry run complete. Use --deploy to actually deploy.")
        return True
    



def main():
    parser = argparse.ArgumentParser(
        description='Deploy Phase 4 infrastructure components using AWS CDK',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be deployed
  python deploy-phase4-infrastructure.py --environment dev --dry-run
  
  # Deploy to development environment
  python deploy-phase4-infrastructure.py --environment dev
  
  # Deploy to staging environment in specific region
  python deploy-phase4-infrastructure.py --environment staging --region us-west-2
  
  # Deploy to production
  python deploy-phase4-infrastructure.py --environment prod

Phase 4 Components:
  - Data Classification (KMS keys for PII and Sensitive data)
  - Audit Logging (Kinesis Firehose, S3 with Object Lock)
  - GDPR Compliance (S3 buckets, DynamoDB tables)
  - Lambda Layers (Shared dependencies)
  - Lambda Performance (Provisioned concurrency)
  - Cache (ElastiCache Redis)
  - CloudFront (CDN for frontend)
        """
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region for deployment (default: us-east-1)'
    )
    parser.add_argument(
        '--environment',
        required=True,
        choices=['dev', 'staging', 'prod'],
        help='Deployment environment'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set AWS region environment variable
    os.environ['AWS_DEFAULT_REGION'] = args.region
    os.environ['CDK_DEFAULT_REGION'] = args.region
    
    print("=" * 80)
    print("Phase 4 Infrastructure Deployment")
    print("=" * 80)
    print(f"Environment: {args.environment}")
    print(f"Region: {args.region}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'DEPLOY'}")
    print("=" * 80)
    
    deployer = Phase4InfrastructureDeployer(
        region=args.region,
        environment=args.environment,
        dry_run=args.dry_run
    )
    
    try:
        if deployer.deploy_all():
            print("\n✅ Deployment completed successfully!")
            return 0
        else:
            print("\n❌ Deployment failed!")
            return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
