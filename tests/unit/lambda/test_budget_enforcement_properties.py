"""
Property-based tests for Budget Enforcement

Feature: dashboard-overhaul, Property 7: Budget Enforcement
Feature: dashboard-overhaul, Property 10: Budget Alert Generation
Feature: dashboard-overhaul, Property 18: Budget Reallocation Authorization
Feature: dashboard-overhaul, Property 19: ML Forecast Integration Accuracy
Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6, 7.7
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from budget_service.handler import BudgetService, BudgetServiceError


# Hypothesis strategies for generating test data

# Budget amounts (positive values)
budget_amount_strategy = st.floats(min_value=1.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)

# Purchase amounts (positive values)
purchase_amount_strategy = st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False)

# Budget categories
budget_category_strategy = st.sampled_from([
    'office-supplies', 'equipment', 'software', 'maintenance', 'utilities',
    'marketing', 'travel', 'training', 'consulting', 'emergency'
])

# Budget periods (YYYY-MM format)
budget_period_strategy = st.text(
    alphabet='0123456789-',
    min_size=7,
    max_size=7
).filter(lambda x: len(x.split('-')) == 2 and x.split('-')[0].isdigit() and x.split('-')[1].isdigit())

# User identifiers
user_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=10,
    max_size=50
)

# Order identifiers
order_id_strategy = st.uuids().map(str)

# Utilization percentages (0.0 to 1.0)
utilization_percentage_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Request context
request_context_strategy = st.fixed_dictionaries({
    'user_id': user_id_strategy,
    'correlation_id': st.uuids().map(str),
    'ip_address': st.ip_addresses().map(str),
    'user_agent': st.text(min_size=10, max_size=100)
})

# Justification text
justification_strategy = st.text(min_size=10, max_size=500)


class TestBudgetEnforcement:
    """
    Property 7: Budget Enforcement
    
    For any purchase order request, the system SHALL validate the request amount 
    against available budget allocations and SHALL prevent approval of requests 
    that would exceed allocated budgets, while maintaining real-time utilization tracking.
    """
    
    @given(
        allocated_amount=budget_amount_strategy,
        utilized_amount=st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        purchase_amount=purchase_amount_strategy,
        category=budget_category_strategy,
        order_id=order_id_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_budget_validation_prevents_overspending(
        self, allocated_amount, utilized_amount, purchase_amount, category, order_id, request_context
    ):
        """
        Property Test: Budget validation prevents overspending
        
        For any purchase amount that would exceed available budget,
        the system must deny the request and maintain accurate tracking.
        """
        # Ensure utilized amount doesn't exceed allocated amount
        assume(utilized_amount <= allocated_amount)
        
        available_amount = allocated_amount - utilized_amount
        should_be_approved = purchase_amount <= available_amount
        
        with patch('budget_service.handler.dynamodb') as mock_dynamodb:
            # Mock budget table
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            
            # Mock existing budget data
            mock_table.get_item.return_value = {
                'Item': {
                    'PK': f"BUDGET#{category}#2024-01",
                    'SK': 'ALLOCATION',
                    'category': category,
                    'period': '2024-01',
                    'allocatedAmount': Decimal(str(allocated_amount)),
                    'utilizedAmount': Decimal(str(utilized_amount)),
                    'reservedAmount': Decimal('0'),
                    'remainingAmount': Decimal(str(available_amount))
                }
            }
            
            # Mock audit logger
            with patch('budget_service.handler.audit_logger') as mock_audit_logger:
                budget_service = BudgetService(request_context)
                
                # Test budget validation
                result = budget_service.validate_budget_availability(
                    purchase_amount, category, order_id
                )
                
                # Verify budget enforcement
                assert result['available'] == should_be_approved, \
                    f"Budget validation failed: available={available_amount}, requested={purchase_amount}, should_approve={should_be_approved}"
                
                assert result['requestedAmount'] == purchase_amount
                assert result['allocatedAmount'] == allocated_amount
                assert result['utilizedAmount'] == utilized_amount
                assert result['availableAmount'] == available_amount
                assert result['category'] == category
                
                # Verify utilization calculation
                expected_utilization = utilized_amount / allocated_amount if allocated_amount > 0 else 0.0
                assert abs(result['utilizationPercentage'] - expected_utilization) < 0.001
                
                # Verify audit logging
                mock_audit_logger.log_user_action.assert_called_once()
                audit_call = mock_audit_logger.log_user_action.call_args[1]
                assert audit_call['action'] == 'VALIDATE_BUDGET_AVAILABILITY'
                assert audit_call['resource'] == 'BUDGET'
                assert audit_call['details']['amount'] == purchase_amount
                assert audit_call['details']['available'] == should_be_approved
    
    @given(
        allocated_amount=budget_amount_strategy,
        utilized_amount=st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        reserved_amount=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        purchase_amount=purchase_amount_strategy,
        category=budget_category_strategy,
        order_id=order_id_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_budget_reservation_maintains_consistency(
        self, allocated_amount, utilized_amount, reserved_amount, purchase_amount, category, order_id, request_context
    ):
        """
        Property Test: Budget reservation maintains data consistency
        
        For any budget reservation, the system must maintain consistent
        utilization tracking and prevent double-spending.
        """
        # Ensure amounts are realistic
        assume(utilized_amount + reserved_amount <= allocated_amount)
        assume(purchase_amount <= (allocated_amount - utilized_amount - reserved_amount))
        
        with patch('budget_service.handler.dynamodb') as mock_dynamodb:
            # Mock budget table
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            
            # Mock successful update
            new_utilized = utilized_amount + purchase_amount
            mock_table.update_item.return_value = {
                'Attributes': {
                    'PK': f"BUDGET#{category}#2024-01",
                    'SK': 'ALLOCATION',
                    'category': category,
                    'period': '2024-01',
                    'allocatedAmount': Decimal(str(allocated_amount)),
                    'utilizedAmount': Decimal(str(new_utilized)),
                    'reservedAmount': Decimal(str(reserved_amount)),
                    'updatedAt': '2024-01-01T00:00:00Z',
                    'updatedBy': request_context['user_id']
                }
            }
            
            # Mock audit logger
            with patch('budget_service.handler.audit_logger') as mock_audit_logger:
                budget_service = BudgetService(request_context)
                
                # Test budget reservation
                result = budget_service.reserve_budget(purchase_amount, category, order_id)
                
                # Verify reservation success
                assert result['reserved'] is True
                assert result['amount'] == purchase_amount
                assert result['category'] == category
                assert result['orderId'] == order_id
                assert result['newUtilization'] == new_utilized
                
                # Verify database update was called
                mock_table.update_item.assert_called_once()
                update_call = mock_table.update_item.call_args[1]
                assert update_call['Key']['PK'] == f"BUDGET#{category}#2024-01"
                assert update_call['Key']['SK'] == 'ALLOCATION'
                
                # Verify audit logging
                mock_audit_logger.log_user_action.assert_called_once()
                audit_call = mock_audit_logger.log_user_action.call_args[1]
                assert audit_call['action'] == 'RESERVE_BUDGET'
                assert audit_call['details']['amount'] == purchase_amount
                assert audit_call['details']['orderId'] == order_id


class TestBudgetAlertGeneration:
    """
    Property 10: Budget Alert Generation
    
    For any budget category where utilization approaches defined thresholds,
    the system SHALL generate alerts to relevant stakeholders with current
    utilization percentages and projected timeline to budget exhaustion.
    """
    
    @given(
        allocated_amount=budget_amount_strategy,
        utilization_percentage=utilization_percentage_strategy,
        category=budget_category_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_budget_alerts_generated_at_thresholds(
        self, allocated_amount, utilization_percentage, category, request_context
    ):
        """
        Property Test: Budget alerts are generated at appropriate thresholds
        
        For any budget utilization that exceeds warning thresholds,
        the system must generate appropriate alerts.
        """
        utilized_amount = allocated_amount * utilization_percentage
        
        # Define thresholds (matching service defaults)
        warning_threshold = 0.8
        critical_threshold = 0.9
        emergency_threshold = 0.95
        
        # Determine expected alert level
        expected_alert_level = 'NORMAL'
        if utilization_percentage >= emergency_threshold:
            expected_alert_level = 'EMERGENCY'
        elif utilization_percentage >= critical_threshold:
            expected_alert_level = 'CRITICAL'
        elif utilization_percentage >= warning_threshold:
            expected_alert_level = 'WARNING'
        
        should_generate_alert = expected_alert_level != 'NORMAL'
        
        with patch('budget_service.handler.dynamodb') as mock_dynamodb:
            # Mock budget table
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            
            # Mock budget data
            budget_data = {
                'PK': f"BUDGET#{category}#2024-01",
                'SK': 'ALLOCATION',
                'category': category,
                'period': '2024-01',
                'allocatedAmount': Decimal(str(allocated_amount)),
                'utilizedAmount': Decimal(str(utilized_amount)),
                'reservedAmount': Decimal('0'),
                'remainingAmount': Decimal(str(allocated_amount - utilized_amount))
            }
            
            # Mock SNS and EventBridge
            with patch('budget_service.handler.sns') as mock_sns, \
                 patch('budget_service.handler.eventbridge') as mock_eventbridge, \
                 patch('budget_service.handler.audit_logger') as mock_audit_logger:
                
                budget_service = BudgetService(request_context)
                
                # Test alert generation
                alert = budget_service._generate_budget_alert(
                    category, '2024-01', utilization_percentage, budget_data
                )
                
                if should_generate_alert:
                    # Verify alert was generated
                    assert alert is not None
                    assert alert['category'] == category
                    assert alert['alertLevel'] == expected_alert_level
                    assert abs(alert['utilizationPercentage'] - utilization_percentage) < 0.001
                    assert alert['allocatedAmount'] == allocated_amount
                    assert alert['utilizedAmount'] == utilized_amount
                    
                    # Verify notification was sent
                    mock_sns.publish.assert_called_once()
                    sns_call = mock_sns.publish.call_args[1]
                    assert expected_alert_level in sns_call['Subject']
                    assert category in sns_call['Subject']
                    
                    # Verify EventBridge event
                    mock_eventbridge.put_events.assert_called_once()
                    
                    # Verify audit logging
                    mock_audit_logger.log_system_event.assert_called_once()
                else:
                    # Verify no alert was generated
                    assert alert is None
                    mock_sns.publish.assert_not_called()
                    mock_eventbridge.put_events.assert_not_called()


class TestBudgetReallocationAuthorization:
    """
    Property 18: Budget Reallocation Authorization
    
    For any budget reallocation request, the system SHALL require proper 
    authorization based on the authority matrix, validate the reallocation 
    doesn't violate overall budget constraints, and maintain complete audit 
    trails for the reallocation decision.
    """
    
    @given(
        source_allocated=budget_amount_strategy,
        source_utilized=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        target_allocated=budget_amount_strategy,
        reallocation_amount=st.floats(min_value=1.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
        source_category=budget_category_strategy,
        target_category=budget_category_strategy,
        justification=justification_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_budget_reallocation_validates_constraints(
        self, source_allocated, source_utilized, target_allocated, reallocation_amount,
        source_category, target_category, justification, request_context
    ):
        """
        Property Test: Budget reallocation validates constraints and maintains audit trails
        
        For any budget reallocation, the system must validate constraints
        and maintain complete audit trails.
        """
        # Ensure different categories
        assume(source_category != target_category)
        
        # Ensure source has sufficient available budget
        assume(source_utilized <= source_allocated)
        source_available = source_allocated - source_utilized
        should_succeed = reallocation_amount <= source_available
        
        with patch('budget_service.handler.dynamodb') as mock_dynamodb:
            # Mock budget table
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            
            # Mock source budget data
            source_budget = {
                'PK': f"BUDGET#{source_category}#2024-01",
                'SK': 'ALLOCATION',
                'category': source_category,
                'period': '2024-01',
                'allocatedAmount': Decimal(str(source_allocated)),
                'utilizedAmount': Decimal(str(source_utilized)),
                'reservedAmount': Decimal('0'),
                'remainingAmount': Decimal(str(source_available))
            }
            
            # Mock target budget data
            target_budget = {
                'PK': f"BUDGET#{target_category}#2024-01",
                'SK': 'ALLOCATION',
                'category': target_category,
                'period': '2024-01',
                'allocatedAmount': Decimal(str(target_allocated)),
                'utilizedAmount': Decimal('0'),
                'reservedAmount': Decimal('0'),
                'remainingAmount': Decimal(str(target_allocated))
            }
            
            # Mock get_item calls for budget validation
            def mock_get_item(Key):
                if Key['PK'] == f"BUDGET#{source_category}#2024-01":
                    return {'Item': source_budget}
                elif Key['PK'] == f"BUDGET#{target_category}#2024-01":
                    return {'Item': target_budget}
                else:
                    return {}
            
            mock_table.get_item.side_effect = mock_get_item
            
            # Mock batch writer for atomic updates
            mock_batch_writer = Mock()
            mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer
            
            # Mock audit logger
            with patch('budget_service.handler.audit_logger') as mock_audit_logger:
                budget_service = BudgetService(request_context)
                
                reallocation_data = {
                    'sourceCategory': source_category,
                    'targetCategory': target_category,
                    'amount': reallocation_amount,
                    'justification': justification,
                    'period': '2024-01'
                }
                
                if should_succeed:
                    # Test successful reallocation
                    result = budget_service.reallocate_budget(reallocation_data)
                    
                    # Verify reallocation success
                    assert result['reallocated'] is True
                    assert result['sourceCategory'] == source_category
                    assert result['targetCategory'] == target_category
                    assert result['amount'] == reallocation_amount
                    
                    # Verify batch operations were called
                    assert mock_batch_writer.put_item.call_count == 2
                    
                    # Verify audit logging
                    mock_audit_logger.log_user_action.assert_called_once()
                    audit_call = mock_audit_logger.log_user_action.call_args[1]
                    assert audit_call['action'] == 'REALLOCATE_BUDGET'
                    assert audit_call['details']['sourceCategory'] == source_category
                    assert audit_call['details']['targetCategory'] == target_category
                    assert audit_call['details']['amount'] == reallocation_amount
                    assert audit_call['details']['justification'] == justification
                else:
                    # Test failed reallocation due to insufficient budget
                    with pytest.raises(BudgetServiceError) as exc_info:
                        budget_service.reallocate_budget(reallocation_data)
                    
                    assert "Insufficient available budget" in str(exc_info.value)


class TestMLForecastIntegrationAccuracy:
    """
    Property 19: ML Forecast Integration Accuracy
    
    For any budget planning or demand forecasting operation, the system SHALL 
    integrate ML forecast data when available, clearly indicate forecast vs. 
    actual variance, and maintain read-only access to forecast data to prevent 
    unauthorized modifications.
    """
    
    @given(
        category=budget_category_strategy,
        actual_spend=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        forecasted_spend=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        forecast_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        forecast_accuracy=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_ml_forecast_integration_maintains_accuracy(
        self, category, actual_spend, forecasted_spend, forecast_confidence, forecast_accuracy, request_context
    ):
        """
        Property Test: ML forecast integration maintains accuracy and read-only access
        
        For any ML forecast integration, the system must accurately calculate
        variance and maintain read-only access to forecast data.
        """
        with patch('budget_service.handler.dynamodb') as mock_dynamodb:
            # Mock tables
            mock_budget_table = Mock()
            mock_ml_table = Mock()
            
            def mock_table(table_name):
                if 'ML-Forecasts' in table_name:
                    return mock_ml_table
                else:
                    return mock_budget_table
            
            mock_dynamodb.Table.side_effect = mock_table
            
            # Mock ML forecast data
            mock_ml_table.get_item.return_value = {
                'Item': {
                    'PK': f"FORECAST#{category}#2024-01",
                    'SK': 'BUDGET_PREDICTION',
                    'category': category,
                    'period': '2024-01',
                    'predictedSpend': Decimal(str(forecasted_spend)),
                    'confidence': Decimal(str(forecast_confidence)),
                    'accuracy': Decimal(str(forecast_accuracy)),
                    'generatedAt': '2024-01-01T00:00:00Z'
                }
            }
            
            # Mock budget utilization data
            mock_budget_table.query.return_value = {
                'Items': [{
                    'PK': f"BUDGET#{category}#2024-01",
                    'SK': 'ALLOCATION',
                    'category': category,
                    'period': '2024-01',
                    'allocatedAmount': Decimal('100000'),
                    'utilizedAmount': Decimal(str(actual_spend)),
                    'reservedAmount': Decimal('0')
                }]
            }
            
            budget_service = BudgetService(request_context)
            
            # Test forecast comparison
            result = budget_service.get_spend_forecast_comparison({'period': '2024-01', 'category': category})
            
            # Verify forecast integration
            assert len(result['comparisonData']) == 1
            comparison = result['comparisonData'][0]
            
            assert comparison['category'] == category
            assert comparison['actualSpend'] == actual_spend
            assert comparison['forecastedSpend'] == forecasted_spend
            
            # Verify variance calculation accuracy
            expected_variance = actual_spend - forecasted_spend
            assert abs(comparison['variance'] - expected_variance) < 0.001
            
            if forecasted_spend > 0:
                expected_variance_percentage = (expected_variance / forecasted_spend) * 100
                assert abs(comparison['variancePercentage'] - expected_variance_percentage) < 0.001
            
            # Verify forecast metadata is preserved (read-only)
            assert comparison['forecastAccuracy'] == forecast_accuracy
            
            # Verify summary calculations
            summary = result['summary']
            assert summary['totalActualSpend'] == actual_spend
            assert summary['totalForecastedSpend'] == forecasted_spend
            assert abs(summary['overallVariance'] - expected_variance) < 0.001
    
    @given(
        category=budget_category_strategy,
        allocated_amount=budget_amount_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_ml_forecast_graceful_degradation_to_rule_based(
        self, category, allocated_amount, request_context
    ):
        """
        Property Test: ML forecast graceful degradation to rule-based prediction
        
        When ML forecast is unavailable, the system must gracefully degrade
        to rule-based prediction while maintaining accuracy indicators.
        """
        with patch('budget_service.handler.dynamodb') as mock_dynamodb:
            # Mock tables
            mock_budget_table = Mock()
            mock_ml_table = Mock()
            
            def mock_table(table_name):
                if 'ML-Forecasts' in table_name:
                    return mock_ml_table
                else:
                    return mock_budget_table
            
            mock_dynamodb.Table.side_effect = mock_table
            
            # Mock ML forecast unavailable (empty response)
            mock_ml_table.get_item.return_value = {}
            
            # Mock budget data for rule-based fallback
            mock_budget_table.get_item.return_value = {
                'Item': {
                    'PK': f"BUDGET#{category}#2024-01",
                    'SK': 'ALLOCATION',
                    'category': category,
                    'period': '2024-01',
                    'allocatedAmount': Decimal(str(allocated_amount)),
                    'utilizedAmount': Decimal('0'),
                    'reservedAmount': Decimal('0')
                }
            }
            
            budget_service = BudgetService(request_context)
            
            # Test rule-based forecast generation
            forecast = budget_service._get_detailed_ml_forecast(category, '2024-01')
            
            # Verify graceful degradation
            assert forecast['available'] is True
            assert forecast['method'] == 'rule-based'
            
            # Verify rule-based prediction (80% of allocated budget)
            expected_prediction = allocated_amount * 0.8
            assert abs(forecast['predictedSpend'] - expected_prediction) < 0.001
            
            # Verify lower confidence for rule-based prediction
            assert forecast['confidence'] == 0.6
            assert forecast['accuracy'] == 0.7
            
            # Verify timestamp is present
            assert 'generatedAt' in forecast
