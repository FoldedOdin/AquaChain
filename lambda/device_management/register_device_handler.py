"""
Device Registration Lambda Handler
Handles registration of new IoT devices for users
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
iot_client = boto3.client('iot')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
IOT_POLICY_NAME = os.environ.get('IOT_POLICY_NAME', 'AquaChainDevicePolicy')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Register a new IoT device for a user
    
    Expected event body:
    {
        "device_id": "ESP32-ABC123",
        "name": "Kitchen Filter",
        "location": "Kitchen Tap",
        "water_source_type": "household",
        "pairing_code": "F9G7A3" (optional)
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get user ID from authorizer context
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Unauthorized - User ID not found'
                })
            }
        
        # Validate required fields
        device_id = body.get('device_id')
        if not device_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Device ID is required'
                })
            }
        
        # Extract device information
        device_name = body.get('name', f'Device {device_id}')
        location = body.get('location', 'Not specified')
        water_source_type = body.get('water_source_type', 'household')
        pairing_code = body.get('pairing_code')
        
        # Check if device already exists
        devices_table = dynamodb.Table(DEVICES_TABLE)
        existing_device = devices_table.get_item(
            Key={'device_id': device_id}
        ).get('Item')
        
        if existing_device:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Device with this ID already exists'
                })
            }
        
        # Create IoT Thing
        iot_thing_name = f'aquachain-{device_id}'
        try:
            iot_client.create_thing(
                thingName=iot_thing_name,
                attributePayload={
                    'attributes': {
                        'device_id': device_id,
                        'user_id': user_id,
                        'location': location,
                        'water_source_type': water_source_type
                    }
                }
            )
            logger.info(f'Created IoT Thing: {iot_thing_name}')
        except iot_client.exceptions.ResourceAlreadyExistsException:
            logger.warning(f'IoT Thing already exists: {iot_thing_name}')
        except Exception as e:
            logger.error(f'Error creating IoT Thing: {str(e)}')
            # Continue anyway - device can be registered without IoT Thing
        
        # Create device certificate (optional - can be done later)
        certificate_arn = None
        certificate_pem = None
        private_key = None
        
        try:
            cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
            certificate_arn = cert_response['certificateArn']
            certificate_pem = cert_response['certificatePem']
            private_key = cert_response['keyPair']['PrivateKey']
            
            # Attach policy to certificate
            iot_client.attach_policy(
                policyName=IOT_POLICY_NAME,
                target=certificate_arn
            )
            
            # Attach certificate to thing
            iot_client.attach_thing_principal(
                thingName=iot_thing_name,
                principal=certificate_arn
            )
            
            logger.info(f'Created and attached certificate for device: {device_id}')
        except Exception as e:
            logger.error(f'Error creating certificate: {str(e)}')
            # Continue anyway - certificate can be created later
        
        # Store device in DynamoDB
        timestamp = datetime.utcnow().isoformat()
        device_item = {
            'device_id': device_id,
            'user_id': user_id,
            'name': device_name,
            'location': location,
            'water_source_type': water_source_type,
            'status': 'active',
            'created_at': timestamp,
            'updated_at': timestamp,
            'iot_thing_name': iot_thing_name,
            'certificate_arn': certificate_arn,
            'pairing_code': pairing_code
        }
        
        devices_table.put_item(Item=device_item)
        logger.info(f'Device registered successfully: {device_id}')
        
        # Prepare response (don't include private key in regular response)
        response_device = {
            'device_id': device_id,
            'user_id': user_id,
            'name': device_name,
            'location': location,
            'water_source_type': water_source_type,
            'status': 'active',
            'created_at': timestamp,
            'iot_thing_name': iot_thing_name,
            'certificate_arn': certificate_arn
        }
        
        # If certificate was created, include it in response for device provisioning
        if certificate_pem and private_key:
            response_device['provisioning'] = {
                'certificate_pem': certificate_pem,
                'private_key': private_key,
                'iot_endpoint': iot_client.describe_endpoint(endpointType='iot:Data-ATS')['endpointAddress']
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Device registered successfully',
                'device': response_device
            })
        }
        
    except json.JSONDecodeError:
        logger.error('Invalid JSON in request body')
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f'Error registering device: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'message': str(e) if os.environ.get('DEBUG') else 'Failed to register device'
            })
        }
