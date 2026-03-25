#!/usr/bin/env python3
"""Fix missing CORS OPTIONS integration responses for notification endpoints."""
import boto3

apigw = boto3.client('apigateway', region_name='ap-south-1')
API_ID = 'vtqjfznspc'
STAGE = 'dev'

# Resource IDs for notification routes that have OPTIONS methods
resources_to_fix = {
    'mkyiy6': '/api/notifications',
    'slu0we': '/api/notifications/{notificationId}',
    'rrorwy': '/api/notifications/read-all',
    'kf3m09': '/api/notifications/{notificationId}/read',
}

allow_headers = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
allow_methods = "'GET,POST,PUT,DELETE,OPTIONS'"
allow_origin = "'*'"

for resource_id, path in resources_to_fix.items():
    print(f'Fixing {path} ({resource_id})...')

    # Ensure method response exists
    try:
        apigw.put_method_response(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False,
            }
        )
        print('  method response created')
    except Exception as e:
        print(f'  method response: {e}')

    # Set integration response with actual CORS values
    try:
        apigw.update_integration_response(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            patchOperations=[
                {'op': 'replace', 'path': '/responseParameters/method.response.header.Access-Control-Allow-Headers', 'value': allow_headers},
                {'op': 'replace', 'path': '/responseParameters/method.response.header.Access-Control-Allow-Methods', 'value': allow_methods},
                {'op': 'replace', 'path': '/responseParameters/method.response.header.Access-Control-Allow-Origin', 'value': allow_origin},
            ]
        )
        print('  integration response updated OK')
    except Exception as e:
        print(f'  integration response error: {e}')

print('\nDeploying stage...')
apigw.create_deployment(
    restApiId=API_ID,
    stageName=STAGE,
    description='Fix notification CORS OPTIONS responses'
)
print('Done - notification CORS fixed')
