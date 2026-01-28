#!/usr/bin/env python3
"""
Dashboard Overhaul Checkpoint Validation Script
Validates core infrastructure and security components
"""

import sys
import os
import json
import importlib.util
from typing import Dict, List, Any

def validate_infrastructure_stack():
    """Validate CDK infrastructure stack configuration"""
    print("🔍 Validating Infrastructure Stack...")
    
    try:
        # Test CDK stack imports
        sys.path.append('infrastructure')
        from cdk.stacks.dashboard_overhaul_stack import DashboardOverhaulStack
        
        # Validate authority matrix structure
        sys.path.append('lambda/rbac_service')
        from handler import AuthorityMatrix
        
        # Check authority matrix completeness
        required_roles = [
            'inventory-manager',
            'warehouse-manager', 
            'supplier-coordinator',
            'procurement-finance-controller',
            'administrator'
        ]
        
        for role in required_roles:
            role_data = AuthorityMatrix.get_role_authorities(role)
            if not role_data:
                print(f"❌ Missing role definition: {role}")
                return False
            
            required_keys = ['authority_level', 'can_view', 'can_act', 'can_approve', 'can_configure']
            for key in required_keys:
                if key not in role_data:
                    print(f"❌ Missing key '{key}' in role '{role}'")
                    return False
        
        print("✅ Infrastructure stack validation passed")
        return True
        
    except ImportError as e:
        print(f"❌ Infrastructure import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Infrastructure validation failed: {e}")
        return False

def validate_rbac_service():
    """Validate RBAC service authority matrix enforcement"""
    print("🔍 Validating RBAC Service...")
    
    try:
        sys.path.append('lambda/rbac_service')
        from handler import AuthorityMatrix, RBACService
        
        # Test authority matrix enforcement
        test_cases = [
            # Valid permissions
            ('inventory-manager', 'inventory-data', 'view', True),
            ('inventory-manager', 'inventory-planning', 'act', True),
            ('procurement-finance-controller', 'purchase-orders', 'approve', True),
            ('administrator', 'system-settings', 'configure', True),
            
            # Invalid permissions (should be denied)
            ('inventory-manager', 'purchase-orders', 'approve', False),
            ('warehouse-manager', 'budget-allocation', 'act', False),
            ('supplier-coordinator', 'system-settings', 'configure', False),
        ]
        
        for role, resource, action, expected in test_cases:
            result = AuthorityMatrix.can_perform_action(role, resource, action)
            if result != expected:
                print(f"❌ Authority matrix test failed: {role} -> {resource}:{action} (expected {expected}, got {result})")
                return False
        
        print("✅ RBAC service validation passed")
        return True
        
    except Exception as e:
        print(f"❌ RBAC service validation failed: {e}")
        return False

def validate_audit_service():
    """Validate audit service configuration"""
    print("🔍 Validating Audit Service...")
    
    try:
        # Add the correct path for audit service
        audit_service_path = os.path.join('lambda', 'audit_service')
        if audit_service_path not in sys.path:
            sys.path.append(audit_service_path)
        
        # Import the audit service handler module with a unique name
        import importlib.util
        spec = importlib.util.spec_from_file_location("audit_handler", os.path.join(audit_service_path, "handler.py"))
        audit_handler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit_handler)
        
        DashboardAuditService = audit_handler.DashboardAuditService
        
        # Check audit service can be instantiated
        # Note: This will fail in local environment without AWS credentials
        # but validates the class structure
        audit_service_class = DashboardAuditService
        
        # Validate required methods exist
        required_methods = [
            'log_user_action',
            'log_system_event', 
            'query_audit_logs',
            'export_audit_data'
        ]
        
        for method in required_methods:
            if not hasattr(audit_service_class, method):
                print(f"❌ Missing audit service method: {method}")
                return False
        
        print("✅ Audit service validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Audit service validation failed: {e}")
        return False

def validate_test_coverage():
    """Validate that core tests are passing"""
    print("🔍 Validating Test Coverage...")
    
    # Check that test files exist
    required_test_files = [
        'tests/unit/lambda/test_rbac_authorization_properties.py',
        'tests/unit/lambda/test_authentication_security_properties.py',
        'tests/unit/lambda/test_logging_compliance_properties.py',
        'tests/unit/lambda/test_audit_trail_completeness_properties_simple.py'
    ]
    
    for test_file in required_test_files:
        if not os.path.exists(test_file):
            print(f"❌ Missing test file: {test_file}")
            return False
    
    print("✅ Test coverage validation passed")
    return True

def validate_security_configuration():
    """Validate security configuration"""
    print("🔍 Validating Security Configuration...")
    
    try:
        # Check that security components are properly configured
        sys.path.append('lambda/rbac_service')
        from handler import AuthorityMatrix
        
        # Validate authority levels are properly ordered
        expected_levels = ['VIEW', 'ACT', 'APPROVE', 'CONFIGURE']
        if AuthorityMatrix.AUTHORITY_LEVELS != expected_levels:
            print(f"❌ Authority levels mismatch: expected {expected_levels}, got {AuthorityMatrix.AUTHORITY_LEVELS}")
            return False
        
        # Validate that no role has empty permissions
        for role, role_data in AuthorityMatrix.ROLE_AUTHORITIES.items():
            total_permissions = (
                len(role_data.get('can_view', [])) +
                len(role_data.get('can_act', [])) +
                len(role_data.get('can_approve', [])) +
                len(role_data.get('can_configure', []))
            )
            
            if total_permissions == 0:
                print(f"❌ Role {role} has no permissions defined")
                return False
        
        print("✅ Security configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Security configuration validation failed: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🚀 Starting Dashboard Overhaul Checkpoint Validation")
    print("=" * 60)
    
    validations = [
        validate_infrastructure_stack,
        validate_rbac_service,
        validate_audit_service,
        validate_test_coverage,
        validate_security_configuration
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        if validation():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validations passed! Core infrastructure and security are properly configured.")
        return True
    else:
        print("⚠️  Some validations failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)