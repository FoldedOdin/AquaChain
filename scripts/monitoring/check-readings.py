#!/usr/bin/env python3
"""
Check if ESP32 readings are in DynamoDB
"""

import boto3
import json
from datetime import datetime, timezone

def check_readings():
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    print("=" * 60)
    print("Checking DynamoDB for ESP32-001 Readings")
    print("=" * 60)
    print()
    
    # Generate deviceId_month for current month
    now = datetime.now(timezone.utc)
    device_id_month = f"ESP32-001_{now.strftime('%Y-%m')}"
    
    print(f"Querying for: {device_id_month}")
    print()
    
    try:
        # Query for most recent readings
        response = dynamodb.query(
            TableName='AquaChain-Readings',
            KeyConditionExpression='deviceId_month = :dim',
            ExpressionAttributeValues={':dim': {'S': device_id_month}},
            Limit=10,  # Get more readings to see the count
            ScanIndexForward=False
        )
        
        if not response['Items']:
            print("❌ No readings found for ESP32-001")
            print()
            print("Possible issues:")
            print("- IoT Rule not triggering")
            print("- Lambda function not writing to DynamoDB")
            print("- Device ID mismatch")
            return False
        
        print(f"✓ Found {len(response['Items'])} reading(s)")
        
        # Count total readings
        count_response = dynamodb.query(
            TableName='AquaChain-Readings',
            KeyConditionExpression='deviceId_month = :dim',
            ExpressionAttributeValues={':dim': {'S': device_id_month}},
            Select='COUNT'
        )
        
        total_count = count_response.get('Count', 0)
        print(f"✓ Total readings this month: {total_count}")
        print()
        
        for i, item in enumerate(response['Items'], 1):
            print(f"Reading {i}:")
            print(f"  Device ID: {item.get('deviceId', {}).get('S', 'N/A')}")
            print(f"  Timestamp: {item.get('timestamp', {}).get('S', 'N/A')}")
            
            # Get readings
            readings = item.get('readings', {}).get('M', {})
            if readings:
                print(f"  pH: {readings.get('pH', {}).get('N', 'N/A')}")
                print(f"  Temperature: {readings.get('temperature', {}).get('N', 'N/A')}°C")
                print(f"  TDS: {readings.get('tds', {}).get('N', 'N/A')} ppm")
                print(f"  Turbidity: {readings.get('turbidity', {}).get('N', 'N/A')} NTU")
            
            # Get diagnostics
            diagnostics = item.get('diagnostics', {}).get('M', {})
            if diagnostics:
                signal = diagnostics.get('signalStrength', {}).get('N', 'N/A')
                print(f"  WiFi Signal: {signal} dBm")
            
            print()
        
        print("=" * 60)
        print("✓ SUCCESS - Data is flowing to DynamoDB!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_readings()
    exit(0 if success else 1)
