#!/usr/bin/env python3
"""
Simple test runner for lightweight tests that won't crash Kiro

This script runs the simplified test files to validate core functionality
without the complexity of property-based tests.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return results"""
    try:
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print(f"{'='*60}")
        
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            test_file, 
            '-v',
            '--tb=short',
            '--no-header'
        ], capture_output=True, text=True, timeout=30)
        
        print(f"Exit Code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {test_file} took too long to run")
        return False
    except Exception as e:
        print(f"ERROR running {test_file}: {e}")
        return False

def main():
    """Run all simplified test files"""
    test_dir = Path("tests/unit/lambda")
    
    # List of simplified test files
    simple_tests = [
        "test_basic_validation.py"
    ]
    
    results = {}
    total_tests = 0
    passed_tests = 0
    
    print("AquaChain Dashboard Overhaul - Simplified Test Runner")
    print("=" * 60)
    print("Running lightweight tests to avoid system crashes...")
    
    for test_file in simple_tests:
        test_path = test_dir / test_file
        
        if not test_path.exists():
            print(f"SKIP: {test_file} (file not found)")
            continue
            
        total_tests += 1
        success = run_test_file(str(test_path))
        results[test_file] = success
        
        if success:
            passed_tests += 1
            print(f"✅ PASSED: {test_file}")
        else:
            print(f"❌ FAILED: {test_file}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
    
    # Detailed results
    print(f"\nDetailed Results:")
    for test_file, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_file}")
    
    # Exit with appropriate code
    if passed_tests == total_tests and total_tests > 0:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed or no tests were run")
        return 1

if __name__ == "__main__":
    sys.exit(main())