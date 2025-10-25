"""
Compliance Violation Detector

Detects and alerts on compliance violations based on defined rules
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class ComplianceViolationDetector:
    """Detect compliance violations and send alerts"""
    
    # Violation severity levels
    SEVERITY_CRITICAL = "CRITICAL"
    SEVERITY_HIGH = "HIGH"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_LOW = "LOW"
    
    # Compliance rules
    RULES = {
        "GDPR_EXPORT_SLA": {
            "name": "GDPR Export SLA Compliance",
            "description": "GDPR data export requests must complete within 48 hours",
            "threshold_hours": 48,
            "severity": SEVERITY_HIGH
        },
        "GDPR_DELETION_SLA": {
            "name": "GDPR Deletion SLA Compliance",
            "description": "GDPR data deletion requests must complete within 30 days",
            "threshold_hours": 30 * 24,
            "severity": SEVERITY_HIGH
        },
        "AUDIT_LOG_RETENTION": {
            "name": "Audit Log Retention Compliance",
            "description": "Audit logs must be retained for 7 years",
            "retention_years": 7,
            "severity": SEVERITY_MEDIUM
        },
        "FAILED_LOGIN_THRESHOLD": {
            "name": "Failed Login Attempts Threshold",
            "description": "Excessive failed login attempts may indicate security issue",
            "threshold_count": 100,
            "severity": SEVERITY_MEDIUM
        },
        "DATA_ACCESS_ANOMALY": {
            "name": "Data Access Anomaly Detection",
            "description": "Unusual data access patterns detected",
            "threshold_multiplier": 3.0,  # 3x normal access
            "severity": SEVERITY_HIGH
        }
    }
    
    def __init__(self):
        self.sns = boto3.client('sns')
        self.dynamodb = boto3.resource('dynamodb')
        self.cloudwatch = boto3.client('cloudwatch')
        self.compliance_topic_arn = os.environ.get('COMPLIANCE_ALERTS_TOPIC_ARN')
    
    def check_violations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check compliance report for violations
        
        Args:
            report: Compliance report dictionary
            
        Returns:
            List of detected violations
        """
        violations = []
        
        # Check GDPR SLA violations
        violations.extend(self._check_gdpr_sla_violations(report))
        
        # Check data retention violations
        violations.extend(self._check_retention_violations(report))
        
        # Check security violations
        violations.extend(self._check_security_violations(report))
        
        # Check data access anomalies
        violations.extend(self._check_access_anomalies(report))
        
        return violations
    
    def _check_gdpr_sla_violations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for GDPR SLA violations"""
        violations = []
        
        gdpr_section = report.get('sections', {}).get('gdpr_requests', {})
        sla_compliance = gdpr_section.get('sla_compliance', {})
        
        # Check export SLA
        export_sla = sla_compliance.get('export', {})
        if not export_sla.get('compliant', True):
            violations.append({
                'rule_id': 'GDPR_EXPORT_SLA',
                'rule_name': self.RULES['GDPR_EXPORT_SLA']['name'],
                'severity': self.RULES['GDPR_EXPORT_SLA']['severity'],
                'description': self.RULES['GDPR_EXPORT_SLA']['description'],
                'details': {
                    'sla_hours': export_sla.get('sla_hours'),
                    'avg_completion_hours': export_sla.get('avg_completion_hours'),
                    'exceeded_by_hours': export_sla.get('avg_completion_hours', 0) - export_sla.get('sla_hours', 48)
                },
                'detected_at': datetime.utcnow().isoformat()
            })
        
        # Check deletion SLA
        deletion_sla = sla_compliance.get('deletion', {})
        if not deletion_sla.get('compliant', True):
            violations.append({
                'rule_id': 'GDPR_DELETION_SLA',
                'rule_name': self.RULES['GDPR_DELETION_SLA']['name'],
                'severity': self.RULES['GDPR_DELETION_SLA']['severity'],
                'description': self.RULES['GDPR_DELETION_SLA']['description'],
                'details': {
                    'sla_hours': deletion_sla.get('sla_hours'),
                    'avg_completion_hours': deletion_sla.get('avg_completion_hours'),
                    'exceeded_by_hours': deletion_sla.get('avg_completion_hours', 0) - deletion_sla.get('sla_hours', 720)
                },
                'detected_at': datetime.utcnow().isoformat()
            })
        
        return violations
    
    def _check_retention_violations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for data retention violations"""
        violations = []
        
        retention_section = report.get('sections', {}).get('data_retention', {})
        audit_logs_data = retention_section.get('audit_logs', {})
        
        if not audit_logs_data.get('retention_compliant', True):
            violations.append({
                'rule_id': 'AUDIT_LOG_RETENTION',
                'rule_name': self.RULES['AUDIT_LOG_RETENTION']['name'],
                'severity': self.RULES['AUDIT_LOG_RETENTION']['severity'],
                'description': self.RULES['AUDIT_LOG_RETENTION']['description'],
                'details': {
                    'logs_exceeding_retention': audit_logs_data.get('logs_exceeding_retention', 0),
                    'retention_period_years': audit_logs_data.get('retention_period_years', 7)
                },
                'detected_at': datetime.utcnow().isoformat()
            })
        
        return violations
    
    def _check_security_violations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for security-related violations"""
        violations = []
        
        security_section = report.get('sections', {}).get('security_controls', {})
        auth_data = security_section.get('authentication', {})
        
        # Check for excessive failed login attempts
        failed_logins = auth_data.get('failed_login_attempts', 0)
        threshold = self.RULES['FAILED_LOGIN_THRESHOLD']['threshold_count']
        
        if failed_logins > threshold:
            violations.append({
                'rule_id': 'FAILED_LOGIN_THRESHOLD',
                'rule_name': self.RULES['FAILED_LOGIN_THRESHOLD']['name'],
                'severity': self.RULES['FAILED_LOGIN_THRESHOLD']['severity'],
                'description': self.RULES['FAILED_LOGIN_THRESHOLD']['description'],
                'details': {
                    'failed_login_attempts': failed_logins,
                    'threshold': threshold,
                    'exceeded_by': failed_logins - threshold
                },
                'detected_at': datetime.utcnow().isoformat()
            })
        
        return violations
    
    def _check_access_anomalies(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for data access anomalies"""
        violations = []
        
        access_section = report.get('sections', {}).get('data_access', {})
        access_by_user = access_section.get('access_by_user', {})
        
        if not access_by_user:
            return violations
        
        # Calculate average access count
        access_counts = list(access_by_user.values())
        avg_access = sum(access_counts) / len(access_counts) if access_counts else 0
        
        # Check for users with anomalous access patterns
        threshold_multiplier = self.RULES['DATA_ACCESS_ANOMALY']['threshold_multiplier']
        anomalous_users = []
        
        for user_id, access_count in access_by_user.items():
            if access_count > avg_access * threshold_multiplier:
                anomalous_users.append({
                    'user_id': user_id,
                    'access_count': access_count,
                    'avg_access': avg_access,
                    'multiplier': access_count / avg_access if avg_access > 0 else 0
                })
        
        if anomalous_users:
            violations.append({
                'rule_id': 'DATA_ACCESS_ANOMALY',
                'rule_name': self.RULES['DATA_ACCESS_ANOMALY']['name'],
                'severity': self.RULES['DATA_ACCESS_ANOMALY']['severity'],
                'description': self.RULES['DATA_ACCESS_ANOMALY']['description'],
                'details': {
                    'anomalous_users': anomalous_users,
                    'threshold_multiplier': threshold_multiplier,
                    'avg_access_count': avg_access
                },
                'detected_at': datetime.utcnow().isoformat()
            })
        
        return violations
    
    def send_alert(self, violations: List[Dict[str, Any]], report_period: str) -> None:
        """
        Send SNS alert for compliance violations
        
        Args:
            violations: List of detected violations
            report_period: Report period (e.g., "2025-10")
        """
        if not violations:
            print("No violations detected, skipping alert")
            return
        
        if not self.compliance_topic_arn:
            print("WARNING: COMPLIANCE_ALERTS_TOPIC_ARN not set, cannot send alerts")
            return
        
        # Group violations by severity
        violations_by_severity = {}
        for violation in violations:
            severity = violation.get('severity', 'UNKNOWN')
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []
            violations_by_severity[severity].append(violation)
        
        # Create alert message
        subject = f"🚨 Compliance Violations Detected - {report_period}"
        
        message_lines = [
            f"Compliance Violations Detected for Period: {report_period}",
            f"Total Violations: {len(violations)}",
            f"Detection Time: {datetime.utcnow().isoformat()}",
            "",
            "=" * 80,
            ""
        ]
        
        # Add violations by severity
        for severity in [self.SEVERITY_CRITICAL, self.SEVERITY_HIGH, self.SEVERITY_MEDIUM, self.SEVERITY_LOW]:
            severity_violations = violations_by_severity.get(severity, [])
            if severity_violations:
                message_lines.append(f"{severity} SEVERITY ({len(severity_violations)} violations):")
                message_lines.append("-" * 80)
                
                for violation in severity_violations:
                    message_lines.append(f"  Rule: {violation['rule_name']}")
                    message_lines.append(f"  Description: {violation['description']}")
                    message_lines.append(f"  Details: {json.dumps(violation['details'], indent=4, cls=DecimalEncoder)}")
                    message_lines.append("")
                
                message_lines.append("")
        
        message_lines.extend([
            "=" * 80,
            "",
            "Action Required:",
            "1. Review the violations listed above",
            "2. Investigate root causes",
            "3. Implement corrective actions",
            "4. Document remediation steps",
            "",
            "This alert was generated automatically by the AquaChain Compliance System."
        ])
        
        message = "\n".join(message_lines)
        
        try:
            # Send SNS notification
            response = self.sns.publish(
                TopicArn=self.compliance_topic_arn,
                Subject=subject,
                Message=message,
                MessageAttributes={
                    'severity': {
                        'DataType': 'String',
                        'StringValue': self._get_highest_severity(violations)
                    },
                    'violation_count': {
                        'DataType': 'Number',
                        'StringValue': str(len(violations))
                    },
                    'report_period': {
                        'DataType': 'String',
                        'StringValue': report_period
                    }
                }
            )
            
            print(f"Alert sent successfully. MessageId: {response['MessageId']}")
            
            # Also publish CloudWatch metric
            self._publish_violation_metrics(violations, report_period)
            
        except Exception as e:
            print(f"Error sending alert: {str(e)}")
            raise
    
    def _get_highest_severity(self, violations: List[Dict[str, Any]]) -> str:
        """Get the highest severity level from violations"""
        severity_order = [
            self.SEVERITY_CRITICAL,
            self.SEVERITY_HIGH,
            self.SEVERITY_MEDIUM,
            self.SEVERITY_LOW
        ]
        
        for severity in severity_order:
            if any(v.get('severity') == severity for v in violations):
                return severity
        
        return 'UNKNOWN'
    
    def _publish_violation_metrics(self, violations: List[Dict[str, Any]], report_period: str) -> None:
        """Publish violation metrics to CloudWatch"""
        try:
            # Count violations by severity
            severity_counts = {}
            for violation in violations:
                severity = violation.get('severity', 'UNKNOWN')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Publish metrics
            metric_data = [
                {
                    'MetricName': 'ComplianceViolations',
                    'Value': len(violations),
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'ReportPeriod', 'Value': report_period}
                    ]
                }
            ]
            
            # Add metrics by severity
            for severity, count in severity_counts.items():
                metric_data.append({
                    'MetricName': 'ComplianceViolations',
                    'Value': count,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'ReportPeriod', 'Value': report_period},
                        {'Name': 'Severity', 'Value': severity}
                    ]
                })
            
            self.cloudwatch.put_metric_data(
                Namespace='AquaChain/Compliance',
                MetricData=metric_data
            )
            
            print(f"Published {len(metric_data)} violation metrics to CloudWatch")
            
        except Exception as e:
            print(f"Error publishing metrics: {str(e)}")
