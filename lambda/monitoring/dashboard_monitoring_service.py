"""
Dashboard Monitoring Service
Provides comprehensive monitoring and alerting for dashboard overhaul services
"""

import json
import boto3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import logging

# Import shared utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from structured_logger import get_logger, create_health_monitor, SystemHealthMonitor
from error_handler import handle_lambda_error


class DashboardMonitoringService:
    """
    Comprehensive monitoring service for dashboard overhaul system
    Provides health checks, performance monitoring, and alerting
    """
    
    def __init__(self):
        """Initialize monitoring service with AWS clients and configuration"""
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        self.dynamodb = boto3.resource('dynamodb')
        
        # Environment configuration
        self.namespace = os.environ.get('CLOUDWATCH_NAMESPACE', 'AquaChain/Dashboard')
        self.alert_topic_arn = os.environ.get('ALERT_TOPIC_ARN')
        self.environment = os.environ.get('ENVIRONMENT', 'dev')
        
        # Service configuration
        self.services = [
            'rbac-service',
            'audit-service', 
            'inventory-service',
            'warehouse-service',
            'supplier-service',
            'procurement-service',
            'budget-service',
            'workflow-service'
        ]
        
        # Initialize logger
        self.logger = get_logger(__name__, "dashboard-monitoring")
        
        # Performance thresholds
        self.performance_thresholds = {
            'api_response_time_ms': 500,  # 95th percentile
            'database_query_time_ms': 200,
            'error_rate_percent': 5.0,
            'memory_utilization_percent': 80.0,
            'concurrent_executions': 100
        }
    
    def perform_system_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check across all dashboard services
        
        Returns:
            System health status
        """
        try:
            self.logger.info("Starting system health check")
            
            system_health = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'healthy',
                'environment': self.environment,
                'services': {},
                'infrastructure': {},
                'alerts': []
            }
            
            # Check individual services
            unhealthy_services = []
            for service in self.services:
                service_health = self._check_service_health(service)
                system_health['services'][service] = service_health
                
                if service_health['status'] != 'healthy':
                    unhealthy_services.append(service)
            
            # Check infrastructure components
            system_health['infrastructure'] = self._check_infrastructure_health()
            
            # Determine overall system health
            if unhealthy_services:
                if len(unhealthy_services) > len(self.services) / 2:
                    system_health['overall_status'] = 'critical'
                else:
                    system_health['overall_status'] = 'degraded'
                
                system_health['unhealthy_services'] = unhealthy_services
            
            # Check for performance issues
            performance_issues = self._check_performance_metrics()
            if performance_issues:
                system_health['performance_issues'] = performance_issues
                if system_health['overall_status'] == 'healthy':
                    system_health['overall_status'] = 'degraded'
            
            # Generate alerts if needed
            if system_health['overall_status'] != 'healthy':
                alert = self._generate_system_alert(system_health)
                system_health['alerts'].append(alert)
            
            # Publish health metrics
            self._publish_system_health_metrics(system_health)
            
            self.logger.info(
                "System health check completed",
                overall_status=system_health['overall_status'],
                unhealthy_services=len(unhealthy_services),
                performance_issues=len(performance_issues) if performance_issues else 0
            )
            
            return system_health
            
        except Exception as e:
            self.logger.error("System health check failed", error=str(e))
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of individual service"""
        try:
            health_monitor = create_health_monitor(service_name)
            return health_monitor.check_service_health()
        except Exception as e:
            return {
                'service': service_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _check_infrastructure_health(self) -> Dict[str, Any]:
        """Check health of infrastructure components"""
        infrastructure_health = {
            'dynamodb': self._check_dynamodb_health(),
            's3': self._check_s3_health(),
            'kms': self._check_kms_health(),
            'cognito': self._check_cognito_health(),
            'api_gateway': self._check_api_gateway_health()
        }
        
        return infrastructure_health
    
    def _check_dynamodb_health(self) -> Dict[str, Any]:
        """Check DynamoDB health and performance"""
        try:
            # Check table status and metrics
            tables_to_check = [
                'dashboard-users',
                'inventory',
                'purchase-orders',
                'budget',
                'workflows',
                'dashboard-audit'
            ]
            
            healthy_tables = 0
            total_tables = len(tables_to_check)
            
            for table_name in tables_to_check:
                try:
                    table = self.dynamodb.Table(f"aquachain-{self.environment}-{table_name}")
                    table.load()
                    if table.table_status == 'ACTIVE':
                        healthy_tables += 1
                except Exception:
                    pass  # Table might not exist or be accessible
            
            health_percentage = (healthy_tables / total_tables) * 100
            
            return {
                'healthy': health_percentage >= 80,
                'healthy_tables': healthy_tables,
                'total_tables': total_tables,
                'health_percentage': health_percentage
            }
            
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_s3_health(self) -> Dict[str, Any]:
        """Check S3 health"""
        try:
            s3 = boto3.client('s3')
            s3.list_buckets()
            return {'healthy': True}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_kms_health(self) -> Dict[str, Any]:
        """Check KMS health"""
        try:
            kms = boto3.client('kms')
            kms.list_keys(Limit=1)
            return {'healthy': True}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_cognito_health(self) -> Dict[str, Any]:
        """Check Cognito health"""
        try:
            cognito = boto3.client('cognito-idp')
            cognito.list_user_pools(MaxResults=1)
            return {'healthy': True}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_api_gateway_health(self) -> Dict[str, Any]:
        """Check API Gateway health"""
        try:
            apigateway = boto3.client('apigateway')
            apigateway.get_rest_apis(limit=1)
            return {'healthy': True}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def _check_performance_metrics(self) -> List[Dict[str, Any]]:
        """Check performance metrics against thresholds"""
        issues = []
        
        try:
            # Get recent metrics from CloudWatch
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=15)
            
            # Check API response times
            api_metrics = self._get_cloudwatch_metrics(
                'AWS/ApiGateway',
                'Latency',
                start_time,
                end_time,
                [{'Name': 'ApiName', 'Value': 'DashboardAPI'}]
            )
            
            if api_metrics and api_metrics > self.performance_thresholds['api_response_time_ms']:
                issues.append({
                    'type': 'high_api_latency',
                    'current_value': api_metrics,
                    'threshold': self.performance_thresholds['api_response_time_ms'],
                    'severity': 'warning'
                })
            
            # Check Lambda error rates
            for service in self.services:
                error_rate = self._get_lambda_error_rate(service, start_time, end_time)
                if error_rate and error_rate > self.performance_thresholds['error_rate_percent']:
                    issues.append({
                        'type': 'high_error_rate',
                        'service': service,
                        'current_value': error_rate,
                        'threshold': self.performance_thresholds['error_rate_percent'],
                        'severity': 'critical'
                    })
            
        except Exception as e:
            self.logger.warning("Failed to check performance metrics", error=str(e))
        
        return issues
    
    def _get_cloudwatch_metrics(
        self,
        namespace: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        dimensions: List[Dict[str, str]]
    ) -> Optional[float]:
        """Get CloudWatch metric value"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return response['Datapoints'][-1]['Average']
            
        except Exception as e:
            self.logger.warning(f"Failed to get CloudWatch metric {metric_name}", error=str(e))
        
        return None
    
    def _get_lambda_error_rate(self, service: str, start_time: datetime, end_time: datetime) -> Optional[float]:
        """Get Lambda function error rate"""
        try:
            function_name = f"aquachain-{self.environment}-{service}"
            
            # Get invocation count
            invocations = self._get_cloudwatch_metrics(
                'AWS/Lambda',
                'Invocations',
                start_time,
                end_time,
                [{'Name': 'FunctionName', 'Value': function_name}]
            )
            
            # Get error count
            errors = self._get_cloudwatch_metrics(
                'AWS/Lambda',
                'Errors',
                start_time,
                end_time,
                [{'Name': 'FunctionName', 'Value': function_name}]
            )
            
            if invocations and invocations > 0:
                error_rate = ((errors or 0) / invocations) * 100
                return error_rate
            
        except Exception as e:
            self.logger.warning(f"Failed to get error rate for {service}", error=str(e))
        
        return None
    
    def _generate_system_alert(self, system_health: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system alert based on health status"""
        alert = {
            'id': f"system-alert-{int(datetime.now().timestamp())}",
            'timestamp': system_health['timestamp'],
            'severity': 'critical' if system_health['overall_status'] == 'critical' else 'warning',
            'title': f"Dashboard System Health Alert - {system_health['overall_status'].upper()}",
            'description': f"System status: {system_health['overall_status']}",
            'details': {}
        }
        
        if 'unhealthy_services' in system_health:
            alert['details']['unhealthy_services'] = system_health['unhealthy_services']
        
        if 'performance_issues' in system_health:
            alert['details']['performance_issues'] = system_health['performance_issues']
        
        # Send alert via SNS
        self._send_alert(alert)
        
        return alert
    
    def _send_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert via SNS"""
        if not self.alert_topic_arn:
            self.logger.warning("No alert topic ARN configured, skipping alert")
            return
        
        try:
            self.sns.publish(
                TopicArn=self.alert_topic_arn,
                Subject=alert['title'],
                Message=json.dumps(alert, indent=2)
            )
            
            self.logger.info("Alert sent successfully", alert_id=alert['id'])
            
        except Exception as e:
            self.logger.error("Failed to send alert", alert_id=alert['id'], error=str(e))
    
    def _publish_system_health_metrics(self, system_health: Dict[str, Any]) -> None:
        """Publish system health metrics to CloudWatch"""
        try:
            dimensions = [
                {'Name': 'Environment', 'Value': self.environment},
                {'Name': 'System', 'Value': 'Dashboard'}
            ]
            
            # Overall health metric
            health_value = {
                'healthy': 1,
                'degraded': 0.5,
                'critical': 0,
                'error': 0
            }.get(system_health['overall_status'], 0)
            
            metric_data = [
                {
                    'MetricName': 'SystemHealth',
                    'Value': health_value,
                    'Unit': 'None',
                    'Dimensions': dimensions
                }
            ]
            
            # Service health metrics
            for service, health in system_health.get('services', {}).items():
                service_value = 1 if health.get('status') == 'healthy' else 0
                metric_data.append({
                    'MetricName': 'ServiceHealth',
                    'Value': service_value,
                    'Unit': 'None',
                    'Dimensions': dimensions + [{'Name': 'Service', 'Value': service}]
                })
            
            # Infrastructure health metrics
            for component, health in system_health.get('infrastructure', {}).items():
                component_value = 1 if health.get('healthy', False) else 0
                metric_data.append({
                    'MetricName': 'InfrastructureHealth',
                    'Value': component_value,
                    'Unit': 'None',
                    'Dimensions': dimensions + [{'Name': 'Component', 'Value': component}]
                })
            
            # Publish metrics in batches
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            
        except Exception as e:
            self.logger.error("Failed to publish system health metrics", error=str(e))
    
    def get_system_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get system metrics summary for the specified time period
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Metrics summary
        """
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            summary = {
                'period': f"Last {hours} hours",
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'metrics': {}
            }
            
            # Get system health metrics
            system_health_data = self._get_cloudwatch_metrics(
                self.namespace,
                'SystemHealth',
                start_time,
                end_time,
                [
                    {'Name': 'Environment', 'Value': self.environment},
                    {'Name': 'System', 'Value': 'Dashboard'}
                ]
            )
            
            if system_health_data:
                summary['metrics']['average_system_health'] = system_health_data
            
            # Get API metrics
            api_latency = self._get_cloudwatch_metrics(
                'AWS/ApiGateway',
                'Latency',
                start_time,
                end_time,
                [{'Name': 'ApiName', 'Value': 'DashboardAPI'}]
            )
            
            if api_latency:
                summary['metrics']['average_api_latency_ms'] = api_latency
            
            # Get Lambda metrics for each service
            service_metrics = {}
            for service in self.services:
                error_rate = self._get_lambda_error_rate(service, start_time, end_time)
                if error_rate is not None:
                    service_metrics[service] = {'error_rate_percent': error_rate}
            
            if service_metrics:
                summary['metrics']['services'] = service_metrics
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to get system metrics summary", error=str(e))
            return {'error': str(e)}


# Lambda handler
def lambda_handler(event, context):
    """
    Lambda handler for dashboard monitoring operations
    """
    try:
        monitoring_service = DashboardMonitoringService()
        
        # Extract operation from event
        operation = event.get('operation', 'health_check')
        
        if operation == 'health_check':
            return monitoring_service.perform_system_health_check()
        
        elif operation == 'metrics_summary':
            hours = event.get('hours', 24)
            return monitoring_service.get_system_metrics_summary(hours)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        return handle_lambda_error(e, event, context)