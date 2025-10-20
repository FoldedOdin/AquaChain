#!/usr/bin/env python3
"""
AquaChain Emergency Rollback Script
Quickly rollback to previous stable deployment
"""

import argparse
import boto3
import json
import time
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

class AquaChainRollback:
    def __init__(self, region: str, environment: str):
        self.region = region
        self.environment = environment
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudfront_client = boto3.client('cloudfront', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
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
    
    def emergency_rollback(self, reason: str = "Emergency rollback") -> bool:
        """
        Execute emergency rollback to previous stable version.
        
        Args:
            reason: Reason for rollback
            
        Returns:
            bool: True if rollback successful, False otherwise
        """
        try:
            print(f"🚨 EMERGENCY ROLLBACK INITIATED")
            print(f"Environment: {self.environment}")
            print(f"Region: {self.region}")
            print(f"Reason: {reason}")
            print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
            print("-" * 60)
            
            # Step 1: Check current system health
            print("🔍 Checking current system health...")
            health_status = self.check_system_health()
            print(f"System health: {health_status}")
            
            # Step 2: Rollback Lambda functions
            print("🔄 Rolling back Lambda functions...")
            lambda_rollback_success = self.rollback_lambda_functions()
            
            # Step 3: Rollback frontend
            print("🌐 Rolling back frontend...")
            frontend_rollback_success = self.rollback_frontend()
            
            # Step 4: Validate rollback
            print("✅ Validating rollback...")
            validation_success = self.validate_rollback()
            
            # Step 5: Send notifications
            print("📢 Sending rollback notifications...")
            self.send_rollback_notifications(reason, lambda_rollback_success and frontend_rollback_success)
            
            # Step 6: Log rollback event
            self.log_rollback_event(reason, lambda_rollback_success and frontend_rollback_success)
            
            if lambda_rollback_success and frontend_rollback_success and validation_success:
                print("🎯 Emergency rollback completed successfully!")
                return True
            else:
                print("❌ Emergency rollback encountered issues!")
                return False
                
        except Exception as e:
            print(f"💥 Emergency rollback failed: {str(e)}")
            self.send_critical_alert(f"Rollback failed: {str(e)}")
            return False
    
    def check_system_health(self) -> Dict[str, str]:
        """Check current system health metrics."""
        health_status = {
            'overall': 'unknown',
            'lambda_functions': 'unknown',
            'frontend': 'unknown',
            'database': 'unknown'
        }
        
        try:
            # Check Lambda function health
            healthy_functions = 0
            total_functions = len(self.lambda_functions)
            
            for function_name in self.lambda_functions:
                full_function_name = f"AquaChain-{function_name}-{self.environment}"
                try:
                    response = self.lambda_client.get_function(FunctionName=full_function_name)
                    if response['Configuration']['State'] == 'Active':
                        healthy_functions += 1
                except Exception:
                    pass
            
            lambda_health_ratio = healthy_functions / total_functions
            health_status['lambda_functions'] = 'healthy' if lambda_health_ratio > 0.8 else 'degraded'
            
            # Check frontend health (S3 bucket accessibility)
            try:
                production_bucket = f"aquachain-frontend-{self.environment}-{self.account_id}"
                self.s3_client.head_object(Bucket=production_bucket, Key='index.html')
                health_status['frontend'] = 'healthy'
            except Exception:
                health_status['frontend'] = 'degraded'
            
            # Check database health (DynamoDB table status)
            try:
                dynamodb = boto3.client('dynamodb', region_name=self.region)
                table_response = dynamodb.describe_table(
                    TableName=f'aquachain-readings-{self.environment}'
                )
                if table_response['Table']['TableStatus'] == 'ACTIVE':
                    health_status['database'] = 'healthy'
                else:
                    health_status['database'] = 'degraded'
            except Exception:
                health_status['database'] = 'degraded'
            
            # Overall health
            healthy_components = sum(1 for status in health_status.values() if status == 'healthy')
            total_components = len(health_status) - 1  # Exclude 'overall'
            
            if healthy_components == total_components:
                health_status['overall'] = 'healthy'
            elif healthy_components > total_components / 2:
                health_status['overall'] = 'degraded'
            else:
                health_status['overall'] = 'critical'
                
        except Exception as e:
            print(f"⚠️  Health check failed: {str(e)}")
            health_status['overall'] = 'unknown'
        
        return health_status
    
    def rollback_lambda_functions(self) -> bool:
        """Rollback all Lambda functions to BLUE aliases."""
        success_count = 0
        
        for function_name in self.lambda_functions:
            full_function_name = f"AquaChain-{function_name}-{self.environment}"
            
            try:
                print(f"  Rolling back {function_name}...")
                
                # Get BLUE alias version
                try:
                    blue_alias = self.lambda_client.get_alias(
                        FunctionName=full_function_name,
                        Name='BLUE'
                    )
                    blue_version = blue_alias['FunctionVersion']
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # If no BLUE alias, try to find previous version
                    versions = self.lambda_client.list_versions_by_function(
                        FunctionName=full_function_name
                    )['Versions']
                    
                    # Get second-to-last version (excluding $LATEST)
                    version_numbers = [v['Version'] for v in versions if v['Version'] != '$LATEST']
                    if len(version_numbers) >= 2:
                        blue_version = sorted(version_numbers, key=int)[-2]
                    else:
                        print(f"    ⚠️  No previous version found for {function_name}")
                        continue
                
                # Update LIVE alias to point to BLUE version
                try:
                    self.lambda_client.update_alias(
                        FunctionName=full_function_name,
                        Name='LIVE',
                        FunctionVersion=blue_version
                    )
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # Create LIVE alias if it doesn't exist
                    self.lambda_client.create_alias(
                        FunctionName=full_function_name,
                        Name='LIVE',
                        FunctionVersion=blue_version
                    )
                
                print(f"    ✅ {function_name} rolled back to version {blue_version}")
                success_count += 1
                
            except Exception as e:
                print(f"    ❌ Failed to rollback {function_name}: {str(e)}")
        
        success_ratio = success_count / len(self.lambda_functions)
        return success_ratio > 0.8  # Consider successful if >80% of functions rolled back
    
    def rollback_frontend(self) -> bool:
        """Rollback frontend to BLUE version."""
        try:
            blue_bucket = f"aquachain-frontend-blue-{self.account_id}"
            production_bucket = f"aquachain-frontend-{self.environment}-{self.account_id}"
            
            # Check if BLUE bucket exists and has content
            try:
                blue_objects = self.s3_client.list_objects_v2(Bucket=blue_bucket, MaxKeys=1)
                if 'Contents' not in blue_objects:
                    print("    ⚠️  No BLUE frontend backup found")
                    return False
            except Exception:
                print("    ⚠️  BLUE frontend bucket not accessible")
                return False
            
            # Copy from BLUE to production bucket
            print("    Copying BLUE frontend to production...")
            self.sync_s3_buckets(blue_bucket, production_bucket)
            
            # Invalidate CloudFront cache
            distribution_id = os.getenv(f'CLOUDFRONT_DISTRIBUTION_ID_{self.environment.upper()}')
            if distribution_id:
                print("    Invalidating CloudFront cache...")
                self.cloudfront_client.create_invalidation(
                    DistributionId=distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': 1,
                            'Items': ['/*']
                        },
                        'CallerReference': f"rollback-{int(time.time())}"
                    }
                )
            
            print("    ✅ Frontend rolled back successfully")
            return True
            
        except Exception as e:
            print(f"    ❌ Frontend rollback failed: {str(e)}")
            return False
    
    def validate_rollback(self) -> bool:
        """Validate that rollback was successful."""
        print("  Running rollback validation...")
        
        try:
            # Wait for changes to propagate
            time.sleep(30)
            
            # Test Lambda functions
            healthy_functions = 0
            for function_name in self.lambda_functions:
                full_function_name = f"AquaChain-{function_name}-{self.environment}"
                
                try:
                    # Test function invocation
                    test_payload = self.get_test_payload(function_name)
                    response = self.lambda_client.invoke(
                        FunctionName=f"{full_function_name}:LIVE",
                        InvocationType='RequestResponse',
                        Payload=json.dumps(test_payload)
                    )
                    
                    if response['StatusCode'] == 200:
                        payload = json.loads(response['Payload'].read())
                        if 'errorMessage' not in payload:
                            healthy_functions += 1
                            
                except Exception as e:
                    print(f"    ⚠️  Function {function_name} validation failed: {str(e)}")
            
            lambda_success_ratio = healthy_functions / len(self.lambda_functions)
            
            # Test frontend
            frontend_healthy = False
            try:
                production_bucket = f"aquachain-frontend-{self.environment}-{self.account_id}"
                self.s3_client.head_object(Bucket=production_bucket, Key='index.html')
                frontend_healthy = True
            except Exception:
                pass
            
            overall_success = lambda_success_ratio > 0.8 and frontend_healthy
            
            if overall_success:
                print("  ✅ Rollback validation passed")
            else:
                print(f"  ❌ Rollback validation failed (Lambda: {lambda_success_ratio:.1%}, Frontend: {frontend_healthy})")
            
            return overall_success
            
        except Exception as e:
            print(f"  ❌ Rollback validation error: {str(e)}")
            return False
    
    def send_rollback_notifications(self, reason: str, success: bool):
        """Send notifications about rollback status."""
        try:
            # Send to SNS topic
            sns = boto3.client('sns', region_name=self.region)
            
            status = "SUCCESS" if success else "FAILED"
            subject = f"🚨 AquaChain {self.environment.upper()} Rollback {status}"
            
            message = f"""
AquaChain Emergency Rollback Report

Environment: {self.environment}
Region: {self.region}
Status: {status}
Reason: {reason}
Timestamp: {datetime.now(timezone.utc).isoformat()}

System Health After Rollback:
{json.dumps(self.check_system_health(), indent=2)}

Please verify system functionality and investigate the root cause.
            """
            
            # Try to find admin notification topic
            topics = sns.list_topics()['Topics']
            admin_topic = None
            
            for topic in topics:
                if f'aquachain-admin-alerts-{self.environment}' in topic['TopicArn']:
                    admin_topic = topic['TopicArn']
                    break
            
            if admin_topic:
                sns.publish(
                    TopicArn=admin_topic,
                    Subject=subject,
                    Message=message
                )
                print("    ✅ Rollback notification sent")
            else:
                print("    ⚠️  Admin notification topic not found")
                
        except Exception as e:
            print(f"    ❌ Failed to send rollback notification: {str(e)}")
    
    def send_critical_alert(self, message: str):
        """Send critical alert for rollback failure."""
        try:
            # This would integrate with PagerDuty or similar
            print(f"🚨 CRITICAL ALERT: {message}")
            
            # Log to CloudWatch as well
            self.cloudwatch.put_metric_data(
                Namespace='AquaChain/Rollback',
                MetricData=[
                    {
                        'MetricName': 'RollbackFailure',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'Environment',
                                'Value': self.environment
                            }
                        ]
                    }
                ]
            )
            
        except Exception as e:
            print(f"Failed to send critical alert: {str(e)}")
    
    def log_rollback_event(self, reason: str, success: bool):
        """Log rollback event to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='AquaChain/Rollback',
                MetricData=[
                    {
                        'MetricName': 'RollbackEvent',
                        'Value': 1 if success else 0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'Environment',
                                'Value': self.environment
                            },
                            {
                                'Name': 'Success',
                                'Value': str(success)
                            }
                        ]
                    }
                ]
            )
            
            # Also log to CloudWatch Logs
            logs_client = boto3.client('logs', region_name=self.region)
            log_group = f'/aquachain/{self.environment}/rollback'
            
            try:
                logs_client.create_log_group(logGroupName=log_group)
            except logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            try:
                logs_client.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=datetime.now().strftime('%Y/%m/%d/rollback-%H%M%S')
                )
            except logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
        except Exception as e:
            print(f"Failed to log rollback event: {str(e)}")
    
    def get_test_payload(self, function_name: str) -> dict:
        """Get test payload for function validation."""
        if function_name == 'data-processing':
            return {
                "deviceId": "ROLLBACK-TEST",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "readings": {
                    "pH": 7.0,
                    "turbidity": 1.0,
                    "tds": 150,
                    "temperature": 25.0,
                    "humidity": 60.0
                }
            }
        else:
            return {"test": True, "rollback_validation": True}
    
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
    parser = argparse.ArgumentParser(description='AquaChain Emergency Rollback')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--environment', required=True, choices=['staging', 'production'], help='Environment to rollback')
    parser.add_argument('--reason', default='Emergency rollback', help='Reason for rollback')
    parser.add_argument('--confirm', action='store_true', help='Confirm rollback execution')
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  This will rollback the entire system to the previous version.")
        print(f"Environment: {args.environment}")
        print(f"Region: {args.region}")
        print(f"Reason: {args.reason}")
        print()
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Rollback cancelled.")
            return 0
    
    rollback = AquaChainRollback(args.region, args.environment)
    success = rollback.emergency_rollback(args.reason)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())