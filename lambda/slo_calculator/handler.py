"""
SLO Calculator Lambda Function
Calculates SLI values, SLO compliance, and error budget consumption
Runs periodically to update SLO metrics
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Add shared utilities to path
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='slo-calculator')

# Initialize AWS clients
cloudwatch = boto3.client('cloudwatch')


class SLOCalculator:
    """Calculate SLO compliance and error budget metrics"""
    
    def __init__(self):
        self.cloudwatch = cloudwatch
        
    def calculate_alert_latency_sli(self, time_window_hours: int = 24) -> float:
        """Calculate alert latency SLI (% of alerts delivered within 30s)"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        try:
            # Get alert latency metrics
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/Alerts',
                MetricName='AlertLatency',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Average', 'SampleCount']
            )
            
            if not response['Datapoints']:
                return 100.0  # No alerts = 100% compliance
            
            # Calculate percentage of alerts under 30 seconds
            total_alerts = 0
            alerts_under_30s = 0
            
            for datapoint in response['Datapoints']:
                count = datapoint['SampleCount']
                avg_latency = datapoint['Average']
                
                total_alerts += count
                
                # Estimate alerts under 30s (simplified calculation)
                if avg_latency <= 30:
                    alerts_under_30s += count
                else:
                    # Assume normal distribution, estimate percentage under threshold
                    # This is a simplified approach - in production, you'd want more precise tracking
                    alerts_under_30s += count * 0.5  # Conservative estimate
            
            if total_alerts == 0:
                return 100.0
            
            sli_value = (alerts_under_30s / total_alerts) * 100
            logger.info(f"Alert Latency SLI: {sli_value:.2f}% ({alerts_under_30s}/{total_alerts} alerts under 30s)")
            
            return min(100.0, max(0.0, sli_value))
            
        except Exception as e:
            logger.error(f"Error calculating alert latency SLI: {e}")
            return 0.0
    
    def calculate_data_ingestion_availability_sli(self, time_window_hours: int = 24) -> float:
        """Calculate data ingestion availability SLI"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        try:
            # Get total messages received
            total_response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/DataIngestion',
                MetricName='DeviceDataReceived',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get processing errors
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/DataIngestion',
                MetricName='ProcessingErrors',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            total_messages = sum(dp['Sum'] for dp in total_response['Datapoints'])
            total_errors = sum(dp['Sum'] for dp in error_response['Datapoints'])
            
            if total_messages == 0:
                return 100.0  # No messages = 100% availability
            
            success_rate = ((total_messages - total_errors) / total_messages) * 100
            logger.info(f"Data Ingestion Availability SLI: {success_rate:.2f}% ({total_messages - total_errors}/{total_messages} successful)")
            
            return min(100.0, max(0.0, success_rate))
            
        except Exception as e:
            logger.error(f"Error calculating data ingestion availability SLI: {e}")
            return 0.0
    
    def calculate_api_response_time_sli(self, time_window_hours: int = 24) -> float:
        """Calculate API response time SLI (% of requests under 2s)"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        try:
            # Get API Gateway latency metrics
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='Latency',
                Dimensions=[
                    {'Name': 'ApiName', 'Value': 'aquachain-api'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'SampleCount']
            )
            
            if not response['Datapoints']:
                return 100.0  # No requests = 100% compliance
            
            total_requests = 0
            requests_under_2s = 0
            
            for datapoint in response['Datapoints']:
                count = datapoint['SampleCount']
                avg_latency = datapoint['Average']
                
                total_requests += count
                
                # Estimate requests under 2000ms
                if avg_latency <= 2000:
                    requests_under_2s += count
                else:
                    # Conservative estimate for requests over threshold
                    requests_under_2s += count * 0.3
            
            if total_requests == 0:
                return 100.0
            
            sli_value = (requests_under_2s / total_requests) * 100
            logger.info(f"API Response Time SLI: {sli_value:.2f}% ({requests_under_2s}/{total_requests} requests under 2s)")
            
            return min(100.0, max(0.0, sli_value))
            
        except Exception as e:
            logger.error(f"Error calculating API response time SLI: {e}")
            return 0.0
    
    def calculate_system_uptime_sli(self, time_window_hours: int = 24) -> float:
        """Calculate system uptime SLI based on error rates"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        try:
            # Get system error rate
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/SystemHealth',
                MetricName='ErrorRate',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            if not response['Datapoints']:
                return 100.0  # No data = assume 100% uptime
            
            # Calculate average error rate
            avg_error_rate = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
            
            # System is "up" when error rate is below 5%
            if avg_error_rate < 5.0:
                uptime_percentage = 100.0
            else:
                # Calculate uptime based on error rate
                uptime_percentage = max(0.0, 100.0 - (avg_error_rate - 5.0) * 2)
            
            logger.info(f"System Uptime SLI: {uptime_percentage:.2f}% (avg error rate: {avg_error_rate:.2f}%)")
            
            return uptime_percentage
            
        except Exception as e:
            logger.error(f"Error calculating system uptime SLI: {e}")
            return 0.0
    
    def calculate_technician_assignment_success_sli(self, time_window_hours: int = 24) -> float:
        """Calculate technician assignment success SLI"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        try:
            # Get total service requests
            total_response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/ServiceRequests',
                MetricName='ServiceRequestsCreated',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get assignment failures
            failure_response = self.cloudwatch.get_metric_statistics(
                Namespace='AquaChain/ServiceRequests',
                MetricName='AssignmentFailures',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            total_requests = sum(dp['Sum'] for dp in total_response['Datapoints'])
            total_failures = sum(dp['Sum'] for dp in failure_response['Datapoints'])
            
            if total_requests == 0:
                return 100.0  # No requests = 100% success
            
            success_rate = ((total_requests - total_failures) / total_requests) * 100
            logger.info(f"Technician Assignment Success SLI: {success_rate:.2f}% ({total_requests - total_failures}/{total_requests} successful)")
            
            return min(100.0, max(0.0, success_rate))
            
        except Exception as e:
            logger.error(f"Error calculating technician assignment success SLI: {e}")
            return 0.0
    
    def calculate_error_budget(self, sli_value: float, slo_target: float, 
                              time_window_days: int = 30, current_period_hours: int = 24) -> Dict[str, float]:
        """Calculate error budget consumption"""
        # Total error budget for the SLO period
        total_error_budget = 100 - slo_target
        
        # Time fraction of current period vs total SLO window
        time_fraction = current_period_hours / (time_window_days * 24)
        
        # Allowed error budget for current period
        period_error_budget = total_error_budget * time_fraction
        
        # Actual errors in current period
        if sli_value >= slo_target:
            actual_errors = 0.0
        else:
            actual_errors = slo_target - sli_value
        
        # Budget consumption
        if period_error_budget > 0:
            budget_consumed = (actual_errors / period_error_budget) * 100
        else:
            budget_consumed = 100.0 if actual_errors > 0 else 0.0
        
        budget_remaining = max(0.0, 100.0 - budget_consumed)
        
        # Burn rate (budget consumption per hour)
        burn_rate = budget_consumed / current_period_hours if current_period_hours > 0 else 0
        
        return {
            'sli_value': sli_value,
            'slo_target': slo_target,
            'total_error_budget': total_error_budget,
            'period_error_budget': period_error_budget,
            'actual_errors': actual_errors,
            'budget_consumed_percentage': min(100.0, budget_consumed),
            'budget_remaining_percentage': budget_remaining,
            'burn_rate_per_hour': burn_rate
        }
    
    def publish_slo_metrics(self, slo_name: str, sli_value: float, error_budget_data: Dict[str, float]):
        """Publish SLO metrics to CloudWatch"""
        try:
            metrics = [
                {
                    'MetricName': f'{slo_name}_compliance',
                    'Value': sli_value,
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': f'{slo_name}_error_budget_remaining',
                    'Value': error_budget_data['budget_remaining_percentage'],
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': f'{slo_name}_burn_rate',
                    'Value': error_budget_data['burn_rate_per_hour'],
                    'Unit': 'Percent/Hour',
                    'Timestamp': datetime.utcnow()
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='AquaChain/SLO',
                MetricData=metrics
            )
            
            logger.info(f"Published SLO metrics for {slo_name}")
            
        except Exception as e:
            logger.error(f"Error publishing SLO metrics for {slo_name}: {e}")


def lambda_handler(event, context):
    """
    Lambda handler for SLO calculation and error budget tracking
    Triggered by CloudWatch Events (scheduled execution)
    """
    try:
        logger.info("Starting SLO calculation and error budget tracking")
        
        calculator = SLOCalculator()
        
        # Define SLOs with their targets
        slos = [
            {'name': 'alert_latency_slo', 'target': 95.0, 'calculator': calculator.calculate_alert_latency_sli},
            {'name': 'data_ingestion_availability_slo', 'target': 99.5, 'calculator': calculator.calculate_data_ingestion_availability_sli},
            {'name': 'api_response_time_slo', 'target': 99.0, 'calculator': calculator.calculate_api_response_time_sli},
            {'name': 'system_uptime_slo', 'target': 99.5, 'calculator': calculator.calculate_system_uptime_sli},
            {'name': 'technician_assignment_success_slo', 'target': 98.0, 'calculator': calculator.calculate_technician_assignment_success_sli}
        ]
        
        results = []
        overall_compliance_sum = 0
        
        # Calculate each SLO
        for slo in slos:
            try:
                # Calculate SLI value
                sli_value = slo['calculator']()
                
                # Calculate error budget
                error_budget_data = calculator.calculate_error_budget(
                    sli_value=sli_value,
                    slo_target=slo['target']
                )
                
                # Publish metrics
                calculator.publish_slo_metrics(slo['name'], sli_value, error_budget_data)
                
                # Store results
                result = {
                    'slo_name': slo['name'],
                    'sli_value': sli_value,
                    'target': slo['target'],
                    'compliant': sli_value >= slo['target'],
                    'error_budget_remaining': error_budget_data['budget_remaining_percentage'],
                    'burn_rate': error_budget_data['burn_rate_per_hour']
                }
                
                results.append(result)
                overall_compliance_sum += sli_value
                
                logger.info(f"SLO {slo['name']}: {sli_value:.2f}% (target: {slo['target']}%, "
                           f"error budget: {error_budget_data['budget_remaining_percentage']:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error calculating SLO {slo['name']}: {e}")
                results.append({
                    'slo_name': slo['name'],
                    'error': str(e)
                })
        
        # Calculate overall compliance
        if len(slos) > 0:
            overall_compliance = overall_compliance_sum / len(slos)
            
            # Publish overall compliance metric
            calculator.cloudwatch.put_metric_data(
                Namespace='AquaChain/SLO',
                MetricData=[
                    {
                        'MetricName': 'overall_slo_compliance',
                        'Value': overall_compliance,
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
            logger.info(f"Overall SLO compliance: {overall_compliance:.2f}%")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SLO calculation completed successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'overall_compliance': overall_compliance,
                'slo_results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Error in SLO calculation: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }