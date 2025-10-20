"""
Disaster Recovery Lambda Function
Handles backup validation, restore testing, and DR automation
"""

import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
backup_client = boto3.client('backup')
dynamodb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
cloudwatch_client = boto3.client('cloudwatch')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for disaster recovery operations
    """
    try:
        operation = event.get('operation')
        environment = event.get('environment', 'dev')
        
        logger.info(f"Starting DR operation: {operation} for environment: {environment}")
        
        if operation == 'validate_backups':
            return validate_backups(environment)
        elif operation == 'test_restore':
            return test_restore(environment)
        elif operation == 'cleanup_test':
            return cleanup_test_resources(environment)
        elif operation == 'full_dr_test':
            return run_full_dr_test(environment)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"DR operation failed: {str(e)}")
        send_notification(f"DR Operation Failed: {str(e)}", "error")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

def validate_backups(environment: str) -> Dict[str, Any]:
    """
    Validate that all critical backups are available and recent
    """
    logger.info("Validating backup availability and recency")
    
    backup_vault_name = os.environ.get('BACKUP_VAULT_NAME')
    validation_results = []
    
    try:
        # Get recent backup jobs
        response = backup_client.list_backup_jobs(
            ByBackupVaultName=backup_vault_name,
            ByState='COMPLETED',
            ByCreatedAfter=datetime.utcnow() - timedelta(days=2)  # Check last 2 days
        )
        
        backup_jobs = response.get('BackupJobs', [])
        
        # Check for required backup types
        required_resource_types = ['DynamoDB', 'S3']
        found_types = set()
        
        for job in backup_jobs:
            resource_type = job.get('ResourceType')
            if resource_type in required_resource_types:
                found_types.add(resource_type)
                
                validation_results.append({
                    'resource_arn': job.get('ResourceArn'),
                    'resource_type': resource_type,
                    'backup_job_id': job.get('BackupJobId'),
                    'creation_date': job.get('CreationDate').isoformat() if job.get('CreationDate') else None,
                    'completion_date': job.get('CompletionDate').isoformat() if job.get('CompletionDate') else None,
                    'backup_size_bytes': job.get('BackupSizeInBytes'),
                    'status': 'valid'
                })
        
        # Check if all required types have recent backups
        missing_types = set(required_resource_types) - found_types
        
        if missing_types:
            logger.warning(f"Missing recent backups for: {missing_types}")
            return {
                'status': 'warning',
                'message': f"Missing recent backups for: {list(missing_types)}",
                'validation_results': validation_results,
                'missing_types': list(missing_types),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Validate backup integrity (check sizes, etc.)
        for result in validation_results:
            if result.get('backup_size_bytes', 0) < 1024:  # Less than 1KB is suspicious
                result['status'] = 'suspicious'
                logger.warning(f"Suspicious backup size for {result['resource_arn']}")
        
        logger.info(f"Backup validation completed. Found {len(validation_results)} valid backups")
        
        return {
            'status': 'success',
            'message': f"All required backups are available and recent",
            'validation_results': validation_results,
            'backup_count': len(validation_results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup validation failed: {str(e)}")
        return {
            'status': 'error',
            'message': f"Backup validation failed: {str(e)}",
            'timestamp': datetime.utcnow().isoformat()
        }

def test_restore(environment: str) -> Dict[str, Any]:
    """
    Test restore functionality by creating test resources from backups
    """
    logger.info("Starting restore test")
    
    test_id = str(uuid.uuid4())[:8]
    test_resources = []
    
    try:
        # Get the most recent backup for testing
        backup_vault_name = os.environ.get('BACKUP_VAULT_NAME')
        
        response = backup_client.list_backup_jobs(
            ByBackupVaultName=backup_vault_name,
            ByState='COMPLETED',
            ByResourceType='DynamoDB',
            MaxResults=1
        )
        
        backup_jobs = response.get('BackupJobs', [])
        
        if not backup_jobs:
            return {
                'status': 'error',
                'message': 'No DynamoDB backups found for testing',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        latest_backup = backup_jobs[0]
        recovery_point_arn = latest_backup.get('RecoveryPointArn')
        
        # Create test table name
        original_table_name = latest_backup.get('ResourceArn').split('/')[-1]
        test_table_name = f"{original_table_name}-dr-test-{test_id}"
        
        logger.info(f"Testing restore of {original_table_name} to {test_table_name}")
        
        # Start restore job
        restore_response = backup_client.start_restore_job(
            RecoveryPointArn=recovery_point_arn,
            Metadata={
                'NewTableName': test_table_name,
                'BillingMode': 'PAY_PER_REQUEST'  # Use on-demand for test
            },
            IamRoleArn=get_backup_role_arn(),
            IdempotencyToken=f"dr-test-{test_id}"
        )
        
        restore_job_id = restore_response.get('RestoreJobId')
        test_resources.append({
            'type': 'dynamodb_table',
            'name': test_table_name,
            'restore_job_id': restore_job_id
        })
        
        # Wait for restore to complete (with timeout)
        max_wait_time = 600  # 10 minutes
        wait_time = 0
        
        while wait_time < max_wait_time:
            restore_status = backup_client.describe_restore_job(
                RestoreJobId=restore_job_id
            )
            
            status = restore_status.get('Status')
            
            if status == 'COMPLETED':
                logger.info(f"Restore completed successfully for {test_table_name}")
                break
            elif status in ['FAILED', 'ABORTED']:
                error_msg = f"Restore failed with status: {status}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'message': error_msg,
                    'restore_job_id': restore_job_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Wait 30 seconds before checking again
            import time
            time.sleep(30)
            wait_time += 30
        
        if wait_time >= max_wait_time:
            return {
                'status': 'error',
                'message': 'Restore test timed out',
                'restore_job_id': restore_job_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Verify restored table
        table_info = dynamodb_client.describe_table(TableName=test_table_name)
        table_status = table_info.get('Table', {}).get('TableStatus')
        item_count = table_info.get('Table', {}).get('ItemCount', 0)
        
        if table_status != 'ACTIVE':
            return {
                'status': 'error',
                'message': f'Restored table is not active. Status: {table_status}',
                'test_resources': test_resources,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        logger.info(f"Restore test successful. Table {test_table_name} is active with {item_count} items")
        
        # Record success metric
        record_dr_metric('RestoreTestSuccess', 1, environment)
        
        return {
            'status': 'success',
            'message': f'Restore test completed successfully',
            'test_resources': test_resources,
            'restored_table': test_table_name,
            'item_count': item_count,
            'restore_job_id': restore_job_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Restore test failed: {str(e)}")
        record_dr_metric('RestoreTestFailure', 1, environment)
        
        return {
            'status': 'error',
            'message': f'Restore test failed: {str(e)}',
            'test_resources': test_resources,
            'timestamp': datetime.utcnow().isoformat()
        }

def cleanup_test_resources(environment: str) -> Dict[str, Any]:
    """
    Clean up resources created during DR testing
    """
    logger.info("Cleaning up DR test resources")
    
    cleanup_results = []
    
    try:
        # Find and delete test tables
        paginator = dynamodb_client.get_paginator('list_tables')
        
        for page in paginator.paginate():
            for table_name in page.get('TableNames', []):
                if '-dr-test-' in table_name:
                    logger.info(f"Deleting test table: {table_name}")
                    
                    try:
                        dynamodb_client.delete_table(TableName=table_name)
                        cleanup_results.append({
                            'resource_type': 'dynamodb_table',
                            'resource_name': table_name,
                            'status': 'deleted'
                        })
                    except Exception as e:
                        logger.warning(f"Failed to delete table {table_name}: {str(e)}")
                        cleanup_results.append({
                            'resource_type': 'dynamodb_table',
                            'resource_name': table_name,
                            'status': 'failed',
                            'error': str(e)
                        })
        
        # Clean up any test S3 objects (if applicable)
        # This would be implemented based on specific test patterns
        
        logger.info(f"Cleanup completed. Processed {len(cleanup_results)} resources")
        
        return {
            'status': 'success',
            'message': f'Cleanup completed for {len(cleanup_results)} resources',
            'cleanup_results': cleanup_results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Cleanup failed: {str(e)}',
            'cleanup_results': cleanup_results,
            'timestamp': datetime.utcnow().isoformat()
        }

def run_full_dr_test(environment: str) -> Dict[str, Any]:
    """
    Run a comprehensive disaster recovery test
    """
    logger.info("Starting full disaster recovery test")
    
    test_results = {
        'test_id': str(uuid.uuid4()),
        'environment': environment,
        'start_time': datetime.utcnow().isoformat(),
        'phases': []
    }
    
    try:
        # Phase 1: Validate backups
        logger.info("Phase 1: Validating backups")
        backup_validation = validate_backups(environment)
        test_results['phases'].append({
            'phase': 'backup_validation',
            'result': backup_validation
        })
        
        if backup_validation['status'] != 'success':
            raise Exception(f"Backup validation failed: {backup_validation['message']}")
        
        # Phase 2: Test restore
        logger.info("Phase 2: Testing restore")
        restore_test = test_restore(environment)
        test_results['phases'].append({
            'phase': 'restore_test',
            'result': restore_test
        })
        
        if restore_test['status'] != 'success':
            raise Exception(f"Restore test failed: {restore_test['message']}")
        
        # Phase 3: Validate restored data
        logger.info("Phase 3: Validating restored data")
        data_validation = validate_restored_data(restore_test.get('restored_table'))
        test_results['phases'].append({
            'phase': 'data_validation',
            'result': data_validation
        })
        
        # Phase 4: Cleanup
        logger.info("Phase 4: Cleaning up test resources")
        cleanup_result = cleanup_test_resources(environment)
        test_results['phases'].append({
            'phase': 'cleanup',
            'result': cleanup_result
        })
        
        test_results['end_time'] = datetime.utcnow().isoformat()
        test_results['status'] = 'success'
        test_results['message'] = 'Full DR test completed successfully'
        
        # Send success notification
        send_notification(
            f"DR Test Successful for {environment}: All phases completed successfully",
            "success"
        )
        
        # Record success metric
        record_dr_metric('FullDRTestSuccess', 1, environment)
        
        return test_results
        
    except Exception as e:
        test_results['end_time'] = datetime.utcnow().isoformat()
        test_results['status'] = 'error'
        test_results['message'] = str(e)
        
        logger.error(f"Full DR test failed: {str(e)}")
        
        # Send failure notification
        send_notification(
            f"DR Test Failed for {environment}: {str(e)}",
            "error"
        )
        
        # Record failure metric
        record_dr_metric('FullDRTestFailure', 1, environment)
        
        return test_results

def validate_restored_data(table_name: str) -> Dict[str, Any]:
    """
    Validate that restored data is accessible and consistent
    """
    if not table_name:
        return {
            'status': 'skipped',
            'message': 'No table name provided for validation'
        }
    
    try:
        # Get table description
        table_info = dynamodb_client.describe_table(TableName=table_name)
        table_status = table_info.get('Table', {}).get('TableStatus')
        item_count = table_info.get('Table', {}).get('ItemCount', 0)
        
        # Try to scan a few items to verify data accessibility
        scan_response = dynamodb_client.scan(
            TableName=table_name,
            Limit=10
        )
        
        scanned_items = scan_response.get('Items', [])
        
        return {
            'status': 'success',
            'message': f'Data validation successful',
            'table_status': table_status,
            'item_count': item_count,
            'sample_items_count': len(scanned_items),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data validation failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'Data validation failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }

def get_backup_role_arn() -> str:
    """
    Get the backup service role ARN
    """
    # This would typically be passed as an environment variable
    # or retrieved from AWS Systems Manager Parameter Store
    account_id = boto3.client('sts').get_caller_identity()['Account']
    region = os.environ.get('AWS_REGION', 'us-east-1')
    environment = os.environ.get('ENVIRONMENT', 'dev')
    
    return f"arn:aws:iam::{account_id}:role/aquachain-role-backup-service-{environment}"

def send_notification(message: str, severity: str = "info") -> None:
    """
    Send notification via SNS
    """
    try:
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if not sns_topic_arn:
            logger.warning("No SNS topic ARN configured for notifications")
            return
        
        subject = f"AquaChain DR Alert - {severity.upper()}"
        
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject=subject,
            Message=message
        )
        
        logger.info(f"Notification sent: {subject}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")

def record_dr_metric(metric_name: str, value: float, environment: str) -> None:
    """
    Record custom CloudWatch metric for DR operations
    """
    try:
        cloudwatch_client.put_metric_data(
            Namespace='AquaChain/DisasterRecovery',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'Environment',
                            'Value': environment
                        }
                    ],
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        logger.info(f"Recorded metric: {metric_name} = {value} for {environment}")
        
    except Exception as e:
        logger.error(f"Failed to record metric: {str(e)}")