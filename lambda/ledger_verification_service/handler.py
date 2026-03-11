"""
Ledger Verification Service
Automated integrity checks for hash chain and cryptographic signatures
"""

import json
import boto3
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
kms_client = boto3.client('kms')
s3_client = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
LEDGER_TABLE = 'aquachain-ledger'
BACKUP_BUCKET = 'aquachain-audit-archive-dev'
SIGNING_KEY_ALIAS = 'alias/aquachain-ledger-signing-key'

class LedgerVerificationService:
    """
    Service for comprehensive ledger integrity verification
    """
    
    def __init__(self):
        self.ledger_table = dynamodb.Table(LEDGER_TABLE)
        self.signing_key_id = SIGNING_KEY_ALIAS
        self.backup_bucket = BACKUP_BUCKET
    
    def run_comprehensive_verification(self, start_sequence: int = None, 
                                     end_sequence: int = None) -> Dict[str, Any]:
        """
        Run comprehensive verification of ledger integrity
        """
        try:
            # Get sequence range if not provided
            if start_sequence is None or end_sequence is None:
                sequence_range = self._get_verification_range()
                start_sequence = start_sequence or sequence_range['start']
                end_sequence = end_sequence or sequence_range['end']
            
            logger.info(f"Starting verification for sequences {start_sequence} to {end_sequence}")
            
            # Get ledger entries
            entries = self._get_ledger_entries(start_sequence, end_sequence)
            
            if not entries:
                return {
                    'status': 'success',
                    'message': 'No entries to verify',
                    'verificationResults': {}
                }
            
            # Sort entries by sequence number
            sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
            
            # Initialize verification results
            verification_results = {
                'totalEntries': len(sorted_entries),
                'verifiedEntries': 0,
                'failedEntries': 0,
                'chainIntegrityValid': True,
                'signatureIntegrityValid': True,
                'backupIntegrityValid': True,
                'errors': [],
                'warnings': [],
                'verificationTimestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Verify each entry
            for i, entry in enumerate(sorted_entries):
                entry_result = self._verify_single_entry(entry, i, sorted_entries)
                
                if entry_result['valid']:
                    verification_results['verifiedEntries'] += 1
                else:
                    verification_results['failedEntries'] += 1
                    verification_results['errors'].extend(entry_result['errors'])
                
                # Update overall status
                if not entry_result['chainValid']:
                    verification_results['chainIntegrityValid'] = False
                if not entry_result['signatureValid']:
                    verification_results['signatureIntegrityValid'] = False
                if not entry_result['backupValid']:
                    verification_results['backupIntegrityValid'] = False
            
            # Calculate verification score
            verification_score = (verification_results['verifiedEntries'] / 
                                verification_results['totalEntries']) * 100
            
            verification_results['verificationScore'] = round(verification_score, 2)
            verification_results['overallStatus'] = (
                'PASS' if verification_score == 100.0 else 
                'PARTIAL' if verification_score >= 95.0 else 
                'FAIL'
            )
            
            # Send metrics to CloudWatch
            self._send_verification_metrics(verification_results)
            
            logger.info(f"Verification complete: {verification_results['overallStatus']} "
                       f"({verification_score}% success rate)")
            
            return {
                'status': 'success',
                'verificationResults': verification_results
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive verification: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _verify_single_entry(self, entry: Dict[str, Any], index: int, 
                           all_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify integrity of a single ledger entry
        """
        result = {
            'sequenceNumber': entry['sequenceNumber'],
            'valid': True,
            'chainValid': True,
            'signatureValid': True,
            'backupValid': True,
            'errors': []
        }
        
        try:
            # 1. Verify hash chain integrity
            chain_valid = self._verify_chain_hash(entry)
            if not chain_valid:
                result['chainValid'] = False
                result['valid'] = False
                result['errors'].append({
                    'type': 'CHAIN_HASH_INVALID',
                    'message': 'Chain hash verification failed'
                })
            
            # 2. Verify KMS signature
            signature_valid = self._verify_kms_signature(entry)
            if not signature_valid:
                result['signatureValid'] = False
                result['valid'] = False
                result['errors'].append({
                    'type': 'SIGNATURE_INVALID',
                    'message': 'KMS signature verification failed'
                })
            
            # 3. Verify previous hash linkage (except for first entry)
            if index > 0:
                previous_entry = all_entries[index - 1]
                if entry['previousHash'] != previous_entry['chainHash']:
                    result['chainValid'] = False
                    result['valid'] = False
                    result['errors'].append({
                        'type': 'CHAIN_BREAK',
                        'message': f'Previous hash mismatch with sequence {previous_entry["sequenceNumber"]}'
                    })
            
            # 4. Verify S3 backup integrity (async check)
            backup_valid = self._verify_backup_integrity(entry)
            if not backup_valid:
                result['backupValid'] = False
                # Don't fail overall validation for backup issues (warning only)
                result['errors'].append({
                    'type': 'BACKUP_INTEGRITY_WARNING',
                    'message': 'S3 backup verification failed or not found'
                })
            
            # 5. Verify data hash integrity
            data_hash_valid = self._verify_data_hash(entry)
            if not data_hash_valid:
                result['valid'] = False
                result['errors'].append({
                    'type': 'DATA_HASH_INVALID',
                    'message': 'Data hash verification failed'
                })
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append({
                'type': 'VERIFICATION_ERROR',
                'message': f'Verification error: {str(e)}'
            })
        
        return result
    
    def _verify_chain_hash(self, entry: Dict[str, Any]) -> bool:
        """
        Verify the chain hash of a ledger entry
        """
        try:
            # Reconstruct chain hash
            chain_data = f"{entry['dataHash']}{entry['previousHash']}{entry['sequenceNumber']}"
            expected_hash = hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
            
            return entry['chainHash'] == expected_hash
            
        except Exception as e:
            logger.error(f"Error verifying chain hash: {e}")
            return False
    
    def _verify_kms_signature(self, entry: Dict[str, Any]) -> bool:
        """
        Verify KMS signature of a ledger entry
        """
        try:
            # Decode signature from base64
            signature = base64.b64decode(entry['kmsSignature'])
            
            # Verify signature
            response = kms_client.verify(
                KeyId=self.signing_key_id,
                Message=entry['chainHash'].encode('utf-8'),
                MessageType='RAW',
                Signature=signature,
                SigningAlgorithm='RSASSA_PSS_SHA_256'
            )
            
            return response['SignatureValid']
            
        except Exception as e:
            logger.error(f"Error verifying KMS signature: {e}")
            return False
    
    def _verify_backup_integrity(self, entry: Dict[str, Any]) -> bool:
        """
        Verify S3 backup integrity (simplified check)
        """
        try:
            # Generate expected S3 key
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            s3_key = self._generate_s3_key(entry['sequenceNumber'], timestamp)
            
            # Check if backup exists
            s3_client.head_object(
                Bucket=self.backup_bucket,
                Key=s3_key
            )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Backup not found for sequence {entry['sequenceNumber']}")
            else:
                logger.error(f"Error checking backup: {e}")
            return False
    
    def _verify_data_hash(self, entry: Dict[str, Any]) -> bool:
        """
        Verify data hash integrity
        """
        try:
            # For now, just check that dataHash exists and is valid SHA-256
            data_hash = entry.get('dataHash', '')
            
            # Check if it's a valid SHA-256 hash (64 hex characters)
            if len(data_hash) != 64:
                return False
            
            # Check if it's valid hex
            int(data_hash, 16)
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _get_ledger_entries(self, start_sequence: int, end_sequence: int) -> List[Dict[str, Any]]:
        """
        Get ledger entries for verification
        """
        try:
            response = self.ledger_table.query(
                KeyConditionExpression='partition_key = :pk AND sequenceNumber BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':pk': 'GLOBAL_SEQUENCE',
                    ':start': start_sequence,
                    ':end': end_sequence
                },
                ScanIndexForward=True
            )
            return response['Items']
            
        except ClientError as e:
            logger.error(f"Error getting ledger entries: {e}")
            return []
    
    def _get_verification_range(self) -> Dict[str, int]:
        """
        Get appropriate range for verification (last 1000 entries or last 24 hours)
        """
        try:
            # Get the latest entry to determine range
            response = self.ledger_table.query(
                KeyConditionExpression='partition_key = :pk',
                ExpressionAttributeValues={':pk': 'GLOBAL_SEQUENCE'},
                ScanIndexForward=False,
                Limit=1
            )
            
            if not response['Items']:
                return {'start': 1, 'end': 1}
            
            latest_sequence = response['Items'][0]['sequenceNumber']
            
            # Verify last 1000 entries or from sequence 1, whichever is smaller
            start_sequence = max(1, latest_sequence - 999)
            
            return {
                'start': start_sequence,
                'end': latest_sequence
            }
            
        except Exception as e:
            logger.error(f"Error determining verification range: {e}")
            return {'start': 1, 'end': 100}
    
    def _generate_s3_key(self, sequence_number: int, timestamp: datetime) -> str:
        """
        Generate S3 key for backup file
        """
        year = timestamp.year
        month = f"{timestamp.month:02d}"
        day = f"{timestamp.day:02d}"
        hour = f"{timestamp.hour:02d}"
        
        return f"ledger/{year}/{month}/{day}/{hour}/seq-{sequence_number}.json"
    
    def _send_verification_metrics(self, results: Dict[str, Any]) -> None:
        """
        Send verification metrics to CloudWatch
        """
        try:
            cloudwatch.put_metric_data(
                Namespace='AquaChain/Ledger',
                MetricData=[
                    {
                        'MetricName': 'VerificationScore',
                        'Value': results['verificationScore'],
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'VerifiedEntries',
                        'Value': results['verifiedEntries'],
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'FailedEntries',
                        'Value': results['failedEntries'],
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
        except Exception as e:
            logger.warning(f"Error sending CloudWatch metrics: {e}")

def lambda_handler(event, context):
    """
    Lambda handler for ledger verification operations
    """
    try:
        logger.info(f"Ledger verification request: {json.dumps(event)}")
        
        verification_service = LedgerVerificationService()
        operation = event.get('operation', 'comprehensive_verification')
        
        if operation == 'comprehensive_verification':
            # Run comprehensive verification
            start_seq = event.get('startSequence')
            end_seq = event.get('endSequence')
            
            result = verification_service.run_comprehensive_verification(start_seq, end_seq)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result, default=str)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid operation'})
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in ledger verification: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }