#!/usr/bin/env python3
"""Check latest readings from DynamoDB"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('AquaChain-Readings')

# Query latest readings for ESP32-001
response = table.query(
    KeyConditionExpression='deviceId_month = :dm',
    ExpressionAttributeValues={
        ':dm': 'ESP32-001_2026-03'
    },
    ScanIndexForward=False,  # Descending order (latest first)
    Limit=10
)

print("="*80)
print("Latest 10 Readings from ESP32-001")
print("="*80)
print()

if response['Items']:
    for item in response['Items']:
        print(f"Timestamp: {item['timestamp']}")
        print(f"  pH: {item['pH']}, Turbidity: {item['turbidity']}, TDS: {item['tds']}, Temp: {item['temperature']}")
        print(f"  WQI: {item['qualityScore']}, Status: {item['qualityStatus']}")
        print()
    
    print(f"Total readings found: {response['Count']}")
else:
    print("No readings found")
