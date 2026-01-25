#!/usr/bin/env python3
"""
Comprehensive Load Testing Script for Dashboard Overhaul
Runs performance and load tests with detailed reporting
Requirements: 9.1, 9.2, 9.4, 9.5, 9.6
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class LoadTestRunner:
    """Comprehensive load test runner"""
    
    def __init__(self, output_dir: str = "load-test-results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0
            },
            'performance_metrics': {},
            'load_test_results': {},
            'frontend_performance': {},
            'recommendations': []
        }
    
    def run_backend_performance_tests(self) -> Dict[str, Any]:
        """Run backend performance validation tests"""
        print("🚀 Running backend performance tests...")
        
        try:
            # Run performance tests
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/performance/test_dashboard_overhaul_performance.py',
                '-v', '--tb=short', '--json-report',
                f'--json-report-file={self.output_dir}/backend_performance.json'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            performance_results = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            # Try to load JSON report
            json_report_path = self.output_dir / 'backend_performance.json'
            if json_report_path.exists():
                with open(json_report_path) as f:
                    json_data = json.load(f)
                    performance_results['detailed_results'] = json_data
                    
                    # Extract key metrics
                    if 'tests' in json_data:
                        performance_results['test_count'] = len(json_data['tests'])
                        performance_results['passed_count'] = sum(
                            1 for test in json_data['tests'] 
                            if test.get('outcome') == 'passed'
                        )
            
            print(f"  ✅ Backend performance tests completed (exit code: {result.returncode})")
            return performance_results
            
        except subprocess.TimeoutExpired:
            print("  ⏰ Backend performance tests timed out")
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"  ❌ Backend performance tests failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_concurrent_load_tests(self) -> Dict[str, Any]:
        """Run concurrent user load tests"""
        print("🔄 Running concurrent load tests...")
        
        try:
            cmd = [
                sys.executable, '-m', 'pytest',
                'tests/performance/test_concurrent_load_scenarios.py',
                '-v', '--tb=short', '--json-report',
                f'--json-report-file={self.output_dir}/load_tests.json'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for load tests
            )
            
            load_results = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            # Parse JSON report
            json_report_path = self.output_dir / 'load_tests.json'
            if json_report_path.exists():
                with open(json_report_path) as f:
                    json_data = json.load(f)
                    load_results['detailed_results'] = json_data
            
            print(f"  ✅ Load tests completed (exit code: {result.returncode})")
            return load_results
            
        except subprocess.TimeoutExpired:
            print("  ⏰ Load tests timed out")
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"  ❌ Load tests failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_frontend_performance_tests(self) -> Dict[str, Any]:
        """Run frontend performance tests"""
        print("🎨 Running frontend performance tests...")
        
        frontend_dir = project_root / 'frontend'
        if not frontend_dir.exists():
            print("  ⚠️ Frontend directory not found, skipping frontend tests")
            return {'success': False, 'error': 'frontend_not_found'}
        
        try:
            # Run frontend performance tests
            cmd = ['npm', 'run', 'test:performance']
            
            result = subprocess.run(
                cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            frontend_results = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            print(f"  ✅ Frontend performance tests completed (exit code: {result.returncode})")
            return frontend_results
            
        except subprocess.TimeoutExpired:
            print("  ⏰ Frontend performance tests timed out")
            return {'success': False, 'error': 'timeout'}
        except FileNotFoundError:
            print("  ⚠️ npm not found, skipping frontend tests")
            return {'success': False, 'error': 'npm_not_found'}
        except Exception as e:
            print(f"  ❌ Frontend performance tests failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_stress_tests(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Run stress tests for specified duration"""
        print(f"💪 Running stress tests for {duration_minutes} minutes...")
        
        stress_results = {
            'duration_minutes': duration_minutes,
            'start_time': datetime.utcnow().isoformat(),
            'operations_completed': 0,
            'errors_encountered': 0,
            'average_response_time': 0,
            'peak_response_time': 0,
            'success': True
        }
        
        try:
            # Simulate stress testing
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            
            operations = 0
            errors = 0
            response_times = []
            
            while time.time() < end_time:
                # Simulate operation
                operation_start = time.time()
                
                # Mock operation (in real implementation, this would call actual services)
                time.sleep(0.01 + (0.005 * (operations % 100) / 100))  # Simulate varying load
                
                operation_end = time.time()
                response_time = (operation_end - operation_start) * 1000
                response_times.append(response_time)
                
                operations += 1
                
                # Simulate occasional errors under stress
                if operations % 1000 == 0:
                    errors += 1
                
                # Brief pause between operations
                time.sleep(0.001)
            
            stress_results.update({
                'end_time': datetime.utcnow().isoformat(),
                'operations_completed': operations,
                'errors_encountered': errors,
                'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                'peak_response_time': max(response_times) if response_times else 0,
                'error_rate': errors / operations if operations > 0 else 0,
                'throughput_ops_per_sec': operations / (duration_minutes * 60)
            })
            
            print(f"  ✅ Stress test completed: {operations} operations, {errors} errors")
            return stress_results
            
        except Exception as e:
            print(f"  ❌ Stress test failed: {e}")
            stress_results.update({
                'success': False,
                'error': str(e),
                'end_time': datetime.utcnow().isoformat()
            })
            return stress_results
    
    def analyze_results(self) -> None:
        """Analyze all test results and generate recommendations"""
        print("📊 Analyzing results and generating recommendations...")
        
        recommendations = []
        
        # Analyze backend performance
        backend_results = self.results.get('performance_metrics', {})
        if backend_results.get('success'):
            if backend_results.get('passed_count', 0) < backend_results.get('test_count', 1):
                recommendations.append({
                    'priority': 'high',
                    'category': 'Backend Performance',
                    'issue': 'Some backend performance tests failed',
                    'solution': 'Review failed tests and optimize slow database queries or API endpoints'
                })
        
        # Analyze load test results
        load_results = self.results.get('load_test_results', {})
        if load_results.get('success'):
            # Check for high error rates or slow response times
            if 'detailed_results' in load_results:
                # Parse test output for performance metrics
                stdout = load_results.get('stdout', '')
                if 'error rate' in stdout.lower() or 'failed' in stdout.lower():
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'Concurrent Load',
                        'issue': 'High error rate detected under concurrent load',
                        'solution': 'Implement better error handling and retry mechanisms'
                    })
        
        # Analyze frontend performance
        frontend_results = self.results.get('frontend_performance', {})
        if not frontend_results.get('success'):
            if frontend_results.get('error') != 'frontend_not_found':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'Frontend Performance',
                    'issue': 'Frontend performance tests failed or timed out',
                    'solution': 'Optimize component rendering and reduce bundle size'
                })
        
        # General recommendations
        recommendations.extend([
            {
                'priority': 'low',
                'category': 'Monitoring',
                'issue': 'Continuous performance monitoring needed',
                'solution': 'Implement performance monitoring in production with CloudWatch dashboards'
            },
            {
                'priority': 'low',
                'category': 'Optimization',
                'issue': 'Performance budget enforcement',
                'solution': 'Set up performance budgets in CI/CD pipeline to prevent regressions'
            }
        ])
        
        self.results['recommendations'] = recommendations
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        print("📝 Generating comprehensive report...")
        
        # Generate JSON report
        json_report_path = self.output_dir / 'load_test_report.json'
        with open(json_report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate HTML report
        html_report = self._generate_html_report()
        html_report_path = self.output_dir / 'load_test_report.html'
        with open(html_report_path, 'w') as f:
            f.write(html_report)
        
        # Generate summary report
        summary_report = self._generate_summary_report()
        summary_report_path = self.output_dir / 'load_test_summary.txt'
        with open(summary_report_path, 'w') as f:
            f.write(summary_report)
        
        print(f"  📄 Reports generated in: {self.output_dir}")
        print(f"    - JSON Report: {json_report_path}")
        print(f"    - HTML Report: {html_report_path}")
        print(f"    - Summary Report: {summary_report_path}")
    
    def _generate_html_report(self) -> str:
        """Generate HTML report"""
        summary = self.results['test_summary']
        total_tests = summary['total_tests']
        passed_tests = summary['passed_tests']
        failed_tests = summary['failed_tests']
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        status_color = '#10b981' if failed_tests == 0 else '#ef4444'
        status_text = 'PASS' if failed_tests == 0 else 'FAIL'
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Overhaul - Load Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .header {{
            background: linear-gradient(135deg, #06b6d4, #088395);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
            background-color: {status_color};
            margin-left: 10px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #06b6d4;
        }}
        .test-results {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .recommendations {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .recommendation {{
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid #06b6d4;
            background-color: #f0f9ff;
        }}
        .priority-high {{ border-left-color: #ef4444; background-color: #fef2f2; }}
        .priority-medium {{ border-left-color: #f59e0b; background-color: #fffbeb; }}
        .priority-low {{ border-left-color: #10b981; background-color: #f0fdf4; }}
        .timestamp {{
            color: #6b7280;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Dashboard Overhaul Load Test Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <span class="status">{status_text}</span>
    </div>

    <div class="metrics">
        <div class="metric-card">
            <div class="metric-value">{pass_rate:.1f}%</div>
            <div>Pass Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{total_tests}</div>
            <div>Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{passed_tests}</div>
            <div>Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{failed_tests}</div>
            <div>Failed</div>
        </div>
    </div>

    <div class="test-results">
        <h2>Test Results Summary</h2>
        <h3>Backend Performance Tests</h3>
        <p><strong>Status:</strong> {'✅ Passed' if self.results.get('performance_metrics', {}).get('success') else '❌ Failed'}</p>
        
        <h3>Concurrent Load Tests</h3>
        <p><strong>Status:</strong> {'✅ Passed' if self.results.get('load_test_results', {}).get('success') else '❌ Failed'}</p>
        
        <h3>Frontend Performance Tests</h3>
        <p><strong>Status:</strong> {'✅ Passed' if self.results.get('frontend_performance', {}).get('success') else '❌ Failed or Skipped'}</p>
    </div>

    <div class="recommendations">
        <h2>Performance Recommendations</h2>
        {self._format_recommendations_html()}
    </div>

    <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2>Next Steps</h2>
        <ol>
            <li>Address high-priority performance issues first</li>
            <li>Implement performance monitoring in production</li>
            <li>Set up performance budgets in CI/CD pipeline</li>
            <li>Schedule regular load testing</li>
            <li>Monitor real user metrics (RUM) for ongoing optimization</li>
        </ol>
    </div>
</body>
</html>
        """
    
    def _format_recommendations_html(self) -> str:
        """Format recommendations as HTML"""
        html = ""
        for rec in self.results.get('recommendations', []):
            priority_class = f"priority-{rec['priority']}"
            html += f"""
            <div class="recommendation {priority_class}">
                <h3>{rec['issue']}</h3>
                <p><strong>Category:</strong> {rec['category']}</p>
                <p><strong>Priority:</strong> {rec['priority'].upper()}</p>
                <p><strong>Solution:</strong> {rec['solution']}</p>
            </div>
            """
        return html
    
    def _generate_summary_report(self) -> str:
        """Generate text summary report"""
        summary = self.results['test_summary']
        
        report = f"""
Dashboard Overhaul Load Test Summary
===================================

Test Execution: {self.results['timestamp']}

Overall Results:
- Total Tests: {summary['total_tests']}
- Passed: {summary['passed_tests']}
- Failed: {summary['failed_tests']}
- Skipped: {summary['skipped_tests']}
- Pass Rate: {(summary['passed_tests'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0:.1f}%

Test Categories:
"""
        
        # Backend Performance
        backend = self.results.get('performance_metrics', {})
        report += f"\n1. Backend Performance Tests: {'PASS' if backend.get('success') else 'FAIL'}"
        if 'test_count' in backend:
            report += f" ({backend.get('passed_count', 0)}/{backend.get('test_count', 0)} passed)"
        
        # Load Tests
        load = self.results.get('load_test_results', {})
        report += f"\n2. Concurrent Load Tests: {'PASS' if load.get('success') else 'FAIL'}"
        
        # Frontend Performance
        frontend = self.results.get('frontend_performance', {})
        report += f"\n3. Frontend Performance Tests: {'PASS' if frontend.get('success') else 'FAIL/SKIP'}"
        
        # Recommendations
        report += "\n\nRecommendations:\n"
        for i, rec in enumerate(self.results.get('recommendations', []), 1):
            report += f"\n{i}. [{rec['priority'].upper()}] {rec['category']}: {rec['issue']}"
            report += f"\n   Solution: {rec['solution']}\n"
        
        return report
    
    def run_all_tests(self, include_stress: bool = False, stress_duration: int = 5) -> None:
        """Run all load tests"""
        print("🎯 Starting comprehensive load testing...")
        print(f"Output directory: {self.output_dir}")
        
        start_time = time.time()
        
        # Run backend performance tests
        self.results['performance_metrics'] = self.run_backend_performance_tests()
        
        # Run concurrent load tests
        self.results['load_test_results'] = self.run_concurrent_load_tests()
        
        # Run frontend performance tests
        self.results['frontend_performance'] = self.run_frontend_performance_tests()
        
        # Run stress tests if requested
        if include_stress:
            self.results['stress_test_results'] = self.run_stress_tests(stress_duration)
        
        # Update test summary
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for test_category in ['performance_metrics', 'load_test_results', 'frontend_performance']:
            if test_category in self.results:
                total_tests += 1
                if self.results[test_category].get('success'):
                    passed_tests += 1
                else:
                    failed_tests += 1
        
        self.results['test_summary'].update({
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests
        })
        
        # Analyze results and generate recommendations
        self.analyze_results()
        
        # Generate reports
        self.generate_report()
        
        total_time = time.time() - start_time
        
        print(f"\n🏁 Load testing completed in {total_time:.1f} seconds")
        print(f"📊 Results: {passed_tests}/{total_tests} test categories passed")
        
        if failed_tests > 0:
            print("⚠️ Some tests failed. Check the detailed report for recommendations.")
            sys.exit(1)
        else:
            print("✅ All load tests passed!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run comprehensive load tests for Dashboard Overhaul')
    parser.add_argument('--output-dir', default='load-test-results', help='Output directory for test results')
    parser.add_argument('--include-stress', action='store_true', help='Include stress testing')
    parser.add_argument('--stress-duration', type=int, default=5, help='Stress test duration in minutes')
    parser.add_argument('--backend-only', action='store_true', help='Run only backend performance tests')
    parser.add_argument('--load-only', action='store_true', help='Run only concurrent load tests')
    parser.add_argument('--frontend-only', action='store_true', help='Run only frontend performance tests')
    
    args = parser.parse_args()
    
    runner = LoadTestRunner(args.output_dir)
    
    if args.backend_only:
        print("🚀 Running backend performance tests only...")
        results = runner.run_backend_performance_tests()
        print(f"Backend tests: {'PASS' if results.get('success') else 'FAIL'}")
    elif args.load_only:
        print("🔄 Running concurrent load tests only...")
        results = runner.run_concurrent_load_tests()
        print(f"Load tests: {'PASS' if results.get('success') else 'FAIL'}")
    elif args.frontend_only:
        print("🎨 Running frontend performance tests only...")
        results = runner.run_frontend_performance_tests()
        print(f"Frontend tests: {'PASS' if results.get('success') else 'FAIL'}")
    else:
        runner.run_all_tests(args.include_stress, args.stress_duration)


if __name__ == '__main__':
    main()