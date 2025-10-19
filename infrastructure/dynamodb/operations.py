"""
DynamoDB operations for AquaChain system
Handles atomic sequence generation, ledger operations, and data queries
"""

import boto3
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

class DynamoDBOperations:
    def __init__(self, region_name: str = 'us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.client = boto3.client('dynamodb', region_name=region_name)
        
        # Table references
        self.readings_table = self.dynamodb.Table('aquachain-readings')
        self.ledger_table = self.dynamodb.Table('aquachain-ledger')
        self.sequence_table = self.dynamodb.Table('aquachain-sequence')
        self.users_table = self.dynamodb.Table('aquachain-users')
        self.service_requests_table = self.dynamodb.Table('aquachain-service-requests')
    
    def get_next_sequence_number(self) -> int:
        """
        Atomically get next sequence number for ledger entries
        Uses conditional update to ensure atomicity
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
            print(f"Error getting sequence number: {e}")
            raise
    
    def get_previous_ledger_hash(self) -> str:
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
                # Genesis block hash
                return '0' * 64
        except ClientError as e:
            print(f"Error getting previous hash: {e}")
            return '0' * 64
    
    def create_ledger_entry(self, device_id: str, data_hash: str, wqi: float, 
                          anomaly_type: str) -> Dict[str, Any]:
        """
        Create a new ledger entry with hash chaining
        """
        sequence_number = self.get_next_sequence_number()
        previous_hash = self.get_previous_ledger_hash()
        timestamp = datetime.utcnow().isoformat()
        log_id = str(uuid.uuid4())
        
        # Create chain hash: SHA-256(dataHash + previousHash + sequenceNumber)
        chain_data = f"{data_hash}{previous_hash}{sequence_number}"
        chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        
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
            'anomalyType': anomaly_type
        }
        
        try:
            self.ledger_table.put_item(Item=ledger_entry)
            print(f"Created ledger entry {log_id} with sequence {sequence_number}")
            return ledger_entry
        except ClientError as e:
            print(f"Error creating ledger entry: {e}")
            raise
    
    def store_reading(self, device_id: str, timestamp: str, readings: Dict[str, float],
                     wqi: float, anomaly_type: str, location: Dict[str, float],
                     diagnostics: Dict[str, Any], s3_reference: str) -> Dict[str, Any]:
        """
        Store water quality reading with time-windowed partition key
        """
        from .tables import generate_time_windowed_partition_key, calculate_ttl_timestamp
        
        # Generate partition key with time window
        partition_key = generate_time_windowed_partition_key(device_id, timestamp)
        
        # Create data hash for ledger
        reading_data = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'readings': readings,
            'wqi': wqi,
            'location': location
        }
        data_hash = hashlib.sha256(json.dumps(reading_data, sort_keys=True).encode()).hexdigest()
        
        # Create ledger entry first
        ledger_entry = self.create_ledger_entry(device_id, data_hash, wqi, anomaly_type)
        
        # Store reading with TTL
        reading_item = {
            'deviceId_month': partition_key,
            'timestamp': timestamp,
            'deviceId': device_id,
            'readings': readings,
            'wqi': wqi,
            'anomalyType': anomaly_type,
            'location': location,
            'diagnostics': diagnostics,
            's3Reference': s3_reference,
            'ledgerHash': ledger_entry['chainHash'],
            'ledgerSequence': ledger_entry['sequenceNumber'],
            'ttl': calculate_ttl_timestamp(90)  # 90 days TTL
        }
        
        try:
            self.readings_table.put_item(Item=reading_item)
            print(f"Stored reading for device {device_id} at {timestamp}")
            return reading_item
        except ClientError as e:
            print(f"Error storing reading: {e}")
            raise
    
    def get_device_readings(self, device_id: str, start_time: str, end_time: str,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get readings for a device within time range using GSI
        """
        try:
            response = self.readings_table.query(
                IndexName='DeviceIndex',
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
            print(f"Error getting device readings: {e}")
            return []
    
    def get_ledger_chain(self, start_sequence: int, end_sequence: int) -> List[Dict[str, Any]]:
        """
        Get ledger entries for hash chain verification
        """
        try:
            response = self.ledger_table.query(
                KeyConditionExpression='partition_key = :pk AND sequenceNumber BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':pk': 'GLOBAL_SEQUENCE',
                    ':start': start_sequence,
                    ':end': end_sequence
                },
                ScanIndexForward=True  # Ascending order for chain verification
            )
            return response['Items']
        except ClientError as e:
            print(f"Error getting ledger chain: {e}")
            return []
    
    def verify_hash_chain(self, entries: List[Dict[str, Any]]) -> bool:
        """
        Verify the integrity of hash chain entries
        """
        if not entries:
            return True
        
        # Sort by sequence number
        sorted_entries = sorted(entries, key=lambda x: x['sequenceNumber'])
        
        for i, entry in enumerate(sorted_entries):
            # Reconstruct chain hash
            chain_data = f"{entry['dataHash']}{entry['previousHash']}{entry['sequenceNumber']}"
            expected_hash = hashlib.sha256(chain_data.encode()).hexdigest()
            
            if entry['chainHash'] != expected_hash:
                print(f"Hash mismatch at sequence {entry['sequenceNumber']}")
                return False
            
            # Check previous hash linkage (except for first entry)
            if i > 0:
                previous_entry = sorted_entries[i-1]
                if entry['previousHash'] != previous_entry['chainHash']:
                    print(f"Chain break at sequence {entry['sequenceNumber']}")
                    return False
        
        return True
    
    def create_user(self, user_id: str, email: str, role: str, profile: Dict[str, Any],
                   device_ids: List[str] = None, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new user profile
        """
        user_item = {
            'userId': user_id,
            'email': email,
            'role': role,
            'profile': profile,
            'deviceIds': device_ids or [],
            'preferences': preferences or {
                'notifications': {'push': True, 'sms': True, 'email': True},
                'theme': 'auto',
                'language': 'en'
            },
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Add role-specific fields
        if role == 'technician':
            user_item['workSchedule'] = {
                'monday': {'start': '09:00', 'end': '17:00'},
                'tuesday': {'start': '09:00', 'end': '17:00'},
                'wednesday': {'start': '09:00', 'end': '17:00'},
                'thursday': {'start': '09:00', 'end': '17:00'},
                'friday': {'start': '09:00', 'end': '17:00'},
                'overrideStatus': 'available'
            }
            user_item['performanceScore'] = 100.0
        
        try:
            self.users_table.put_item(Item=user_item)
            print(f"Created user {user_id} with role {role}")
            return user_item
        except ClientError as e:
            print(f"Error creating user: {e}")
            raise
    
    def create_service_request(self, consumer_id: str, device_id: str, 
                             location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new service request
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        service_request = {
            'requestId': request_id,
            'timestamp': timestamp,
            'consumerId': consumer_id,
            'deviceId': device_id,
            'status': 'pending',
            'location': location,
            'notes': [],
            'createdAt': timestamp
        }
        
        try:
            self.service_requests_table.put_item(Item=service_request)
            print(f"Created service request {request_id}")
            return service_request
        except ClientError as e:
            print(f"Error creating service request: {e}")
            raise
    
    def update_service_request_status(self, request_id: str, timestamp: str, 
                                    status: str, technician_id: str = None,
                                    notes: str = None) -> Dict[str, Any]:
        """
        Update service request status
        """
        update_expression = 'SET #status = :status, updatedAt = :updated'
        expression_values = {
            ':status': status,
            ':updated': datetime.utcnow().isoformat()
        }
        expression_names = {'#status': 'status'}
        
        if technician_id:
            update_expression += ', technicianId = :tech_id'
            expression_values[':tech_id'] = technician_id
        
        if notes:
            update_expression += ', notes = list_append(if_not_exists(notes, :empty_list), :note)'
            expression_values[':empty_list'] = []
            expression_values[':note'] = [{
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'status_update',
                'content': notes
            }]
        
        try:
            response = self.service_requests_table.update_item(
                Key={'requestId': request_id, 'timestamp': timestamp},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            return response['Attributes']
        except ClientError as e:
            print(f"Error updating service request: {e}")
            raise