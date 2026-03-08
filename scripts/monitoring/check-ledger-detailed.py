#!/usr/bin/env python3
"""
Check ledger entries with full details
"""

import boto3
import json
from datetime import datetime

def check_ledger_detailed():
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    print("=" * 60)
    print("Checking Ledger Entries (Detailed)")
    print("=" * 60)
    print()
    
    try:
        # Scan for recent ledger entries
        response = dynamodb.scan(
            TableName='aquachain-ledger',
            Limit=5
        )
        
        if not response['Items']:
            print("❌ No ledger entries found")
            return False
        
        print(f"✓ Found {len(response['Items'])} ledger entries")
        print()
        
        for i, item in enumerate(response['Items'], 1):
            print(f"Ledger Entry {i}:")
            print(f"  Partition Key: {item.get('partition_key', {}).get('S', 'N/A')}")
            print(f"  Sequence Number: {item.get('sequenceNumber', {}).get('N', 'N/A')}")
            print(f"  Device ID: {item.get('deviceId', {}).get('S', 'N/A')}")
            print(f"  Timestamp: {item.get('timestamp', {}).get('S', 'N/A')}")
            print(f"  Event Type: {item.get('event_type', {}).get('S', 'N/A')}")
            
            # Parse and display data field
            data_str = item.get('data', {}).get('S', '')
            if data_str:
                try:
                    data = json.loads(data_str)
                    print(f"  Data:")
                    print(f"    Device: {data.get('deviceId', 'N/A')}")
                    print(f"    WQI: {data.get('wqi', 'N/A')}")
                    print(f"    Anomaly Type: {data.get('anomalyType', 'N/A')}")
                    readings = data.get('readings', {})
                    if readings:
                        print(f"    Readings:")
                        print(f"      pH: {readings.get('pH', 'N/A')}")
                        print(f"      Turbidity: {readings.get('turbidity', 'N/A')}")
                        print(f"      TDS: {readings.get('tds', 'N/A')}")
                        print(f"      Temperature: {readings.get('temperature', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"  Data (raw): {data_str[:100]}...")
            
            print()
        
        print("=" * 60)
        print("✓ SUCCESS - Ledger is working correctly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_ledger_detailed()
    exit(0 if success else 1)
