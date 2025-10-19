"""
Analytics API Lambda function for reporting and compliance
Handles system analytics, compliance reports, and performance metrics
"""
import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from botocore.exceptions import ClientError
import statistics

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

# Table references
readings_table = dynamodb.Table('aquachain-readings')
service_requests_table = dynamodb.Table('aquachain-service-requests')
ledger_table = dynamodb.Table('aquachain-ledger')
users_table = dynamodb.Table('aquachain-users')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """Main Lambda handler for analytics API"""
    try:
        # Parse request
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {}) or {}
        query_parameters = event.get('queryStringParameters', {}) or {}
        
        # Get user context from authorizer
        user_context = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = user_context.get('sub')
        user_groups = user_context.get('cognito:groups', '').split(',')
        
        if not user_id:
            return create_response(401, {'error': 'Unauthorized', 'message': 'User not authenticated'})
        
        # Only administrators and technicians can access analytics
        if 'administrators' not in user_groups and 'technicians' not in user_groups:
            return create_response(403, {'error': 'Forbidden', 'message': 'Insufficient permissions for analytics'})
        
        # Route request based on path
        if http_method == 'GET':
            analytics_type = path_parameters.get('proxy', '').split('/')[0] if path_parameters.get('proxy') else 'dashboard'
            
            if analytics_type == 'dashboard':
                return get_dashboard_analytics(query_parameters, user_groups)
            elif analytics_type == 'compliance':
                return get_compliance_report(query_parameters, user_groups)
            elif analytics_type == 'performance':
                return get_performance_metrics(query_parameters, user_groups)
            elif analytics_type == 'water-quality':
                return get_water_quality_analytics(query_parameters, user_groups)
            elif analytics_type == 'service-metrics':
                return get_service_metrics(query_parameters, user_groups)
            else:
                return create_response(404, {'error': 'Not Found', 'message': 'Analytics endpoint not found'})
        
        else:
            return create_response(405, {'error': 'Method Not Allowed'})
    
    except Exception as e:
        logger.error(f"Error processing analytics request: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_dashboard_analytics(query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Get dashboard analytics overview"""
    try:
        # Parse time range
        days = int(query_params.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get system health metrics
        system_health = get_system_health_metrics()
        
        # Get device fleet status
        device_status = get_device_fleet_status(start_date, end_date)
        
        # Get alert summary
        alert_summary = get_alert_summary(start_date, end_date)
        
        # Get service request summary
        service_summary = get_service_request_summary(start_date, end_date)
        
        # Get water quality trends
        wq_trends = get_water_quality_trends(start_date, end_date)
        
        return create_response(200, {
            'timeRange': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'systemHealth': system_health,
            'deviceStatus': device_status,
            'alertSummary': alert_summary,
            'serviceSummary': service_summary,
            'waterQualityTrends': wq_trends
        })
    
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_compliance_report(query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Generate compliance report"""
    try:
        # Only administrators can access compliance reports
        if 'administrators' not in user_groups:
            return create_response(403, {'error': 'Forbidden', 'message': 'Administrator access required'})
        
        # Parse parameters
        start_date = query_params.get('startDate')
        end_date = query_params.get('endDate')
        report_type = query_params.get('type', 'full')
        
        if not start_date or not end_date:
            return create_response(400, {'error': 'Bad Request', 'message': 'Start and end dates required'})
        
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Generate compliance report
        compliance_data = {
            'reportMetadata': {
                'reportId': f"compliance-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'generatedAt': datetime.utcnow().isoformat(),
                'reportType': report_type,
                'dateRange': {
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat()
                }
            },
            'dataIntegrity': get_data_integrity_report(start_dt, end_dt),
            'systemUptime': get_uptime_compliance(start_dt, end_dt),
            'auditTrail': get_audit_trail_summary(start_dt, end_dt),
            'alertCompliance': get_alert_compliance_metrics(start_dt, end_dt)
        }
        
        # Generate PDF if requested
        if query_params.get('format') == 'pdf':
            pdf_url = generate_compliance_pdf(compliance_data)
            compliance_data['downloadUrl'] = pdf_url
        
        return create_response(200, compliance_data)
    
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_performance_metrics(query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Get system performance metrics"""
    try:
        # Parse time range
        hours = int(query_params.get('hours', 24))
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get CloudWatch metrics
        metrics = {
            'apiLatency': get_api_latency_metrics(start_time, end_time),
            'alertLatency': get_alert_latency_metrics(start_time, end_time),
            'errorRates': get_error_rate_metrics(start_time, end_time),
            'throughput': get_throughput_metrics(start_time, end_time),
            'systemLoad': get_system_load_metrics(start_time, end_time)
        }
        
        # Calculate SLA compliance
        sla_compliance = calculate_sla_compliance(metrics)
        
        return create_response(200, {
            'timeRange': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': hours
            },
            'metrics': metrics,
            'slaCompliance': sla_compliance
        })
    
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_water_quality_analytics(query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Get water quality analytics and trends"""
    try:
        # Parse parameters
        days = int(query_params.get('days', 30))
        device_id = query_params.get('deviceId')
        region = query_params.get('region')
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get water quality data
        wq_data = get_water_quality_data(start_date, end_date, device_id, region)
        
        # Calculate analytics
        analytics = {
            'summary': calculate_wq_summary(wq_data),
            'trends': calculate_wq_trends(wq_data),
            'anomalies': identify_wq_anomalies(wq_data),
            'predictions': generate_wq_predictions(wq_data),
            'compliance': check_wq_compliance(wq_data)
        }
        
        return create_response(200, {
            'timeRange': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'filters': {
                'deviceId': device_id,
                'region': region
            },
            'analytics': analytics,
            'dataPoints': len(wq_data)
        })
    
    except Exception as e:
        logger.error(f"Error getting water quality analytics: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_service_metrics(query_params: Dict[str, str], user_groups: List[str]) -> Dict[str, Any]:
    """Get service request metrics and technician performance"""
    try:
        # Parse parameters
        days = int(query_params.get('days', 30))
        technician_id = query_params.get('technicianId')
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get service metrics
        service_metrics = {
            'requestVolume': get_service_request_volume(start_date, end_date),
            'responseTime': get_service_response_times(start_date, end_date),
            'completionRate': get_service_completion_rate(start_date, end_date),
            'customerSatisfaction': get_customer_satisfaction_metrics(start_date, end_date),
            'technicianPerformance': get_technician_performance_metrics(start_date, end_date, technician_id)
        }
        
        return create_response(200, {
            'timeRange': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'filters': {
                'technicianId': technician_id
            },
            'metrics': service_metrics
        })
    
    except Exception as e:
        logger.error(f"Error getting service metrics: {str(e)}")
        return create_response(500, {'error': 'Internal Server Error', 'message': str(e)})


def get_system_health_metrics() -> Dict[str, Any]:
    """Get current system health status"""
    try:
        # Get CloudWatch metrics for system health
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # Mock system health data
        return {
            'status': 'healthy',
            'uptime': 99.8,
            'activeDevices': 1247,
            'dataIngestionRate': 2.3,  # readings per second
            'alertLatency': 12.5,  # seconds
            'apiResponseTime': 145,  # milliseconds
            'errorRate': 0.02  # percentage
        }
    
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return {'status': 'unknown', 'error': str(e)}


def get_device_fleet_status(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get device fleet status summary"""
    try:
        # Mock device fleet data
        return {
            'totalDevices': 1247,
            'onlineDevices': 1198,
            'offlineDevices': 49,
            'maintenanceRequired': 23,
            'batteryLow': 15,
            'signalWeak': 8,
            'uptimePercentage': 96.1
        }
    
    except Exception as e:
        logger.error(f"Error getting device fleet status: {str(e)}")
        return {}


def get_alert_summary(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get alert summary for time period"""
    try:
        # Mock alert data
        return {
            'totalAlerts': 156,
            'criticalAlerts': 23,
            'warningAlerts': 89,
            'infoAlerts': 44,
            'averageResponseTime': 18.5,  # seconds
            'alertsByType': {
                'water_quality': 89,
                'sensor_fault': 34,
                'device_offline': 23,
                'system_error': 10
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting alert summary: {str(e)}")
        return {}


def get_service_request_summary(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get service request summary"""
    try:
        # Mock service request data
        return {
            'totalRequests': 89,
            'completedRequests': 76,
            'pendingRequests': 8,
            'cancelledRequests': 5,
            'averageResponseTime': 42.3,  # minutes
            'averageCompletionTime': 2.1,  # hours
            'customerSatisfaction': 4.6  # out of 5
        }
    
    except Exception as e:
        logger.error(f"Error getting service request summary: {str(e)}")
        return {}


def get_water_quality_trends(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get water quality trends"""
    try:
        # Mock water quality trends
        return {
            'averageWQI': 78.5,
            'wqiTrend': 'improving',
            'parametersInRange': 94.2,  # percentage
            'anomaliesDetected': 12,
            'topConcerns': [
                {'parameter': 'pH', 'deviation': 2.3},
                {'parameter': 'turbidity', 'deviation': 1.8}
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting water quality trends: {str(e)}")
        return {}


def get_data_integrity_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get data integrity report for compliance"""
    try:
        # Check ledger integrity
        ledger_integrity = verify_ledger_integrity(start_date, end_date)
        
        return {
            'ledgerIntegrity': ledger_integrity,
            'dataCompleteness': 99.7,  # percentage
            'hashChainValid': True,
            'auditTrailComplete': True,
            'backupStatus': 'current',
            'encryptionStatus': 'compliant'
        }
    
    except Exception as e:
        logger.error(f"Error getting data integrity report: {str(e)}")
        return {}


def verify_ledger_integrity(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Verify ledger hash chain integrity"""
    try:
        # This would perform actual hash chain verification
        # For now, return mock data
        return {
            'status': 'valid',
            'entriesVerified': 15847,
            'hashChainIntact': True,
            'lastVerification': datetime.utcnow().isoformat(),
            'anomaliesFound': 0
        }
    
    except Exception as e:
        logger.error(f"Error verifying ledger integrity: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def get_uptime_compliance(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get uptime compliance metrics"""
    try:
        return {
            'targetUptime': 99.5,
            'actualUptime': 99.8,
            'compliant': True,
            'outageMinutes': 14.2,
            'mttr': 8.5,  # mean time to recovery in minutes
            'mtbf': 720  # mean time between failures in hours
        }
    
    except Exception as e:
        logger.error(f"Error getting uptime compliance: {str(e)}")
        return {}


def generate_compliance_pdf(compliance_data: Dict[str, Any]) -> str:
    """Generate PDF compliance report"""
    try:
        # This would generate an actual PDF report
        # For now, return a mock S3 URL
        report_key = f"compliance-reports/{compliance_data['reportMetadata']['reportId']}.pdf"
        return f"https://aquachain-reports.s3.amazonaws.com/{report_key}"
    
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return None


def get_api_latency_metrics(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Get API latency metrics from CloudWatch"""
    try:
        # Mock CloudWatch data
        return {
            'average': 145.2,
            'p50': 120.5,
            'p95': 280.1,
            'p99': 450.3,
            'max': 1200.0
        }
    
    except Exception as e:
        logger.error(f"Error getting API latency metrics: {str(e)}")
        return {}


def calculate_sla_compliance(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate SLA compliance based on metrics"""
    try:
        # Calculate compliance based on requirements
        alert_latency_compliant = metrics.get('alertLatency', {}).get('average', 0) < 30
        api_latency_compliant = metrics.get('apiLatency', {}).get('p95', 0) < 500
        error_rate_compliant = metrics.get('errorRates', {}).get('overall', 0) < 5
        
        return {
            'overall': alert_latency_compliant and api_latency_compliant and error_rate_compliant,
            'alertLatency': {
                'compliant': alert_latency_compliant,
                'target': 30,
                'actual': metrics.get('alertLatency', {}).get('average', 0)
            },
            'apiLatency': {
                'compliant': api_latency_compliant,
                'target': 500,
                'actual': metrics.get('apiLatency', {}).get('p95', 0)
            },
            'errorRate': {
                'compliant': error_rate_compliant,
                'target': 5,
                'actual': metrics.get('errorRates', {}).get('overall', 0)
            }
        }
    
    except Exception as e:
        logger.error(f"Error calculating SLA compliance: {str(e)}")
        return {}


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }


# Additional helper functions would be implemented here for:
# - get_alert_latency_metrics
# - get_error_rate_metrics  
# - get_throughput_metrics
# - get_system_load_metrics
# - get_water_quality_data
# - calculate_wq_summary
# - calculate_wq_trends
# - identify_wq_anomalies
# - generate_wq_predictions
# - check_wq_compliance
# - get_service_request_volume
# - get_service_response_times
# - get_service_completion_rate
# - get_customer_satisfaction_metrics
# - get_technician_performance_metrics
# - get_audit_trail_summary
# - get_alert_compliance_metrics