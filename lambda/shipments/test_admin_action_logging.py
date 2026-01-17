"""
Test admin action logging for audit trail compliance

This test verifies:
1. Admin user_id is logged for shipment creation
2. Manual interventions (address change, cancellation) are logged
3. Timestamp and action type are included

Requirements: 15.3
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from audit_trail import create_admin_action_log
from datetime import datetime


def test_shipment_creation_logging():
    """Test admin action logging for shipment creation"""
    print("\n" + "=" * 80)
    print("TEST: Shipment Creation Logging")
    print("=" * 80)
    
    # Create admin action log for shipment creation
    admin_action = create_admin_action_log(
        action_type='SHIPMENT_CREATED',
        user_id='admin-user-123',
        details={
            'courier_name': 'Delhivery',
            'tracking_number': 'DELHUB123456',
            'destination': '123 Main St, Bangalore'
        }
    )
    
    # Verify required fields
    assert 'action_type' in admin_action, "Missing action_type"
    assert 'user_id' in admin_action, "Missing user_id"
    assert 'timestamp' in admin_action, "Missing timestamp"
    
    assert admin_action['action_type'] == 'SHIPMENT_CREATED'
    assert admin_action['user_id'] == 'admin-user-123'
    assert 'details' in admin_action
    assert admin_action['details']['courier_name'] == 'Delhivery'
    
    print(f"✓ Action Type: {admin_action['action_type']}")
    print(f"✓ User ID: {admin_action['user_id']}")
    print(f"✓ Timestamp: {admin_action['timestamp']}")
    print(f"✓ Details: {admin_action['details']}")
    
    print("\n✓ Shipment creation logging test passed")


def test_address_change_logging():
    """Test admin action logging for address changes"""
    print("\n" + "=" * 80)
    print("TEST: Address Change Logging")
    print("=" * 80)
    
    # Create admin action log for address change
    admin_action = create_admin_action_log(
        action_type='ADDRESS_CHANGED',
        user_id='admin-user-456',
        details={
            'old_address': '123 Old St, Mumbai',
            'new_address': '456 New St, Bangalore',
            'reason': 'Customer requested address correction'
        }
    )
    
    # Verify required fields
    assert admin_action['action_type'] == 'ADDRESS_CHANGED'
    assert admin_action['user_id'] == 'admin-user-456'
    assert 'timestamp' in admin_action
    assert 'details' in admin_action
    
    # Verify details
    details = admin_action['details']
    assert 'old_address' in details
    assert 'new_address' in details
    assert 'reason' in details
    
    print(f"✓ Action Type: {admin_action['action_type']}")
    print(f"✓ User ID: {admin_action['user_id']}")
    print(f"✓ Timestamp: {admin_action['timestamp']}")
    print(f"✓ Old Address: {details['old_address']}")
    print(f"✓ New Address: {details['new_address']}")
    print(f"✓ Reason: {details['reason']}")
    
    print("\n✓ Address change logging test passed")


def test_cancellation_logging():
    """Test admin action logging for shipment cancellation"""
    print("\n" + "=" * 80)
    print("TEST: Cancellation Logging")
    print("=" * 80)
    
    # Create admin action log for cancellation
    admin_action = create_admin_action_log(
        action_type='CANCELLED',
        user_id='admin-user-789',
        details={
            'reason': 'Customer requested cancellation',
            'refund_initiated': True,
            'cancelled_at': datetime.utcnow().isoformat() + 'Z'
        }
    )
    
    # Verify required fields
    assert admin_action['action_type'] == 'CANCELLED'
    assert admin_action['user_id'] == 'admin-user-789'
    assert 'timestamp' in admin_action
    assert 'details' in admin_action
    
    # Verify details
    details = admin_action['details']
    assert 'reason' in details
    assert details['refund_initiated'] == True
    
    print(f"✓ Action Type: {admin_action['action_type']}")
    print(f"✓ User ID: {admin_action['user_id']}")
    print(f"✓ Timestamp: {admin_action['timestamp']}")
    print(f"✓ Reason: {details['reason']}")
    print(f"✓ Refund Initiated: {details['refund_initiated']}")
    
    print("\n✓ Cancellation logging test passed")


def test_status_override_logging():
    """Test admin action logging for manual status override"""
    print("\n" + "=" * 80)
    print("TEST: Status Override Logging")
    print("=" * 80)
    
    # Create admin action log for status override
    admin_action = create_admin_action_log(
        action_type='STATUS_OVERRIDE',
        user_id='admin-user-999',
        details={
            'old_status': 'in_transit',
            'new_status': 'delivered',
            'reason': 'Manual delivery confirmation after courier system failure'
        }
    )
    
    # Verify required fields
    assert admin_action['action_type'] == 'STATUS_OVERRIDE'
    assert admin_action['user_id'] == 'admin-user-999'
    assert 'timestamp' in admin_action
    assert 'details' in admin_action
    
    # Verify details
    details = admin_action['details']
    assert 'old_status' in details
    assert 'new_status' in details
    assert 'reason' in details
    
    print(f"✓ Action Type: {admin_action['action_type']}")
    print(f"✓ User ID: {admin_action['user_id']}")
    print(f"✓ Timestamp: {admin_action['timestamp']}")
    print(f"✓ Old Status: {details['old_status']}")
    print(f"✓ New Status: {details['new_status']}")
    print(f"✓ Reason: {details['reason']}")
    
    print("\n✓ Status override logging test passed")


def test_multiple_admin_actions():
    """Test logging multiple admin actions for a shipment"""
    print("\n" + "=" * 80)
    print("TEST: Multiple Admin Actions")
    print("=" * 80)
    
    # Simulate multiple admin actions on a shipment
    admin_actions = []
    
    # Action 1: Shipment created
    admin_actions.append(create_admin_action_log(
        action_type='SHIPMENT_CREATED',
        user_id='admin-001',
        details={'courier': 'Delhivery'}
    ))
    
    # Action 2: Address changed
    admin_actions.append(create_admin_action_log(
        action_type='ADDRESS_CHANGED',
        user_id='admin-002',
        details={'new_address': '789 Updated St'}
    ))
    
    # Action 3: Status overridden
    admin_actions.append(create_admin_action_log(
        action_type='STATUS_OVERRIDE',
        user_id='admin-001',
        details={'new_status': 'delivered'}
    ))
    
    # Verify all actions are logged
    assert len(admin_actions) == 3, "Should have 3 admin actions"
    print(f"✓ Logged {len(admin_actions)} admin actions")
    
    # Verify each action has required fields
    for i, action in enumerate(admin_actions, 1):
        assert 'action_type' in action
        assert 'user_id' in action
        assert 'timestamp' in action
        print(f"✓ Action {i}: {action['action_type']} by {action['user_id']}")
    
    # Verify chronological order
    for i in range(len(admin_actions) - 1):
        assert admin_actions[i]['timestamp'] <= admin_actions[i+1]['timestamp']
    print("✓ Actions are in chronological order")
    
    print("\n✓ Multiple admin actions test passed")


def test_admin_action_audit_trail():
    """Test complete admin action audit trail"""
    print("\n" + "=" * 80)
    print("TEST: Complete Admin Action Audit Trail")
    print("=" * 80)
    
    # Simulate complete lifecycle with admin interventions
    audit_trail = []
    
    # Initial creation
    audit_trail.append(create_admin_action_log(
        action_type='SHIPMENT_CREATED',
        user_id='admin-alice',
        details={
            'order_id': 'ord_12345',
            'courier': 'Delhivery',
            'tracking_number': 'DELHUB999'
        }
    ))
    
    # Address correction
    audit_trail.append(create_admin_action_log(
        action_type='ADDRESS_CHANGED',
        user_id='admin-bob',
        details={
            'old_address': '123 Wrong St',
            'new_address': '456 Correct St',
            'reason': 'Customer called to update address'
        }
    ))
    
    # Delivery attempt failed - manual intervention
    audit_trail.append(create_admin_action_log(
        action_type='STATUS_OVERRIDE',
        user_id='admin-alice',
        details={
            'old_status': 'delivery_failed',
            'new_status': 'out_for_delivery',
            'reason': 'Rescheduled delivery after customer confirmation'
        }
    ))
    
    # Final delivery confirmation
    audit_trail.append(create_admin_action_log(
        action_type='STATUS_OVERRIDE',
        user_id='admin-bob',
        details={
            'old_status': 'out_for_delivery',
            'new_status': 'delivered',
            'reason': 'Manual confirmation after courier system delay'
        }
    ))
    
    # Verify complete audit trail
    assert len(audit_trail) == 4, "Should have 4 admin actions"
    print(f"✓ Complete audit trail with {len(audit_trail)} actions")
    
    # Verify all actions have required fields
    for action in audit_trail:
        assert 'action_type' in action
        assert 'user_id' in action
        assert 'timestamp' in action
        assert 'details' in action
    print("✓ All actions have required fields")
    
    # Print audit trail
    print("\nComplete Admin Action Audit Trail:")
    for i, action in enumerate(audit_trail, 1):
        print(f"  {i}. {action['timestamp']}")
        print(f"     Action: {action['action_type']}")
        print(f"     User: {action['user_id']}")
        if 'reason' in action.get('details', {}):
            print(f"     Reason: {action['details']['reason']}")
    
    print("\n✓ Complete admin action audit trail test passed")


def main():
    """Run all admin action logging tests"""
    print("=" * 80)
    print("ADMIN ACTION LOGGING VERIFICATION")
    print("=" * 80)
    print("Requirements: 15.3")
    
    try:
        test_shipment_creation_logging()
        test_address_change_logging()
        test_cancellation_logging()
        test_status_override_logging()
        test_multiple_admin_actions()
        test_admin_action_audit_trail()
        
        print("\n" + "=" * 80)
        print("✓ ALL ADMIN ACTION LOGGING TESTS PASSED")
        print("=" * 80)
        print("\nAdmin action logging implementation verified:")
        print("  ✓ Admin user_id logged for shipment creation")
        print("  ✓ Manual interventions (address change, cancellation) logged")
        print("  ✓ Timestamp and action type included")
        print("  ✓ Detailed information preserved in 'details' field")
        print("  ✓ Complete audit trail maintained")
        print("\nRequirement validated: 15.3")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
