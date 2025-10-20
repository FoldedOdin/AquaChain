"""
SLI/SLO Monitoring Setup for AquaChain System
Implements Service Level Indicators, Objectives, and Error Budget tracking
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError
import math


class SLIDefinition:
    """Service Level Indicator definition"""
    
    def __init__(self, name: str, description: str, metric_namespace: str, 
                 metric_name: str, good_threshold: float, total_metric_name: str = None):
        self.name = name
        self.description = description
        self.metric_namespace = metric_namespace
        self.metric_name = metric_name
        self.good_threshold = good_threshold
        self.total_metric_name = total_metric_name or metric_name


class SLODefinition:
    """Service Level Objective definition"""
    
    def __init__(self, name: str, sli: SLIDefinition, target_percentage: float, 
                 time_window_days: int = 30):
        self.name = name
        self.sli = sli
        self.target_percentage = target_percentage
        self.time_window_days = time_window_days
        self.error_budget_percentage = 100 - target_percentage


class AquaChainSLISetup:
    """Set up Service Level Indicators for AquaChain system"""
    
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.region = region
        
    def define_system_slis(self) -> List[SLIDefinition]:
        """Define all SLIs for the AquaChain system"""
        slis = [
            # Alert Latency SLI
            SLIDefinition(
                name='alert_latency',
                description='Percentage of alerts delivered within 30 seconds',
                metric_namespace='AquaChain/Alerts',
                metric_name='AlertLatency',
                good_threshold=30.0  # seconds
            ),
            
            # Data Ingestion Availability SLI
            SLIDefinition(
                name='data_ingestion_availability',
                description='Percentage of IoT data successfully processed',
                metric_namespace='AquaChain/DataIngestion',
                metric_name='ProcessingErrors',
                good_threshold=0.0,  # 0 errors is good
                total_metric_name='DeviceDataReceived'
            ),
            
            # API Response Time SLI
            SLIDefinition(
                name='api_response_time',
                description='Percentage of API requests completed within 2 seconds',
                metric_namespace='AWS/ApiGateway',
                metric_name='Latency',
                good_threshold=2000.0  # milliseconds
            ),
            
            # System Uptime SLI
            SLIDefinition(
                name='system_uptime',
                description='Percentage of time system is available',
                metric_namespace='AquaChain/SystemHealth',
                metric_name='ErrorRate',
                good_threshold=5.0  # <5% error rate is considered "up"
            ),
            
            # Technician Assignment Success SLI
            SLIDefinition(
                name='technician_assignment_success',
                description='Percentage of service requests successfully assigned',
                metric_namespace='AquaChain/ServiceRequests',
                metric_name='AssignmentFailures',
                good_threshold=0.0,  # 0 failures is good
                total_metric_name='ServiceRequestsCreated'
            ),
            
            # ML Inference Accuracy SLI
            SLIDefinition(
                name='ml_inference_accuracy',
                description='Percentage of ML predictions with high confidence',
                metric_namespace='AquaChain/ML',
                metric_name='LowConfidencePredictions',
                good_threshold=0.15,  # <15% low confidence is good
                total_metric_name='TotalPredictions'
            )
        ]
        
        return slis
    
    def create_sli_metrics(self, slis: List[SLIDefinition]):
        """Create CloudWatch metrics for SLI tracking"""
        created_metrics = []
        
        for sli in slis:
            # Create composite metric for SLI calculation
            metric_math = self._generate_sli_metric_math(sli)
            
            try:
                # Note: CloudWatch doesn't have a direct API for creating metric math expressions
                # These would typically be created through dashboards or alarms
                created_metrics.append({
                    'sli_name': sli.name,
                    'metric_math': metric_math,
                    'description': sli.description
                })
                print(f"SLI metric definition created: {sli.name}")
            except Exception as e:
                print(f"Error creating SLI metric {sli.name}: {e}")
                
        return created_metrics
    
    def _generate_sli_metric_math(self, sli: SLIDefinition) -> Dict[str, Any]:
        """Generate CloudWatch metric math expression for SLI calculation"""
        if sli.name == 'alert_latency':
            return {
                'expression': 'SUM(METRICS("m1")) / SUM(METRICS("m2")) * 100',
                'metrics': [
                    {
                        'id': 'm1',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': 'AlertsUnder30s',
                            'stat': 'Sum'
                        }
                    },
                    {
                        'id': 'm2',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': 'TotalAlerts',
                            'stat': 'Sum'
                        }
                    }
                ]
            }
        elif sli.name == 'data_ingestion_availability':
            return {
                'expression': '(m2 - m1) / m2 * 100',
                'metrics': [
                    {
                        'id': 'm1',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': sli.metric_name,
                            'stat': 'Sum'
                        }
                    },
                    {
                        'id': 'm2',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': sli.total_metric_name,
                            'stat': 'Sum'
                        }
                    }
                ]
            }
        elif sli.name == 'api_response_time':
            return {
                'expression': 'SUM(METRICS("m1")) / SUM(METRICS("m2")) * 100',
                'metrics': [
                    {
                        'id': 'm1',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': 'RequestsUnder2s',
                            'stat': 'Sum'
                        }
                    },
                    {
                        'id': 'm2',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': 'Count',
                            'stat': 'Sum'
                        }
                    }
                ]
            }
        else:
            # Generic SLI calculation
            return {
                'expression': f'100 - (m1 / m2 * 100)',
                'metrics': [
                    {
                        'id': 'm1',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': sli.metric_name,
                            'stat': 'Sum'
                        }
                    },
                    {
                        'id': 'm2',
                        'metric': {
                            'namespace': sli.metric_namespace,
                            'metric_name': sli.total_metric_name,
                            'stat': 'Sum'
                        }
                    }
                ]
            }


class AquaChainSLOSetup:
    """Set up Service Level Objectives and Error Budget tracking"""
    
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        
    def define_system_slos(self, slis: List[SLIDefinition]) -> List[SLODefinition]:
        """Define SLOs based on business requirements"""
        sli_map = {sli.name: sli for sli in slis}
        
        slos = [
            # Critical SLOs (99.5% target)
            SLODefinition(
                name='alert_latency_slo',
                sli=sli_map['alert_latency'],
                target_percentage=95.0,  # 95% of alerts within 30s
                time_window_days=30
            ),
            
            SLODefinition(
                name='data_ingestion_availability_slo',
                sli=sli_map['data_ingestion_availability'],
                target_percentage=99.5,  # 99.5% successful processing
                time_window_days=30
            ),
            
            # High Priority SLOs (99.0% target)
            SLODefinition(
                name='api_response_time_slo',
                sli=sli_map['api_response_time'],
                target_percentage=99.0,  # 99% of requests under 2s
                time_window_days=30
            ),
            
            SLODefinition(
                name='system_uptime_slo',
                sli=sli_map['system_uptime'],
                target_percentage=99.5,  # 99.5% uptime
                time_window_days=30
            ),
            
            # Medium Priority SLOs (98.0% target)
            SLODefinition(
                name='technician_assignment_success_slo',
                sli=sli_map['technician_assignment_success'],
                target_percentage=98.0,  # 98% successful assignments
                time_window_days=30
            ),
            
            SLODefinition(
                name='ml_inference_accuracy_slo',
                sli=sli_map['ml_inference_accuracy'],
                target_percentage=85.0,  # 85% high confidence predictions
                time_window_days=30
            )
        ]
        
        return slos
    
    def create_slo_dashboard(self, slos: List[SLODefinition]):
        """Create comprehensive SLO monitoring dashboard"""
        dashboard_body = {
            "widgets": []
        }
        
        # Create widgets for each SLO
        widget_x = 0
        widget_y = 0
        
        for i, slo in enumerate(slos):
            # SLO compliance widget
            slo_widget = {
                "type": "metric",
                "x": widget_x,
                "y": widget_y,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AquaChain/SLO", f"{slo.name}_compliance", {"stat": "Average"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": self.region,
                    "title": f"{slo.name.replace('_', ' ').title()} - Target: {slo.target_percentage}%",
                    "period": 3600,  # 1 hour periods
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {
                                "label": f"SLO Target ({slo.target_percentage}%)",
                                "value": slo.target_percentage
                            }
                        ]
                    }
                }
            }
            
            # Error budget widget
            error_budget_widget = {
                "type": "metric",
                "x": widget_x + 12,
                "y": widget_y,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AquaChain/SLO", f"{slo.name}_error_budget_remaining", {"stat": "Average"}]
                    ],
                    "view": "singleValue",
                    "region": self.region,
                    "title": f"{slo.name.replace('_', ' ').title()} - Error Budget Remaining",
                    "period": 3600
                }
            }
            
            dashboard_body["widgets"].extend([slo_widget, error_budget_widget])
            
            # Move to next row
            widget_y += 6
            if i % 2 == 1:  # Every 2 SLOs, reset x position
                widget_x = 0
            else:
                widget_x = 0
        
        # Add summary widget
        summary_widget = {
            "type": "metric",
            "x": 0,
            "y": widget_y,
            "width": 24,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AquaChain/SLO", "overall_slo_compliance", {"stat": "Average"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.region,
                "title": "Overall SLO Compliance",
                "period": 3600,
                "yAxis": {
                    "left": {
                        "min": 95,
                        "max": 100
                    }
                }
            }
        }
        
        dashboard_body["widgets"].append(summary_widget)
        
        try:
            response = self.cloudwatch.put_dashboard(
                DashboardName='AquaChain-SLO-ErrorBudgets',
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"Created SLO dashboard: {response}")
            return response
        except ClientError as e:
            print(f"Error creating SLO dashboard: {e}")
            raise
    
    def create_error_budget_alarms(self, slos: List[SLODefinition], sns_topic_arn: str):
        """Create alarms for error budget exhaustion"""
        alarms = []
        
        for slo in slos:
            # Error budget warning (50% consumed)
            warning_alarm = {
                'AlarmName': f'AquaChain-{slo.name}-ErrorBudget-Warning',
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 1,
                'MetricName': f'{slo.name}_error_budget_remaining',
                'Namespace': 'AquaChain/SLO',
                'Period': 3600,
                'Statistic': 'Average',
                'Threshold': 50.0,  # 50% error budget remaining
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': f'Warning: {slo.name} error budget 50% consumed',
                'Unit': 'Percent'
            }
            
            # Error budget critical (90% consumed)
            critical_alarm = {
                'AlarmName': f'AquaChain-{slo.name}-ErrorBudget-Critical',
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 1,
                'MetricName': f'{slo.name}_error_budget_remaining',
                'Namespace': 'AquaChain/SLO',
                'Period': 3600,
                'Statistic': 'Average',
                'Threshold': 10.0,  # 10% error budget remaining
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': f'CRITICAL: {slo.name} error budget 90% consumed',
                'Unit': 'Percent'
            }
            
            # SLO breach alarm
            breach_alarm = {
                'AlarmName': f'AquaChain-{slo.name}-SLO-Breach',
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': f'{slo.name}_compliance',
                'Namespace': 'AquaChain/SLO',
                'Period': 3600,
                'Statistic': 'Average',
                'Threshold': slo.target_percentage,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': f'SLO BREACH: {slo.name} below {slo.target_percentage}% target',
                'Unit': 'Percent'
            }
            
            alarms.extend([warning_alarm, critical_alarm, breach_alarm])
        
        created_alarms = []
        for alarm in alarms:
            try:
                response = self.cloudwatch.put_metric_alarm(**alarm)
                created_alarms.append(alarm['AlarmName'])
                print(f"Created error budget alarm: {alarm['AlarmName']}")
            except ClientError as e:
                print(f"Error creating alarm {alarm['AlarmName']}: {e}")
                
        return created_alarms


class ErrorBudgetCalculator:
    """Calculate and track error budgets"""
    
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
    def calculate_error_budget(self, slo: SLODefinition, 
                              current_sli_value: float, 
                              time_period_hours: int = 24) -> Dict[str, float]:
        """
        Calculate error budget consumption
        
        Args:
            slo: SLO definition
            current_sli_value: Current SLI percentage (0-100)
            time_period_hours: Time period for calculation
            
        Returns:
            Dictionary with error budget metrics
        """
        # Calculate allowed error budget for the time period
        total_budget = slo.error_budget_percentage
        time_fraction = time_period_hours / (slo.time_window_days * 24)
        period_budget = total_budget * time_fraction
        
        # Calculate actual errors
        if current_sli_value >= slo.target_percentage:
            actual_errors = 0.0
        else:
            actual_errors = slo.target_percentage - current_sli_value
        
        # Calculate budget consumption
        budget_consumed = (actual_errors / period_budget) * 100 if period_budget > 0 else 100
        budget_remaining = max(0, 100 - budget_consumed)
        
        # Calculate burn rate (how fast we're consuming budget)
        burn_rate = budget_consumed / time_period_hours if time_period_hours > 0 else 0
        
        # Estimate time to budget exhaustion
        if burn_rate > 0 and budget_remaining > 0:
            hours_to_exhaustion = budget_remaining / burn_rate
        else:
            hours_to_exhaustion = float('inf')
        
        return {
            'slo_name': slo.name,
            'target_percentage': slo.target_percentage,
            'current_sli_value': current_sli_value,
            'total_error_budget': total_budget,
            'period_error_budget': period_budget,
            'actual_errors': actual_errors,
            'budget_consumed_percentage': min(100, budget_consumed),
            'budget_remaining_percentage': budget_remaining,
            'burn_rate_per_hour': burn_rate,
            'hours_to_exhaustion': hours_to_exhaustion,
            'status': self._get_budget_status(budget_remaining)
        }
    
    def _get_budget_status(self, budget_remaining: float) -> str:
        """Get error budget status based on remaining budget"""
        if budget_remaining > 50:
            return 'healthy'
        elif budget_remaining > 10:
            return 'warning'
        else:
            return 'critical'
    
    def publish_error_budget_metrics(self, error_budget_data: Dict[str, float]):
        """Publish error budget metrics to CloudWatch"""
        try:
            metrics = [
                {
                    'MetricName': f"{error_budget_data['slo_name']}_error_budget_remaining",
                    'Value': error_budget_data['budget_remaining_percentage'],
                    'Unit': 'Percent'
                },
                {
                    'MetricName': f"{error_budget_data['slo_name']}_burn_rate",
                    'Value': error_budget_data['burn_rate_per_hour'],
                    'Unit': 'Percent/Hour'
                },
                {
                    'MetricName': f"{error_budget_data['slo_name']}_compliance",
                    'Value': error_budget_data['current_sli_value'],
                    'Unit': 'Percent'
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='AquaChain/SLO',
                MetricData=metrics
            )
            
            print(f"Published error budget metrics for {error_budget_data['slo_name']}")
            
        except Exception as e:
            print(f"Error publishing error budget metrics: {e}")


def setup_complete_sli_slo_monitoring():
    """Set up complete SLI/SLO monitoring infrastructure"""
    print("Setting up SLI/SLO monitoring for AquaChain...")
    
    # Initialize components
    sli_setup = AquaChainSLISetup()
    slo_setup = AquaChainSLOSetup()
    
    # Define SLIs and SLOs
    slis = sli_setup.define_system_slis()
    slos = slo_setup.define_system_slos(slis)
    
    # Create SLI metrics
    sli_metrics = sli_setup.create_sli_metrics(slis)
    
    # Create SLO dashboard
    slo_setup.create_slo_dashboard(slos)
    
    # Create SNS topic for SLO alerts
    sns_client = boto3.client('sns')
    try:
        topic_response = sns_client.create_topic(
            Name='aquachain-slo-alerts',
            Attributes={
                'DisplayName': 'AquaChain SLO Alerts',
                'Description': 'Alerts for SLO breaches and error budget exhaustion'
            }
        )
        sns_topic_arn = topic_response['TopicArn']
    except Exception as e:
        print(f"Error creating SNS topic: {e}")
        sns_topic_arn = 'arn:aws:sns:us-east-1:123456789012:aquachain-slo-alerts'
    
    # Create error budget alarms
    error_budget_alarms = slo_setup.create_error_budget_alarms(slos, sns_topic_arn)
    
    return {
        'slis': [sli.name for sli in slis],
        'slos': [slo.name for slo in slos],
        'sli_metrics': sli_metrics,
        'error_budget_alarms': error_budget_alarms,
        'sns_topic_arn': sns_topic_arn
    }


if __name__ == "__main__":
    # Example usage
    result = setup_complete_sli_slo_monitoring()
    print("SLI/SLO monitoring setup complete!")
    print(json.dumps(result, indent=2, default=str))