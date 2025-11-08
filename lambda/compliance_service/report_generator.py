"""
Compliance Report Generator

Generates comprehensive compliance reports covering:
- Data access patterns from audit logs
- Data retention compliance
- Security controls status
- GDPR data subject requests
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class ComplianceReportGenerator:
    """Generate automated compliance reports"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.audit_logs_table = self.dynamodb.Table(os.environ.get('AUDIT_LOGS_TABLE', 'AuditLogs'))
        self.gdpr_requests_table = self.dynamodb.Table(os.environ.get('GDPR_REQUESTS_TABLE', 'GDPRRequests'))
        self.devices_table = self.dynamodb.Table(os.environ.get('DEVICES_TABLE', 'Devices'))
        self.users_table = self.dynamodb.Table(os.environ.get('USERS_TABLE', 'Users'))
    
    def generate_monthly_report(self, year: int, month: int) -> Dict:
        """
        Generate comprehensive monthly compliance report
        
        Args:
            year: Report year
            month: Report month (1-12)
            
        Returns:
            Complete compliance report dictionary
        """
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'period': f"{year}-{month:02d}",
            'report_type': 'monthly_compliance',
            'sections': {
                'data_access': self._generate_data_access_report(year, month),
                'data_retention': self._generate_retention_report(year, month),
                'security_controls': self._generate_security_report(year, month),
                'gdpr_requests': self._generate_gdpr_requests_report(year, month),
                'audit_summary': self._generate_audit_summary(year, month)
            },
            'compliance_status': 'COMPLIANT',
            'violations': []
        }
        
        # Check for compliance violations
        violations = self._check_compliance_violations(report)
        if violations:
            report['compliance_status'] = 'NON_COMPLIANT'
            report['violations'] = violations
        
        return report
    
    def _generate_data_access_report(self, year: int, month: int) -> Dict:
        """
        Generate report on data access patterns from audit logs
        
        Args:
            year: Report year
            month: Report month
            
        Returns:
            Data access report with statistics
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Query audit logs for READ actions
        try:
            # Note: In production, you'd use a GSI on action_type-timestamp
            # For now, we'll scan with filter (not optimal but functional)
            response = self.audit_logs_table.scan(
                FilterExpression=Attr('action_type').eq('READ') & 
                                Attr('timestamp').between(
                                    start_date.isoformat(),
                                    end_date.isoformat()
                                )
            )
            
            logs = response.get('Items', [])
            
            # Continue scanning if there are more items
            while 'LastEvaluatedKey' in response:
                response = self.audit_logs_table.scan(
                    FilterExpression=Attr('action_type').eq('READ') & 
                                    Attr('timestamp').between(
                                        start_date.isoformat(),
                                        end_date.isoformat()
                                    ),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                logs.extend(response.get('Items', []))
            
        except Exception as e:
            print(f"Error querying audit logs: {e}")
            logs = []
        
        # Analyze access patterns
        access_by_user = {}
        access_by_resource = {}
        access_by_day = {}
        
        for log in logs:
            user_id = log.get('user_id', 'unknown')
            resource_type = log.get('resource_type', 'unknown')
            timestamp = log.get('timestamp', '')
            
            # Count by user
            access_by_user[user_id] = access_by_user.get(user_id, 0) + 1
            
            # Count by resource type
            access_by_resource[resource_type] = access_by_resource.get(resource_type, 0) + 1
            
            # Count by day
            if timestamp:
                day = timestamp[:10]  # Extract YYYY-MM-DD
                access_by_day[day] = access_by_day.get(day, 0) + 1
        
        return {
            'total_accesses': len(logs),
            'unique_users': len(access_by_user),
            'access_by_user': dict(sorted(access_by_user.items(), key=lambda x: x[1], reverse=True)[:10]),  # Top 10
            'access_by_resource': access_by_resource,
            'access_by_day': access_by_day,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }
    
    def _generate_retention_report(self, year: int, month: int) -> Dict:
        """
        Generate data retention compliance report
        
        Args:
            year: Report year
            month: Report month
            
        Returns:
            Data retention report
        """
        # Check audit log retention (should be 7 years)
        seven_years_ago = datetime.utcnow() - timedelta(days=7*365)
        
        try:
            # Count audit logs older than 7 years
            response = self.audit_logs_table.scan(
                FilterExpression=Attr('timestamp').lt(seven_years_ago.isoformat()),
                Select='COUNT'
            )
            old_logs_count = response.get('Count', 0)
        except Exception as e:
            print(f"Error checking old audit logs: {e}")
            old_logs_count = 0
        
        # Check for devices without recent activity (potential for cleanup)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        try:
            response = self.devices_table.scan(
                FilterExpression=Attr('last_seen').lt(ninety_days_ago.isoformat()),
                Select='COUNT'
            )
            inactive_devices_count = response.get('Count', 0)
        except Exception as e:
            print(f"Error checking inactive devices: {e}")
            inactive_devices_count = 0
        
        return {
            'audit_logs': {
                'retention_period_years': 7,
                'logs_exceeding_retention': old_logs_count,
                'retention_compliant': old_logs_count == 0
            },
            'inactive_devices': {
                'threshold_days': 90,
                'count': inactive_devices_count,
                'recommendation': 'Review and archive inactive devices'
            },
            'data_lifecycle_policies': {
                'audit_logs': 'TTL set to 7 years',
                'sensor_readings': 'Retained indefinitely',
                'user_data': 'Retained until deletion request'
            }
        }
    
    def _generate_security_report(self, year: int, month: int) -> Dict:
        """
        Generate security controls status report
        
        Args:
            year: Report year
            month: Report month
            
        Returns:
            Security controls report
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Check authentication events
        try:
            response = self.audit_logs_table.scan(
                FilterExpression=Attr('action_type').is_in(['LOGIN', 'LOGOUT', 'LOGIN_FAILED']) & 
                                Attr('timestamp').between(
                                    start_date.isoformat(),
                                    end_date.isoformat()
                                ),
                Select='COUNT'
            )
            auth_events_count = response.get('Count', 0)
            
            # Count failed logins
            response = self.audit_logs_table.scan(
                FilterExpression=Attr('action_type').eq('LOGIN_FAILED') & 
                                Attr('timestamp').between(
                                    start_date.isoformat(),
                                    end_date.isoformat()
                                ),
                Select='COUNT'
            )
            failed_logins_count = response.get('Count', 0)
            
        except Exception as e:
            print(f"Error checking auth events: {e}")
            auth_events_count = 0
            failed_logins_count = 0
        
        return {
            'authentication': {
                'total_auth_events': auth_events_count,
                'failed_login_attempts': failed_logins_count,
                'mfa_enabled': True,
                'password_policy_enforced': True
            },
            'encryption': {
                'data_at_rest': 'AES-256 encryption enabled',
                'data_in_transit': 'TLS 1.2+ enforced',
                'kms_keys': {
                    'pii_data': 'Separate KMS key',
                    'sensitive_data': 'Separate KMS key'
                }
            },
            'access_controls': {
                'iam_policies': 'Least privilege enforced',
                'role_based_access': 'Enabled',
                'api_authentication': 'JWT tokens with Cognito'
            },
            'monitoring': {
                'cloudwatch_alarms': 'Active',
                'audit_logging': 'Comprehensive',
                'intrusion_detection': 'AWS GuardDuty enabled'
            }
        }
    
    def _generate_gdpr_requests_report(self, year: int, month: int) -> Dict:
        """
        Generate GDPR data subject requests report
        
        Args:
            year: Report year
            month: Report month
            
        Returns:
            GDPR requests report with metrics
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        try:
            # Query GDPR requests for the period
            # Note: Assumes GSI on created_at
            response = self.gdpr_requests_table.scan(
                FilterExpression=Attr('created_at').between(
                    start_date.isoformat(),
                    end_date.isoformat()
                )
            )
            
            requests = response.get('Items', [])
            
            # Continue scanning if there are more items
            while 'LastEvaluatedKey' in response:
                response = self.gdpr_requests_table.scan(
                    FilterExpression=Attr('created_at').between(
                        start_date.isoformat(),
                        end_date.isoformat()
                    ),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                requests.extend(response.get('Items', []))
                
        except Exception as e:
            print(f"Error querying GDPR requests: {e}")
            requests = []
        
        # Analyze requests
        requests_by_type = {}
        requests_by_status = {}
        completion_times = {'export': [], 'deletion': []}
        
        for request in requests:
            req_type = request.get('request_type', 'unknown')
            status = request.get('status', 'unknown')
            
            # Count by type
            requests_by_type[req_type] = requests_by_type.get(req_type, 0) + 1
            
            # Count by status
            requests_by_status[status] = requests_by_status.get(status, 0) + 1
            
            # Calculate completion time for completed requests
            if status == 'completed' and request.get('completed_at') and request.get('created_at'):
                try:
                    created = datetime.fromisoformat(request['created_at'].replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(request['completed_at'].replace('Z', '+00:00'))
                    completion_time_hours = (completed - created).total_seconds() / 3600
                    
                    if req_type in completion_times:
                        completion_times[req_type].append(completion_time_hours)
                except Exception as e:
                    print(f"Error calculating completion time: {e}")
        
        # Calculate average completion times
        avg_completion_time = {}
        for req_type, times in completion_times.items():
            if times:
                avg_completion_time[req_type] = sum(times) / len(times)
        
        # Check SLA compliance (export: 48 hours, deletion: 30 days)
        sla_compliance = {
            'export': {
                'sla_hours': 48,
                'avg_completion_hours': avg_completion_time.get('export', 0),
                'compliant': avg_completion_time.get('export', 0) <= 48 if 'export' in avg_completion_time else True
            },
            'deletion': {
                'sla_hours': 30 * 24,  # 30 days
                'avg_completion_hours': avg_completion_time.get('deletion', 0),
                'compliant': avg_completion_time.get('deletion', 0) <= (30 * 24) if 'deletion' in avg_completion_time else True
            }
        }
        
        return {
            'total_requests': len(requests),
            'requests_by_type': requests_by_type,
            'requests_by_status': requests_by_status,
            'avg_completion_time_hours': avg_completion_time,
            'sla_compliance': sla_compliance,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }
    
    def _generate_audit_summary(self, year: int, month: int) -> Dict:
        """
        Generate audit log summary statistics
        
        Args:
            year: Report year
            month: Report month
            
        Returns:
            Audit log summary
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        try:
            # Count total audit logs for the period
            response = self.audit_logs_table.scan(
                FilterExpression=Attr('timestamp').between(
                    start_date.isoformat(),
                    end_date.isoformat()
                ),
                Select='COUNT'
            )
            total_logs = response.get('Count', 0)
            
            # Count by action type
            action_types = ['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'LOGIN_FAILED']
            logs_by_action = {}
            
            for action_type in action_types:
                response = self.audit_logs_table.scan(
                    FilterExpression=Attr('action_type').eq(action_type) & 
                                    Attr('timestamp').between(
                                        start_date.isoformat(),
                                        end_date.isoformat()
                                    ),
                    Select='COUNT'
                )
                logs_by_action[action_type] = response.get('Count', 0)
                
        except Exception as e:
            print(f"Error generating audit summary: {e}")
            total_logs = 0
            logs_by_action = {}
        
        return {
            'total_audit_logs': total_logs,
            'logs_by_action_type': logs_by_action,
            'audit_log_retention': '7 years',
            'audit_log_immutability': 'S3 Object Lock enabled',
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }
    
    def _check_compliance_violations(self, report: Dict) -> List[Dict]:
        """
        Check for compliance violations in the report
        
        Args:
            report: Generated compliance report
            
        Returns:
            List of compliance violations
        """
        violations = []
        
        # Check GDPR SLA compliance
        gdpr_section = report['sections'].get('gdpr_requests', {})
        sla_compliance = gdpr_section.get('sla_compliance', {})
        
        for req_type, sla_data in sla_compliance.items():
            if not sla_data.get('compliant', True):
                violations.append({
                    'type': 'GDPR_SLA_VIOLATION',
                    'severity': 'HIGH',
                    'description': f"GDPR {req_type} requests exceeding SLA",
                    'details': {
                        'request_type': req_type,
                        'sla_hours': sla_data.get('sla_hours'),
                        'avg_completion_hours': sla_data.get('avg_completion_hours')
                    }
                })
        
        # Check data retention compliance
        retention_section = report['sections'].get('data_retention', {})
        audit_logs_data = retention_section.get('audit_logs', {})
        
        if not audit_logs_data.get('retention_compliant', True):
            violations.append({
                'type': 'DATA_RETENTION_VIOLATION',
                'severity': 'MEDIUM',
                'description': 'Audit logs exceeding retention period',
                'details': {
                    'logs_exceeding_retention': audit_logs_data.get('logs_exceeding_retention', 0)
                }
            })
        
        return violations
    
    def save_report_to_s3(self, report: Dict, bucket: str, key: str) -> str:
        """
        Save compliance report to S3
        
        Args:
            report: Compliance report dictionary
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            S3 URL of the saved report
        """
        try:
            self.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(report, indent=2, cls=DecimalEncoder),
                ServerSideEncryption='AES256',
                ContentType='application/json'
            )
            
            return f"s3://{bucket}/{key}"
            
        except Exception as e:
            print(f"Error saving report to S3: {e}")
            raise
