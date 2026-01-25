"""
Property-based tests for audit trail completeness

Feature: dashboard-overhaul, Property 5: Audit Trail Completeness
Feature: dashboard-overhaul, Property 20: Audit Query and Export Functionality  
Feature: dashboard-overhaul, Property 29: Security Audit Logging with Tamper Detection
Validates: Requirements 8.1, 8.2, 8.3, 8.4, 10.6
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock, call
import json
import sys
import os
from datetime import datetime, timezone, timedelta
import uuid
import hashlib
import base64

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from audit_service.handler import DashboardAuditService
from shared.errors import AuditServiceError


# Hypothesis strategies for generating test data

# User identifiers
user_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=10,
    max_size=50
)

# Actions from dashboard system
actions_strategy = st.sampled_from([
    'CREATE', 'READ', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT',
    'LOGIN', 'LOGOUT', 'EXPORT', 'QUERY', 'CONFIGURE',
    'SYSTEM_EVENT', 'SECURITY_VIOLATION', 'CONFIG_CHANGE'
])

# Resources from dashboard system
resources_strategy = st.sampled_from([
    'PURCHASE_ORDER', 'BUDGET', 'INVENTORY', 'USER', 'ROLE',
    'SUPPLIER', 'WAREHOUSE', 'WORKFLOW', 'AUDIT_LOG', 'SYSTEM'
])

# Resource IDs
resource_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
    min_size=5,
    max_size=30
)

# Request context
request_context_strategy = st.fixed_dictionaries({
    'ipAddress': st.ip_addresses().map(str),
    'userAgent': st.text(min_size=10, max_size=100),
    'correlationId': st.uuids().map(str),
    'sessionId': st.text(min_size=10, max_size=50),
    'source': st.sampled_from(['dashboard', 'api', 'system'])
})

# Action details
action_details_strategy = st.dictionaries(
    keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=1, max_size=20),
    values=st.one_of(
        st.text(min_size=1, max_size=100),
        st.integers(min_value=0, max_value=1000000),
        st.booleans(),
        st.none()
    ),
    min_size=0,
    max_size=10
)

# State data (before/after states)
state_data_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=1, max_size=20),
        values=st.one_of(
            st.text(min_size=1, max_size=100),
            st.integers(min_value=0, max_value=1000000),
            st.booleans()
        ),
        min_size=1,
        max_size=5
    )
)

# System event types
system_event_types_strategy = st.sampled_from([
    'SECURITY_VIOLATION', 'CONFIG_CHANGE', 'ERROR', 'WARNING',
    'TAMPERING_DETECTED', 'INTEGRITY_FAILURE', 'UNAUTHORIZED_ACCESS'
])

# Event severity levels
severity_strategy = st.sampled_from(['INFO', 'WARNING', 'ERROR', 'CRITICAL'])

# Date ranges for queries
date_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2025, 12, 31)
)


class TestAuditTrailCompleteness:
    """
    Property 5: Audit Trail Completeness
    
    For any user action, system event, or data modification, the system SHALL 
    create immutable audit records containing timestamp, user identity, action 
    details, before/after states, and cryptographic integrity verification.
    """
    
    @given(
        user_id=user_id_strategy,
        action=actions_strategy,
        resource=resources_strategy,
        resource_id=resource_id_strategy,
        details=action_details_strategy,
        request_context=request_context_strategy,
        before_state=state_data_strategy,
        after_state=state_data_strategy
    )
    @settings(max_examples=3)
    def test_user_actions_create_complete_audit_records(
        self, user_id, action, resource, resource_id, details, 
        request_context, before_state, after_state
    ):
        """
        Property Test: User actions create complete audit records
        
        For any user action with valid parameters, the system must create
        a complete audit record with all required fields and integrity verification.
        """
        with patch('audit_service.handler.boto3') as mock_boto3:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_boto3.resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mock_boto3.client.return_value = mock_s3
            
            # Mock KMS client for signing
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            mock_kms.verify.return_value = {'SignatureValid': True}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test user action logging
                result = audit_service.log_user_action(
                    user_id=user_id,
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    details=details,
                    request_context=request_context,
                    before_state=before_state,
                    after_state=after_state
                )
                
                # Verify result structure
                assert 'auditId' in result
                assert 'timestamp' in result
                assert 'status' in result
                assert 's3Key' in result
                assert result['status'] == 'logged'
                
                # Verify DynamoDB put_item was called
                mock_table.put_item.assert_called_once()
                dynamodb_item = mock_table.put_item.call_args[1]['Item']
                
                # Verify all required fields are present in DynamoDB record
                required_fields = [
                    'PK', 'SK', 'GSI1PK', 'GSI1SK', 'auditId', 'timestamp',
                    'userId', 'action', 'resource', 'resourceId', 'details',
                    'requestContext', 'integrity', 'compliance', 'ttl'
                ]
                
                for field in required_fields:
                    assert field in dynamodb_item, f"Missing required field: {field}"
                
                # Verify field values
                assert dynamodb_item['userId'] == user_id
                assert dynamodb_item['action'] == action
                assert dynamodb_item['resource'] == resource
                assert dynamodb_item['resourceId'] == resource_id
                assert dynamodb_item['details'] == details
                assert dynamodb_item['beforeState'] == before_state
                assert dynamodb_item['afterState'] == after_state
                
                # Verify integrity verification is present
                integrity = dynamodb_item['integrity']
                assert 'recordHash' in integrity
                assert 'digitalSignature' in integrity
                assert 'signingKeyId' in integrity
                assert 'hashAlgorithm' in integrity
                assert 'signatureAlgorithm' in integrity
                
                # Verify compliance fields
                compliance = dynamodb_item['compliance']
                assert compliance['retentionPeriod'] == '7-years'
                assert compliance['immutable'] is True
                assert compliance['encrypted'] is True
                
                # Verify S3 storage was called
                mock_s3.put_object.assert_called_once()
                s3_call = mock_s3.put_object.call_args
                
                # Verify S3 object has proper encryption and metadata
                assert s3_call[1]['ServerSideEncryption'] == 'aws:kms'
                assert 'SSEKMSKeyId' in s3_call[1]
                assert 'Metadata' in s3_call[1]
                
                s3_metadata = s3_call[1]['Metadata']
                assert s3_metadata['auditId'] == result['auditId']
                assert s3_metadata['userId'] == user_id
                assert s3_metadata['action'] == action
                assert s3_metadata['resource'] == resource
    
    @given(
        event_type=system_event_types_strategy,
        source=st.text(min_size=5, max_size=30),
        details=action_details_strategy,
        severity=severity_strategy
    )
    @settings(max_examples=3)
    def test_system_events_create_complete_audit_records(
        self, event_type, source, details, severity
    ):
        """
        Property Test: System events create complete audit records
        
        For any system event, the system must create a complete audit record
        with proper system context and integrity verification.
        """
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test system event logging
                result = audit_service.log_system_event(
                    event_type=event_type,
                    source=source,
                    details=details,
                    severity=severity
                )
                
                # Verify result structure
                assert 'auditId' in result
                assert 'timestamp' in result
                assert 'status' in result
                assert result['status'] == 'logged'
                
                # Verify DynamoDB record
                mock_table.put_item.assert_called_once()
                dynamodb_item = mock_table.put_item.call_args[1]['Item']
                
                # Verify system event specific fields
                assert dynamodb_item['userId'] == 'SYSTEM'
                assert dynamodb_item['action'] == 'SYSTEM_EVENT'
                assert dynamodb_item['resource'] == 'SYSTEM'
                assert dynamodb_item['resourceId'] == source
                
                # Verify event details contain system event information
                event_details = dynamodb_item['details']
                assert event_details['eventType'] == event_type
                assert event_details['source'] == source
                assert event_details['severity'] == severity
                
                # Verify system request context
                request_context = dynamodb_item['requestContext']
                assert request_context['ipAddress'] == 'internal'
                assert request_context['userAgent'] == 'system'
                assert request_context['source'] == 'system'
    
    @given(
        user_id=user_id_strategy,
        action=actions_strategy,
        resource=resources_strategy,
        resource_id=resource_id_strategy
    )
    @settings(max_examples=3)
    def test_audit_records_have_cryptographic_integrity(
        self, user_id, action, resource, resource_id
    ):
        """
        Property Test: Audit records have cryptographic integrity
        
        For any audit record, the system must include cryptographic integrity
        verification that can be used to detect tampering.
        """
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client with realistic signature
            mock_kms = Mock()
            mock_signature = base64.b64encode(b'realistic_signature_data').decode('utf-8')
            mock_kms.sign.return_value = {'Signature': base64.b64decode(mock_signature)}
            mock_kms.verify.return_value = {'SignatureValid': True}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test audit record creation
                result = audit_service.log_user_action(
                    user_id=user_id,
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    details={'test': 'data'},
                    request_context={'source': 'test'}
                )
                
                # Get the stored audit record from DynamoDB call
                dynamodb_item = mock_table.put_item.call_args[1]['Item']
                integrity = dynamodb_item['integrity']
                
                # Verify cryptographic integrity fields
                assert 'recordHash' in integrity
                assert 'digitalSignature' in integrity
                assert 'signingKeyId' in integrity
                assert 'hashAlgorithm' in integrity
                assert 'signatureAlgorithm' in integrity
                
                # Verify hash algorithm and signature algorithm
                assert integrity['hashAlgorithm'] == 'SHA256'
                assert integrity['signatureAlgorithm'] == 'RSA_PKCS1_V1_5'
                
                # Verify digital signature is base64 encoded
                signature = integrity['digitalSignature']
                try:
                    base64.b64decode(signature)
                    signature_valid = True
                except Exception:
                    signature_valid = False
                assert signature_valid, "Digital signature must be valid base64"
                
                # Verify KMS signing was called
                mock_kms.sign.assert_called_once()
                sign_call = mock_kms.sign.call_args[1]
                assert sign_call['MessageType'] == 'RAW'
                assert sign_call['SigningAlgorithm'] == 'RSASSA_PKCS1_V1_5_SHA_256'
    
    @given(
        user_id=user_id_strategy,
        actions_list=st.lists(actions_strategy, min_size=2, max_size=10, unique=True),
        resource=resources_strategy
    )
    @settings(max_examples=3)
    def test_multiple_actions_create_separate_audit_records(
        self, user_id, actions_list, resource
    ):
        """
        Property Test: Multiple actions create separate audit records
        
        For any sequence of user actions, each action must create a separate
        audit record with unique identifiers and timestamps.
        """
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                audit_ids = []
                timestamps = []
                
                # Log multiple actions
                for action in actions_list:
                    result = audit_service.log_user_action(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        resource_id=f"resource_{action}",
                        details={'action_index': actions_list.index(action)},
                        request_context={'source': 'test'}
                    )
                    
                    audit_ids.append(result['auditId'])
                    timestamps.append(result['timestamp'])
                
                # Verify all audit IDs are unique
                assert len(set(audit_ids)) == len(actions_list), "All audit IDs must be unique"
                
                # Verify all timestamps are unique (or very close)
                assert len(set(timestamps)) >= len(actions_list) - 1, "Timestamps should be unique or very close"
                
                # Verify correct number of DynamoDB calls
                assert mock_table.put_item.call_count == len(actions_list)
                
                # Verify correct number of S3 calls
                assert mock_s3.put_object.call_count == len(actions_list)


class TestAuditQueryAndExportFunctionality:
    """
    Property 20: Audit Query and Export Functionality
    
    For any audit query request by authorized users, the system SHALL support 
    filtering by time range, user, action type, and resource, and SHALL provide 
    export capabilities while maintaining audit log integrity and access controls.
    """
    
    @given(
        requester_user_id=user_id_strategy,
        query_user_id=user_id_strategy,
        start_time=date_strategy,
        end_time=date_strategy,
        limit=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=3)
    def test_audit_query_by_user_and_time_range(
        self, requester_user_id, query_user_id, start_time, end_time, limit
    ):
        """
        Property Test: Audit query by user and time range
        
        For any valid query parameters, the system must execute the query
        and return properly formatted results with pagination info.
        """
        assume(start_time <= end_time)
        
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table with query response
            mock_table = Mock()
            mock_query_response = {
                'Items': [
                    {
                        'auditId': str(uuid.uuid4()),
                        'timestamp': start_time.isoformat() + 'Z',
                        'userId': query_user_id,
                        'action': 'READ',
                        'resource': 'TEST_RESOURCE'
                    }
                ],
                'Count': 1
            }
            mock_table.query.return_value = mock_query_response
            mock_table.put_item.return_value = {}
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test audit query
                query_params = {
                    'userId': query_user_id,
                    'startTime': start_time.isoformat() + 'Z',
                    'endTime': end_time.isoformat() + 'Z',
                    'limit': limit
                }
                
                result = audit_service.query_audit_logs(
                    query_params=query_params,
                    requester_user_id=requester_user_id
                )
                
                # Verify query result structure
                assert 'items' in result
                assert 'count' in result
                assert isinstance(result['items'], list)
                assert isinstance(result['count'], int)
                assert result['count'] >= 0
                
                # Verify DynamoDB query was called
                mock_table.query.assert_called()
                query_call = mock_table.query.call_args[1]
                
                # Verify query parameters
                assert 'KeyConditionExpression' in query_call
                assert 'Limit' in query_call
                assert query_call['Limit'] == limit
                assert query_call['ScanIndexForward'] is False  # Newest first
                
                # Verify audit logging of the query request
                audit_calls = [call for call in mock_table.put_item.call_args_list]
                assert len(audit_calls) >= 1  # At least one audit log for the query
    
    @given(
        requester_user_id=user_id_strategy,
        resource=resources_strategy,
        start_time=date_strategy,
        end_time=date_strategy
    )
    @settings(max_examples=3)
    def test_audit_query_by_resource_type(
        self, requester_user_id, resource, start_time, end_time
    ):
        """
        Property Test: Audit query by resource type
        
        For any resource type query, the system must use the appropriate
        GSI and return filtered results.
        """
        assume(start_time <= end_time)
        
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_query_response = {
                'Items': [
                    {
                        'auditId': str(uuid.uuid4()),
                        'resource': resource,
                        'action': 'UPDATE'
                    }
                ],
                'Count': 1
            }
            mock_table.query.return_value = mock_query_response
            mock_table.put_item.return_value = {}
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 and KMS
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test resource-based query
                query_params = {
                    'resource': resource,
                    'startTime': start_time.isoformat() + 'Z',
                    'endTime': end_time.isoformat() + 'Z'
                }
                
                result = audit_service.query_audit_logs(
                    query_params=query_params,
                    requester_user_id=requester_user_id
                )
                
                # Verify query used GSI
                mock_table.query.assert_called()
                query_call = mock_table.query.call_args[1]
                assert 'IndexName' in query_call
                assert query_call['IndexName'] == 'GSI1'
                
                # Verify GSI key condition
                # The actual KeyConditionExpression is a boto3 condition object
                # We verify it was called with the right structure
                assert 'KeyConditionExpression' in query_call
    
    @given(
        requester_user_id=user_id_strategy,
        start_date=date_strategy,
        end_date=date_strategy,
        export_format=st.sampled_from(['json', 'csv', 'xlsx'])
    )
    @settings(max_examples=3)
    def test_audit_data_export_functionality(
        self, requester_user_id, start_date, end_date, export_format
    ):
        """
        Property Test: Audit data export functionality
        
        For any export request, the system must initiate an export job
        and return proper job details with estimated completion time.
        """
        assume(start_date <= end_date)
        
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 and KMS
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test export request
                export_request = {
                    'startDate': start_date.isoformat() + 'Z',
                    'endDate': end_date.isoformat() + 'Z',
                    'format': export_format,
                    'filters': {'resource': 'PURCHASE_ORDER'}
                }
                
                result = audit_service.export_audit_data(
                    export_request=export_request,
                    requester_user_id=requester_user_id
                )
                
                # Verify export result structure
                assert 'exportId' in result
                assert 'status' in result
                assert 'exportKey' in result
                assert 'estimatedCompletionTime' in result
                assert 'format' in result
                
                # Verify export details
                assert result['status'] == 'initiated'
                assert result['format'] == export_format
                assert result['exportKey'].startswith('exports/audit-export-')
                
                # Verify export request was audited
                mock_table.put_item.assert_called()
                audit_call = mock_table.put_item.call_args[1]['Item']
                assert audit_call['action'] == 'EXPORT_AUDIT_DATA'
                assert audit_call['userId'] == requester_user_id


class TestSecurityAuditLoggingWithTamperDetection:
    """
    Property 29: Security Audit Logging with Tamper Detection
    
    For any security-relevant event, the system SHALL create tamper-evident 
    audit logs with cryptographic integrity verification and immediate alerting 
    for any tampering attempts.
    """
    
    @given(
        user_id=user_id_strategy,
        security_event_type=st.sampled_from([
            'UNAUTHORIZED_ACCESS_ATTEMPT', 'PRIVILEGE_ESCALATION',
            'SUSPICIOUS_ACTIVITY', 'AUTHENTICATION_FAILURE',
            'AUTHORIZATION_VIOLATION', 'DATA_BREACH_ATTEMPT'
        ]),
        details=action_details_strategy
    )
    @settings(max_examples=3)
    def test_security_events_create_tamper_evident_logs(
        self, user_id, security_event_type, details
    ):
        """
        Property Test: Security events create tamper-evident logs
        
        For any security-relevant event, the system must create audit logs
        with cryptographic integrity that can detect tampering.
        """
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'security_signature'}
            mock_kms.verify.return_value = {'SignatureValid': True}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Test security event logging
                result = audit_service.log_system_event(
                    event_type=security_event_type,
                    source='security-monitor',
                    details={**details, 'userId': user_id, 'securityLevel': 'HIGH'},
                    severity='CRITICAL'
                )
                
                # Verify security event was logged
                assert result['status'] == 'logged'
                
                # Verify DynamoDB record has security-specific fields
                mock_table.put_item.assert_called_once()
                dynamodb_item = mock_table.put_item.call_args[1]['Item']
                
                # Verify security event details
                event_details = dynamodb_item['details']
                assert event_details['eventType'] == security_event_type
                assert event_details['severity'] == 'CRITICAL'
                assert event_details['userId'] == user_id
                assert event_details['securityLevel'] == 'HIGH'
                
                # Verify cryptographic integrity for security events
                integrity = dynamodb_item['integrity']
                assert 'recordHash' in integrity
                assert 'digitalSignature' in integrity
                
                # Verify S3 storage with encryption
                mock_s3.put_object.assert_called_once()
                s3_call = mock_s3.put_object.call_args[1]
                assert s3_call['ServerSideEncryption'] == 'aws:kms'
    
    @given(
        audit_id=st.uuids().map(str),
        requester_user_id=user_id_strategy
    )
    @settings(max_examples=3)
    def test_audit_integrity_verification_detects_valid_records(
        self, audit_id, requester_user_id
    ):
        """
        Property Test: Audit integrity verification detects valid records
        
        For any valid audit record, integrity verification must confirm
        the record is valid and has not been tampered with.
        """
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Create a mock valid audit record
            mock_audit_record = {
                'auditId': audit_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'userId': 'test_user',
                'action': 'READ',
                'resource': 'TEST_RESOURCE',
                'resourceId': 'test_id',
                'details': {'test': 'data'},
                'integrity': {
                    'recordHash': 'valid_hash',
                    'digitalSignature': base64.b64encode(b'valid_signature').decode('utf-8'),
                    'signingKeyId': 'test-key',
                    'hashAlgorithm': 'SHA256',
                    'signatureAlgorithm': 'RSA_PKCS1_V1_5'
                }
            }
            
            # Mock DynamoDB table to return the audit record
            mock_table = Mock()
            mock_table.scan.return_value = {'Items': [mock_audit_record]}
            mock_table.put_item.return_value = {}
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client to verify signature
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            mock_kms.verify.return_value = {'SignatureValid': True}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Mock the hash calculation to match
                with patch('audit_service.handler.hashlib.sha256') as mock_hash:
                    mock_hash.return_value.hexdigest.return_value = 'valid_hash'
                    
                    # Test integrity verification
                    result = audit_service.verify_audit_integrity(
                        audit_id=audit_id,
                        requester_user_id=requester_user_id
                    )
                    
                    # Verify integrity check results
                    assert 'auditId' in result
                    assert 'verified' in result
                    assert 'hashValid' in result
                    assert 'signatureValid' in result
                    assert 'verifiedAt' in result
                    
                    assert result['auditId'] == audit_id
                    assert result['verified'] is True
                    assert result['hashValid'] is True
                    assert result['signatureValid'] is True
                    
                    # Verify KMS verify was called
                    mock_kms.verify.assert_called_once()
    
    @given(
        start_date=date_strategy,
        end_date=date_strategy,
        requester_user_id=user_id_strategy
    )
    @settings(max_examples=3)
    def test_tampering_detection_identifies_integrity_violations(
        self, start_date, end_date, requester_user_id
    ):
        """
        Property Test: Tampering detection identifies integrity violations
        
        For any date range, tampering detection must analyze audit records
        and identify any integrity violations or suspicious patterns.
        """
        assume(start_date <= end_date)
        
        with patch.multiple(
            'audit_service.handler',
            boto3=MagicMock(),
        ) as mocks:
            # Mock DynamoDB table
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            mocks['boto3'].resource.return_value.Table.return_value = mock_table
            
            # Mock S3 client
            mock_s3 = Mock()
            mocks['boto3'].client.return_value = mock_s3
            
            # Mock KMS client
            mock_kms = Mock()
            mock_kms.sign.return_value = {'Signature': b'mock_signature'}
            
            with patch('audit_service.handler.boto3.client', return_value=mock_kms):
                audit_service = DashboardAuditService()
                
                # Mock the query execution to return some records
                with patch.object(audit_service, '_execute_audit_query') as mock_query:
                    mock_query.return_value = {
                        'items': [
                            {
                                'auditId': str(uuid.uuid4()),
                                'integrity': {
                                    'recordHash': 'test_hash',
                                    'digitalSignature': 'test_signature'
                                }
                            }
                        ]
                    }
                    
                    # Mock integrity verification to return valid
                    with patch.object(audit_service, '_verify_record_integrity') as mock_verify:
                        mock_verify.return_value = {'verified': True}
                        
                        # Test tampering detection
                        result = audit_service.detect_tampering(
                            start_date=start_date.isoformat() + 'Z',
                            end_date=end_date.isoformat() + 'Z',
                            requester_user_id=requester_user_id
                        )
                        
                        # Verify tampering detection result structure
                        assert 'tamperingDetected' in result
                        assert 'checkedRecords' in result
                        assert 'invalidRecords' in result
                        assert 'suspiciousPatterns' in result
                        assert 'checkedPeriod' in result
                        assert 'detectionTimestamp' in result
                        
                        # Verify result types
                        assert isinstance(result['tamperingDetected'], bool)
                        assert isinstance(result['checkedRecords'], int)
                        assert isinstance(result['invalidRecords'], int)
                        assert isinstance(result['suspiciousPatterns'], list)
                        
                        # Verify checked period
                        checked_period = result['checkedPeriod']
                        assert checked_period['startDate'] == start_date.isoformat() + 'Z'
                        assert checked_period['endDate'] == end_date.isoformat() + 'Z'
                        
                        # Verify system event was logged for tampering detection
                        system_event_calls = [
                            call for call in mock_table.put_item.call_args_list
                            if call[1]['Item']['action'] == 'SYSTEM_EVENT'
                        ]
                        assert len(system_event_calls) >= 1
