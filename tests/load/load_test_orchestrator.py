"""
Load Test Orchestrator for AquaChain
Coordinates and executes all load tests with comprehensive reporting
"""

import argparse
import json
import time
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import concurrent.futures
import os

@dataclass
class TestSuite:
    """Configuration for a test suite."""
    name: str
    script_path: str
    args: List[str]
    timeout: int = 600  # 10 minutes default timeout
    critical: bool = True  # Whether failure should fail entire test run

@dataclass
class TestResult:
    """Result from running a test suite."""
    suite_name: str
    success: bool
    duration: float
    return_code: int
    stdout: str
    stderr: str
    error_message: Optional[str] = None

@dataclass
class LoadTestReport:
    """Comprehensive load test report."""
    test_run_id: str
    start_time: str
    end_time: str
    total_duration: float
    total_suites: int
    passed_suites: int
    failed_suites: int
    critical_failures: int
    test_results: List[TestResult]
    summary: Dict[str, Any]
    sla_compliance: Dict[str, bool]

class LoadTestOrchestrator:
    """Orchestrates execution of all AquaChain load tests."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.test_run_id = f"load-test-{int(time.time())}"
        self.results: List[TestResult] = []
        
        # Default test suites
        self.test_suites = [
            TestSuite(
                name="IoT Ingestion Load Test",
                script_path="tests/load/test_iot_ingestion_load.py",
                args=["--devices", "100", "--duration", "300", "--burst-devices", "500"],
                timeout=900,  # 15 minutes
                critical=True
            ),
            TestSuite(
                name="API Load Test",
                script_path="tests/load/test_api_load.py",
                args=["--concurrent-users", "50", "--duration", "300"],
                timeout=600,  # 10 minutes
                critical=True
            ),
            TestSuite(
                name="Database Load Test",
                script_path="tests/load/test_database_load.py",
                args=["--concurrent-workers", "50", "--duration", "300"],
                timeout=900,  # 15 minutes
                critical=True
            ),
            TestSuite(
                name="End-to-End Latency Test",
                script_path="tests/load/test_e2e_latency.py",
                args=["--num-tests", "50", "--concurrent-tests", "10"],
                timeout=1200,  # 20 minutes
                critical=True
            )
        ]
    
    def load_config(self, config_file: str):
        """Load test configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Override default test suites with config
            if 'test_suites' in config:
                self.test_suites = []
                for suite_config in config['test_suites']:
                    self.test_suites.append(TestSuite(**suite_config))
            
            # Update test run ID if specified
            if 'test_run_id' in config:
                self.test_run_id = config['test_run_id']
                
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            print("Using default configuration")
    
    def run_test_suite(self, suite: TestSuite) -> TestResult:
        """Run a single test suite."""
        print(f"🚀 Running {suite.name}...")
        
        start_time = time.time()
        
        try:
            # Prepare command
            cmd = [sys.executable, suite.script_path] + suite.args
            
            # Run test with timeout
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite.timeout,
                cwd=os.getcwd()
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = process.returncode == 0
            
            result = TestResult(
                suite_name=suite.name,
                success=success,
                duration=duration,
                return_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr
            )
            
            if success:
                print(f"✅ {suite.name} completed successfully ({duration:.1f}s)")
            else:
                print(f"❌ {suite.name} failed ({duration:.1f}s)")
                result.error_message = f"Test failed with return code {process.returncode}"
            
            return result
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ {suite.name} timed out after {duration:.1f}s")
            
            return TestResult(
                suite_name=suite.name,
                success=False,
                duration=duration,
                return_code=-1,
                stdout="",
                stderr="",
                error_message=f"Test timed out after {suite.timeout} seconds"
            )
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"💥 {suite.name} failed with exception: {e}")
            
            return TestResult(
                suite_name=suite.name,
                success=False,
                duration=duration,
                return_code=-2,
                stdout="",
                stderr=str(e),
                error_message=f"Test failed with exception: {e}"
            )
    
    def run_all_tests(self, parallel: bool = False, max_workers: int = 2) -> LoadTestReport:
        """Run all test suites and generate comprehensive report."""
        print("🔬 AquaChain Load Testing Orchestrator")
        print("=" * 60)
        print(f"Test Run ID: {self.test_run_id}")
        print(f"Total Test Suites: {len(self.test_suites)}")
        print(f"Parallel Execution: {'Yes' if parallel else 'No'}")
        if parallel:
            print(f"Max Workers: {max_workers}")
        print("=" * 60)
        
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()
        
        if parallel:
            # Run tests in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_suite = {
                    executor.submit(self.run_test_suite, suite): suite 
                    for suite in self.test_suites
                }
                
                for future in concurrent.futures.as_completed(future_to_suite):
                    result = future.result()
                    self.results.append(result)
        else:
            # Run tests sequentially
            for suite in self.test_suites:
                result = self.run_test_suite(suite)
                self.results.append(result)
        
        end_time = time.time()
        end_timestamp = datetime.now(timezone.utc).isoformat()
        total_duration = end_time - start_time
        
        # Generate report
        report = self._generate_report(start_timestamp, end_timestamp, total_duration)
        
        return report
    
    def _generate_report(self, start_timestamp: str, end_timestamp: str, 
                        total_duration: float) -> LoadTestReport:
        """Generate comprehensive load test report."""
        passed_suites = sum(1 for result in self.results if result.success)
        failed_suites = len(self.results) - passed_suites
        
        # Count critical failures
        critical_failures = 0
        for result in self.results:
            if not result.success:
                # Find corresponding suite to check if it's critical
                suite = next((s for s in self.test_suites if s.name == result.suite_name), None)
                if suite and suite.critical:
                    critical_failures += 1
        
        # Generate summary
        summary = {
            "overall_success": critical_failures == 0,
            "total_test_time": sum(result.duration for result in self.results),
            "average_test_duration": sum(result.duration for result in self.results) / len(self.results) if self.results else 0,
            "success_rate": (passed_suites / len(self.results)) * 100 if self.results else 0,
            "failed_tests": [result.suite_name for result in self.results if not result.success],
            "longest_test": max(self.results, key=lambda r: r.duration).suite_name if self.results else None,
            "shortest_test": min(self.results, key=lambda r: r.duration).suite_name if self.results else None
        }
        
        # SLA compliance assessment
        sla_compliance = {
            "all_tests_passed": critical_failures == 0,
            "no_timeouts": all(result.return_code != -1 for result in self.results),
            "reasonable_duration": total_duration < 3600,  # Less than 1 hour
            "high_success_rate": summary["success_rate"] >= 90
        }
        
        return LoadTestReport(
            test_run_id=self.test_run_id,
            start_time=start_timestamp,
            end_time=end_timestamp,
            total_duration=total_duration,
            total_suites=len(self.results),
            passed_suites=passed_suites,
            failed_suites=failed_suites,
            critical_failures=critical_failures,
            test_results=self.results,
            summary=summary,
            sla_compliance=sla_compliance
        )
    
    def print_report(self, report: LoadTestReport):
        """Print formatted load test report."""
        print("\n" + "=" * 60)
        print("📊 LOAD TEST REPORT")
        print("=" * 60)
        print(f"Test Run ID: {report.test_run_id}")
        print(f"Start Time: {report.start_time}")
        print(f"End Time: {report.end_time}")
        print(f"Total Duration: {report.total_duration:.1f} seconds ({report.total_duration/60:.1f} minutes)")
        print(f"Total Suites: {report.total_suites}")
        print(f"Passed: {report.passed_suites}")
        print(f"Failed: {report.failed_suites}")
        print(f"Critical Failures: {report.critical_failures}")
        print(f"Success Rate: {report.summary['success_rate']:.1f}%")
        
        print("\n📋 Test Suite Results:")
        print("-" * 60)
        for result in report.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.suite_name} ({result.duration:.1f}s)")
            if not result.success and result.error_message:
                print(f"    Error: {result.error_message}")
        
        print("\n📈 Summary:")
        print("-" * 60)
        print(f"Overall Success: {'✅ YES' if report.summary['overall_success'] else '❌ NO'}")
        print(f"Total Test Time: {report.summary['total_test_time']:.1f}s")
        print(f"Average Test Duration: {report.summary['average_test_duration']:.1f}s")
        
        if report.summary['failed_tests']:
            print(f"Failed Tests: {', '.join(report.summary['failed_tests'])}")
        
        print(f"Longest Test: {report.summary['longest_test']}")
        print(f"Shortest Test: {report.summary['shortest_test']}")
        
        print("\n🎯 SLA Compliance:")
        print("-" * 60)
        for sla_name, passed in report.sla_compliance.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {sla_name.replace('_', ' ').title()}")
        
        # Overall assessment
        print("\n🏆 OVERALL ASSESSMENT:")
        print("=" * 60)
        if report.critical_failures == 0 and all(report.sla_compliance.values()):
            print("✅ ALL LOAD TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        elif report.critical_failures == 0:
            print("⚠️  LOAD TESTS PASSED WITH WARNINGS - REVIEW RECOMMENDED")
        else:
            print("❌ LOAD TESTS FAILED - SYSTEM NOT READY FOR PRODUCTION")
            print(f"   Critical failures: {report.critical_failures}")
    
    def save_report(self, report: LoadTestReport, output_file: str):
        """Save load test report to JSON file."""
        try:
            # Convert dataclass to dict for JSON serialization
            report_dict = asdict(report)
            
            with open(output_file, 'w') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            print(f"📄 Report saved to: {output_file}")
            
        except Exception as e:
            print(f"Warning: Could not save report to {output_file}: {e}")
    
    def generate_html_report(self, report: LoadTestReport, output_file: str):
        """Generate HTML report for better visualization."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>AquaChain Load Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .success { color: green; }
        .failure { color: red; }
        .warning { color: orange; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metric { display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 AquaChain Load Test Report</h1>
        <p><strong>Test Run ID:</strong> {test_run_id}</p>
        <p><strong>Duration:</strong> {total_duration:.1f} seconds</p>
        <p><strong>Overall Status:</strong> 
            <span class="{overall_class}">{overall_status}</span>
        </p>
    </div>
    
    <h2>📊 Summary Metrics</h2>
    <div class="metric">
        <strong>Total Suites:</strong> {total_suites}
    </div>
    <div class="metric">
        <strong>Passed:</strong> <span class="success">{passed_suites}</span>
    </div>
    <div class="metric">
        <strong>Failed:</strong> <span class="failure">{failed_suites}</span>
    </div>
    <div class="metric">
        <strong>Success Rate:</strong> {success_rate:.1f}%
    </div>
    
    <h2>📋 Test Results</h2>
    <table>
        <tr>
            <th>Test Suite</th>
            <th>Status</th>
            <th>Duration (s)</th>
            <th>Error Message</th>
        </tr>
        {test_rows}
    </table>
    
    <h2>🎯 SLA Compliance</h2>
    <table>
        <tr>
            <th>SLA Requirement</th>
            <th>Status</th>
        </tr>
        {sla_rows}
    </table>
    
    <p><em>Generated on {timestamp}</em></p>
</body>
</html>
        """
        
        try:
            # Prepare template variables
            overall_status = "PASSED" if report.critical_failures == 0 else "FAILED"
            overall_class = "success" if report.critical_failures == 0 else "failure"
            
            # Generate test result rows
            test_rows = ""
            for result in report.test_results:
                status_class = "success" if result.success else "failure"
                status_text = "✅ PASS" if result.success else "❌ FAIL"
                error_msg = result.error_message or ""
                
                test_rows += f"""
                <tr>
                    <td>{result.suite_name}</td>
                    <td><span class="{status_class}">{status_text}</span></td>
                    <td>{result.duration:.1f}</td>
                    <td>{error_msg}</td>
                </tr>
                """
            
            # Generate SLA compliance rows
            sla_rows = ""
            for sla_name, passed in report.sla_compliance.items():
                status_class = "success" if passed else "failure"
                status_text = "✅ PASS" if passed else "❌ FAIL"
                sla_display = sla_name.replace('_', ' ').title()
                
                sla_rows += f"""
                <tr>
                    <td>{sla_display}</td>
                    <td><span class="{status_class}">{status_text}</span></td>
                </tr>
                """
            
            # Fill template
            html_content = html_template.format(
                test_run_id=report.test_run_id,
                total_duration=report.total_duration,
                overall_class=overall_class,
                overall_status=overall_status,
                total_suites=report.total_suites,
                passed_suites=report.passed_suites,
                failed_suites=report.failed_suites,
                success_rate=report.summary['success_rate'],
                test_rows=test_rows,
                sla_rows=sla_rows,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            with open(output_file, 'w') as f:
                f.write(html_content)
            
            print(f"📄 HTML report saved to: {output_file}")
            
        except Exception as e:
            print(f"Warning: Could not generate HTML report: {e}")

def main():
    """Main function to run load test orchestrator."""
    parser = argparse.ArgumentParser(description='AquaChain Load Test Orchestrator')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--max-workers', type=int, default=2, help='Max parallel workers (default: 2)')
    parser.add_argument('--output', type=str, default=f'load_test_report_{int(time.time())}.json', 
                       help='Output report file')
    parser.add_argument('--html-output', type=str, help='HTML report output file')
    parser.add_argument('--quiet', action='store_true', help='Suppress detailed output')
    
    args = parser.parse_args()
    
    try:
        orchestrator = LoadTestOrchestrator(config_file=args.config)
        
        if args.config:
            orchestrator.load_config(args.config)
        
        # Run all tests
        report = orchestrator.run_all_tests(
            parallel=args.parallel,
            max_workers=args.max_workers
        )
        
        # Print report unless quiet mode
        if not args.quiet:
            orchestrator.print_report(report)
        
        # Save JSON report
        orchestrator.save_report(report, args.output)
        
        # Generate HTML report if requested
        if args.html_output:
            orchestrator.generate_html_report(report, args.html_output)
        
        # Return appropriate exit code
        if report.critical_failures == 0:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"💥 Load test orchestrator failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())