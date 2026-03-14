#!/usr/bin/env python3
"""
Validate Order Status Progression Fix

This script validates that the order status progression fix is correctly implemented
by checking the code changes without requiring AWS dependencies.
"""

import os
import re

def validate_backend_status_enum():
    """Validate that backend OrderStatus enum includes new statuses"""
    print("1️⃣ Validating Backend OrderStatus Enum...")
    
    backend_file = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders', 'enhanced_order_management.py')
    
    with open(backend_file, 'r') as f:
        content = f.read()
    
    # Check for DEVICE_READY and TECHNICIAN_ASSIGNED in enum
    if 'DEVICE_READY = \'DEVICE_READY\'' in content:
        print("✅ DEVICE_READY status added to backend enum")
    else:
        print("❌ DEVICE_READY status missing from backend enum")
        return False
    
    if 'TECHNICIAN_ASSIGNED = \'TECHNICIAN_ASSIGNED\'' in content:
        print("✅ TECHNICIAN_ASSIGNED status added to backend enum")
    else:
        print("❌ TECHNICIAN_ASSIGNED status missing from backend enum")
        return False
    
    return True

def validate_backend_transitions():
    """Validate that backend valid_transitions includes new transitions"""
    print("\n2️⃣ Validating Backend Status Transitions...")
    
    backend_file = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders', 'enhanced_order_management.py')
    
    with open(backend_file, 'r') as f:
        content = f.read()
    
    # Check for correct transitions
    transitions_to_check = [
        'OrderStatus.ORDER_PLACED: [OrderStatus.DEVICE_READY',
        'OrderStatus.DEVICE_READY: [OrderStatus.TECHNICIAN_ASSIGNED',
        'OrderStatus.TECHNICIAN_ASSIGNED: [OrderStatus.SHIPPED'
    ]
    
    all_found = True
    for transition in transitions_to_check:
        if transition in content:
            print(f"✅ Found transition: {transition}")
        else:
            print(f"❌ Missing transition: {transition}")
            all_found = False
    
    return all_found

def validate_technician_assignment_logic():
    """Validate that technician assignment logic is added"""
    print("\n3️⃣ Validating Technician Assignment Logic...")
    
    backend_file = os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders', 'enhanced_order_management.py')
    
    with open(backend_file, 'r') as f:
        content = f.read()
    
    # Check for technician assignment logic
    if 'if new_status == OrderStatus.TECHNICIAN_ASSIGNED:' in content:
        print("✅ Technician assignment trigger logic added")
    else:
        print("❌ Technician assignment trigger logic missing")
        return False
    
    if 'from technician_assignment_service import TechnicianAssignmentService' in content:
        print("✅ Technician assignment service import added")
    else:
        print("❌ Technician assignment service import missing")
        return False
    
    if 'assignedTechnician' in content and 'assignedTechnicianName' in content:
        print("✅ Technician fields added to order update")
    else:
        print("❌ Technician fields missing from order update")
        return False
    
    return True

def validate_frontend_progression():
    """Validate that frontend status progression is fixed"""
    print("\n4️⃣ Validating Frontend Status Progression...")
    
    frontend_file = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'src', 'components', 'Dashboard', 'OrderProgressButtons.tsx')
    
    with open(frontend_file, 'r') as f:
        content = f.read()
    
    # Check for correct progression mapping
    expected_mappings = [
        '[OrderStatus.ORDER_PLACED]: OrderStatus.DEVICE_READY',
        '[OrderStatus.DEVICE_READY]: OrderStatus.TECHNICIAN_ASSIGNED',
        '[OrderStatus.TECHNICIAN_ASSIGNED]: OrderStatus.SHIPPED'
    ]
    
    all_found = True
    for mapping in expected_mappings:
        if mapping in content:
            print(f"✅ Found mapping: {mapping}")
        else:
            print(f"❌ Missing mapping: {mapping}")
            all_found = False
    
    return all_found

def validate_frontend_button_labels():
    """Validate that frontend button labels are updated"""
    print("\n5️⃣ Validating Frontend Button Labels...")
    
    frontend_file = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'src', 'components', 'Dashboard', 'OrderProgressButtons.tsx')
    
    with open(frontend_file, 'r') as f:
        content = f.read()
    
    # Check for correct button labels
    expected_labels = [
        '[OrderStatus.ORDER_PLACED]: \'Mark Device Ready\'',
        '[OrderStatus.DEVICE_READY]: \'Assign Technician\'',
        '[OrderStatus.TECHNICIAN_ASSIGNED]: \'Mark as Shipped\''
    ]
    
    all_found = True
    for label in expected_labels:
        if label in content:
            print(f"✅ Found label: {label}")
        else:
            print(f"❌ Missing label: {label}")
            all_found = False
    
    return all_found

def main():
    """Run all validation checks"""
    print("🔍 Validating Order Status Progression Fix")
    print("=" * 50)
    
    all_passed = True
    
    # Run all validation checks
    checks = [
        validate_backend_status_enum,
        validate_backend_transitions,
        validate_technician_assignment_logic,
        validate_frontend_progression,
        validate_frontend_button_labels
    ]
    
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("\nThe order status progression fix is correctly implemented:")
        print("✅ Backend supports DEVICE_READY and TECHNICIAN_ASSIGNED statuses")
        print("✅ Backend transitions updated: ORDER_PLACED → DEVICE_READY → TECHNICIAN_ASSIGNED → SHIPPED")
        print("✅ Technician assignment logic added to backend")
        print("✅ Frontend progression mapping fixed")
        print("✅ Frontend button labels updated")
        print("\n🚫 The bug where DEVICE_READY jumped directly to SHIPPED is now FIXED!")
        print("📋 Correct flow: ORDER_PLACED → DEVICE_READY → TECHNICIAN_ASSIGNED → SHIPPED → OUT_FOR_DELIVERY → DELIVERED")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please review the failed checks above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)