"""
Performance Monitoring and Alerting System for AquaChain
Provides continuous performance monitoring with automated alerting
"""

import boto3
import json
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
import argparse
from dataclasses import dataclass, asdict
import threading
import requests

@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    alert_id: str
    metric_name: str
    threshold_value: float
    comparison: str  # greater_than, less_than, equals
    severity: str  # low, medium, high, critical
    notification_channels: List[str]  # email, sns, pagerduty
    cooldown_minutes: int
    enabled: bool

@dataclass
class AlertTrigger:
    """Alert trigger event."""
    alert_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str
    timestamp: str
    message: str
    notification_sent: bool

@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    metric_name: str
    value: float
    timestamp: str
    dimensions: Dict[str, str]
    unit: str

class PerformanceMonitor:
    """Continuous performance monitoring and alerting system."""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.sns = boto3.client('sns', region_name=aws_region)
        self.lambda_client = boto3.client('lambda', region_name=aws_region)
        
        # Monitoring state
        self.monitoring_active = False
        self.alert_history: List[AlertTrigger] = []
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Performance alerts configuration
        self.performance_alerts = [
            PerformanceAlert(
                alert_id="lambda_duration_high",
                metric_name="lambda_duration",
                threshold_value=5000,  # 5 seconds
                comparison="greater_than",
                severity="high",
                notification_channels=["sns", "email"],
                cooldown_minutes=15,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="lambda_duration_critical",
                metric_name="lambda_duration",
                threshold_value=10000,  # 10 seconds
                comparison="greater_than",
                severity="critical",
                notification_channels=["sns", "email", "pagerduty"],
                cooldown_minutes=5,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="api_latency_high",
                metric_name="api_latency",
                threshold_value=1000,  # 1 second
                comparison="greater_than",
                severity="high",
                notification_channels=["sns", "email"],
                cooldown_minutes=10,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="api_latency_critical",
                metric_name="api_latency",
                threshold_value=2000,  # 2 seconds
                comparison="greater_than",
                severity="critical",
                notification_channels=["sns", "email", "pagerduty"],
                cooldown_minutes=5,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="error_rate_high",
                metric_name="error_rate",
                threshold_value=5.0,  # 5%
                comparison="greater_than",
                severity="high",
                notification_channels=["sns", "email"],
                cooldown_minutes=10,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="error_rate_critical",
                metric_name="error_rate",
                threshold_value=10.0,  # 10%
                comparison="greater_than",
                severity="critical",
                notification_channels=["sns", "email", "pagerduty"],
                cooldown_minutes=5,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="dynamodb_latency_high",
                metric_name="dynamodb_latency",
                threshold_value=100,  # 100ms
                comparison="greater_than",
                severity="medium",
                notification_channels=["sns"],
                cooldown_minutes=20,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="throughput_low",
                metric_name="throughput",
                threshold_value=100,  # 100 requests/minute
                comparison="less_than",
                severity="medium",
                notification_channels=["sns", "email"],
                cooldown_minutes=30,
                enabled=True
            ),
            PerformanceAlert(
                alert_id="memory_utilization_high",
                metric_name="memory_utilization",
                threshold_value=80.0,  # 80%
                comparison="greater_than",
                severity="medium",
                notification_channels=["sns"],
                cooldown_minutes=15,
                enabled=True
            )
        ]
    
    def collect_performance_metrics(self) -> List[PerformanceMetric]:
        """Collect current performance metrics from various sources."""
        metrics = []
        current_time = datetime.now(timezone.utc).isoformat()
        
        try:
            # Lambda duration metrics
            lambda_duration = self._get_lambda_duration_metric()
            if lambda_duration is not None:
                metrics.append(PerformanceMetric(
                    metric_name="lambda_duration",
                    value=lambda_duration,
                    timestamp=current_time,
                    dimensions={"FunctionName": "AquaChain-data-processing"},
                    unit="Milliseconds"
                ))
            
            # API latency metrics
            api_latency = self._get_api_latency_metric()
            if api_latency is not None:
                metrics.append(PerformanceMetric(
                    metric_name="api_latency",
                    value=api_latency,
                    timestamp=current_time,
                    dimensions={"ApiName": "AquaChain-API"},
                    unit="Milliseconds"
                ))
            
            # Error rate metrics
            error_rate = self._get_error_rate_metric()
            if error_rate is not None:
                metrics.append(PerformanceMetric(
                    metric_name="error_rate",
                    value=error_rate,
                    timestamp=current_time,
                    dimensions={"Service": "AquaChain"},
                    unit="Percent"
                ))
            
            # DynamoDB latency metrics
            dynamodb_latency = self._get_dynamodb_latency_metric()
            if dynamodb_latency is not None:
                metrics.append(PerformanceMetric(
                    metric_name="dynamodb_latency",
                    value=dynamodb_latency,
                    timestamp=current_time,
                    dimensions={"TableName": "aquachain-readings"},
                    unit="Milliseconds"
                ))
            
            # Throughput metrics
            throughput = self._get_throughput_metric()
            if throughput is not None:
                metrics.append(PerformanceMetric(
                    metric_name="throughput",
                    value=throughput,
                    timestamp=current_time,
                    dimensions={"Service": "AquaChain"},
                    unit="Count/Minute"
                ))
            
            # Memory utilization metrics
            memory_utilization = self._get_memory_utilization_metric()
            if memory_utilization is not None:
                metrics.append(PerformanceMetric(
                    metric_name="memory_utilization",
                    value=memory_utilization,
                    timestamp=current_time,
                    dimensions={"FunctionName": "AquaChain-data-processing"},
                    unit="Percent"
                ))
            
        except Exception as e:
            print(f"Warning: Error collecting metrics: {e}")
        
        return metrics
    
    def _get_lambda_duration_metric(self) -> Optional[float]:
        """Get Lambda function duration metric."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                return statistics.mean([dp['Average'] for dp in datapoints])
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not get Lambda duration metric: {e}")
            return None
    
    def _get_api_latency_metric(self) -> Optional[float]:
        """Get API latency metric by testing endpoints."""
        try:
            test_endpoints = [
                'https://api.aquachain.io/health',
                'https://api.aquachain.io/api/v1/readings/test-device'
            ]
            
            latencies = []
            for endpoint in test_endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(endpoint, timeout=5)
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000  # Convert to milliseconds
                    latencies.append(latency)
                except Exception:
                    latencies.append(5000)  # 5 second timeout
            
            return statistics.mean(latencies) if latencies else None
            
        except Exception as e:
            print(f"Warning: Could not get API latency metric: {e}")
            return None
    
    def _get_error_rate_metric(self) -> Optional[float]:
        """Get system error rate metric."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            # Get Lambda errors
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Get Lambda invocations
            invocation_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            total_errors = sum(dp['Sum'] for dp in error_response.get('Datapoints', []))
            total_invocations = sum(dp['Sum'] for dp in invocation_response.get('Datapoints', []))
            
            if total_invocations > 0:
                return (total_errors / total_invocations) * 100
            
            return 0.0
            
        except Exception as e:
            print(f"Warning: Could not get error rate metric: {e}")
            return None
    
    def _get_dynamodb_latency_metric(self) -> Optional[float]:
        """Get DynamoDB latency metric."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='SuccessfulRequestLatency',
                Dimensions=[
                    {'Name': 'TableName', 'Value': 'aquachain-readings'},
                    {'Name': 'Operation', 'Value': 'Query'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                return statistics.mean([dp['Average'] for dp in datapoints])
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not get DynamoDB latency metric: {e}")
            return None
    
    def _get_throughput_metric(self) -> Optional[float]:
        """Get system throughput metric."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': 'AquaChain-data-processing'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                total_invocations = sum(dp['Sum'] for dp in datapoints)
                return total_invocations  # Invocations per 5 minutes
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not get throughput metric: {e}")
            return None
    
    def _get_memory_utilization_metric(self) -> Optional[float]:
        """Get memory utilization metric (estimated from duration)."""
        try:
            # This is a simplified estimation - in real implementation,
            # you would use custom metrics or Lambda Insights
            duration = self._get_lambda_duration_metric()
            if duration is not None:
                # Rough estimation: higher duration often correlates with higher memory usage
                # This is a simplified heuristic
                estimated_memory_usage = min(100, (duration / 1000) * 20)  # Cap at 100%
                return estimated_memory_usage
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not get memory utilization metric: {e}")
            return None
    
    def evaluate_alerts(self, metrics: List[PerformanceMetric]) -> List[AlertTrigger]:
        """Evaluate performance metrics against alert thresholds."""
        triggered_alerts = []
        current_time = datetime.now(timezone.utc)
        
        # Create metric lookup
        metric_values = {metric.metric_name: metric.value for metric in metrics}
        
        for alert in self.performance_alerts:
            if not alert.enabled:
                continue
            
            if alert.metric_name not in metric_values:
                continue
            
            current_value = metric_values[alert.metric_name]
            
            # Check if alert should trigger
            should_trigger = False
            if alert.comparison == "greater_than":
                should_trigger = current_value > alert.threshold_value
            elif alert.comparison == "less_than":
                should_trigger = current_value < alert.threshold_value
            elif alert.comparison == "equals":
                should_trigger = abs(current_value - alert.threshold_value) < 0.01
            
            if should_trigger:
                # Check cooldown period
                last_alert_time = self.last_alert_times.get(alert.alert_id)
                if last_alert_time:
                    time_since_last = (current_time - last_alert_time).total_seconds() / 60
                    if time_since_last < alert.cooldown_minutes:
                        continue  # Still in cooldown period
                
                # Create alert trigger
                message = self._generate_alert_message(alert, current_value)
                
                alert_trigger = AlertTrigger(
                    alert_id=alert.alert_id,
                    metric_name=alert.metric_name,
                    current_value=current_value,
                    threshold_value=alert.threshold_value,
                    severity=alert.severity,
                    timestamp=current_time.isoformat(),
                    message=message,
                    notification_sent=False
                )
                
                triggered_alerts.append(alert_trigger)
                self.last_alert_times[alert.alert_id] = current_time
        
        return triggered_alerts
    
    def _generate_alert_message(self, alert: PerformanceAlert, current_value: float) -> str:
        """Generate alert message."""
        comparison_text = {
            "greater_than": "exceeded",
            "less_than": "fell below",
            "equals": "equals"
        }
        
        return (f"ALERT: {alert.metric_name} has {comparison_text.get(alert.comparison, 'triggered')} "
                f"threshold of {alert.threshold_value}. Current value: {current_value:.2f}")
    
    def send_notifications(self, alert_triggers: List[AlertTrigger]):
        """Send notifications for triggered alerts."""
        for alert_trigger in alert_triggers:
            alert_config = next((a for a in self.performance_alerts if a.alert_id == alert_trigger.alert_id), None)
            if not alert_config:
                continue
            
            print(f"🚨 ALERT: {alert_trigger.message}")
            
            # Send notifications based on configured channels
            notification_sent = False
            
            if "sns" in alert_config.notification_channels:
                notification_sent |= self._send_sns_notification(alert_trigger)
            
            if "email" in alert_config.notification_channels:
                notification_sent |= self._send_email_notification(alert_trigger)
            
            if "pagerduty" in alert_config.notification_channels:
                notification_sent |= self._send_pagerduty_notification(alert_trigger)
            
            alert_trigger.notification_sent = notification_sent
            self.alert_history.append(alert_trigger)
    
    def _send_sns_notification(self, alert_trigger: AlertTrigger) -> bool:
        """Send SNS notification."""
        try:
            topic_arn = "arn:aws:sns:us-east-1:123456789012:aquachain-performance-alerts"
            
            message = {
                "alert_id": alert_trigger.alert_id,
                "metric_name": alert_trigger.metric_name,
                "current_value": alert_trigger.current_value,
                "threshold_value": alert_trigger.threshold_value,
                "severity": alert_trigger.severity,
                "timestamp": alert_trigger.timestamp,
                "message": alert_trigger.message
            }
            
            self.sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message, indent=2),
                Subject=f"AquaChain Performance Alert: {alert_trigger.severity.upper()}"
            )
            
            print(f"  ✅ SNS notification sent for {alert_trigger.alert_id}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to send SNS notification: {e}")
            return False
    
    def _send_email_notification(self, alert_trigger: AlertTrigger) -> bool:
        """Send email notification."""
        try:
            # In a real implementation, this would use SES or another email service
            print(f"  📧 Email notification would be sent for {alert_trigger.alert_id}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to send email notification: {e}")
            return False
    
    def _send_pagerduty_notification(self, alert_trigger: AlertTrigger) -> bool:
        """Send PagerDuty notification."""
        try:
            # In a real implementation, this would integrate with PagerDuty API
            print(f"  📟 PagerDuty notification would be sent for {alert_trigger.alert_id}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to send PagerDuty notification: {e}")
            return False
    
    def publish_custom_metrics(self, metrics: List[PerformanceMetric]):
        """Publish custom metrics to CloudWatch."""
        try:
            metric_data = []
            
            for metric in metrics:
                metric_data.append({
                    'MetricName': metric.metric_name,
                    'Value': metric.value,
                    'Unit': metric.unit,
                    'Timestamp': datetime.fromisoformat(metric.timestamp.replace('Z', '+00:00')),
                    'Dimensions': [
                        {'Name': key, 'Value': value} 
                        for key, value in metric.dimensions.items()
                    ]
                })
            
            # Publish in batches of 20 (CloudWatch limit)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                
                self.cloudwatch.put_metric_data(
                    Namespace='AquaChain/Performance',
                    MetricData=batch
                )
            
            print(f"📊 Published {len(metrics)} custom metrics to CloudWatch")
            
        except Exception as e:
            print(f"❌ Failed to publish custom metrics: {e}")
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous performance monitoring."""
        print(f"🔄 Starting performance monitoring (interval: {interval_seconds}s)")
        self.monitoring_active = True
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    print(f"\n📊 Collecting metrics at {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Collect metrics
                    metrics = self.collect_performance_metrics()
                    print(f"   Collected {len(metrics)} metrics")
                    
                    # Publish to CloudWatch
                    if metrics:
                        self.publish_custom_metrics(metrics)
                    
                    # Evaluate alerts
                    alert_triggers = self.evaluate_alerts(metrics)
                    if alert_triggers:
                        print(f"   🚨 {len(alert_triggers)} alert(s) triggered")
                        self.send_notifications(alert_triggers)
                    else:
                        print("   ✅ No alerts triggered")
                    
                    # Wait for next interval
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    print(f"❌ Error in monitoring loop: {e}")
                    time.sleep(interval_seconds)
        
        # Start monitoring in background thread
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        return monitoring_thread
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        print("🛑 Stopping performance monitoring")
        self.monitoring_active = False
    
    def get_alert_history(self, hours_back: int = 24) -> List[AlertTrigger]:
        """Get alert history for specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')) > cutoff_time
        ]
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate performance monitoring report."""
        current_time = datetime.now(timezone.utc)
        
        # Get recent metrics
        recent_metrics = self.collect_performance_metrics()
        
        # Get alert history
        recent_alerts = self.get_alert_history(hours_back=24)
        
        # Calculate statistics
        alert_counts_by_severity = {}
        for alert in recent_alerts:
            severity = alert.severity
            alert_counts_by_severity[severity] = alert_counts_by_severity.get(severity, 0) + 1
        
        # Generate report
        report = {
            "timestamp": current_time.isoformat(),
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "current_metrics": [asdict(metric) for metric in recent_metrics],
            "alert_summary": {
                "total_alerts_24h": len(recent_alerts),
                "alerts_by_severity": alert_counts_by_severity,
                "most_recent_alert": recent_alerts[-1].timestamp if recent_alerts else None
            },
            "alert_configuration": {
                "total_alerts_configured": len(self.performance_alerts),
                "enabled_alerts": len([a for a in self.performance_alerts if a.enabled]),
                "critical_alerts": len([a for a in self.performance_alerts if a.severity == "critical"])
            },
            "system_health": self._assess_system_health(recent_metrics, recent_alerts)
        }
        
        return report
    
    def _assess_system_health(self, metrics: List[PerformanceMetric], 
                            alerts: List[AlertTrigger]) -> Dict[str, Any]:
        """Assess overall system health."""
        # Count recent critical alerts
        critical_alerts_1h = len([
            alert for alert in alerts
            if alert.severity == "critical" and
            datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')) > 
            datetime.now(timezone.utc) - timedelta(hours=1)
        ])
        
        # Assess health based on metrics and alerts
        if critical_alerts_1h > 0:
            health_status = "critical"
            health_score = 25
        elif len(alerts) > 10:  # Many alerts in 24h
            health_status = "degraded"
            health_score = 50
        elif len(alerts) > 5:
            health_status = "warning"
            health_score = 75
        else:
            health_status = "healthy"
            health_score = 95
        
        return {
            "status": health_status,
            "score": health_score,
            "critical_alerts_1h": critical_alerts_1h,
            "total_alerts_24h": len(alerts),
            "metrics_collected": len(metrics)
        }
    
    def print_monitoring_report(self, report: Dict[str, Any]):
        """Print formatted monitoring report."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE MONITORING REPORT")
        print("=" * 60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Monitoring Status: {report['monitoring_status'].upper()}")
        
        # System health
        health = report['system_health']
        health_icon = {
            "healthy": "✅",
            "warning": "⚠️",
            "degraded": "🟡",
            "critical": "🚨"
        }.get(health['status'], "❓")
        
        print(f"System Health: {health_icon} {health['status'].upper()} (Score: {health['score']}/100)")
        
        # Current metrics
        print(f"\n📈 Current Metrics:")
        print("-" * 40)
        for metric_data in report['current_metrics']:
            print(f"  {metric_data['metric_name']}: {metric_data['value']:.2f} {metric_data['unit']}")
        
        # Alert summary
        alert_summary = report['alert_summary']
        print(f"\n🚨 Alert Summary (24h):")
        print("-" * 40)
        print(f"  Total Alerts: {alert_summary['total_alerts_24h']}")
        
        for severity, count in alert_summary['alerts_by_severity'].items():
            severity_icon = {
                "critical": "🚨",
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(severity, "⚪")
            print(f"  {severity_icon} {severity.title()}: {count}")
        
        if alert_summary['most_recent_alert']:
            print(f"  Most Recent: {alert_summary['most_recent_alert']}")
        
        # Alert configuration
        alert_config = report['alert_configuration']
        print(f"\n⚙️  Alert Configuration:")
        print("-" * 40)
        print(f"  Total Configured: {alert_config['total_alerts_configured']}")
        print(f"  Enabled: {alert_config['enabled_alerts']}")
        print(f"  Critical: {alert_config['critical_alerts']}")

def main():
    """Main function to run performance monitoring."""
    parser = argparse.ArgumentParser(description='AquaChain Performance Monitor')
    parser.add_argument('--aws-region', type=str, default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Monitoring duration in seconds (default: 300)')
    parser.add_argument('--report-only', action='store_true', 
                       help='Generate report only, do not start monitoring')
    parser.add_argument('--output', type=str, 
                       help='Output report file (JSON format)')
    
    args = parser.parse_args()
    
    try:
        monitor = PerformanceMonitor(aws_region=args.aws_region)
        
        print("🔬 AquaChain Performance Monitor")
        print("=" * 50)
        
        if args.report_only:
            # Generate report only
            report = monitor.generate_monitoring_report()
            monitor.print_monitoring_report(report)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                print(f"\n📄 Report saved to: {args.output}")
        else:
            # Start monitoring
            monitoring_thread = monitor.start_monitoring(interval_seconds=args.interval)
            
            try:
                # Run for specified duration
                time.sleep(args.duration)
            except KeyboardInterrupt:
                print("\n⌨️  Monitoring interrupted by user")
            finally:
                monitor.stop_monitoring()
                
                # Generate final report
                print("\n📊 Generating final monitoring report...")
                report = monitor.generate_monitoring_report()
                monitor.print_monitoring_report(report)
                
                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(report, f, indent=2, default=str)
                    print(f"\n📄 Report saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"💥 Performance monitoring failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())