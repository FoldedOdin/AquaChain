"""
Alert Detection Lambda Function for AquaChain System
Handles critical event detection, alert classification, and threshold monitoring
Also serves as API endpoint for retrieving user alerts
"""

import json
import boto3
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Environment variables — never hardcoded
ALERTS_TABLE = os.environ.get('ALERTS_TABLE', 'AquaChain-Alerts')
USERS_TABLE = os.environ.get('USERS_TABLE', 'AquaChain-Users')
DEVICES_TABLE = os.environ.get('DEVICES_TABLE', 'AquaChain-Devices')
CONFIG_TABLE = os.environ.get('CONFIG_TABLE', 'AquaChain-SystemConfig')
CRITICAL_ALERTS_TOPIC = os.environ.get('CRITICAL_ALERTS_TOPIC_ARN', '')
WARNING_ALERTS_TOPIC = os.environ.get('WARNING_ALERTS_TOPIC_ARN', '')
NOTIFICATION_LAMBDA = os.environ.get('NOTIFICATION_LAMBDA_NAME', 'aquachain-function-notification-dev')

# ── Default thresholds (used as fallback when DynamoDB config is unavailable) ──
_DEFAULT_CRITICAL = {
    'wqi_min': 50,
    'pH_min': 6.5,
    'pH_max': 8.5,
    'turbidity_max': 25,
    'tds_max': 1000,
    'temperature_min': 0,
    'temperature_max': 45,
}
_DEFAULT_WARNING = {
    'wqi_min': 70,
    'pH_min': 6.8,
    'pH_max': 8.2,
    'turbidity_max': 10,
    'tds_max': 600,
    'temperature_min': 5,
    'temperature_max': 40,
}

# ── In-memory threshold cache (refreshed every 60 s) ──
_threshold_cache: Dict[str, Any] = {}
_threshold_cache_ts: float = 0.0
_THRESHOLD_CACHE_TTL = 60  # seconds


def _load_thresholds() -> Dict[str, Dict[str, Any]]:
    """
    Load alert thresholds from AquaChain-SystemConfig DynamoDB table.
    Results are cached for _THRESHOLD_CACHE_TTL seconds to avoid a DB hit
    on every stream record.  Falls back to hardcoded defaults on any error.

    Returns a dict with keys 'critical' and 'warning', each mapping
    sensor names to their threshold values in the internal format used by
    detect_alert_level() and get_alert_reasons().
    """
    import time
    global _threshold_cache, _threshold_cache_ts

    now = time.monotonic()
    if _threshold_cache and (now - _threshold_cache_ts) < _THRESHOLD_CACHE_TTL:
        return _threshold_cache

    try:
        table = dynamodb.Table(CONFIG_TABLE)
        response = table.get_item(Key={'configKey': 'system_config'})
        item = response.get('Item')

        if not item or 'alertThresholds' not in item:
            raise ValueError("No alertThresholds in system config")

        global_t = item['alertThresholds'].get('global', {})

        def _num(val, default):
            """Convert Decimal or numeric to float, fall back to default."""
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        # pH — supports both legacy {min/max} and severity {critical/warning} formats
        ph = global_t.get('pH', {})
        ph_crit = ph.get('critical', {})
        ph_warn = ph.get('warning', {})

        # turbidity
        turb = global_t.get('turbidity', {})
        turb_crit = turb.get('critical', {})
        turb_warn = turb.get('warning', {})

        # TDS
        tds = global_t.get('tds', {})
        tds_crit = tds.get('critical', {})
        tds_warn = tds.get('warning', {})

        # temperature
        temp = global_t.get('temperature', {})
        temp_crit = temp.get('critical', {})
        temp_warn = temp.get('warning', {})

        # WQI
        wqi_t = global_t.get('wqi', {})

        raw_ph_crit_max = _num(ph_crit.get('max', ph.get('max')), _DEFAULT_CRITICAL['pH_max'])
        raw_ph_crit_min = _num(ph_crit.get('min', ph.get('min')), _DEFAULT_CRITICAL['pH_min'])

        # Sanity-check: critical pH_max must be > 7.5 (neutral pH is 7.0; a critical upper
        # bound ≤ 7.5 means the admin set the "inner safe zone" upper limit instead of the
        # actual danger threshold, which causes false critical alerts for normal pH values).
        # Fall back to the WHO-standard default (8.5) if the configured value is too low.
        if raw_ph_crit_max <= 7.5:
            logger.warning(
                f"Configured pH critical max ({raw_ph_crit_max}) is ≤ 7.5 — "
                "this would cause false critical alerts for normal pH. "
                f"Falling back to default ({_DEFAULT_CRITICAL['pH_max']}). "
                "Please update System Configuration: Critical pH max should be ~8.5."
            )
            raw_ph_crit_max = _DEFAULT_CRITICAL['pH_max']

        critical = {
            'wqi_min':        _num(wqi_t.get('critical'), _DEFAULT_CRITICAL['wqi_min']),
            'pH_min':         raw_ph_crit_min,
            'pH_max':         raw_ph_crit_max,
            'turbidity_max':  _num(turb_crit.get('max', turb.get('max')), _DEFAULT_CRITICAL['turbidity_max']),
            'tds_max':        _num(tds_crit.get('max', tds.get('max')), _DEFAULT_CRITICAL['tds_max']),
            'temperature_min': _num(temp_crit.get('min', temp.get('min')), _DEFAULT_CRITICAL['temperature_min']),
            'temperature_max': _num(temp_crit.get('max', temp.get('max')), _DEFAULT_CRITICAL['temperature_max']),
        }
        warning = {
            'wqi_min':        _num(wqi_t.get('warning'), _DEFAULT_WARNING['wqi_min']),
            'pH_min':         _num(ph_warn.get('min'), _DEFAULT_WARNING['pH_min']),
            'pH_max':         _num(ph_warn.get('max'), _DEFAULT_WARNING['pH_max']),
            'turbidity_max':  _num(turb_warn.get('max'), _DEFAULT_WARNING['turbidity_max']),
            'tds_max':        _num(tds_warn.get('max'), _DEFAULT_WARNING['tds_max']),
            'temperature_min': _num(temp_warn.get('min'), _DEFAULT_WARNING['temperature_min']),
            'temperature_max': _num(temp_warn.get('max'), _DEFAULT_WARNING['temperature_max']),
        }

        _threshold_cache = {'critical': critical, 'warning': warning}
        _threshold_cache_ts = now
        logger.info("Loaded alert thresholds from SystemConfig")
        return _threshold_cache

    except Exception as e:
        logger.warning(f"Could not load thresholds from DynamoDB, using defaults: {e}")
        return {'critical': _DEFAULT_CRITICAL, 'warning': _DEFAULT_WARNING}


# Alert escalation settings
ESCALATION_WINDOW_MINUTES = 30  # Time window for sustained issues
ESCALATION_THRESHOLD_COUNT = 3  # Number of alerts in window to trigger escalation

class AlertDetectionError(Exception):
    """Custom exception for alert detection errors"""
    pass

def lambda_handler(event, context):
    """
    Main Lambda handler for alert detection and API requests
    Handles both DynamoDB Streams and HTTP API Gateway requests
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        
        # Check if this is an API Gateway request
        if 'httpMethod' in event:
            return handle_api_request(event, context)
        
        # Otherwise, process DynamoDB Stream records
        for record in event.get('Records', []):
            if record['eventName'] in ['INSERT', 'MODIFY']:
                process_reading_record(record)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Alert detection completed',
                'processedRecords': len(event.get('Records', []))
            })
        }
        
    except Exception as e:
        logger.error(f"Alert detection error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def handle_api_request(event, context):
    """
    Handle API Gateway requests for alerts
    """
    try:
        method = event['httpMethod']
        path = event['path']
        
        # Add CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Credentials': 'true'
        }
        
        # Handle OPTIONS request for CORS preflight
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Handle GET /alerts
        if method == 'GET' and '/alerts' in path:
            return get_user_alerts(event, headers)

        # Handle PUT /api/alerts/{alertId}/acknowledge
        if method == 'PUT' and '/acknowledge' in path:
            return acknowledge_alert(event, headers)

        # Handle PUT /api/alerts/{alertId}/mute
        if method == 'PUT' and '/mute' in path:
            return mute_alert(event, headers)

        # Handle PUT /api/alerts/{alertId}/resolve
        if method == 'PUT' and '/resolve' in path:
            return resolve_alert(event, headers)

        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Endpoint not found'})
        }
        
    except Exception as e:
        logger.error(f"API request error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_user_alerts(event, headers):
    """
    Get alerts for the authenticated user
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 50))

        # Extract user ID from Cognito JWT claims (set by API Gateway authorizer)
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')

        if not user_id:
            logger.warning("No user_id found in JWT claims, returning empty alerts")
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'alerts': [], 'count': 0, 'timestamp': datetime.utcnow().isoformat()})
            }

        # Get user's device IDs so we only return alerts for their devices
        devices_table = dynamodb.Table(DEVICES_TABLE)
        try:
            dev_response = devices_table.query(
                IndexName='UserIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id)
            )
        except Exception:
            dev_response = devices_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('userId').eq(user_id)
            )
        user_device_ids = {d['deviceId'] for d in dev_response.get('Items', [])}

        # Query alerts table
        table = dynamodb.Table(ALERTS_TABLE)
        response = table.scan(Limit=min(limit * 3, 300))  # over-fetch to allow filtering
        all_alerts = response.get('Items', [])

        # Filter to only this user's devices
        if user_device_ids:
            all_alerts = [a for a in all_alerts if a.get('deviceId') in user_device_ids]

        # Sort by timestamp descending and apply limit
        all_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        alerts = all_alerts[:limit]

        # Convert Decimal to float for JSON serialization
        alerts = convert_decimals_to_float(alerts)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

    except Exception as e:
        logger.error(f"Error getting user alerts: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def _get_alert_user_id(event):
    """Extract user ID from Cognito JWT claims."""
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    return claims.get('sub') or claims.get('cognito:username')


def _get_alert_id_from_path(path):
    """Extract alertId from path like /api/alerts/{alertId}/acknowledge."""
    parts = [p for p in path.split('/') if p]
    # parts: ['api', 'alerts', '<alertId>', 'acknowledge']
    try:
        alerts_idx = parts.index('alerts')
        return parts[alerts_idx + 1]
    except (ValueError, IndexError):
        return None


def acknowledge_alert(event, headers):
    """PUT /api/alerts/{alertId}/acknowledge"""
    try:
        user_id = _get_alert_user_id(event)
        alert_id = (
            (event.get('pathParameters') or {}).get('alertId')
            or _get_alert_id_from_path(event.get('path', ''))
        )
        if not alert_id:
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'Alert ID required'})}

        table = dynamodb.Table(ALERTS_TABLE)
        update_time = datetime.utcnow().isoformat()
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET #s = :s, acknowledgedBy = :u, acknowledgedAt = :t',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'ACKNOWLEDGED', ':u': user_id or 'user', ':t': update_time},
        )
        logger.info(f"Alert acknowledged: {alert_id} by {user_id}")
        return {
            'statusCode': 200, 'headers': headers,
            'body': json.dumps({'message': 'Alert acknowledged', 'alertId': alert_id,
                                'status': 'ACKNOWLEDGED', 'acknowledgedAt': update_time})
        }
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}


def mute_alert(event, headers):
    """PUT /api/alerts/{alertId}/mute"""
    try:
        user_id = _get_alert_user_id(event)
        alert_id = (
            (event.get('pathParameters') or {}).get('alertId')
            or _get_alert_id_from_path(event.get('path', ''))
        )
        if not alert_id:
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'Alert ID required'})}

        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except Exception:
                pass

        mute_minutes = int(body.get('muteMinutes', 120))
        mute_until = (datetime.utcnow() + timedelta(minutes=mute_minutes)).isoformat()
        update_time = datetime.utcnow().isoformat()

        table = dynamodb.Table(ALERTS_TABLE)
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET #s = :s, mutedBy = :u, mutedAt = :t, muteUntil = :until',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'ARCHIVED', ':u': user_id or 'user',
                                       ':t': update_time, ':until': mute_until},
        )
        logger.info(f"Alert muted until {mute_until}: {alert_id} by {user_id}")
        return {
            'statusCode': 200, 'headers': headers,
            'body': json.dumps({'message': f'Muted for {mute_minutes} minutes', 'alertId': alert_id,
                                'status': 'ARCHIVED', 'muteUntil': mute_until})
        }
    except Exception as e:
        logger.error(f"Error muting alert: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}


def resolve_alert(event, headers):
    """PUT /api/alerts/{alertId}/resolve"""
    try:
        user_id = _get_alert_user_id(event)
        alert_id = (
            (event.get('pathParameters') or {}).get('alertId')
            or _get_alert_id_from_path(event.get('path', ''))
        )
        if not alert_id:
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'Alert ID required'})}

        update_time = datetime.utcnow().isoformat()
        table = dynamodb.Table(ALERTS_TABLE)
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET #s = :s, resolvedBy = :u, resolvedAt = :t',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'RESOLVED', ':u': user_id or 'user', ':t': update_time},
        )
        logger.info(f"Alert resolved: {alert_id} by {user_id}")
        return {
            'statusCode': 200, 'headers': headers,
            'body': json.dumps({'message': 'Alert resolved', 'alertId': alert_id,
                                'status': 'RESOLVED', 'resolvedAt': update_time})
        }
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}


def convert_decimals_to_float(obj):
    """
    Convert Decimal objects to float for JSON serialization
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    return obj

def generate_mock_alerts(limit):
    """
    Generate mock alerts for testing
    """
    mock_alerts = []
    for i in range(min(limit, 5)):
        alert = {
            'alertId': f'alert-{i+1}',
            'deviceId': f'ESP32-{i+1:03d}',
            'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            'alertLevel': 'warning' if i % 2 == 0 else 'critical',
            'wqi': 45 + (i * 5),
            'issue': f'Water quality degraded - pH level abnormal',
            'status': 'active',
            'location': 'Kitchen Sink'
        }
        mock_alerts.append(alert)
    
    return mock_alerts

def process_reading_record(record: Dict[str, Any]) -> None:
    """
    Process individual DynamoDB Stream record for alert detection
    """
    try:
        # Extract reading data from DynamoDB Stream record
        if record['eventName'] == 'INSERT':
            reading_data = record['dynamodb']['NewImage']
        else:  # MODIFY
            reading_data = record['dynamodb']['NewImage']
        
        # Convert DynamoDB format to standard format
        reading = convert_dynamodb_record(reading_data)
        
        # Detect alert conditions
        alert_level = detect_alert_level(reading)
        
        if alert_level != 'safe':
            # Create alert record
            alert = create_alert_record(reading, alert_level)
            
            # Store alert in database
            store_alert(alert)
            
            # Check for alert deduplication
            if not is_duplicate_alert(alert):
                # Trigger notification
                trigger_alert_notification(alert)
                
                # Check for escalation conditions
                check_alert_escalation(alert)
            
            logger.info(f"Alert processed: {alert_level} for device {reading['deviceId']}")
        
    except Exception as e:
        logger.error(f"Error processing reading record: {e}")
        raise AlertDetectionError(f"Failed to process record: {e}")

def convert_dynamodb_record(dynamodb_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert DynamoDB Stream record format to standard reading format
    """
    try:
        # Readings are stored as top-level fields in DynamoDB (not nested under 'readings')
        # anomalyType was added later; older records use qualityStatus as the fallback.
        anomaly_type = (
            dynamodb_data['anomalyType']['S']
            if 'anomalyType' in dynamodb_data
            else dynamodb_data.get('qualityStatus', {}).get('S', 'unknown')
        )
        # wqi stored as Decimal(0) sentinel when sensor_fault; treat 0 as valid number
        wqi_val = float(dynamodb_data['wqi']['N']) if 'wqi' in dynamodb_data else float(dynamodb_data.get('qualityScore', {}).get('N', 0))

        reading = {
            'deviceId': dynamodb_data['deviceId']['S'],
            'timestamp': dynamodb_data['timestamp']['S'],
            'wqi': wqi_val,
            'anomalyType': anomaly_type,
            'readings': {
                'pH': float(dynamodb_data['pH']['N']),
                'turbidity': float(dynamodb_data['turbidity']['N']),
                'tds': float(dynamodb_data['tds']['N']),
                'temperature': float(dynamodb_data['temperature']['N'])
            },
            'location': {
                'latitude': float(dynamodb_data.get('location', {}).get('M', {}).get('latitude', {}).get('N', 0)),
                'longitude': float(dynamodb_data.get('location', {}).get('M', {}).get('longitude', {}).get('N', 0))
            }
        }

        # Carry the device owner through so notifications can target them directly
        if 'userId' in dynamodb_data:
            reading['userId'] = dynamodb_data['userId']['S']

        return reading

    except Exception as e:
        logger.error(f"Error converting DynamoDB record: {e}")
        raise AlertDetectionError(f"Record conversion failed: {e}")

def detect_alert_level(reading: Dict[str, Any]) -> str:
    """
    Detect alert level based on WQI and sensor thresholds loaded from SystemConfig.
    Returns: 'critical', 'warning', or 'safe'
    """
    try:
        anomaly_type = reading['anomalyType']

        # sensor_fault is always a warning — wqi=0 is a sentinel, not a real measurement,
        # so skip numeric threshold checks to avoid false critical alerts.
        if anomaly_type == 'sensor_fault':
            return 'warning'

        thresholds = _load_thresholds()
        crit = thresholds['critical']
        warn = thresholds['warning']

        wqi = reading['wqi']
        r = reading['readings']

        # Check for critical conditions
        if (wqi < crit['wqi_min'] or
                r['pH'] < crit['pH_min'] or
                r['pH'] > crit['pH_max'] or
                r['turbidity'] > crit['turbidity_max'] or
                r['tds'] > crit['tds_max'] or
                r['temperature'] < crit['temperature_min'] or
                r['temperature'] > crit['temperature_max'] or
                anomaly_type == 'contamination'):
            return 'critical'

        # Check for warning conditions
        if (wqi < warn['wqi_min'] or
                r['pH'] < warn['pH_min'] or
                r['pH'] > warn['pH_max'] or
                r['turbidity'] > warn['turbidity_max'] or
                r['tds'] > warn['tds_max'] or
                r['temperature'] < warn['temperature_min'] or
                r['temperature'] > warn['temperature_max']):
            return 'warning'

        return 'safe'

    except Exception as e:
        logger.error(f"Error detecting alert level: {e}")
        return 'safe'  # Default to safe if detection fails

def create_alert_record(reading: Dict[str, Any], alert_level: str) -> Dict[str, Any]:
    """
    Create alert record with all necessary information
    """
    try:
        alert_id = generate_alert_id(reading['deviceId'], reading['timestamp'])
        
        # Determine specific alert reasons
        alert_reasons = get_alert_reasons(reading, alert_level)
        
        alert = {
            'alertId': alert_id,
            'deviceId': reading['deviceId'],
            'timestamp': reading['timestamp'],
            'alertLevel': alert_level,
            'severity': alert_level,          # frontend reads 'severity'
            'wqi': reading['wqi'],
            'anomalyType': reading['anomalyType'],
            'readings': reading['readings'],
            'location': reading['location'],
            'alertReasons': alert_reasons,
            'issue': alert_reasons[0] if alert_reasons else 'Water quality alert',
            'status': 'TRIGGERED',            # lifecycle: TRIGGERED → ACKNOWLEDGED → RESOLVED → ARCHIVED
            'createdAt': datetime.utcnow().isoformat(),
            'acknowledgedAt': None,
            'resolvedAt': None,
            'notificationsSent': [],
            'escalated': False
        }
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating alert record: {e}")
        raise AlertDetectionError(f"Alert creation failed: {e}")

def generate_alert_id(device_id: str, timestamp: str) -> str:
    """
    Generate unique alert ID based on device and timestamp
    """
    data = f"{device_id}:{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()[:12]

def get_alert_reasons(reading: Dict[str, Any], alert_level: str) -> List[str]:
    """
    Get specific reasons for the alert based on threshold violations.
    Thresholds are loaded from SystemConfig so they reflect admin-configured values.
    """
    reasons = []
    wqi = reading['wqi']
    r = reading['readings']
    anomaly_type = reading['anomalyType']

    # sensor_fault: report the fault directly, skip numeric threshold checks
    # since wqi=0 is a sentinel value and readings may be physically impossible.
    if anomaly_type == 'sensor_fault':
        reasons.append("Sensor malfunction detected - readings may be inaccurate")
        return reasons

    thresholds = _load_thresholds()
    t = thresholds['critical'] if alert_level == 'critical' else thresholds['warning']

    if wqi < t['wqi_min']:
        reasons.append(f"Water Quality Index ({wqi:.1f}) below safe threshold ({t['wqi_min']})")

    if r['pH'] < t['pH_min']:
        reasons.append(f"pH level ({r['pH']:.2f}) too acidic (below {t['pH_min']})")
    elif r['pH'] > t['pH_max']:
        reasons.append(f"pH level ({r['pH']:.2f}) too alkaline (above {t['pH_max']})")

    if r['turbidity'] > t['turbidity_max']:
        reasons.append(f"High turbidity ({r['turbidity']:.1f} NTU) above threshold ({t['turbidity_max']})")

    if r['tds'] > t['tds_max']:
        reasons.append(f"High dissolved solids ({r['tds']:.0f} ppm) above threshold ({t['tds_max']})")

    if r['temperature'] < t['temperature_min']:
        reasons.append(f"Temperature ({r['temperature']:.1f}°C) below minimum ({t['temperature_min']}°C)")
    elif r['temperature'] > t['temperature_max']:
        reasons.append(f"Temperature ({r['temperature']:.1f}°C) above maximum ({t['temperature_max']}°C)")

    if anomaly_type == 'contamination':
        reasons.append("AI model detected potential water contamination")

    return reasons

def convert_floats_to_decimal(obj):
    """
    Recursively convert float values to Decimal for DynamoDB compatibility
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj

def store_alert(alert: Dict[str, Any]) -> None:
    """
    Store alert record in DynamoDB
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        # Add TTL for alert cleanup (30 days)
        ttl_timestamp = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        alert['ttl'] = ttl_timestamp
        
        # Convert floats to Decimal for DynamoDB
        alert_decimal = convert_floats_to_decimal(alert)
        
        table.put_item(Item=alert_decimal)
        
        logger.info(f"Stored alert {alert['alertId']} for device {alert['deviceId']}")
        
    except Exception as e:
        logger.error(f"Error storing alert: {e}")
        raise AlertDetectionError(f"Alert storage failed: {e}")

def is_duplicate_alert(alert: Dict[str, Any]) -> bool:
    """
    Check if similar alert was recently sent to avoid spam.
    Cooldown windows:
      - warning:  2 minutes  (same device + same alert level)
      - critical: 5 minutes  (same device + same alert level)
    Deduplication is per-device per-level so a device can escalate from
    warning → critical without being suppressed.
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)

        cooldown_minutes = 5 if alert['alertLevel'] == 'critical' else 2
        current_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
        window_start = current_time - timedelta(minutes=cooldown_minutes)

        response = table.query(
            IndexName='DeviceAlerts',
            KeyConditionExpression=(
                boto3.dynamodb.conditions.Key('deviceId').eq(alert['deviceId']) &
                boto3.dynamodb.conditions.Key('createdAt').gt(window_start.isoformat())
            ),
            FilterExpression=boto3.dynamodb.conditions.Attr('alertLevel').eq(alert['alertLevel'])
        )

        recent_alerts = response.get('Items', [])

        if recent_alerts:
            logger.info(
                f"Duplicate alert suppressed for device {alert['deviceId']} "
                f"(level={alert['alertLevel']}, cooldown={cooldown_minutes}m)"
            )
            return True

        return False

    except Exception as e:
        logger.warning(f"Error checking duplicate alert: {e}")
        return False  # Continue with notification if check fails

def trigger_alert_notification(alert: Dict[str, Any]) -> None:
    """
    Trigger alert notification through SNS and notification service
    """
    try:
        # Determine SNS topic based on alert level
        topic_arn = CRITICAL_ALERTS_TOPIC if alert['alertLevel'] == 'critical' else WARNING_ALERTS_TOPIC

        # Create notification message — include userId so the notification
        # Lambda can target the consumer directly without a second lookup
        notification_message = {
            'type': 'water_quality_alert',
            'alertId': alert['alertId'],
            'deviceId': alert['deviceId'],
            'userId': alert.get('userId'),
            'alertLevel': alert['alertLevel'],
            'timestamp': alert['timestamp'],
            'wqi': alert['wqi'],
            'location': alert['location'],
            'alertReasons': alert['alertReasons'],
            'anomalyType': alert['anomalyType']
        }

        # Publish to SNS topic
        if topic_arn:
            sns_response = sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(notification_message),
                Subject=f"{alert['alertLevel'].title()} Water Quality Alert - Device {alert['deviceId']}",
                MessageAttributes={
                    'alertLevel': {'DataType': 'String', 'StringValue': alert['alertLevel']},
                    'deviceId': {'DataType': 'String', 'StringValue': alert['deviceId']},
                    'wqi': {'DataType': 'Number', 'StringValue': str(alert['wqi'] if alert['wqi'] is not None else 0)}
                }
            )
            update_alert_notifications(alert['alertId'], 'sns', sns_response['MessageId'])
        else:
            logger.warning(
                f"SNS topic ARN not configured for alert level '{alert['alertLevel']}' — "
                f"set CRITICAL_ALERTS_TOPIC_ARN / WARNING_ALERTS_TOPIC_ARN env vars. "
                f"Alert {alert['alertId']} for device {alert['deviceId']} was NOT published to SNS."
            )

        # Invoke notification service Lambda for multi-channel delivery (push/email/SMS)
        if NOTIFICATION_LAMBDA:
            lambda_client.invoke(
                FunctionName=NOTIFICATION_LAMBDA,
                InvocationType='Event',  # Async
                Payload=json.dumps({
                    'action': 'send_alert',
                    'alert': notification_message
                })
            )
        else:
            logger.warning(
                f"Notification Lambda name not configured — "
                f"set NOTIFICATION_LAMBDA_NAME env var. "
                f"Alert {alert['alertId']} for device {alert['deviceId']} was NOT delivered via push/email/SMS."
            )

        logger.info(f"Triggered {alert['alertLevel']} alert notification for device {alert['deviceId']}")

    except Exception as e:
        logger.error(f"Error triggering alert notification: {e}")
        # Don't fail the entire process if notification fails

def check_alert_escalation(alert: Dict[str, Any]) -> None:
    """
    Severity escalation logic:
    - If a WARNING has fired ≥3 times in the last 15 minutes → escalate to CRITICAL
    - If a CRITICAL has fired ≥ESCALATION_THRESHOLD_COUNT times in ESCALATION_WINDOW_MINUTES → escalate to admin
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        current_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))

        # Warning → Critical escalation
        if alert['alertLevel'] == 'warning':
            window_start = current_time - timedelta(minutes=15)
            response = table.query(
                IndexName='DeviceAlerts',
                KeyConditionExpression=(
                    boto3.dynamodb.conditions.Key('deviceId').eq(alert['deviceId']) &
                    boto3.dynamodb.conditions.Key('createdAt').gt(window_start.isoformat())
                ),
                FilterExpression=boto3.dynamodb.conditions.Attr('alertLevel').eq('warning')
            )
            warning_count = len(response.get('Items', []))
            if warning_count >= 3:
                logger.warning(
                    f"Escalating device {alert['deviceId']} from warning to critical "
                    f"({warning_count} warnings in 15 min)"
                )
                # Re-trigger notification at critical level
                escalated = {**alert, 'alertLevel': 'critical', 'escalated': True,
                             'escalationReason': f'{warning_count} warnings in 15 minutes'}
                trigger_alert_notification(escalated)
            return

        # Critical → Admin escalation
        if alert['alertLevel'] != 'critical':
            return

        window_start = current_time - timedelta(minutes=ESCALATION_WINDOW_MINUTES)
        response = table.query(
            IndexName='DeviceAlerts',
            KeyConditionExpression=(
                boto3.dynamodb.conditions.Key('deviceId').eq(alert['deviceId']) &
                boto3.dynamodb.conditions.Key('createdAt').gt(window_start.isoformat())
            ),
            FilterExpression=boto3.dynamodb.conditions.Attr('alertLevel').eq('critical')
        )
        critical_alerts = response.get('Items', [])
        if len(critical_alerts) >= ESCALATION_THRESHOLD_COUNT:
            escalate_alert(alert, len(critical_alerts))

    except Exception as e:
        logger.error(f"Error checking alert escalation: {e}")

def escalate_alert(alert: Dict[str, Any], alert_count: int) -> None:
    """
    Escalate sustained critical alerts to administrators
    """
    try:
        escalation_message = {
            'alertId': alert['alertId'],
            'deviceId': alert['deviceId'],
            'alertLevel': 'escalated',
            'sustainedAlertCount': alert_count,
            'timeWindow': f"{ESCALATION_WINDOW_MINUTES} minutes",
            'location': alert['location'],
            'latestWQI': alert['wqi'],
            'alertReasons': alert['alertReasons'],
            'escalatedAt': datetime.utcnow().isoformat()
        }
        
        # Send escalation notification to admin topic
        admin_topic = 'arn:aws:sns:us-east-1:123456789012:aquachain-admin-alerts'
        
        sns_client.publish(
            TopicArn=admin_topic,
            Message=json.dumps(escalation_message),
            Subject=f"ESCALATED: Sustained Critical Water Quality Issues - Device {alert['deviceId']}",
            MessageAttributes={
                'alertLevel': {'DataType': 'String', 'StringValue': 'escalated'},
                'deviceId': {'DataType': 'String', 'StringValue': alert['deviceId']},
                'sustainedCount': {'DataType': 'Number', 'StringValue': str(alert_count)}
            }
        )
        
        # Mark alert as escalated
        update_alert_escalation(alert['alertId'])
        
        logger.warning(f"Escalated sustained critical alerts for device {alert['deviceId']} "
                      f"({alert_count} alerts in {ESCALATION_WINDOW_MINUTES} minutes)")
        
    except Exception as e:
        logger.error(f"Error escalating alert: {e}")

def update_alert_notifications(alert_id: str, channel: str, message_id: str) -> None:
    """
    Update alert record with notification delivery information
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        notification_record = {
            'channel': channel,
            'messageId': message_id,
            'sentAt': datetime.utcnow().isoformat()
        }
        
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET notificationsSent = list_append(if_not_exists(notificationsSent, :empty_list), :notification)',
            ExpressionAttributeValues={
                ':notification': [notification_record],
                ':empty_list': []
            }
        )
        
    except Exception as e:
        logger.warning(f"Error updating alert notifications: {e}")

def update_alert_escalation(alert_id: str) -> None:
    """
    Mark alert as escalated in database
    """
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        
        table.update_item(
            Key={'alertId': alert_id},
            UpdateExpression='SET escalated = :escalated, escalatedAt = :escalatedAt',
            ExpressionAttributeValues={
                ':escalated': True,
                ':escalatedAt': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.warning(f"Error updating alert escalation: {e}")

def get_device_users(device_id: str) -> List[Dict[str, Any]]:
    """
    Get users associated with a device.
    Looks up the device record first (which stores the owner's userId),
    then fetches the user profile — avoids a full Users table scan.
    """
    try:
        # 1. Look up device to get the owner's userId
        devices_table = dynamodb.Table(DEVICES_TABLE)
        device_response = devices_table.get_item(Key={'deviceId': device_id})
        device = device_response.get('Item')

        if not device:
            logger.warning(f"Device {device_id} not found in devices table")
            return []

        owner_id = device.get('userId') or device.get('ownerId')
        if not owner_id:
            logger.warning(f"Device {device_id} has no userId/ownerId")
            return []

        # 2. Fetch the owner's user profile
        users_table = dynamodb.Table(USERS_TABLE)
        user_response = users_table.get_item(Key={'userId': owner_id})
        user = user_response.get('Item')

        return [user] if user else []

    except Exception as e:
        logger.error(f"Error getting device users: {e}")
        return []