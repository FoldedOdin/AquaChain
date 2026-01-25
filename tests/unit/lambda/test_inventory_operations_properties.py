"""
Property-based tests for inventory operations

Feature: dashboard-overhaul, Property 4: Inventory Alert Generation
Feature: dashboard-overhaul, Property 12: Comprehensive Graceful Degradation (ML fallback)
Validates: Requirements 1.6, 13.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from inventory_management.handler import InventoryService


# Hypothesis strategies for generating test data

# Stock levels (non-negative numbers)
stock_level_strategy = st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)

# Positive numbers for thresholds
positive_float_strategy = st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False)

# Item identifiers
item_id_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
    min_size=5,
    max_size=20
)

location_id_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
    min_size=3,
    max_size=15
)

# Inventory item data
inventory_item_strategy = st.fixed_dictionaries({
    'item_id': item_id_strategy,
    'location_id': location_id_strategy,
    'name': st.text(min_size=3, max_size=50),
    'current_stock': stock_level_strategy,
    'reorder_point': positive_float_strategy,
    'safety_stock': positive_float_strategy,
    'critical_threshold': positive_float_strategy,
    'reorder_quantity': positive_float_strategy,
    'avg_daily_demand': positive_float_strategy,
    'unit_cost': positive_float_strategy,
    'supplier_id': st.text(min_size=5, max_size=20),
    'category': st.sampled_from(['filters', 'sensors', 'pumps', 'chemicals', 'maintenance']),
    'status': st.sampled_from(['active', 'inactive', 'discontinued']),
    'created_at': st.datetimes().map(lambda dt: dt.isoformat()),
    'updated_at': st.datetimes().map(lambda dt: dt.isoformat())
})

# Request context for audit logging
request_context_strategy = st.fixed_dictionaries({
    'user_id': st.text(min_size=10, max_size=30),
    'correlation_id': st.uuids().map(str),
    'ip_address': st.ip_addresses().map(str),
    'user_agent': st.text(min_size=10, max_size=100),
    'request_id': st.uuids().map(str)
})

# Forecast days
forecast_days_strategy = st.integers(min_value=1, max_value=365)


class TestInventoryAlertGeneration:
    """
    Property 4: Inventory Alert Generation
    
    For any inventory item where current stock levels are at or below the reorder point,
    the system SHALL generate and display real-time alerts with recommended actions
    to users with appropriate permissions.
    """
    
    @given(
        item=inventory_item_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_reorder_alerts_generated_when_stock_below_reorder_point(self, item, request_context):
        """
        Property Test: Reorder alerts are generated when stock is below reorder point
        
        For any inventory item where current_stock <= reorder_point,
        the system must generate appropriate alerts with correct urgency levels.
        """
        # Ensure stock is at or below reorder point
        assume(item['current_stock'] <= item['reorder_point'])
        
        with patch('inventory_management.handler.inventory_table') as mock_table, \
             patch('inventory_management.handler.sns') as mock_sns, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB responses
            mock_table.get_item.return_value = {'Item': item}
            mock_table.update_item.return_value = {'Attributes': item}
            
            # Initialize inventory service
            inventory_service = InventoryService(request_context)
            
            # Test alert generation logic
            inventory_service._check_and_generate_alerts(item)
            
            # Verify reorder status was updated
            mock_table.update_item.assert_called()
            update_call = mock_table.update_item.call_args
            
            # Check that reorder_status was set to 'needs_reorder'
            assert ':status' in update_call[1]['ExpressionAttributeValues']
            assert update_call[1]['ExpressionAttributeValues'][':status'] == 'needs_reorder'
            
            # Verify urgency was calculated and set
            assert ':urgency' in update_call[1]['ExpressionAttributeValues']
            urgency = update_call[1]['ExpressionAttributeValues'][':urgency']
            assert urgency in ['critical', 'high', 'medium', 'low']
            
            # Verify SNS alert was sent if topic is configured
            if inventory_service.sns_topic:
                mock_sns.publish.assert_called_once()
                sns_call = mock_sns.publish.call_args
                
                # Verify alert message structure
                message_data = json.loads(sns_call[1]['Message'])
                assert message_data['alert_type'] == 'reorder_needed'
                assert message_data['item_id'] == item['item_id']
                assert message_data['current_stock'] == item['current_stock']
                assert message_data['urgency'] == urgency
    
    @given(
        item=inventory_item_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_alert_urgency_calculation_is_consistent(self, item, request_context):
        """
        Property Test: Alert urgency calculation is consistent
        
        For any inventory item, the urgency calculation must be consistent
        and based on stock status and days of supply.
        """
        inventory_service = InventoryService(request_context)
        
        # Calculate stock status and urgency
        stock_status = inventory_service._calculate_stock_status(item)
        urgency = inventory_service._calculate_reorder_urgency(item)
        days_of_supply = inventory_service._calculate_days_of_supply(item)
        
        # Verify urgency is consistent with stock status
        if stock_status == 'out_of_stock':
            assert urgency == 'critical', f"Out of stock items must have critical urgency, got {urgency}"
        elif stock_status == 'critical' or days_of_supply <= 3:
            assert urgency in ['critical', 'high'], f"Critical stock must have critical/high urgency, got {urgency}"
        elif stock_status in ['very_low', 'low'] or days_of_supply <= 7:
            assert urgency in ['high', 'medium'], f"Low stock must have high/medium urgency, got {urgency}"
        else:
            assert urgency in ['medium', 'low'], f"Normal stock must have medium/low urgency, got {urgency}"
    
    @given(
        item=inventory_item_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_recommended_actions_are_provided_with_alerts(self, item, request_context):
        """
        Property Test: Recommended actions are provided with alerts
        
        For any inventory item that triggers an alert, the system must provide
        appropriate recommended actions based on urgency level.
        """
        inventory_service = InventoryService(request_context)
        
        # Enrich item to get recommended actions
        enriched_item = inventory_service._enrich_inventory_item(item)
        recommended_actions = inventory_service._get_recommended_actions(enriched_item)
        
        # Verify recommended actions are provided
        assert isinstance(recommended_actions, list), "Recommended actions must be a list"
        assert len(recommended_actions) > 0, "At least one recommended action must be provided"
        
        # Verify action structure
        for action in recommended_actions:
            assert 'action' in action, "Each action must have an 'action' field"
            assert 'description' in action, "Each action must have a 'description' field"
            assert 'priority' in action, "Each action must have a 'priority' field"
            assert action['priority'] in ['high', 'medium', 'low'], f"Invalid priority: {action['priority']}"
        
        # Verify urgency-appropriate actions
        urgency = enriched_item.get('reorder_urgency', 'low')
        action_types = [action['action'] for action in recommended_actions]
        
        if urgency == 'critical':
            assert 'emergency_order' in action_types, "Critical urgency must include emergency order action"
        elif urgency == 'high':
            assert 'expedited_order' in action_types, "High urgency must include expedited order action"
    
    @given(
        items=st.lists(inventory_item_strategy, min_size=1, max_size=20),
        urgency_filter=st.one_of(st.none(), st.sampled_from(['critical', 'high', 'medium', 'low'])),
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_reorder_alerts_filtering_works_correctly(self, items, urgency_filter, request_context):
        """
        Property Test: Reorder alerts filtering works correctly
        
        For any list of inventory items and urgency filter, the system must
        return only items matching the filter criteria.
        """
        with patch('inventory_management.handler.inventory_table') as mock_table, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock DynamoDB query to return items that need reordering
            reorder_items = []
            for item in items:
                # Make some items need reordering
                if item['current_stock'] <= item['reorder_point']:
                    item['reorder_status'] = 'needs_reorder'
                    reorder_items.append(item)
            
            mock_table.query.return_value = {'Items': reorder_items}
            
            # Mock supplier table for enrichment
            with patch('inventory_management.handler.suppliers_table') as mock_suppliers_table:
                mock_suppliers_table.get_item.return_value = {
                    'Item': {'supplier_id': 'test', 'name': 'Test Supplier'}
                }
                
                inventory_service = InventoryService(request_context)
                
                # Get reorder alerts with filter
                result = inventory_service.get_reorder_alerts(urgency_filter)
                
                # Verify response structure
                assert result['statusCode'] == 200
                alerts = result['body']['alerts']
                
                # If filter is applied, verify all returned items match the filter
                if urgency_filter:
                    for alert in alerts:
                        assert alert.get('reorder_urgency') == urgency_filter or alert.get('urgency') == urgency_filter, \
                            f"Alert urgency {alert.get('urgency')} doesn't match filter {urgency_filter}"


class TestComprehensiveGracefulDegradation:
    """
    Property 12: Comprehensive Graceful Degradation (ML fallback)
    
    For any dependent service failure (ML forecasting, real-time data, authentication, database),
    the system SHALL degrade gracefully by falling back to alternative methods,
    displaying last-known-good data with warnings, and providing clear status indicators.
    """
    
    @given(
        item_id=item_id_strategy,
        forecast_days=forecast_days_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_ml_forecasting_fallback_to_rule_based(self, item_id, forecast_days, request_context):
        """
        Property Test: ML forecasting falls back to rule-based when ML service fails
        
        For any item_id and forecast_days, when ML forecasting service is unavailable,
        the system must fall back to rule-based forecasting with appropriate warnings.
        """
        with patch('inventory_management.handler.lambda_client') as mock_lambda_client, \
             patch('inventory_management.handler.forecasts_table') as mock_forecasts_table, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock ML service failure
            mock_lambda_client.invoke.side_effect = Exception("ML service unavailable")
            
            # Mock no cached forecast
            mock_forecasts_table.get_item.return_value = {}
            
            inventory_service = InventoryService(request_context)
            
            # Test demand forecast with ML failure
            result = inventory_service.get_demand_forecast(item_id, forecast_days)
            
            # Verify successful response with fallback
            assert result['statusCode'] == 200
            forecast_data = result['body']
            
            # Verify fallback was used
            assert forecast_data['source'] == 'rule_based'
            assert 'warning' in forecast_data
            assert 'ML forecasting service unavailable' in forecast_data['warning']
            
            # Verify forecast structure
            forecast = forecast_data['forecast']
            assert forecast['item_id'] == item_id
            assert forecast['forecast_horizon_days'] == forecast_days
            assert forecast['method'] in ['rule_based', 'fallback']
            assert 'predictions' in forecast
            assert len(forecast['predictions']) == forecast_days
            
            # Verify each prediction has required fields
            for prediction in forecast['predictions']:
                assert 'date' in prediction
                assert 'demand' in prediction
                assert 'confidence_lower' in prediction
                assert 'confidence_upper' in prediction
                assert prediction['demand'] >= 0
                assert prediction['confidence_lower'] >= 0
                assert prediction['confidence_upper'] >= prediction['confidence_lower']
    
    @given(
        item_id=item_id_strategy,
        forecast_days=forecast_days_strategy,
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_circuit_breaker_prevents_repeated_ml_service_calls(self, item_id, forecast_days, request_context):
        """
        Property Test: Circuit breaker prevents repeated calls to failed ML service
        
        For any item_id and forecast_days, when ML service fails repeatedly,
        the circuit breaker must prevent additional calls and use fallback immediately.
        """
        with patch('inventory_management.handler.lambda_client') as mock_lambda_client, \
             patch('inventory_management.handler.forecasts_table') as mock_forecasts_table, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock ML service failure
            mock_lambda_client.invoke.side_effect = Exception("ML service unavailable")
            mock_forecasts_table.get_item.return_value = {}
            
            inventory_service = InventoryService(request_context)
            
            # First call should attempt ML service and fail
            result1 = inventory_service.get_demand_forecast(item_id, forecast_days)
            assert result1['statusCode'] == 200
            assert result1['body']['source'] == 'rule_based'
            
            # Verify ML service was called once
            assert mock_lambda_client.invoke.call_count == 1
            
            # Second call should use circuit breaker and skip ML service
            result2 = inventory_service.get_demand_forecast(item_id, forecast_days)
            assert result2['statusCode'] == 200
            assert result2['body']['source'] == 'rule_based'
            
            # Verify ML service was not called again (circuit breaker active)
            assert mock_lambda_client.invoke.call_count == 1
    
    @given(
        item_id=item_id_strategy,
        forecast_days=forecast_days_strategy,
        cached_forecast_age_hours=st.integers(min_value=1, max_value=24),
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_cached_forecast_used_when_ml_service_unavailable(self, item_id, forecast_days, cached_forecast_age_hours, request_context):
        """
        Property Test: Cached forecast is used when ML service is unavailable
        
        For any item_id and forecast_days, when ML service is unavailable but
        a fresh cached forecast exists, the system must use the cached data.
        """
        with patch('inventory_management.handler.lambda_client') as mock_lambda_client, \
             patch('inventory_management.handler.forecasts_table') as mock_forecasts_table, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock ML service failure
            mock_lambda_client.invoke.side_effect = Exception("ML service unavailable")
            
            # Mock cached forecast (fresh if < 6 hours old)
            cached_forecast_time = datetime.utcnow() - timedelta(hours=cached_forecast_age_hours)
            cached_forecast = {
                'item_id': item_id,
                'forecast_horizon_days': forecast_days,
                'forecast_date': cached_forecast_time.isoformat(),
                'predictions': [{'date': datetime.utcnow().isoformat(), 'demand': 5.0}],
                'method': 'ml',
                'accuracy_metrics': {'mae': 0.5}
            }
            
            mock_forecasts_table.get_item.return_value = {'Item': cached_forecast}
            
            inventory_service = InventoryService(request_context)
            
            # Test demand forecast
            result = inventory_service.get_demand_forecast(item_id, forecast_days)
            
            assert result['statusCode'] == 200
            forecast_data = result['body']
            
            # If cache is fresh (< 6 hours), should use cached data
            if cached_forecast_age_hours < 6:
                assert forecast_data['source'] == 'ml'
                assert 'accuracy_metrics' in forecast_data
                # ML service should not have been called due to cache hit
                mock_lambda_client.invoke.assert_not_called()
            else:
                # Cache is stale, should fall back to rule-based
                assert forecast_data['source'] == 'rule_based'
                assert 'warning' in forecast_data
    
    @given(
        items=st.lists(inventory_item_strategy, min_size=1, max_size=10),
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_database_failure_graceful_degradation(self, items, request_context):
        """
        Property Test: Database failures are handled gracefully
        
        For any inventory operation, when database operations fail,
        the system must handle the failure gracefully and return appropriate errors.
        """
        with patch('inventory_management.handler.inventory_table') as mock_table, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock database failure
            mock_table.scan.side_effect = Exception("Database connection failed")
            mock_table.query.side_effect = Exception("Database connection failed")
            
            inventory_service = InventoryService(request_context)
            
            # Test stock levels retrieval with database failure
            result = inventory_service.get_stock_levels()
            
            # Verify graceful error handling
            assert result['statusCode'] == 500
            assert 'error' in result['body']
            assert 'correlation_id' in result['body']
            
            # Verify audit logging was attempted (even if it might fail)
            mock_audit_logger.log_data_access.assert_called_once()
    
    @given(
        item_id=item_id_strategy,
        location_id=location_id_strategy,
        updates=st.dictionaries(
            keys=st.sampled_from(['current_stock', 'reorder_point', 'safety_stock']),
            values=positive_float_strategy,
            min_size=1,
            max_size=3
        ),
        request_context=request_context_strategy
    )
    @settings(max_examples=3)
    def test_audit_logging_failure_does_not_break_operations(self, item_id, location_id, updates, request_context):
        """
        Property Test: Audit logging failures do not break core operations
        
        For any inventory operation, when audit logging fails, the core operation
        must still succeed and the failure must be handled gracefully.
        """
        with patch('inventory_management.handler.inventory_table') as mock_table, \
             patch('inventory_management.handler.audit_logger') as mock_audit_logger:
            
            # Mock successful database operations
            current_item = {
                'item_id': item_id,
                'location_id': location_id,
                'current_stock': 100.0,
                'reorder_point': 50.0
            }
            updated_item = current_item.copy()
            updated_item.update(updates)
            
            mock_table.get_item.return_value = {'Item': current_item}
            mock_table.update_item.return_value = {'Attributes': updated_item}
            
            # Mock audit logging failure
            mock_audit_logger.log_data_modification.side_effect = Exception("Audit logging failed")
            
            inventory_service = InventoryService(request_context)
            
            # Test stock level update with audit logging failure
            result = inventory_service.update_stock_level(item_id, location_id, updates)
            
            # Core operation should still succeed despite audit logging failure
            assert result['statusCode'] == 200
            assert 'item' in result['body']
            assert result['body']['item']['item_id'] == item_id
            
            # Verify database operations were performed
            mock_table.get_item.assert_called_once()
            mock_table.update_item.assert_called_once()
    
    @given(
        request_context=request_context_strategy
    )
    @settings(max_examples=5)
    def test_health_check_reports_service_degradation(self, request_context):
        """
        Property Test: Health check reports service degradation
        
        For any service health check, when dependent services are failing,
        the health check must report degraded status with details.
        """
        with patch('inventory_management.handler.health_monitor') as mock_health_monitor:
            
            # Mock degraded health status
            degraded_health = {
                'service': 'inventory-service',
                'status': 'degraded',
                'timestamp': datetime.utcnow().isoformat(),
                'checks': {
                    'dynamodb': {'healthy': True, 'response_time_ms': 50},
                    's3': {'healthy': False, 'error': 'Connection timeout'},
                    'kms': {'healthy': True, 'response_time_ms': 30}
                },
                'failed_checks': ['s3']
            }
            
            mock_health_monitor.check_service_health.return_value = degraded_health
            
            # Simulate health check endpoint call
            event = {
                'httpMethod': 'GET',
                'path': '/api/inventory/health',
                'requestContext': {'authorizer': {'user_id': request_context['user_id']}}
            }
            
            from inventory_management.handler import lambda_handler
            result = lambda_handler(event, {})
            
            # Verify health check response
            assert result['statusCode'] == 503  # Service unavailable due to degradation
            health_data = json.loads(result['body'])
            assert health_data['status'] == 'degraded'
            assert 'failed_checks' in health_data
            assert 's3' in health_data['failed_checks']
            
            # Verify health metrics were published
            mock_health_monitor.publish_health_metrics.assert_called_once()
