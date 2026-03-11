"""
Ledger Backup Service with S3 Object Lock
Creates immutable backups of ledger entries in S3 with 7-year retention
"""

import json
import boto3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
BACKUP_BUCKET = 'aquachain-audit-archive-dev'
LEDGER_TABLE = 'aquachain-ledger'
RETENTION_YEARS = 7

class LedgerBackupService:
    """
    Service for creating immutable S3 backups of ledger entries
    """
    
    def __init__(self):
        self.ledger_table = dynamodb.Table(LEDGER_TABLE)
        self.backup_bucket = BACKUP_BUCKET
        self.retention_period = timedelta(days=365 * RETENTION_YEARS)
    
    def backup_ledger_entry(self, ledger_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create immutable S3 backup of ledger entry with Object Lock
        """
        try:
            # Generate backup metadata
            sequence_number = ledger_entry['sequenceNumber']
            timestamp = datetime.fromisoformat(ledger_entry['timestamp'].replace('Z', '+00:00'))
            
            # Create S3 key with hierarchical structure
            s3_key = self._generate_s3_key(sequence_number, timestamp)
            
            # Create backup payload with integrity verification
            backup_payload = {
                'ledgerEntry': ledger_entry,
                'backupMetadata': {
                    'backupTimestamp': datetime.utcnow().isoformat() + 'Z',
                    'backupVersion': '1.0',
                    'integrityHash': self._calculate_integrity_hash(ledger_entry),
                    'retentionUntil': (datetime.utcnow() + self.retention_period).isoformat() + 'Z'
                }
            }
            
            # Store in S3 with Object Lock
            retention_until = datetime.utcnow() + self.retention_period
            
            response = s3_client.put_object(
                Bucket=self.backup_bucket,
                Key=s3_key,
                Body=json.dumps(backup_payload, indent=2, default=str),
                ContentType='application/json',
                Metadata={
                    'ledger-sequence': str(sequence_number),
                    'device-id': ledger_entry['deviceId'],
                    'backup-timestamp': datetime.utcnow().isoformat(),
                    'integrity-hash': backup_payload['backupMetadata']['integrityHash']
                },
                ObjectLockMode='COMPLIANCE',
                ObjectLockRetainUntilDate=retention_until,
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId='alias/aquachain-ledger-key'
            )
            
            logger.info(f"Created immutable backup for sequence {sequence_number} at {s3_key}")
            
            return {
                'success': True,
                'backupLocation': f"s3://{self.backup_bucket}/{s3_key}",
                'retentionUntil': retention_until.isoformat() + 'Z',
                'integrityHash': backup_payload['backupMetadata']['integrityHash'],
                'etag': response['ETag']
            }
            
        except ClientError as e:
            logger.error(f"Error creating S3 backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_backup_integrity(self, sequence_number: int) -> Dict[str, Any]:
        """
        Verify integrity of backed up ledger entry
        """
        try:
            # Get original ledger entry
            ledger_response = self.ledger_table.get_item(
                Key={
                    'partition_key': 'GLOBAL_SEQUENCE',
                    'sequenceNumber': sequence_number
                }
            )
            
            if 'Item' not in ledger_response:
                return {
                    'valid': False,
                    'error': 'Ledger entry not found'
                }
            
            original_entry = ledger_response['Item']
            
            # Find backup in S3
            timestamp = datetime.fromisoformat(original_entry['timestamp'].replace('Z', '+00:00'))
            s3_key = self._generate_s3_key(sequence_number, timestamp)
            
            # Get backup from S3
            backup_response = s3_client.get_object(
                Bucket=self.backup_bucket,
                Key=s3_key
            )
            
            backup_data = json.loads(backup_response['Body'].read())
            backed_up_entry = backup_data['ledgerEntry']
            
            # Verify integrity
            original_hash = self._calculate_integrity_hash(original_entry)
            backup_hash = backup_data['backupMetadata']['integrityHash']
            backed_up_hash = self._calculate_integrity_hash(backed_up_entry)
            
            integrity_valid = (original_hash == backup_hash == backed_up_hash)
            
            # Verify Object Lock status
            object_retention = s3_client.get_object_retention(
                Bucket=self.backup_bucket,
                Key=s3_key
            )
            
            return {
                'valid': integrity_valid,
                'originalHash': original_hash,
                'backupHash': backup_hash,
                'objectLockMode': object_retention.get('Retention', {}).get('Mode'),
                'retentionUntil': object_retention.get('Retention', {}).get('RetainUntilDate'),
                'backupLocation': f"s3://{self.backup_bucket}/{s3_key}"
            }
            
        except ClientError as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _generate_s3_key(self, sequence_number: int, timestamp: datetime) -> str:
        """
        Generate hierarchical S3 key for ledger backup
        """
        year = timestamp.year
        month = f"{timestamp.month:02d}"
        day = f"{timestamp.day:02d}"
        hour = f"{timestamp.hour:02d}"
        
        return f"ledger/{year}/{month}/{day}/{hour}/seq-{sequence_number}.json"
    
    def _calculate_integrity_hash(self, ledger_entry: Dict[str, Any]) -> str:
        """
        Calculate SHA-256 hash of ledger entry for integrity verification
        """
        # Create deterministic hash by sorting keys
        entry_copy = dict(ledger_entry)
        
        # Remove any AWS-specific metadata that might change
        entry_copy.pop('aws:rep:deleting', None)
        entry_copy.pop('aws:rep:updateregion', None)
        entry_copy.pop('aws:rep:updatetime', None)
        
        # Create sorted JSON string
        entry_json = json.dumps(entry_copy, sort_keys=True, default=str)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(entry_json.encode('utf-8')).hexdigest()

def lambda_handler(event, context):
    """
    Lambda handler for ledger backup operations
    """
    try:
        logger.info(f"Ledger backup request: {json.dumps(event)}")
        
        backup_service = LedgerBackupService()
        operation = event.get('operation')
        
        if operation == 'backup_entry':
            # Create backup of ledger entry
            ledger_entry = event['ledgerEntry']
            result = backup_service.backup_ledger_entry(ledger_entry)
            
            return {
                'statusCode': 200 if result['success'] else 500,
                'body': json.dumps(result)
            }
        
        elif operation == 'verify_backup':
            # Verify backup integrity
            sequence_number = event['sequenceNumber']
            result = backup_service.verify_backup_integrity(sequence_number)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid operation'})
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in ledger backup: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }