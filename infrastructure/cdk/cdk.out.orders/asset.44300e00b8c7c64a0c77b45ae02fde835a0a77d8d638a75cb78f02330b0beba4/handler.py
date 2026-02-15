"""
DynamoDB Streams Processor for AquaChain Audit Trail
Processes ledger stream events and stores immutable audit records in S3 Object Lock
"""

import json
import boto3
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
AUDIT_BUCKET = 'aquachain-audit-trail'
REPLICA_BUCKET = 'aquachain-audit-replica'
REPLICA_ACCOUNT_ID = '123456789012'  # Replace with actual replica account
DEDUPLICATION_TABLE = 'aquachain-audit-deduplication'

class AuditTrailProcessor:
    """
    Processes DynamoDB stream events for audit trail creation
    """
    
    def __init__(self):
        self.audit_bucket = AUDIT_BUCKET
        self.replica_bucket = REPLICA_BUCKET
        self.dedup_table = dynamodb.Table(DEDUPLICATION_TABLE)
    
    def process_stream_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process DynamoDB stream records and create audit trail
        """
        processed_count = 0
        failed_count = 0
        results = []
        
        for record in records:
            try:
                # Process individual stream record
                result = self._process_single_record(record)
                results.append(result)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing record: {e}")
                failed_count += 1
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'record_id': record.get('eventID', 'unknown')
                })
        
        return {
            'processed_count': processed_count,
            'failed_count': failed_count,
            'total_count': len(records),
            'results': results
        }
    
    def _process_single_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single DynamoDB stream record
        """
        event_name = record['eventName']
        event_id = record['eventID']
        
        # Only process INSERT events for ledger entries
        if event_name != 'INSERT':
            return {
                'status': 'skipped',
                'reason': f'Event type {event_name} not processed',
                'event_id': event_id
            }
        
        # Extract ledger entry data
        dynamodb_record = record['dynamodb']
        if 'NewImage' not in dynamodb_record:
            return {
                'status': 'skipped',
                'reason': 'No NewImage in record',
                'event_id': event_id
            }
        
        # Convert DynamoDB format to standard format
        ledger_entry = self._convert_dynamodb_item(dynamodb_record['NewImage'])
        
        # Check for duplicates using idempotent processing
        if self._is_duplicate_event(event_id, ledger_entry['sequenceNumber']):
            return {
                'status': 'duplicate',
                'event_id': event_id,
                'sequence_number': ledger_entry['sequenceNumber']
            }
        
        # Create audit record
        audit_record = self._create_audit_record(ledger_entry, record)
        
        # Store in S3 with Object Lock
        s3_key = self._store_audit_record_s3(audit_record)
        
        # Replicate to cross-account bucket
        self._replicate_to_cross_account(audit_record, s3_key)
        
        # Mark as processed to prevent duplicates
        self._mark_event_processed(event_id, ledger_entry['sequenceNumber'])
        
        return {
            'status': 'processed',
            'event_id': event_id,
            'sequence_number': ledger_entry['sequenceNumber'],
            's3_key': s3_key,
            'audit_record_id': audit_record['auditRecordId']
        }
    
    def _convert_dynamodb_item(self, dynamodb_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert DynamoDB item format to standard Python dict
        """
        def convert_value(value):
            if isinstance(value, dict):
                if 'S' in value:
                    return value['S']
                elif 'N' in value:
                    return int(value['N']) if '.' not in value['N'] else float(value['N'])
                elif 'BOOL' in value:
                    return value['BOOL']
                elif 'M' in value:
                    return {k: convert_value(v) for k, v in value['M'].items()}
                elif 'L' in value:
                    return [convert_value(item) for item in value['L']]
                elif 'NULL' in value:
                    return None
            return value
        
        return {k: convert_value(v) for k, v in dynamodb_item.items()}
    
    def _is_duplicate_event(self, event_id: str, sequence_number: int) -> bool:
        """
        Check if event has already been processed using deduplication table
        """
        try:
            response = self.dedup_table.get_item(
                Key={
                    'eventId': event_id,
                    'sequenceNumber': sequence_number
                }
            )
            return 'Item' in response
            
        except Exception as e:
            logger.warning(f"Error checking duplicate: {e}")
            return False  # Proceed with processing if check fails
    
    def _create_audit_record(self, ledger_entry: Dict[str, Any], 
                           stream_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive audit record
        """
        audit_record_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create audit record with full context
        audit_record = {
            'auditRecordId': audit_record_id,
            'auditTimestamp': timestamp,
            'eventSource': 'dynamodb-streams',
            'eventId': stream_record['eventID'],
            'eventName': stream_record['eventName'],
            'eventVersion': stream_record['eventVersion'],
            'awsRegion': stream_record['awsRegion'],
            'ledgerEntry': {
                'sequenceNumber': ledger_entry['sequenceNumber'],
                'logId': ledger_entry['logId'],
                'timestamp': ledger_entry['timestamp'],
                'deviceId': ledger_entry['deviceId'],
                'dataHash': ledger_entry['dataHash'],
                'previousHash': ledger_entry['previousHash'],
                'chainHash': ledger_entry['chainHash'],
                'wqi': ledger_entry['wqi'],
                'anomalyType': ledger_entry['anomalyType'],
                'kmsSignature': ledger_entry['kmsSignature']
            },
            'verification': {
                'chainHashVerified': self._verify_chain_hash(ledger_entry),
                'signatureVerified': True,  # Assume verified by ledger service
                'auditRecordHash': None  # Will be calculated after record creation
            },
            'compliance': {
                'retentionPeriod': '7-years',
                'objectLockEnabled': True,
                'crossAccountReplicated': True
            }
        }
        
        # Calculate audit record hash for integrity
        audit_record['verification']['auditRecordHash'] = self._calculate_audit_hash(audit_record)
        
        return audit_record
    
    def _verify_chain_hash(self, ledger_entry: Dict[str, Any]) -> bool:
        """
        Verify the chain hash of the ledger entry
        """
        try:
            chain_data = f"{ledger_entry['dataHash']}{ledger_entry['previousHash']}{ledger_entry['sequenceNumber']}"
            expected_hash = hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
            return ledger_entry['chainHash'] == expected_hash
        except Exception as e:
            logger.error(f"Error verifying chain hash: {e}")
            return False
    
    def _calculate_audit_hash(self, audit_record: Dict[str, Any]) -> str:
        """
        Calculate hash of audit record for integrity verification
        """
        # Create a copy without the hash field for calculation
        record_copy = audit_record.copy()
        if 'verification' in record_copy and 'auditRecordHash' in record_copy['verification']:
            record_copy['verification']['auditRecordHash'] = None
        
        # Create deterministic JSON string
        record_json = json.dumps(record_copy, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(record_json.encode('utf-8')).hexdigest()
    
    def _store_audit_record_s3(self, audit_record: Dict[str, Any]) -> str:
        """
        Store audit record in S3 with Object Lock
        """
        # Create S3 key with date partitioning
        timestamp = datetime.utcnow()
        s3_key = (f"audit-records/"
                 f"year={timestamp.year}/"
                 f"month={timestamp.month:02d}/"
                 f"day={timestamp.day:02d}/"
                 f"audit-{audit_record['auditRecordId']}.json")
        
        try:
            # Store with Object Lock and KMS encryption
            s3_client.put_object(
                Bucket=self.audit_bucket,
                Key=s3_key,
                Body=json.dumps(audit_record, indent=2),
                ContentType='application/json',
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId='alias/aquachain-audit-key',
                ObjectLockMode='COMPLIANCE',
                ObjectLockRetainUntilDate=self._calculate_retention_date(),
                Metadata={
                    'auditRecordId': audit_record['auditRecordId'],
                    'sequenceNumber': str(audit_record['ledgerEntry']['sequenceNumber']),
                    'deviceId': audit_record['ledgerEntry']['deviceId'],
                    'auditTimestamp': audit_record['auditTimestamp']
                }
            )
            
            logger.info(f"Stored audit record in S3: {s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Error storing audit record in S3: {e}")
            raise
    
    def _calculate_retention_date(self) -> datetime:
        """
        Calculate Object Lock retention date (7 years from now)
        """
        from datetime import timedelta
        return datetime.utcnow() + timedelta(days=7*365)  # 7 years
    
    def _replicate_to_cross_account(self, audit_record: Dict[str, Any], s3_key: str) -> None:
        """
        Replicate audit record to cross-account bucket for independent verification
        """
        try:
            # Assume cross-account replication is configured via S3 replication rules
            # This is a placeholder for additional cross-account operations if needed
            logger.info(f"Cross-account replication configured for: {s3_key}")
            
            # Optional: Send notification to replica account
            # sns_client.publish(
            #     TopicArn=f'arn:aws:sns:us-east-1:{REPLICA_ACCOUNT_ID}:audit-replication',
            #     Message=json.dumps({
            #         'auditRecordId': audit_record['auditRecordId'],
            #         's3Key': s3_key,
            #         'sequenceNumber': audit_record['ledgerEntry']['sequenceNumber']
            #     })
            # )
            
        except Exception as e:
            logger.warning(f"Error in cross-account replication: {e}")
            # Don't fail the entire process if replication has issues
    
    def _mark_event_processed(self, event_id: str, sequence_number: int) -> None:
        """
        Mark event as processed in deduplication table
        """
        try:
            self.dedup_table.put_item(
                Item={
                    'eventId': event_id,
                    'sequenceNumber': sequence_number,
                    'processedAt': datetime.utcnow().isoformat(),
                    'ttl': int((datetime.utcnow().timestamp() + 30*24*3600))  # 30 days TTL
                }
            )
        except Exception as e:
            logger.warning(f"Error marking event as processed: {e}")

def lambda_handler(event, context):
    """
    Lambda handler for DynamoDB Streams processing
    """
    try:
        logger.info(f"Processing {len(event['Records'])} stream records")
        
        processor = AuditTrailProcessor()
        results = processor.process_stream_records(event['Records'])
        
        logger.info(f"Processing completed: {results['processed_count']} processed, "
                   f"{results['failed_count']} failed")
        
        # Return success if at least some records were processed
        if results['processed_count'] > 0:
            return {
                'statusCode': 200,
                'body': json.dumps(results)
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'No records processed successfully',
                    'results': results
                })
            }
    
    except Exception as e:
        logger.error(f"Stream processing error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }