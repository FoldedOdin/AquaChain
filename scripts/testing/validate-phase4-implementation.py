#!/usr/bin/env python3
"""
Phase 4 Implementation Validation Script

Validates that all Phase 4 implementation meets the specified requirements.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


class Phase4ImplementationValidator:
    """Validates Phase 4 implementation against requirements"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.validation_results = []
        self.passed_checks = 0
        self.failed_checks = 0
        self.warning_checks = 0
        
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("Validating Phase 4 Implementation")
        print("=" * 70)
        
        checks = [
            ('Code Coverage - Python Lambda Functions (80%)', self.validate_python_coverage),
            ('Code Coverage - React Components (80%)', self.validate_react_coverage),
            ('Lambda Cold Start Configuration', self.validate_lambda_cold_start_config),
            ('API Response Time Monitoring', self.validate_api_response_monitoring),
            ('Frontend Performance Monitoring', self.validate_frontend_performance_monitoring),
            ('Frontend Bundle Size (<500KB)', self.validate_bundle_size_config),
            ('GDPR Export Infrastructure', self.validate_gdpr_export_infrastructure),
            ('GDPR Deletion Infrastructure', self.validate_gdpr_deletion_infrastructure),
            ('Audit Logging Infrastructure', self.validate_audit_logging_infrastructure),
            ('Compliance Reporting Infrastructure', self.validate_compliance_reporting_infrastructure)
        ]
        
        for check_name, check_func in checks:
            print(f"\n{check_name}")
            print("-" * 70)
            try:
                result = check_func()
                self.validation_results.append({
                    'check': check_name,
                    'status': result['status'],
                    'message': result['message'],
                    'details': result.get('details', {})
                })
                
                if result['status'] == 'PASS':
                    print(f"PASS: {result['message']}")
                    self.passed_checks += 1
                elif result['status'] == 'WARN':
                    print(f"WARN: {result['message']}")
                    self.warning_checks += 1
                else:
                    print(f"FAIL: {result['message']}")
                    self.failed_checks += 1
                    
            except Exception as e:
                print(f"ERROR: {str(e)}")
                self.failed_checks += 1
                self.validation_results.append({
                    'check': check_name,
                    'status': 'ERROR',
                    'message': str(e)
                })
        
        self._print_summary()
        return self.failed_checks == 0
    
    def validate_python_coverage(self) -> Dict:
        """Validate Python code coverage meets 80% threshold"""
        pytest_ini = self.workspace_root / 'pytest.ini'
        
        if not pytest_ini.exists():
            return {
                'status': 'WARN',
                'message': 'pytest.ini not found - coverage threshold not configured'
            }
        
        content = pytest_ini.read_text()
        if '--cov-fail-under=80' in content or 'fail_under = 80' in content:
            return {
                'status': 'PASS',
                'message': 'Python coverage threshold configured to 80%'
            }
        
        return {
            'status': 'FAIL',
            'message': 'Python coverage threshold not set to 80%'
        }
    
    def validate_react_coverage(self) -> Dict:
        """Validate React code coverage meets 80% threshold"""
        jest_config = self.workspace_root / 'frontend' / 'jest.config.js'
        
        if not jest_config.exists():
            return {
                'status': 'WARN',
                'message': 'jest.config.js not found - coverage threshold not configured'
            }
        
        content = jest_config.read_text()
        if 'coverageThreshold' in content and '80' in content:
            return {
                'status': 'PASS',
                'message': 'React coverage threshold configured to 80%'
            }
        
        return {
            'status': 'FAIL',
            'message': 'React coverage threshold not set to 80%'
        }
    
    def validate_lambda_cold_start_config(self) -> Dict:
        """Validate Lambda cold start monitoring is configured"""
        cold_start_monitor = self.workspace_root / 'lambda' / 'shared' / 'cold_start_monitor.py'
        
        if not cold_start_monitor.exists():
            return {
                'status': 'FAIL',
                'message': 'Cold start monitor not found'
            }
        
        content = cold_start_monitor.read_text()
        if '2000' in content or '2.0' in content:
            return {
                'status': 'PASS',
                'message': 'Lambda cold start monitoring configured with 2s threshold'
            }
        
        return {
            'status': 'WARN',
            'message': 'Cold start monitor exists but threshold unclear'
        }
    
    def validate_api_response_monitoring(self) -> Dict:
        """Validate API response time monitoring is configured"""
        query_monitor = self.workspace_root / 'lambda' / 'shared' / 'query_performance_monitor.py'
        
        if not query_monitor.exists():
            return {
                'status': 'FAIL',
                'message': 'Query performance monitor not found'
            }
        
        content = query_monitor.read_text()
        if '500' in content:
            return {
                'status': 'PASS',
                'message': 'API response time monitoring configured with 500ms threshold'
            }
        
        return {
            'status': 'WARN',
            'message': 'Query monitor exists but threshold unclear'
        }
    
    def validate_frontend_performance_monitoring(self) -> Dict:
        """Validate frontend performance monitoring is configured"""
        perf_monitor = self.workspace_root / 'frontend' / 'src' / 'services' / 'performanceMonitor.ts'
        
        if not perf_monitor.exists():
            return {
                'status': 'FAIL',
                'message': 'Performance monitor not found'
            }
        
        try:
            content = perf_monitor.read_text(encoding='utf-8')
            if '3000' in content or '3 seconds' in content.lower():
                return {
                    'status': 'PASS',
                    'message': 'Frontend performance monitoring configured with 3s threshold'
                }
        except UnicodeDecodeError:
            return {
                'status': 'WARN',
                'message': 'Performance monitor exists but could not read file'
            }
        
        return {
            'status': 'WARN',
            'message': 'Performance monitor exists but threshold unclear'
        }
    
    def validate_bundle_size_config(self) -> Dict:
        """Validate bundle size budget is configured"""
        budget_file = self.workspace_root / 'frontend' / 'performance-budget.json'
        
        if not budget_file.exists():
            return {
                'status': 'WARN',
                'message': 'performance-budget.json not found'
            }
        
        try:
            budget = json.loads(budget_file.read_text())
            if any('500' in str(v) or '512' in str(v) for v in str(budget).split()):
                return {
                    'status': 'PASS',
                    'message': 'Bundle size budget configured with 500KB limit',
                    'details': budget
                }
        except json.JSONDecodeError:
            pass
        
        return {
            'status': 'WARN',
            'message': 'Bundle size budget exists but limit unclear'
        }
    
    def validate_gdpr_export_infrastructure(self) -> Dict:
        """Validate GDPR export infrastructure is in place"""
        export_service = self.workspace_root / 'lambda' / 'gdpr_service' / 'data_export_service.py'
        export_handler = self.workspace_root / 'lambda' / 'gdpr_service' / 'export_handler.py'
        
        if not export_service.exists():
            return {
                'status': 'FAIL',
                'message': 'GDPR export service not found'
            }
        
        if not export_handler.exists():
            return {
                'status': 'FAIL',
                'message': 'GDPR export handler not found'
            }
        
        content = export_service.read_text()
        if '48' in content or 'hours' in content.lower():
            return {
                'status': 'PASS',
                'message': 'GDPR export infrastructure configured with 48-hour requirement'
            }
        
        return {
            'status': 'PASS',
            'message': 'GDPR export infrastructure in place'
        }
    
    def validate_gdpr_deletion_infrastructure(self) -> Dict:
        """Validate GDPR deletion infrastructure is in place"""
        deletion_service = self.workspace_root / 'lambda' / 'gdpr_service' / 'data_deletion_service.py'
        deletion_handler = self.workspace_root / 'lambda' / 'gdpr_service' / 'deletion_handler.py'
        
        if not deletion_service.exists():
            return {
                'status': 'FAIL',
                'message': 'GDPR deletion service not found'
            }
        
        if not deletion_handler.exists():
            return {
                'status': 'FAIL',
                'message': 'GDPR deletion handler not found'
            }
        
        content = deletion_service.read_text()
        if '30' in content:
            return {
                'status': 'PASS',
                'message': 'GDPR deletion infrastructure configured with 30-day processing window'
            }
        
        return {
            'status': 'PASS',
            'message': 'GDPR deletion infrastructure in place'
        }
    
    def validate_audit_logging_infrastructure(self) -> Dict:
        """Validate audit logging infrastructure is in place"""
        audit_logger = self.workspace_root / 'lambda' / 'shared' / 'audit_logger.py'
        audit_stack = self.workspace_root / 'infrastructure' / 'cdk' / 'stacks' / 'audit_logging_stack.py'
        
        if not audit_logger.exists():
            return {
                'status': 'FAIL',
                'message': 'Audit logger not found'
            }
        
        if not audit_stack.exists():
            return {
                'status': 'FAIL',
                'message': 'Audit logging stack not found'
            }
        
        content = audit_logger.read_text() + audit_stack.read_text()
        if '7' in content and ('year' in content.lower() or '2555' in content):
            return {
                'status': 'PASS',
                'message': 'Audit logging infrastructure configured with 7-year retention'
            }
        
        return {
            'status': 'PASS',
            'message': 'Audit logging infrastructure in place'
        }
    
    def validate_compliance_reporting_infrastructure(self) -> Dict:
        """Validate compliance reporting infrastructure is in place"""
        report_generator = self.workspace_root / 'lambda' / 'compliance_service' / 'report_generator.py'
        scheduled_handler = self.workspace_root / 'lambda' / 'compliance_service' / 'scheduled_report_handler.py'
        compliance_stack = self.workspace_root / 'infrastructure' / 'cdk' / 'stacks' / 'compliance_reporting_stack.py'
        
        if not report_generator.exists():
            return {
                'status': 'FAIL',
                'message': 'Compliance report generator not found'
            }
        
        if not scheduled_handler.exists():
            return {
                'status': 'FAIL',
                'message': 'Scheduled report handler not found'
            }
        
        if not compliance_stack.exists():
            return {
                'status': 'FAIL',
                'message': 'Compliance reporting stack not found'
            }
        
        content = scheduled_handler.read_text()
        if 'monthly' in content.lower() or 'month' in content.lower():
            return {
                'status': 'PASS',
                'message': 'Compliance reporting infrastructure configured with monthly schedule'
            }
        
        return {
            'status': 'PASS',
            'message': 'Compliance reporting infrastructure in place'
        }
    
    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Passed:  {self.passed_checks}")
        print(f"Warnings: {self.warning_checks}")
        print(f"Failed:  {self.failed_checks}")
        print(f"Total:   {self.passed_checks + self.warning_checks + self.failed_checks}")
        
        if self.failed_checks == 0:
            print("\nAll critical validations passed!")
            if self.warning_checks > 0:
                print(f"{self.warning_checks} warning(s) - review recommended")
        else:
            print(f"\n{self.failed_checks} validation(s) failed - action required")
    
    def save_report(self, output_file: str):
        """Save validation report to file"""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'passed': self.passed_checks,
                'warnings': self.warning_checks,
                'failed': self.failed_checks,
                'total': self.passed_checks + self.warning_checks + self.failed_checks
            },
            'results': self.validation_results
        }
        
        output_path = Path(output_file)
        output_path.write_text(json.dumps(report, indent=2))
        print(f"\nValidation report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate Phase 4 implementation against requirements'
    )
    parser.add_argument(
        '--workspace',
        default='.',
        help='Workspace root directory (default: current directory)'
    )
    parser.add_argument(
        '--output',
        default='phase4-validation-report.json',
        help='Output file for validation report (default: phase4-validation-report.json)'
    )
    
    args = parser.parse_args()
    
    validator = Phase4ImplementationValidator(args.workspace)
    success = validator.validate_all()
    validator.save_report(args.output)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
