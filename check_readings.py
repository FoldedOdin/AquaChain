#!/usr/bin/env python3
"""
Check if there are readings in DynamoDB and test the readings API
"""

import boto3
from datetime import datetime, timedelta
import json

def check_dynamodb_readings():
    """Check DynamoDB for readings"""
    print("=" * 60)
    print("CHECKING DYNAMODB FOR READINGS")
    print("=" * 60)
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('AquaChain-Readings')
    
    now = datetime.utcnow()
    device_id = 'ESP32-001'
    
    # Check current month
    current_month = now.strftime('%Y-%m')
    device_month = f"{device_id}_{current_month}"
    
    print(f"\n1. Checking partition: {device_month}")
    try:
        response = table.query(
            KeyConditionExpression='deviceId_month = :dm',
            ExpressionAttributeValues={':dm': device_month},
            Limit=10,
            ScanIndexForward=False  # Latest first
        )
        
        items = response.get('Items', [])
        print(f"   Found {len(items)} readings in current month")
        
        if items:
            print("\n   Latest readings:")
            for i, item in enumerate(items[:5], 1):
                timestamp = item.get('timestamp', 'N/A')
                pH = item.get('pH', 'N/A')
                wqi = item.get('wqi', item.get('qualityScore', 'N/A'))
                quality = item.get('quality', item.get('qualityStatus', 'N/A'))
                print(f"   {i}. {timestamp}")
                print(f"      pH: {pH}, WQI: {wqi}, Quality: {quality}")
        else:
            print("   ⚠️  No readings found in current month")
            
    except Exception as e:
        print(f"   ❌ Error querying current month: {e}")
    
    # Check previous month
    prev_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    device_month_prev = f"{device_id}_{prev_month}"
    
    print(f"\n2. Checking partition: {device_month_prev}")
    try:
        response = table.query(
            KeyConditionExpression='deviceId_month = :dm',
            ExpressionAttributeValues={':dm': device_month_prev},
            Limit=5,
            ScanIndexForward=False
        )
        
        items = response.get('Items', [])
        print(f"   Found {len(items)} readings in previous month")
        
    except Exception as e:
        print(f"   ❌ Error querying previous month: {e}")
    
    # Try legacy format with # separator
    device_month_legacy = f"{device_id}#{current_month}"
    print(f"\n3. Checking legacy partition: {device_month_legacy}")
    try:
        response = table.query(
            KeyConditionExpression='deviceId_month = :dm',
            ExpressionAttributeValues={':dm': device_month_legacy},
            Limit=5,
            ScanIndexForward=False
        )
        
        items = response.get('Items', [])
        print(f"   Found {len(items)} readings in legacy format")
        
    except Exception as e:
        print(f"   ❌ Error querying legacy format: {e}")
    
    # Scan for any readings (expensive, but useful for debugging)
    print(f"\n4. Scanning for ANY readings with deviceId={device_id}")
    try:
        response = table.scan(
            FilterExpression='begins_with(deviceId_month, :device_id)',
            ExpressionAttributeValues={':device_id': device_id},
            Limit=10
        )
        
        items = response.get('Items', [])
        print(f"   Found {len(items)} readings total (scan)")
        
        if items:
            print("\n   Sample partition keys found:")
            partitions = set(item.get('deviceId_month', 'N/A') for item in items)
            for partition in sorted(partitions):
                print(f"   - {partition}")
        
    except Exception as e:
        print(f"   ❌ Error scanning: {e}")

def test_readings_api():
    """Test the readings API endpoint"""
    print("\n" + "=" * 60)
    print("TESTING READINGS API ENDPOINT")
    print("=" * 60)
    
    import requests
    
    # Get auth token
    token = None
    try:
        with open('auth_token.txt', 'r') as f:
            token = f.read().strip()
        print(f"\n✓ Found auth token: {token[:20]}...")
    except:
        print("\n⚠️  No auth token found (auth_token.txt)")
        print("   Attempting without authentication...")
    
    # Test endpoints
    base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
    device_id = "ESP32-001"
    
    endpoints = [
        f"/api/v1/readings/{device_id}/latest",
        f"/api/v1/readings/{device_id}/history?days=7",
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n📡 Testing: {endpoint}")
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Success!")
                
                if 'reading' in data:
                    reading = data['reading']
                    print(f"   Latest reading:")
                    print(f"     Timestamp: {reading.get('timestamp', 'N/A')}")
                    print(f"     pH: {reading.get('pH', 'N/A')}")
                    print(f"     WQI: {reading.get('wqi', 'N/A')}")
                
                if 'readings' in data:
                    readings = data['readings']
                    print(f"   Found {len(readings)} readings")
                    if readings:
                        print(f"   Latest: {readings[0].get('timestamp', 'N/A')}")
                        print(f"   Oldest: {readings[-1].get('timestamp', 'N/A')}")
            
            elif response.status_code == 404:
                print(f"   ⚠️  404: No readings found")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown')}")
                except:
                    pass
            
            elif response.status_code == 401:
                print(f"   ❌ 401: Authentication required")
            
            elif response.status_code == 403:
                print(f"   ❌ 403: Access denied")
            
            else:
                print(f"   ❌ Error: {response.text[:200]}")
        
        except Exception as e:
            print(f"   ❌ Request failed: {e}")

if __name__ == '__main__':
    check_dynamodb_readings()
    test_readings_api()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
