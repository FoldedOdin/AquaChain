#!/usr/bin/env python3
"""
Test script to broadcast a message to WebSocket connections
"""

import json
import boto3

lambda_client = boto3.client('lambda', region_name='ap-south-1')

# Test payload
payload = {
    'topic': 'admin-dashboard',
    'message': {
        'type': 'metrics_update',
        'systemMetrics': {
            'activeDevices': 42,
            'activeAlerts': 3,
            'systemAvailability': 99.8
        },
        'realTimeMetrics': {
            'totalUsers': 150,
            'apiSuccessRate': 99.5,
            'systemUptime': 99.9,
            'uptimeStatus': 'Operational'
        },
        'timestamp': '2026-02-25T09:50:00Z'
    },
    'domainName': 'nnznduptme.execute-api.ap-south-1.amazonaws.com',
    'stage': 'dev'
}

print('Broadcasting test message to admin-dashboard topic...')
print(f'Payload: {json.dumps(payload, indent=2)}')

response = lambda_client.invoke(
    FunctionName='aquachain-websocket-broadcast-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
print(f'\nResponse: {json.dumps(result, indent=2)}')
