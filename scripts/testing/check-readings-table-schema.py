#!/usr/bin/env python3
"""
Check the actual schema of the readings table
"""

import boto3
import json
from datetime import datetime

def check_table_schema():
    """Check the readings table schema"""
    
    dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
    
    table_name = 'AquaChain-Readings'
    
    try:
        response = dynamodb.describe_table(TableName=table_name)
        table_info = response['Table']
        
        print(f"📋 Table: {table_name}")
        print(f"Status: {table_info['TableStatus']}")
        
        # Key schema
        print("\n🔑 Key Schema:")
        for key in table_info['KeySchema']:
            print(f"  {key['AttributeName']}: {key['KeyType']}")
        
        # Attribute definitions
        print("\n📝 Attributes:")
        for attr in table_info['AttributeDefinitions']:
            print(f"  {attr['AttributeName']}: {attr['AttributeType']}")
        
        # Global Secondary Indexes
        if 'GlobalSecondaryIndexes' in table_info:
            print("\n🔍 Global Secondary Indexes:")
            for gsi in table_info['GlobalSecondaryIndexes']:
                print(f"  {gsi['IndexName']}:")
                for key in gsi['KeySchema']:
                    print(f"    {key['AttributeName']}: {key['KeyType']}")
        
        return table_info
        
    except Exception as e:
        print(f"❌ Error describing table: {e}")
        return None

def test_correct_query():
    """Test the correct way to query the readings table"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('AquaChain-Readings')
    
    device_id = "ESP32-001"
    
    # Generate the correct partition key (deviceId_month)
    current_month = datetime.utcnow().strftime('%Y-%m')
    device_month = f"{device_id}_{current_month}"
    
    print(f"\n🧪 Testing query with deviceId_month: {device_month}")
    
    try:
        response = table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': device_month
            },
            ScanIndexForward=False,  # Most recent first
            Limit=5
        )
        
        readings = response.get('Items', [])
        print(f"✅ Found {len(readings)} readings for current month")
        
        if readings:
            print(f"Latest reading: {readings[0]}")
        
        return readings
        
    except Exception as e:
        print(f"❌ Error querying with correct key: {e}")
        return []

def scan_for_any_data():
    """Scan the table to see if there's any data at all"""
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('AquaChain-Readings')
    
    print(f"\n🔍 Scanning table for any data...")
    
    try:
        response = table.scan(Limit=10)
        items = response.get('Items', [])
        
        print(f"Found {len(items)} items in table")
        
        if items:
            print("Sample items:")
            for i, item in enumerate(items[:3]):
                print(f"  {i+1}. {item}")
        
        return items
        
    except Exception as e:
        print(f"❌ Error scanning table: {e}")
        return []

def main():
    """Main function"""
    
    print("🔍 Checking Readings Table Schema")
    print("=" * 40)
    
    # Check table schema
    schema = check_table_schema()
    
    # Test correct query
    readings = test_correct_query()
    
    # If no readings in current month, scan for any data
    if not readings:
        scan_for_any_data()

if __name__ == "__main__":
    main()