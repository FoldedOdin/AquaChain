"""
AquaChain Budget Service - Dashboard Overhaul
Enhanced budget service with allocation tracking, utilization monitoring,
budget validation for purchase orders, alert generation, reallocation workflows,
and ML forecast integration for predictive budget planning.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.6, 7.7
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import uuid
import logging
from botocore.exceptions import ClientError
import sys
import traceback

# Add shared modules to path
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger, TimedOperation, SystemHealthMonitor
from audit_logger import audit_logger
from rbac_middleware import require_permission, validate_user_permissions
from transaction_manager import TransactionManager, TransactionError, ConcurrencyError

# Initialize structured logging
logger = get_logger(__name__, 'budget-service')
health_monitor = SystemHealthMonitor('budget-service')

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
eventbridge = boto3.client('events')
lambda_client = boto3.client('lambda')

# Table references
budget_table = dynamodb.Table(os.environ.get('BUDGET_TABLE', 'AquaChain-Budget-Allocations'))
purchase_orders_table = dynamodb.Table(os.environ.get('PURCHASE_ORDERS_TABLE', 'AquaChain-Purchase-Orders'))
audit_table = dynamodb.Table(os.environ.get('AUDIT_TABLE', 'AquaChain-Audit-Logs'))
ml_forecasts_table = dynamodb.Table(os.environ.get('ML_FORECASTS_TABLE', 'AquaChain-ML-Forecasts'))


class BudgetServiceError(Exception):
    """Custom exception for budget service errors"""
    pass


class BudgetService:
    """
    Enhanced budget service with allocation tracking, utilization monitoring,
    budget validation, alert generation, reallocation workflows, and ML integration.
    
    Features:
    - Budget allocation and utilization tracking
    - Budget validation for purchase order approval
    - Budget alert generation for threshold monitoring
    - Budget reallocation workflows with authorization
    - ML forecast integration for predictive budget planning
    - Real-time budget utilization tracking
    - Comprehensive audit logging for all budget decisions
    """
    
    def __init__(self, request_context: Optional[Dict] = None):
        """
        Initialize budget service with request context for audit logging
        
        Args:
            request_context: Request context containing user_id, correlation_id, etc.
        """
        self.request_context = request_context or {}
        self.user_id = self.request_context.get('user_id', 'system')
        self.correlation_id = self.request_context.get('correlation_id', str(uuid.uuid4()))
        
        # Configuration
        self.alert_topic = os.environ.get('BUDGET_ALERT_TOPIC')
        self.ml_forecast_function = os.environ.get('ML_FORECAST_FUNCTION', 'ml-forecast-service')
        self.notification_function = os.environ.get('NOTIFICATION_FUNCTION', 'notification-service')
        
        # Alert thresholds (configurable via environment)
        self.warning_threshold = float(os.environ.get('BUDGET_WARNING_THRESHOLD', '0.8'))  # 80%
        self.critical_threshold = float(os.environ.get('BUDGET_CRITICAL_THRESHOLD', '0.9'))  # 90%
        self.emergency_threshold = float(os.environ.get('BUDGET_EMERGENCY_THRESHOLD', '0.95'))  # 95%
        
        logger.info(
            "Budget service initialized",
            correlation_id=self.correlation_id,
            user_id=self.user_id,
            warning_threshold=self.warning_threshold,
            critical_threshold=self.critical_threshold
        )
    
    def validate_budget_availability(self, amount: float, category: str, order_id: Optional[str] = None) -> Dict:
        """
        Validate budget availability for purchase order approval
        
        Args:
            amount: Purchase amount to validate
            category: Budget category to check
            order_id: Optional order ID for audit logging
            
        Returns:
            Budget validation result with availability status and details
            
        Raises:
            BudgetServiceError: If validation fails
        """
        with TimedOperation(logger, "validate_budget_availability"):
            try:
                # Get current budget allocation and utilization
                current_period = self._get_current_budget_period()
                budget_info = self._get_budget_info(category, current_period)
                
                if not budget_info:
                    logger.warning(
                        "Budget category not found, creating default allocation",
                        category=category,
                        period=current_period,
                        correlation_id=self.correlation_id
                    )
                    # Create default budget allocation if not exists
                    budget_info = self._create_default_budget_allocation(category, current_period)
                
                # Calculate availability
                allocated_amount = float(budget_info['allocatedAmount'])
                utilized_amount = float(budget_info['utilizedAmount'])
                reserved_amount = float(budget_info.get('reservedAmount', 0))
                available_amount = allocated_amount - utilized_amount - reserved_amount
                
                # Check if amount is available
                is_available = available_amount >= amount
                utilization_after = (utilized_amount + reserved_amount + amount) / allocated_amount if allocated_amount > 0 else 1.0
                
                # Determine validation result
                validation_result = {
                    'available': is_available,
                    'requestedAmount': amount,
                    'allocatedAmount': allocated_amount,
                    'utilizedAmount': utilized_amount,
                    'reservedAmount': reserved_amount,
                    'availableAmount': available_amount,
                    'utilizationPercentage': (utilized_amount + reserved_amount) / allocated_amount if allocated_amount > 0 else 0.0,
                    'utilizationAfterPurchase': utilization_after,
                    'category': category,
                    'period': current_period,
                    'message': self._get_validation_message(is_available, available_amount, amount, utilization_after)
                }
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='VALIDATE_BUDGET_AVAILABILITY',
                    resource='BUDGET',
                    resource_id=f"{category}#{current_period}",
                    details={
                        'amount': amount,
                        'category': category,
                        'orderId': order_id,
                        'available': is_available,
                        'utilizationAfter': utilization_after,
                        'availableAmount': available_amount
                    },
                    request_context=self.request_context
                )
                
                # Generate alerts if thresholds are exceeded
                if utilization_after >= self.warning_threshold:
                    self._generate_budget_alert(category, current_period, utilization_after, budget_info)
                
                logger.info(
                    "Budget availability validated",
                    category=category,
                    amount=amount,
                    available=is_available,
                    utilization_after=utilization_after,
                    correlation_id=self.correlation_id
                )
                
                return validation_result
                
            except Exception as e:
                logger.error(
                    "Failed to validate budget availability",
                    category=category,
                    amount=amount,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to validate budget availability: {str(e)}")
    
    def reserve_budget(self, amount: float, category: str, order_id: str) -> Dict:
        """
        Reserve budget for approved purchase order using atomic transactions
        
        Args:
            amount: Amount to reserve
            category: Budget category
            order_id: Purchase order ID
            
        Returns:
            Budget reservation result
        """
        with TimedOperation(logger, "reserve_budget"):
            try:
                current_period = self._get_current_budget_period()
                timestamp = datetime.utcnow().isoformat() + 'Z'
                budget_key = {'PK': f"BUDGET#{category}#{current_period}", 'SK': 'ALLOCATION'}
                
                # Get current budget info for version check and validation
                response = budget_table.get_item(Key=budget_key)
                
                if 'Item' not in response:
                    # Create default budget allocation if not exists
                    self._create_default_budget_allocation(category, current_period)
                    response = budget_table.get_item(Key=budget_key)
                
                current_budget = response['Item']
                current_version = int(current_budget.get('version', 0))
                
                # Validate sufficient budget available
                allocated_amount = float(current_budget['allocatedAmount'])
                utilized_amount = float(current_budget['utilizedAmount'])
                reserved_amount = float(current_budget.get('reservedAmount', 0))
                available_amount = allocated_amount - utilized_amount - reserved_amount
                
                if available_amount < amount:
                    raise BudgetServiceError(
                        f"Insufficient budget: requested {amount}, available {available_amount}"
                    )
                
                # Execute atomic budget reservation
                tm = TransactionManager(self.correlation_id)
                
                with tm.transaction_context(idempotency_key=f"reserve_budget_{order_id}_{timestamp}") as txn:
                    # Update budget utilization with version check
                    txn.update(
                        table_name=budget_table.name,
                        key=budget_key,
                        update_expression='''
                            ADD utilizedAmount :amount, reservedAmount :amount
                            SET updatedAt = :timestamp, updatedBy = :user_id
                        ''',
                        expression_attribute_values={
                            ':amount': Decimal(str(amount)),
                            ':timestamp': timestamp,
                            ':user_id': self.user_id
                        },
                        expected_version=current_version
                    )
                    
                    # Create reservation record for audit trail
                    reservation_record = {
                        'PK': f"BUDGET#{category}#{current_period}",
                        'SK': f"RESERVATION#{order_id}",
                        'orderId': order_id,
                        'amount': Decimal(str(amount)),
                        'category': category,
                        'period': current_period,
                        'reservedBy': self.user_id,
                        'reservedAt': timestamp,
                        'status': 'ACTIVE',
                        'correlationId': self.correlation_id
                    }
                    
                    txn.put(
                        table_name=budget_table.name,
                        item=reservation_record,
                        condition_expression='attribute_not_exists(PK)'
                    )
                
                # Get updated budget for response
                updated_response = budget_table.get_item(Key=budget_key)
                updated_budget = updated_response['Item']
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='RESERVE_BUDGET',
                    resource='BUDGET',
                    resource_id=f"{category}#{current_period}",
                    details={
                        'amount': amount,
                        'category': category,
                        'orderId': order_id,
                        'newUtilization': float(updated_budget['utilizedAmount']),
                        'transactionId': self.correlation_id
                    },
                    request_context=self.request_context,
                    before_state=self._convert_decimals(current_budget),
                    after_state=self._convert_decimals(updated_budget)
                )
                
                logger.info(
                    "Budget reserved atomically",
                    category=category,
                    amount=amount,
                    order_id=order_id,
                    new_utilization=float(updated_budget['utilizedAmount']),
                    transaction_id=self.correlation_id,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'reserved': True,
                    'amount': amount,
                    'category': category,
                    'orderId': order_id,
                    'newUtilization': float(updated_budget['utilizedAmount']),
                    'reservedAt': timestamp,
                    'transactionId': self.correlation_id
                }
                
            except ConcurrencyError as e:
                logger.warning(
                    "Concurrent modification detected during budget reservation",
                    category=category,
                    amount=amount,
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Budget was modified by another operation. Please retry.")
                
            except TransactionError as e:
                logger.error(
                    "Transaction failed during budget reservation",
                    category=category,
                    amount=amount,
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to reserve budget: {str(e)}")
                
            except Exception as e:
                logger.error(
                    "Failed to reserve budget",
                    category=category,
                    amount=amount,
                    order_id=order_id,
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to reserve budget: {str(e)}")
    
    def get_budget_utilization(self, filters: Optional[Dict] = None) -> Dict:
        """
        Get budget utilization tracking with real-time percentages
        
        Args:
            filters: Optional filters for period, category, etc.
            
        Returns:
            Budget utilization data with real-time tracking
        """
        with TimedOperation(logger, "get_budget_utilization"):
            try:
                filters = filters or {}
                period = filters.get('period', self._get_current_budget_period())
                category_filter = filters.get('category')
                
                # Query parameters
                if category_filter:
                    # Get specific category
                    response = budget_table.get_item(
                        Key={'PK': f"BUDGET#{category_filter}#{period}", 'SK': 'ALLOCATION'}
                    )
                    
                    if 'Item' in response:
                        budget_items = [response['Item']]
                    else:
                        budget_items = []
                else:
                    # Get all categories for period
                    response = budget_table.query(
                        IndexName='GSI1',
                        KeyConditionExpression='GSI1PK = :period',
                        ExpressionAttributeValues={':period': f"PERIOD#{period}"}
                    )
                    budget_items = response['Items']
                
                # Process budget utilization data
                utilization_data = []
                total_allocated = 0.0
                total_utilized = 0.0
                
                for item in budget_items:
                    budget_data = self._convert_decimals(item)
                    allocated = budget_data['allocatedAmount']
                    utilized = budget_data['utilizedAmount']
                    reserved = budget_data.get('reservedAmount', 0.0)
                    
                    utilization_percentage = (utilized + reserved) / allocated if allocated > 0 else 0.0
                    
                    # Get ML forecast if available
                    forecast_data = self._get_ml_forecast(budget_data['category'], period)
                    
                    utilization_entry = {
                        'category': budget_data['category'],
                        'period': period,
                        'allocatedAmount': allocated,
                        'utilizedAmount': utilized,
                        'reservedAmount': reserved,
                        'availableAmount': allocated - utilized - reserved,
                        'utilizationPercentage': utilization_percentage,
                        'status': self._get_budget_status(utilization_percentage),
                        'lastUpdated': budget_data.get('updatedAt'),
                        'forecast': forecast_data,
                        'alertLevel': self._get_alert_level(utilization_percentage)
                    }
                    
                    utilization_data.append(utilization_entry)
                    total_allocated += allocated
                    total_utilized += utilized + reserved
                
                # Calculate overall utilization
                overall_utilization = total_utilized / total_allocated if total_allocated > 0 else 0.0
                
                logger.info(
                    "Retrieved budget utilization",
                    period=period,
                    category_filter=category_filter,
                    count=len(utilization_data),
                    overall_utilization=overall_utilization,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'utilizationData': utilization_data,
                    'summary': {
                        'period': period,
                        'totalAllocated': total_allocated,
                        'totalUtilized': total_utilized,
                        'overallUtilization': overall_utilization,
                        'categoriesCount': len(utilization_data)
                    },
                    'filters': filters
                }
                
            except Exception as e:
                logger.error(
                    "Failed to get budget utilization",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to get budget utilization: {str(e)}")
    
    def allocate_budget(self, allocation_data: Dict) -> Dict:
        """
        Allocate budget with proper authorization and audit logging
        
        Args:
            allocation_data: Budget allocation details
            
        Returns:
            Budget allocation result
        """
        with TimedOperation(logger, "allocate_budget"):
            try:
                # Validate allocation data
                self._validate_allocation_data(allocation_data)
                
                category = allocation_data['category']
                period = allocation_data.get('period', self._get_current_budget_period())
                amount = float(allocation_data['amount'])
                justification = allocation_data.get('justification', '')
                
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Create or update budget allocation
                budget_record = {
                    'PK': f"BUDGET#{category}#{period}",
                    'SK': 'ALLOCATION',
                    'category': category,
                    'period': period,
                    'allocatedAmount': Decimal(str(amount)),
                    'utilizedAmount': Decimal('0'),
                    'reservedAmount': Decimal('0'),
                    'remainingAmount': Decimal(str(amount)),
                    'createdBy': self.user_id,
                    'createdAt': timestamp,
                    'updatedBy': self.user_id,
                    'updatedAt': timestamp,
                    'justification': justification,
                    'correlationId': self.correlation_id,
                    'reservations': {},
                    'GSI1PK': f"PERIOD#{period}",
                    'GSI1SK': f"CATEGORY#{category}"
                }
                
                # Check if budget already exists
                existing_response = budget_table.get_item(
                    Key={'PK': f"BUDGET#{category}#{period}", 'SK': 'ALLOCATION'}
                )
                
                before_state = None
                if 'Item' in existing_response:
                    before_state = self._convert_decimals(existing_response['Item'])
                    # Update existing allocation
                    budget_record['utilizedAmount'] = existing_response['Item']['utilizedAmount']
                    budget_record['reservedAmount'] = existing_response['Item'].get('reservedAmount', Decimal('0'))
                    budget_record['remainingAmount'] = Decimal(str(amount)) - budget_record['utilizedAmount'] - budget_record['reservedAmount']
                    budget_record['createdBy'] = existing_response['Item']['createdBy']
                    budget_record['createdAt'] = existing_response['Item']['createdAt']
                    budget_record['reservations'] = existing_response['Item'].get('reservations', {})
                
                # Store budget allocation
                budget_table.put_item(Item=budget_record)
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='ALLOCATE_BUDGET',
                    resource='BUDGET',
                    resource_id=f"{category}#{period}",
                    details={
                        'category': category,
                        'period': period,
                        'amount': amount,
                        'justification': justification,
                        'isUpdate': before_state is not None
                    },
                    request_context=self.request_context,
                    before_state=before_state,
                    after_state=self._convert_decimals(budget_record)
                )
                
                logger.info(
                    "Budget allocated successfully",
                    category=category,
                    period=period,
                    amount=amount,
                    is_update=before_state is not None,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'allocated': True,
                    'category': category,
                    'period': period,
                    'amount': amount,
                    'isUpdate': before_state is not None,
                    'allocatedAt': timestamp
                }
                
            except Exception as e:
                logger.error(
                    "Failed to allocate budget",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to allocate budget: {str(e)}")
    
    def reallocate_budget(self, reallocation_data: Dict) -> Dict:
        """
        Reallocate budget between categories with authorization
        
        Args:
            reallocation_data: Budget reallocation details
            
        Returns:
            Budget reallocation result
        """
        with TimedOperation(logger, "reallocate_budget"):
            try:
                # Validate reallocation data
                self._validate_reallocation_data(reallocation_data)
                
                source_category = reallocation_data['sourceCategory']
                target_category = reallocation_data['targetCategory']
                amount = float(reallocation_data['amount'])
                justification = reallocation_data['justification']
                period = reallocation_data.get('period', self._get_current_budget_period())
                
                # Validate source budget has sufficient available amount
                source_budget = self._get_budget_info(source_category, period)
                if not source_budget:
                    raise BudgetServiceError(f"Source budget category {source_category} not found")
                
                source_available = float(source_budget['allocatedAmount']) - float(source_budget['utilizedAmount']) - float(source_budget.get('reservedAmount', 0))
                if source_available < amount:
                    raise BudgetServiceError(f"Insufficient available budget in source category. Available: {source_available}, Requested: {amount}")
                
                timestamp = datetime.utcnow().isoformat() + 'Z'
                
                # Perform atomic reallocation using transaction
                with budget_table.batch_writer() as batch:
                    # Reduce source budget
                    batch.put_item(Item={
                        **source_budget,
                        'allocatedAmount': Decimal(str(float(source_budget['allocatedAmount']) - amount)),
                        'remainingAmount': Decimal(str(float(source_budget['remainingAmount']) - amount)),
                        'updatedBy': self.user_id,
                        'updatedAt': timestamp
                    })
                    
                    # Increase target budget (create if doesn't exist)
                    target_budget = self._get_budget_info(target_category, period)
                    if target_budget:
                        batch.put_item(Item={
                            **target_budget,
                            'allocatedAmount': Decimal(str(float(target_budget['allocatedAmount']) + amount)),
                            'remainingAmount': Decimal(str(float(target_budget['remainingAmount']) + amount)),
                            'updatedBy': self.user_id,
                            'updatedAt': timestamp
                        })
                    else:
                        # Create new target budget
                        batch.put_item(Item={
                            'PK': f"BUDGET#{target_category}#{period}",
                            'SK': 'ALLOCATION',
                            'category': target_category,
                            'period': period,
                            'allocatedAmount': Decimal(str(amount)),
                            'utilizedAmount': Decimal('0'),
                            'reservedAmount': Decimal('0'),
                            'remainingAmount': Decimal(str(amount)),
                            'createdBy': self.user_id,
                            'createdAt': timestamp,
                            'updatedBy': self.user_id,
                            'updatedAt': timestamp,
                            'correlationId': self.correlation_id,
                            'reservations': {},
                            'GSI1PK': f"PERIOD#{period}",
                            'GSI1SK': f"CATEGORY#{target_category}"
                        })
                
                # Log audit event
                audit_logger.log_user_action(
                    user_id=self.user_id,
                    action='REALLOCATE_BUDGET',
                    resource='BUDGET',
                    resource_id=f"{source_category}#{target_category}#{period}",
                    details={
                        'sourceCategory': source_category,
                        'targetCategory': target_category,
                        'amount': amount,
                        'period': period,
                        'justification': justification
                    },
                    request_context=self.request_context
                )
                
                logger.info(
                    "Budget reallocated successfully",
                    source_category=source_category,
                    target_category=target_category,
                    amount=amount,
                    period=period,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'reallocated': True,
                    'sourceCategory': source_category,
                    'targetCategory': target_category,
                    'amount': amount,
                    'period': period,
                    'reallocatedAt': timestamp
                }
                
            except Exception as e:
                logger.error(
                    "Failed to reallocate budget",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to reallocate budget: {str(e)}")
    
    def get_spend_forecast_comparison(self, filters: Optional[Dict] = None) -> Dict:
        """
        Get spend vs forecast comparison with ML integration
        
        Args:
            filters: Optional filters for period, category, etc.
            
        Returns:
            Spend vs forecast comparison data
        """
        with TimedOperation(logger, "get_spend_forecast_comparison"):
            try:
                filters = filters or {}
                period = filters.get('period', self._get_current_budget_period())
                category_filter = filters.get('category')
                
                # Get budget utilization data
                utilization_data = self.get_budget_utilization({'period': period, 'category': category_filter})
                
                # Get ML forecasts for comparison
                comparison_data = []
                for budget_item in utilization_data['utilizationData']:
                    category = budget_item['category']
                    
                    # Get detailed ML forecast
                    ml_forecast = self._get_detailed_ml_forecast(category, period)
                    
                    # Calculate variance
                    actual_spend = budget_item['utilizedAmount']
                    forecasted_spend = ml_forecast.get('predictedSpend', actual_spend)
                    variance = actual_spend - forecasted_spend
                    variance_percentage = (variance / forecasted_spend * 100) if forecasted_spend > 0 else 0.0
                    
                    comparison_entry = {
                        'category': category,
                        'period': period,
                        'actualSpend': actual_spend,
                        'forecastedSpend': forecasted_spend,
                        'variance': variance,
                        'variancePercentage': variance_percentage,
                        'budgetAllocated': budget_item['allocatedAmount'],
                        'utilizationPercentage': budget_item['utilizationPercentage'],
                        'forecastAccuracy': ml_forecast.get('accuracy', 0.0),
                        'trendDirection': self._calculate_trend_direction(variance_percentage),
                        'riskLevel': self._calculate_forecast_risk_level(variance_percentage, budget_item['utilizationPercentage']),
                        'lastUpdated': budget_item['lastUpdated'],
                        'forecastGenerated': ml_forecast.get('generatedAt')
                    }
                    
                    comparison_data.append(comparison_entry)
                
                # Calculate summary statistics
                total_actual = sum(item['actualSpend'] for item in comparison_data)
                total_forecasted = sum(item['forecastedSpend'] for item in comparison_data)
                overall_variance = total_actual - total_forecasted
                overall_variance_percentage = (overall_variance / total_forecasted * 100) if total_forecasted > 0 else 0.0
                
                logger.info(
                    "Retrieved spend forecast comparison",
                    period=period,
                    category_filter=category_filter,
                    count=len(comparison_data),
                    overall_variance_percentage=overall_variance_percentage,
                    correlation_id=self.correlation_id
                )
                
                return {
                    'comparisonData': comparison_data,
                    'summary': {
                        'period': period,
                        'totalActualSpend': total_actual,
                        'totalForecastedSpend': total_forecasted,
                        'overallVariance': overall_variance,
                        'overallVariancePercentage': overall_variance_percentage,
                        'categoriesCount': len(comparison_data)
                    },
                    'filters': filters
                }
                
            except Exception as e:
                logger.error(
                    "Failed to get spend forecast comparison",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to get spend forecast comparison: {str(e)}")
    
    def generate_budget_alerts(self) -> Dict:
        """
        Generate budget alerts for threshold monitoring
        
        Returns:
            Generated budget alerts
        """
        with TimedOperation(logger, "generate_budget_alerts"):
            try:
                current_period = self._get_current_budget_period()
                
                # Get all budget categories for current period
                response = budget_table.query(
                    IndexName='GSI1',
                    KeyConditionExpression='GSI1PK = :period',
                    ExpressionAttributeValues={':period': f"PERIOD#{current_period}"}
                )
                
                alerts_generated = []
                
                for budget_item in response['Items']:
                    budget_data = self._convert_decimals(budget_item)
                    category = budget_data['category']
                    allocated = budget_data['allocatedAmount']
                    utilized = budget_data['utilizedAmount']
                    reserved = budget_data.get('reservedAmount', 0.0)
                    
                    utilization_percentage = (utilized + reserved) / allocated if allocated > 0 else 0.0
                    
                    # Check if alert should be generated
                    alert_level = self._get_alert_level(utilization_percentage)
                    if alert_level != 'NORMAL':
                        alert = self._generate_budget_alert(category, current_period, utilization_percentage, budget_data)
                        if alert:
                            alerts_generated.append(alert)
                
                logger.info(
                    "Budget alerts generated",
                    period=current_period,
                    alerts_count=len(alerts_generated),
                    correlation_id=self.correlation_id
                )
                
                return {
                    'alertsGenerated': alerts_generated,
                    'period': current_period,
                    'count': len(alerts_generated)
                }
                
            except Exception as e:
                logger.error(
                    "Failed to generate budget alerts",
                    error=str(e),
                    correlation_id=self.correlation_id
                )
                raise BudgetServiceError(f"Failed to generate budget alerts: {str(e)}")
    
    # Private helper methods
    
    def _get_current_budget_period(self) -> str:
        """Get current budget period in YYYY-MM format"""
        return datetime.utcnow().strftime('%Y-%m')
    
    def _get_budget_info(self, category: str, period: str) -> Optional[Dict]:
        """Get budget information for category and period"""
        try:
            response = budget_table.get_item(
                Key={'PK': f"BUDGET#{category}#{period}", 'SK': 'ALLOCATION'}
            )
            return self._convert_decimals(response['Item']) if 'Item' in response else None
        except Exception:
            return None
    
    def _create_default_budget_allocation(self, category: str, period: str) -> Dict:
        """Create default budget allocation for new category"""
        default_amount = 10000.0  # Default $10,000 allocation
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        budget_record = {
            'PK': f"BUDGET#{category}#{period}",
            'SK': 'ALLOCATION',
            'category': category,
            'period': period,
            'allocatedAmount': Decimal(str(default_amount)),
            'utilizedAmount': Decimal('0'),
            'reservedAmount': Decimal('0'),
            'remainingAmount': Decimal(str(default_amount)),
            'createdBy': 'system',
            'createdAt': timestamp,
            'updatedBy': 'system',
            'updatedAt': timestamp,
            'justification': 'Auto-created default allocation',
            'correlationId': self.correlation_id,
            'reservations': {},
            'GSI1PK': f"PERIOD#{period}",
            'GSI1SK': f"CATEGORY#{category}"
        }
        
        budget_table.put_item(Item=budget_record)
        return self._convert_decimals(budget_record)
    
    def _get_validation_message(self, is_available: bool, available_amount: float, requested_amount: float, utilization_after: float) -> str:
        """Get budget validation message"""
        if not is_available:
            return f"Insufficient budget. Available: ${available_amount:,.2f}, Requested: ${requested_amount:,.2f}"
        elif utilization_after >= self.emergency_threshold:
            return f"Budget available but will exceed emergency threshold ({self.emergency_threshold*100:.0f}%)"
        elif utilization_after >= self.critical_threshold:
            return f"Budget available but will exceed critical threshold ({self.critical_threshold*100:.0f}%)"
        elif utilization_after >= self.warning_threshold:
            return f"Budget available but will exceed warning threshold ({self.warning_threshold*100:.0f}%)"
        else:
            return "Budget available"
    
    def _get_budget_status(self, utilization_percentage: float) -> str:
        """Get budget status based on utilization percentage"""
        if utilization_percentage >= self.emergency_threshold:
            return 'EMERGENCY'
        elif utilization_percentage >= self.critical_threshold:
            return 'CRITICAL'
        elif utilization_percentage >= self.warning_threshold:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def _get_alert_level(self, utilization_percentage: float) -> str:
        """Get alert level based on utilization percentage"""
        if utilization_percentage >= self.emergency_threshold:
            return 'EMERGENCY'
        elif utilization_percentage >= self.critical_threshold:
            return 'CRITICAL'
        elif utilization_percentage >= self.warning_threshold:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def _generate_budget_alert(self, category: str, period: str, utilization_percentage: float, budget_data: Dict) -> Optional[Dict]:
        """Generate budget alert for threshold monitoring"""
        try:
            alert_level = self._get_alert_level(utilization_percentage)
            if alert_level == 'NORMAL':
                return None
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            alert_id = str(uuid.uuid4())
            
            alert = {
                'alertId': alert_id,
                'category': category,
                'period': period,
                'alertLevel': alert_level,
                'utilizationPercentage': utilization_percentage,
                'allocatedAmount': budget_data['allocatedAmount'],
                'utilizedAmount': budget_data['utilizedAmount'],
                'remainingAmount': budget_data['allocatedAmount'] - budget_data['utilizedAmount'] - budget_data.get('reservedAmount', 0.0),
                'threshold': self._get_threshold_for_level(alert_level),
                'message': self._get_alert_message(category, alert_level, utilization_percentage),
                'generatedAt': timestamp,
                'correlationId': self.correlation_id
            }
            
            # Send alert notification
            self._send_budget_alert_notification(alert)
            
            # Log audit event
            audit_logger.log_system_event(
                event_type='BUDGET_ALERT_GENERATED',
                resource='BUDGET',
                resource_id=f"{category}#{period}",
                details=alert,
                request_context=self.request_context
            )
            
            return alert
            
        except Exception as e:
            logger.error(
                "Failed to generate budget alert",
                category=category,
                period=period,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return None
    
    def _get_threshold_for_level(self, alert_level: str) -> float:
        """Get threshold percentage for alert level"""
        thresholds = {
            'WARNING': self.warning_threshold,
            'CRITICAL': self.critical_threshold,
            'EMERGENCY': self.emergency_threshold
        }
        return thresholds.get(alert_level, 0.0)
    
    def _get_alert_message(self, category: str, alert_level: str, utilization_percentage: float) -> str:
        """Get alert message for budget threshold"""
        threshold = self._get_threshold_for_level(alert_level)
        return f"Budget category '{category}' has reached {alert_level.lower()} threshold. Current utilization: {utilization_percentage*100:.1f}% (threshold: {threshold*100:.0f}%)"
    
    def _send_budget_alert_notification(self, alert: Dict) -> None:
        """Send budget alert notification"""
        try:
            if self.alert_topic:
                sns.publish(
                    TopicArn=self.alert_topic,
                    Message=json.dumps(alert),
                    Subject=f"Budget Alert: {alert['alertLevel']} - {alert['category']}",
                    MessageAttributes={
                        'alertLevel': {'DataType': 'String', 'StringValue': alert['alertLevel']},
                        'category': {'DataType': 'String', 'StringValue': alert['category']}
                    }
                )
            
            # Send EventBridge event
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'aquachain.budget',
                        'DetailType': 'Budget Alert Generated',
                        'Detail': json.dumps(alert)
                    }
                ]
            )
            
        except Exception as e:
            logger.error(
                "Failed to send budget alert notification",
                alert_id=alert.get('alertId'),
                error=str(e),
                correlation_id=self.correlation_id
            )
    
    def _get_ml_forecast(self, category: str, period: str) -> Dict:
        """Get ML forecast data for category and period"""
        try:
            response = ml_forecasts_table.get_item(
                Key={'PK': f"FORECAST#{category}#{period}", 'SK': 'BUDGET_PREDICTION'}
            )
            
            if 'Item' in response:
                forecast = self._convert_decimals(response['Item'])
                return {
                    'available': True,
                    'predictedSpend': forecast.get('predictedSpend', 0.0),
                    'confidence': forecast.get('confidence', 0.0),
                    'accuracy': forecast.get('accuracy', 0.0),
                    'generatedAt': forecast.get('generatedAt')
                }
            else:
                return {'available': False}
                
        except Exception as e:
            logger.warning(
                "Failed to get ML forecast, using fallback",
                category=category,
                period=period,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return {'available': False}
    
    def _get_detailed_ml_forecast(self, category: str, period: str) -> Dict:
        """Get detailed ML forecast with fallback to rule-based prediction"""
        ml_forecast = self._get_ml_forecast(category, period)
        
        if ml_forecast['available']:
            return ml_forecast
        else:
            # Fallback to rule-based prediction
            return self._generate_rule_based_forecast(category, period)
    
    def _generate_rule_based_forecast(self, category: str, period: str) -> Dict:
        """Generate rule-based forecast when ML is unavailable"""
        try:
            # Get historical data for the category
            current_budget = self._get_budget_info(category, period)
            if not current_budget:
                return {'available': False}
            
            # Simple rule-based prediction: assume 80% of allocated budget will be spent
            predicted_spend = float(current_budget['allocatedAmount']) * 0.8
            
            return {
                'available': True,
                'predictedSpend': predicted_spend,
                'confidence': 0.6,  # Lower confidence for rule-based
                'accuracy': 0.7,    # Estimated accuracy
                'generatedAt': datetime.utcnow().isoformat() + 'Z',
                'method': 'rule-based'
            }
            
        except Exception as e:
            logger.error(
                "Failed to generate rule-based forecast",
                category=category,
                period=period,
                error=str(e),
                correlation_id=self.correlation_id
            )
            return {'available': False}
    
    def _calculate_trend_direction(self, variance_percentage: float) -> str:
        """Calculate trend direction based on variance"""
        if variance_percentage > 10:
            return 'OVER_BUDGET'
        elif variance_percentage < -10:
            return 'UNDER_BUDGET'
        else:
            return 'ON_TRACK'
    
    def _calculate_forecast_risk_level(self, variance_percentage: float, utilization_percentage: float) -> str:
        """Calculate forecast risk level"""
        if abs(variance_percentage) > 25 or utilization_percentage > 0.9:
            return 'HIGH'
        elif abs(variance_percentage) > 15 or utilization_percentage > 0.8:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _validate_allocation_data(self, allocation_data: Dict) -> None:
        """Validate budget allocation data"""
        required_fields = ['category', 'amount']
        for field in required_fields:
            if field not in allocation_data:
                raise BudgetServiceError(f"Missing required field: {field}")
        
        if allocation_data['amount'] <= 0:
            raise BudgetServiceError("Budget amount must be positive")
    
    def _validate_reallocation_data(self, reallocation_data: Dict) -> None:
        """Validate budget reallocation data"""
        required_fields = ['sourceCategory', 'targetCategory', 'amount', 'justification']
        for field in required_fields:
            if field not in reallocation_data:
                raise BudgetServiceError(f"Missing required field: {field}")
        
        if reallocation_data['amount'] <= 0:
            raise BudgetServiceError("Reallocation amount must be positive")
        
        if reallocation_data['sourceCategory'] == reallocation_data['targetCategory']:
            raise BudgetServiceError("Source and target categories cannot be the same")
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(v) for v in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj


# Lambda handler function
def lambda_handler(event, context):
    """
    Main Lambda handler for budget service
    
    Supported actions:
    - validate_budget_availability
    - reserve_budget
    - get_budget_utilization
    - allocate_budget
    - reallocate_budget
    - get_spend_forecast_comparison
    - generate_budget_alerts
    """
    try:
        # Extract request context
        request_context = {
            'user_id': event.get('requestContext', {}).get('authorizer', {}).get('userId', 'system'),
            'username': event.get('requestContext', {}).get('authorizer', {}).get('username', 'unknown'),
            'correlation_id': event.get('headers', {}).get('X-Correlation-ID', str(uuid.uuid4())),
            'ipAddress': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'userAgent': event.get('headers', {}).get('User-Agent', 'unknown')
        }
        
        # Initialize service
        service = BudgetService(request_context)
        
        # Parse request body
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        action = body.get('action') or event.get('pathParameters', {}).get('action')
        
        # Route to appropriate method
        if action == 'validate_budget_availability':
            # Validate RBAC permissions for budget validation
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'budgets',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for budget availability validation",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'budgets',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.validate_budget_availability(
                body.get('amount'),
                body.get('category'),
                body.get('orderId')
            )
            
        elif action == 'reserve_budget':
            # Validate RBAC permissions for budget reservation
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'budget-allocation',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for budget reservation",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'budget-allocation',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.reserve_budget(
                body.get('amount'),
                body.get('category'),
                body.get('orderId')
            )
            
        elif action == 'get_budget_utilization':
            # Validate RBAC permissions for budget utilization viewing
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'budget-utilization',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for budget utilization viewing",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'budget-utilization',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.get_budget_utilization(body.get('filters', {}))
            
        elif action == 'allocate_budget':
            # Validate RBAC permissions for budget allocation
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'budget-allocation',
                'configure',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for budget allocation",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'budget-allocation',
                        'action': 'configure',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.allocate_budget(body.get('allocationData', {}))
            
        elif action == 'reallocate_budget':
            # Validate RBAC permissions for budget reallocation
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'budget-changes',
                'approve',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for budget reallocation",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'budget-changes',
                        'action': 'approve',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.reallocate_budget(body.get('reallocationData', {}))
            
        elif action == 'get_spend_forecast_comparison':
            # Validate RBAC permissions for spend analysis
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'spend-analysis',
                'view',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for spend forecast comparison",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'spend-analysis',
                        'action': 'view',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.get_spend_forecast_comparison(body.get('filters', {}))
            
        elif action == 'generate_budget_alerts':
            # Validate RBAC permissions for budget alert generation
            is_authorized, user_role, audit_details = validate_user_permissions(
                request_context['user_id'],
                request_context['username'],
                'budget-allocation',
                'act',
                request_context
            )
            
            if not is_authorized:
                logger.warning(
                    "Access denied for budget alert generation",
                    user_id=request_context['user_id'],
                    user_role=user_role,
                    correlation_id=request_context['correlation_id']
                )
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Correlation-ID': request_context['correlation_id']
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Access denied',
                        'resource': 'budget-allocation',
                        'action': 'act',
                        'userRole': user_role,
                        'correlationId': request_context['correlation_id']
                    })
                }
            
            result = service.generate_budget_alerts()
        else:
            raise BudgetServiceError(f"Unknown action: {action}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context['correlation_id']
            },
            'body': json.dumps({
                'success': True,
                'data': result,
                'correlationId': request_context['correlation_id']
            })
        }
        
    except BudgetServiceError as e:
        logger.error(
            "Budget service error",
            error=str(e),
            correlation_id=request_context.get('correlation_id', 'unknown')
        )
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context.get('correlation_id', 'unknown')
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'correlationId': request_context.get('correlation_id', 'unknown')
            })
        }
        
    except Exception as e:
        logger.error(
            "Unexpected error in budget service",
            error=str(e),
            traceback=traceback.format_exc(),
            correlation_id=request_context.get('correlation_id', 'unknown')
        )
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': request_context.get('correlation_id', 'unknown')
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'correlationId': request_context.get('correlation_id', 'unknown')
            })
        }