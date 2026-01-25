#!/usr/bin/env python3
"""
Deployment validation test runner
Runs all deployment-related tests and generates a comprehensive report
"""

import pytest
import sys
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

def run_deployment_tests():
    """
    Run all deployment validation tests and generate report
    """
    
    print("=" * 80)
    print("AquaChain Dashboard Overhaul - Deployment Validation Tests")
    print("=" * 80)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Test configuration
    test_files = [
        "test_deployment_validation.py",
        "test_feature_flags.py",
        "test_rollback_procedures.py"
    ]
    
    # Results storage
    test_results = {
        "start_time": datetime.now(timezone.utc).isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "dev"),
        "region": os.environ.get("AWS_DEFAULT_REGION", "ap-south-1"),
        "test_files": {},
        "summary": {}
    }
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    # Run each test file
    for test_file in test_files:
        print(f"Running {test_file}...")
        print("-" * 40)
        
        # Run pytest for this file
        result = pytest.main([
            test_file,
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file=results_{test_file.replace('.py', '.json')}"
        ])
        
        # Load and parse results
        results_file = f"results_{test_file.replace('.py', '.json')}"
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                file_results = json.load(f)
            
            # Extract test statistics
            summary = file_results.get('summary', {})
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            skipped = summary.get('skipped', 0)
            total = passed + failed + skipped
            
            test_results["test_files"][test_file] = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration": file_results.get('duration', 0),
                "exit_code": result
            }
            
            total_tests += total
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            
            print(f"  Total: {total}, Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
            
            # Clean up results file
            os.remove(results_file)
        else:
            print(f"  Warning: Results file {results_file} not found")
            test_results["test_files"][test_file] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0,
                "exit_code": result,
                "error": "Results file not found"
            }
        
        print()
    
    # Calculate overall summary
    test_results["summary"] = {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
        "overall_status": "PASS" if total_failed == 0 else "FAIL"
    }
    
    test_results["end_time"] = datetime.now(timezone.utc).isoformat()
    
    # Print summary
    print("=" * 80)
    print("DEPLOYMENT VALIDATION TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Skipped: {total_skipped}")
    print(f"Success Rate: {test_results['summary']['success_rate']:.1f}%")
    print(f"Overall Status: {test_results['summary']['overall_status']}")
    print()
    
    # Print detailed results
    print("DETAILED RESULTS:")
    print("-" * 40)
    for test_file, results in test_results["test_files"].items():
        status = "✓" if results["failed"] == 0 else "✗"
        print(f"{status} {test_file}: {results['passed']}/{results['total']} passed")
        if results["failed"] > 0:
            print(f"    {results['failed']} failed tests")
        if results["skipped"] > 0:
            print(f"    {results['skipped']} skipped tests")
    
    print()
    
    # Save detailed results to file
    results_filename = f"deployment_validation_results_{int(time.time())}.json"
    with open(results_filename, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"Detailed results saved to: {results_filename}")
    
    # Generate recommendations
    print()
    print("RECOMMENDATIONS:")
    print("-" * 40)
    
    if total_failed > 0:
        print("❌ Some tests failed. Review failed tests before proceeding with deployment.")
    
    if total_skipped > 10:
        print("⚠️  Many tests were skipped. Verify test environment configuration.")
    
    if test_results['summary']['success_rate'] < 80:
        print("⚠️  Success rate is below 80%. Consider fixing issues before deployment.")
    
    if total_failed == 0 and total_skipped < 5:
        print("✅ All tests passed! Deployment validation successful.")
    
    print()
    print("=" * 80)
    
    # Return appropriate exit code
    return 0 if total_failed == 0 else 1

def main():
    """
    Main entry point
    """
    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run tests
    exit_code = run_deployment_tests()
    
    # Exit with appropriate code
    sys.exit(exit_code)

if __name__ == "__main__":
    main()