"""
Compliance API Handler

Provides REST API endpoints for compliance reporting
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any
from report_generator import ComplianceReportGenerator, DecimalEncoder


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API Gateway requests for compliance endpoints
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    print(f"Compliance API request: {json.dumps(event)}")
    
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    path_parameters = event.get('pathParameters', {}) or {}
    query_parameters = event.get('queryStringParameters', {}) or {}
    
    try:
        # Route to appropriate handler
        if path == '/compliance/reports' and http_method == 'GET':
            return handle_list_reports(query_parameters)
        
        elif path.startswith('/compliance/reports/') and http_method == 'GET':
            # Extract year and month from path
            parts = path.split('/')
            if len(parts) >= 5:
                year = int(parts[3])
                month = int(parts[4])
                return handle_get_report(year, month)
        
        elif path == '/compliance/reports/generate' and http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return handle_generate_report(body)
        
        elif path == '/compliance/metrics/summary' and http_method == 'GET':
            return handle_metrics_summary()
        
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'Endpoint not found: {http_method} {path}'
                })
            }
    
    except Exception as e:
        print(f"Error handling request: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }


def handle_list_reports(query_params: Dict[str, str]) -> Dict[str, Any]:
    """List recent compliance reports from S3"""
    s3 = boto3.client('s3')
    bucket = os.environ.get('COMPLIANCE_REPORTS_BUCKET')
    
    if not bucket:
        raise ValueError("COMPLIANCE_REPORTS_BUCKET not configured")
    
    limit = int(query_params.get('limit', '12'))
    
    try:
        # List objects in compliance-reports/ prefix
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix='compliance-reports/',
            MaxKeys=100
        )
        
        reports = []
        
        # Get the most recent reports
        objects = sorted(
            response.get('Contents', []),
            key=lambda x: x['LastModified'],
            reverse=True
        )[:limit]
        
        for obj in objects:
            try:
                # Download and parse report
                report_obj = s3.get_object(Bucket=bucket, Key=obj['Key'])
                report_data = json.loads(report_obj['Body'].read().decode('utf-8'))
                
                # Add metadata
                report_data['s3_key'] = obj['Key']
                report_data['last_modified'] = obj['LastModified'].isoformat()
                
                reports.append(report_data)
            except Exception as e:
                print(f"Error loading report {obj['Key']}: {str(e)}")
                continue
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'reports': reports,
                'count': len(reports)
            }, cls=DecimalEncoder)
        }
    
    except Exception as e:
        print(f"Error listing reports: {str(e)}")
        raise


def handle_get_report(year: int, month: int) -> Dict[str, Any]:
    """Get a specific compliance report"""
    s3 = boto3.client('s3')
    bucket = os.environ.get('COMPLIANCE_REPORTS_BUCKET')
    
    if not bucket:
        raise ValueError("COMPLIANCE_REPORTS_BUCKET not configured")
    
    try:
        # List reports for the specified period
        prefix = f"compliance-reports/{year}/{month:02d}/"
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=10
        )
        
        objects = response.get('Contents', [])
        
        if not objects:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'No report found for {year}-{month:02d}'
                })
            }
        
        # Get the most recent report for this period
        latest_obj = sorted(objects, key=lambda x: x['LastModified'], reverse=True)[0]
        
        # Download report
        report_obj = s3.get_object(Bucket=bucket, Key=latest_obj['Key'])
        report_data = json.loads(report_obj['Body'].read().decode('utf-8'))
        
        # Add metadata
        report_data['s3_key'] = latest_obj['Key']
        report_data['last_modified'] = latest_obj['LastModified'].isoformat()
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(report_data, cls=DecimalEncoder)
        }
    
    except Exception as e:
        print(f"Error getting report: {str(e)}")
        raise


def handle_generate_report(body: Dict[str, Any]) -> Dict[str, Any]:
    """Manually trigger report generation"""
    # Get current date for report
    now = datetime.utcnow()
    
    # Use provided year/month or default to previous month
    if 'year' in body and 'month' in body:
        report_year = int(body['year'])
        report_month = int(body['month'])
    else:
        if now.month == 1:
            report_year = now.year - 1
            report_month = 12
        else:
            report_year = now.year
            report_month = now.month - 1
    
    try:
        # Generate report
        generator = ComplianceReportGenerator()
        report = generator.generate_monthly_report(report_year, report_month)
        
        # Save to S3
        bucket = os.environ.get('COMPLIANCE_REPORTS_BUCKET')
        if not bucket:
            raise ValueError("COMPLIANCE_REPORTS_BUCKET not configured")
        
        report_key = f"compliance-reports/{report_year}/{report_month:02d}/manual-report-{now.isoformat()}.json"
        s3_url = generator.save_report_to_s3(report, bucket, report_key)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Report generated successfully',
                'report_location': s3_url,
                'report_period': f"{report_year}-{report_month:02d}",
                'compliance_status': report.get('compliance_status', 'UNKNOWN')
            })
        }
    
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise


def handle_metrics_summary() -> Dict[str, Any]:
    """Get compliance metrics summary"""
    s3 = boto3.client('s3')
    bucket = os.environ.get('COMPLIANCE_REPORTS_BUCKET')
    
    if not bucket:
        raise ValueError("COMPLIANCE_REPORTS_BUCKET not configured")
    
    try:
        # List all reports
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix='compliance-reports/',
            MaxKeys=100
        )
        
        total_reports = 0
        compliant_reports = 0
        total_violations = 0
        violations_by_severity = {}
        
        for obj in response.get('Contents', []):
            try:
                # Download and parse report
                report_obj = s3.get_object(Bucket=bucket, Key=obj['Key'])
                report_data = json.loads(report_obj['Body'].read().decode('utf-8'))
                
                total_reports += 1
                
                if report_data.get('compliance_status') == 'COMPLIANT':
                    compliant_reports += 1
                
                violations = report_data.get('violations', [])
                total_violations += len(violations)
                
                for violation in violations:
                    severity = violation.get('severity', 'UNKNOWN')
                    violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
            
            except Exception as e:
                print(f"Error processing report {obj['Key']}: {str(e)}")
                continue
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'total_reports': total_reports,
                'compliant_reports': compliant_reports,
                'total_violations': total_violations,
                'violations_by_severity': violations_by_severity
            })
        }
    
    except Exception as e:
        print(f"Error getting metrics summary: {str(e)}")
        raise


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
