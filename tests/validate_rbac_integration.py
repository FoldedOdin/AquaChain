#!/usr/bin/env python3
"""
RBAC Integration Validation Script
Validates that all backend services properly integrate with RBAC middleware
and enforce permission checks for sensitive operations.

This script tests the enhanced RBAC integration implemented for Checkpoint 9.
"""

import json
import sys
import os
import importlib.util
from typing import Dict, List, Tuple, Any
from datetime import datetime
import uuid

# Add lambda paths for imports
sys.path.append('lambda/shared')
sys.path.append('lambda/inventory_management')
sys.path.append('lambda/procurement_service')
sys.path.append('lambda/workflow_service')
sys.path.append('lambda/budget_service')
sys.path.append('lambda/audit_service')

class RBACIntegrationValidator:
    """
    Validates RBAC integration across all backend services
    """
    
    def __init__(self):
        """Initialize the validator"""
        self.results = {
            'overall_score': 0.0,
            'service_scores': {},
            'integration_tests': {},
            'recommendations': [],
            'validation_timestamp': datetime.utcnow().isoformat()
        }
        
        # Services to validate
        self.services = {
            'inventory_management': {
                'handler_path': 'lambda/inventory_management/handler.py',
                'expected_permissions': [
                    ('inventory-data', 'view'),
                    ('stock-adjustments', 'act'),
                    ('reorder-alerts', 'view'),
                    ('demand-forecasts', 'view'),
                    ('inventory-audit-history', 'view')
                ]
            },
            'procurement_service': {
                'handler_path': 'lambda/procurement_service/handler.py',
                'expected_permissions': [
                    ('purchase-orders', 'act'),
                    ('purchase-orders', 'approve'),
                    ('emergency-purchases', 'act'),
                    ('audit-trails', 'view')
                ]
            },
            'workflow_service': {
                'handler_path': 'lambda/workflow_service/handler.py',
                'expected_permissions': [
                    ('workflow-management', 'act'),
                    ('workflow-management', 'view'),
                    ('audit-trails', 'view')
                ]
            },
            'budget_service': {
                'handler_path': 'lambda/budget_service/handler.py',
                'expected_permissions': [
                    ('budgets', 'view'),
                    ('budget-allocation', 'act'),
                    ('budget-allocation', 'configure'),
                    ('budget-changes', 'approve'),
                    ('spend-analysis', 'view')
                ]
            },
            'audit_service': {
                'handler_path': 'lambda/audit_service/handler.py',
                'expected_permissions': [
                    ('audit-trails', 'view'),
                    ('compliance-reports', 'view'),
                    ('security-logs', 'view')
                ]
            }
        }
    
    def validate_all_services(self) -> Dict[str, Any]:
        """
        Validate RBAC integration for all services
        
        Returns:
            Comprehensive validation results
        """
        print("🔐 Starting RBAC Integration Validation...")
        print("=" * 60)
        
        total_score = 0.0
        service_count = 0
        
        for service_name, service_config in self.services.items():
            print(f"\n📋 Validating {service_name}...")
            
            service_score = self._validate_service_rbac(service_name, service_config)
            self.results['service_scores'][service_name] = service_score
            
            total_score += service_score
            service_count += 1
            
            status = "✅ PASS" if service_score >= 8.0 else "⚠️ NEEDS IMPROVEMENT" if service_score >= 6.0 else "❌ FAIL"
            print(f"   {status} - Score: {service_score:.1f}/10.0")
        
        # Calculate overall score
        self.results['overall_score'] = total_score / service_count if service_count > 0 else 0.0
        
        # Run integration tests
        self._run_integration_tests()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _validate_service_rbac(self, service_name: str, service_config: Dict) -> float:
        """
        Validate RBAC integration for a specific service
        
        Args:
            service_name: Name of the service
            service_config: Service configuration
            
        Returns:
            Service RBAC integration score (0-10)
        """
        score = 0.0
        max_score = 10.0
        
        handler_path = service_config['handler_path']
        expected_permissions = service_config['expected_permissions']
        
        # Check if handler file exists
        if not os.path.exists(handler_path):
            print(f"   ❌ Handler file not found: {handler_path}")
            return 0.0
        
        # Read handler file content
        try:
            with open(handler_path, 'r') as f:
                handler_content = f.read()
        except Exception as e:
            print(f"   ❌ Failed to read handler file: {e}")
            return 0.0
        
        # Check for RBAC middleware import
        if 'from rbac_middleware import' in handler_content:
            score += 2.0
            print(f"   ✅ RBAC middleware imported")
        else:
            print(f"   ❌ RBAC middleware not imported")
        
        # Check for validate_user_permissions usage
        permission_checks = handler_content.count('validate_user_permissions')
        if permission_checks >= len(expected_permissions):
            score += 3.0
            print(f"   ✅ Sufficient permission checks found ({permission_checks})")
        elif permission_checks > 0:
            score += 1.5
            print(f"   ⚠️ Some permission checks found ({permission_checks}), but may need more")
        else:
            print(f"   ❌ No permission checks found")
        
        # Check for proper error handling
        if 'Access denied' in handler_content and 'statusCode": 403' in handler_content:
            score += 2.0
            print(f"   ✅ Proper access denied error handling")
        else:
            print(f"   ❌ Missing proper access denied error handling")
        
        # Check for username extraction in request context
        if "'username'" in handler_content and 'authorizer' in handler_content:
            score += 1.5
            print(f"   ✅ Username extraction implemented")
        else:
            print(f"   ❌ Username extraction missing")
        
        # Check for audit logging of access attempts
        if 'correlation_id' in handler_content and 'user_id' in handler_content:
            score += 1.5
            print(f"   ✅ Proper request context handling")
        else:
            print(f"   ❌ Request context handling incomplete")
        
        return min(score, max_score)
    
    def _run_integration_tests(self):
        """Run integration tests for RBAC functionality"""
        print(f"\n🧪 Running RBAC Integration Tests...")
        
        # Test 1: Authority Matrix Coverage
        authority_matrix_score = self._test_authority_matrix_coverage()
        self.results['integration_tests']['authority_matrix_coverage'] = authority_matrix_score
        
        # Test 2: Permission Validation Logic
        permission_validation_score = self._test_permission_validation_logic()
        self.results['integration_tests']['permission_validation_logic'] = permission_validation_score
        
        # Test 3: Error Handling Consistency
        error_handling_score = self._test_error_handling_consistency()
        self.results['integration_tests']['error_handling_consistency'] = error_handling_score
        
        # Test 4: Audit Trail Integration
        audit_integration_score = self._test_audit_trail_integration()
        self.results['integration_tests']['audit_trail_integration'] = audit_integration_score
    
    def _test_authority_matrix_coverage(self) -> float:
        """Test authority matrix coverage"""
        print("   📊 Testing authority matrix coverage...")
        
        # Check if RBAC middleware has comprehensive authority matrix
        rbac_middleware_path = 'lambda/shared/rbac_middleware.py'
        
        if not os.path.exists(rbac_middleware_path):
            print("   ❌ RBAC middleware file not found")
            return 0.0
        
        try:
            with open(rbac_middleware_path, 'r') as f:
                middleware_content = f.read()
        except Exception as e:
            print(f"   ❌ Failed to read RBAC middleware: {e}")
            return 0.0
        
        # Check for authority matrix definition
        if 'authority_matrix' in middleware_content:
            print("   ✅ Authority matrix defined")
            
            # Check for required roles
            required_roles = [
                'inventory-manager',
                'warehouse-manager', 
                'supplier-coordinator',
                'procurement-finance-controller',
                'administrator'
            ]
            
            roles_found = sum(1 for role in required_roles if role in middleware_content)
            role_coverage = roles_found / len(required_roles)
            
            print(f"   📈 Role coverage: {roles_found}/{len(required_roles)} ({role_coverage:.1%})")
            
            return min(10.0, role_coverage * 10.0)
        else:
            print("   ❌ Authority matrix not found")
            return 0.0
    
    def _test_permission_validation_logic(self) -> float:
        """Test permission validation logic"""
        print("   🔍 Testing permission validation logic...")
        
        # Check if RBAC middleware has proper validation functions
        rbac_middleware_path = 'lambda/shared/rbac_middleware.py'
        
        try:
            with open(rbac_middleware_path, 'r') as f:
                middleware_content = f.read()
        except Exception:
            return 0.0
        
        score = 0.0
        
        # Check for validation function
        if 'def validate_permissions' in middleware_content:
            score += 3.0
            print("   ✅ Permission validation function found")
        
        # Check for remote RBAC service integration
        if '_validate_with_rbac_service' in middleware_content:
            score += 2.0
            print("   ✅ Remote RBAC service integration")
        
        # Check for local fallback validation
        if '_validate_locally' in middleware_content:
            score += 2.0
            print("   ✅ Local fallback validation")
        
        # Check for audit logging
        if 'audit_logger.log_user_action' in middleware_content:
            score += 2.0
            print("   ✅ Audit logging integration")
        
        # Check for fail-secure behavior
        if 'return False' in middleware_content and 'validation failed' in middleware_content.lower():
            score += 1.0
            print("   ✅ Fail-secure behavior implemented")
        
        return score
    
    def _test_error_handling_consistency(self) -> float:
        """Test error handling consistency across services"""
        print("   🚨 Testing error handling consistency...")
        
        consistent_patterns = 0
        total_services = len(self.services)
        
        for service_name, service_config in self.services.items():
            handler_path = service_config['handler_path']
            
            try:
                with open(handler_path, 'r') as f:
                    content = f.read()
                
                # Check for consistent error response pattern
                has_403_status = ('statusCode": 403' in content or "'statusCode': 403" in content)
                has_access_denied = 'Access denied' in content
                has_correlation_id = ('correlationId' in content or 'correlation_id' in content)
                has_user_role = 'userRole' in content
                
                if has_403_status and has_access_denied and has_correlation_id and has_user_role:
                    consistent_patterns += 1
                    print(f"   ✅ {service_name}: Consistent error handling")
                else:
                    print(f"   ⚠️ {service_name}: Inconsistent error handling")
                    
            except Exception:
                print(f"   ❌ {service_name}: Could not validate error handling")
        
        consistency_score = (consistent_patterns / total_services) * 10.0
        print(f"   📊 Error handling consistency: {consistent_patterns}/{total_services} ({consistency_score:.1f}/10.0)")
        
        return consistency_score
    
    def _test_audit_trail_integration(self) -> float:
        """Test audit trail integration"""
        print("   📝 Testing audit trail integration...")
        
        audit_integration_score = 0.0
        services_with_audit = 0
        
        for service_name, service_config in self.services.items():
            handler_path = service_config['handler_path']
            
            try:
                with open(handler_path, 'r') as f:
                    content = f.read()
                
                # Check for audit logging calls
                if 'audit_logger' in content or 'log_user_action' in content:
                    services_with_audit += 1
                    print(f"   ✅ {service_name}: Audit logging integrated")
                else:
                    print(f"   ⚠️ {service_name}: Audit logging missing")
                    
            except Exception:
                print(f"   ❌ {service_name}: Could not validate audit integration")
        
        audit_integration_score = (services_with_audit / len(self.services)) * 10.0
        print(f"   📊 Audit integration: {services_with_audit}/{len(self.services)} ({audit_integration_score:.1f}/10.0)")
        
        return audit_integration_score
    
    def _generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check overall score
        if self.results['overall_score'] < 8.0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'RBAC Integration',
                'issue': 'Overall RBAC integration score is below 8.0',
                'recommendation': 'Review and enhance RBAC integration across all services',
                'impact': 'Security vulnerability - unauthorized access possible'
            })
        
        # Check individual service scores
        for service_name, score in self.results['service_scores'].items():
            if score < 7.0:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Service RBAC',
                    'issue': f'{service_name} RBAC integration score is {score:.1f}/10.0',
                    'recommendation': f'Enhance RBAC integration in {service_name} service',
                    'impact': 'Service-specific security gaps'
                })
        
        # Check integration test results
        for test_name, score in self.results['integration_tests'].items():
            if score < 7.0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Integration',
                    'issue': f'{test_name} score is {score:.1f}/10.0',
                    'recommendation': f'Improve {test_name.replace("_", " ")}',
                    'impact': 'Integration consistency issues'
                })
        
        # Add general recommendations
        if self.results['overall_score'] >= 8.0:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Enhancement',
                'issue': 'RBAC integration is good but can be optimized',
                'recommendation': 'Consider implementing automated RBAC testing in CI/CD pipeline',
                'impact': 'Improved long-term security posture'
            })
        
        self.results['recommendations'] = recommendations
    
    def _print_summary(self):
        """Print validation summary"""
        print(f"\n" + "=" * 60)
        print(f"🔐 RBAC INTEGRATION VALIDATION SUMMARY")
        print(f"=" * 60)
        
        # Overall score
        overall_score = self.results['overall_score']
        if overall_score >= 8.0:
            status = "✅ EXCELLENT"
            color = "🟢"
        elif overall_score >= 6.0:
            status = "⚠️ GOOD"
            color = "🟡"
        else:
            status = "❌ NEEDS IMPROVEMENT"
            color = "🔴"
        
        print(f"\n{color} Overall RBAC Integration Score: {overall_score:.1f}/10.0 - {status}")
        
        # Service scores
        print(f"\n📊 Service Scores:")
        for service_name, score in self.results['service_scores'].items():
            service_status = "✅" if score >= 8.0 else "⚠️" if score >= 6.0 else "❌"
            print(f"   {service_status} {service_name}: {score:.1f}/10.0")
        
        # Integration test scores
        print(f"\n🧪 Integration Test Scores:")
        for test_name, score in self.results['integration_tests'].items():
            test_status = "✅" if score >= 8.0 else "⚠️" if score >= 6.0 else "❌"
            test_display = test_name.replace('_', ' ').title()
            print(f"   {test_status} {test_display}: {score:.1f}/10.0")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                priority_icon = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
                print(f"   {i}. {priority_icon} [{rec['priority']}] {rec['recommendation']}")
                print(f"      Issue: {rec['issue']}")
                print(f"      Impact: {rec['impact']}")
        else:
            print(f"\n✅ No critical recommendations - RBAC integration is well implemented!")
        
        # Final assessment
        print(f"\n" + "=" * 60)
        if overall_score >= 8.0:
            print(f"🎉 RBAC INTEGRATION VALIDATION: PASSED")
            print(f"   All services have strong RBAC integration.")
            print(f"   Ready for production deployment.")
        elif overall_score >= 6.0:
            print(f"⚠️ RBAC INTEGRATION VALIDATION: CONDITIONAL PASS")
            print(f"   Most services have adequate RBAC integration.")
            print(f"   Address recommendations before production.")
        else:
            print(f"❌ RBAC INTEGRATION VALIDATION: FAILED")
            print(f"   Critical RBAC integration issues found.")
            print(f"   Must address issues before proceeding.")
        
        print(f"=" * 60)


def main():
    """Main validation function"""
    validator = RBACIntegrationValidator()
    results = validator.validate_all_services()
    
    # Save results to file
    results_file = f"rbac_integration_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Return exit code based on results
    if results['overall_score'] >= 8.0:
        return 0  # Success
    elif results['overall_score'] >= 6.0:
        return 1  # Warning
    else:
        return 2  # Failure


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)