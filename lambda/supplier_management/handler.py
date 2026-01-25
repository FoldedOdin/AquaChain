"""
AquaChain Supplier Management Service - Dashboard Overhaul
Enhanced supplier management with comprehensive audit logging, performance scoring,
financial risk assessment, and contract management for role-based dashboards.

Requirements: 1.3, 2.7
- Supplier profiles, contracts, performance scoring, and risk indicators
- Supplier financial risk overview with automated risk scoring
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import uuid
import logging
import requests
from botocore.exceptions import ClientError
import hashlib
import statistics

# Import shared utilities for dashboard overhaul
import sys
sys.path.append('/opt/python')
from audit_logger import audit_logger
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, "supplier-management-service")

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
secrets_manager = boto3.client('secretsmanager')
kms = boto3.client('kms')

# Table references for dashboard overhaul
suppliers_table = dynamodb.Table(os.environ.get('SUPPLIERS_TABLE', 'AquaChain-Suppliers'))
contracts_table = dynamodb.Table(os.environ.get('CONTRACTS_TABLE', 'AquaChain-Supplier-Contracts'))
purchase_orders_table = dynamodb.Table(os.environ.get('PURCHASE_ORDERS_TABLE', 'AquaChain-Purchase-Orders'))
inventory_table = dynamodb.Table(os.environ.get('INVENTORY_TABLE', 'AquaChain-Inventory-Items'))
financial_data_table = dynamodb.Table(os.environ.get('FINANCIAL_DATA_TABLE', 'AquaChain-Financial-Data'))


class SupplierRiskAssessment:
    """
    Financial and operational risk assessment for suppliers
    Implements automated risk scoring for Requirements 1.3 and 2.7
    """
    
    def __init__(self):
        self.risk_weights = {
            'financial_stability': 0.30,
            'delivery_performance': 0.25,
            'quality_score': 0.20,
            'contract_compliance': 0.15,
            'market_reputation': 0.10
        }
    
    def calculate_financial_risk_score(self, supplier_id: str, financial_data: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive financial risk score
        
        Args:
            supplier_id: Supplier identifier
            financial_data: Financial metrics and data
            
        Returns:
            Risk assessment with score and indicators
        """
        try:
            risk_indicators = {}
            
            # Financial stability indicators
            credit_rating = financial_data.get('credit_rating', 'C')
            debt_to_equity = float(financial_data.get('debt_to_equity_ratio', 1.0))
            cash_flow = float(financial_data.get('cash_flow_trend', 0))
            
            # Calculate financial stability score (0-100)
            credit_scores = {'AAA': 100, 'AA': 90, 'A': 80, 'BBB': 70, 'BB': 60, 'B': 50, 'C': 30}
            credit_score = credit_scores.get(credit_rating, 30)
            
            debt_score = max(0, 100 - (debt_to_equity * 20))  # Lower debt = higher score
            cash_flow_score = min(100, max(0, 50 + (cash_flow * 10)))  # Positive trend = higher score
            
            financial_stability = (credit_score * 0.5 + debt_score * 0.3 + cash_flow_score * 0.2)
            risk_indicators['financial_stability'] = {
                'score': round(financial_stability, 2),
                'credit_rating': credit_rating,
                'debt_to_equity_ratio': debt_to_equity,
                'cash_flow_trend': cash_flow
            }
            
            # Get performance metrics
            performance_metrics = self._get_supplier_performance_metrics(supplier_id)
            
            # Delivery performance score
            on_time_rate = performance_metrics.get('on_time_delivery_rate', 0)
            delivery_score = min(100, on_time_rate)
            risk_indicators['delivery_performance'] = {
                'score': delivery_score,
                'on_time_rate': on_time_rate
            }
            
            # Quality score
            quality_score = performance_metrics.get('quality_score', 0)
            risk_indicators['quality_score'] = {
                'score': quality_score,
                'defect_rate': performance_metrics.get('defect_rate', 0)
            }
            
            # Contract compliance score
            compliance_score = self._calculate_contract_compliance_score(supplier_id)
            risk_indicators['contract_compliance'] = {
                'score': compliance_score,
                'violations': self._get_contract_violations(supplier_id)
            }
            
            # Market reputation score (simplified)
            market_score = financial_data.get('market_reputation_score', 75)
            risk_indicators['market_reputation'] = {
                'score': market_score,
                'industry_rating': financial_data.get('industry_rating', 'Average')
            }
            
            # Calculate overall risk score
            overall_score = sum(
                risk_indicators[category]['score'] * self.risk_weights[category]
                for category in self.risk_weights.keys()
            )
            
            # Determine risk level
            if overall_score >= 80:
                risk_level = 'LOW'
            elif overall_score >= 60:
                risk_level = 'MEDIUM'
            elif overall_score >= 40:
                risk_level = 'HIGH'
            else:
                risk_level = 'CRITICAL'
            
            return {
                'supplier_id': supplier_id,
                'overall_risk_score': round(overall_score, 2),
                'risk_level': risk_level,
                'risk_indicators': risk_indicators,
                'assessment_date': datetime.utcnow().isoformat(),
                'recommendations': self._generate_risk_recommendations(risk_level, risk_indicators)
            }
            
        except Exception as e:
            logger.error(f"Error calculating financial risk score: {str(e)}", supplier_id=supplier_id)
            return {
                'supplier_id': supplier_id,
                'overall_risk_score': 50,
                'risk_level': 'UNKNOWN',
                'error': str(e)
            }
    
    def _get_supplier_performance_metrics(self, supplier_id: str) -> Dict:
        """Get supplier performance metrics for risk assessment"""
        try:
            # Get recent orders for performance calculation
            response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id},
                ScanIndexForward=False,
                Limit=50  # Last 50 orders for assessment
            )
            
            orders = response.get('Items', [])
            if not orders:
                return {'on_time_delivery_rate': 0, 'quality_score': 0, 'defect_rate': 0, 'total_orders': 0, 'delivered_orders': 0}
            
            # Calculate metrics
            delivered_orders = [o for o in orders if o.get('status') == 'delivered']
            on_time_orders = [o for o in delivered_orders if self._is_delivery_on_time(o)]
            quality_issues = sum(1 for o in orders if o.get('quality_issues', 0) > 0)
            
            on_time_rate = (len(on_time_orders) / len(delivered_orders)) * 100 if delivered_orders else 0
            defect_rate = (quality_issues / len(orders)) * 100 if orders else 0
            quality_score = max(0, 100 - defect_rate)
            
            return {
                'on_time_delivery_rate': round(on_time_rate, 2),
                'quality_score': round(quality_score, 2),
                'defect_rate': round(defect_rate, 2),
                'total_orders': len(orders),
                'delivered_orders': len(delivered_orders)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}", supplier_id=supplier_id)
            return {'on_time_delivery_rate': 0, 'quality_score': 0, 'defect_rate': 0}
    
    def _calculate_contract_compliance_score(self, supplier_id: str) -> float:
        """Calculate contract compliance score"""
        try:
            # Get active contracts
            response = contracts_table.query(
                KeyConditionExpression='supplier_id = :sid',
                FilterExpression='contract_status = :status',
                ExpressionAttributeValues={
                    ':sid': supplier_id,
                    ':status': 'active'
                }
            )
            
            contracts = response.get('Items', [])
            if not contracts:
                return 75  # Default score if no contracts
            
            total_score = 0
            for contract in contracts:
                # Check compliance indicators
                violations = contract.get('violations', [])
                penalty_amount = float(contract.get('penalty_amount', 0))
                
                contract_score = 100
                contract_score -= len(violations) * 10  # -10 per violation
                contract_score -= min(penalty_amount / 1000, 20)  # Penalty impact
                
                total_score += max(0, contract_score)
            
            return total_score / len(contracts) if contracts else 75
            
        except Exception as e:
            logger.error(f"Error calculating contract compliance: {str(e)}", supplier_id=supplier_id)
            return 75
    
    def _get_contract_violations(self, supplier_id: str) -> List[Dict]:
        """Get recent contract violations"""
        try:
            response = contracts_table.query(
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            violations = []
            for contract in response.get('Items', []):
                contract_violations = contract.get('violations', [])
                for violation in contract_violations:
                    violations.append({
                        'contract_id': contract['contract_id'],
                        'violation_type': violation.get('type'),
                        'date': violation.get('date'),
                        'severity': violation.get('severity', 'medium')
                    })
            
            # Return recent violations (last 6 months)
            six_months_ago = (datetime.utcnow() - timedelta(days=180)).isoformat()
            recent_violations = [
                v for v in violations 
                if v.get('date', '') >= six_months_ago
            ]
            
            return recent_violations[:10]  # Limit to 10 most recent
            
        except Exception as e:
            logger.error(f"Error getting contract violations: {str(e)}", supplier_id=supplier_id)
            return []
    
    def _is_delivery_on_time(self, order: Dict) -> bool:
        """Check if delivery was on time"""
        try:
            if 'expected_delivery' not in order or 'actual_delivery_date' not in order:
                return False
                
            expected = datetime.fromisoformat(order['expected_delivery'].replace('Z', '+00:00'))
            actual = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
            
            return actual <= expected
            
        except Exception:
            return False
    
    def _generate_risk_recommendations(self, risk_level: str, risk_indicators: Dict) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if risk_level == 'CRITICAL':
            recommendations.append("URGENT: Consider immediate supplier review and potential replacement")
            recommendations.append("Implement enhanced monitoring and frequent performance reviews")
        elif risk_level == 'HIGH':
            recommendations.append("Schedule supplier performance review within 30 days")
            recommendations.append("Consider backup supplier identification")
        
        # Specific recommendations based on indicators
        financial_score = risk_indicators.get('financial_stability', {}).get('score', 0)
        if financial_score < 60:
            recommendations.append("Monitor supplier financial health closely")
            recommendations.append("Consider requiring financial guarantees for large orders")
        
        delivery_score = risk_indicators.get('delivery_performance', {}).get('score', 0)
        if delivery_score < 80:
            recommendations.append("Discuss delivery performance improvement plan")
        
        quality_score = risk_indicators.get('quality_score', {}).get('score', 0)
        if quality_score < 85:
            recommendations.append("Implement enhanced quality control measures")
        
        return recommendations


class ContractManager:
    """
    Contract management for supplier relationships
    Supports Requirements 1.3 - contract management functionality
    """
    
    def __init__(self):
        self.audit_logger = audit_logger
    
    def create_contract(self, contract_data: Dict, user_id: str, request_context: Dict) -> Dict:
        """Create new supplier contract"""
        try:
            # Generate contract ID
            contract_id = f"CONTRACT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            
            # Set default values
            now = datetime.utcnow().isoformat()
            contract_data.update({
                'contract_id': contract_id,
                'created_at': now,
                'updated_at': now,
                'created_by': user_id,
                'contract_status': 'draft',
                'version': 1,
                'violations': [],
                'penalty_amount': Decimal('0')
            })
            
            # Validate required fields
            required_fields = ['supplier_id', 'contract_type', 'start_date', 'end_date', 'terms']
            for field in required_fields:
                if field not in contract_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Create contract
            contracts_table.put_item(Item=contract_data)
            
            # Audit log
            self.audit_logger.log_action(
                action_type='CREATE',
                user_id=user_id,
                resource_type='CONTRACT',
                resource_id=contract_id,
                details={
                    'supplier_id': contract_data['supplier_id'],
                    'contract_type': contract_data['contract_type'],
                    'contract_value': contract_data.get('contract_value', 0)
                },
                request_context=request_context
            )
            
            logger.info(
                "Contract created successfully",
                contract_id=contract_id,
                supplier_id=contract_data['supplier_id'],
                user_id=user_id
            )
            
            return {
                'statusCode': 201,
                'body': {
                    'message': 'Contract created successfully',
                    'contract': contract_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating contract: {str(e)}", user_id=user_id)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create contract'}
            }
    
    def get_supplier_contracts(self, supplier_id: str, user_id: str, request_context: Dict) -> Dict:
        """Get all contracts for a supplier"""
        try:
            response = contracts_table.query(
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id},
                ScanIndexForward=False  # Most recent first
            )
            
            contracts = response.get('Items', [])
            
            # Audit log
            self.audit_logger.log_data_access(
                user_id=user_id,
                resource_type='CONTRACT',
                resource_id=f"supplier-{supplier_id}",
                operation='LIST',
                request_context=request_context,
                details={'contracts_count': len(contracts)}
            )
            
            return {
                'statusCode': 200,
                'body': {
                    'contracts': contracts,
                    'count': len(contracts),
                    'active_contracts': len([c for c in contracts if c.get('contract_status') == 'active'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting supplier contracts: {str(e)}", supplier_id=supplier_id)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve contracts'}
            }
    
    def update_contract_status(self, contract_id: str, status: str, user_id: str, request_context: Dict) -> Dict:
        """Update contract status"""
        try:
            # First, find the contract by scanning (since we only have contract_id)
            response = contracts_table.scan(
                FilterExpression='contract_id = :cid',
                ExpressionAttributeValues={':cid': contract_id}
            )
            
            contracts = response.get('Items', [])
            if not contracts:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Contract not found'}
                }
            
            current_contract = contracts[0]
            supplier_id = current_contract['supplier_id']
            previous_status = current_contract.get('contract_status')
            
            # Update contract using composite key
            updated_contract = contracts_table.update_item(
                Key={'supplier_id': supplier_id, 'contract_id': contract_id},
                UpdateExpression='SET contract_status = :status, updated_at = :now, updated_by = :user',
                ExpressionAttributeValues={
                    ':status': status,
                    ':now': datetime.utcnow().isoformat(),
                    ':user': user_id
                },
                ReturnValues='ALL_NEW'
            )
            
            # Audit log
            self.audit_logger.log_data_modification(
                user_id=user_id,
                resource_type='CONTRACT',
                resource_id=contract_id,
                modification_type='UPDATE',
                previous_values={'contract_status': previous_status},
                new_values={'contract_status': status},
                request_context=request_context
            )
            
            logger.info(
                "Contract status updated",
                contract_id=contract_id,
                previous_status=previous_status,
                new_status=status,
                user_id=user_id
            )
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Contract status updated successfully',
                    'contract': updated_contract['Attributes']
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating contract status: {str(e)}", contract_id=contract_id)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update contract status'}
            }

class SupplierManager:
    """
    Enhanced supplier management operations for dashboard overhaul
    Implements Requirements 1.3 and 2.7 with comprehensive audit logging,
    performance scoring, and financial risk assessment
    """
    
    def __init__(self):
        self.sns_topic = os.environ.get('SUPPLIER_ALERTS_TOPIC')
        self.audit_logger = audit_logger
        self.risk_assessment = SupplierRiskAssessment()
        self.contract_manager = ContractManager()
        
    def get_suppliers(self, filters: Optional[Dict] = None, user_id: str = None, request_context: Dict = None) -> Dict:
        """Get suppliers with optional filtering and enhanced risk data"""
        try:
            logger.start_operation("get_suppliers")
            
            if filters:
                if 'supplier_type' in filters:
                    response = suppliers_table.query(
                        IndexName='TypeIndex',
                        KeyConditionExpression='supplier_type = :type',
                        ExpressionAttributeValues={':type': filters['supplier_type']},
                        ScanIndexForward=False  # Sort by performance score descending
                    )
                elif 'status' in filters:
                    response = suppliers_table.query(
                        IndexName='StatusIndex',
                        KeyConditionExpression='status = :status',
                        ExpressionAttributeValues={':status': filters['status']}
                    )
                elif 'risk_level' in filters:
                    # Filter by risk level
                    response = suppliers_table.scan(
                        FilterExpression='risk_level = :risk',
                        ExpressionAttributeValues={':risk': filters['risk_level']}
                    )
                else:
                    response = suppliers_table.scan()
            else:
                response = suppliers_table.scan()
                
            suppliers = response.get('Items', [])
            
            # Enrich with performance metrics and risk assessment
            for supplier in suppliers:
                supplier['performance_metrics'] = self._calculate_performance_metrics(supplier['supplier_id'])
                
                # Get or calculate risk assessment
                risk_data = self._get_cached_risk_assessment(supplier['supplier_id'])
                if not risk_data:
                    financial_data = self._get_supplier_financial_data(supplier['supplier_id'])
                    risk_data = self.risk_assessment.calculate_financial_risk_score(
                        supplier['supplier_id'], 
                        financial_data
                    )
                    self._cache_risk_assessment(supplier['supplier_id'], risk_data)
                
                supplier['risk_assessment'] = risk_data
                
                # Get contract summary
                supplier['contract_summary'] = self._get_contract_summary(supplier['supplier_id'])
            
            # Audit log
            if user_id and request_context:
                self.audit_logger.log_data_access(
                    user_id=user_id,
                    resource_type='SUPPLIER',
                    resource_id='all',
                    operation='LIST',
                    request_context=request_context,
                    details={
                        'filters': filters,
                        'suppliers_count': len(suppliers)
                    }
                )
            
            logger.end_operation("get_suppliers", success=True, suppliers_count=len(suppliers))
            
            return {
                'statusCode': 200,
                'body': {
                    'suppliers': suppliers,
                    'count': len(suppliers),
                    'active_count': len([s for s in suppliers if s.get('status') == 'active']),
                    'high_risk_count': len([s for s in suppliers if s.get('risk_assessment', {}).get('risk_level') == 'HIGH']),
                    'top_performers': [s for s in suppliers if s.get('performance_metrics', {}).get('overall_score', 0) >= 90]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting suppliers: {str(e)}", user_id=user_id)
            logger.end_operation("get_suppliers", success=False)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve suppliers'}
            }
    
    def create_supplier(self, supplier_data: Dict, user_id: str, request_context: Dict) -> Dict:
        """Create new supplier with enhanced audit logging"""
        try:
            logger.start_operation("create_supplier")
            
            # Generate supplier ID if not provided
            if 'supplier_id' not in supplier_data:
                supplier_data['supplier_id'] = f"SUP-{uuid.uuid4().hex[:8].upper()}"
            
            # Set default values
            now = datetime.utcnow().isoformat()
            supplier_data.update({
                'created_at': now,
                'updated_at': now,
                'created_by': user_id,
                'status': 'active',
                'performance_score': Decimal('75'),  # Default starting score
                'risk_level': 'MEDIUM',  # Default risk level
                'total_orders': 0,
                'on_time_deliveries': 0,
                'quality_issues': 0,
                'last_risk_assessment': now
            })
            
            # Validate required fields
            required_fields = ['supplier_id', 'name', 'supplier_type', 'contact_email']
            for field in required_fields:
                if field not in supplier_data:
                    return {
                        'statusCode': 400,
                        'body': {'error': f'Missing required field: {field}'}
                    }
            
            # Create the supplier
            suppliers_table.put_item(Item=supplier_data)
            
            # Audit log
            self.audit_logger.log_action(
                action_type='CREATE',
                user_id=user_id,
                resource_type='SUPPLIER',
                resource_id=supplier_data['supplier_id'],
                details={
                    'supplier_name': supplier_data['name'],
                    'supplier_type': supplier_data['supplier_type'],
                    'contact_email': supplier_data['contact_email']
                },
                request_context=request_context
            )
            
            logger.end_operation("create_supplier", success=True, supplier_id=supplier_data['supplier_id'])
            
            return {
                'statusCode': 201,
                'body': {
                    'message': 'Supplier created successfully',
                    'supplier': supplier_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating supplier: {str(e)}", user_id=user_id)
            logger.end_operation("create_supplier", success=False)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to create supplier'}
            }
    
    def get_supplier_performance(self, supplier_id: str, user_id: str, request_context: Dict) -> Dict:
        """Get comprehensive supplier performance with risk assessment"""
        try:
            logger.start_operation("get_supplier_performance")
            
            # Get supplier info
            supplier_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in supplier_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Supplier not found'}
                }
            
            supplier = supplier_response['Item']
            
            # Get comprehensive performance metrics
            performance_metrics = self._calculate_comprehensive_performance_metrics(supplier_id)
            
            # Get financial risk assessment
            financial_data = self._get_supplier_financial_data(supplier_id)
            risk_assessment = self.risk_assessment.calculate_financial_risk_score(supplier_id, financial_data)
            
            # Cache risk assessment
            self._cache_risk_assessment(supplier_id, risk_assessment)
            
            # Get contract information
            contracts_response = self.contract_manager.get_supplier_contracts(
                supplier_id, user_id, request_context
            )
            contracts = contracts_response.get('body', {}).get('contracts', [])
            
            # Get recent orders with detailed analysis
            recent_orders_response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id},
                ScanIndexForward=False,
                Limit=20
            )
            
            recent_orders = recent_orders_response.get('Items', [])
            
            # Audit log
            self.audit_logger.log_data_access(
                user_id=user_id,
                resource_type='SUPPLIER',
                resource_id=supplier_id,
                operation='GET_PERFORMANCE',
                request_context=request_context,
                details={
                    'performance_score': performance_metrics.get('overall_score', 0),
                    'risk_level': risk_assessment.get('risk_level', 'UNKNOWN')
                }
            )
            
            logger.end_operation("get_supplier_performance", success=True, supplier_id=supplier_id)
            
            return {
                'statusCode': 200,
                'body': {
                    'supplier': supplier,
                    'performance_metrics': performance_metrics,
                    'risk_assessment': risk_assessment,
                    'contracts': contracts,
                    'recent_orders': recent_orders,
                    'recommendations': self._generate_comprehensive_recommendations(
                        supplier, performance_metrics, risk_assessment
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting supplier performance: {str(e)}", supplier_id=supplier_id)
            logger.end_operation("get_supplier_performance", success=False)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve supplier performance'}
            }
    
    def update_supplier_financial_data(self, supplier_id: str, financial_data: Dict, user_id: str, request_context: Dict) -> Dict:
        """Update supplier financial data and recalculate risk assessment"""
        try:
            logger.start_operation("update_financial_data")
            
            # Validate supplier exists
            supplier_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            if 'Item' not in supplier_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Supplier not found'}
                }
            
            # Prepare financial data record
            financial_record = {
                'supplier_id': supplier_id,
                'data_type': 'financial_metrics',
                'timestamp': datetime.utcnow().isoformat(),
                'updated_by': user_id,
                **financial_data
            }
            
            # Store financial data
            financial_data_table.put_item(Item=financial_record)
            
            # Recalculate risk assessment
            risk_assessment = self.risk_assessment.calculate_financial_risk_score(supplier_id, financial_data)
            
            # Update supplier with new risk level
            suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression='SET risk_level = :risk, last_risk_assessment = :date, updated_at = :now',
                ExpressionAttributeValues={
                    ':risk': risk_assessment['risk_level'],
                    ':date': datetime.utcnow().isoformat(),
                    ':now': datetime.utcnow().isoformat()
                }
            )
            
            # Cache risk assessment
            self._cache_risk_assessment(supplier_id, risk_assessment)
            
            # Audit log
            self.audit_logger.log_data_modification(
                user_id=user_id,
                resource_type='SUPPLIER_FINANCIAL_DATA',
                resource_id=supplier_id,
                modification_type='UPDATE',
                previous_values=None,  # Could fetch previous if needed
                new_values=financial_data,
                request_context=request_context
            )
            
            logger.end_operation("update_financial_data", success=True, 
                               supplier_id=supplier_id, risk_level=risk_assessment['risk_level'])
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Financial data updated successfully',
                    'risk_assessment': risk_assessment
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating financial data: {str(e)}", supplier_id=supplier_id)
            logger.end_operation("update_financial_data", success=False)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update financial data'}
            }
    
    def update_supplier(self, supplier_id: str, updates: Dict, user_id: str, request_context: Dict) -> Dict:
        """Update supplier information with audit logging"""
        try:
            logger.start_operation("update_supplier")
            
            # Get current supplier
            current_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in current_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Supplier not found'}
                }
            
            current_supplier = current_response['Item']
            
            # Prepare update expression
            update_expression = "SET updated_at = :now, updated_by = :user"
            expression_values = {
                ':now': datetime.utcnow().isoformat(),
                ':user': user_id
            }
            expression_names = {}
            
            # Build update expression dynamically
            for key, value in updates.items():
                if key != 'supplier_id':  # Don't update primary key
                    if key == 'status':  # Handle reserved keyword
                        update_expression += f", #status = :status"
                        expression_values[':status'] = value
                        expression_names['#status'] = 'status'
                    else:
                        update_expression += f", {key} = :{key}"
                        expression_values[f":{key}"] = value
            
            # Update the supplier
            update_params = {
                'Key': {'supplier_id': supplier_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values,
                'ReturnValues': 'ALL_NEW'
            }
            
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names
            
            response = suppliers_table.update_item(**update_params)
            
            # Audit log
            self.audit_logger.log_data_modification(
                user_id=user_id,
                resource_type='SUPPLIER',
                resource_id=supplier_id,
                modification_type='UPDATE',
                previous_values={k: current_supplier.get(k) for k in updates.keys()},
                new_values=updates,
                request_context=request_context
            )
            
            logger.end_operation("update_supplier", success=True, supplier_id=supplier_id)
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Supplier updated successfully',
                    'supplier': response['Attributes']
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating supplier: {str(e)}", supplier_id=supplier_id)
            logger.end_operation("update_supplier", success=False)
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update supplier'}
            }
    
    # Helper methods for performance metrics and risk assessment
    def _calculate_performance_metrics(self, supplier_id: str) -> Dict:
        """Calculate basic supplier performance metrics"""
        try:
            # Get all orders for this supplier
            response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            orders = response.get('Items', [])
            
            if not orders:
                return {
                    'total_orders': 0,
                    'on_time_delivery_rate': 0,
                    'quality_score': 0,
                    'average_lead_time': 0,
                    'total_value': 0
                }
            
            # Calculate metrics
            total_orders = len(orders)
            delivered_orders = [o for o in orders if o.get('status') == 'delivered']
            on_time_orders = [o for o in delivered_orders if self._is_delivery_on_time(o)]
            
            on_time_rate = (len(on_time_orders) / len(delivered_orders)) * 100 if delivered_orders else 0
            
            # Calculate average lead time
            lead_times = []
            for order in delivered_orders:
                if 'actual_delivery_date' in order and 'created_date' in order:
                    created = datetime.fromisoformat(order['created_date'].replace('Z', '+00:00'))
                    delivered = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
                    lead_time = (delivered - created).days
                    lead_times.append(lead_time)
            
            avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            
            # Calculate total value
            total_value = sum(float(o.get('total_amount', 0)) for o in orders)
            
            # Quality score (based on returns, defects, etc.)
            quality_issues = sum(1 for o in orders if o.get('quality_issues', 0) > 0)
            quality_score = max(0, 100 - (quality_issues / total_orders * 100)) if total_orders > 0 else 100
            
            return {
                'total_orders': total_orders,
                'on_time_delivery_rate': round(on_time_rate, 2),
                'quality_score': round(quality_score, 2),
                'average_lead_time': round(avg_lead_time, 1),
                'total_value': round(total_value, 2),
                'delivered_orders': len(delivered_orders),
                'pending_orders': len([o for o in orders if o.get('status') in ['pending', 'approved', 'shipped']])
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def _generate_supplier_recommendations(self, supplier: Dict, metrics: Dict) -> List[str]:
        """Generate recommendations for supplier management"""
        recommendations = []
        
        performance_score = metrics.get('quality_score', 0)
        on_time_rate = metrics.get('on_time_delivery_rate', 0)
        
        if performance_score >= 90 and on_time_rate >= 95:
            recommendations.append("Excellent supplier - consider preferred vendor status")
        elif performance_score >= 75 and on_time_rate >= 85:
            recommendations.append("Good supplier performance - maintain current relationship")
        elif performance_score >= 60 or on_time_rate >= 70:
            recommendations.append("Average performance - schedule improvement discussion")
        else:
            recommendations.append("Poor performance - consider supplier review")
        
        if on_time_rate < 80:
            recommendations.append("Address delivery performance issues")
        
        if performance_score < 85:
            recommendations.append("Implement quality improvement measures")
        
        return recommendations
    
    def _get_cached_risk_assessment(self, supplier_id: str) -> Optional[Dict]:
        """Get cached risk assessment if recent enough"""
        try:
            supplier_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in supplier_response:
                return None
            
            supplier = supplier_response['Item']
            last_assessment = supplier.get('last_risk_assessment')
            
            if last_assessment:
                assessment_date = datetime.fromisoformat(last_assessment.replace('Z', '+00:00'))
                # Use cached assessment if less than 7 days old
                if (datetime.utcnow() - assessment_date.replace(tzinfo=None)).days < 7:
                    return {
                        'supplier_id': supplier_id,
                        'risk_level': supplier.get('risk_level', 'MEDIUM'),
                        'overall_risk_score': float(supplier.get('risk_score', 50)),
                        'assessment_date': last_assessment,
                        'cached': True
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached risk assessment: {str(e)}")
            return None
    
    def _cache_risk_assessment(self, supplier_id: str, risk_data: Dict) -> None:
        """Cache risk assessment in supplier record"""
        try:
            suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression='SET risk_level = :level, risk_score = :score, last_risk_assessment = :date',
                ExpressionAttributeValues={
                    ':level': risk_data.get('risk_level', 'MEDIUM'),
                    ':score': Decimal(str(risk_data.get('overall_risk_score', 50))),
                    ':date': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error caching risk assessment: {str(e)}")
    
    def _get_contract_summary(self, supplier_id: str) -> Dict:
        """Get contract summary for supplier"""
        try:
            response = contracts_table.query(
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            contracts = response.get('Items', [])
            
            active_contracts = [c for c in contracts if c.get('contract_status') == 'active']
            total_value = sum(float(c.get('contract_value', 0)) for c in active_contracts)
            
            return {
                'total_contracts': len(contracts),
                'active_contracts': len(active_contracts),
                'total_active_value': round(total_value, 2),
                'expiring_soon': len([
                    c for c in active_contracts 
                    if c.get('end_date') and 
                    datetime.fromisoformat(c['end_date']) < datetime.utcnow() + timedelta(days=90)
                ])
            }
            
        except Exception as e:
            logger.error(f"Error getting contract summary: {str(e)}")
            return {'total_contracts': 0, 'active_contracts': 0}
    
    def _generate_comprehensive_recommendations(self, supplier: Dict, performance: Dict, risk: Dict) -> List[str]:
        """Generate comprehensive recommendations based on all metrics"""
        recommendations = []
        
        # Performance-based recommendations
        overall_score = performance.get('overall_score', 0)
        on_time_rate = performance.get('on_time_delivery_rate', 0)
        quality_score = performance.get('quality_score', 0)
        
        if overall_score >= 90:
            recommendations.append("Excellent supplier - consider preferred vendor status and volume discounts")
        elif overall_score >= 75:
            recommendations.append("Good supplier performance - maintain current relationship")
        elif overall_score >= 60:
            recommendations.append("Average performance - schedule improvement discussion")
        else:
            recommendations.append("Poor performance - consider supplier review or replacement")
        
        if on_time_rate < 85:
            recommendations.append("Address delivery performance issues - consider penalty clauses")
        
        if quality_score < 90:
            recommendations.append("Implement enhanced quality control measures")
        
        # Risk-based recommendations
        risk_level = risk.get('risk_level', 'MEDIUM')
        
        if risk_level == 'CRITICAL':
            recommendations.append("URGENT: High financial risk - consider immediate supplier diversification")
        elif risk_level == 'HIGH':
            recommendations.append("Monitor closely - implement risk mitigation measures")
        elif risk_level == 'LOW':
            recommendations.append("Low risk supplier - suitable for strategic partnerships")
        
        # Contract-based recommendations
        contract_summary = self._get_contract_summary(supplier['supplier_id'])
        if contract_summary.get('expiring_soon', 0) > 0:
            recommendations.append("Contract renewal required - schedule negotiation")
        
        return recommendations
    
    def _calculate_comprehensive_performance_metrics(self, supplier_id: str) -> Dict:
        """Calculate comprehensive supplier performance metrics with enhanced scoring"""
        try:
            # Get all orders for this supplier
            response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            orders = response.get('Items', [])
            
            if not orders:
                return {
                    'total_orders': 0,
                    'on_time_delivery_rate': 0,
                    'quality_score': 0,
                    'average_lead_time': 0,
                    'total_value': 0,
                    'overall_score': 0
                }
            
            # Calculate basic metrics
            total_orders = len(orders)
            delivered_orders = [o for o in orders if o.get('status') == 'delivered']
            on_time_orders = [o for o in delivered_orders if self._is_delivery_on_time(o)]
            
            on_time_rate = (len(on_time_orders) / len(delivered_orders)) * 100 if delivered_orders else 0
            
            # Calculate lead times
            lead_times = []
            for order in delivered_orders:
                if 'actual_delivery_date' in order and 'created_date' in order:
                    created = datetime.fromisoformat(order['created_date'].replace('Z', '+00:00'))
                    delivered = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
                    lead_time = (delivered - created).days
                    lead_times.append(lead_time)
            
            avg_lead_time = statistics.mean(lead_times) if lead_times else 0
            lead_time_consistency = 100 - (statistics.stdev(lead_times) if len(lead_times) > 1 else 0)
            
            # Calculate total value and order value consistency
            total_value = sum(float(o.get('total_amount', 0)) for o in orders)
            order_values = [float(o.get('total_amount', 0)) for o in orders if o.get('total_amount')]
            avg_order_value = statistics.mean(order_values) if order_values else 0
            
            # Quality metrics
            quality_issues = sum(1 for o in orders if o.get('quality_issues', 0) > 0)
            quality_score = max(0, 100 - (quality_issues / total_orders * 100)) if total_orders > 0 else 100
            
            # Communication and responsiveness metrics
            response_times = [float(o.get('response_time_hours', 24)) for o in orders if o.get('response_time_hours')]
            avg_response_time = statistics.mean(response_times) if response_times else 24
            communication_score = max(0, 100 - (avg_response_time - 2) * 5)  # Penalty for slow response
            
            # Calculate overall performance score
            weights = {
                'on_time_delivery': 0.30,
                'quality': 0.25,
                'communication': 0.20,
                'lead_time_consistency': 0.15,
                'order_fulfillment': 0.10
            }
            
            order_fulfillment_rate = (len(delivered_orders) / total_orders) * 100 if total_orders > 0 else 0
            
            overall_score = (
                on_time_rate * weights['on_time_delivery'] +
                quality_score * weights['quality'] +
                communication_score * weights['communication'] +
                lead_time_consistency * weights['lead_time_consistency'] +
                order_fulfillment_rate * weights['order_fulfillment']
            )
            
            return {
                'total_orders': total_orders,
                'on_time_delivery_rate': round(on_time_rate, 2),
                'quality_score': round(quality_score, 2),
                'communication_score': round(communication_score, 2),
                'average_lead_time': round(avg_lead_time, 1),
                'lead_time_consistency': round(lead_time_consistency, 2),
                'total_value': round(total_value, 2),
                'average_order_value': round(avg_order_value, 2),
                'order_fulfillment_rate': round(order_fulfillment_rate, 2),
                'overall_score': round(overall_score, 2),
                'delivered_orders': len(delivered_orders),
                'pending_orders': len([o for o in orders if o.get('status') in ['pending', 'approved', 'shipped']]),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def _get_supplier_financial_data(self, supplier_id: str) -> Dict:
        """Get supplier financial data for risk assessment"""
        try:
            response = financial_data_table.query(
                KeyConditionExpression='supplier_id = :sid AND data_type = :type',
                ExpressionAttributeValues={
                    ':sid': supplier_id,
                    ':type': 'financial_metrics'
                },
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                return items[0]
            else:
                # Return default financial data if none exists
                return {
                    'credit_rating': 'B',
                    'debt_to_equity_ratio': 0.8,
                    'cash_flow_trend': 0,
                    'market_reputation_score': 75,
                    'industry_rating': 'Average'
                }
                
        except Exception as e:
            logger.error(f"Error getting financial data: {str(e)}")
            return {}
    
    def _is_delivery_on_time(self, order: Dict) -> bool:
        """Check if delivery was on time"""
        try:
            if 'expected_delivery' not in order or 'actual_delivery_date' not in order:
                return False
                
            expected = datetime.fromisoformat(order['expected_delivery'].replace('Z', '+00:00'))
            actual = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
            
            return actual <= expected
            
        except Exception:
            return False


# Legacy methods for backward compatibility
class LegacySupplierManager:
    """Legacy supplier management methods maintained for backward compatibility"""
    
    def __init__(self):
        self.sns_topic = os.environ.get('SUPPLIER_ALERTS_TOPIC')
    
    def get_purchase_orders(self, filters: Optional[Dict] = None) -> Dict:
        """Get purchase orders with optional filtering"""
        try:
            if filters:
                if 'supplier_id' in filters:
                    response = purchase_orders_table.query(
                        IndexName='SupplierOrdersIndex',
                        KeyConditionExpression='supplier_id = :sid',
                        ExpressionAttributeValues={':sid': filters['supplier_id']},
                        ScanIndexForward=False  # Most recent first
                    )
                elif 'status' in filters:
                    response = purchase_orders_table.query(
                        IndexName='StatusIndex',
                        KeyConditionExpression='status = :status',
                        ExpressionAttributeValues={':status': filters['status']}
                    )
                else:
                    response = purchase_orders_table.scan()
            else:
                response = purchase_orders_table.scan()
                
            orders = response.get('Items', [])
            
            # Enrich with supplier information
            for order in orders:
                supplier_response = suppliers_table.get_item(
                    Key={'supplier_id': order['supplier_id']}
                )
                if 'Item' in supplier_response:
                    order['supplier_info'] = supplier_response['Item']
                    
            return {
                'statusCode': 200,
                'body': {
                    'purchase_orders': orders,
                    'count': len(orders),
                    'pending_count': len([o for o in orders if o.get('status') == 'pending']),
                    'total_value': sum(float(o.get('total_amount', 0)) for o in orders)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting purchase orders: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve purchase orders'}
            }
    
    def update_purchase_order_status(self, po_id: str, status: str, notes: Optional[str] = None) -> Dict:
        """Update purchase order status"""
        try:
            # Get current PO
            current_response = purchase_orders_table.get_item(Key={'po_id': po_id})
            
            if 'Item' not in current_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Purchase order not found'}
                }
            
            current_po = current_response['Item']
            
            # Prepare update
            update_expression = "SET #status = :status, updated_at = :now"
            expression_values = {
                ':status': status,
                ':now': datetime.utcnow().isoformat()
            }
            expression_names = {'#status': 'status'}
            
            if notes:
                update_expression += ", notes = :notes"
                expression_values[':notes'] = notes
            
            # Add status history
            status_history = current_po.get('status_history', [])
            status_history.append({
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'notes': notes
            })
            update_expression += ", status_history = :history"
            expression_values[':history'] = status_history
            
            # Update the PO
            response = purchase_orders_table.update_item(
                Key={'po_id': po_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            updated_po = response['Attributes']
            
            # Handle status-specific actions
            if status == 'delivered':
                self._handle_delivery_received(updated_po)
            elif status == 'cancelled':
                self._handle_po_cancelled(updated_po)
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'Purchase order status updated successfully',
                    'purchase_order': updated_po
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating purchase order status: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to update purchase order status'}
            }
    
    def get_supplier_performance(self, supplier_id: str) -> Dict:
        """Get detailed supplier performance metrics"""
        try:
            # Get supplier info
            supplier_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in supplier_response:
                return {
                    'statusCode': 404,
                    'body': {'error': 'Supplier not found'}
                }
            
            supplier = supplier_response['Item']
            
            # Get performance metrics
            performance_metrics = self._calculate_performance_metrics(supplier_id)
            
            # Get recent orders
            recent_orders_response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id},
                ScanIndexForward=False,
                Limit=10
            )
            
            recent_orders = recent_orders_response.get('Items', [])
            
            return {
                'statusCode': 200,
                'body': {
                    'supplier': supplier,
                    'performance_metrics': performance_metrics,
                    'recent_orders': recent_orders,
                    'recommendations': self._generate_supplier_recommendations(supplier, performance_metrics)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting supplier performance: {str(e)}")
            return {
                'statusCode': 500,
                'body': {'error': 'Failed to retrieve supplier performance'}
            }
    
    def _calculate_comprehensive_performance_metrics(self, supplier_id: str) -> Dict:
        """Calculate comprehensive supplier performance metrics with enhanced scoring"""
        try:
            # Get all orders for this supplier
            response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            orders = response.get('Items', [])
            
            if not orders:
                return {
                    'total_orders': 0,
                    'on_time_delivery_rate': 0,
                    'quality_score': 0,
                    'average_lead_time': 0,
                    'total_value': 0,
                    'overall_score': 0
                }
            
            # Calculate basic metrics
            total_orders = len(orders)
            delivered_orders = [o for o in orders if o.get('status') == 'delivered']
            on_time_orders = [o for o in delivered_orders if self._is_delivery_on_time(o)]
            
            on_time_rate = (len(on_time_orders) / len(delivered_orders)) * 100 if delivered_orders else 0
            
            # Calculate lead times
            lead_times = []
            for order in delivered_orders:
                if 'actual_delivery_date' in order and 'created_date' in order:
                    created = datetime.fromisoformat(order['created_date'].replace('Z', '+00:00'))
                    delivered = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
                    lead_time = (delivered - created).days
                    lead_times.append(lead_time)
            
            avg_lead_time = statistics.mean(lead_times) if lead_times else 0
            lead_time_consistency = 100 - (statistics.stdev(lead_times) if len(lead_times) > 1 else 0)
            
            # Calculate total value and order value consistency
            total_value = sum(float(o.get('total_amount', 0)) for o in orders)
            order_values = [float(o.get('total_amount', 0)) for o in orders if o.get('total_amount')]
            avg_order_value = statistics.mean(order_values) if order_values else 0
            
            # Quality metrics
            quality_issues = sum(1 for o in orders if o.get('quality_issues', 0) > 0)
            quality_score = max(0, 100 - (quality_issues / total_orders * 100)) if total_orders > 0 else 100
            
            # Communication and responsiveness metrics
            response_times = [float(o.get('response_time_hours', 24)) for o in orders if o.get('response_time_hours')]
            avg_response_time = statistics.mean(response_times) if response_times else 24
            communication_score = max(0, 100 - (avg_response_time - 2) * 5)  # Penalty for slow response
            
            # Calculate overall performance score
            weights = {
                'on_time_delivery': 0.30,
                'quality': 0.25,
                'communication': 0.20,
                'lead_time_consistency': 0.15,
                'order_fulfillment': 0.10
            }
            
            order_fulfillment_rate = (len(delivered_orders) / total_orders) * 100 if total_orders > 0 else 0
            
            overall_score = (
                on_time_rate * weights['on_time_delivery'] +
                quality_score * weights['quality'] +
                communication_score * weights['communication'] +
                lead_time_consistency * weights['lead_time_consistency'] +
                order_fulfillment_rate * weights['order_fulfillment']
            )
            
            return {
                'total_orders': total_orders,
                'on_time_delivery_rate': round(on_time_rate, 2),
                'quality_score': round(quality_score, 2),
                'communication_score': round(communication_score, 2),
                'average_lead_time': round(avg_lead_time, 1),
                'lead_time_consistency': round(lead_time_consistency, 2),
                'total_value': round(total_value, 2),
                'average_order_value': round(avg_order_value, 2),
                'order_fulfillment_rate': round(order_fulfillment_rate, 2),
                'overall_score': round(overall_score, 2),
                'delivered_orders': len(delivered_orders),
                'pending_orders': len([o for o in orders if o.get('status') in ['pending', 'approved', 'shipped']]),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def _get_supplier_financial_data(self, supplier_id: str) -> Dict:
        """Get supplier financial data for risk assessment"""
        try:
            response = financial_data_table.query(
                KeyConditionExpression='supplier_id = :sid AND data_type = :type',
                ExpressionAttributeValues={
                    ':sid': supplier_id,
                    ':type': 'financial_metrics'
                },
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                return items[0]
            else:
                # Return default financial data if none exists
                return {
                    'credit_rating': 'B',
                    'debt_to_equity_ratio': 0.8,
                    'cash_flow_trend': 0,
                    'market_reputation_score': 75,
                    'industry_rating': 'Average'
                }
                
        except Exception as e:
            logger.error(f"Error getting financial data: {str(e)}")
            return {}
    
    def _get_cached_risk_assessment(self, supplier_id: str) -> Optional[Dict]:
        """Get cached risk assessment if recent enough"""
        try:
            supplier_response = suppliers_table.get_item(Key={'supplier_id': supplier_id})
            
            if 'Item' not in supplier_response:
                return None
            
            supplier = supplier_response['Item']
            last_assessment = supplier.get('last_risk_assessment')
            
            if last_assessment:
                assessment_date = datetime.fromisoformat(last_assessment.replace('Z', '+00:00'))
                # Use cached assessment if less than 7 days old
                if (datetime.utcnow() - assessment_date.replace(tzinfo=None)).days < 7:
                    return {
                        'supplier_id': supplier_id,
                        'risk_level': supplier.get('risk_level', 'MEDIUM'),
                        'overall_risk_score': float(supplier.get('risk_score', 50)),
                        'assessment_date': last_assessment,
                        'cached': True
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached risk assessment: {str(e)}")
            return None
    
    def _cache_risk_assessment(self, supplier_id: str, risk_data: Dict) -> None:
        """Cache risk assessment in supplier record"""
        try:
            suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression='SET risk_level = :level, risk_score = :score, last_risk_assessment = :date',
                ExpressionAttributeValues={
                    ':level': risk_data.get('risk_level', 'MEDIUM'),
                    ':score': Decimal(str(risk_data.get('overall_risk_score', 50))),
                    ':date': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error caching risk assessment: {str(e)}")
    
    def _get_contract_summary(self, supplier_id: str) -> Dict:
        """Get contract summary for supplier"""
        try:
            response = contracts_table.query(
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            contracts = response.get('Items', [])
            
            active_contracts = [c for c in contracts if c.get('contract_status') == 'active']
            total_value = sum(float(c.get('contract_value', 0)) for c in active_contracts)
            
            return {
                'total_contracts': len(contracts),
                'active_contracts': len(active_contracts),
                'total_active_value': round(total_value, 2),
                'expiring_soon': len([
                    c for c in active_contracts 
                    if c.get('end_date') and 
                    datetime.fromisoformat(c['end_date']) < datetime.utcnow() + timedelta(days=90)
                ])
            }
            
        except Exception as e:
            logger.error(f"Error getting contract summary: {str(e)}")
            return {'total_contracts': 0, 'active_contracts': 0}
    
    def _generate_comprehensive_recommendations(self, supplier: Dict, performance: Dict, risk: Dict) -> List[str]:
        """Generate comprehensive recommendations based on all metrics"""
        recommendations = []
        
        # Performance-based recommendations
        overall_score = performance.get('overall_score', 0)
        on_time_rate = performance.get('on_time_delivery_rate', 0)
        quality_score = performance.get('quality_score', 0)
        
        if overall_score >= 90:
            recommendations.append("Excellent supplier - consider preferred vendor status and volume discounts")
        elif overall_score >= 75:
            recommendations.append("Good supplier performance - maintain current relationship")
        elif overall_score >= 60:
            recommendations.append("Average performance - schedule improvement discussion")
        else:
            recommendations.append("Poor performance - consider supplier review or replacement")
        
        if on_time_rate < 85:
            recommendations.append("Address delivery performance issues - consider penalty clauses")
        
        if quality_score < 90:
            recommendations.append("Implement enhanced quality control measures")
        
        # Risk-based recommendations
        risk_level = risk.get('risk_level', 'MEDIUM')
        
        if risk_level == 'CRITICAL':
            recommendations.append("URGENT: High financial risk - consider immediate supplier diversification")
        elif risk_level == 'HIGH':
            recommendations.append("Monitor closely - implement risk mitigation measures")
        elif risk_level == 'LOW':
            recommendations.append("Low risk supplier - suitable for strategic partnerships")
        
        # Contract-based recommendations
        contract_summary = self._get_contract_summary(supplier['supplier_id'])
        if contract_summary.get('expiring_soon', 0) > 0:
            recommendations.append("Contract renewal required - schedule negotiation")
        
        return recommendations
    
    def _is_delivery_on_time(self, order: Dict) -> bool:
        """Check if delivery was on time"""
        try:
            if 'expected_delivery' not in order or 'actual_delivery_date' not in order:
                return False
                
            expected = datetime.fromisoformat(order['expected_delivery'].replace('Z', '+00:00'))
            actual = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
            
            return actual <= expected
            
        except Exception:
            return False
    
    def _check_approval_needed(self, po_data: Dict) -> bool:
        """Check if purchase order needs approval"""
        total_amount = float(po_data.get('total_amount', 0))
        
        # Approval thresholds
        if total_amount > 25000:
            return True  # Executive approval needed
        elif total_amount > 5000:
            return True  # Manager approval needed
        else:
            return False  # Auto-approve small orders
    
    def _send_approval_request(self, po_data: Dict):
        """Send approval request notification"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'approval_request',
                'po_id': po_data['po_id'],
                'supplier_id': po_data['supplier_id'],
                'total_amount': po_data['total_amount'],
                'items_count': len(po_data.get('items', [])),
                'created_by': po_data.get('created_by', 'system'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Purchase Order Approval Required: {po_data['po_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending approval request: {str(e)}")
    
    def _send_po_to_supplier(self, po_data: Dict, supplier: Dict):
        """Send purchase order to supplier via API or email"""
        try:
            # Check if supplier has API integration
            if supplier.get('api_endpoint'):
                self._send_po_via_api(po_data, supplier)
            else:
                self._send_po_via_email(po_data, supplier)
                
        except Exception as e:
            logger.error(f"Error sending PO to supplier: {str(e)}")
    
    def _send_po_via_api(self, po_data: Dict, supplier: Dict):
        """Send PO via supplier API"""
        try:
            # Get API credentials from Secrets Manager
            secret_name = f"supplier-api-{supplier['supplier_id']}"
            
            try:
                secret_response = secrets_manager.get_secret_value(SecretId=secret_name)
                credentials = json.loads(secret_response['SecretString'])
            except ClientError:
                logger.warning(f"No API credentials found for supplier {supplier['supplier_id']}")
                return
            
            # Prepare API payload
            api_payload = {
                'purchase_order_id': po_data['po_id'],
                'items': po_data['items'],
                'total_amount': po_data['total_amount'],
                'expected_delivery': po_data['expected_delivery'],
                'delivery_address': po_data.get('delivery_address'),
                'special_instructions': po_data.get('special_instructions')
            }
            
            # Send to supplier API
            headers = {
                'Authorization': f"Bearer {credentials.get('api_key')}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                supplier['api_endpoint'],
                json=api_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Update PO with supplier confirmation
                purchase_orders_table.update_item(
                    Key={'po_id': po_data['po_id']},
                    UpdateExpression='SET supplier_confirmation = :conf, status = :status',
                    ExpressionAttributeValues={
                        ':conf': response.json(),
                        ':status': 'confirmed'
                    }
                )
            else:
                logger.error(f"Supplier API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending PO via API: {str(e)}")
    
    def _send_po_via_email(self, po_data: Dict, supplier: Dict):
        """Send PO via email notification"""
        try:
            message = {
                'type': 'purchase_order',
                'po_id': po_data['po_id'],
                'supplier_email': supplier.get('contact_email'),
                'po_data': po_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"New Purchase Order: {po_data['po_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending PO via email: {str(e)}")
    
    def _handle_delivery_received(self, po_data: Dict):
        """Handle actions when delivery is received"""
        try:
            # Update supplier performance
            supplier_id = po_data['supplier_id']
            
            # Check if delivery was on time
            on_time = self._is_delivery_on_time(po_data)
            
            # Update supplier metrics
            suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression='ADD total_orders :one, on_time_deliveries :on_time',
                ExpressionAttributeValues={
                    ':one': 1,
                    ':on_time': 1 if on_time else 0
                }
            )
            
            # Update inventory levels (would integrate with warehouse system)
            self._update_inventory_from_delivery(po_data)
            
        except Exception as e:
            logger.error(f"Error handling delivery received: {str(e)}")
    
    def _handle_po_cancelled(self, po_data: Dict):
        """Handle actions when PO is cancelled"""
        try:
            # Log cancellation reason
            logger.info(f"PO {po_data['po_id']} cancelled: {po_data.get('notes', 'No reason provided')}")
            
            # Notify relevant parties
            if self.sns_topic:
                message = {
                    'type': 'po_cancelled',
                    'po_id': po_data['po_id'],
                    'supplier_id': po_data['supplier_id'],
                    'reason': po_data.get('notes', 'No reason provided'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                sns.publish(
                    TopicArn=self.sns_topic,
                    Message=json.dumps(message),
                    Subject=f"Purchase Order Cancelled: {po_data['po_id']}"
                )
                
        except Exception as e:
            logger.error(f"Error handling PO cancellation: {str(e)}")
    
    def _update_inventory_from_delivery(self, po_data: Dict):
        """Update inventory levels when delivery is received"""
        try:
            for item in po_data.get('items', []):
                item_id = item.get('item_id')
                quantity_received = item.get('quantity_received', item.get('quantity', 0))
                location_id = item.get('location_id', 'MAIN-WAREHOUSE')
                
                if item_id and quantity_received > 0:
                    # Update inventory
                    inventory_table.update_item(
                        Key={'item_id': item_id, 'location_id': location_id},
                        UpdateExpression='ADD current_stock :qty SET last_received = :date, updated_at = :now',
                        ExpressionAttributeValues={
                            ':qty': quantity_received,
                            ':date': datetime.utcnow().isoformat(),
                            ':now': datetime.utcnow().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error updating inventory from delivery: {str(e)}")
        """Calculate comprehensive supplier performance metrics"""
        try:
            # Get all orders for this supplier
            response = purchase_orders_table.query(
                IndexName='SupplierOrdersIndex',
                KeyConditionExpression='supplier_id = :sid',
                ExpressionAttributeValues={':sid': supplier_id}
            )
            
            orders = response.get('Items', [])
            
            if not orders:
                return {
                    'total_orders': 0,
                    'on_time_delivery_rate': 0,
                    'quality_score': 0,
                    'average_lead_time': 0,
                    'total_value': 0
                }
            
            # Calculate metrics
            total_orders = len(orders)
            delivered_orders = [o for o in orders if o.get('status') == 'delivered']
            on_time_orders = [o for o in delivered_orders if self._is_delivery_on_time(o)]
            
            on_time_rate = (len(on_time_orders) / len(delivered_orders)) * 100 if delivered_orders else 0
            
            # Calculate average lead time
            lead_times = []
            for order in delivered_orders:
                if 'actual_delivery_date' in order and 'created_date' in order:
                    created = datetime.fromisoformat(order['created_date'].replace('Z', '+00:00'))
                    delivered = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
                    lead_time = (delivered - created).days
                    lead_times.append(lead_time)
            
            avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            
            # Calculate total value
            total_value = sum(float(o.get('total_amount', 0)) for o in orders)
            
            # Quality score (based on returns, defects, etc.)
            quality_issues = sum(1 for o in orders if o.get('quality_issues', 0) > 0)
            quality_score = max(0, 100 - (quality_issues / total_orders * 100)) if total_orders > 0 else 100
            
            return {
                'total_orders': total_orders,
                'on_time_delivery_rate': round(on_time_rate, 2),
                'quality_score': round(quality_score, 2),
                'average_lead_time': round(avg_lead_time, 1),
                'total_value': round(total_value, 2),
                'delivered_orders': len(delivered_orders),
                'pending_orders': len([o for o in orders if o.get('status') in ['pending', 'approved', 'shipped']])
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def _is_delivery_on_time(self, order: Dict) -> bool:
        """Check if delivery was on time"""
        try:
            if 'expected_delivery' not in order or 'actual_delivery_date' not in order:
                return False
                
            expected = datetime.fromisoformat(order['expected_delivery'].replace('Z', '+00:00'))
            actual = datetime.fromisoformat(order['actual_delivery_date'].replace('Z', '+00:00'))
            
            return actual <= expected
            
        except Exception:
            return False
    
    def _check_approval_needed(self, po_data: Dict) -> bool:
        """Check if purchase order needs approval"""
        total_amount = float(po_data.get('total_amount', 0))
        
        # Approval thresholds
        if total_amount > 25000:
            return True  # Executive approval needed
        elif total_amount > 5000:
            return True  # Manager approval needed
        else:
            return False  # Auto-approve small orders
    
    def _send_approval_request(self, po_data: Dict):
        """Send approval request notification"""
        if not self.sns_topic:
            return
            
        try:
            message = {
                'type': 'approval_request',
                'po_id': po_data['po_id'],
                'supplier_id': po_data['supplier_id'],
                'total_amount': po_data['total_amount'],
                'items_count': len(po_data.get('items', [])),
                'created_by': po_data.get('created_by', 'system'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"Purchase Order Approval Required: {po_data['po_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending approval request: {str(e)}")
    
    def _send_po_to_supplier(self, po_data: Dict, supplier: Dict):
        """Send purchase order to supplier via API or email"""
        try:
            # Check if supplier has API integration
            if supplier.get('api_endpoint'):
                self._send_po_via_api(po_data, supplier)
            else:
                self._send_po_via_email(po_data, supplier)
                
        except Exception as e:
            logger.error(f"Error sending PO to supplier: {str(e)}")
    
    def _send_po_via_api(self, po_data: Dict, supplier: Dict):
        """Send PO via supplier API"""
        try:
            # Get API credentials from Secrets Manager
            secret_name = f"supplier-api-{supplier['supplier_id']}"
            
            try:
                secret_response = secrets_manager.get_secret_value(SecretId=secret_name)
                credentials = json.loads(secret_response['SecretString'])
            except ClientError:
                logger.warning(f"No API credentials found for supplier {supplier['supplier_id']}")
                return
            
            # Prepare API payload
            api_payload = {
                'purchase_order_id': po_data['po_id'],
                'items': po_data['items'],
                'total_amount': po_data['total_amount'],
                'expected_delivery': po_data['expected_delivery'],
                'delivery_address': po_data.get('delivery_address'),
                'special_instructions': po_data.get('special_instructions')
            }
            
            # Send to supplier API
            headers = {
                'Authorization': f"Bearer {credentials.get('api_key')}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                supplier['api_endpoint'],
                json=api_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Update PO with supplier confirmation
                purchase_orders_table.update_item(
                    Key={'po_id': po_data['po_id']},
                    UpdateExpression='SET supplier_confirmation = :conf, status = :status',
                    ExpressionAttributeValues={
                        ':conf': response.json(),
                        ':status': 'confirmed'
                    }
                )
            else:
                logger.error(f"Supplier API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending PO via API: {str(e)}")
    
    def _send_po_via_email(self, po_data: Dict, supplier: Dict):
        """Send PO via email notification"""
        try:
            message = {
                'type': 'purchase_order',
                'po_id': po_data['po_id'],
                'supplier_email': supplier.get('contact_email'),
                'po_data': po_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=self.sns_topic,
                Message=json.dumps(message),
                Subject=f"New Purchase Order: {po_data['po_id']}"
            )
            
        except Exception as e:
            logger.error(f"Error sending PO via email: {str(e)}")
    
    def _handle_delivery_received(self, po_data: Dict):
        """Handle actions when delivery is received"""
        try:
            # Update supplier performance
            supplier_id = po_data['supplier_id']
            
            # Check if delivery was on time
            on_time = self._is_delivery_on_time(po_data)
            
            # Update supplier metrics
            suppliers_table.update_item(
                Key={'supplier_id': supplier_id},
                UpdateExpression='ADD total_orders :one, on_time_deliveries :on_time',
                ExpressionAttributeValues={
                    ':one': 1,
                    ':on_time': 1 if on_time else 0
                }
            )
            
            # Update inventory levels (would integrate with warehouse system)
            self._update_inventory_from_delivery(po_data)
            
        except Exception as e:
            logger.error(f"Error handling delivery received: {str(e)}")
    
    def _handle_po_cancelled(self, po_data: Dict):
        """Handle actions when PO is cancelled"""
        try:
            # Log cancellation reason
            logger.info(f"PO {po_data['po_id']} cancelled: {po_data.get('notes', 'No reason provided')}")
            
            # Notify relevant parties
            if self.sns_topic:
                message = {
                    'type': 'po_cancelled',
                    'po_id': po_data['po_id'],
                    'supplier_id': po_data['supplier_id'],
                    'reason': po_data.get('notes', 'No reason provided'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                sns.publish(
                    TopicArn=self.sns_topic,
                    Message=json.dumps(message),
                    Subject=f"Purchase Order Cancelled: {po_data['po_id']}"
                )
                
        except Exception as e:
            logger.error(f"Error handling PO cancellation: {str(e)}")
    
    def _update_inventory_from_delivery(self, po_data: Dict):
        """Update inventory levels when delivery is received"""
        try:
            for item in po_data.get('items', []):
                item_id = item.get('item_id')
                quantity_received = item.get('quantity_received', item.get('quantity', 0))
                location_id = item.get('location_id', 'MAIN-WAREHOUSE')
                
                if item_id and quantity_received > 0:
                    # Update inventory
                    inventory_table.update_item(
                        Key={'item_id': item_id, 'location_id': location_id},
                        UpdateExpression='ADD current_stock :qty SET last_received = :date, updated_at = :now',
                        ExpressionAttributeValues={
                            ':qty': quantity_received,
                            ':date': datetime.utcnow().isoformat(),
                            ':now': datetime.utcnow().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error updating inventory from delivery: {str(e)}")
    
    def _generate_supplier_recommendations(self, supplier: Dict, metrics: Dict) -> List[str]:
        """Generate recommendations for supplier management"""
        recommendations = []
        
        # Performance-based recommendations
        on_time_rate = metrics.get('on_time_delivery_rate', 0)
        quality_score = metrics.get('quality_score', 0)
        
        if on_time_rate < 85:
            recommendations.append("Consider discussing delivery performance with supplier")
        
        if quality_score < 90:
            recommendations.append("Review quality control processes with supplier")
        
        if metrics.get('total_orders', 0) > 50 and on_time_rate > 95:
            recommendations.append("Consider negotiating volume discounts")
        
        if supplier.get('status') == 'active' and on_time_rate > 90 and quality_score > 95:
            recommendations.append("Excellent supplier - consider preferred vendor status")
        
        return recommendations

def lambda_handler(event, context):
    """
    Enhanced Lambda handler for supplier management with dashboard overhaul features
    Supports Requirements 1.3 and 2.7 with comprehensive audit logging
    """
    try:
        logger.start_operation("lambda_handler")
        
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Extract user context for audit logging
        request_context = {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'request_id': event.get('requestContext', {}).get('requestId', 'unknown'),
            'source': 'api_gateway'
        }
        
        # Extract user ID from JWT token or authorizer context
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('user_id', 'unknown')
        
        # Parse request body
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        
        supplier_manager = SupplierManager()
        
        # Route requests with enhanced endpoints
        if http_method == 'GET' and path == '/api/suppliers':
            return supplier_manager.get_suppliers(query_parameters, user_id, request_context)
            
        elif http_method == 'POST' and path == '/api/suppliers':
            return supplier_manager.create_supplier(body, user_id, request_context)
            
        elif http_method == 'PUT' and '/api/suppliers/' in path and path.endswith('/suppliers'):
            supplier_id = path_parameters.get('supplier_id')
            return supplier_manager.update_supplier(supplier_id, body, user_id, request_context)
            
        elif http_method == 'GET' and '/api/suppliers/' in path and '/performance' in path:
            supplier_id = path_parameters.get('supplier_id')
            return supplier_manager.get_supplier_performance(supplier_id, user_id, request_context)
            
        elif http_method == 'PUT' and '/api/suppliers/' in path and '/financial-data' in path:
            supplier_id = path_parameters.get('supplier_id')
            return supplier_manager.update_supplier_financial_data(supplier_id, body, user_id, request_context)
            
        # Contract management endpoints
        elif http_method == 'POST' and path == '/api/contracts':
            return supplier_manager.contract_manager.create_contract(body, user_id, request_context)
            
        elif http_method == 'GET' and '/api/suppliers/' in path and '/contracts' in path:
            supplier_id = path_parameters.get('supplier_id')
            return supplier_manager.contract_manager.get_supplier_contracts(supplier_id, user_id, request_context)
            
        elif http_method == 'PUT' and '/api/contracts/' in path and '/status' in path:
            contract_id = path_parameters.get('contract_id')
            status = body.get('status')
            return supplier_manager.contract_manager.update_contract_status(contract_id, status, user_id, request_context)
            
        # Risk assessment endpoints
        elif http_method == 'POST' and '/api/suppliers/' in path and '/risk-assessment' in path:
            supplier_id = path_parameters.get('supplier_id')
            financial_data = body.get('financial_data', {})
            risk_assessment = supplier_manager.risk_assessment.calculate_financial_risk_score(supplier_id, financial_data)
            
            # Audit log
            supplier_manager.audit_logger.log_action(
                action_type='RISK_ASSESSMENT',
                user_id=user_id,
                resource_type='SUPPLIER',
                resource_id=supplier_id,
                details={'risk_level': risk_assessment.get('risk_level')},
                request_context=request_context
            )
            
            return {
                'statusCode': 200,
                'body': risk_assessment
            }
            
        # Legacy purchase order endpoints (maintained for backward compatibility)
        elif http_method == 'GET' and path == '/api/purchase-orders':
            return supplier_manager.get_purchase_orders(query_parameters)
            
        elif http_method == 'POST' and path == '/api/purchase-orders':
            return supplier_manager.create_purchase_order(body)
            
        elif http_method == 'PUT' and '/api/purchase-orders/' in path and '/status' in path:
            po_id = path_parameters.get('po_id')
            status = body.get('status')
            notes = body.get('notes')
            return supplier_manager.update_purchase_order_status(po_id, status, notes)
            
        # Health check endpoint
        elif http_method == 'GET' and path == '/health':
            return {
                'statusCode': 200,
                'body': {
                    'status': 'healthy',
                    'service': 'supplier-management',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '2.0.0'
                }
            }
            
        else:
            return {
                'statusCode': 404,
                'body': {'error': 'Endpoint not found'}
            }
            
    except Exception as e:
        logger.error(f"Unhandled error in supplier handler: {str(e)}")
        logger.end_operation("lambda_handler", success=False)
        return {
            'statusCode': 500,
            'body': {'error': 'Internal server error'}
        }
    finally:
        logger.end_operation("lambda_handler", success=True)
        # Publish metrics to CloudWatch
        logger.publish_metrics({'user_id': user_id} if 'user_id' in locals() else None)