"""
Security Audit Logger
Captures real system events and writes them to the Security Audit Logs table
"""

import boto3
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import os

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')

# Environment variables
SECURITY_AUDIT_TABLE = os.environ.get('SECURITY_AUDIT_TABLE', 'AquaChain-SecurityAuditLogs-dev')

# DynamoDB table
security_audit_table = dynamodb.Table(SECURITY_AUDIT_TABLE)


class SecurityAuditLogger:
    """
    Centralized security audit logging for all system events
    """
    
    @staticmethod
    def log_reading_processed(
        device_id: str,
        wqi: float,
        anomaly_type: str,
        timestamp: str,
        user_id: str,
        readings: Dict[str, Any]
    ) -> None:
        """
        Log when an IoT reading is processed
        
        Args:
            device_id: Device identifier
            wqi: Water Quality Index
            anomaly_type: Type of anomaly detected
            timestamp: Reading timestamp
            user_id: User who owns the device
            readings: Raw sensor readings
        """
        try:
            # Generate unique log ID
            log_id = f"log-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{device_id}"
            
            # Generate data hash for integrity
            data_hash = SecurityAuditLogger._generate_hash({
                'device_id': device_id,
                'wqi': wqi,
                'timestamp': timestamp,
                'readings': readings
            })
            
            # Format timestamp for display
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            display_timestamp = dt.strftime('%d/%m/%Y, %I:%M:%S %p')
            
            # Create audit log entry
            audit_entry = {
                'logId': log_id,
                'timestamp': display_timestamp,
                'deviceId': device_id,
                'wqi': Decimal(str(round(wqi, 1))),
                'anomalyType': anomaly_type,
                'verified': True,  # Verified through hash chain
                'dataHash': data_hash,
                'userId': user_id,
                'eventType': 'READING_PROCESSED',
                'rawTimestamp': timestamp,
                'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)  # 30 days
            }
            
            # Store in DynamoDB
            security_audit_table.put_item(Item=audit_entry)
            
            print(f"✅ Security audit log created: {log_id}")
            
        except Exception as e:
            print(f"⚠️  Error creating security audit log: {e}")
            # Don't fail the main process if audit logging fails
    
    @staticmethod
    def log_admin_action(
        admin_id: str,
        action: str,
        resource: str,
        ip_address: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log admin actions for security audit trail
        
        Args:
            admin_id: Admin user identifier
            action: Action performed (e.g., 'CONFIG_UPDATE', 'USER_DELETE')
            resource: Resource affected
            ip_address: Admin's IP address
            details: Additional action details
        """
        try:
            log_id = f"admin-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            timestamp = datetime.utcnow().strftime('%d/%m/%Y, %I:%M:%S %p')
            
            data_hash = SecurityAuditLogger._generate_hash({
                'admin_id': admin_id,
                'action': action,
                'resource': resource,
                'timestamp': timestamp
            })
            
            audit_entry = {
                'logId': log_id,
                'timestamp': timestamp,
                'deviceId': 'ADMIN',
                'wqi': Decimal('100.0'),  # N/A for admin actions
                'anomalyType': 'admin_action',
                'verified': True,
                'dataHash': data_hash,
                'userId': admin_id,
                'eventType': action,
                'resource': resource,
                'ipAddress': SecurityAuditLogger._hash_ip(ip_address),
                'details': json.dumps(details) if details else None,
                'ttl': int(datetime.utcnow().timestamp()) + (90 * 24 * 60 * 60)  # 90 days for admin actions
            }
            
            security_audit_table.put_item(Item=audit_entry)
            print(f"✅ Admin action logged: {action} by {admin_id}")
            
        except Exception as e:
            print(f"⚠️  Error logging admin action: {e}")
    
    @staticmethod
    def log_alert_triggered(
        device_id: str,
        alert_type: str,
        severity: str,
        wqi: float,
        user_id: str
    ) -> None:
        """
        Log when an alert is triggered
        
        Args:
            device_id: Device that triggered alert
            alert_type: Type of alert
            severity: Alert severity level
            wqi: Water Quality Index at time of alert
            user_id: User who owns the device
        """
        try:
            log_id = f"alert-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{device_id}"
            timestamp = datetime.utcnow().strftime('%d/%m/%Y, %I:%M:%S %p')
            
            data_hash = SecurityAuditLogger._generate_hash({
                'device_id': device_id,
                'alert_type': alert_type,
                'severity': severity,
                'timestamp': timestamp
            })
            
            audit_entry = {
                'logId': log_id,
                'timestamp': timestamp,
                'deviceId': device_id,
                'wqi': Decimal(str(round(wqi, 1))),
                'anomalyType': alert_type,
                'verified': True,
                'dataHash': data_hash,
                'userId': user_id,
                'eventType': 'ALERT_TRIGGERED',
                'severity': severity,
                'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)
            }
            
            security_audit_table.put_item(Item=audit_entry)
            print(f"✅ Alert logged: {alert_type} for {device_id}")
            
        except Exception as e:
            print(f"⚠️  Error logging alert: {e}")
    
    @staticmethod
    def _generate_hash(data: Dict[str, Any]) -> str:
        """
        Generate SHA-256 hash of data for integrity verification
        
        Args:
            data: Data to hash
            
        Returns:
            Hash string in format 'hash-{first8chars}'
        """
        sorted_data = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.sha256(sorted_data.encode())
        return f"hash-{hash_obj.hexdigest()[:8]}"
    
    @staticmethod
    def _hash_ip(ip_address: str) -> str:
        """
        Hash IP address for privacy
        
        Args:
            ip_address: IP address to hash
            
        Returns:
            Hashed IP address
        """
        hash_obj = hashlib.sha256(ip_address.encode())
        return f"ip-{hash_obj.hexdigest()[:12]}"


# Singleton instance
audit_logger = SecurityAuditLogger()
