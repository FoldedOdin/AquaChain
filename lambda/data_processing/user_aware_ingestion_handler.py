"""
User-Aware Data Ingestion Lambda
Processes IoT device readings with user context and ownership validation
"""

import json
import os
import boto3
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import hashlib
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices-dev')
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings-dev')
LEDGER_TABLE = os.environ.get('LEDGER_TABLE', 'AquaChain-Ledger-dev')
ENABLE_CACHE = os.environ.get('ENABLE_DEVICE_CACHE', 'true').lower() == 'true'

# DynamoDB tables
devices_table = dynamodb.Table(DEVICES_TABLE)
readings_table = dynamodb.Table(READINGS_TABLE)
ledger_table = dynamodb.Table(LEDGER_TABLE)

# In-memory cache for device ownership (Lambda container reuse)
device_cache = {}
CACHE_TTL = 300  # 5 minutes


class DeviceOwnershipCache:
    """Simple in-memory cache for device-to-user mappings"""
    
    @staticmethod
    def get(device_id: str) -> Optional[Dict[str, Any]]:
        """Get cached device info"""
        if not ENABLE_CACHE:
            return None
        
        cached = device_cache.get(device_id)
        if not cached:
            return None
        
        # Check TTL
        if (datetime.utcnow().timestamp() - cached['cached_at']) > CACHE_TTL:
            del device_cache[device_id]
            return None
        
        return cached['data']
    
    @staticmethod
    def set(device_id: str, device_data: Dict[str, Any]):
        """Cache device info"""
        if ENABLE_CACHE:
            device_cache[device_id] = {
                'data': device_data,
                'cached_at': datetime.utcnow().timestamp()
            }


def lookup_device_owner(device_id: str) -> Dict[str, Any]:
    """
    Lookup device owner from DynamoDB with caching
    
    Returns:
        Device record with user_id
    
    Raises:
        ValueError: If device not found or invalid
    """
    # Check cache first
    cached_device = DeviceOwnershipCache.get(device_id)
    if cached_device:
        print(f"✅ Cache hit for device: {device_id}")
        return cached_device
    
    # Query DynamoDB
    try:
        response = devices_table.get_item(Key={'device_id': device_id})
        
        if 'Item' not in response:
            raise ValueError(f"Unknown device_id: {device_id}")
        
        device = response['Item']
        
        # Validate device is active
        if device.get('status') != 'active':
            raise ValueError(f"Device {device_id} is not active (status: {device.get('status')})")
        
        # Cache the result
        DeviceOwnershipCache.set(device_id, device)
        
        print(f"✅ Device owner lookup: {device_id} → {device['user_id']}")
        return device
        
    except ClientError as e:
        print(f"❌ DynamoDB error looking up device: {e}")
        raise ValueError(f"Error looking up device: {e}")


def validate_reading(reading: Dict[str, Any]) -> bool:
    """Validate sensor reading data"""
    required_fields = ['pH', 'turbidity', 'tds', 'temperature']
    
    for field in required_fields:
        if field not in reading:
            print(f"⚠️  Missing required field: {field}")
            return False
        
        value = reading[field]
        
        # Basic range validation
        if field == 'pH' and not (0 <= value <= 14):
            print(f"⚠️  pH out of range: {value}")
            return False
        
        if field == 'turbidity' and not (0 <= value <= 1000):
            print(f"⚠️  Turbidity out of range: {value}")
            return False
        
        if field == 'tds' and not (0 <= value <= 2000):
            print(f"⚠️  TDS out of range: {value}")
            return False
        
        if field == 'temperature' and not (-10 <= value <= 50):
            print(f"⚠️  Temperature out of range: {value}")
            return False
    
    return True


def calculate_reading_hash(reading_data: Dict[str, Any]) -> str:
    """Calculate SHA-256 hash of reading for ledger"""
    # Sort keys for consistent hashing
    sorted_data = json.dumps(reading_data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def store_reading_with_user_context(device_id: str, user_id: str, reading: Dict[str, Any], 
                                    timestamp: str, device_info: Dict[str, Any]):
    """
    Store reading in DynamoDB with user_id tag
    
    This ensures all readings are associated with the correct user
    for proper data isolation and access control
    """
    # Create partition key with user context
    month = timestamp[:7]  # YYYY-MM
    partition_key = f"{user_id}#{device_id}#{month}"
    
    # Prepare reading item
    reading_item = {
        'user_id': user_id,  # ✅ Critical: User association
        'device_id': device_id,
        'deviceId_month': partition_key,  # Composite key for efficient queries
        'timestamp': timestamp,
        'reading': reading,
        'pH': Decimal(str(reading['pH'])),
        'turbidity': Decimal(str(reading['turbidity'])),
        'tds': Decimal(str(reading['tds'])),
        'temperature': Decimal(str(reading['temperature'])),
        'metric_type': 'water_quality',
        'alert_level': determine_alert_level(reading),
        'device_firmware': device_info.get('firmware_version', 'unknown'),
        'ingestion_timestamp': datetime.utcnow().isoformat(),
        'ttl': int(datetime.utcnow().timestamp()) + (365 * 24 * 60 * 60)  # 1 year retention
    }
    
    # Store in readings table
    readings_table.put_item(Item=reading_item)
    
    print(f"✅ Reading stored: user={user_id}, device={device_id}, ts={timestamp}")
    
    return reading_item


def store_in_ledger(user_id: str, device_id: str, reading_item: Dict[str, Any]):
    """Store immutable record in ledger for audit trail"""
    try:
        # Calculate hash
        reading_hash = calculate_reading_hash(reading_item)
        
        # Get next sequence number (simplified - production would use atomic counter)
        sequence_number = int(datetime.utcnow().timestamp() * 1000)
        
        ledger_entry = {
            'GLOBAL_SEQUENCE': 'GLOBAL_SEQUENCE',
            'sequenceNumber': sequence_number,
            'user_id': user_id,
            'device_id': device_id,
            'timestamp': reading_item['timestamp'],
            'reading_hash': reading_hash,
            'event_type': 'READING_INGESTED',
            'created_at': datetime.utcnow().isoformat()
        }
        
        ledger_table.put_item(Item=ledger_entry)
        print(f"✅ Ledger entry created: seq={sequence_number}")
        
    except Exception as e:
        print(f"⚠️  Error writing to ledger: {e}")
        # Don't fail the entire ingestion if ledger write fails


def determine_alert_level(reading: Dict[str, Any]) -> str:
    """Determine alert level based on reading values"""
    pH = reading['pH']
    turbidity = reading['turbidity']
    tds = reading['tds']
    
    # Critical thresholds
    if pH < 6.0 or pH > 8.5 or turbidity > 5 or tds > 500:
        return 'critical'
    
    # Warning thresholds
    if pH < 6.5 or pH > 8.0 or turbidity > 3 or tds > 300:
        return 'warning'
    
    return 'normal'


def update_device_last_seen(device_id: str, timestamp: str):
    """Update device last_seen timestamp and set status to online"""
    try:
        devices_table.update_item(
            Key={'deviceId': device_id},  # Use correct key format
            UpdateExpression='SET lastSeen = :ts, connectionStatus = :status, statusUpdatedAt = :status_ts',
            ExpressionAttributeValues={
                ':ts': timestamp,
                ':status': 'online',
                ':status_ts': timestamp
            }
        )
        print(f"✅ Updated device {device_id} lastSeen and status to online")
    except Exception as e:
        print(f"⚠️  Error updating device status: {e}")


def publish_metrics(user_id: str, device_id: str, reading: Dict[str, Any]):
    """Publish custom CloudWatch metrics"""
    try:
        cloudwatch.put_metric_data(
            Namespace='AquaChain/Readings',
            MetricData=[
                {
                    'MetricName': 'pH',
                    'Value': reading['pH'],
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'UserId', 'Value': user_id},
                        {'Name': 'DeviceId', 'Value': device_id}
                    ]
                },
                {
                    'MetricName': 'Turbidity',
                    'Value': reading['turbidity'],
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'UserId', 'Value': user_id},
                        {'Name': 'DeviceId', 'Value': device_id}
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"⚠️  Error publishing metrics: {e}")


def lambda_handler(event, context):
    """
    Main Lambda handler for user-aware IoT data ingestion
    
    Event structure from IoT Rule:
    {
        "deviceId": "AquaChain-Device-001",
        "reading": {
            "pH": 7.2,
            "turbidity": 1.5,
            "tds": 150,
            "temperature": 22.5,
            "humidity": 65
        },
        "timestamp": "2025-10-26T12:00:00Z"
    }
    """
    print(f"📥 Received event: {json.dumps(event)}")
    
    try:
        # Import security audit logger
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
        from security_audit_logger import audit_logger
        
        # Extract payload
        device_id = event.get('deviceId')
        reading = event.get('reading', {})
        timestamp = event.get('timestamp') or datetime.utcnow().isoformat()
        
        if not device_id:
            raise ValueError("Missing deviceId in event")
        
        if not reading:
            raise ValueError("Missing reading data in event")
        
        # Validate reading data
        if not validate_reading(reading):
            raise ValueError("Invalid reading data")
        
        # 1️⃣ CRITICAL: Lookup device owner
        device_info = lookup_device_owner(device_id)
        user_id = device_info['user_id']
        
        print(f"👤 Processing reading for user: {user_id}")
        
        # 2️⃣ Store reading with user context
        reading_item = store_reading_with_user_context(
            device_id=device_id,
            user_id=user_id,
            reading=reading,
            timestamp=timestamp,
            device_info=device_info
        )
        
        # 3️⃣ Store in immutable ledger
        store_in_ledger(user_id, device_id, reading_item)
        
        # 4️⃣ Update device last_seen
        update_device_last_seen(device_id, timestamp)
        
        # 5️⃣ Publish CloudWatch metrics
        publish_metrics(user_id, device_id, reading)
        
        # 6️⃣ Check for alerts and notify user if needed
        alert_level = reading_item['alert_level']
        if alert_level in ['warning', 'critical']:
            print(f"⚠️  Alert detected: {alert_level} for user {user_id}")
            # TODO: Trigger SNS notification to user
        
        # 7️⃣ Calculate WQI for security audit log
        wqi = calculate_wqi(reading)
        anomaly_type = map_alert_to_anomaly(alert_level, reading)
        
        # 8️⃣ Log to security audit trail
        try:
            audit_logger.log_reading_processed(
                device_id=device_id,
                wqi=wqi,
                anomaly_type=anomaly_type,
                timestamp=timestamp,
                user_id=user_id,
                readings=reading
            )
        except Exception as audit_error:
            print(f"⚠️  Security audit logging failed: {audit_error}")
            # Don't fail the main process
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Reading processed successfully',
                'user_id': user_id,
                'device_id': device_id,
                'timestamp': timestamp,
                'alert_level': alert_level,
                'wqi': wqi
            })
        }
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def calculate_wqi(reading: Dict[str, Any]) -> float:
    """
    Calculate Water Quality Index from sensor readings
    Simplified calculation for audit logging
    """
    pH = reading['pH']
    turbidity = reading['turbidity']
    tds = reading['tds']
    
    # Simple WQI calculation (0-100 scale)
    # Ideal values: pH 7.0, turbidity 0, TDS 100
    pH_score = max(0, 100 - abs(pH - 7.0) * 20)
    turbidity_score = max(0, 100 - turbidity * 10)
    tds_score = max(0, 100 - abs(tds - 100) / 5)
    
    wqi = (pH_score + turbidity_score + tds_score) / 3
    return round(wqi, 1)


def map_alert_to_anomaly(alert_level: str, reading: Dict[str, Any]) -> str:
    """
    Map alert level to anomaly type for security audit
    """
    if alert_level == 'critical':
        # Determine specific anomaly type
        if reading['turbidity'] > 5:
            return 'contamination'
        elif reading['pH'] < 6.0 or reading['pH'] > 8.5:
            return 'contamination'
        else:
            return 'sensor_fault'
    elif alert_level == 'warning':
        return 'calibration_needed'
    else:
        return 'normal'
