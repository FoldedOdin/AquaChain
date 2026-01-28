#!/usr/bin/env python3
"""
Comprehensive test runner for Shipment Tracking Automation
Runs all tests in the correct order and reports results
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

class TestRunner:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        
    def run_test_file(self, test_path: str, description: str) -> bool:
        """Run a single test file and capture results"""
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"File: {test_path}")
        print(f"{'='*80}\n")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            if result.returncode == 0:
                self.passed.append((description, test_path))
                print(f"\n✅ PASSED: {description}")
                return True
            else:
                self.failed.append((description, test_path, result.stdout))
                print(f"\n❌ FAILED: {description}")
                return False
                
        except subprocess.TimeoutExpired:
            self.failed.append((description, test_path, "Test timed out after 300 seconds"))
            print(f"\n⏱️ TIMEOUT: {description}")
            return False
        except Exception as e:
            self.failed.append((description, test_path, str(e)))
            print(f"\n💥 ERROR: {description} - {e}")
            return False
    
    def print_summary(self):
        """Print final test summary"""
        print(f"\n\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}\n")
        
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⏭️  Skipped: {len(self.skipped)}")
        
        if self.passed:
            print(f"\n{'='*80}")
            print("PASSED TESTS:")
            print(f"{'='*80}")
            for desc, path in self.passed:
                print(f"  ✅ {desc}")
        
        if self.failed:
            print(f"\n{'='*80}")
            print("FAILED TESTS:")
            print(f"{'='*80}")
            for desc, path, error in self.failed:
                print(f"  ❌ {desc}")
                print(f"     Path: {path}")
                if error and len(error) < 500:
                    print(f"     Error: {error[:500]}")
        
        if self.skipped:
            print(f"\n{'='*80}")
            print("SKIPPED TESTS:")
            print(f"{'='*80}")
            for desc, path in self.skipped:
                print(f"  ⏭️  {desc}")
        
        print(f"\n{'='*80}\n")
        
        return len(self.failed) == 0

def main():
    runner = TestRunner()
    
    # Define all test files in execution order
    tests = [
        # Infrastructure Tests
        ("tests/unit/infrastructure/test_table_creation_properties.py", 
         "Property Test: Table Creation Idempotency"),
        
        # Shipment Creation Tests
        ("lambda/shipments/test_shipment_creation_atomicity.py",
         "Property Test: Shipment Creation Atomicity"),
        
        # Webhook Handler Tests
        ("lambda/shipments/test_webhook_signature_verification.py",
         "Property Test: Webhook Signature Verification"),
        ("lambda/shipments/test_courier_payload_normalization.py",
         "Property Test: Courier Payload Normalization"),
        ("lambda/shipments/test_state_transition_validity.py",
         "Property Test: State Transition Validity"),
        ("lambda/shipments/test_timeline_monotonicity.py",
         "Property Test: Timeline Monotonicity"),
        ("lambda/shipments/test_webhook_idempotency.py",
         "Property Test: Webhook Idempotency"),
        ("lambda/shipments/test_delivery_confirmation_notification.py",
         "Property Test: Delivery Confirmation Triggers Notification"),
        ("lambda/shipments/test_webhook_handler_unit.py",
         "Unit Tests: Webhook Handler"),
        
        # Shipment Status Tests
        ("lambda/shipments/test_get_shipment_status_unit.py",
         "Unit Tests: Get Shipment Status"),
        
        # Delivery Failure Tests
        ("lambda/shipments/test_retry_counter_bounds.py",
         "Property Test: Retry Counter Bounds"),
        ("lambda/shipments/test_delivery_failure_retry_unit.py",
         "Unit Tests: Delivery Failure Retry Logic"),
        
        # Polling Fallback Tests
        ("lambda/shipments/test_polling_fallback_activation.py",
         "Property Test: Polling Fallback Activation"),
        ("lambda/shipments/test_polling_fallback_unit.py",
         "Unit Tests: Polling Fallback"),
        
        # Stale Shipment Tests
        ("lambda/shipments/test_stale_shipment_detection.py",
         "Property Test: Stale Shipment Detection"),
        ("lambda/shipments/test_stale_shipment_detector_unit.py",
         "Unit Tests: Stale Shipment Detector"),
        
        # Multi-Courier Tests
        ("lambda/shipments/test_multi_courier_support.py",
         "Unit Tests: Multi-Courier Support"),
        
        # Notification Tests
        ("lambda/shipments/test_notification_handler_unit.py",
         "Unit Tests: Notification Handler"),
        
        # Backward Compatibility Tests
        ("lambda/orders/test_backward_compatibility_preservation.py",
         "Property Test: Backward Compatibility Preservation"),
        ("lambda/orders/test_backward_compatibility.py",
         "Unit Tests: Backward Compatibility"),
        ("lambda/orders/test_existing_workflow.py",
         "Unit Tests: Existing Workflow"),
        ("lambda/shipments/test_graceful_degradation.py",
         "Unit Tests: Graceful Degradation"),
        
        # Audit Trail Tests
        ("lambda/shipments/test_webhook_event_storage.py",
         "Unit Tests: Webhook Event Storage"),
        ("lambda/shipments/test_admin_action_logging.py",
         "Unit Tests: Admin Action Logging"),
        ("lambda/shipments/test_data_retention_policy.py",
         "Unit Tests: Data Retention Policy"),
        ("lambda/shipments/test_audit_trail_completeness.py",
         "Property Test: Audit Trail Completeness"),
        
        # Integration Tests
        ("tests/integration/test_shipment_api_endpoints.py",
         "Integration Tests: Shipment API Endpoints"),
    ]
    
    print("="*80)
    print("SHIPMENT TRACKING AUTOMATION - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"\nTotal test files to run: {len(tests)}\n")
    
    # Run all tests
    for test_path, description in tests:
        if not Path(test_path).exists():
            print(f"\n⚠️  WARNING: Test file not found: {test_path}")
            runner.skipped.append((description, test_path))
            continue
        
        runner.run_test_file(test_path, description)
    
    # Print summary
    all_passed = runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
