"""
Comprehensive audit logging system for AquaChain.
Implements audit trail for all user actions and sensitive operations.
Requirements: 15.5
"""

import json
import boto3
import logging
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from botocore.exceptions import ClientError

from structured_logger import get_logger

logger = get_logger(__name__, service='audit-logger')

class AuditEventType(Enum):
    """Enumeration of audit event types"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    USER_PROFILE_UPDATE = "user_profile_update"
    DEVICE_ACCESS = "device_access"
    DATA_EXPORT = "data_export"
    SERVICE_REQUEST_CREATE = "service_request_create"
    SERVICE_REQUEST_UPDATE = "service_request_update"
    ADMIN_ACTION = "admin_action"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SECURITY_VIOLATION = "security_violation"
    DATA_MODIFICATION = "data_modification"
    COMPLIANCE_REPORT_GENERATION = "compliance_report_generation"
    LEDGER_ACCESS = "ledger_access"
    HASH_CHAIN_VERIFICATION = "hash_chain_verification"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: str
    user_id: Optional[str]
    user_role: Optional[str]
    source_ip: str
    user_agent: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    outcome: str  # success, failure, partial
    details: Dict[str, Any]
    request_id: Optional[str]
    session_id: Optional[str]
    compliance_tags: List[str]
    data_classification: str  # public, internal, confidential, restricted
    retention_period: int  # days
    hash_signature: Optional[str] = None

class AuditLogger:
    """
    Comprehensive audit logging system.
    Implements requirement 15.5 for audit trail and compliance tracking.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('logs', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
        
        # Initialize tables and resources
        self.audit_table = self.dynamodb.Table('aquachain-audit-logs')
        self.compliance_table = self.dynamodb.Table('aquachain-compliance-tracking')
        self.audit_bucket = 'aquachain-audit-archive'
        self.log_group = '/aws/lambda/aquachain-audit'
        
        # KMS key for audit log signing
        self.audit_signing_key = 'arn:aws:kms:us-east-1:123456789012:key/audit-signing-key'
    
    def log_event(self, event: AuditEvent) -> bool:
        """
        Log audit event to multiple destinations.
        """
        try:
            # Generate hash signature for integrity
            event.hash_signature = self._generate_event_signature(event)
            
            # Store in DynamoDB for real-time access
            self._store_in_dynamodb(event)
            
            # Store in CloudWatch Logs for monitoring
            self._store_in_cloudwatch(event)
            
            # Archive in S3 for long-term retention
            self._archive_in_s3(event)
            
            # Update compliance metrics
            self._update_compliance_metrics(event)
            
            # Trigger alerts for critical events
            if event.severity == AuditSeverity.CRITICAL:
                self._trigger_security_alert(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            # Fallback to CloudWatch Logs only
            try:
                self._store_in_cloudwatch(event)
            except Exception as fallback_error:
                logger.error(f"Fallback audit logging failed: {fallback_error}")
            return False
    
    def _generate_event_signature(self, event: AuditEvent) -> str:
        """Generate cryptographic signature for audit event integrity"""
        try:
            # Create canonical string representation
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp,
                'user_id': event.user_id,
                'action': event.action,
                'outcome': event.outcome,
                'details': json.dumps(event.details, sort_keys=True)
            }
            
            canonical_string = json.dumps(event_data, sort_keys=True)
            
            # Generate HMAC signature using KMS
            response = self.kms.generate_mac(
                KeyId=self.audit_signing_key,
                Message=canonical_string.encode('utf-8'),
                MacAlgorithm='HMAC_SHA_256'
            )
            
            return response['Mac'].hex()
            
        except ClientError as e:
            logger.error(f"Error generating event signature: {e}")
            # Fallback to local HMAC
            secret_key = "audit-fallback-key"  # Should be from secure storage
            return hmac.new(
                secret_key.encode('utf-8'),
                canonical_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
    
    def _store_in_dynamodb(self, event: AuditEvent) -> None:
        """Store audit event in DynamoDB for real-time access"""
        try:
            # Convert event to DynamoDB item
            item = asdict(event)
            item['event_type'] = event.event_type.value
            item['severity'] = event.severity.value
            
            # Add TTL based on retention period
            ttl_timestamp = int(datetime.now(timezone.utc).timestamp()) + (event.retention_period * 24 * 3600)
            item['ttl'] = ttl_timestamp
            
            # Store with conditional write to prevent duplicates
            self.audit_table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(event_id)'
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                logger.error(f"Error storing audit event in DynamoDB: {e}")
                raise
    
    def _store_in_cloudwatch(self, event: AuditEvent) -> None:
        """Store audit event in CloudWatch Logs"""
        try:
            log_entry = {
                'timestamp': event.timestamp,
                'level': 'AUDIT',
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'severity': event.severity.value,
                'user_id': event.user_id,
                'action': event.action,
                'outcome': event.outcome,
                'source_ip': event.source_ip,
                'details': event.details
            }
            
            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"audit-{datetime.now().strftime('%Y-%m-%d')}",
                logEvents=[
                    {
                        'timestamp': int(datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).timestamp() * 1000),
                        'message': json.dumps(log_entry)
                    }
                ]
            )
            
        except ClientError as e:
            logger.error(f"Error storing audit event in CloudWatch: {e}")
            raise
    
    def _archive_in_s3(self, event: AuditEvent) -> None:
        """Archive audit event in S3 for long-term retention"""
        try:
            # Create S3 key with date partitioning
            date_partition = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).strftime('%Y/%m/%d')
            s3_key = f"audit-logs/{date_partition}/{event.event_id}.json"
            
            # Prepare event data for archival
            archive_data = asdict(event)
            archive_data['event_type'] = event.event_type.value
            archive_data['severity'] = event.severity.value
            
            # Store in S3 with server-side encryption
            self.s3.put_object(
                Bucket=self.audit_bucket,
                Key=s3_key,
                Body=json.dumps(archive_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=self.audit_signing_key,
                Metadata={
                    'event-type': event.event_type.value,
                    'severity': event.severity.value,
                    'data-classification': event.data_classification
                }
            )
            
        except ClientError as e:
            logger.error(f"Error archiving audit event in S3: {e}")
            # Don't raise - archival failure shouldn't block operations
    
    def _update_compliance_metrics(self, event: AuditEvent) -> None:
        """Update compliance tracking metrics"""
        try:
            current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            # Update daily metrics
            self.compliance_table.update_item(
                Key={
                    'metric_type': 'daily_events',
                    'date': current_date
                },
                UpdateExpression='ADD event_count :inc, #event_type :inc',
                ExpressionAttributeNames={
                    '#event_type': event.event_type.value
                },
                ExpressionAttributeValues={
                    ':inc': 1
                }
            )
            
            # Update severity metrics
            self.compliance_table.update_item(
                Key={
                    'metric_type': 'severity_counts',
                    'date': current_date
                },
                UpdateExpression='ADD #severity :inc',
                ExpressionAttributeNames={
                    '#severity': event.severity.value
                },
                ExpressionAttributeValues={
                    ':inc': 1
                }
            )
            
            # Update compliance tag metrics
            for tag in event.compliance_tags:
                self.compliance_table.update_item(
                    Key={
                        'metric_type': 'compliance_tags',
                        'date': current_date
                    },
                    UpdateExpression='ADD #tag :inc',
                    ExpressionAttributeNames={
                        '#tag': tag
                    },
                    ExpressionAttributeValues={
                        ':inc': 1
                    }
                )
                
        except ClientError as e:
            logger.error(f"Error updating compliance metrics: {e}")
            # Don't raise - metrics failure shouldn't block operations
    
    def _trigger_security_alert(self, event: AuditEvent) -> None:
        """Trigger security alert for critical events"""
        try:
            sns = boto3.client('sns', region_name=self.region)
            
            alert_message = {
                'alert_type': 'SECURITY_AUDIT',
                'severity': 'CRITICAL',
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp,
                'user_id': event.user_id,
                'source_ip': event.source_ip,
                'action': event.action,
                'outcome': event.outcome,
                'details': event.details
            }
            
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:aquachain-security-alerts',
                Subject=f'AquaChain Security Alert: {event.event_type.value}',
                Message=json.dumps(alert_message, indent=2)
            )
            
        except ClientError as e:
            logger.error(f"Error triggering security alert: {e}")
    
    def query_audit_logs(self, 
                        start_date: str,
                        end_date: str,
                        event_types: Optional[List[AuditEventType]] = None,
                        user_id: Optional[str] = None,
                        severity: Optional[AuditSeverity] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query audit logs with filtering.
        """
        try:
            # Build filter expression
            filter_expressions = []
            expression_values = {}
            
            # Date range filter
            filter_expressions.append('#timestamp BETWEEN :start_date AND :end_date')
            expression_values[':start_date'] = start_date
            expression_values[':end_date'] = end_date
            
            # Event type filter
            if event_types:
                event_type_conditions = []
                for i, event_type in enumerate(event_types):
                    key = f':event_type_{i}'
                    event_type_conditions.append(f'event_type = {key}')
                    expression_values[key] = event_type.value
                filter_expressions.append(f"({' OR '.join(event_type_conditions)})")
            
            # User ID filter
            if user_id:
                filter_expressions.append('user_id = :user_id')
                expression_values[':user_id'] = user_id
            
            # Severity filter
            if severity:
                filter_expressions.append('severity = :severity')
                expression_values[':severity'] = severity.value
            
            # Execute scan with filters
            response = self.audit_table.scan(
                FilterExpression=' AND '.join(filter_expressions),
                ExpressionAttributeNames={'#timestamp': 'timestamp'},
                ExpressionAttributeValues=expression_values,
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Error querying audit logs: {e}")
            return []
    
    def generate_compliance_report(self, 
                                 start_date: str,
                                 end_date: str,
                                 compliance_framework: str = 'SOC2') -> Dict[str, Any]:
        """
        Generate compliance report for specified date range.
        """
        try:
            # Query compliance metrics
            response = self.compliance_table.scan(
                FilterExpression='#date BETWEEN :start_date AND :end_date',
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={
                    ':start_date': start_date,
                    ':end_date': end_date
                }
            )
            
            metrics = response.get('Items', [])
            
            # Aggregate metrics
            total_events = 0
            event_types = {}
            severity_counts = {}
            compliance_tags = {}
            
            for metric in metrics:
                metric_type = metric.get('metric_type')
                
                if metric_type == 'daily_events':
                    total_events += metric.get('event_count', 0)
                    for event_type, count in metric.items():
                        if event_type not in ['metric_type', 'date', 'event_count']:
                            event_types[event_type] = event_types.get(event_type, 0) + count
                
                elif metric_type == 'severity_counts':
                    for severity, count in metric.items():
                        if severity not in ['metric_type', 'date']:
                            severity_counts[severity] = severity_counts.get(severity, 0) + count
                
                elif metric_type == 'compliance_tags':
                    for tag, count in metric.items():
                        if tag not in ['metric_type', 'date']:
                            compliance_tags[tag] = compliance_tags.get(tag, 0) + count
            
            # Generate report
            report = {
                'report_id': hashlib.sha256(f"{start_date}-{end_date}-{compliance_framework}".encode()).hexdigest()[:16],
                'framework': compliance_framework,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_events': total_events,
                    'event_types': event_types,
                    'severity_distribution': severity_counts,
                    'compliance_tags': compliance_tags
                },
                'compliance_status': self._assess_compliance_status(severity_counts, compliance_framework),
                'recommendations': self._generate_compliance_recommendations(severity_counts, event_types)
            }
            
            # Store report
            self._store_compliance_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    def _assess_compliance_status(self, severity_counts: Dict[str, int], framework: str) -> Dict[str, Any]:
        """Assess compliance status based on audit metrics"""
        critical_events = severity_counts.get('critical', 0)
        high_events = severity_counts.get('high', 0)
        
        if critical_events > 0:
            status = 'NON_COMPLIANT'
            risk_level = 'HIGH'
        elif high_events > 10:  # Threshold for high-severity events
            status = 'AT_RISK'
            risk_level = 'MEDIUM'
        else:
            status = 'COMPLIANT'
            risk_level = 'LOW'
        
        return {
            'status': status,
            'risk_level': risk_level,
            'critical_events': critical_events,
            'high_severity_events': high_events,
            'framework': framework
        }
    
    def _generate_compliance_recommendations(self, severity_counts: Dict[str, int], 
                                           event_types: Dict[str, int]) -> List[str]:
        """Generate compliance recommendations based on audit data"""
        recommendations = []
        
        if severity_counts.get('critical', 0) > 0:
            recommendations.append("Immediate investigation required for critical security events")
        
        if severity_counts.get('high', 0) > 10:
            recommendations.append("Review and strengthen security controls for high-severity events")
        
        if event_types.get('security_violation', 0) > 5:
            recommendations.append("Implement additional security monitoring and alerting")
        
        if event_types.get('data_export', 0) > 100:
            recommendations.append("Review data export policies and implement additional controls")
        
        return recommendations
    
    def _store_compliance_report(self, report: Dict[str, Any]) -> None:
        """Store compliance report in S3"""
        try:
            report_key = f"compliance-reports/{report['framework']}/{report['report_id']}.json"
            
            self.s3.put_object(
                Bucket=self.audit_bucket,
                Key=report_key,
                Body=json.dumps(report, indent=2),
                ContentType='application/json',
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=self.audit_signing_key
            )
            
        except ClientError as e:
            logger.error(f"Error storing compliance report: {e}")

class AuditDecorator:
    """Decorator for automatic audit logging of function calls"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    def audit_action(self, 
                    event_type: AuditEventType,
                    severity: AuditSeverity = AuditSeverity.MEDIUM,
                    resource_type: Optional[str] = None,
                    compliance_tags: Optional[List[str]] = None,
                    data_classification: str = 'internal'):
        """Decorator for auditing function calls"""
        def decorator(func):
            def wrapper(event, context):
                import uuid
                
                # Extract user context
                user_context = event.get('userContext', {})
                security_context = event.get('securityContext', {})
                
                # Create audit event
                audit_event = AuditEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=event_type,
                    severity=severity,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    user_id=user_context.get('userId'),
                    user_role=user_context.get('role'),
                    source_ip=security_context.get('clientIp', '0.0.0.0'),
                    user_agent=security_context.get('userAgent', ''),
                    resource_type=resource_type,
                    resource_id=event.get('pathParameters', {}).get('deviceId') or event.get('pathParameters', {}).get('requestId'),
                    action=func.__name__,
                    outcome='pending',
                    details={
                        'function_name': func.__name__,
                        'path_parameters': event.get('pathParameters', {}),
                        'query_parameters': event.get('queryStringParameters', {})
                    },
                    request_id=security_context.get('requestId'),
                    session_id=user_context.get('sessionId'),
                    compliance_tags=compliance_tags or [],
                    data_classification=data_classification,
                    retention_period=2555  # 7 years in days
                )
                
                try:
                    # Execute function
                    result = func(event, context)
                    
                    # Update audit event with success
                    audit_event.outcome = 'success'
                    if isinstance(result, dict) and result.get('statusCode'):
                        audit_event.details['status_code'] = result['statusCode']
                    
                    return result
                    
                except Exception as e:
                    # Update audit event with failure
                    audit_event.outcome = 'failure'
                    audit_event.details['error'] = str(e)
                    audit_event.severity = AuditSeverity.HIGH
                    
                    raise
                    
                finally:
                    # Log audit event
                    self.audit_logger.log_event(audit_event)
            
            return wrapper
        return decorator

# Global audit logger instance
audit_logger = AuditLogger()
audit_decorator = AuditDecorator(audit_logger)

# Convenience decorators
def audit_user_action(event_type: AuditEventType, compliance_tags: Optional[List[str]] = None):
    """Decorator for auditing user actions"""
    return audit_decorator.audit_action(
        event_type=event_type,
        severity=AuditSeverity.MEDIUM,
        compliance_tags=compliance_tags or ['user_activity']
    )

def audit_admin_action(event_type: AuditEventType, compliance_tags: Optional[List[str]] = None):
    """Decorator for auditing admin actions"""
    return audit_decorator.audit_action(
        event_type=event_type,
        severity=AuditSeverity.HIGH,
        compliance_tags=compliance_tags or ['admin_activity', 'privileged_access']
    )

def audit_data_access(resource_type: str, compliance_tags: Optional[List[str]] = None):
    """Decorator for auditing data access"""
    return audit_decorator.audit_action(
        event_type=AuditEventType.DEVICE_ACCESS,
        severity=AuditSeverity.MEDIUM,
        resource_type=resource_type,
        compliance_tags=compliance_tags or ['data_access'],
        data_classification='confidential'
    )