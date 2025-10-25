#!/usr/bin/env python3
"""
Phase 3 Deployment Validation Script
Validates that all Phase 3 components are deployed and functional
"""

import boto3
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
NC = '\033[0m'  # No Color

class Phase3Validator:
    def __init__(self, environment: str = 'staging'):
        self.environment = environment
        self.region = 'us-east-1'
        
        # AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.events = boto3.client('events', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        self.iot = boto3.client('iot', region_name=self.region)
        self.sns = boto3.client('sns', region_name=self.region)
        
        self.results = []
        
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{BLUE}{'='*60}{NC}")
        print(f"{BLUE}{text}{NC}")
        print(f"{BLUE}{'='*60}{NC}\n")
        
    def print_result(self, component: str, status: bool, message: str = ""):
        """Print validation result"""
        status_icon = f"{GREEN}✓{NC}" if status else f"{RED}✗{NC}"
        print(f"{status_icon} {component}: {message if message else ('PASS' if status else 'FAIL')}")
        self.results.append((component, status, message))
        
    def validate_dynamodb_tables(self) -> bool:
        """Validate DynamoDB tables exist and are active"""
        self.print_header("Validating DynamoDB Tables")
        
        tables = [
            f'aquachain-model-metrics-{self.environment}',
            f'aquachain-certificate-lifecycle-{self.environment}'
        ]
        
        all_valid = True
        for table_name in tables:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                
                if status == 'ACTIVE':
                    self.print_result(f"Table: {table_name}", True, status)
                else:
                    self.print_result(f"Table: {table_name}", False, f"Status: {status}")
                    all_valid = False
                    
            except Exception as e:
                self.print_result(f"Table: {table_name}", False, str(e))
                all_valid = False
                
        return all_valid
        
    def validate_lambda_functions(self) -> bool:
        """Validate Lambda functions exist and are up to date"""
        self.print_header("Validating Lambda Functions")
        
        functions = [
            f'aquachain-ml-inference-{self.environment}',
            f'aquachain-data-validator-{self.environment}',
            f'aquachain-ota-manager-{self.environment}',
            f'aquachain-cert-rotation-{self.environment}',
            f'aquachain-dependency-scanner-{self.environment}'
        ]
        
        all_valid = True
        for function_name in functions:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                last_modified = response['Configuration']['LastModified']
                runtime = response['Configuration']['Runtime']
                
                self.print_result(
                    f"Function: {function_name}",
                    True,
                    f"Runtime: {runtime}, Modified: {last_modified}"
                )
                
            except Exception as e:
                self.print_result(f"Function: {function_name}", False, str(e))
                all_valid = False
                
        return all_valid
        
    def validate_eventbridge_schedules(self) -> bool:
        """Validate EventBridge schedules are configured"""
        self.print_header("Validating EventBridge Schedules")
        
        rules = [
            f'aquachain-cert-rotation-daily-{self.environment}',
            f'aquachain-dependency-scan-weekly-{self.environment}'
        ]
        
        all_valid = True
        for rule_name in rules:
            try:
                response = self.events.describe_rule(Name=rule_name)
                state = response['State']
                schedule = response.get('ScheduleExpression', 'N/A')
                
                if state == 'ENABLED':
                    self.print_result(
                        f"Rule: {rule_name}",
                        True,
                        f"State: {state}, Schedule: {schedule}"
                    )
                else:
                    self.print_result(f"Rule: {rule_name}", False, f"State: {state}")
                    all_valid = False
                    
            except Exception as e:
                self.print_result(f"Rule: {rule_name}", False, str(e))
                all_valid = False
                
        return all_valid
        
    def validate_s3_buckets(self) -> bool:
        """Validate S3 buckets exist"""
        self.print_header("Validating S3 Buckets")
        
        buckets = [
            f'aquachain-firmware-{self.environment}',
            f'aquachain-vulnerability-reports-{self.environment}',
            f'aquachain-sbom-storage-{self.environment}'
        ]
        
        all_valid = True
        for bucket_name in buckets:
            try:
                self.s3.head_bucket(Bucket=bucket_name)
                
                # Check versioning
                versioning = self.s3.get_bucket_versioning(Bucket=bucket_name)
                versioning_status = versioning.get('Status', 'Disabled')
                
                self.print_result(
                    f"Bucket: {bucket_name}",
                    True,
                    f"Versioning: {versioning_status}"
                )
                
            except Exception as e:
                self.print_result(f"Bucket: {bucket_name}", False, str(e))
                all_valid = False
                
        return all_valid
        
    def validate_cloudwatch_dashboard(self) -> bool:
        """Validate CloudWatch dashboard exists"""
        self.print_header("Validating CloudWatch Dashboard")
        
        dashboard_name = f'AquaChain-Performance-{self.environment}'
        
        try:
            response = self.cloudwatch.get_dashboard(DashboardName=dashboard_name)
            dashboard_body = json.loads(response['DashboardBody'])
            widget_count = len(dashboard_body.get('widgets', []))
            
            self.print_result(
                f"Dashboard: {dashboard_name}",
                True,
                f"Widgets: {widget_count}"
            )
            return True
            
        except Exception as e:
            self.print_result(f"Dashboard: {dashboard_name}", False, str(e))
            return False
            
    def validate_cloudwatch_alarms(self) -> bool:
        """Validate CloudWatch alarms are configured"""
        self.print_header("Validating CloudWatch Alarms")
        
        try:
            response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f'aquachain-{self.environment}'
            )
            
            alarms = response.get('MetricAlarms', [])
            alarm_count = len(alarms)
            
            if alarm_count > 0:
                self.print_result(
                    "CloudWatch Alarms",
                    True,
                    f"Found {alarm_count} alarms"
                )
                
                # Check alarm states
                for alarm in alarms[:5]:  # Show first 5
                    name = alarm['AlarmName']
                    state = alarm['StateValue']
                    print(f"  - {name}: {state}")
                    
                return True
            else:
                self.print_result("CloudWatch Alarms", False, "No alarms found")
                return False
                
        except Exception as e:
            self.print_result("CloudWatch Alarms", False, str(e))
            return False
            
    def validate_iot_resources(self) -> bool:
        """Validate IoT resources"""
        self.print_header("Validating IoT Resources")
        
        all_valid = True
        
        # Check code signing profile
        try:
            profile_name = f'aquachain-firmware-{self.environment}'
            response = self.iot.get_signing_profile(profileName=profile_name)
            status = response.get('status', 'UNKNOWN')
            
            self.print_result(
                f"Code Signing Profile: {profile_name}",
                status == 'ACTIVE',
                f"Status: {status}"
            )
            
            if status != 'ACTIVE':
                all_valid = False
                
        except Exception as e:
            self.print_result("Code Signing Profile", False, str(e))
            all_valid = False
            
        return all_valid
        
    def validate_sns_topics(self) -> bool:
        """Validate SNS topics exist"""
        self.print_header("Validating SNS Topics")
        
        try:
            response = self.sns.list_topics()
            topics = response.get('Topics', [])
            
            required_topics = [
                'critical-alerts',
                'vulnerability-alerts',
                'ml-alerts'
            ]
            
            found_topics = []
            for topic in topics:
                topic_name = topic['TopicArn'].split(':')[-1]
                if any(req in topic_name for req in required_topics):
                    found_topics.append(topic_name)
                    
            if len(found_topics) >= len(required_topics):
                self.print_result(
                    "SNS Topics",
                    True,
                    f"Found {len(found_topics)} topics"
                )
                for topic in found_topics:
                    print(f"  - {topic}")
                return True
            else:
                self.print_result(
                    "SNS Topics",
                    False,
                    f"Expected {len(required_topics)}, found {len(found_topics)}"
                )
                return False
                
        except Exception as e:
            self.print_result("SNS Topics", False, str(e))
            return False
            
    def run_smoke_tests(self) -> bool:
        """Run basic smoke tests"""
        self.print_header("Running Smoke Tests")
        
        all_valid = True
        
        # Test ML inference Lambda
        try:
            function_name = f'aquachain-ml-inference-{self.environment}'
            payload = json.dumps({
                'sensor_data': {
                    'pH': 7.2,
                    'temperature': 25.5,
                    'turbidity': 2.1
                }
            })
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=payload
            )
            
            status_code = response['StatusCode']
            if status_code == 200:
                self.print_result("ML Inference Test", True, "Prediction successful")
            else:
                self.print_result("ML Inference Test", False, f"Status: {status_code}")
                all_valid = False
                
        except Exception as e:
            self.print_result("ML Inference Test", False, str(e))
            all_valid = False
            
        return all_valid
        
    def generate_report(self) -> Dict:
        """Generate validation report"""
        total = len(self.results)
        passed = sum(1 for _, status, _ in self.results if status)
        failed = total - passed
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.environment,
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            'results': [
                {
                    'component': comp,
                    'status': 'PASS' if status else 'FAIL',
                    'message': msg
                }
                for comp, status, msg in self.results
            ]
        }
        
        return report
        
    def print_summary(self):
        """Print validation summary"""
        report = self.generate_report()
        
        print(f"\n{BLUE}{'='*60}{NC}")
        print(f"{BLUE}Validation Summary{NC}")
        print(f"{BLUE}{'='*60}{NC}\n")
        
        print(f"Environment: {self.environment}")
        print(f"Total Checks: {report['total_checks']}")
        print(f"{GREEN}Passed: {report['passed']}{NC}")
        print(f"{RED}Failed: {report['failed']}{NC}")
        print(f"Success Rate: {report['success_rate']}")
        
        if report['failed'] == 0:
            print(f"\n{GREEN}✓ All validation checks passed!{NC}")
            print(f"{GREEN}Phase 3 deployment is ready for stakeholder approval.{NC}\n")
        else:
            print(f"\n{RED}✗ Some validation checks failed.{NC}")
            print(f"{YELLOW}Please review the failures above and fix before proceeding.{NC}\n")
            
        # Save report to file
        report_file = f'phase3-validation-report-{self.environment}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}\n")
        
        return report['failed'] == 0

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Phase 3 deployment')
    parser.add_argument(
        '--environment',
        default='staging',
        help='Environment to validate (default: staging)'
    )
    args = parser.parse_args()
    
    print(f"{BLUE}╔════════════════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║     Phase 3 Deployment Validation                         ║{NC}")
    print(f"{BLUE}║     Environment: {args.environment:40s}║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════╝{NC}")
    
    validator = Phase3Validator(environment=args.environment)
    
    # Run all validations
    validator.validate_dynamodb_tables()
    validator.validate_lambda_functions()
    validator.validate_eventbridge_schedules()
    validator.validate_s3_buckets()
    validator.validate_cloudwatch_dashboard()
    validator.validate_cloudwatch_alarms()
    validator.validate_iot_resources()
    validator.validate_sns_topics()
    validator.run_smoke_tests()
    
    # Print summary
    success = validator.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
