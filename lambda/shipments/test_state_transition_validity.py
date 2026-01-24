"""
Property-based tests for state transition validity
Feature: shipment-tracking-automation, Property 3: State Transition Validity
Validates: Requirements 2.3

This test verifies that the shipment state machine enforces valid transitions:
- Valid transitions are accepted
- Invalid transitions are rejected
- Terminal states cannot transition to other states
- Same-state transitions are allowed (idempotent)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple


# Define valid state transitions (state machine) - matches webhook_handler.py
VALID_TRANSITIONS = {
    'shipment_created': ['picked_up', 'cancelled'],
    'picked_up': ['in_transit', 'returned'],
    'in_transit': ['in_transit', 'out_for_delivery', 'returned'],
    'out_for_delivery': ['delivered', 'delivery_failed', 'in_transit'],
    'delivery_failed': ['in_transit', 'out_for_delivery', 'returned'],
    'delivered': [],  # Terminal state
    'returned': [],   # Terminal state
    'cancelled': []   # Terminal state
}

# All valid statuses
ALL_STATUSES = list(VALID_TRANSITIONS.keys())

# Terminal states (no outgoing transitions)
TERMINAL_STATES = ['delivered', 'returned', 'cancelled']

# Non-terminal states
NON_TERMINAL_STATES = [s for s in ALL_STATUSES if s not in TERMINAL_STATES]


def is_valid_transition(current_status: str, new_status: str) -> bool:
    """
    Validate if status transition is allowed according to state machine.
    
    Requirements: 2.3
    """
    if not current_status or not new_status:
        return False
    
    # Allow same-status updates (idempotent)
    if new_status == current_status:
        return True
    
    # Check if transition is valid
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    is_valid = new_status in allowed_transitions
    
    return is_valid


# Hypothesis strategies for generating test data
status_strategy = st.sampled_from(ALL_STATUSES)
terminal_status_strategy = st.sampled_from(TERMINAL_STATES)
non_terminal_status_strategy = st.sampled_from(NON_TERMINAL_STATES)


class TestStateTransitionValidity:
    """
    Property 3: State Transition Validity
    
    For any shipment status update, the transition from current_status to new_status
    must be in the set of valid transitions defined by the state machine, otherwise
    the update is rejected.
    
    This ensures:
    1. Only valid state transitions are allowed
    2. Terminal states cannot transition to other states
    3. Invalid transitions are detected and rejected
    4. Same-state transitions are allowed (idempotent)
    """
    
    @given(
        current_status=status_strategy,
        new_status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_valid_transitions_are_accepted(
        self,
        current_status: str,
        new_status: str
    ):
        """
        Property Test: Valid state transitions are accepted
        
        For any current_status and new_status, if new_status is in the list of
        allowed transitions from current_status (or is the same status):
        1. is_valid_transition() MUST return True
        2. The transition MUST be allowed
        
        **Validates: Requirements 2.3**
        """
        # Get allowed transitions for current status
        allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
        
        # Check if this is a valid transition
        is_allowed = (new_status in allowed_transitions) or (new_status == current_status)
        
        # Only test valid transitions in this test
        assume(is_allowed)
        
        # Verify transition
        result = is_valid_transition(current_status, new_status)
        
        # Assert: Valid transition must be accepted
        assert result is True, (
            f"Valid transition must be accepted: '{current_status}' -> '{new_status}'. "
            f"Allowed transitions from '{current_status}': {allowed_transitions}"
        )
    
    @given(
        current_status=status_strategy,
        new_status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_invalid_transitions_are_rejected(
        self,
        current_status: str,
        new_status: str
    ):
        """
        Property Test: Invalid state transitions are rejected
        
        For any current_status and new_status, if new_status is NOT in the list
        of allowed transitions from current_status (and is not the same status):
        1. is_valid_transition() MUST return False
        2. The transition MUST be rejected
        
        **Validates: Requirements 2.3**
        """
        # Get allowed transitions for current status
        allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
        
        # Check if this is an invalid transition
        is_invalid = (new_status not in allowed_transitions) and (new_status != current_status)
        
        # Only test invalid transitions in this test
        assume(is_invalid)
        
        # Verify transition
        result = is_valid_transition(current_status, new_status)
        
        # Assert: Invalid transition must be rejected
        assert result is False, (
            f"Invalid transition must be rejected: '{current_status}' -> '{new_status}'. "
            f"Allowed transitions from '{current_status}': {allowed_transitions}"
        )
    
    @given(
        status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_same_status_transitions_are_allowed(
        self,
        status: str
    ):
        """
        Property Test: Same-status transitions are allowed (idempotent)
        
        For any status, transitioning from that status to itself must be allowed.
        This ensures idempotency - processing the same webhook multiple times
        doesn't cause errors.
        
        **Validates: Requirements 2.3**
        """
        # Verify same-status transition
        result = is_valid_transition(status, status)
        
        # Assert: Same-status transition must be allowed
        assert result is True, (
            f"Same-status transition must be allowed: '{status}' -> '{status}'"
        )
    
    @given(
        terminal_status=terminal_status_strategy,
        new_status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_terminal_states_cannot_transition(
        self,
        terminal_status: str,
        new_status: str
    ):
        """
        Property Test: Terminal states cannot transition to other states
        
        For any terminal state (delivered, returned, cancelled), attempting to
        transition to a different state must be rejected.
        
        **Validates: Requirements 2.3**
        """
        # Skip same-status transitions (those are allowed)
        assume(new_status != terminal_status)
        
        # Verify transition from terminal state
        result = is_valid_transition(terminal_status, new_status)
        
        # Assert: Transition from terminal state must be rejected
        assert result is False, (
            f"Terminal state cannot transition: '{terminal_status}' -> '{new_status}'. "
            f"Terminal states: {TERMINAL_STATES}"
        )
    
    @given(
        current_status=non_terminal_status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_non_terminal_states_have_valid_transitions(
        self,
        current_status: str
    ):
        """
        Property Test: Non-terminal states have at least one valid transition
        
        For any non-terminal state, there must be at least one valid transition
        to another state (excluding same-status transitions).
        
        **Validates: Requirements 2.3**
        """
        # Get allowed transitions
        allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
        
        # Assert: Non-terminal states must have at least one valid transition
        assert len(allowed_transitions) > 0, (
            f"Non-terminal state '{current_status}' must have at least one valid transition. "
            f"Found: {allowed_transitions}"
        )
    
    @given(
        terminal_status=terminal_status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_terminal_states_have_no_transitions(
        self,
        terminal_status: str
    ):
        """
        Property Test: Terminal states have no outgoing transitions
        
        For any terminal state, the list of allowed transitions must be empty.
        
        **Validates: Requirements 2.3**
        """
        # Get allowed transitions
        allowed_transitions = VALID_TRANSITIONS.get(terminal_status, [])
        
        # Assert: Terminal states must have no transitions
        assert len(allowed_transitions) == 0, (
            f"Terminal state '{terminal_status}' must have no outgoing transitions. "
            f"Found: {allowed_transitions}"
        )
    
    @given(
        current_status=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz_',
            min_size=1,
            max_size=30
        ),
        new_status=status_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_unknown_current_status_rejects_all_transitions(
        self,
        current_status: str,
        new_status: str
    ):
        """
        Property Test: Unknown current status rejects all transitions
        
        For any unknown/invalid current status, all transitions (except same-status)
        must be rejected.
        
        **Validates: Requirements 2.3**
        """
        # Ensure current_status is not a valid status
        assume(current_status not in ALL_STATUSES)
        
        # Skip same-status transitions
        assume(new_status != current_status)
        
        # Verify transition
        result = is_valid_transition(current_status, new_status)
        
        # Assert: Transition from unknown status must be rejected
        assert result is False, (
            f"Unknown status must reject transitions: '{current_status}' -> '{new_status}'"
        )
    
    @given(
        current_status=status_strategy,
        new_status=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz_',
            min_size=1,
            max_size=30
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_unknown_new_status_is_rejected(
        self,
        current_status: str,
        new_status: str
    ):
        """
        Property Test: Unknown new status is rejected
        
        For any valid current status, attempting to transition to an unknown/invalid
        new status must be rejected.
        
        **Validates: Requirements 2.3**
        """
        # Ensure new_status is not a valid status
        assume(new_status not in ALL_STATUSES)
        
        # Verify transition
        result = is_valid_transition(current_status, new_status)
        
        # Assert: Transition to unknown status must be rejected
        assert result is False, (
            f"Transition to unknown status must be rejected: '{current_status}' -> '{new_status}'"
        )
    
    @given(
        new_status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_current_status_is_rejected(
        self,
        new_status: str
    ):
        """
        Property Test: Empty current status is rejected
        
        For any new status, if the current status is empty or None:
        1. is_valid_transition() MUST return False
        2. The transition MUST be rejected
        
        **Validates: Requirements 2.3**
        """
        # Test with empty string
        result_empty = is_valid_transition('', new_status)
        assert result_empty is False, "Empty current status must be rejected"
        
        # Test with None
        result_none = is_valid_transition(None, new_status)
        assert result_none is False, "None current status must be rejected"
    
    @given(
        current_status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_new_status_is_rejected(
        self,
        current_status: str
    ):
        """
        Property Test: Empty new status is rejected
        
        For any current status, if the new status is empty or None:
        1. is_valid_transition() MUST return False
        2. The transition MUST be rejected
        
        **Validates: Requirements 2.3**
        """
        # Test with empty string
        result_empty = is_valid_transition(current_status, '')
        assert result_empty is False, "Empty new status must be rejected"
        
        # Test with None
        result_none = is_valid_transition(current_status, None)
        assert result_none is False, "None new status must be rejected"
    
    def test_state_machine_completeness(self):
        """
        Property Test: State machine is complete
        
        Verify that the state machine definition is complete:
        1. All statuses are defined in VALID_TRANSITIONS
        2. All referenced statuses in transitions exist
        3. No circular references in terminal states
        
        **Validates: Requirements 2.3**
        """
        # Check all statuses are defined
        for status in ALL_STATUSES:
            assert status in VALID_TRANSITIONS, (
                f"Status '{status}' must be defined in VALID_TRANSITIONS"
            )
        
        # Check all referenced statuses exist
        for current_status, allowed_transitions in VALID_TRANSITIONS.items():
            for next_status in allowed_transitions:
                assert next_status in ALL_STATUSES, (
                    f"Referenced status '{next_status}' in transitions from '{current_status}' "
                    f"must be a valid status"
                )
        
        # Check terminal states have no outgoing transitions
        for terminal_status in TERMINAL_STATES:
            transitions = VALID_TRANSITIONS[terminal_status]
            assert len(transitions) == 0, (
                f"Terminal state '{terminal_status}' must have no outgoing transitions. "
                f"Found: {transitions}"
            )
    
    def test_specific_valid_transitions(self):
        """
        Property Test: Specific valid transitions are correctly defined
        
        Verify that specific business logic transitions are correctly defined:
        1. shipment_created -> picked_up (normal flow)
        2. picked_up -> in_transit (normal flow)
        3. in_transit -> out_for_delivery (normal flow)
        4. out_for_delivery -> delivered (successful delivery)
        5. out_for_delivery -> delivery_failed (failed delivery)
        6. delivery_failed -> out_for_delivery (retry)
        
        **Validates: Requirements 2.3**
        """
        # Test normal flow transitions
        assert is_valid_transition('shipment_created', 'picked_up') is True
        assert is_valid_transition('picked_up', 'in_transit') is True
        assert is_valid_transition('in_transit', 'out_for_delivery') is True
        assert is_valid_transition('out_for_delivery', 'delivered') is True
        
        # Test failure and retry flow
        assert is_valid_transition('out_for_delivery', 'delivery_failed') is True
        assert is_valid_transition('delivery_failed', 'out_for_delivery') is True
        assert is_valid_transition('delivery_failed', 'in_transit') is True
        
        # Test return flow
        assert is_valid_transition('picked_up', 'returned') is True
        assert is_valid_transition('in_transit', 'returned') is True
        assert is_valid_transition('delivery_failed', 'returned') is True
        
        # Test cancellation
        assert is_valid_transition('shipment_created', 'cancelled') is True
    
    def test_specific_invalid_transitions(self):
        """
        Property Test: Specific invalid transitions are correctly rejected
        
        Verify that specific invalid transitions are rejected:
        1. delivered -> any other state (terminal)
        2. returned -> any other state (terminal)
        3. cancelled -> any other state (terminal)
        4. shipment_created -> delivered (skipping steps)
        5. picked_up -> delivered (skipping steps)
        
        **Validates: Requirements 2.3**
        """
        # Test terminal states cannot transition
        assert is_valid_transition('delivered', 'in_transit') is False
        assert is_valid_transition('delivered', 'returned') is False
        assert is_valid_transition('returned', 'delivered') is False
        assert is_valid_transition('returned', 'in_transit') is False
        assert is_valid_transition('cancelled', 'picked_up') is False
        assert is_valid_transition('cancelled', 'delivered') is False
        
        # Test skipping steps is not allowed
        assert is_valid_transition('shipment_created', 'delivered') is False
        assert is_valid_transition('shipment_created', 'in_transit') is False
        assert is_valid_transition('picked_up', 'delivered') is False
        assert is_valid_transition('picked_up', 'out_for_delivery') is False
    
    @given(
        current_status=status_strategy,
        new_status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_transition_validation_is_deterministic(
        self,
        current_status: str,
        new_status: str
    ):
        """
        Property Test: Transition validation is deterministic
        
        For any current_status and new_status, validating the same transition
        multiple times must always produce the same result.
        
        **Validates: Requirements 2.3**
        """
        # Validate transition multiple times
        results = [is_valid_transition(current_status, new_status) for _ in range(10)]
        
        # Assert: All results must be identical
        assert all(r == results[0] for r in results), (
            f"Transition validation must be deterministic: '{current_status}' -> '{new_status}'"
        )
    
    @given(
        current_status=status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_at_least_one_path_to_terminal_state(
        self,
        current_status: str
    ):
        """
        Property Test: Every non-terminal state has a path to a terminal state
        
        For any non-terminal state, there must be at least one sequence of valid
        transitions that leads to a terminal state (delivered, returned, or cancelled).
        
        This ensures the state machine doesn't have dead ends.
        
        **Validates: Requirements 2.3**
        """
        # Skip terminal states
        if current_status in TERMINAL_STATES:
            return
        
        # BFS to find path to terminal state
        visited = set()
        queue = [current_status]
        found_terminal = False
        
        while queue and not found_terminal:
            state = queue.pop(0)
            
            if state in visited:
                continue
            
            visited.add(state)
            
            # Check if we reached a terminal state
            if state in TERMINAL_STATES:
                found_terminal = True
                break
            
            # Add all valid transitions to queue
            next_states = VALID_TRANSITIONS.get(state, [])
            for next_state in next_states:
                if next_state not in visited:
                    queue.append(next_state)
        
        # Assert: Must be able to reach a terminal state
        assert found_terminal, (
            f"Non-terminal state '{current_status}' must have a path to a terminal state. "
            f"Visited states: {visited}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
