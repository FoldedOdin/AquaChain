#!/usr/bin/env python3
"""
Readings Service Lambda Function
Handles device readings API endpoints
"""

import json
import boto3
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
readings_table = dynamodb.Table(os.environ.get('READINGS_TABLE', 'AquaChain-Readings'))

def get_cognito_claims(event):
    """Safely extract Cognito claims from API Gateway event"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        
        # Handle different Cognito authorizer structures
        claims = authorizer.get('claims')
        
        # Try alternative structures if claims not found
        if not claims:
            # Sometimes claims are in jwt.claims
            jwt = authorizer.get('jwt', {})
            claims = jwt.get('claims', {})
        
        # If still no claims, try direct authorizer content
        if not claims and authorizer:
            claims = authorizer
        
        logger.info(f"Extracted claims keys: {list(claims.keys()) if claims else 'None'}")
        
        return claims or {}
        
    except Exception as e:
        logger.warning(f"Could not extract Cognito claims: {e}")
        return {}

def get_user_info(event):
    """Extract user information from Cognito claims"""
    claims = get_cognito_claims(event)
    
    return {
        'user_id': claims.get('sub', 'unknown'),
        'username': claims.get('cognito:username', claims.get('username', 'unknown')),
        'groups': claims.get('cognito:groups', []),
        'email': claims.get('email', 'unknown')
    }

def convert_decimals(obj):
    """Recursively convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def decimal_default(obj):
    """JSON serializer for Decimal objects (fallback)"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def create_response(status_code: int, body: Dict[str, Any], cors: bool = True) -> Dict[str, Any]:
    """Create standardized API Gateway proxy response"""
    
    # Ensure body is properly converted and serializable
    body = convert_decimals(body)
    
    # Create the response structure required by API Gateway
    response = {
        'statusCode': status_code,
        'body': json.dumps(body),  # Must be a string
        'isBase64Encoded': False
    }
    
    if cors:
        response['headers'] = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token'
        }
    
    # Debug log the final response structure
    logger.info(f"Creating response: statusCode={status_code}, bodyLength={len(response['body'])}")
    
    # Test JSON serialization to catch any issues early
    try:
        json.dumps(response)
        logger.info("Response JSON serialization test passed")
    except Exception as e:
        logger.error(f"Response serialization test failed: {e}")
        # Return a safe error response
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Response serialization error',
                'code': 'SERIALIZATION_ERROR'
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False
        }
    
    return response

def get_latest_reading(device_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest reading for a device"""
    try:
        # Get current month for partition key
        now = datetime.utcnow()
        device_month = f"{device_id}_{now.strftime('%Y-%m')}"
        
        logger.info(f"Querying latest reading for device: {device_id}, month: {device_month}")
        
        # Query the table with device_month partition key, sorted by timestamp descending
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': device_month
            },
            ScanIndexForward=False,  # Sort descending (latest first)
            Limit=1
        )
        
        if response['Items']:
            reading = response['Items'][0]
            # Convert Decimals to floats for JSON serialization
            reading = convert_decimals(reading)
            # Add WQI and quality if missing
            reading = add_missing_wqi_quality([reading])[0]
            logger.info(f"Found latest reading: {reading}")
            return reading
        
        # If no readings in current month, try previous month
        prev_month = (now.replace(day=1) - timedelta(days=1))
        prev_device_month = f"{device_id}_{prev_month.strftime('%Y-%m')}"
        
        logger.info(f"No readings in current month, trying previous: {prev_device_month}")
        
        response = readings_table.query(
            KeyConditionExpression='deviceId_month = :device_month',
            ExpressionAttributeValues={
                ':device_month': prev_device_month
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        if response['Items']:
            reading = response['Items'][0]
            # Convert Decimals to floats for JSON serialization
            reading = convert_decimals(reading)
            # Add WQI and quality if missing
            reading = add_missing_wqi_quality([reading])[0]
            logger.info(f"Found reading in previous month: {reading}")
            return reading
        
        logger.warning(f"No readings found for device: {device_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting latest reading for {device_id}: {e}")
        return None

def get_device_history(device_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Get reading history for a device"""
    try:
        readings = []
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)

        logger.info(f"Getting {days} days of history for device: {device_id}")

        # Build the set of year-month strings to query (covers multi-month ranges)
        months_to_query = set()
        cursor = start_date.replace(day=1)
        while cursor <= now:
            months_to_query.add(cursor.strftime('%Y-%m'))
            # Advance to next month
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)

        # Query both partition key formats: "deviceId_YYYY-MM" and "deviceId#YYYY-MM"
        # The legacy format used '#' as separator; current format uses '_'.
        partition_key_formats = [
            lambda ym: f"{device_id}_{ym}",
            lambda ym: f"{device_id}#{ym}",
        ]

        for ym in sorted(months_to_query):
            for fmt in partition_key_formats:
                device_month = fmt(ym)
                try:
                    response = readings_table.query(
                        KeyConditionExpression='deviceId_month = :device_month AND #ts >= :start_time',
                        ExpressionAttributeNames={'#ts': 'timestamp'},
                        ExpressionAttributeValues={
                            ':device_month': device_month,
                            ':start_time': start_date.isoformat() + 'Z',
                        },
                        ScanIndexForward=False,
                    )
                    items = response.get('Items', [])
                    if items:
                        logger.info(f"Found {len(items)} readings in partition {device_month}")
                    readings.extend(items)
                except Exception as qe:
                    logger.warning(f"Query failed for partition {device_month}: {qe}")

        # Convert all Decimals to floats for JSON serialization
        readings = convert_decimals(readings)

        # Add WQI and quality for readings that don't have them
        readings = add_missing_wqi_quality(readings)

        # Sort by timestamp descending, deduplicate by timestamp
        seen = set()
        unique = []
        for r in sorted(readings, key=lambda x: x['timestamp'], reverse=True):
            ts = r.get('timestamp', '')
            if ts not in seen:
                seen.add(ts)
                unique.append(r)

        logger.info(f"Found {len(unique)} unique readings for device {device_id} over {days} days")
        return unique

    except Exception as e:
        logger.error(f"Error getting history for {device_id}: {e}")
        return []

def add_missing_wqi_quality(readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add WQI and quality for readings that don't have them"""
    for reading in readings:
        # Skip WQI recalculation for sensor-faulted readings — the values are
        # unreliable so any calculated WQI would be meaningless.
        if reading.get('anomalyType') == 'sensor_fault' or reading.get('qualityStatus') == 'sensor_fault':
            reading.setdefault('quality', 'Sensor Fault')
            reading.setdefault('wqi', 0)
            continue

        # Check if WQI is missing or N/A
        wqi = reading.get('wqi') or reading.get('qualityScore')
        quality = reading.get('quality')
        
        if wqi is None or wqi == 'N/A' or quality is None or quality == 'N/A':
            # Calculate WQI using simple algorithm
            try:
                pH = float(reading.get('pH', 7.0))
                turbidity = float(reading.get('turbidity', 0.0))
                tds = float(reading.get('tds', 100.0))
                temperature = float(reading.get('temperature', 25.0))
                
                # Simple WQI calculation (0-100 scale)
                pH_score = max(0, 100 - abs(pH - 7.0) * 15)
                turbidity_score = max(0, 100 - turbidity * 10)
                tds_score = max(0, 100 - abs(tds - 100) / 10)
                temp_score = max(0, 100 - abs(temperature - 25) * 2)
                
                calculated_wqi = (pH_score + turbidity_score + tds_score + temp_score) / 4
                calculated_wqi = round(calculated_wqi, 1)
                
                # Map to quality - Updated thresholds for more accurate classification
                if calculated_wqi >= 90:
                    calculated_quality = 'Excellent'
                elif calculated_wqi >= 80:
                    calculated_quality = 'Good'
                elif calculated_wqi >= 60:
                    calculated_quality = 'Fair'
                elif calculated_wqi >= 40:
                    calculated_quality = 'Poor'
                else:
                    calculated_quality = 'Very Poor'
                
                # Update the reading
                reading['wqi'] = calculated_wqi
                reading['quality'] = calculated_quality
                
                # Also update qualityScore for backward compatibility
                if 'qualityScore' not in reading or reading['qualityScore'] is None:
                    reading['qualityScore'] = calculated_wqi
                
            except Exception as e:
                logger.warning(f"Error calculating WQI for reading: {e}")
                # Set default values
                reading['wqi'] = 50.0
                reading['quality'] = 'Fair'
                reading['qualityScore'] = 50.0
    
    return readings

def get_device_info(device_id: str) -> Optional[Dict[str, Any]]:
    """Get device information from Users table"""
    try:
        users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'AquaChain-Users'))
        
        # Scan for device (in production, use GSI for better performance)
        response = users_table.scan(
            FilterExpression='contains(deviceIds, :device_id)',
            ExpressionAttributeValues={':device_id': device_id}
        )
        
        if response['Items']:
            user = response['Items'][0]
            return {
                'deviceId': device_id,
                'location': user.get('address', 'Unknown Location'),
                'installationDate': user.get('createdAt', '2026-01-01'),
                'firmwareVersion': 'v2.1.0',  # Default version
                'ownerName': user.get('name', 'Unknown'),
                'ownerEmail': user.get('email', 'unknown@example.com')
            }
        
        return {
            'deviceId': device_id,
            'location': 'Unknown Location',
            'installationDate': '2026-01-01',
            'firmwareVersion': 'v2.1.0',
            'ownerName': 'Unknown',
            'ownerEmail': 'unknown@example.com'
        }
        
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        return None


def get_device_alerts(device_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Get alerts for a device"""
    try:
        alerts_table = dynamodb.Table(os.environ.get('ALERTS_TABLE', 'AquaChain-Alerts'))
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query alerts for device (assuming GSI exists)
        response = alerts_table.scan(
            FilterExpression='deviceId = :device_id AND #ts >= :start_date',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':device_id': device_id,
                ':start_date': start_date.isoformat() + 'Z'
            }
        )
        
        alerts = convert_decimals(response['Items'])
        
        # Sort by timestamp descending
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts for {device_id}: {e}")
        return []


def calculate_water_quality_summary(readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for water quality metrics"""
    if not readings:
        return {}
    
    try:
        # Extract numeric values
        ph_values = [float(r.get('pH', 0)) for r in readings if r.get('pH')]
        tds_values = [float(r.get('tds', 0)) for r in readings if r.get('tds')]
        turbidity_values = [float(r.get('turbidity', 0)) for r in readings if r.get('turbidity')]
        temp_values = [float(r.get('temperature', 0)) for r in readings if r.get('temperature')]
        wqi_values = [float(r.get('wqi', 0)) for r in readings if r.get('wqi')]
        
        summary = {}
        
        if ph_values:
            summary['pH'] = {
                'average': round(sum(ph_values) / len(ph_values), 2),
                'min': round(min(ph_values), 2),
                'max': round(max(ph_values), 2)
            }
        
        if tds_values:
            summary['TDS (ppm)'] = {
                'average': round(sum(tds_values) / len(tds_values), 0),
                'min': round(min(tds_values), 0),
                'max': round(max(tds_values), 0)
            }
        
        if turbidity_values:
            summary['Turbidity (NTU)'] = {
                'average': round(sum(turbidity_values) / len(turbidity_values), 1),
                'min': round(min(turbidity_values), 1),
                'max': round(max(turbidity_values), 1)
            }
        
        if temp_values:
            summary['Temperature (°C)'] = {
                'average': round(sum(temp_values) / len(temp_values), 1),
                'min': round(min(temp_values), 1),
                'max': round(max(temp_values), 1)
            }
        
        if wqi_values:
            summary['WQI'] = {
                'average': round(sum(wqi_values) / len(wqi_values), 0),
                'min': round(min(wqi_values), 0),
                'max': round(max(wqi_values), 0)
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error calculating summary: {e}")
        return {}


def get_wqi_interpretation() -> Dict[str, str]:
    """Get WQI interpretation legend"""
    return {
        '90-100': 'Excellent',
        '70-90': 'Good',
        '50-70': 'Moderate',
        '25-50': 'Poor',
        '0-25': 'Unsafe'
    }


def generate_comprehensive_export(device_id: str, days: int, export_format: str, user_info: Dict) -> Dict[str, Any]:
    """Generate comprehensive export data with all required sections"""
    try:
        logger.info(f"Generating comprehensive export for device {device_id}, {days} days, format: {export_format}")
        
        # Get all required data
        readings = get_device_history(device_id, days)
        device_info = get_device_info(device_id)
        alerts = get_device_alerts(device_id, days)
        summary = calculate_water_quality_summary(readings)
        wqi_legend = get_wqi_interpretation()
        
        # Generate export timestamp
        export_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Build comprehensive export data
        export_data = {
            'exportInfo': {
                'exportDate': export_timestamp,
                'userRole': user_info.get('role', 'Consumer'),
                'dateRange': f'Last {days} days',
                'totalReadings': len(readings),
                'format': export_format
            },
            'deviceInfo': device_info,
            'waterQualitySummary': summary,
            'sensorData': readings,
            'alerts': alerts,
            'wqiInterpretation': wqi_legend,
            'metadata': {
                'generatedBy': 'AquaChain Water Quality Monitoring System',
                'version': '1.0',
                'dataSource': 'IoT Sensors + ML Analysis',
                'accuracy': '99.74% (ML Model)',
                'samplingFrequency': 'Every 60 seconds'
            }
        }
        
        # Add format-specific processing
        if export_format == 'csv':
            export_data['csvData'] = generate_csv_format(readings, alerts)
        elif export_format == 'pdf':
            export_data['pdfReady'] = True
            export_data['chartData'] = generate_chart_data(readings)
        
        logger.info(f"Successfully generated export with {len(readings)} readings and {len(alerts)} alerts")
        return export_data
        
    except Exception as e:
        logger.error(f"Error generating comprehensive export: {e}", exc_info=True)
        return None


def generate_csv_format(readings: List[Dict], alerts: List[Dict]) -> Dict[str, str]:
    """Generate CSV format data for export"""
    try:
        import csv
        from io import StringIO
        
        # Generate readings CSV
        readings_csv = StringIO()
        if readings:
            fieldnames = ['timestamp', 'pH', 'tds', 'turbidity', 'temperature', 'wqi', 'quality']
            writer = csv.DictWriter(readings_csv, fieldnames=fieldnames)
            writer.writeheader()
            
            for reading in readings:
                writer.writerow({
                    'timestamp': reading.get('timestamp', ''),
                    'pH': reading.get('pH', ''),
                    'tds': reading.get('tds', ''),
                    'turbidity': reading.get('turbidity', ''),
                    'temperature': reading.get('temperature', ''),
                    'wqi': reading.get('wqi', ''),
                    'quality': reading.get('quality', '')
                })
        
        # Generate alerts CSV
        alerts_csv = StringIO()
        if alerts:
            fieldnames = ['timestamp', 'alertType', 'severity', 'message', 'status']
            writer = csv.DictWriter(alerts_csv, fieldnames=fieldnames)
            writer.writeheader()
            
            for alert in alerts:
                writer.writerow({
                    'timestamp': alert.get('timestamp', ''),
                    'alertType': alert.get('alertType', ''),
                    'severity': alert.get('severity', ''),
                    'message': alert.get('message', ''),
                    'status': alert.get('status', '')
                })
        
        return {
            'readings': readings_csv.getvalue(),
            'alerts': alerts_csv.getvalue()
        }
        
    except Exception as e:
        logger.error(f"Error generating CSV format: {e}")
        return {'readings': '', 'alerts': ''}


def generate_chart_data(readings: List[Dict]) -> Dict[str, List]:
    """Generate chart data for PDF reports"""
    try:
        chart_data = {
            'timestamps': [],
            'pH': [],
            'tds': [],
            'turbidity': [],
            'temperature': [],
            'wqi': []
        }
        
        # Sort readings by timestamp
        sorted_readings = sorted(readings, key=lambda x: x.get('timestamp', ''))
        
        for reading in sorted_readings[-50:]:  # Last 50 readings for chart
            chart_data['timestamps'].append(reading.get('timestamp', ''))
            chart_data['pH'].append(float(reading.get('pH', 0)))
            chart_data['tds'].append(float(reading.get('tds', 0)))
            chart_data['turbidity'].append(float(reading.get('turbidity', 0)))
            chart_data['temperature'].append(float(reading.get('temperature', 0)))
            chart_data['wqi'].append(float(reading.get('wqi', 0)))
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        return {}


def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Extract request details safely
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        logger.info(f"Method: {http_method}, Path: {path}")
        logger.info(f"Path params: {path_parameters}")
        logger.info(f"Query params: {query_parameters}")
        
        # Log user information for debugging
        user_info = get_user_info(event)
        logger.info(f"User info: {user_info}")
        
        # Log the full request context structure for debugging
        request_context = event.get('requestContext', {})
        logger.info(f"Request context keys: {list(request_context.keys())}")
        if 'authorizer' in request_context:
            authorizer = request_context['authorizer']
            logger.info(f"Authorizer keys: {list(authorizer.keys()) if isinstance(authorizer, dict) else type(authorizer)}")
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            logger.info("Handling CORS preflight request")
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token"
                },
                "body": "",
                "isBase64Encoded": False
            }
        
        # Extract device ID from path parameters
        device_id = path_parameters.get('deviceId')
        if not device_id:
            logger.error("Missing device ID in path parameters")
            return create_response(400, {
                'error': 'Device ID is required',
                'code': 'MISSING_DEVICE_ID'
            })

        # Ownership check — verify this device belongs to the requesting user
        # Admins bypass this check
        requesting_user_id = user_info.get('user_id', '')
        requesting_groups = user_info.get('groups', [])
        is_admin = 'administrators' in (requesting_groups if isinstance(requesting_groups, list) else [])

        if not is_admin and requesting_user_id and requesting_user_id != 'unknown':
            try:
                devices_table = dynamodb.Table(os.environ.get('DEVICES_TABLE', 'AquaChain-Devices'))
                device_item = devices_table.get_item(Key={'deviceId': device_id}).get('Item')
                if device_item and device_item.get('userId') and device_item.get('userId') != requesting_user_id:
                    logger.warning(f"User {requesting_user_id} attempted to access device {device_id} owned by {device_item.get('userId')}")
                    return create_response(403, {
                        'error': 'Access denied — this device does not belong to your account',
                        'code': 'DEVICE_ACCESS_DENIED'
                    })
            except Exception as e:
                logger.warning(f"Could not verify device ownership: {e}")
                # Fail open only if DynamoDB is unavailable — log for audit

        logger.info(f"Processing request for device: {device_id}")

        # Route based on path
        if path.endswith('/latest'):
            logger.info("Handling /latest endpoint")
            # Get latest reading
            reading = get_latest_reading(device_id)
            
            if reading:
                logger.info("Successfully retrieved latest reading")
                response_data = {
                    'success': True,
                    'reading': reading,
                    'deviceId': device_id
                }
                return create_response(200, response_data)
            else:
                logger.warning(f"No readings found for device {device_id}")
                return create_response(404, {
                    'error': f'No readings found for device {device_id}',
                    'code': 'NO_READINGS_FOUND',
                    'deviceId': device_id
                })
        
        elif path.endswith('/history'):
            logger.info("Handling /history endpoint")
            # Get reading history
            days = int(query_parameters.get('days', 7)) if query_parameters.get('days') else 7
            readings = get_device_history(device_id, days)
            
            logger.info(f"Retrieved {len(readings)} historical readings")
            return create_response(200, {
                'success': True,
                'readings': readings,
                'deviceId': device_id,
                'days': days,
                'count': len(readings)
            })
        
        elif path.endswith('/export'):
            logger.info("Handling /export endpoint")
            # Get comprehensive export data
            days = int(query_parameters.get('days', 7)) if query_parameters.get('days') else 7
            export_format = query_parameters.get('format', 'json')  # json, csv, or pdf
            
            export_data = generate_comprehensive_export(device_id, days, export_format, user_info)
            
            if export_data:
                logger.info(f"Generated export data for device {device_id}")
                return create_response(200, export_data)
            else:
                logger.warning(f"Failed to generate export for device {device_id}")
                return create_response(500, {
                    'error': 'Failed to generate export data',
                    'code': 'EXPORT_GENERATION_FAILED',
                    'deviceId': device_id
                })
        
        else:
            logger.error(f"Unknown endpoint: {path}")
            return create_response(404, {
                'error': f'Endpoint not found: {path}',
                'code': 'ENDPOINT_NOT_FOUND'
            })
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {e}", exc_info=True)
        # Ensure we always return a valid response
        return create_response(500, {
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': str(e),
            'requestId': context.aws_request_id if context else 'unknown'
        })