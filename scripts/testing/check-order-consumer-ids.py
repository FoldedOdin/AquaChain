#!/usr/bin/env python3
"""
Check what consumer IDs exist in orders
"""

import boto3
import json

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
orders_table = dynamodb.Table('aquachain-orders')

def check_consumer_ids():
    """Check what consumer IDs exist in orders"""
    try:
        response = orders_table.scan()
        orders = response.get('Items', [])
        
        print(f"🔍 Found {len(orders)} total orders")
        
        consumer_ids = set()
        for order in orders:
            consumer_id = order.get('consumerId') or order.get('userId')
            if consumer_id:
                consumer_ids.add(consumer_id)
            
            print(f"📋 Order {order.get('orderId')}:")
            print(f"   consumerId: {order.get('consumerId', 'N/A')}")
            print(f"   userId: {order.get('userId', 'N/A')}")
            print(f"   status: {order.get('status', 'N/A')}")
            print(f"   assignedTechnician: {order.get('assignedTechnician', 'N/A')}")
            print()
        
        print(f"🎯 Unique Consumer IDs found: {list(consumer_ids)}")
        
        return list(consumer_ids)
        
    except Exception as e:
        print(f"❌ Error checking consumer IDs: {e}")
        return []

def main():
    """Main execution"""
    print("🚀 Checking consumer IDs in orders...")
    consumer_ids = check_consumer_ids()
    
    if consumer_ids:
        print(f"\n✅ Found consumer IDs: {consumer_ids}")
        print(f"Use one of these IDs to test the API")
    else:
        print(f"\n⚠️  No consumer IDs found in orders")

if __name__ == "__main__":
    main()