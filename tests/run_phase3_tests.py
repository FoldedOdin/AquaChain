#!/usr/bin/env python3
"""
Phase 3 Test Execution Script
Runs all Phase 3 tests and generates comprehensive report
"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Test execution and reporting"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_suites': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }
    
    def run_test_suite(self, name, test_path, description):
        """Run a test suite and capture results"""
        print(f"\n{'='*70}")
        print(f"Running {name}")
        print(f"Description: {description}")
        print(f"{'='*70}\n")
        
        try:
            result = subprocess.run(
                ['pytest', test_path, '-v', '--tb=short', '--json-report', '--json-report-file=temp_report.json'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse JSON report if available
            report_file = Path('temp_report.json')
            if report_file.exists():
                with open(report_file) as f:
                    report = json.load(f)
                
                self.results['test_suites'][name] = {
                    'description': description,
                    'passed': report.get('summary', {}).get('passed', 0),
                    'failed': report.get('summary', {}).get('failed', 0),
                    'skipped': report.get('summary', {}).get('skipped', 0),
                    'duration': report.get('duration', 0),
                    'exit_code': result.returncode
                }
                
                # Update summary
                self.results['summary']['total'] += report.get('summary', {}).get('total', 0)
                self.results['summary']['passed'] += report.get('summary', {}).get('passed', 0)
                self.results['summary']['failed'] += report.get('summary', {}).get('failed', 0)
                self.results['summary']['skipped'] += report.get('summary', {}).get('skipped', 0)
                
                report_file.unlink()
            else:
                # Fallback if JSON report not available
                self.results['test_suites'][name] = {
                    'description': description,
                    'exit_code': result.returncode,
                    'output': result.stdout
                }
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"❌ {name} timed out after 300 seconds")
            self.results['test_suites'][name] = {
                'description': description,
                'error': 'Timeout after 300 seconds'
            }
            return False
        except Exception as e:
            print(f"❌ Error running {name}: {e}")
            self.results['test_suites'][name] = {
                'description': description,
                'error': str(e)
            }
            return False
    
    def generate_report(self):
        """Generate test execution report"""
        print(f"\n{'='*70}")
        print("PHASE 3 TEST EXECUTION SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"\nOverall Results:")
        print(f"  Total Tests: {self.results['summary']['total']}")
        print(f"  ✅ Passed: {self.results['summary']['passed']}")
        print(f"  ❌ Failed: {self.results['summary']['failed']}")
        print(f"  ⏭️  Skipped: {self.results['summary']['skipped']}")
        
        if self.results['summary']['total'] > 0:
            pass_rate = (self.results['summary']['passed'] / self.results['summary']['total']) * 100
            print(f"  Pass Rate: {pass_rate:.1f}%")
        
        print(f"\nTest Suite Results:")
        for suite_name, suite_results in self.results['test_suites'].items():
            print(f"\n  {suite_name}:")
            print(f"    Description: {suite_results.get('description', 'N/A')}")
            
            if 'error' in suite_results:
                print(f"    ❌ Error: {suite_results['error']}")
            elif 'exit_code' in suite_results:
                if suite_results['exit_code'] == 0:
                    print(f"    ✅ Status: PASSED")
                else:
                    print(f"    ❌ Status: FAILED (exit code: {suite_results['exit_code']})")
                
                if 'passed' in suite_results:
                    print(f"    Passed: {suite_results['passed']}")
                    print(f"    Failed: {suite_results['failed']}")
                    print(f"    Skipped: {suite_results['skipped']}")
                    print(f"    Duration: {suite_results['duration']:.2f}s")
        
        # Save report to file
        report_file = Path('phase3_test_report.json')
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return overall success
        return self.results['summary']['failed'] == 0


def main():
    """Main test execution"""
    runner = TestRunner()
    
    # Define test suites
    test_suites = [
        {
            'name': 'End-to-End Integration Tests',
            'path': 'tests/integration/test_phase3_e2e.py',
            'description': 'Tests complete workflows for ML monitoring, OTA updates, certificate rotation, and dependency scanning'
        },
        {
            'name': 'Performance Tests',
            'path': 'tests/performance/test_phase3_performance.py',
            'description': 'Validates latency requirements and load handling capabilities'
        },
        {
            'name': 'Security Tests',
            'path': 'tests/security/test_phase3_security.py',
            'description': 'Validates security controls, encryption, and compliance requirements'
        },
        {
            'name': 'Monitoring and Alerting Tests',
            'path': 'tests/monitoring/test_phase3_monitoring.py',
            'description': 'Validates CloudWatch alarms and SNS notification delivery'
        }
    ]
    
    # Run all test suites
    all_passed = True
    for suite in test_suites:
        passed = runner.run_test_suite(
            suite['name'],
            suite['path'],
            suite['description']
        )
        all_passed = all_passed and passed
    
    # Generate final report
    success = runner.generate_report()
    
    # Exit with appropriate code
    if success:
        print("\n✅ All Phase 3 tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some Phase 3 tests failed. Review the report for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
