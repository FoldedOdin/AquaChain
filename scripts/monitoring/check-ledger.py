#!/usr/bin/env python3
"""
Check if readings are in the immutable ledger
"""

import boto3
from datetime import datetime, timezone

def check_ledger():
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    print("=" * 60)
    print("Checking Ledger for IoT Readings")
    print("=" * 60)
    print()
    
    try:
        # Scan for recent ledger entries (limited scan)
        response = dynamodb.scan(
            TableName='aquachain-ledger',
            Limit=20,
            FilterExpression='contains(#data, :device)',
            ExpressionAttributeNames={'#data': 'data'},
            ExpressionAttributeValues={':device': {'S': 'ESP32-001'}}
        )
        
        if not response['Items']:
            print("❌ No ledger entries found for ESP32-001")
            print()
            print("This means:")
            print("- Lambda is writing to AquaChain-Readings")
            print("- But NOT writing to the immutable ledger")
            print("- Audit trail is incomplete")
            return False
        
        print(f"✓ Found {len(response['Items'])} ledger entry/entries")
        print()
        
        for i, item in enumerate(response['Items'][:5], 1):
            print(f"Ledger Entry {i}:")
            print(f"  Partition Key: {item.get('partition_key', {}).get('S', 'N/A')}")
            print(f"  Sequence Number: {item.get('sequenceNumber', {}).get('N', 'N/A')}")
            print(f"  Timestamp: {item.get('timestamp', {}).get('S', 'N/A')}")
            
            # Check if it's a reading entry
            data = item.get('data', {}).get('S', '')
            if 'ESP32-001' in data:
                print(f"  Type: IoT Reading")
                if 'pH' in data:
                    print(f"  Contains: Sensor data")
            
            print()
        
        print("=" * 60)
        print("✓ SUCCESS - Readings are in immutable ledger!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_ledger()
    exit(0 if success else 1)
