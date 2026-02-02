"""
Lambda function to add a demo device for consumers
Provides sample water quality data for dashboard demonstration
"""
import sys
import os
import json
import boto3
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
READINGS_TABLE = os.environ.get('READINGS_TABLE', 'AquaChain-Readings')

# Initialize logger
logger = get_logger(__name__, service='add-demo-device')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def handler(event, context):
    """
    Add a demo device with sample water quality data
    
    This creates a demonstration device that:
    - Has realistic water quality parameters
    - Generates sample historical data
    - Is clearly marked as a demo device
    - Can be easily removed by the user
    
    Returns:
    {
      "success": true,
      "device": {...},
      "message": "Demo device added successfully"
    }
    """
    request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
    
    try:
        # Extract user ID from authorizer context
        user_id = extract_user_id(event)
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

        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        logger.info(
            "Adding demo device",
            request_id=request_id,
            user_id=user_id
        )

        # Create demo device
        demo_device = create_demo_device(user_id, body)
        
        # Save device to DynamoDB
        save_demo_device(demo_device)
        
        # Generate sample readings
        generate_sample_readings(demo_device['device_id'])
        
        logger.info(
            "Demo device added successfully",
            request_id=request_id,
            device_id=demo_device['device_id']
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'device': demo_device,
                'message': 'Demo device added successfully'
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(
            f"Error adding demo device: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__
        )
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Failed to add demo device'
            })
        }


def extract_user_id(event):
    """Extract user ID from request context"""
    try:
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub', '')
    except Exception:
        return ''


def create_demo_device(user_id, request_data):
    """Create demo device data structure"""
    now = datetime.utcnow()
    device_id = request_data.get('device_id') or f"demo_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}"
    
    return {
        'device_id': device_id,
        'user_id': user_id,
        'name': request_data.get('name', 'Demo Water Monitor'),
        'location': request_data.get('location', 'Kitchen Sink - Demo Location'),
        'status': 'active',
        'type': 'ESP32-WQ-Monitor-Demo',
        'installation_date': now.isoformat(),
        'last_reading': now.isoformat(),
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'metadata': {
            'isDemo': True,
            'description': 'Demonstration device with simulated water quality data',
            'firmware_version': 'demo-v1.0.0',
            'hardware_version': 'demo-hw-v1.0'
        },
        'settings': {
            'reading_interval': 300,  # 5 minutes
            'alert_thresholds': {
                'pH_min': Decimal('6.5'),
                'pH_max': Decimal('8.5'),
                'turbidity_max': Decimal('5.0'),
                'tds_max': Decimal('500'),
                'temperature_min': Decimal('15'),
                'temperature_max': Decimal('25')
            }
        },
        'current_reading': {
            'pH': Decimal(str(request_data.get('readings', {}).get('pH', 7.2))),
            'turbidity': Decimal(str(request_data.get('readings', {}).get('turbidity', 2.1))),
            'tds': Decimal(str(request_data.get('readings', {}).get('tds', 145))),
            'temperature': Decimal(str(request_data.get('readings', {}).get('temperature', 22.5))),
            'timestamp': now.isoformat()
        }
    }


def save_demo_device(device):
    """Save demo device to DynamoDB"""
    devices_table = dynamodb.Table(DEVICES_TABLE)
    
    try:
        devices_table.put_item(Item=device)
        logger.info(f"Demo device saved: {device['device_id']}")
    except Exception as e:
        logger.error(f"Error saving demo device: {str(e)}")
        raise


def generate_sample_readings(device_id):
    """Generate sample historical readings for the demo device"""
    readings_table = dynamodb.Table(READINGS_TABLE)
    
    try:
        now = datetime.utcnow()
        readings = []
        
        # Generate 7 days of sample data (every 30 minutes)
        for i in range(7 * 24 * 2):  # 7 days * 24 hours * 2 (30-min intervals)
            timestamp = now - timedelta(minutes=30 * i)
            
            # Generate realistic water quality variations
            base_ph = 7.2
            base_turbidity = 2.1
            base_tds = 145
            base_temp = 22.5
            
            # Add some realistic variation
            import random
            ph_variation = random.uniform(-0.3, 0.3)
            turbidity_variation = random.uniform(-0.5, 0.8)
            tds_variation = random.uniform(-20, 30)
            temp_variation = random.uniform(-2, 3)
            
            reading = {
                'device_id': device_id,
                'timestamp': timestamp.isoformat(),
                'pH': Decimal(str(round(base_ph + ph_variation, 2))),
                'turbidity': Decimal(str(round(max(0, base_turbidity + turbidity_variation), 2))),
                'tds': Decimal(str(round(max(0, base_tds + tds_variation), 1))),
                'temperature': Decimal(str(round(base_temp + temp_variation, 1))),
                'created_at': timestamp.isoformat(),
                'reading_type': 'demo'
            }
            
            readings.append(reading)
            
            # Batch write every 25 items (DynamoDB limit)
            if len(readings) >= 25:
                batch_write_readings(readings_table, readings)
                readings = []
        
        # Write remaining readings
        if readings:
            batch_write_readings(readings_table, readings)
            
        logger.info(f"Generated sample readings for demo device: {device_id}")
        
    except Exception as e:
        logger.error(f"Error generating sample readings: {str(e)}")
        # Don't raise - device creation should succeed even if readings fail


def batch_write_readings(table, readings):
    """Batch write readings to DynamoDB"""
    try:
        with table.batch_writer() as batch:
            for reading in readings:
                batch.put_item(Item=reading)
    except Exception as e:
        logger.error(f"Error batch writing readings: {str(e)}")
        # Continue processing - some readings are better than none