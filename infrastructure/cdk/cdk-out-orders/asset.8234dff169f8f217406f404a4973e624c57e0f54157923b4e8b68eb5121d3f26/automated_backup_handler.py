"""
Automated DynamoDB Backup Handler
Creates daily backups with verification and retention management
"""

import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class BackupManager:
    """
    Manages automated DynamoDB backups with verification
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        
        # Configuration
        self.backup_retention_days = 30
        self.tables_to_backup = [
            'aquachain-readings',
            'aquachain-devices',
            'aquachain-users',
            'aquachain-service-requests',
            'aquachain-audit-trail'
        ]
    
    def create_backups(self) -> Dict[str, Any]:
        """
        Create backups for all configured tables
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'backups_created': [],
            'backups_failed': [],
            'total_size_bytes': 0
        }
        
        for table_name in self.tables_to_backup:
            try:
                backup_result = self._create_table_backup(table_name)
                results['backups_created'].append(backup_result)
                results['total_size_bytes'] += backup_result.get('size_bytes', 0)
                
                logger.info(f"✅ Backup created for {table_name}: {backup_result['backup_arn']}")
                
            except Exception as e:
                error_info = {
                    'table_name': table_name,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                results['backups_failed'].append(error_info)
                logger.error(f"❌ Backup failed for {table_name}: {e}")
        
        # Send notification
        self._send_backup_notification(results)
        
        return results
    
    def _create_table_backup(self, table_name: str) -> Dict[str, Any]:
        """
        Create backup for a single table
        """
        backup_name = f"{table_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        # Create backup
        response = self.dynamodb.create_backup(
            TableName=table_name,
            BackupName=backup_name
        )
        
        backup_details = response['BackupDetails']
        
        # Wait for backup to complete and get size
        backup_arn = backup_details['BackupArn']
        backup_info = self._wait_for_backup_completion(backup_arn)
        
        return {
            'table_name': table_name,
            'backup_name': backup_name,
            'backup_arn': backup_arn,
            'backup_status': backup_info['BackupStatus'],
            'size_bytes': backup_info.get('BackupSizeBytes', 0),
            'created_at': backup_details['BackupCreationDateTime'].isoformat()
        }
    
    def _wait_for_backup_completion(self, backup_arn: str, max_wait_seconds: int = 300) -> Dict[str, Any]:
        """
        Wait for backup to complete and return details
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            response = self.dynamodb.describe_backup(BackupArn=backup_arn)
            backup_details = response['BackupDescription']['BackupDetails']
            
            status = backup_details['BackupStatus']
            
            if status == 'AVAILABLE':
                return backup_details
            elif status == 'DELETED':
                raise Exception(f"Backup was deleted: {backup_arn}")
            
            time.sleep(10)  # Wait 10 seconds before checking again
        
        raise Exception(f"Backup did not complete within {max_wait_seconds} seconds")
    
    def verify_backups(self) -> Dict[str, Any]:
        """
        Verify all recent backups
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'backups_verified': [],
            'backups_failed': []
        }
        
        for table_name in self.tables_to_backup:
            try:
                # Get recent backups
                backups = self._list_table_backups(table_name, days=1)
                
                for backup in backups:
                    verification = self._verify_backup(backup['BackupArn'])
                    
                    if verification['valid']:
                        results['backups_verified'].append({
                            'table_name': table_name,
                            'backup_arn': backup['BackupArn'],
                            'size_bytes': verification['size_bytes']
                        })
                    else:
                        results['backups_failed'].append({
                            'table_name': table_name,
                            'backup_arn': backup['BackupArn'],
                            'reason': verification['reason']
                        })
                        
            except Exception as e:
                logger.error(f"Error verifying backups for {table_name}: {e}")
        
        return results
    
    def _list_table_backups(self, table_name: str, days: int = 1) -> List[Dict[str, Any]]:
        """
        List backups for a table within the specified time range
        """
        time_range_lower_bound = datetime.utcnow() - timedelta(days=days)
        
        response = self.dynamodb.list_backups(
            TableName=table_name,
            TimeRangeLowerBound=time_range_lower_bound
        )
        
        return response.get('BackupSummaries', [])
    
    def _verify_backup(self, backup_arn: str) -> Dict[str, Any]:
        """
        Verify backup integrity
        """
        try:
            response = self.dynamodb.describe_backup(BackupArn=backup_arn)
            backup_details = response['BackupDescription']['BackupDetails']
            
            # Check status
            if backup_details['BackupStatus'] != 'AVAILABLE':
                return {
                    'valid': False,
                    'reason': f"Backup status is {backup_details['BackupStatus']}"
                }
            
            # Check size
            size_bytes = backup_details.get('BackupSizeBytes', 0)
            if size_bytes == 0:
                return {
                    'valid': False,
                    'reason': 'Backup size is 0 bytes'
                }
            
            return {
                'valid': True,
                'size_bytes': size_bytes
            }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': str(e)
            }
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """
        Delete backups older than retention period
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'backups_deleted': [],
            'deletion_failed': []
        }
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.backup_retention_days)
        
        for table_name in self.tables_to_backup:
            try:
                # List all backups
                response = self.dynamodb.list_backups(TableName=table_name)
                
                for backup in response.get('BackupSummaries', []):
                    backup_date = backup['BackupCreationDateTime']
                    
                    # Delete if older than retention period
                    if backup_date < cutoff_date:
                        try:
                            self.dynamodb.delete_backup(BackupArn=backup['BackupArn'])
                            
                            results['backups_deleted'].append({
                                'table_name': table_name,
                                'backup_arn': backup['BackupArn'],
                                'backup_date': backup_date.isoformat()
                            })
                            
                            logger.info(f"Deleted old backup: {backup['BackupArn']}")
                            
                        except Exception as e:
                            results['deletion_failed'].append({
                                'backup_arn': backup['BackupArn'],
                                'error': str(e)
                            })
                            
            except Exception as e:
                logger.error(f"Error cleaning up backups for {table_name}: {e}")
        
        return results
    
    def test_restore(self, table_name: str) -> Dict[str, Any]:
        """
        Test restore process by restoring to a temporary table
        """
        try:
            # Get most recent backup
            backups = self._list_table_backups(table_name, days=1)
            
            if not backups:
                raise Exception(f"No recent backups found for {table_name}")
            
            latest_backup = backups[0]
            backup_arn = latest_backup['BackupArn']
            
            # Create temporary table name
            temp_table_name = f"{table_name}-restore-test-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Restore to temporary table
            logger.info(f"Testing restore: {backup_arn} -> {temp_table_name}")
            
            response = self.dynamodb.restore_table_from_backup(
                TargetTableName=temp_table_name,
                BackupArn=backup_arn
            )
            
            # Wait for restore to complete
            self._wait_for_table_active(temp_table_name)
            
            # Verify restored table
            table_info = self.dynamodb.describe_table(TableName=temp_table_name)
            item_count = table_info['Table']['ItemCount']
            
            # Delete temporary table
            self.dynamodb.delete_table(TableName=temp_table_name)
            
            return {
                'success': True,
                'table_name': table_name,
                'backup_arn': backup_arn,
                'restored_item_count': item_count,
                'test_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Restore test failed: {e}")
            return {
                'success': False,
                'table_name': table_name,
                'error': str(e)
            }
    
    def _wait_for_table_active(self, table_name: str, max_wait_seconds: int = 600):
        """
        Wait for table to become active
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            response = self.dynamodb.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            
            if status == 'ACTIVE':
                return True
            
            time.sleep(10)
        
        raise Exception(f"Table did not become active within {max_wait_seconds} seconds")
    
    def _send_backup_notification(self, results: Dict[str, Any]):
        """
        Send SNS notification about backup results
        """
        try:
            topic_arn = f"arn:aws:sns:{self.region}:ACCOUNT_ID:aquachain-backup-notifications"
            
            success_count = len(results['backups_created'])
            failure_count = len(results['backups_failed'])
            total_size_mb = results['total_size_bytes'] / (1024 * 1024)
            
            subject = f"AquaChain Backup Report - {success_count} Success, {failure_count} Failed"
            
            message = f"""
AquaChain DynamoDB Backup Report
================================

Timestamp: {results['timestamp']}

Summary:
- Backups Created: {success_count}
- Backups Failed: {failure_count}
- Total Size: {total_size_mb:.2f} MB

Successful Backups:
{json.dumps(results['backups_created'], indent=2)}

Failed Backups:
{json.dumps(results['backups_failed'], indent=2)}
"""
            
            self.sns.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


def lambda_handler(event, context):
    """
    Lambda handler for automated backups
    """
    try:
        action = event.get('action', 'create_backups')
        
        backup_manager = BackupManager()
        
        if action == 'create_backups':
            results = backup_manager.create_backups()
            
        elif action == 'verify_backups':
            results = backup_manager.verify_backups()
            
        elif action == 'cleanup_old_backups':
            results = backup_manager.cleanup_old_backups()
            
        elif action == 'test_restore':
            table_name = event.get('table_name', 'aquachain-readings')
            results = backup_manager.test_restore(table_name)
            
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
        
    except Exception as e:
        logger.error(f"Backup handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
