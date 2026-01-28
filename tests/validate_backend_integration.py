#!/usr/bin/env python3
"""
Backend Services Integration Validation Script
Validates that all backend services integrate correctly for the dashboard overhaul checkpoint.

This script:
1. Runs comprehensive integration tests
2. Validates service-to-service communication
3. Tests workflow state machines
4. Confirms budget enforcement
5. Tests graceful degradation scenarios
6. Generates a validation report
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add test modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests', 'integration'))

try:
    from test_backend_services_integration import BackendServicesIntegrationTest
except ImportError as e:
    print(f"❌ Failed to import integration tests: {e}")
    sys.exit(1)


class BackendIntegrationValidator:
    """
    Validates backend services integration for checkpoint 9
    """
    
    def __init__(self):
        self.validation_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.results = {
            'validation_id': self.validation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'checkpoint': 'Backend Services Integration Validation',
            'status': 'running',
            'tests': {},
            'summary': {},
            'recommendations': []
        }
    
    def validate_service_files_exist(self):
        """
        Validate that all required service files exist
        """
        print("🔍 Validating service files...")
        
        required_services = [
            'lambda/rbac_service/handler.py',
            'lambda/inventory_management/handler.py',
            'lambda/procurement_service/handler.py',
            'lambda/workflow_service/handler.py',
            'lambda/budget_service/handler.py',
            'lambda/audit_service/handler.py'
        ]
        
        missing_files = []
        existing_files = []
        
        for service_file in required_services:
            if os.path.exists(service_file):
                existing_files.append(service_file)
                print(f"  ✅ {service_file}")
            else:
                missing_files.append(service_file)
                print(f"  ❌ {service_file}")
        
        self.results['tests']['service_files'] = {
            'status': 'passed' if len(missing_files) == 0 else 'failed',
            'existing_files': existing_files,
            'missing_files': missing_files,
            'total_required': len(required_services),
            'total_existing': len(existing_files)
        }
        
        if missing_files:
            self.results['recommendations'].append(
                f"Missing service files: {', '.join(missing_files)}. "
                "Ensure all backend services are implemented."
            )
        
        return len(missing_files) == 0
    
    def validate_shared_modules(self):
        """
        Validate that shared modules exist and are accessible
        """
        print("🔍 Validating shared modules...")
        
        shared_modules = [
            'lambda/shared/structured_logger.py',
            'lambda/shared/audit_logger.py',
            'lambda/shared/errors.py',
            'lambda/shared/error_handler.py'
        ]
        
        missing_modules = []
        existing_modules = []
        
        for module_file in shared_modules:
            if os.path.exists(module_file):
                existing_modules.append(module_file)
                print(f"  ✅ {module_file}")
            else:
                missing_modules.append(module_file)
                print(f"  ❌ {module_file}")
        
        self.results['tests']['shared_modules'] = {
            'status': 'passed' if len(missing_modules) == 0 else 'failed',
            'existing_modules': existing_modules,
            'missing_modules': missing_modules,
            'total_required': len(shared_modules),
            'total_existing': len(existing_modules)
        }
        
        if missing_modules:
            self.results['recommendations'].append(
                f"Missing shared modules: {', '.join(missing_modules)}. "
                "Ensure shared utilities are implemented."
            )
        
        return len(missing_modules) == 0
    
    def run_integration_tests(self):
        """
        Run the comprehensive integration test suite
        """
        print("🧪 Running integration tests...")
        
        try:
            # Initialize and run integration tests
            test_suite = BackendServicesIntegrationTest()
            test_results = test_suite.run_all_integration_tests()
            
            self.results['tests']['integration'] = test_results
            
            if test_results.get('overall_success', False):
                print("  ✅ All integration tests passed")
                return True
            else:
                print("  ❌ Some integration tests failed")
                
                # Add specific failure details
                if 'error' in test_results:
                    self.results['recommendations'].append(
                        f"Integration test error: {test_results['error']}"
                    )
                
                return False
                
        except Exception as e:
            print(f"  ❌ Integration tests failed to run: {e}")
            self.results['tests']['integration'] = {
                'status': 'error',
                'error': str(e),
                'overall_success': False
            }
            self.results['recommendations'].append(
                f"Integration tests could not run: {str(e)}. "
                "Check service implementations and dependencies."
            )
            return False
    
    def validate_service_interfaces(self):
        """
        Validate that services have proper interfaces and can be imported
        """
        print("🔍 Validating service interfaces...")
        
        service_validations = {}
        
        # Test RBAC Service
        try:
            sys.path.append('lambda/rbac_service')
            from handler import RBACService
            service_validations['rbac_service'] = {
                'importable': True,
                'has_main_class': True,
                'error': None
            }
            print("  ✅ RBAC Service")
        except Exception as e:
            service_validations['rbac_service'] = {
                'importable': False,
                'has_main_class': False,
                'error': str(e)
            }
            print(f"  ❌ RBAC Service: {e}")
        
        # Test Inventory Service
        try:
            sys.path.append('lambda/inventory_management')
            from handler import InventoryService
            service_validations['inventory_service'] = {
                'importable': True,
                'has_main_class': True,
                'error': None
            }
            print("  ✅ Inventory Service")
        except Exception as e:
            service_validations['inventory_service'] = {
                'importable': False,
                'has_main_class': False,
                'error': str(e)
            }
            print(f"  ❌ Inventory Service: {e}")
        
        # Test Procurement Service
        try:
            sys.path.append('lambda/procurement_service')
            from handler import ProcurementService
            service_validations['procurement_service'] = {
                'importable': True,
                'has_main_class': True,
                'error': None
            }
            print("  ✅ Procurement Service")
        except Exception as e:
            service_validations['procurement_service'] = {
                'importable': False,
                'has_main_class': False,
                'error': str(e)
            }
            print(f"  ❌ Procurement Service: {e}")
        
        # Test Workflow Service
        try:
            sys.path.append('lambda/workflow_service')
            from handler import WorkflowService
            service_validations['workflow_service'] = {
                'importable': True,
                'has_main_class': True,
                'error': None
            }
            print("  ✅ Workflow Service")
        except Exception as e:
            service_validations['workflow_service'] = {
                'importable': False,
                'has_main_class': False,
                'error': str(e)
            }
            print(f"  ❌ Workflow Service: {e}")
        
        # Test Budget Service
        try:
            sys.path.append('lambda/budget_service')
            from handler import BudgetService
            service_validations['budget_service'] = {
                'importable': True,
                'has_main_class': True,
                'error': None
            }
            print("  ✅ Budget Service")
        except Exception as e:
            service_validations['budget_service'] = {
                'importable': False,
                'has_main_class': False,
                'error': str(e)
            }
            print(f"  ❌ Budget Service: {e}")
        
        # Test Audit Service
        try:
            sys.path.append('lambda/audit_service')
            from handler import DashboardAuditService
            service_validations['audit_service'] = {
                'importable': True,
                'has_main_class': True,
                'error': None
            }
            print("  ✅ Audit Service")
        except Exception as e:
            service_validations['audit_service'] = {
                'importable': False,
                'has_main_class': False,
                'error': str(e)
            }
            print(f"  ❌ Audit Service: {e}")
        
        self.results['tests']['service_interfaces'] = service_validations
        
        # Check if all services are importable
        all_importable = all(
            validation['importable'] for validation in service_validations.values()
        )
        
        if not all_importable:
            failed_services = [
                name for name, validation in service_validations.items()
                if not validation['importable']
            ]
            self.results['recommendations'].append(
                f"Failed to import services: {', '.join(failed_services)}. "
                "Check service implementations and dependencies."
            )
        
        return all_importable
    
    def check_property_based_tests(self):
        """
        Check if property-based tests exist and are properly implemented
        """
        print("🔍 Checking property-based tests...")
        
        pbt_files = [
            'tests/unit/lambda/test_rbac_authorization_properties.py',
            'tests/unit/lambda/test_inventory_operations_properties.py',
            'tests/unit/lambda/test_procurement_operations_properties.py',
            'tests/unit/lambda/test_workflow_management_properties.py',
            'tests/unit/lambda/test_budget_enforcement_properties.py',
            'tests/unit/lambda/test_audit_trail_completeness_properties.py'
        ]
        
        existing_pbt_files = []
        missing_pbt_files = []
        
        for pbt_file in pbt_files:
            if os.path.exists(pbt_file):
                existing_pbt_files.append(pbt_file)
                print(f"  ✅ {pbt_file}")
            else:
                missing_pbt_files.append(pbt_file)
                print(f"  ❌ {pbt_file}")
        
        self.results['tests']['property_based_tests'] = {
            'status': 'passed' if len(missing_pbt_files) == 0 else 'partial',
            'existing_files': existing_pbt_files,
            'missing_files': missing_pbt_files,
            'total_expected': len(pbt_files),
            'total_existing': len(existing_pbt_files)
        }
        
        if missing_pbt_files:
            self.results['recommendations'].append(
                f"Missing property-based tests: {', '.join(missing_pbt_files)}. "
                "Consider implementing remaining PBT tests for comprehensive validation."
            )
        
        return len(existing_pbt_files) > 0
    
    def generate_validation_report(self):
        """
        Generate comprehensive validation report
        """
        print("📊 Generating validation report...")
        
        # Calculate overall status
        test_results = self.results['tests']
        
        passed_tests = 0
        total_tests = 0
        
        for test_name, test_result in test_results.items():
            total_tests += 1
            if isinstance(test_result, dict):
                if test_result.get('status') == 'passed' or test_result.get('overall_success') == True:
                    passed_tests += 1
                elif test_name == 'service_interfaces':
                    # Special handling for service interfaces
                    if all(v.get('importable', False) for v in test_result.values()):
                        passed_tests += 1
                elif test_name == 'property_based_tests':
                    # Partial credit for PBT tests
                    if test_result.get('total_existing', 0) > 0:
                        passed_tests += 0.5
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_status': 'passed' if success_rate >= 80 else 'failed',
            'critical_issues': len([r for r in self.results['recommendations'] if 'error' in r.lower()]),
            'total_recommendations': len(self.results['recommendations'])
        }
        
        self.results['status'] = 'completed'
        
        # Save report to file
        report_file = f"backend_integration_validation_{self.validation_id}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"  📄 Report saved to: {report_file}")
        
        return self.results
    
    def print_summary(self):
        """
        Print validation summary
        """
        summary = self.results['summary']
        
        print("\n" + "=" * 80)
        print("BACKEND SERVICES INTEGRATION VALIDATION SUMMARY")
        print("=" * 80)
        
        if summary['overall_status'] == 'passed':
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        
        print(f"\nTest Results:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed Tests: {summary['passed_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['critical_issues'] > 0:
            print(f"\n⚠️  Critical Issues: {summary['critical_issues']}")
        
        if summary['total_recommendations'] > 0:
            print(f"\n📋 Recommendations ({summary['total_recommendations']}):")
            for i, recommendation in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. {recommendation}")
        
        print(f"\nValidation ID: {self.validation_id}")
        print(f"Timestamp: {self.results['timestamp']}")
        print("=" * 80)
    
    def run_validation(self):
        """
        Run complete validation process
        """
        print("🚀 Starting Backend Services Integration Validation")
        print("=" * 80)
        
        validation_steps = [
            ("Service Files", self.validate_service_files_exist),
            ("Shared Modules", self.validate_shared_modules),
            ("Service Interfaces", self.validate_service_interfaces),
            ("Property-Based Tests", self.check_property_based_tests),
            ("Integration Tests", self.run_integration_tests)
        ]
        
        for step_name, step_function in validation_steps:
            print(f"\n📋 Step: {step_name}")
            try:
                step_function()
            except Exception as e:
                print(f"  ❌ Step failed: {e}")
                self.results['recommendations'].append(
                    f"Validation step '{step_name}' failed: {str(e)}"
                )
        
        # Generate final report
        self.generate_validation_report()
        self.print_summary()
        
        return self.results


def main():
    """
    Main validation function
    """
    validator = BackendIntegrationValidator()
    results = validator.run_validation()
    
    # Exit with appropriate code
    if results['summary']['overall_status'] == 'passed':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()