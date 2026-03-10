#!/usr/bin/env python3
"""
Test Alert Generation by inserting critical water quality readings
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal

def insert_test_reading(reading_type='critical'):
    """Insert test reading into DynamoDB to trigger alert"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('AquaChain-Readings')
    
    print(f"Testing Alert Generation - {reading_type.upper()} Reading")
    print("=" * 60)
    
    # Define test readings
    test_readings = {
        'critical': {
            'wqi': Decimal('45.0'),  # Below 50 threshold
            'anomalyType': 'contamination',
            'readings': {
                'pH': Decimal('6.0'),  # Below 6.5 threshold
                'turbidity': Decimal('28.5'),  # Above 25 threshold
                'tds': Decimal('1050'),  # Above 1000 threshold
                'temperature': Decimal('24.5')
            },
            'description': 'Critical water quality - multiple violations'
        },
        'warning': {
            'wqi': Decimal('65.0'),  # Below 70 threshold
            'anomalyType': 'sensor_fault',
            'readings': {
                'pH': Decimal('6.7'),  # Below 6.8 threshold
                'turbidity': Decimal('12.0'),  # Above 10 threshold
                'tds': Decimal('650'),  # Above 600 threshold
                'temperature': Decimal('25.0')
            },
            'description': 'Warning - moderate water quality issues'
        },
        'safe': {
            'wqi': Decimal('85.0'),  # Above 70 threshold
            'anomalyType': 'normal',
            'readings': {
                'pH': Decimal('7.2'),
                'turbidity': Decimal('3.5'),
                'tds': Decimal('450'),
                'temperature': Decimal('24.0')
            },
            'description': 'Safe - all parameters within normal range'
        }
    }
    
    reading_data = test_readings.get(reading_type, test_readings['critical'])
    
    # Create test reading
    timestamp = datetime.utcnow().isoformat() + 'Z'
    month = datetime.utcnow().strftime('%Y-%m')
    device_id_month = f"ESP32-001#{month}"
    
    reading = {
        'deviceId_month': device_id_month,  # Composite partition key
        'timestamp': timestamp,
        'deviceId': 'ESP32-001',
        'wqi': reading_data['wqi'],
        'anomalyType': reading_data['anomalyType'],
        'readings': reading_data['readings'],
        'location': {
            'latitude': Decimal('19.0760'),
            'longitude': Decimal('72.8777')
        },
        'userId': 'test-user-123',
        'deviceName': 'Test Kitchen Monitor',
        'waterSourceType': 'household'
    }
    
    print(f"\n1. Inserting {reading_type} test reading...")
    print(f"   Device: {reading['deviceId']}")
    print(f"   WQI: {reading['wqi']}")
    print(f"   pH: {reading['readings']['pH']}")
    print(f"   Turbidity: {reading['readings']['turbidity']} NTU")
    print(f"   TDS: {reading['readings']['tds']} ppm")
    print(f"   Anomaly: {reading['anomalyType']}")
    print(f"   Description: {reading_data['description']}")
    
    try:
        table.put_item(Item=reading)
        print(f"✓ Test reading inserted successfully")
        print(f"  Timestamp: {timestamp}")
        
    except Exception as e:
        print(f"✗ Error inserting reading: {e}")
        return False
    
    print(f"\n2. DynamoDB Stream will trigger Alert Detection Lambda...")
    print(f"   Expected behavior:")
    
    if reading_type == 'critical':
        print(f"   ✓ Critical alert should be generated")
        print(f"   ✓ Alert stored in aquachain-alerts table")
        print(f"   ✓ SNS notification sent to critical alerts topic")
        print(f"   ✓ Notification service invoked")
        print(f"   ✓ Alert reasons:")
        print(f"     - WQI (45.0) below safe threshold (50)")
        print(f"     - pH (6.0) too acidic (below 6.5)")
        print(f"     - High turbidity (28.5 NTU)")
        print(f"     - High dissolved solids (1050 ppm)")
        print(f"     - AI detected contamination")
    
    elif reading_type == 'warning':
        print(f"   ✓ Warning alert should be generated")
        print(f"   ✓ Alert stored in aquachain-alerts table")
        print(f"   ✓ SNS notification sent to warning alerts topic")
        print(f"   ✓ Alert reasons:")
        print(f"     - WQI (65.0) below optimal threshold (70)")
        print(f"     - pH (6.7) slightly acidic (below 6.8)")
        print(f"     - Moderate turbidity (12.0 NTU)")
        print(f"     - Moderate dissolved solids (650 ppm)")
        print(f"     - Sensor fault detected")
    
    else:
        print(f"   ✓ No alert should be generated (safe reading)")
        print(f"   ✓ Reading stored but no notifications sent")
    
    print(f"\n3. Verification steps:")
    print(f"   a) Check CloudWatch logs:")
    print(f"      aws logs tail /aws/lambda/aquachain-function-alert-detection-dev --follow")
    print(f"   ")
    print(f"   b) Check alerts table:")
    print(f"      aws dynamodb scan --table-name aquachain-alerts --region ap-south-1")
    print(f"   ")
    print(f"   c) Check SNS topic (if subscribed):")
    print(f"      Check your email/SMS for alert notification")
    
    print("\n" + "=" * 60)
    print(f"✓ Test reading inserted - Alert system should process it now")
    
    return True

if __name__ == '__main__':
    import sys
    
    reading_type = sys.argv[1] if len(sys.argv) > 1 else 'critical'
    
    if reading_type not in ['critical', 'warning', 'safe']:
        print("Usage: python test-alert-generation.py [critical|warning|safe]")
        sys.exit(1)
    
    success = insert_test_reading(reading_type)
    
    if not success:
        sys.exit(1)
