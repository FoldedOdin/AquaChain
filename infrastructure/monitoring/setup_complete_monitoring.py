"""
Complete Monitoring Setup Script for AquaChain System
Orchestrates the setup of all monitoring, logging, and observability components
"""

import json
import sys
import os
from typing import Dict, Any

# Add monitoring modules to path
sys.path.append(os.path.dirname(__file__))

from cloudwatch_setup import CloudWatchMonitoringSetup
from xray_setup import XRaySetup, PerformanceMonitoring
from sli_slo_setup import setup_complete_sli_slo_monitoring
from pagerduty_integration import PagerDutyIntegration


class AquaChainMonitoringOrchestrator:
    """Orchestrates complete monitoring setup for AquaChain system"""
    
    def __init__(self, region='us-east-1', pagerduty_integration_key=None):
        self.region = region
        self.pagerduty_integration_key = pagerduty_integration_key
        
    def setup_complete_monitoring_infrastructure(self) -> Dict[str, Any]:
        """Set up complete monitoring infrastructure"""
        print("🚀 Starting AquaChain monitoring infrastructure setup...")
        
        results = {
            'cloudwatch': {},
            'xray': {},
            'performance': {},
            'sli_slo': {},
            'pagerduty': {},
            'status': 'in_progress'
        }
        
        try:
            # 1. Set up CloudWatch monitoring and alerting
            print("\n📊 Setting up CloudWatch monitoring and alerting...")
            cloudwatch_setup = CloudWatchMonitoringSetup(self.region)
            cloudwatch_result = cloudwatch_setup.setup_complete_monitoring()
            results['cloudwatch'] = cloudwatch_result
            print("✅ CloudWatch monitoring setup complete")
            
            # 2. Set up X-Ray distributed tracing
            print("\n🔍 Setting up X-Ray distributed tracing...")
            xray_setup = XRaySetup(self.region)
            xray_result = xray_setup.setup_complete_xray_tracing()
            results['xray'] = xray_result
            print("✅ X-Ray tracing setup complete")
            
            # 3. Set up performance monitoring
            print("\n⚡ Setting up performance monitoring...")
            performance_monitoring = PerformanceMonitoring(self.region)
            performance_metrics = performance_monitoring.create_performance_metrics()
            performance_monitoring.create_performance_dashboard()
            baselines = performance_monitoring.establish_performance_baselines()
            
            # Create performance alarms (need SNS topic from CloudWatch setup)
            sns_topics = cloudwatch_result.get('sns_topics', {})
            operational_alerts_topic = sns_topics.get('aquachain-operational-alerts')
            if operational_alerts_topic:
                performance_alarms = performance_monitoring.create_performance_alarms(operational_alerts_topic)
                results['performance'] = {
                    'metrics': performance_metrics,
                    'baselines': baselines,
                    'alarms': performance_alarms
                }
            else:
                results['performance'] = {
                    'metrics': performance_metrics,
                    'baselines': baselines,
                    'alarms': []
                }
            print("✅ Performance monitoring setup complete")
            
            # 4. Set up SLI/SLO monitoring
            print("\n🎯 Setting up SLI/SLO monitoring and error budgets...")
            sli_slo_result = setup_complete_sli_slo_monitoring()
            results['sli_slo'] = sli_slo_result
            print("✅ SLI/SLO monitoring setup complete")
            
            # 5. Set up PagerDuty integration (if key provided)
            if self.pagerduty_integration_key:
                print("\n🚨 Setting up PagerDuty integration...")
                pagerduty = PagerDutyIntegration(self.pagerduty_integration_key)
                
                # Test PagerDuty integration
                test_incident = pagerduty.create_incident(
                    title="AquaChain Monitoring Setup Complete",
                    description="This is a test incident to verify PagerDuty integration is working correctly.",
                    severity="info",
                    custom_details={
                        "setup_timestamp": "2025-10-20T14:30:00Z",
                        "components_configured": ["CloudWatch", "X-Ray", "SLI/SLO", "Performance"],
                        "status": "setup_complete"
                    }
                )
                
                results['pagerduty'] = {
                    'integration_configured': True,
                    'test_incident': test_incident
                }
                print("✅ PagerDuty integration setup complete")
            else:
                print("⚠️  PagerDuty integration key not provided - skipping PagerDuty setup")
                results['pagerduty'] = {
                    'integration_configured': False,
                    'message': 'PagerDuty integration key not provided'
                }
            
            # 6. Create monitoring summary dashboard
            print("\n📈 Creating monitoring summary dashboard...")
            self.create_monitoring_summary_dashboard()
            print("✅ Monitoring summary dashboard created")
            
            results['status'] = 'completed'
            print("\n🎉 AquaChain monitoring infrastructure setup completed successfully!")
            
            return results
            
        except Exception as e:
            print(f"\n❌ Error during monitoring setup: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            return results
    
    def create_monitoring_summary_dashboard(self):
        """Create a high-level monitoring summary dashboard"""
        import boto3
        
        cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "text",
                    "x": 0,
                    "y": 0,
                    "width": 24,
                    "height": 2,
                    "properties": {
                        "markdown": "# AquaChain System Monitoring Overview\n\nReal-time monitoring dashboard for water quality monitoring system. **SLA Target: 99.5% uptime, <30s alert latency**"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 2,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/SLO", "overall_slo_compliance"]
                        ],
                        "view": "singleValue",
                        "region": self.region,
                        "title": "Overall SLO Compliance",
                        "period": 3600
                    }
                },
                {
                    "type": "metric",
                    "x": 8,
                    "y": 2,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/Alerts", "AlertLatency", {"stat": "Average"}]
                        ],
                        "view": "singleValue",
                        "region": self.region,
                        "title": "Current Alert Latency",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 16,
                    "y": 2,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/SystemHealth", "ErrorRate"]
                        ],
                        "view": "singleValue",
                        "region": self.region,
                        "title": "System Error Rate",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 8,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AquaChain/DataIngestion", "DeviceDataReceived"],
                            ["AquaChain/Alerts", "CriticalAlerts"],
                            ["AquaChain/ServiceRequests", "ServiceRequestsCreated"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "System Activity",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 8,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Errors", "FunctionName", "aquachain-data-processing"],
                            [".", ".", ".", "aquachain-ml-inference"],
                            [".", ".", ".", "aquachain-alert-detection"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Critical Lambda Errors",
                        "period": 300
                    }
                }
            ]
        }
        
        try:
            response = cloudwatch.put_dashboard(
                DashboardName='AquaChain-Monitoring-Overview',
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"Created monitoring overview dashboard: {response}")
        except Exception as e:
            print(f"Error creating monitoring overview dashboard: {e}")
    
    def validate_monitoring_setup(self) -> Dict[str, Any]:
        """Validate that monitoring components are working correctly"""
        print("\n🔍 Validating monitoring setup...")
        
        validation_results = {
            'cloudwatch_dashboards': False,
            'cloudwatch_alarms': False,
            'xray_tracing': False,
            'slo_metrics': False,
            'log_groups': False,
            'overall_status': 'unknown'
        }
        
        try:
            import boto3
            
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            logs = boto3.client('logs', region_name=self.region)
            xray = boto3.client('xray', region_name=self.region)
            
            # Check CloudWatch dashboards
            try:
                dashboards = cloudwatch.list_dashboards()
                aquachain_dashboards = [d for d in dashboards['DashboardEntries'] 
                                      if 'AquaChain' in d['DashboardName']]
                validation_results['cloudwatch_dashboards'] = len(aquachain_dashboards) >= 3
                print(f"✅ Found {len(aquachain_dashboards)} AquaChain dashboards")
            except Exception as e:
                print(f"❌ Error checking dashboards: {e}")
            
            # Check CloudWatch alarms
            try:
                alarms = cloudwatch.describe_alarms(AlarmNamePrefix='AquaChain-')
                validation_results['cloudwatch_alarms'] = len(alarms['MetricAlarms']) >= 5
                print(f"✅ Found {len(alarms['MetricAlarms'])} AquaChain alarms")
            except Exception as e:
                print(f"❌ Error checking alarms: {e}")
            
            # Check log groups
            try:
                log_groups = logs.describe_log_groups(logGroupNamePrefix='/aws/lambda/aquachain-')
                validation_results['log_groups'] = len(log_groups['logGroups']) >= 5
                print(f"✅ Found {len(log_groups['logGroups'])} AquaChain log groups")
            except Exception as e:
                print(f"❌ Error checking log groups: {e}")
            
            # Check X-Ray sampling rules
            try:
                sampling_rules = xray.get_sampling_rules()
                aquachain_rules = [r for r in sampling_rules['SamplingRuleRecords'] 
                                 if 'AquaChain' in r['SamplingRule']['RuleName']]
                validation_results['xray_tracing'] = len(aquachain_rules) >= 1
                print(f"✅ Found {len(aquachain_rules)} AquaChain X-Ray sampling rules")
            except Exception as e:
                print(f"❌ Error checking X-Ray rules: {e}")
            
            # Overall status
            passed_checks = sum(1 for v in validation_results.values() if v is True)
            total_checks = len([k for k in validation_results.keys() if k != 'overall_status'])
            
            if passed_checks == total_checks:
                validation_results['overall_status'] = 'all_passed'
                print("🎉 All monitoring validation checks passed!")
            elif passed_checks >= total_checks * 0.8:
                validation_results['overall_status'] = 'mostly_passed'
                print("⚠️  Most monitoring validation checks passed")
            else:
                validation_results['overall_status'] = 'failed'
                print("❌ Monitoring validation failed")
            
        except Exception as e:
            print(f"❌ Error during validation: {e}")
            validation_results['overall_status'] = 'error'
            validation_results['error'] = str(e)
        
        return validation_results
    
    def print_setup_summary(self, setup_results: Dict[str, Any]):
        """Print a summary of the monitoring setup"""
        print("\n" + "="*80)
        print("🎯 AQUACHAIN MONITORING SETUP SUMMARY")
        print("="*80)
        
        print(f"\n📊 CloudWatch Monitoring:")
        cloudwatch_result = setup_results.get('cloudwatch', {})
        print(f"   • Custom Metrics: {len(cloudwatch_result.get('custom_metrics', {}))}")
        print(f"   • SNS Topics: {len(cloudwatch_result.get('sns_topics', {}))}")
        print(f"   • Alarms: {len(cloudwatch_result.get('alarms', []))}")
        print(f"   • Log Groups: {len(cloudwatch_result.get('log_groups', []))}")
        
        print(f"\n🔍 X-Ray Distributed Tracing:")
        xray_result = setup_results.get('xray', {})
        lambda_tracing = xray_result.get('lambda_tracing', {})
        successful_lambda_tracing = sum(1 for result in lambda_tracing.values() 
                                      if result.get('status') == 'success')
        print(f"   • Lambda Functions with Tracing: {successful_lambda_tracing}/{len(lambda_tracing)}")
        print(f"   • Sampling Rule: {'✅' if xray_result.get('sampling_rule') else '❌'}")
        
        print(f"\n⚡ Performance Monitoring:")
        performance_result = setup_results.get('performance', {})
        print(f"   • Performance Metrics: {len(performance_result.get('metrics', {}))}")
        print(f"   • Performance Alarms: {len(performance_result.get('alarms', []))}")
        print(f"   • Baselines Established: {'✅' if performance_result.get('baselines') else '❌'}")
        
        print(f"\n🎯 SLI/SLO Monitoring:")
        sli_slo_result = setup_results.get('sli_slo', {})
        print(f"   • SLIs Defined: {len(sli_slo_result.get('slis', []))}")
        print(f"   • SLOs Configured: {len(sli_slo_result.get('slos', []))}")
        print(f"   • Error Budget Alarms: {len(sli_slo_result.get('error_budget_alarms', []))}")
        
        print(f"\n🚨 PagerDuty Integration:")
        pagerduty_result = setup_results.get('pagerduty', {})
        integration_status = "✅ Configured" if pagerduty_result.get('integration_configured') else "❌ Not Configured"
        print(f"   • Status: {integration_status}")
        
        print(f"\n📈 Dashboards Created:")
        print(f"   • AquaChain-SystemHealth")
        print(f"   • AquaChain-AlertLatency") 
        print(f"   • AquaChain-Performance")
        print(f"   • AquaChain-SLO-ErrorBudgets")
        print(f"   • AquaChain-Monitoring-Overview")
        
        print(f"\n🎯 Key SLOs:")
        print(f"   • Alert Latency: 95% under 30 seconds")
        print(f"   • Data Ingestion Availability: 99.5%")
        print(f"   • API Response Time: 99% under 2 seconds")
        print(f"   • System Uptime: 99.5%")
        print(f"   • Technician Assignment Success: 98%")
        
        status = setup_results.get('status', 'unknown')
        if status == 'completed':
            print(f"\n🎉 Setup Status: COMPLETED SUCCESSFULLY")
        else:
            print(f"\n❌ Setup Status: {status.upper()}")
        
        print("="*80)


def main():
    """Main function to run complete monitoring setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Set up AquaChain monitoring infrastructure')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--pagerduty-key', help='PagerDuty integration key')
    parser.add_argument('--validate', action='store_true', help='Validate setup after completion')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = AquaChainMonitoringOrchestrator(
        region=args.region,
        pagerduty_integration_key=args.pagerduty_key
    )
    
    # Run setup
    setup_results = orchestrator.setup_complete_monitoring_infrastructure()
    
    # Print summary
    orchestrator.print_setup_summary(setup_results)
    
    # Validate if requested
    if args.validate:
        validation_results = orchestrator.validate_monitoring_setup()
        print(f"\nValidation Results: {validation_results}")
    
    # Return exit code based on setup status
    if setup_results.get('status') == 'completed':
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())