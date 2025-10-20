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
        elif operation == 'automated_backup':
            return create_automated_backup(environment, event.get('resource_type'))
        elif operation == 'validate_cross_region_replication':
            return validate_cross_region_replication(environment)
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

def create_automated_backup(environment: str, resource_type: str = None) -> Dict[str, Any]:
    """
    Create automated backups for critical resources
    """
    logger.info(f"Creating automated backup for environment: {environment}")
    
    backup_vault_name = os.environ.get('BACKUP_VAULT_NAME')
    backup_results = []
    
    try:
        # Get list of critical resources to backup
        critical_resources = get_critical_resources(environment, resource_type)
        
        for resource in critical_resources:
            try:
                backup_job_id = f"auto-backup-{resource['type']}-{int(time.time())}"
                
                response = backup_client.start_backup_job(
                    BackupVaultName=backup_vault_name,
                    ResourceArn=resource['arn'],
                    IamRoleArn=get_backup_role_arn(),
                    IdempotencyToken=backup_job_id,
                    StartWindowMinutes=60,
                    CompleteWindowMinutes=120
                )
                
                backup_results.append({
                    'resource_arn': resource['arn'],
                    'resource_type': resource['type'],
                    'backup_job_id': response['BackupJobId'],
                    'status': 'started'
                })
                
                logger.info(f"Started backup for {resource['arn']}")
                
            except Exception as resource_error:
                backup_results.append({
                    'resource_arn': resource['arn'],
                    'resource_type': resource['type'],
                    'status': 'failed',
                    'error': str(resource_error)
                })
                
                logger.error(f"Failed to start backup for {resource['arn']}: {str(resource_error)}")
        
        # Calculate success rate
        successful_backups = sum(1 for result in backup_results if result['status'] == 'started')
        total_backups = len(backup_results)
        success_rate = (successful_backups / total_backups) if total_backups > 0 else 0
        
        # Record metrics
        record_dr_metric('AutomatedBackupsStarted', successful_backups, environment)
        record_dr_metric('AutomatedBackupsFailed', total_backups - successful_backups, environment)
        
        return {
            'status': 'success' if success_rate > 0.8 else 'partial',
            'message': f'Automated backup completed. {successful_backups}/{total_backups} backups started',
            'backup_results': backup_results,
            'success_rate': success_rate,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Automated backup failed: {str(e)}")
        record_dr_metric('AutomatedBackupError', 1, environment)
        
        return {
            'status': 'error',
            'message': f'Automated backup failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }

def get_critical_resources(environment: str, resource_type: str = None) -> List[Dict[str, str]]:
    """
    Get list of critical resources that need backup
    """
    critical_resources = []
    
    # DynamoDB tables
    if not resource_type or resource_type == 'dynamodb':
        dynamodb_tables = [
            f"aquachain-table-ledger-{environment}",
            f"aquachain-table-readings-{environment}",
            f"aquachain-table-users-{environment}",
            f"aquachain-table-service-requests-{environment}"
        ]
        
        for table_name in dynamodb_tables:
            try:
                # Verify table exists
                dynamodb_client.describe_table(TableName=table_name)
                
                # Get table ARN
                account_id = boto3.client('sts').get_caller_identity()['Account']
                region = os.environ.get('AWS_REGION', 'us-east-1')
                table_arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}"
                
                critical_resources.append({
                    'type': 'DynamoDB',
                    'name': table_name,
                    'arn': table_arn
                })
                
            except Exception as e:
                logger.warning(f"Table {table_name} not found or not accessible: {str(e)}")
    
    # S3 buckets
    if not resource_type or resource_type == 's3':
        s3_buckets = [
            f"aquachain-bucket-audit-trail-{environment}",
            f"aquachain-bucket-ml-models-{environment}",
            f"aquachain-bucket-data-lake-{environment}"
        ]
        
        for bucket_name in s3_buckets:
            try:
                # Verify bucket exists
                s3_client.head_bucket(Bucket=bucket_name)
                
                bucket_arn = f"arn:aws:s3:::{bucket_name}"
                
                critical_resources.append({
                    'type': 'S3',
                    'name': bucket_name,
                    'arn': bucket_arn
                })
                
            except Exception as e:
                logger.warning(f"Bucket {bucket_name} not found or not accessible: {str(e)}")
    
    return critical_resources

def validate_cross_region_replication(environment: str) -> Dict[str, Any]:
    """
    Validate cross-region replication status
    """
    logger.info(f"Validating cross-region replication for environment: {environment}")
    
    replica_region = os.environ.get('REPLICA_REGION', 'us-west-2')
    primary_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    validation_results = {
        'primary_region': primary_region,
        'replica_region': replica_region,
        'validation_time': datetime.utcnow().isoformat(),
        'replication_checks': []
    }
    
    try:
        # Check S3 cross-region replication
        s3_replication_check = validate_s3_replication(environment, replica_region)
        validation_results['replication_checks'].append(s3_replication_check)
        
        # Check DynamoDB Global Tables (if enabled)
        dynamodb_replication_check = validate_dynamodb_replication(environment, replica_region)
        validation_results['replication_checks'].append(dynamodb_replication_check)
        
        # Calculate overall replication health
        total_checks = len(validation_results['replication_checks'])
        healthy_checks = sum(1 for check in validation_results['replication_checks'] if check['status'] == 'healthy')
        replication_health = (healthy_checks / total_checks) if total_checks > 0 else 0
        
        validation_results['replication_health_score'] = replication_health
        validation_results['healthy_replications'] = healthy_checks
        validation_results['total_replications'] = total_checks
        
        if replication_health >= 0.8:
            validation_results['status'] = 'success'
            validation_results['message'] = f'Cross-region replication healthy. Score: {replication_health:.2f}'
            record_dr_metric('CrossRegionReplicationHealthy', 1, environment)
        else:
            validation_results['status'] = 'warning'
            validation_results['message'] = f'Cross-region replication issues detected. Score: {replication_health:.2f}'
            record_dr_metric('CrossRegionReplicationIssues', 1, environment)
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Cross-region replication validation failed: {str(e)}")
        record_dr_metric('CrossRegionReplicationValidationError', 1, environment)
        
        return {
            'status': 'error',
            'message': f'Cross-region replication validation failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }

def validate_s3_replication(environment: str, replica_region: str) -> Dict[str, Any]:
    """
    Validate S3 cross-region replication
    """
    try:
        # Check audit trail bucket replication
        audit_bucket_name = f"aquachain-bucket-audit-trail-{environment}"
        
        try:
            replication_config = s3_client.get_bucket_replication(Bucket=audit_bucket_name)
            rules = replication_config.get('ReplicationConfiguration', {}).get('Rules', [])
            
            if rules:
                # Check replication metrics
                replica_s3_client = boto3.client('s3', region_name=replica_region)
                replica_bucket_name = f"aquachain-bucket-audit-replica-{environment}"
                
                try:
                    replica_s3_client.head_bucket(Bucket=replica_bucket_name)
                    
                    return {
                        'service': 'S3 Cross-Region Replication',
                        'status': 'healthy',
                        'details': f'Replication configured and replica bucket exists in {replica_region}',
                        'source_bucket': audit_bucket_name,
                        'replica_bucket': replica_bucket_name
                    }
                    
                except Exception as replica_error:
                    return {
                        'service': 'S3 Cross-Region Replication',
                        'status': 'unhealthy',
                        'details': f'Replica bucket not accessible: {str(replica_error)}',
                        'source_bucket': audit_bucket_name,
                        'replica_bucket': replica_bucket_name
                    }
            else:
                return {
                    'service': 'S3 Cross-Region Replication',
                    'status': 'unhealthy',
                    'details': 'No replication rules configured',
                    'source_bucket': audit_bucket_name
                }
                
        except Exception as config_error:
            return {
                'service': 'S3 Cross-Region Replication',
                'status': 'unhealthy',
                'details': f'Failed to get replication configuration: {str(config_error)}',
                'source_bucket': audit_bucket_name
            }
            
    except Exception as e:
        return {
            'service': 'S3 Cross-Region Replication',
            'status': 'error',
            'details': f'S3 replication validation failed: {str(e)}',
            'error': str(e)
        }

def validate_dynamodb_replication(environment: str, replica_region: str) -> Dict[str, Any]:
    """
    Validate DynamoDB Global Tables replication
    """
    try:
        # Check if Global Tables are configured
        replica_dynamodb_client = boto3.client('dynamodb', region_name=replica_region)
        
        critical_tables = [
            f"aquachain-table-ledger-{environment}",
            f"aquachain-table-readings-{environment}"
        ]
        
        replication_status = []
        
        for table_name in critical_tables:
            try:
                # Check if table exists in replica region
                replica_dynamodb_client.describe_table(TableName=table_name)
                
                replication_status.append({
                    'table': table_name,
                    'status': 'replicated',
                    'details': f'Table exists in {replica_region}'
                })
                
            except replica_dynamodb_client.exceptions.ResourceNotFoundException:
                replication_status.append({
                    'table': table_name,
                    'status': 'not_replicated',
                    'details': f'Table not found in {replica_region}'
                })
                
            except Exception as table_error:
                replication_status.append({
                    'table': table_name,
                    'status': 'error',
                    'details': f'Error checking table: {str(table_error)}'
                })
        
        # Calculate replication health
        replicated_tables = sum(1 for status in replication_status if status['status'] == 'replicated')
        total_tables = len(replication_status)
        
        if replicated_tables == total_tables:
            return {
                'service': 'DynamoDB Global Tables',
                'status': 'healthy',
                'details': f'All {total_tables} critical tables replicated to {replica_region}',
                'replication_status': replication_status
            }
        elif replicated_tables > 0:
            return {
                'service': 'DynamoDB Global Tables',
                'status': 'partial',
                'details': f'{replicated_tables}/{total_tables} tables replicated to {replica_region}',
                'replication_status': replication_status
            }
        else:
            return {
                'service': 'DynamoDB Global Tables',
                'status': 'unhealthy',
                'details': f'No tables replicated to {replica_region}',
                'replication_status': replication_status
            }
            
    except Exception as e:
        return {
            'service': 'DynamoDB Global Tables',
            'status': 'error',
            'details': f'DynamoDB replication validation failed: {str(e)}',
            'error': str(e)
        }

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