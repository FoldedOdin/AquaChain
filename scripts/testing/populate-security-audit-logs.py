"""
Populate Security Audit Logs with realistic test data
"""

import boto3
import hashlib
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
REGION = 'us-east-1'
ENVIRONMENT = 'dev'
TABLE_NAME = f'AquaChain-SecurityAuditLogs-{ENVIRONMENT}'

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# Test data configuration
DEVICE_IDS = ['DEV-3421', 'DEV-3422', 'DEV-3423', 'DEV-3424', 'DEV-3425']
ANOMALY_TYPES = ['normal', 'contamination', 'sensor_fault', 'calibration_needed']
WQI_RANGES = {
    'normal': (70, 100),
    'contamination': (40, 75),
    'sensor_fault': (85, 100),
    'calibration_needed': (60, 85)
}


def generate_data_hash(device_id: str, timestamp: str, wqi: float) -> str:
    """
    Generate a realistic data hash
    """
    data = f"{device_id}:{timestamp}:{wqi}"
    hash_obj = hashlib.sha256(data.encode())
    return f"hash-{hash_obj.hexdigest()[:8]}"


def generate_log_entry(timestamp: datetime, device_id: str) -> dict:
    """
    Generate a single audit log entry
    """
    anomaly_type = random.choice(ANOMALY_TYPES)
    wqi_min, wqi_max = WQI_RANGES[anomaly_type]
    wqi = round(random.uniform(wqi_min, wqi_max), 1)
    
    timestamp_str = timestamp.strftime('%d/%m/%Y, %I:%M:%S %p')
    log_id = f"log-{timestamp.strftime('%Y%m%d%H%M%S')}-{device_id}"
    
    return {
        'logId': log_id,
        'timestamp': timestamp_str,
        'deviceId': device_id,
        'wqi': Decimal(str(wqi)),
        'anomalyType': anomaly_type,
        'verified': True,
        'dataHash': generate_data_hash(device_id, timestamp_str, wqi),
        'ttl': int((timestamp + timedelta(days=30)).timestamp())
    }


def populate_logs(num_logs: int = 100):
    """
    Populate the table with test data
    """
    print(f"Populating {TABLE_NAME} with {num_logs} log entries...")
    
    # Generate logs for the past 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    time_increment = (end_time - start_time) / num_logs
    
    with table.batch_writer() as batch:
        for i in range(num_logs):
            timestamp = start_time + (time_increment * i)
            device_id = random.choice(DEVICE_IDS)
            
            log_entry = generate_log_entry(timestamp, device_id)
            
            try:
                batch.put_item(Item=log_entry)
                if (i + 1) % 10 == 0:
                    print(f"  Inserted {i + 1}/{num_logs} entries...")
            except Exception as e:
                print(f"  Error inserting entry {i + 1}: {str(e)}")
    
    print(f"✓ Successfully populated {num_logs} log entries")
    
    # Verify insertion
    response = table.scan(Select='COUNT')
    print(f"✓ Total records in table: {response['Count']}")


def populate_integrity_hashes():
    """
    Populate integrity hashes table with verification records
    """
    integrity_table_name = f'AquaChain-IntegrityHashes-{ENVIRONMENT}'
    integrity_table = dynamodb.Table(integrity_table_name)
    
    print(f"\nPopulating {integrity_table_name} with verification records...")
    
    # Generate verification records for the past 7 days
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        record = {
            'date': date,
            'verified': True,
            'recordCount': random.randint(50, 150),
            'dailyRootHash': hashlib.sha256(date.encode()).hexdigest()[:16]
        }
        
        try:
            integrity_table.put_item(Item=record)
            print(f"  Inserted verification record for {date}")
        except Exception as e:
            print(f"  Error inserting record for {date}: {str(e)}")
    
    print(f"✓ Successfully populated integrity verification records")


if __name__ == '__main__':
    try:
        # Populate audit logs
        populate_logs(num_logs=100)
        
        # Populate integrity hashes
        populate_integrity_hashes()
        
        print("\n✓ All test data populated successfully!")
        print(f"\nYou can now view the data in the admin dashboard:")
        print(f"  - Security Audit Logs: /admin/security/audit")
        print(f"  - Integrity Status: /admin/security/integrity")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nMake sure:")
        print("  1. The DynamoDB tables exist")
        print("  2. You have AWS credentials configured")
        print("  3. You have permissions to write to DynamoDB")
