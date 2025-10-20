#!/usr/bin/env python3
"""
AquaChain Disaster Recovery Management Script
Manual disaster recovery operations and testing
"""

import argparse
import boto3
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

class DisasterRecoveryManager:
    """
    Manages disaster recovery operations for AquaChain system
    """
    
    def __init__(self, environment: str, region: str = 'us-east-1'):
        self.environment = environment
        self.region = region
        
        # Initialize AWS clients
        self.backup_client = boto3.client('backup', region_name=region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.stepfunctions_client = boto3.client('stepfunctions', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
        # Resource names
        self.backup_vault_name = f"aquachain-vault-main-{environment}"
        self.state_machine_name = f"aquachain-statemachine-disaster-recovery-{environment}"
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups
        """
        print(f"Listing backups for environment: {self.environment}")
        
        try:
            response = self.backup_client.list_backup_jobs(
                ByBackupVaultName=self.backup_vault_name,
                ByState='COMPLETED',
                MaxResults=50
            )
            
            backups = response.get('BackupJobs', [])
            
            if not backups:
                print("No completed backups found")
                return []
            
            print(f"\nFound {len(backups)} completed backups:")
            print("-" * 100)
            print(f"{'Resource Type':<15} {'Resource Name':<30} {'Creation Date':<20} {'Size (MB)':<12}")
            print("-" * 100)
            
            for backup in backups:
                resource_arn = backup.get('ResourceArn', '')
                resource_name = resource_arn.split('/')[-1] if '/' in resource_arn else resource_arn
                resource_type = backup.get('ResourceType', 'Unknown')
                creation_date = backup.get('CreationDate')
                size_bytes = backup.get('BackupSizeInBytes', 0)
                size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0
                
                creation_str = creation_date.strftime('%Y-%m-%d %H:%M') if creation_date else 'Unknown'
                
                print(f"{resource_type:<15} {resource_name:<30} {creation_str:<20} {size_mb:<12}")
            
            return backups
            
        except Exception as e:
            print(f"Error listing backups: {str(e)}")
            return []
    
    def validate_backups(self) -> bool:
        """
        Validate backup availability and recency
        """
        print(f"Validating backups for environment: {self.environment}")
        
        try:
            # Check for recent backups (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            response = self.backup_client.list_backup_jobs(
                ByBackupVaultName=self.backup_vault_name,
                ByState='COMPLETED',
                ByCreatedAfter=cutoff_time
            )
            
            recent_backups = response.get('BackupJobs', [])
            
            # Group by resource type
            backup_types = {}
            for backup in recent_backups:
                resource_type = backup.get('ResourceType')
                if resource_type not in backup_types:
                    backup_types[resource_type] = []
                backup_types[resource_type].append(backup)
            
            print(f"\nRecent backups (last 24 hours):")
            print(f"Found {len(recent_backups)} recent backups")
            
            required_types = ['DynamoDB', 'S3']
            missing_types = []
            
            for req_type in required_types:
                if req_type in backup_types:
                    count = len(backup_types[req_type])
                    print(f"✓ {req_type}: {count} recent backup(s)")
                else:
                    print(f"✗ {req_type}: No recent backups found")
                    missing_types.append(req_type)
            
            if missing_types:
                print(f"\nWARNING: Missing recent backups for: {missing_types}")
                return False
            
            print("\n✓ All required backup types have recent backups")
            return True
            
        except Exception as e:
            print(f"Error validating backups: {str(e)}")
            return False
    
    def run_dr_test(self) -> bool:
        """
        Run automated disaster recovery test using Step Functions
        """
        print(f"Starting DR test for environment: {self.environment}")
        
        try:
            # Get state machine ARN
            account_id = boto3.client('sts').get_caller_identity()['Account']
            state_machine_arn = f"arn:aws:states:{self.region}:{account_id}:stateMachine:{self.state_machine_name}"
            
            # Start execution
            execution_name = f"dr-test-{int(time.time())}"
            
            response = self.stepfunctions_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,
                input=json.dumps({
                    'operation': 'full_dr_test',
                    'environment': self.environment
                })
            )
            
            execution_arn = response['executionArn']
            print(f"Started DR test execution: {execution_name}")
            print(f"Execution ARN: {execution_arn}")
            
            # Monitor execution
            print("\nMonitoring execution progress...")
            
            while True:
                status_response = self.stepfunctions_client.describe_execution(
                    executionArn=execution_arn
                )
                
                status = status_response['status']
                
                if status == 'SUCCEEDED':
                    print("✓ DR test completed successfully!")
                    
                    # Get execution output
                    output = json.loads(status_response.get('output', '{}'))
                    self._print_dr_test_results(output)
                    return True
                    
                elif status == 'FAILED':
                    print("✗ DR test failed!")
                    
                    # Get error details
                    error = status_response.get('error', 'Unknown error')
                    cause = status_response.get('cause', 'Unknown cause')
                    print(f"Error: {error}")
                    print(f"Cause: {cause}")
                    return False
                    
                elif status == 'TIMED_OUT':
                    print("✗ DR test timed out!")
                    return False
                    
                elif status == 'ABORTED':
                    print("✗ DR test was aborted!")
                    return False
                
                # Still running
                print(f"Status: {status} - waiting...")
                time.sleep(30)
                
        except Exception as e:
            print(f"Error running DR test: {str(e)}")
            return False
    
    def _print_dr_test_results(self, results: Dict[str, Any]) -> None:
        """
        Print formatted DR test results
        """
        print("\n" + "="*60)
        print("DISASTER RECOVERY TEST RESULTS")
        print("="*60)
        
        print(f"Test ID: {results.get('test_id', 'Unknown')}")
        print(f"Environment: {results.get('environment', 'Unknown')}")
        print(f"Start Time: {results.get('start_time', 'Unknown')}")
        print(f"End Time: {results.get('end_time', 'Unknown')}")
        print(f"Overall Status: {results.get('status', 'Unknown')}")
        
        phases = results.get('phases', [])
        
        if phases:
            print(f"\nPhase Results ({len(phases)} phases):")
            print("-" * 40)
            
            for i, phase in enumerate(phases, 1):
                phase_name = phase.get('phase', 'Unknown')
                phase_result = phase.get('result', {})
                phase_status = phase_result.get('status', 'Unknown')
                phase_message = phase_result.get('message', 'No message')
                
                status_icon = "✓" if phase_status == 'success' else "✗"
                print(f"{i}. {phase_name}: {status_icon} {phase_status}")
                print(f"   Message: {phase_message}")
                
                if phase_status != 'success' and 'error' in phase_result:
                    print(f"   Error: {phase_result['error']}")
                
                print()
    
    def create_manual_backup(self, resource_arn: str) -> bool:
        """
        Create a manual backup of a specific resource
        """
        print(f"Creating manual backup for: {resource_arn}")
        
        try:
            backup_job_id = f"manual-backup-{int(time.time())}"
            
            response = self.backup_client.start_backup_job(
                BackupVaultName=self.backup_vault_name,
                ResourceArn=resource_arn,
                IamRoleArn=self._get_backup_role_arn(),
                IdempotencyToken=backup_job_id,
                StartWindowMinutes=60,
                CompleteWindowMinutes=120
            )
            
            job_id = response['BackupJobId']
            print(f"Backup job started: {job_id}")
            
            # Monitor backup progress
            print("Monitoring backup progress...")
            
            while True:
                job_response = self.backup_client.describe_backup_job(
                    BackupJobId=job_id
                )
                
                state = job_response['State']
                
                if state == 'COMPLETED':
                    print("✓ Backup completed successfully!")
                    
                    # Print backup details
                    backup_size = job_response.get('BackupSizeInBytes', 0)
                    size_mb = round(backup_size / (1024 * 1024), 2) if backup_size else 0
                    print(f"Backup size: {size_mb} MB")
                    
                    recovery_point_arn = job_response.get('RecoveryPointArn')
                    print(f"Recovery point ARN: {recovery_point_arn}")
                    
                    return True
                    
                elif state in ['FAILED', 'ABORTED', 'EXPIRED']:
                    print(f"✗ Backup failed with state: {state}")
                    
                    status_message = job_response.get('StatusMessage', 'No details available')
                    print(f"Status message: {status_message}")
                    
                    return False
                
                # Still running
                print(f"Status: {state} - waiting...")
                time.sleep(30)
                
        except Exception as e:
            print(f"Error creating manual backup: {str(e)}")
            return False
    
    def _get_backup_role_arn(self) -> str:
        """
        Get the backup service role ARN
        """
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"arn:aws:iam::{account_id}:role/aquachain-role-backup-service-{self.environment}"
    
    def get_dr_metrics(self, days: int = 7) -> None:
        """
        Get disaster recovery metrics from CloudWatch
        """
        print(f"Getting DR metrics for last {days} days")
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Get backup success/failure metrics
            metrics = [
                'RestoreTestSuccess',
                'RestoreTestFailure',
                'FullDRTestSuccess',
                'FullDRTestFailure',
                'RegionalOutageDetected',
                'FailoverInitiated',
                'FailoverFailed',
                'FailoverValidationSuccess',
                'FailoverRollback'
            ]
            
            print("\nDisaster Recovery Metrics:")
            print("-" * 50)
            
            for metric_name in metrics:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AquaChain/DisasterRecovery',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'Environment',
                            'Value': self.environment
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # Daily
                    Statistics=['Sum']
                )
                
                datapoints = response.get('Datapoints', [])
                total = sum(point['Sum'] for point in datapoints)
                
                print(f"{metric_name}: {int(total)}")
            
            # Calculate DR health score
            self._calculate_dr_health_score(start_time, end_time)
            
        except Exception as e:
            print(f"Error getting DR metrics: {str(e)}")
    
    def _calculate_dr_health_score(self, start_time: datetime, end_time: datetime) -> None:
        """
        Calculate and display DR health score
        """
        try:
            # Get backup success rate
            backup_success = self._get_metric_sum('RestoreTestSuccess', start_time, end_time)
            backup_failure = self._get_metric_sum('RestoreTestFailure', start_time, end_time)
            backup_total = backup_success + backup_failure
            backup_success_rate = (backup_success / backup_total * 100) if backup_total > 0 else 100
            
            # Get DR test success rate
            dr_success = self._get_metric_sum('FullDRTestSuccess', start_time, end_time)
            dr_failure = self._get_metric_sum('FullDRTestFailure', start_time, end_time)
            dr_total = dr_success + dr_failure
            dr_success_rate = (dr_success / dr_total * 100) if dr_total > 0 else 100
            
            # Get failover metrics
            failover_initiated = self._get_metric_sum('FailoverInitiated', start_time, end_time)
            failover_failed = self._get_metric_sum('FailoverFailed', start_time, end_time)
            
            print(f"\nDR Health Score:")
            print("-" * 30)
            print(f"Backup Success Rate: {backup_success_rate:.1f}% ({backup_success}/{backup_total})")
            print(f"DR Test Success Rate: {dr_success_rate:.1f}% ({dr_success}/{dr_total})")
            print(f"Failover Events: {int(failover_initiated)} initiated, {int(failover_failed)} failed")
            
            # Overall health score (weighted average)
            overall_score = (backup_success_rate * 0.4 + dr_success_rate * 0.6)
            print(f"Overall DR Health Score: {overall_score:.1f}%")
            
            # Health status
            if overall_score >= 95:
                print("Status: ✓ EXCELLENT")
            elif overall_score >= 85:
                print("Status: ✓ GOOD")
            elif overall_score >= 70:
                print("Status: ⚠ NEEDS ATTENTION")
            else:
                print("Status: ✗ CRITICAL")
                
        except Exception as e:
            print(f"Error calculating DR health score: {str(e)}")
    
    def _get_metric_sum(self, metric_name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Get sum of metric values for time period
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AquaChain/DisasterRecovery',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'Environment',
                        'Value': self.environment
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            return sum(point['Sum'] for point in datapoints)
            
        except Exception:
            return 0.0
    
    def test_failover_system(self) -> bool:
        """
        Test the automated failover system
        """
        print(f"Testing automated failover system for environment: {self.environment}")
        
        try:
            # Get failover state machine ARN
            account_id = boto3.client('sts').get_caller_identity()['Account']
            failover_state_machine_name = f"aquachain-statemachine-automated-failover-{self.environment}"
            state_machine_arn = f"arn:aws:states:{self.region}:{account_id}:stateMachine:{failover_state_machine_name}"
            
            # Start test execution
            execution_name = f"failover-test-{int(time.time())}"
            
            response = self.stepfunctions_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,
                input=json.dumps({
                    'operation': 'assess_outage',
                    'environment': self.environment,
                    'test_mode': True
                })
            )
            
            execution_arn = response['executionArn']
            print(f"Started failover test execution: {execution_name}")
            print(f"Execution ARN: {execution_arn}")
            
            # Monitor execution (shorter timeout for test)
            print("\nMonitoring test execution...")
            
            max_wait_time = 300  # 5 minutes for test
            wait_time = 0
            
            while wait_time < max_wait_time:
                status_response = self.stepfunctions_client.describe_execution(
                    executionArn=execution_arn
                )
                
                status = status_response['status']
                
                if status == 'SUCCEEDED':
                    print("✓ Failover system test completed successfully!")
                    
                    # Get execution output
                    output = json.loads(status_response.get('output', '{}'))
                    self._print_failover_test_results(output)
                    return True
                    
                elif status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
                    print(f"✗ Failover system test failed with status: {status}")
                    
                    # Get error details
                    error = status_response.get('error', 'Unknown error')
                    cause = status_response.get('cause', 'Unknown cause')
                    print(f"Error: {error}")
                    print(f"Cause: {cause}")
                    return False
                
                # Still running
                print(f"Status: {status} - waiting...")
                time.sleep(15)
                wait_time += 15
            
            print("✗ Failover system test timed out!")
            return False
                
        except Exception as e:
            print(f"Error testing failover system: {str(e)}")
            return False
    
    def _print_failover_test_results(self, results: Dict[str, Any]) -> None:
        """
        Print formatted failover test results
        """
        print("\n" + "="*60)
        print("FAILOVER SYSTEM TEST RESULTS")
        print("="*60)
        
        print(f"Test Environment: {results.get('environment', 'Unknown')}")
        print(f"Assessment Time: {results.get('assessment_time', 'Unknown')}")
        print(f"Health Score: {results.get('health_score', 'Unknown')}")
        print(f"Status: {results.get('status', 'Unknown')}")
        
        checks = results.get('checks', [])
        if checks:
            print(f"\nService Health Checks ({len(checks)} services):")
            print("-" * 40)
            
            for check in checks:
                service = check.get('service', 'Unknown')
                status = check.get('status', 'Unknown')
                details = check.get('details', 'No details')
                
                status_icon = "✓" if status == 'healthy' else "⚠" if status == 'warning' else "✗"
                print(f"{status_icon} {service}: {status}")
                print(f"   {details}")
                print()
    
    def generate_dr_report(self, output_file: str = None) -> bool:
        """
        Generate comprehensive DR report
        """
        print(f"Generating DR report for environment: {self.environment}")
        
        try:
            report_data = {
                'report_generated': datetime.utcnow().isoformat(),
                'environment': self.environment,
                'region': self.region
            }
            
            # Get backup information
            print("Gathering backup information...")
            backups = self.list_backups()
            report_data['backup_summary'] = {
                'total_backups': len(backups),
                'recent_backups': len([b for b in backups if self._is_recent_backup(b)]),
                'backup_types': self._categorize_backups(backups)
            }
            
            # Get DR metrics
            print("Gathering DR metrics...")
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            metrics_data = {}
            for metric in ['RestoreTestSuccess', 'RestoreTestFailure', 'FullDRTestSuccess', 'FullDRTestFailure']:
                metrics_data[metric] = self._get_metric_sum(metric, start_time, end_time)
            
            report_data['metrics'] = metrics_data
            
            # Calculate compliance scores
            report_data['compliance'] = self._calculate_compliance_scores(metrics_data)
            
            # Generate report
            report_content = self._format_dr_report(report_data)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report_content)
                print(f"✓ DR report saved to: {output_file}")
            else:
                print("\n" + "="*80)
                print("DISASTER RECOVERY REPORT")
                print("="*80)
                print(report_content)
            
            return True
            
        except Exception as e:
            print(f"Error generating DR report: {str(e)}")
            return False
    
    def _is_recent_backup(self, backup: Dict[str, Any]) -> bool:
        """
        Check if backup is recent (within last 48 hours)
        """
        try:
            creation_date = backup.get('CreationDate')
            if creation_date:
                cutoff_time = datetime.utcnow() - timedelta(hours=48)
                return creation_date > cutoff_time
            return False
        except Exception:
            return False
    
    def _categorize_backups(self, backups: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Categorize backups by resource type
        """
        categories = {}
        for backup in backups:
            resource_type = backup.get('ResourceType', 'Unknown')
            categories[resource_type] = categories.get(resource_type, 0) + 1
        return categories
    
    def _calculate_compliance_scores(self, metrics_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate compliance scores based on metrics
        """
        # Backup test compliance (target: 95% success rate)
        backup_success = metrics_data.get('RestoreTestSuccess', 0)
        backup_failure = metrics_data.get('RestoreTestFailure', 0)
        backup_total = backup_success + backup_failure
        backup_compliance = (backup_success / backup_total * 100) if backup_total > 0 else 100
        
        # DR test compliance (target: 90% success rate)
        dr_success = metrics_data.get('FullDRTestSuccess', 0)
        dr_failure = metrics_data.get('FullDRTestFailure', 0)
        dr_total = dr_success + dr_failure
        dr_compliance = (dr_success / dr_total * 100) if dr_total > 0 else 100
        
        return {
            'backup_test_compliance': {
                'score': backup_compliance,
                'target': 95.0,
                'status': 'PASS' if backup_compliance >= 95 else 'FAIL'
            },
            'dr_test_compliance': {
                'score': dr_compliance,
                'target': 90.0,
                'status': 'PASS' if dr_compliance >= 90 else 'FAIL'
            }
        }
    
    def _format_dr_report(self, report_data: Dict[str, Any]) -> str:
        """
        Format DR report as readable text
        """
        report = []
        
        report.append(f"Environment: {report_data['environment']}")
        report.append(f"Region: {report_data['region']}")
        report.append(f"Report Generated: {report_data['report_generated']}")
        report.append("")
        
        # Backup Summary
        backup_summary = report_data['backup_summary']
        report.append("BACKUP SUMMARY")
        report.append("-" * 20)
        report.append(f"Total Backups: {backup_summary['total_backups']}")
        report.append(f"Recent Backups (48h): {backup_summary['recent_backups']}")
        report.append("Backup Types:")
        for backup_type, count in backup_summary['backup_types'].items():
            report.append(f"  {backup_type}: {count}")
        report.append("")
        
        # Metrics Summary
        metrics = report_data['metrics']
        report.append("METRICS SUMMARY (Last 30 Days)")
        report.append("-" * 30)
        for metric, value in metrics.items():
            report.append(f"{metric}: {int(value)}")
        report.append("")
        
        # Compliance Scores
        compliance = report_data['compliance']
        report.append("COMPLIANCE SCORES")
        report.append("-" * 20)
        for test_type, data in compliance.items():
            status_icon = "✓" if data['status'] == 'PASS' else "✗"
            report.append(f"{status_icon} {test_type}: {data['score']:.1f}% (Target: {data['target']:.1f}%)")
        report.append("")
        
        return "\n".join(report)

def main():
    """
    Main CLI entry point
    """
    parser = argparse.ArgumentParser(description='AquaChain Disaster Recovery Management')
    parser.add_argument('--environment', '-e', required=True, 
                       choices=['dev', 'staging', 'prod'],
                       help='Environment to operate on')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List backups command
    subparsers.add_parser('list-backups', help='List all available backups')
    
    # Validate backups command
    subparsers.add_parser('validate-backups', help='Validate backup availability and recency')
    
    # Run DR test command
    subparsers.add_parser('run-dr-test', help='Run automated disaster recovery test')
    
    # Manual backup command
    backup_parser = subparsers.add_parser('create-backup', help='Create manual backup')
    backup_parser.add_argument('--resource-arn', required=True,
                              help='ARN of resource to backup')
    
    # Get metrics command
    metrics_parser = subparsers.add_parser('get-metrics', help='Get DR metrics')
    metrics_parser.add_argument('--days', type=int, default=7,
                               help='Number of days to look back (default: 7)')
    
    # Test failover system command
    subparsers.add_parser('test-failover', help='Test automated failover system')
    
    # Generate DR report command
    report_parser = subparsers.add_parser('generate-report', help='Generate comprehensive DR report')
    report_parser.add_argument('--output', '-o', help='Output file path (default: print to console)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize DR manager
    dr_manager = DisasterRecoveryManager(args.environment, args.region)
    
    # Execute command
    success = True
    
    if args.command == 'list-backups':
        dr_manager.list_backups()
    elif args.command == 'validate-backups':
        success = dr_manager.validate_backups()
    elif args.command == 'run-dr-test':
        success = dr_manager.run_dr_test()
    elif args.command == 'create-backup':
        success = dr_manager.create_manual_backup(args.resource_arn)
    elif args.command == 'get-metrics':
        dr_manager.get_dr_metrics(args.days)
    elif args.command == 'test-failover':
        success = dr_manager.test_failover_system()
    elif args.command == 'generate-report':
        success = dr_manager.generate_dr_report(args.output)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()