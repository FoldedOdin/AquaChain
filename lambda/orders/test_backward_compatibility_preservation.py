"""
Property-based tests for backward compatibility preservation
Feature: shipment-tracking-automation, Property 8: Backward Compatibility Preservation
Validates: Requirements 8.2, 8.3

This test verifies that existing API endpoints maintain backward compatibility:
- Response format remains unchanged
- Status values remain unchanged (always "shipped" externally)
- Internal shipment fields are not exposed
- Existing workflow continues to function
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List, Any, Optional
import json
from unittest.mock import Mock, patch, MagicMock

# Import the handler and helper functions
from orders.get_orders import (
    handler,
    ensure_backward_compatibility,
    extract_user_id,
    extract_user_role
)


# Hypothesis strategies for generating test data
order_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=10,
    max_size=30
)

user_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=10,
    max_size=30
)

shipment_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=10,
    max_size=30
)

tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=8,
    max_size=20
)

# Valid order statuses
order_status_strategy = st.sampled_from([
    'pending',
    'approved',
    'shipped',
    'installed',
    'completed',
    'cancelled'
])

# Internal shipment statuses (should NOT be exposed)
internal_shipment_status_strategy = st.sampled_from([
    'shipment_created',
    'picked_up',
    'in_transit',
    'out_for_delivery',
    'delivered',
    'delivery_failed',
    'returned',
    'cancelled'
])


def generate_order_with_shipment_fields(
    order_id: str,
    user_id: str,
    status: str,
    shipment_id: Optional[str] = None,
    tracking_number: Optional[str] = None,
    internal_status: Optional[str] = None
) -> Dict[str, Any]:
    """Generate an order with optional shipment fields"""
    order = {
        'orderId': order_id,
        'userId': user_id,
        'status': status,
        'deviceSKU': 'AQ-001',
        'address': '123 Main St',
        'createdAt': '2025-01-01T00:00:00Z'
    }
    
    # Add shipment fields if provided
    if shipment_id:
        order['shipment_id'] = shipment_id
    if tracking_number:
        order['tracking_number'] = tracking_number
    if internal_status:
        order['internal_status'] = internal_status
    
    return order


class TestBackwardCompatibilityPreservation:
    """
    Property 8: Backward Compatibility Preservation
    
    For any existing API endpoint that queries order status, the response format
    and status values must remain unchanged when the Shipments table is introduced.
    
    This ensures:
    1. API responses maintain the same format
    2. Status values remain unchanged (always "shipped" externally)
    3. Internal shipment fields (shipment_id, tracking_number, internal_status) are not exposed
    4. Existing workflow continues to function
    """
    
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        status=order_status_strategy,
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_shipment_fields_are_never_exposed(
        self,
        order_id: str,
        user_id: str,
        status: str,
        shipment_id: str,
        tracking_number: str
    ):
        """
        Property Test: Shipment fields are never exposed in API responses
        
        For any order with shipment_id and tracking_number fields:
        1. ensure_backward_compatibility() MUST remove these fields
        2. The returned order MUST NOT contain 'shipment_id'
        3. The returned order MUST NOT contain 'tracking_number'
        4. The returned order MUST NOT contain 'internal_status'
        
        **Validates: Requirements 8.2**
        """
        # Generate order with shipment fields
        order = generate_order_with_shipment_fields(
            order_id=order_id,
            user_id=user_id,
            status=status,
            shipment_id=shipment_id,
            tracking_number=tracking_number
        )
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility([order])
        
        # Assert: Shipment fields must be removed
        assert len(result) == 1, "Must return exactly one order"
        cleaned_order = result[0]
        
        assert 'shipment_id' not in cleaned_order, (
            f"shipment_id must not be exposed in API response. "
            f"Order: {cleaned_order}"
        )
        assert 'tracking_number' not in cleaned_order, (
            f"tracking_number must not be exposed in API response. "
            f"Order: {cleaned_order}"
        )
        assert 'internal_status' not in cleaned_order, (
            f"internal_status must not be exposed in API response. "
            f"Order: {cleaned_order}"
        )
    
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        status=order_status_strategy,
        shipment_id=shipment_id_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_external_status_remains_unchanged(
        self,
        order_id: str,
        user_id: str,
        status: str,
        shipment_id: str
    ):
        """
        Property Test: External status remains unchanged
        
        For any order, regardless of whether it has shipment fields:
        1. The 'status' field MUST remain unchanged
        2. The status value MUST be preserved exactly
        3. Internal shipment status MUST NOT replace external status
        
        **Validates: Requirements 8.2**
        """
        # Generate order with shipment fields
        order = generate_order_with_shipment_fields(
            order_id=order_id,
            user_id=user_id,
            status=status,
            shipment_id=shipment_id
        )
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility([order])
        
        # Assert: Status must remain unchanged
        assert len(result) == 1
        cleaned_order = result[0]
        
        assert 'status' in cleaned_order, "Status field must be present"
        assert cleaned_order['status'] == status, (
            f"Status must remain unchanged. Expected: '{status}', Got: '{cleaned_order['status']}'"
        )
    
    @given(
        orders=st.lists(
            st.fixed_dictionaries({
                'orderId': order_id_strategy,
                'userId': user_id_strategy,
                'status': order_status_strategy,
                'shipment_id': st.one_of(st.none(), shipment_id_strategy),
                'tracking_number': st.one_of(st.none(), tracking_number_strategy)
            }),
            min_size=0,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_response_format_preserved_for_multiple_orders(
        self,
        orders: List[Dict[str, Any]]
    ):
        """
        Property Test: Response format preserved for multiple orders
        
        For any list of orders (including empty list):
        1. ensure_backward_compatibility() MUST return a list
        2. The list length MUST be preserved
        3. All shipment fields MUST be removed from all orders
        4. All other fields MUST be preserved
        
        **Validates: Requirements 8.2**
        """
        # Apply backward compatibility filter
        result = ensure_backward_compatibility(orders)
        
        # Assert: List structure preserved
        assert isinstance(result, list), "Result must be a list"
        assert len(result) == len(orders), (
            f"List length must be preserved. Expected: {len(orders)}, Got: {len(result)}"
        )
        
        # Assert: All shipment fields removed
        for i, cleaned_order in enumerate(result):
            assert 'shipment_id' not in cleaned_order, (
                f"Order {i}: shipment_id must not be exposed"
            )
            assert 'tracking_number' not in cleaned_order, (
                f"Order {i}: tracking_number must not be exposed"
            )
            assert 'internal_status' not in cleaned_order, (
                f"Order {i}: internal_status must not be exposed"
            )
            
            # Assert: Core fields preserved
            if i < len(orders):
                original = orders[i]
                assert cleaned_order['orderId'] == original['orderId'], (
                    f"Order {i}: orderId must be preserved"
                )
                assert cleaned_order['userId'] == original['userId'], (
                    f"Order {i}: userId must be preserved"
                )
                assert cleaned_order['status'] == original['status'], (
                    f"Order {i}: status must be preserved"
                )
    
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        status=order_status_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_orders_without_shipment_fields_unchanged(
        self,
        order_id: str,
        user_id: str,
        status: str
    ):
        """
        Property Test: Orders without shipment fields remain unchanged
        
        For any order without shipment fields:
        1. ensure_backward_compatibility() MUST return the order unchanged
        2. All fields MUST be preserved
        3. No fields MUST be added or removed
        
        **Validates: Requirements 8.3**
        """
        # Generate order without shipment fields
        order = generate_order_with_shipment_fields(
            order_id=order_id,
            user_id=user_id,
            status=status
        )
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility([order])
        
        # Assert: Order unchanged
        assert len(result) == 1
        cleaned_order = result[0]
        
        # All original fields must be present
        for key, value in order.items():
            assert key in cleaned_order, f"Field '{key}' must be preserved"
            assert cleaned_order[key] == value, (
                f"Field '{key}' value must be unchanged. Expected: {value}, Got: {cleaned_order[key]}"
            )
        
        # No extra fields added
        for key in cleaned_order.keys():
            assert key in order, f"No extra field '{key}' should be added"
    
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_shipped_status_preserved_with_shipment_fields(
        self,
        order_id: str,
        user_id: str,
        shipment_id: str,
        tracking_number: str
    ):
        """
        Property Test: "shipped" status preserved even with shipment fields
        
        For any order with status="shipped" and shipment fields:
        1. The status MUST remain "shipped" (not replaced with internal status)
        2. Shipment fields MUST be removed
        3. The order MUST still be identifiable as shipped
        
        **Validates: Requirements 8.2**
        """
        # Generate shipped order with shipment fields
        order = generate_order_with_shipment_fields(
            order_id=order_id,
            user_id=user_id,
            status='shipped',
            shipment_id=shipment_id,
            tracking_number=tracking_number
        )
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility([order])
        
        # Assert: Status remains "shipped"
        assert len(result) == 1
        cleaned_order = result[0]
        
        assert cleaned_order['status'] == 'shipped', (
            f"Status must remain 'shipped'. Got: '{cleaned_order['status']}'"
        )
        assert 'shipment_id' not in cleaned_order
        assert 'tracking_number' not in cleaned_order
    
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        internal_status=internal_shipment_status_strategy,
        shipment_id=shipment_id_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_internal_status_never_exposed(
        self,
        order_id: str,
        user_id: str,
        internal_status: str,
        shipment_id: str
    ):
        """
        Property Test: Internal shipment status never exposed
        
        For any order with internal_status field:
        1. ensure_backward_compatibility() MUST remove internal_status
        2. The external status MUST be preserved
        3. Internal shipment states MUST NOT leak to API responses
        
        **Validates: Requirements 8.2**
        """
        # Generate order with internal status
        order = generate_order_with_shipment_fields(
            order_id=order_id,
            user_id=user_id,
            status='shipped',  # External status
            shipment_id=shipment_id,
            internal_status=internal_status  # Internal status (should be removed)
        )
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility([order])
        
        # Assert: Internal status removed
        assert len(result) == 1
        cleaned_order = result[0]
        
        assert 'internal_status' not in cleaned_order, (
            f"internal_status must not be exposed. Order: {cleaned_order}"
        )
        assert cleaned_order['status'] == 'shipped', (
            f"External status must be preserved. Got: '{cleaned_order['status']}'"
        )
    
    @given(
        orders=st.lists(
            st.fixed_dictionaries({
                'orderId': order_id_strategy,
                'userId': user_id_strategy,
                'status': order_status_strategy,
                'shipment_id': shipment_id_strategy,
                'tracking_number': tracking_number_strategy,
                'deviceSKU': st.text(min_size=5, max_size=10),
                'address': st.text(min_size=10, max_size=50)
            }),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_backward_compatibility_is_idempotent(
        self,
        orders: List[Dict[str, Any]]
    ):
        """
        Property Test: Backward compatibility filter is idempotent
        
        For any list of orders, applying ensure_backward_compatibility() multiple
        times must produce the same result.
        
        **Validates: Requirements 8.2**
        """
        # Apply filter once
        result1 = ensure_backward_compatibility(orders)
        
        # Apply filter again on the result
        result2 = ensure_backward_compatibility(result1)
        
        # Apply filter a third time
        result3 = ensure_backward_compatibility(result2)
        
        # Assert: All results must be identical
        assert result1 == result2, "Filter must be idempotent (1st vs 2nd application)"
        assert result2 == result3, "Filter must be idempotent (2nd vs 3rd application)"
        
        # Assert: No shipment fields in any result
        for result in [result1, result2, result3]:
            for order in result:
                assert 'shipment_id' not in order
                assert 'tracking_number' not in order
                assert 'internal_status' not in order
    
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        status=order_status_strategy,
        shipment_id=shipment_id_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_essential_order_fields_preserved(
        self,
        order_id: str,
        user_id: str,
        status: str,
        shipment_id: str
    ):
        """
        Property Test: Essential order fields are always preserved
        
        For any order, the following essential fields must be preserved:
        - orderId
        - userId
        - status
        - deviceSKU (if present)
        - address (if present)
        - createdAt (if present)
        
        **Validates: Requirements 8.2, 8.3**
        """
        # Generate order with essential fields
        order = {
            'orderId': order_id,
            'userId': user_id,
            'status': status,
            'shipment_id': shipment_id,
            'deviceSKU': 'AQ-001',
            'address': '123 Main St',
            'createdAt': '2025-01-01T00:00:00Z'
        }
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility([order])
        
        # Assert: Essential fields preserved
        assert len(result) == 1
        cleaned_order = result[0]
        
        assert cleaned_order['orderId'] == order_id
        assert cleaned_order['userId'] == user_id
        assert cleaned_order['status'] == status
        assert cleaned_order['deviceSKU'] == 'AQ-001'
        assert cleaned_order['address'] == '123 Main St'
        assert cleaned_order['createdAt'] == '2025-01-01T00:00:00Z'
        
        # Assert: Shipment field removed
        assert 'shipment_id' not in cleaned_order
    
    @given(
        orders=st.lists(
            st.fixed_dictionaries({
                'orderId': order_id_strategy,
                'userId': user_id_strategy,
                'status': order_status_strategy
            }),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_and_small_lists_handled_correctly(
        self,
        orders: List[Dict[str, Any]]
    ):
        """
        Property Test: Empty and small lists handled correctly
        
        For any list of orders (including empty):
        1. ensure_backward_compatibility() MUST handle it without errors
        2. The result MUST be a list of the same length
        3. Empty list MUST return empty list
        
        **Validates: Requirements 8.3**
        """
        # Apply backward compatibility filter
        result = ensure_backward_compatibility(orders)
        
        # Assert: Correct handling
        assert isinstance(result, list)
        assert len(result) == len(orders)
        
        if len(orders) == 0:
            assert len(result) == 0, "Empty list must return empty list"
    
    @patch('orders.get_orders.dynamodb')
    @given(
        order_id=order_id_strategy,
        user_id=user_id_strategy,
        shipment_id=shipment_id_strategy,
        tracking_number=tracking_number_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_api_handler_never_exposes_shipment_fields(
        self,
        mock_dynamodb,
        order_id: str,
        user_id: str,
        shipment_id: str,
        tracking_number: str
    ):
        """
        Property Test: API handler never exposes shipment fields
        
        For any order returned by the API handler:
        1. The response MUST NOT contain shipment_id
        2. The response MUST NOT contain tracking_number
        3. The response MUST NOT contain internal_status
        4. The status MUST be the external status
        
        **Validates: Requirements 8.2**
        """
        # Setup mock
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock DynamoDB response with shipment fields
        mock_table.query.return_value = {
            'Items': [{
                'orderId': order_id,
                'userId': user_id,
                'status': 'shipped',
                'shipment_id': shipment_id,
                'tracking_number': tracking_number,
                'deviceSKU': 'AQ-001',
                'address': '123 Main St',
                'createdAt': '2025-01-01T00:00:00Z'
            }]
        }
        
        # Create event
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': user_id,
                        'custom:role': 'consumer'
                    }
                }
            },
            'queryStringParameters': None
        }
        
        context = Mock()
        context.request_id = 'test-request-123'
        
        # Call handler
        response = handler(event, context)
        
        # Assert: Response is valid
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert len(body['orders']) == 1
        
        # Assert: Shipment fields not exposed
        order = body['orders'][0]
        assert 'shipment_id' not in order, (
            f"API response must not expose shipment_id. Order: {order}"
        )
        assert 'tracking_number' not in order, (
            f"API response must not expose tracking_number. Order: {order}"
        )
        assert 'internal_status' not in order, (
            f"API response must not expose internal_status. Order: {order}"
        )
        
        # Assert: Status is external status
        assert order['status'] == 'shipped'
    
    def test_backward_compatibility_with_real_world_orders(self):
        """
        Property Test: Backward compatibility with real-world order structures
        
        Test with realistic order structures that might exist in production.
        
        **Validates: Requirements 8.2, 8.3**
        """
        # Real-world order examples
        orders = [
            # Order with shipment fields
            {
                'orderId': 'ord_1735392000000',
                'userId': 'user_123',
                'status': 'shipped',
                'shipment_id': 'ship_1735478400000',
                'tracking_number': 'DELHUB123456789',
                'deviceSKU': 'AQ-001',
                'address': '123 Main St, Bangalore',
                'createdAt': '2025-01-01T00:00:00Z',
                'shippedAt': '2025-01-02T00:00:00Z'
            },
            # Order without shipment fields
            {
                'orderId': 'ord_1735392000001',
                'userId': 'user_456',
                'status': 'pending',
                'deviceSKU': 'AQ-002',
                'address': '456 Oak Ave, Mumbai',
                'createdAt': '2025-01-03T00:00:00Z'
            },
            # Completed order
            {
                'orderId': 'ord_1735392000002',
                'userId': 'user_789',
                'status': 'completed',
                'deviceSKU': 'AQ-003',
                'address': '789 Pine Rd, Delhi',
                'createdAt': '2024-12-01T00:00:00Z',
                'completedAt': '2024-12-15T00:00:00Z'
            }
        ]
        
        # Apply backward compatibility filter
        result = ensure_backward_compatibility(orders)
        
        # Assert: Correct number of orders
        assert len(result) == 3
        
        # Assert: First order (shipped with shipment fields)
        assert result[0]['orderId'] == 'ord_1735392000000'
        assert result[0]['status'] == 'shipped'
        assert 'shipment_id' not in result[0]
        assert 'tracking_number' not in result[0]
        assert result[0]['deviceSKU'] == 'AQ-001'
        
        # Assert: Second order (pending without shipment fields)
        assert result[1]['orderId'] == 'ord_1735392000001'
        assert result[1]['status'] == 'pending'
        assert 'shipment_id' not in result[1]
        assert result[1]['deviceSKU'] == 'AQ-002'
        
        # Assert: Third order (completed)
        assert result[2]['orderId'] == 'ord_1735392000002'
        assert result[2]['status'] == 'completed'
        assert 'shipment_id' not in result[2]
        assert result[2]['deviceSKU'] == 'AQ-003'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
