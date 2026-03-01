"""
AquaChain Security Audit Service
Handles security audit log retrieval, filtering, and export
"""

import json
import os
import boto3
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
AUDIT_LOGS_TABLE = os.environ.get('AUDIT_LOGS_TABLE', 'AquaChain-SecurityAuditLogs')
INTEGRITY_HASHES_TABLE = os.environ.get('INTEGRITY_HASHES_TABLE', 'AquaChain-IntegrityHashes')
EXPORT_BUCKET = os.environ.get('EXPORT_BUCKET', 'aquachain-audit-exports')

# DynamoDB tables
audit_logs_table = dynamodb.Table(AUDIT_LOGS_TABLE)
integrity_hashes_table = dynamodb.Table(INTEGRITY_HASHES_TABLE)


def lambda_handler(event, context):
    """
    Main Lambda handler for security audit operations
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        
        # Route to appropriate handler
        if '/admin/security/audit' in path:
            if http_method == 'GET' and path == '/admin/security/audit':
                return _get_audit_logs(query_params)
            elif http_method == 'POST' and '/export' in path:
                return _export_audit_logs(body, query_params)
        
        elif '/admin/security/integrity' in path:
            if http_method == 'GET':
                return _get_integrity_status(query_params)
            elif http_method == 'POST' and '/verify' in path:
                return _verify_integrity(body)
        
        return _create_response(404, {'error': 'Not found'})
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return _create_response(500, {'error': 'Internal server error', 'details': str(e)})


def _get_audit_logs(query_params: Dict) -> Dict:
    """
    Retrieve audit logs with filtering and pagination
    """
    try:
        # Extract filter parameters
        device_id = query_params.get('deviceId')
        anomaly_type = query_params.get('anomalyType')
        verification_status = query_params.get('verificationStatus')
        search_query = query_params.get('search')
        start_date = query_params.get('startDate')
        end_date = query_params.get('endDate')
        limit = int(query_params.get('limit', '100'))
        next_token = query_params.get('nextToken')
        
        # Build query parameters
        scan_kwargs = {
            'Limit': min(limit, 100)  # Cap at 100
        }
        
        if next_token:
            scan_kwargs['ExclusiveStartKey'] = json.loads(next_token)
        
        # Apply filters
        filter_expressions = []
        expression_values = {}
        expression_names = {}
        
        if device_id:
            filter_expressions.append('#deviceId = :deviceId')
            expression_values[':deviceId'] = device_id
            expression_names['#deviceId'] = 'deviceId'
        
        if anomaly_type and anomaly_type != 'All Types':
            filter_expressions.append('anomalyType = :anomalyType')
            expression_values[':anomalyType'] = anomaly_type
        
        if verification_status and verification_status != 'All Status':
            filter_expressions.append('verified = :verified')
            expression_values[':verified'] = verification_status == 'verified'
        
        if start_date:
            filter_expressions.append('#timestamp >= :startDate')
            expression_values[':startDate'] = start_date
            expression_names['#timestamp'] = 'timestamp'
        
        if end_date:
            filter_expressions.append('#timestamp <= :endDate')
            expression_values[':endDate'] = end_date
            expression_names['#timestamp'] = 'timestamp'
        
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
            if expression_names:
                scan_kwargs['ExpressionAttributeNames'] = expression_names
        
        # Execute scan
        response = audit_logs_table.scan(**scan_kwargs)
        
        items = response.get('Items', [])
        
        # Apply search filter if provided
        if search_query:
            search_lower = search_query.lower()
            items = [
                item for item in items
                if search_lower in item.get('deviceId', '').lower()
                or search_lower in item.get('anomalyType', '').lower()
                or search_lower in item.get('dataHash', '').lower()
            ]
        
        # Convert Decimal to float for JSON serialization
        items = json.loads(json.dumps(items, default=_decimal_default))
        
        # Prepare response
        result = {
            'logs': items,
            'count': len(items),
            'total': response.get('Count', 0)
        }
        
        if 'LastEvaluatedKey' in response:
            result['nextToken'] = json.dumps(response['LastEvaluatedKey'], default=_decimal_default)
        
        return _create_response(200, result)
        
    except Exception as e:
        print(f"Error in _get_audit_logs: {str(e)}")
        return _create_response(500, {'error': 'Failed to retrieve audit logs', 'details': str(e)})


def _export_audit_logs(body: Dict, query_params: Dict) -> Dict:
    """
    Export audit logs to CSV format
    """
    try:
        export_format = body.get('format', 'csv')
        filters = body.get('filters', {})
        
        # Retrieve all matching logs (up to 10,000)
        all_logs = []
        scan_kwargs = {'Limit': 1000}
        
        # Apply filters similar to _get_audit_logs
        filter_expressions = []
        expression_values = {}
        
        if filters.get('deviceId'):
            filter_expressions.append('deviceId = :deviceId')
            expression_values[':deviceId'] = filters['deviceId']
        
        if filters.get('anomalyType'):
            filter_expressions.append('anomalyType = :anomalyType')
            expression_values[':anomalyType'] = filters['anomalyType']
        
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
        
        # Paginate through results
        while len(all_logs) < 10000:
            response = audit_logs_table.scan(**scan_kwargs)
            all_logs.extend(response.get('Items', []))
            
            if 'LastEvaluatedKey' not in response:
                break
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        
        # Generate export file
        export_id = f"export-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        if export_format == 'csv':
            file_content = _generate_csv(all_logs)
            file_key = f"exports/{export_id}.csv"
            content_type = 'text/csv'
        else:
            file_content = json.dumps(all_logs, default=_decimal_default, indent=2)
            file_key = f"exports/{export_id}.json"
            content_type = 'application/json'
        
        # Upload to S3
        s3_client.put_object(
            Bucket=EXPORT_BUCKET,
            Key=file_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # Generate pre-signed URL (1 hour expiry)
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': EXPORT_BUCKET, 'Key': file_key},
            ExpiresIn=3600
        )
        
        return _create_response(200, {
            'exportId': export_id,
            'downloadUrl': download_url,
            'recordCount': len(all_logs),
            'expiresIn': 3600
        })
        
    except Exception as e:
        print(f"Error in _export_audit_logs: {str(e)}")
        return _create_response(500, {'error': 'Failed to export audit logs', 'details': str(e)})


def _generate_csv(logs: List[Dict]) -> str:
    """
    Generate CSV content from audit logs
    """
    if not logs:
        return "No data"
    
    # CSV header
    headers = ['Timestamp', 'Device ID', 'WQI', 'Anomaly Type', 'Verified', 'Data Hash']
    csv_lines = [','.join(headers)]
    
    # CSV rows
    for log in logs:
        row = [
            log.get('timestamp', ''),
            log.get('deviceId', ''),
            str(log.get('wqi', '')),
            log.get('anomalyType', ''),
            'Yes' if log.get('verified') else 'No',
            log.get('dataHash', '')
        ]
        csv_lines.append(','.join(f'"{field}"' for field in row))
    
    return '\n'.join(csv_lines)


def _get_integrity_status(query_params: Dict) -> Dict:
    """
    Get integrity verification status
    """
    try:
        # Get recent integrity checks
        response = integrity_hashes_table.scan(Limit=10)
        
        checks = response.get('Items', [])
        checks = json.loads(json.dumps(checks, default=_decimal_default))
        
        # Sort by date descending
        checks.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return _create_response(200, {
            'recentChecks': checks[:5],
            'lastVerified': checks[0].get('date') if checks else None,
            'status': 'healthy' if all(c.get('verified', False) for c in checks[:5]) else 'warning'
        })
        
    except Exception as e:
        print(f"Error in _get_integrity_status: {str(e)}")
        return _create_response(500, {'error': 'Failed to get integrity status', 'details': str(e)})


def _verify_integrity(body: Dict) -> Dict:
    """
    Verify hash chain integrity for a date range
    """
    try:
        start_date = body.get('startDate')
        end_date = body.get('endDate')
        
        if not start_date or not end_date:
            return _create_response(400, {'error': 'startDate and endDate are required'})
        
        # Retrieve logs for date range
        response = audit_logs_table.scan(
            FilterExpression='#timestamp BETWEEN :start AND :end',
            ExpressionAttributeNames={'#timestamp': 'timestamp'},
            ExpressionAttributeValues={
                ':start': start_date,
                ':end': end_date
            }
        )
        
        logs = response.get('Items', [])
        
        # Sort by timestamp
        logs.sort(key=lambda x: x.get('timestamp', ''))
        
        # Verify hash chain
        tampering_detected = False
        previous_hash = None
        
        for log in logs:
            current_hash = log.get('dataHash', '')
            
            # Verify hash includes previous hash (simplified check)
            if previous_hash and previous_hash not in current_hash:
                tampering_detected = True
                break
            
            previous_hash = current_hash
        
        # Store verification result
        verification_record = {
            'date': datetime.utcnow().isoformat(),
            'startDate': start_date,
            'endDate': end_date,
            'verified': not tampering_detected,
            'recordCount': len(logs)
        }
        
        integrity_hashes_table.put_item(Item=verification_record)
        
        return _create_response(200, {
            'verified': not tampering_detected,
            'recordCount': len(logs),
            'message': 'Integrity verified successfully' if not tampering_detected else 'Tampering detected!'
        })
        
    except Exception as e:
        print(f"Error in _verify_integrity: {str(e)}")
        return _create_response(500, {'error': 'Failed to verify integrity', 'details': str(e)})


def _decimal_default(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def _create_response(status_code: int, body: Dict) -> Dict:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, default=_decimal_default)
    }
