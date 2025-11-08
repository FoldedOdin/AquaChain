#!/usr/bin/env python3
"""
AquaChain Blue-Green Deployment Script
Handles automated deployment with rollback capabilities
"""

import argparse
import boto3
import json
import time
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

class AquaChainDeployment:
    def __init__(self, region: str, environment: str):
        self.region = region
        self.environment = environment
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudfront_client = boto3.client('cloudfront', region_name=region)
        self.apigateway_client = boto3.client('apigateway', region_name=region)
        
        # Get account ID
        sts_client = boto3.client('sts', region_name=region)
        self.account_id = sts_client.get_caller_identity()['Account']
        
        self.lambda_functions = [
            'data-processing',
            'ml-inference',
            'ledger-service',
            'audit-trail-processor',
            'alert-detection',
            'notification-service',
            'auth-service',
            'user-management',
            'technician-service',
            'api-gateway',
            'websocket-api'
        ]
    
    def deploy(self, deployment_package_path: str, validate_only: bool = False) -> bool:
        """
        Execute blue-green deployment.
        
        Args:
            deployment_package_path: Path to deployment packages
            validate_only: If True, only validate without switching traffic
            
        Returns:
            bool: True if deployment successful, False otherwise
        """
        try:
            print(f"🚀 Starting AquaChain deployment to {self.environment}")
            print(f"Region: {self.region}")
            print(f"Account: {self.account_id}")
            print(f"Validate only: {validate_only}")
            print("-" * 60)
            
            # Step 1: Deploy Lambda functions to GREEN
            print("📦 Deploying Lambda functions to GREEN environment...")
            green_versions = self.deploy_lambda_functions(deployment_package_path)
            
            # Step 2: Deploy frontend to GREEN S3 bucket
            print("🌐 Deploying frontend to GREEN environment...")
            self.deploy_frontend_green(deployment_package_path)
            
            # Step 3: Validate GREEN environment
            print("🔍 Validating GREEN environment...")
            validation_success = self.validate_green_environment(green_versions)
            
            if not validation_success:
                print("❌ GREEN environment validation failed")
                return False
            
            if validate_only:
                print("✅ Validation completed successfully (validate-only mode)")
                return True
            
            # Step 4: Switch traffic to GREEN
            print("🔄 Switching traffic to GREEN environment...")
            self.switch_traffic_to_green(green_versions)
            
            # Step 5: Final validation
            print("🔍 Running post-deployment validation...")
            final_validation = self.validate_production_environment()
            
            if not final_validation:
                print("❌ Post-deployment validation failed, initiating rollback...")
                self.rollback_deployment()
                return False
            
            # Step 6: Update BLUE aliases for future rollback
            print("💾 Updating BLUE aliases for rollback capability...")
            self.update_blue_aliases()
            
            print("🎉 Deployment completed successfully!")
            return True
            
        except Exception as e:
            print(f"💥 Deployment failed: {str(e)}")
            if not validate_only:
                print("🔄 Initiating rollback...")
                self.rollback_deployment()
            return False
    
    def deploy_lambda_functions(self, package_path: str) -> Dict[str, str]:
        """Deploy Lambda functions and return GREEN version numbers."""
        green_versions = {}
        
        for function_name in self.lambda_functions:
            full_function_name = f"AquaChain-{function_name}-{self.environment}"
            package_file = os.path.join(package_path, f"{function_name}-deployment.zip")
            
            if not os.path.exists(package_file):
                print(f"⚠️  Package not found: {package_file}, skipping...")
                continue
            
            print(f"  Deploying {function_name}...")
            
            try:
                # Update function code
                with open(package_file, 'rb') as f:
                    zip_content = f.read()
                
                self.lambda_client.update_function_code(
                    FunctionName=full_function_name,
                    ZipFile=zip_content
                )
                
                # Wait for update to complete
                self.lambda_client.get_waiter('function_updated').wait(
                    FunctionName=full_function_name,
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 60}
                )
                
                # Publish new version
                version_response = self.lambda_client.publish_version(
                    FunctionName=full_function_name,
                    Description=f"Deployment {datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
                )
                
                version_number = version_response['Version']
                green_versions[function_name] = version_number
                
                # Update GREEN alias
                try:
                    self.lambda_client.update_alias(
                        FunctionName=full_function_name,
                        Name='GREEN',
                        FunctionVersion=version_number
                    )
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # Create alias if it doesn't exist
                    self.lambda_client.create_alias(
                        FunctionName=full_function_name,
                        Name='GREEN',
                        FunctionVersion=version_number
                    )
                
                print(f"    ✅ {function_name} deployed to version {version_number}")
                
            except Exception as e:
                print(f"    ❌ Failed to deploy {function_name}: {str(e)}")
                raise
        
        return green_versions
    
    def deploy_frontend_green(self, package_path: str):
        """Deploy frontend to GREEN S3 bucket."""
        frontend_build_path = os.path.join(package_path, 'frontend', 'build')
        green_bucket = f"aquachain-frontend-green-{self.account_id}"
        
        if not os.path.exists(frontend_build_path):
            print(f"⚠️  Frontend build not found: {frontend_build_path}")
            return
        
        try:
            # Upload files to GREEN bucket
            for root, dirs, files in os.walk(frontend_build_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, frontend_build_path)
                    s3_key = relative_path.replace('\\', '/')  # Handle Windows paths
                    
                    # Determine content type
                    content_type = self.get_content_type(file)
                    
                    with open(local_path, 'rb') as f:
                        self.s3_client.put_object(
                            Bucket=green_bucket,
                            Key=s3_key,
                            Body=f.read(),
                            ContentType=content_type
                        )
            
            print(f"    ✅ Frontend deployed to {green_bucket}")
            
        except Exception as e:
            print(f"    ❌ Failed to deploy frontend: {str(e)}")
            raise
    
    def validate_green_environment(self, green_versions: Dict[str, str]) -> bool:
        """Validate GREEN environment functionality."""
        print("  Running GREEN environment validation...")
        
        try:
            # Test Lambda functions
            for function_name, version in green_versions.items():
                full_function_name = f"AquaChain-{function_name}-{self.environment}"
                
                # Invoke function with test payload
                test_payload = self.get_test_payload(function_name)
                
                response = self.lambda_client.invoke(
                    FunctionName=f"{full_function_name}:GREEN",
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_payload)
                )
                
                if response['StatusCode'] != 200:
                    print(f"    ❌ Function {function_name} validation failed")
                    return False
                
                # Check for function errors
                payload = json.loads(response['Payload'].read())
                if 'errorMessage' in payload:
                    print(f"    ❌ Function {function_name} returned error: {payload['errorMessage']}")
                    return False
            
            # Test frontend accessibility
            green_bucket = f"aquachain-frontend-green-{self.account_id}"
            try:
                self.s3_client.head_object(Bucket=green_bucket, Key='index.html')
                print("    ✅ Frontend validation passed")
            except Exception:
                print("    ❌ Frontend validation failed")
                return False
            
            print("  ✅ GREEN environment validation passed")
            return True
            
        except Exception as e:
            print(f"  ❌ GREEN environment validation failed: {str(e)}")
            return False
    
    def switch_traffic_to_green(self, green_versions: Dict[str, str]):
        """Switch production traffic to GREEN environment."""
        print("  Switching Lambda traffic to GREEN...")
        
        for function_name, version in green_versions.items():
            full_function_name = f"AquaChain-{function_name}-{self.environment}"
            
            try:
                # Update LIVE alias to point to GREEN version
                try:
                    self.lambda_client.update_alias(
                        FunctionName=full_function_name,
                        Name='LIVE',
                        FunctionVersion=version
                    )
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # Create LIVE alias if it doesn't exist
                    self.lambda_client.create_alias(
                        FunctionName=full_function_name,
                        Name='LIVE',
                        FunctionVersion=version
                    )
                
                print(f"    ✅ {function_name} traffic switched to version {version}")
                
            except Exception as e:
                print(f"    ❌ Failed to switch traffic for {function_name}: {str(e)}")
                raise
        
        # Switch frontend traffic
        print("  Switching frontend traffic to GREEN...")
        try:
            green_bucket = f"aquachain-frontend-green-{self.account_id}"
            production_bucket = f"aquachain-frontend-{self.environment}-{self.account_id}"
            
            # Copy from GREEN to production bucket
            self.sync_s3_buckets(green_bucket, production_bucket)
            
            # Invalidate CloudFront cache
            distribution_id = os.getenv(f'CLOUDFRONT_DISTRIBUTION_ID_{self.environment.upper()}')
            if distribution_id:
                self.cloudfront_client.create_invalidation(
                    DistributionId=distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': 1,
                            'Items': ['/*']
                        },
                        'CallerReference': str(int(time.time()))
                    }
                )
            
            print("    ✅ Frontend traffic switched to GREEN")
            
        except Exception as e:
            print(f"    ❌ Failed to switch frontend traffic: {str(e)}")
            raise
    
    def validate_production_environment(self) -> bool:
        """Validate production environment after traffic switch."""
        print("  Running production validation...")
        
        # Wait for CloudFront invalidation to propagate
        time.sleep(60)
        
        try:
            # Run production validation tests
            validation_script = os.path.join(
                os.path.dirname(__file__), 
                '..', 'tests', 'smoke', 'production_validation_tests.py'
            )
            
            if os.path.exists(validation_script):
                import subprocess
                result = subprocess.run([
                    sys.executable, validation_script
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("  ✅ Production validation passed")
                    return True
                else:
                    print(f"  ❌ Production validation failed: {result.stderr}")
                    return False
            else:
                print("  ⚠️  Production validation script not found, skipping...")
                return True
                
        except Exception as e:
            print(f"  ❌ Production validation error: {str(e)}")
            return False
    
    def update_blue_aliases(self):
        """Update BLUE aliases to current LIVE versions for rollback."""
        print("  Updating BLUE aliases for rollback capability...")
        
        for function_name in self.lambda_functions:
            full_function_name = f"AquaChain-{function_name}-{self.environment}"
            
            try:
                # Get current LIVE version
                live_alias = self.lambda_client.get_alias(
                    FunctionName=full_function_name,
                    Name='LIVE'
                )
                
                live_version = live_alias['FunctionVersion']
                
                # Update BLUE alias to previous LIVE version
                try:
                    blue_alias = self.lambda_client.get_alias(
                        FunctionName=full_function_name,
                        Name='BLUE'
                    )
                    blue_version = blue_alias['FunctionVersion']
                    
                    # Keep BLUE as the previous version
                    # (In a real implementation, you'd track version history)
                    
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # Create BLUE alias with current LIVE version
                    self.lambda_client.create_alias(
                        FunctionName=full_function_name,
                        Name='BLUE',
                        FunctionVersion=live_version
                    )
                
            except Exception as e:
                print(f"    ⚠️  Failed to update BLUE alias for {function_name}: {str(e)}")
    
    def rollback_deployment(self):
        """Rollback to BLUE environment."""
        print("🔄 Rolling back to BLUE environment...")
        
        try:
            # Rollback Lambda functions
            for function_name in self.lambda_functions:
                full_function_name = f"AquaChain-{function_name}-{self.environment}"
                
                try:
                    # Get BLUE version
                    blue_alias = self.lambda_client.get_alias(
                        FunctionName=full_function_name,
                        Name='BLUE'
                    )
                    
                    blue_version = blue_alias['FunctionVersion']
                    
                    # Switch LIVE back to BLUE
                    self.lambda_client.update_alias(
                        FunctionName=full_function_name,
                        Name='LIVE',
                        FunctionVersion=blue_version
                    )
                    
                    print(f"    ✅ {function_name} rolled back to version {blue_version}")
                    
                except Exception as e:
                    print(f"    ❌ Failed to rollback {function_name}: {str(e)}")
            
            # Rollback frontend
            try:
                blue_bucket = f"aquachain-frontend-blue-{self.account_id}"
                production_bucket = f"aquachain-frontend-{self.environment}-{self.account_id}"
                
                # Copy from BLUE to production bucket
                self.sync_s3_buckets(blue_bucket, production_bucket)
                
                # Invalidate CloudFront cache
                distribution_id = os.getenv(f'CLOUDFRONT_DISTRIBUTION_ID_{self.environment.upper()}')
                if distribution_id:
                    self.cloudfront_client.create_invalidation(
                        DistributionId=distribution_id,
                        InvalidationBatch={
                            'Paths': {
                                'Quantity': 1,
                                'Items': ['/*']
                            },
                            'CallerReference': str(int(time.time()))
                        }
                    )
                
                print("    ✅ Frontend rolled back to BLUE")
                
            except Exception as e:
                print(f"    ❌ Failed to rollback frontend: {str(e)}")
            
            print("🎯 Rollback completed")
            
        except Exception as e:
            print(f"💥 Rollback failed: {str(e)}")
    
    def get_test_payload(self, function_name: str) -> dict:
        """Get test payload for function validation."""
        if function_name == 'data-processing':
            return {
                "deviceId": "TEST-VALIDATION",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "readings": {
                    "pH": 7.0,
                    "turbidity": 1.0,
                    "tds": 150,
                    "temperature": 25.0
                }
            }
        else:
            return {"test": True, "validation": True}
    
    def get_content_type(self, filename: str) -> str:
        """Get content type for file."""
        extension = os.path.splitext(filename)[1].lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon'
        }
        return content_types.get(extension, 'binary/octet-stream')
    
    def sync_s3_buckets(self, source_bucket: str, dest_bucket: str):
        """Sync contents between S3 buckets."""
        # List objects in source bucket
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=source_bucket)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Copy object to destination bucket
                    copy_source = {'Bucket': source_bucket, 'Key': obj['Key']}
                    self.s3_client.copy_object(
                        CopySource=copy_source,
                        Bucket=dest_bucket,
                        Key=obj['Key']
                    )

def main():
    parser = argparse.ArgumentParser(description='AquaChain Blue-Green Deployment')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--environment', required=True, choices=['staging', 'production'], help='Deployment environment')
    parser.add_argument('--package-path', required=True, help='Path to deployment packages')
    parser.add_argument('--validate-only', action='store_true', help='Only validate, do not switch traffic')
    parser.add_argument('--rollback', action='store_true', help='Rollback to previous deployment')
    
    args = parser.parse_args()
    
    deployment = AquaChainDeployment(args.region, args.environment)
    
    if args.rollback:
        deployment.rollback_deployment()
        return 0
    
    success = deployment.deploy(args.package_path, args.validate_only)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())