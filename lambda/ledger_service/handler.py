"""
Secure Ledger Service for AquaChain System
Implements cryptographic hash chaining with KMS signing for tamper-evident records
"""

import json
import boto3
import hashlib
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
kms_client = boto3.client('kms')

# Environment variables
LEDGER_TABLE = 'aquachain-ledger'
SEQUENCE_TABLE = 'aquachain-sequence'
SIGNING_KEY_ALIAS = 'alias/aquachain-ledger-signing-key'

class LedgerError(Exception):
    """Custom exception for ledger operations"""
    pass

class SecureLedgerService:
    """
    Secure ledger service with cryptographic verification
    """
    
    def __init__(self):
        self.ledger_table = dynamodb.Table(LEDGER_TABLE)
        self.sequence_table = dynamodb.Table(SEQUENCE_TABLE)
        self.signing_key_id = SIGNING_KEY_ALIAS
    
    def create_ledger_entry(self, device_id: str, data_hash: str, wqi: float, 
                          anomaly_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new ledger entry with hash chaining and KMS signing
        """
        try:
            # Get next sequence number atomically
            sequence_number = self._get_next_sequence_number()
            
            # Get previous hash for chaining
            previous_hash = self._get_previous_ledger_hash()
            
            # Create unique log ID
            log_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Create chain hash: SHA-256(dataHash + previousHash + sequenceNumber)
            chain_data = f"{data_hash}{previous_hash}{sequence_number}"
            chain_hash = hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
            
            # Sign the chain hash with KMS
            kms_signature = self._sign_with_kms(chain_hash)
            
            # Create ledger entry
            ledger_entry = {
                'partition_key': 'GLOBAL_SEQUENCE',
                'sequenceNumber': sequence_number,
                'logId': log_id,
                'timestamp': timestamp,
                'deviceId': device_id,
                'dataHash': data_hash,
                'previousHash': previous_hash,
                'chainHash': chain_hash,
                'wqi': wqi,
                'anomalyType': anomaly_type,
                'kmsSignature': kms_signature,
                'metadata': metadata or {}
            }
            
            # Store in DynamoDB with conditional write for consistency
            self._store_ledger_entry(ledger_entry)
            
            logger.info(f"Created ledger entry {log_id} with sequence {sequence_number}")
            return ledger_entry
            
        except Exception as e:
            logger.error(f"Error creating ledger entry: {e}")
            raise LedgerError(f"Failed to create ledger entry: {e}")
    
    def _get_next_sequence_number(self) -> int:
        """
        Atomically get next sequence number for global ordering
        """
        try:
            response = self.sequence_table.update_item(
                Key={'sequenceType': 'LEDGER'},
                UpdateExpression='ADD currentSequence :inc SET lastUpdated = :timestamp',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':timestamp': datetime.utcnow().isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )
            return int(response['Attributes']['currentSequence'])
            
        except ClientError as e:
            logger.error(f"Error getting sequence number: {e}")
            raise LedgerError(f"Failed to get sequence number: {e}")
    
    def _get_previous_ledger_hash(self) -> str:
        """
        Get the hash of the most recent ledger entry for chain linking
        """
        try:
            response = self.ledger_table.query(
                KeyConditionExpression='partition_key = :pk',
                ExpressionAttributeValues={':pk': 'GLOBAL_SEQUENCE'},
                ScanIndexForward=False,  # Descending order
                Limit=1
            )
            
            if response['Items']:
                return response['Items'][0]['chainHash']
            else:
                # Genesis block hash (64 zeros)
                return '0' * 64
                
        except ClientError as e:
            logger.warning(f"Error getting previous hash: {e}")
            return '0' * 64  # Fallback to genesis hash
    
    def _sign_with_kms(self, data: str) -> str:
        """
        Sign data using KMS asymmetric key
        """
        try:
            response = kms_client.sign(
                KeyId=self.signing_key_id,
                Message=data.encode('utf-8'),
                MessageType='RAW',
                SigningAlgorithm='RSASSA_PSS_SHA_256'
            )
            
            # Return base64 encoded signature
            return base64.b64encode(response['Signature']).decode('utf-8')
            
        except ClientError as e:
            logger.error(f"Error signing with KMS: {e}")
            raise LedgerError(f"Failed to sign data: {e}")
    
    def _store_ledger_entry(self, ledger_entry: Dict[str, Any]) -> None:
        """
        Store ledger entry in DynamoDB with conditional write
        """
        try:
            # Use conditional write to ensure sequence number uniqueness
            self.ledger_table.put_item(
                Item=ledger_entry,
                ConditionExpression='attribute_not_exists(sequenceNumber)'
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Sequence number collision: {ledger_entry['sequenceNumber']}")
                raise LedgerError("Sequence number already exists")
            else:
                logger.error(f"Error storing ledger entry: {e}")
                raise LedgerError(f"Failed to store ledger entry: {e}")
    
    def verify_hash_chain(self, start_sequence: int, end_sequence: int) -> Dict[str, Any]:
        """
        Verify the integrity of hash chain entries
        """
        try:
            # Get ledger entries in sequence order
            entries = self._get_ledger_entries(start_sequence, end_sequence)
            
            if not entries:
                return {'valid': True, 'message': 'No entries to verify'}
            
            # Sort by sequence number
            sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
            
            verification_results = {
                'valid': True,
                'verified_entries': 0,
                'total_entries': len(sorted_entries),
                'errors': []
            }
            
            for i, entry in enumerate(sorted_entries):
                # Verify hash chain integrity
                chain_valid = self._verify_chain_hash(entry)
                if not chain_valid:
                    verification_results['valid'] = False
                    verification_results['errors'].append({
                        'sequence': entry['sequenceNumber'],
                        'error': 'Invalid chain hash'
                    })
                
                # Verify KMS signature
                signature_valid = self._verify_kms_signature(entry)
                if not signature_valid:
                    verification_results['valid'] = False
                    verification_results['errors'].append({
                        'sequence': entry['sequenceNumber'],
                        'error': 'Invalid KMS signature'
                    })
                
                # Verify previous hash linkage (except for first entry)
                if i > 0:
                    previous_entry = sorted_entries[i-1]
                    if entry['previousHash'] != previous_entry['chainHash']:
                        verification_results['valid'] = False
                        verification_results['errors'].append({
                            'sequence': entry['sequenceNumber'],
                            'error': 'Chain break - previous hash mismatch'
                        })
                
                if chain_valid and signature_valid:
                    verification_results['verified_entries'] += 1
            
            logger.info(f"Verified {verification_results['verified_entries']}/{verification_results['total_entries']} entries")
            return verification_results
            
        except Exception as e:
            logger.error(f"Error verifying hash chain: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _get_ledger_entries(self, start_sequence: int, end_sequence: int) -> list:
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
                ScanIndexForward=True  # Ascending order
            )
            return response['Items']
            
        except ClientError as e:
            logger.error(f"Error getting ledger entries: {e}")
            return []
    
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
    
    def get_ledger_entry(self, sequence_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific ledger entry by sequence number
        """
        try:
            response = self.ledger_table.get_item(
                Key={
                    'partition_key': 'GLOBAL_SEQUENCE',
                    'sequenceNumber': sequence_number
                }
            )
            
            return response.get('Item')
            
        except ClientError as e:
            logger.error(f"Error getting ledger entry: {e}")
            return None
    
    def get_device_ledger_entries(self, device_id: str, start_time: str, 
                                end_time: str, limit: int = 100) -> list:
        """
        Get ledger entries for a specific device within time range
        """
        try:
            response = self.ledger_table.query(
                IndexName='DeviceLedgerIndex',
                KeyConditionExpression='deviceId = :device_id AND #ts BETWEEN :start AND :end',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':device_id': device_id,
                    ':start': start_time,
                    ':end': end_time
                },
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            return response['Items']
            
        except ClientError as e:
            logger.error(f"Error getting device ledger entries: {e}")
            return []

def lambda_handler(event, context):
    """
    Lambda handler for ledger service operations
    """
    try:
        logger.info(f"Ledger service request: {json.dumps(event)}")
        
        ledger_service = SecureLedgerService()
        operation = event.get('operation')
        
        if operation == 'create_entry':
            # Create new ledger entry
            result = ledger_service.create_ledger_entry(
                device_id=event['deviceId'],
                data_hash=event['dataHash'],
                wqi=event['wqi'],
                anomaly_type=event['anomalyType'],
                metadata=event.get('metadata', {})
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'logId': result['logId'],
                    'sequenceNumber': result['sequenceNumber'],
                    'chainHash': result['chainHash'],
                    'timestamp': result['timestamp']
                })
            }
        
        elif operation == 'verify_chain':
            # Verify hash chain integrity
            start_seq = event.get('startSequence', 1)
            end_seq = event.get('endSequence', 100)
            
            result = ledger_service.verify_hash_chain(start_seq, end_seq)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        elif operation == 'get_entry':
            # Get specific ledger entry
            sequence_number = event['sequenceNumber']
            entry = ledger_service.get_ledger_entry(sequence_number)
            
            if entry:
                return {
                    'statusCode': 200,
                    'body': json.dumps(entry, default=str)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Ledger entry not found'})
                }
        
        elif operation == 'get_device_entries':
            # Get device-specific ledger entries
            entries = ledger_service.get_device_ledger_entries(
                device_id=event['deviceId'],
                start_time=event['startTime'],
                end_time=event['endTime'],
                limit=event.get('limit', 100)
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps(entries, default=str)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid operation'})
            }
    
    except LedgerError as e:
        logger.error(f"Ledger error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }