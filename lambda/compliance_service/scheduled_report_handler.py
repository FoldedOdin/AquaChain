"""
Scheduled Compliance Report Handler

Lambda function triggered monthly by EventBridge to generate compliance reports
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from report_generator import ComplianceReportGenerator
from violation_detector import ComplianceViolationDetector


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate monthly compliance report and upload to S3
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
        
    Returns:
        Response with report location
    """
    print(f"Starting compliance report generation: {json.dumps(event)}")
    
    # Get current date for report
    now = datetime.utcnow()
    
    # Generate report for previous month
    if now.month == 1:
        report_year = now.year - 1
        report_month = 12
    else:
        report_year = now.year
        report_month = now.month - 1
    
    # Allow override from event for testing
    if 'year' in event and 'month' in event:
        report_year = int(event['year'])
        report_month = int(event['month'])
    
    try:
        # Initialize report generator
        generator = ComplianceReportGenerator()
        
        # Generate comprehensive report
        print(f"Generating compliance report for {report_year}-{report_month:02d}")
        report = generator.generate_monthly_report(report_year, report_month)
        
        # Save to S3
        bucket = os.environ.get('COMPLIANCE_REPORTS_BUCKET')
        if not bucket:
            raise ValueError("COMPLIANCE_REPORTS_BUCKET environment variable not set")
        
        report_key = f"compliance-reports/{report_year}/{report_month:02d}/monthly-report-{now.isoformat()}.json"
        
        print(f"Saving report to s3://{bucket}/{report_key}")
        s3_url = generator.save_report_to_s3(report, bucket, report_key)
        
        # Check for compliance violations
        detector = ComplianceViolationDetector()
        violations = detector.check_violations(report)
        
        # Update report with violations
        if violations:
            report['compliance_status'] = 'NON_COMPLIANT'
            report['violations'] = violations
        else:
            report['compliance_status'] = 'COMPLIANT'
            report['violations'] = []
        
        # Re-save report with violation data
        generator.save_report_to_s3(report, bucket, report_key)
        
        # Log compliance status
        compliance_status = report.get('compliance_status', 'UNKNOWN')
        
        print(f"Report generated successfully. Compliance status: {compliance_status}")
        
        if violations:
            print(f"WARNING: {len(violations)} compliance violations detected:")
            for violation in violations:
                print(f"  - {violation['rule_name']}: {violation['description']}")
            
            # Send alert for violations
            try:
                detector.send_alert(violations, f"{report_year}-{report_month:02d}")
                print("Compliance violation alert sent successfully")
            except Exception as alert_error:
                print(f"Error sending violation alert: {str(alert_error)}")
                # Don't fail the entire function if alert fails
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Compliance report generated successfully',
                'report_location': s3_url,
                'report_period': f"{report_year}-{report_month:02d}",
                'compliance_status': compliance_status,
                'violations_count': len(violations)
            })
        }
        
    except Exception as e:
        print(f"Error generating compliance report: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to generate compliance report',
                'message': str(e)
            })
        }
