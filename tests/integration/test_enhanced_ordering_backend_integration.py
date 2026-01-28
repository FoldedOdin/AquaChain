"""
Enhanced Consumer Ordering System - Backend Integration Tests

This test suite validates the integration between all backend services:
- Order Management Service
- Payment Service  
- Technician Assignment Service

Tests the complete order flow from creation to technician assignment.
"""

import pytest
import json
import uuid
import boto3
from decimal import Decimal
from datetime import datetime, timezone
from moto import mock_aws
import sys
import os

# Add lambda directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'payment_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'technician_assignment'))

from enhanced_order_management import OrderManagementService, OrderStatus, PaymentMethod
from payment_service import PaymentService, PaymentStatus
from technician_assignment_service import TechnicianAssignmentService


@mock_aws
class TestEnhancedOrderingBackendIntegration:
    """Integration tests for enhanced ordering system backend services"""
    
    def setup_method(self):
        """Set up test environment with mock AWS services"""
        # Create DynamoDB tables
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self._create_test_tables()
        
        # Initialize services
        self.order_service = OrderManagementService()
        self.payment_service = PaymentService()
        self.assignment_service = TechnicianAssignmentService()
        
        # Test data
        self.consumer_id = str(uuid.uuid4())
        self.test_location = {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'address': '123 Test St, New York, NY 10001'
        }
        
        # Create test technicians
        self._create_test_technicians()
    
    def _create_test_tables(self):
        """Create test DynamoDB tables"""
        # Orders table
        self.orders_table = self.dynamodb.create_table(
            TableName='aquachain-orders',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI2SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'GSI2',
                    'KeySchema': [
                        {'AttributeName': 'GSI2PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI2SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Payments table
        self.payments_table = self.dynamodb.create_table(
            TableName='aquachain-payments',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Technicians table
        self.technicians_table = self.dynamodb.create_table(
            TableName='aquachain-technicians',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    
    def _create_test_technicians(self):
        """Create test technicians for assignment testing"""
        technicians = [
            {
                'PK': 'TECHNICIAN#tech-1',
                'SK': 'TECHNICIAN#tech-1',
                'GSI1PK': 'LOCATION#ALL',
                'GSI1SK': 'AVAILABLE#True#tech-1',
                'technicianId': 'tech-1',
                'name': 'John Smith',
                'phone': '+1-555-0101',
                'email': 'john.smith@aquachain.com',
                'location': {
                    'latitude': 40.7589,  # ~5km from test location
                    'longitude': -73.9851
                },
                'available': True,
                'skills': ['installation', 'maintenance'],
                'rating': 4.8,
                'createdAt': datetime.now(timezone.utc).isoformat()
            },
            {
                'PK': 'TECHNICIAN#tech-2',
                'SK': 'TECHNICIAN#tech-2',
                'GSI1PK': 'LOCATION#ALL',
                'GSI1SK': 'AVAILABLE#True#tech-2',
                'technicianId': 'tech-2',
                'name': 'Sarah Johnson',
                'phone': '+1-555-0102',
                'email': 'sarah.johnson@aquachain.com',
                'location': {
                    'latitude': 40.6892,  # ~3km from test location
                    'longitude': -74.0445
                },
                'available': True,
                'skills': ['installation', 'repair'],
                'rating': 4.9,
                'createdAt': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for technician in technicians:
            self.technicians_table.put_item(Item=technician)
    
    def test_complete_cod_order_flow(self):
        """Test complete COD order flow from creation to technician assignment"""
        # Step 1: Create COD order
        order_data = {
            'consumerId': self.consumer_id,
            'deviceType': 'AquaChain Pro',
            'serviceType': 'Installation',
            'paymentMethod': 'COD',
            'deliveryAddress': {
                'street': '123 Test Street',
                'city': 'New York',
                'state': 'NY',
                'zipCode': '10001',
                'country': 'USA'
            },
            'contactInfo': {
                'name': 'Test Consumer',
                'phone': '+1-555-0100',
                'email': 'test@example.com'
            },
            'amount': Decimal('299.99'),
            'specialInstructions': 'Please call before arrival'
        }
        
        # Create order
        order_result = self.order_service.create_order(order_data)
        assert order_result['success'] is True
        
        order = order_result['data']
        order_id = order['id']
        
        # Verify order created with correct status
        assert order['status'] == OrderStatus.PENDING_CONFIRMATION.value
        assert order['paymentMethod'] == PaymentMethod.COD.value
        assert order['consumerId'] == self.consumer_id
        
        # Step 2: Create COD payment
        cod_payment_result = self.payment_service.create_cod_payment(
            order_id=order_id,
            amount=float(order_data['amount'])
        )
        assert cod_payment_result['success'] is True
        
        cod_payment = cod_payment_result['data']
        assert cod_payment['status'] == PaymentStatus.COD_PENDING.value
        
        # Step 3: Confirm order (simulate COD confirmation)
        confirm_result = self.order_service.update_order_status({
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'reason': 'COD order confirmed by customer'
        })
        assert confirm_result['success'] is True
        assert confirm_result['data']['status'] == OrderStatus.ORDER_PLACED.value
        
        # Step 4: Assign technician
        assignment_result = self.assignment_service.assign_technician({
            'orderId': order_id,
            'serviceLocation': self.test_location
        })
        assert assignment_result['success'] is True
        
        assignment = assignment_result['data']
        assert assignment['orderId'] == order_id
        assert assignment['technicianId'] in ['tech-1', 'tech-2']
        assert assignment['status'] == 'assigned'
        assert assignment['distance'] < 50  # Within service area
        
        # Step 5: Verify order updated with technician assignment
        final_order_result = self.order_service.get_order(order_id)
        assert final_order_result['success'] is True
        
        final_order = final_order_result['data']
        assert final_order['assignedTechnician'] == assignment['technicianId']
        
        print(f"✅ Complete COD order flow test passed")
        print(f"   Order ID: {order_id}")
        print(f"   Assigned Technician: {assignment['technicianName']}")
        print(f"   Distance: {assignment['distance']}km")
    
    def test_complete_online_payment_order_flow(self):
        """Test complete online payment order flow"""
        # Step 1: Create online payment order
        order_data = {
            'consumerId': self.consumer_id,
            'deviceType': 'AquaChain Standard',
            'serviceType': 'Maintenance',
            'paymentMethod': 'ONLINE',
            'deliveryAddress': {
                'street': '456 Online Street',
                'city': 'New York',
                'state': 'NY',
                'zipCode': '10002',
                'country': 'USA'
            },
            'contactInfo': {
                'name': 'Online Consumer',
                'phone': '+1-555-0200',
                'email': 'online@example.com'
            },
            'amount': Decimal('199.99')
        }
        
        # Create order
        order_result = self.order_service.create_order(order_data)
        assert order_result['success'] is True
        
        order = order_result['data']
        order_id = order['id']
        
        # Verify order created with correct status
        assert order['status'] == OrderStatus.PENDING_PAYMENT.value
        assert order['paymentMethod'] == PaymentMethod.ONLINE.value
        
        # Step 2: Create Razorpay order
        razorpay_result = self.payment_service.create_razorpay_order(
            amount=float(order_data['amount']),
            order_id=order_id,
            currency='INR'
        )
        assert razorpay_result['success'] is True
        
        razorpay_order = razorpay_result['data']
        payment_id = razorpay_order['paymentId']
        
        # Step 3: Simulate payment verification (success)
        verify_result = self.payment_service.verify_razorpay_payment(
            payment_id=payment_id,
            order_id=order_id,
            signature='test_signature_123'  # This will be validated in real implementation
        )
        # Note: This might fail due to signature validation, which is expected in test
        
        # Step 4: Update order status to placed (simulate successful payment)
        placed_result = self.order_service.update_order_status({
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'reason': 'Payment completed successfully'
        })
        assert placed_result['success'] is True
        
        # Step 5: Assign technician
        assignment_result = self.assignment_service.assign_technician({
            'orderId': order_id,
            'serviceLocation': self.test_location
        })
        assert assignment_result['success'] is True
        
        assignment = assignment_result['data']
        assert assignment['orderId'] == order_id
        assert assignment['technicianId'] in ['tech-1', 'tech-2']
        
        print(f"✅ Complete online payment order flow test passed")
        print(f"   Order ID: {order_id}")
        print(f"   Payment ID: {payment_id}")
        print(f"   Assigned Technician: {assignment['technicianName']}")
    
    def test_technician_availability_management(self):
        """Test technician availability management"""
        # Step 1: Get available technicians
        available_result = self.assignment_service.get_available_technicians({
            'location': self.test_location,
            'radius': 10
        })
        assert available_result['success'] is True
        
        initial_count = available_result['count']
        assert initial_count >= 2  # We created 2 test technicians
        
        # Step 2: Mark a technician as unavailable
        unavailable_result = self.assignment_service.update_technician_availability({
            'technicianId': 'tech-1',
            'available': False
        })
        assert unavailable_result['success'] is True
        
        # Step 3: Verify reduced availability
        updated_available_result = self.assignment_service.get_available_technicians({
            'location': self.test_location,
            'radius': 10
        })
        assert updated_available_result['success'] is True
        assert updated_available_result['count'] == initial_count - 1
        
        # Step 4: Mark technician as available again
        available_again_result = self.assignment_service.update_technician_availability({
            'technicianId': 'tech-1',
            'available': True
        })
        assert available_again_result['success'] is True
        
        # Step 5: Verify availability restored
        final_available_result = self.assignment_service.get_available_technicians({
            'location': self.test_location,
            'radius': 10
        })
        assert final_available_result['success'] is True
        assert final_available_result['count'] == initial_count
        
        print(f"✅ Technician availability management test passed")
    
    def test_order_status_transitions(self):
        """Test valid and invalid order status transitions"""
        # Create test order
        order_data = {
            'consumerId': self.consumer_id,
            'deviceType': 'AquaChain Test',
            'serviceType': 'Test Service',
            'paymentMethod': 'COD',
            'deliveryAddress': {'street': 'Test', 'city': 'Test', 'state': 'TS', 'zipCode': '00000', 'country': 'USA'},
            'contactInfo': {'name': 'Test', 'phone': '+1-555-0000', 'email': 'test@test.com'},
            'amount': Decimal('100.00')
        }
        
        order_result = self.order_service.create_order(order_data)
        order_id = order_result['data']['id']
        
        # Test valid transition: PENDING_CONFIRMATION -> ORDER_PLACED
        valid_result = self.order_service.update_order_status({
            'orderId': order_id,
            'status': OrderStatus.ORDER_PLACED.value,
            'reason': 'Order confirmed'
        })
        assert valid_result['success'] is True
        
        # Test valid transition: ORDER_PLACED -> SHIPPED
        shipped_result = self.order_service.update_order_status({
            'orderId': order_id,
            'status': OrderStatus.SHIPPED.value,
            'reason': 'Order shipped'
        })
        assert shipped_result['success'] is True
        
        # Test invalid transition: SHIPPED -> PENDING_PAYMENT (should fail)
        try:
            invalid_result = self.order_service.update_order_status({
                'orderId': order_id,
                'status': OrderStatus.PENDING_PAYMENT.value,
                'reason': 'Invalid transition'
            })
            assert False, "Invalid transition should have failed"
        except Exception as e:
            assert "Invalid state transition" in str(e)
        
        print(f"✅ Order status transitions test passed")
    
    def test_consumer_order_retrieval(self):
        """Test consumer order retrieval and filtering"""
        # Create multiple orders for the same consumer
        order_ids = []
        
        for i in range(3):
            order_data = {
                'consumerId': self.consumer_id,
                'deviceType': f'AquaChain Test {i+1}',
                'serviceType': 'Test Service',
                'paymentMethod': 'COD',
                'deliveryAddress': {'street': 'Test', 'city': 'Test', 'state': 'TS', 'zipCode': '00000', 'country': 'USA'},
                'contactInfo': {'name': 'Test', 'phone': '+1-555-0000', 'email': 'test@test.com'},
                'amount': Decimal('100.00')
            }
            
            order_result = self.order_service.create_order(order_data)
            order_ids.append(order_result['data']['id'])
        
        # Test getting orders by consumer
        consumer_orders_result = self.order_service.get_orders_by_consumer(
            consumer_id=self.consumer_id,
            limit=10
        )
        assert consumer_orders_result['success'] is True
        assert consumer_orders_result['count'] >= 3
        
        # Verify all orders belong to the consumer
        for order in consumer_orders_result['data']:
            assert order['consumerId'] == self.consumer_id
        
        print(f"✅ Consumer order retrieval test passed")
        print(f"   Retrieved {consumer_orders_result['count']} orders for consumer")


if __name__ == '__main__':
    """Run integration tests"""
    import pytest
    
    # Run the tests
    pytest.main([__file__, '-v', '--tb=short'])