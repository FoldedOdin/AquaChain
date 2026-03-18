#!/usr/bin/env python3
"""Remove mock/test orders from the orders table"""
import boto3

REGION = 'ap-south-1'
ORDERS_TABLE = 'aquachain-orders'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(ORDERS_TABLE)

# Scan all orders and identify mock ones
response = table.scan()
orders = response.get('Items', [])

mock_orders = []
for o in orders:
    consumer_id = o.get('consumerId') or o.get('userId', '')
    # Mock orders use test-consumer-123 as the consumer ID
    if consumer_id == 'test-consumer-123':
        mock_orders.append(o)

print(f"Found {len(mock_orders)} mock order(s) to remove:")
for o in mock_orders:
    print(f"  orderId: {o['orderId']} | status: {o.get('status')} | consumerId: {o.get('consumerId') or o.get('userId')}")

if not mock_orders:
    print("Nothing to delete.")
else:
    confirm = input("\nDelete these? (yes/no): ").strip().lower()
    if confirm == 'yes':
        for o in mock_orders:
            table.delete_item(Key={'orderId': o['orderId']})
            print(f"  Deleted: {o['orderId']}")
        print("Done.")
    else:
        print("Aborted.")
