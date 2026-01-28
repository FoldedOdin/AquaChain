#!/usr/bin/env python3
"""
Production Readiness Validation Script
Validates all aspects of the AquaChain Dashboard Overhaul system for production deployment.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
from pathlib import Path

class ProductionReadinessValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'test_results': {},
            'property_tests': {},
            'security_validation': {},
            'performance_validation': {},
            'audit_validation': {},
            'role_boundary_validation': {},
            'summary': {}
        }
        self.failed_tests = []
        self.passed_tests = []
        
    def run_command(self, command: str, cwd: str = None, timeout: int = 300) -> Tuple[bool, str, str]:
        """Execute a command and return success status, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def validate_unit_tests(self) -> bool:
        """Run all unit tests and validate 100% success rate"""
        print("🧪 Running unit tests validation...")
        
        # Frontend unit tests
        print("  Running frontend unit tests...")
        success, stdout, stderr = self.run_command("npm test -- --run --coverage", cwd="frontend")
        
        if success:
            self.results['test_results']['frontend_unit'] = {
                'status': 'PASSED',
                'output': stdout
            }
            self.passed_tests.append('Frontend Unit Tests')
        else:
            self.results['test_results']['frontend_unit'] = {
                'status': 'FAILED',
                'error': stderr,
                'output': stdout
            }
            self.failed_tests.append('Frontend Unit Tests')
        
        # Backend unit tests
        print("  Running backend unit tests...")
        success, stdout, stderr = self.run_command("python -m pytest tests/unit/ -v --tb=short", cwd=".")
        
        if success:
            self.results['test_results']['backend_unit'] = {
                'status': 'PASSED',
                'output': stdout
            }
            self.passed_tests.append('Backend Unit Tests')
        else:
            self.results['test_results']['backend_unit'] = {
                'status': 'FAILED',
                'error': stderr,
                'output': stdout
            }
            self.failed_tests.append('Backend Unit Tests')
        
        return len(self.failed_tests) == 0
    
    def validate_property_tests(self) -> bool:
        """Validate all 31 correctness properties are implemented and passing"""
        print("🔍 Validating correctness properties...")
        
        # List of all 31 properties that should be implemented
        expected_properties = [
            "Role-Based Dashboard Rendering",
            "Unauthorized Access Prevention and Logging", 
            "API Authorization Validation",
            "Inventory Alert Generation",
            "Audit Trail Completeness",
            "Purchase Order Approval Workflow",
            "Budget Enforcement",
            "Workflow State Transition Validation",
            "Emergency Purchase Expedited Processing",
            "Budget Alert Generation",
            "Authority Matrix Enforcement",
            "Comprehensive Graceful Degradation",
            "Workflow Timeout Escalation",
            "Structured Logging Compliance",
            "Idempotent Operation Guarantee",
            "Comprehensive Error Handling",
            "Notification Delivery for Workflow Changes",
            "Budget Reallocation Authorization",
            "ML Forecast Integration Accuracy",
            "Audit Query and Export Functionality",
            "Transactional Data Consistency",
            "Input Validation and Schema Enforcement",
            "Concurrent Access Data Protection",
            "Caching Strategy Effectiveness",
            "Performance Monitoring and Alerting",
            "Multi-Factor Authentication Enforcement",
            "Session Management Security",
            "Web Security Vulnerability Protection",
            "Security Audit Logging with Tamper Detection",
            "Compliance Reporting Accuracy",
            "Health Check Service Status"
        ]
        
        # Run property tests
        property_test_files = [
            "tests/unit/lambda/test_rbac_authorization_properties.py",
            "tests/unit/lambda/test_authentication_security_properties.py",
            "tests/unit/lambda/test_audit_trail_completeness_properties.py",
            "tests/unit/lambda/test_logging_compliance_properties.py",
            "tests/unit/lambda/test_inventory_operations_properties.py",
            "tests/unit/lambda/test_procurement_operations_properties.py",
            "tests/unit/lambda/test_workflow_management_properties.py",
            "tests/unit/lambda/test_budget_enforcement_properties.py",
            "tests/unit/lambda/test_data_consistency_properties.py",
            "tests/unit/lambda/test_input_validation_properties.py",
            "tests/unit/lambda/test_caching_effectiveness_properties.py",
            "tests/unit/lambda/test_graceful_degradation_properties.py",
            "tests/unit/lambda/test_enhanced_security_properties_fixed.py",
            "frontend/src/components/Dashboard/__tests__/OperationsDashboard.property.test.tsx",
            "frontend/src/components/Dashboard/__tests__/AdminDashboardRestructured.property.test.tsx"
        ]
        
        passed_properties = 0
        failed_properties = 0
        
        for test_file in property_test_files:
            if os.path.exists(test_file):
                print(f"  Running property tests in {test_file}...")
                
                if test_file.endswith('.py'):
                    success, stdout, stderr = self.run_command(f"python -m pytest {test_file} -v")
                else:
                    success, stdout, stderr = self.run_command(f"npm test -- {test_file} --run", cwd="frontend")
                
                if success:
                    passed_properties += 1
                    self.results['property_tests'][test_file] = {
                        'status': 'PASSED',
                        'output': stdout
                    }
                else:
                    failed_properties += 1
                    self.results['property_tests'][test_file] = {
                        'status': 'FAILED',
                        'error': stderr,
                        'output': stdout
                    }
                    self.failed_tests.append(f'Property Tests: {test_file}')
        
        self.results['property_tests']['summary'] = {
            'expected_properties': len(expected_properties),
            'passed_properties': passed_properties,
            'failed_properties': failed_properties,
            'coverage_percentage': (passed_properties / len(expected_properties)) * 100
        }
        
        return failed_properties == 0
    
    def validate_security_controls(self) -> bool:
        """Validate security controls are properly configured"""
        print("🔒 Validating security controls...")
        
        # Run security boundary tests
        success, stdout, stderr = self.run_command("python -m pytest tests/security/ -v")
        
        if success:
            self.results['security_validation']['boundary_tests'] = {
                'status': 'PASSED',
                'output': stdout
            }
            self.passed_tests.append('Security Boundary Tests')
        else:
            self.results['security_validation']['boundary_tests'] = {
                'status': 'FAILED',
                'error': stderr,
                'output': stdout
            }
            self.failed_tests.append('Security Boundary Tests')
        
        # Validate RBAC configuration
        if os.path.exists('validate_rbac_integration.py'):
            success, stdout, stderr = self.run_command("python validate_rbac_integration.py")
            
            if success:
                self.results['security_validation']['rbac_integration'] = {
                    'status': 'PASSED',
                    'output': stdout
                }
                self.passed_tests.append('RBAC Integration')
            else:
                self.results['security_validation']['rbac_integration'] = {
                    'status': 'FAILED',
                    'error': stderr,
                    'output': stdout
                }
                self.failed_tests.append('RBAC Integration')
        
        return 'FAILED' not in [v.get('status', 'UNKNOWN') for v in self.results['security_validation'].values()]
    
    def validate_performance_requirements(self) -> bool:
        """Validate system meets performance requirements"""
        print("⚡ Validating performance requirements...")
        
        # Run performance tests
        success, stdout, stderr = self.run_command("python -m pytest tests/performance/ -v")
        
        if success:
            self.results['performance_validation']['performance_tests'] = {
                'status': 'PASSED',
                'output': stdout
            }
            self.passed_tests.append('Performance Tests')
        else:
            self.results['performance_validation']['performance_tests'] = {
                'status': 'FAILED',
                'error': stderr,
                'output': stdout
            }
            self.failed_tests.append('Performance Tests')
        
        # Run load tests if available
        if os.path.exists('scripts/performance/run_load_tests.py'):
            success, stdout, stderr = self.run_command("python scripts/performance/run_load_tests.py --quick")
            
            if success:
                self.results['performance_validation']['load_tests'] = {
                    'status': 'PASSED',
                    'output': stdout
                }
                self.passed_tests.append('Load Tests')
            else:
                self.results['performance_validation']['load_tests'] = {
                    'status': 'FAILED',
                    'error': stderr,
                    'output': stdout
                }
                self.failed_tests.append('Load Tests')
        
        return 'FAILED' not in [v.get('status', 'UNKNOWN') for v in self.results['performance_validation'].values()]
    
    def validate_audit_logging(self) -> bool:
        """Validate audit logging captures all required events"""
        print("📋 Validating audit logging...")
        
        # Run audit trail tests
        audit_test_files = [
            "tests/unit/lambda/test_audit_trail_completeness_properties.py",
            "tests/unit/lambda/test_audit_trail_completeness_properties_simple.py"
        ]
        
        all_passed = True
        for test_file in audit_test_files:
            if os.path.exists(test_file):
                success, stdout, stderr = self.run_command(f"python -m pytest {test_file} -v")
                
                if success:
                    self.results['audit_validation'][test_file] = {
                        'status': 'PASSED',
                        'output': stdout
                    }
                else:
                    self.results['audit_validation'][test_file] = {
                        'status': 'FAILED',
                        'error': stderr,
                        'output': stdout
                    }
                    self.failed_tests.append(f'Audit Tests: {test_file}')
                    all_passed = False
        
        return all_passed
    
    def validate_role_boundaries(self) -> bool:
        """Validate role boundaries are properly enforced"""
        print("👥 Validating role boundaries...")
        
        # Run integration tests that verify role boundaries
        success, stdout, stderr = self.run_command("python -m pytest tests/integration/ -k role -v")
        
        if success:
            self.results['role_boundary_validation']['integration_tests'] = {
                'status': 'PASSED',
                'output': stdout
            }
            self.passed_tests.append('Role Boundary Integration Tests')
        else:
            self.results['role_boundary_validation']['integration_tests'] = {
                'status': 'FAILED',
                'error': stderr,
                'output': stdout
            }
            self.failed_tests.append('Role Boundary Integration Tests')
        
        # Run frontend role boundary tests
        success, stdout, stderr = self.run_command("npm test -- --testNamePattern='role|Role|RBAC' --run", cwd="frontend")
        
        if success:
            self.results['role_boundary_validation']['frontend_tests'] = {
                'status': 'PASSED',
                'output': stdout
            }
            self.passed_tests.append('Frontend Role Boundary Tests')
        else:
            self.results['role_boundary_validation']['frontend_tests'] = {
                'status': 'FAILED',
                'error': stderr,
                'output': stdout
            }
            self.failed_tests.append('Frontend Role Boundary Tests')
        
        return 'FAILED' not in [v.get('status', 'UNKNOWN') for v in self.results['role_boundary_validation'].values()]
    
    def validate_deployment_readiness(self) -> bool:
        """Validate deployment pipeline and infrastructure"""
        print("🚀 Validating deployment readiness...")
        
        # Run deployment tests if available
        if os.path.exists('tests/deployment/'):
            success, stdout, stderr = self.run_command("python -m pytest tests/deployment/ -v")
            
            if success:
                self.results['deployment_validation'] = {
                    'status': 'PASSED',
                    'output': stdout
                }
                self.passed_tests.append('Deployment Tests')
            else:
                self.results['deployment_validation'] = {
                    'status': 'FAILED',
                    'error': stderr,
                    'output': stdout
                }
                self.failed_tests.append('Deployment Tests')
                return False
        
        return True
    
    def generate_summary(self):
        """Generate validation summary"""
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': len(self.passed_tests),
            'failed_tests': len(self.failed_tests),
            'success_rate': success_rate,
            'passed_test_names': self.passed_tests,
            'failed_test_names': self.failed_tests,
            'production_ready': len(self.failed_tests) == 0 and success_rate == 100.0
        }
        
        self.results['overall_status'] = 'READY' if self.results['summary']['production_ready'] else 'NOT_READY'
    
    def run_validation(self) -> bool:
        """Run complete production readiness validation"""
        print("🎯 Starting Production Readiness Validation")
        print("=" * 60)
        
        validation_steps = [
            ("Unit Tests", self.validate_unit_tests),
            ("Property Tests", self.validate_property_tests),
            ("Security Controls", self.validate_security_controls),
            ("Performance Requirements", self.validate_performance_requirements),
            ("Audit Logging", self.validate_audit_logging),
            ("Role Boundaries", self.validate_role_boundaries),
            ("Deployment Readiness", self.validate_deployment_readiness)
        ]
        
        all_passed = True
        
        for step_name, validation_func in validation_steps:
            print(f"\n📋 {step_name}")
            print("-" * 40)
            
            try:
                step_passed = validation_func()
                if not step_passed:
                    all_passed = False
                    print(f"❌ {step_name} validation failed")
                else:
                    print(f"✅ {step_name} validation passed")
            except Exception as e:
                print(f"❌ {step_name} validation error: {str(e)}")
                all_passed = False
                self.failed_tests.append(f"{step_name} (Exception)")
        
        self.generate_summary()
        
        # Save results to file
        results_file = f"production_readiness_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Validation Results Summary")
        print("=" * 60)
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"Passed: {self.results['summary']['passed_tests']}")
        print(f"Failed: {self.results['summary']['failed_tests']}")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"Production Ready: {'✅ YES' if self.results['summary']['production_ready'] else '❌ NO'}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return all_passed

def main():
    """Main entry point"""
    validator = ProductionReadinessValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🎉 System is READY for production deployment!")
        sys.exit(0)
    else:
        print("\n⚠️  System is NOT READY for production deployment.")
        print("Please address the failed tests before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()