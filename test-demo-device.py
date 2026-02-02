#!/usr/bin/env python3
"""
Comprehensive Demo Device Validation Suite
Tests all aspects of demo device implementation
"""

import json
import boto3
import requests
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional

class DemoDeviceValidator:
    """
    Comprehensive validator for demo device implementation
    Tests both backend Lambda function and frontend integration
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Test configuration
        self.test_user_id = 'test-user-demo-validation'
        self.api_base_url = 'http://localhost:3002'  # Development API
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and data:
            print(f"    Data: {json.dumps(data, indent=2)}")
    
    def test_lambda_function_exists(self) -> bool:
        """Test if device management Lambda function exists"""
        function_patterns = [
            'AquaChain-DeviceManagement-dev',
            'AquaChain-Device-Management-dev',
            'device-management'
        ]
        
        for function_name in function_patterns:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                self.lambda_function_name = function_name
                self.log_test(
                    "Lambda Function Exists",
                    True,
                    f"Found function: {function_name}",
                    {
                        'function_name': function_name,
                        'runtime': response['Configuration']['Runtime'],
                        'last_modified': response['Configuration']['LastModified']
                    }
                )
                return True
            except self.lambda_client.exceptions.ResourceNotFoundException:
                continue
            except Exception as e:
                self.log_test(
                    "Lambda Function Exists",
                    False,
                    f"Error checking {function_name}: {str(e)}"
                )
                continue
        
        self.log_test(
            "Lambda Function Exists",
            False,
            "No device management Lambda function found"
        )
        return False
    
    def test_lambda_demo_endpoint(self) -> bool:
        """Test demo device endpoint via direct Lambda invocation"""
        if not hasattr(self, 'lambda_function_name'):
            self.log_test(
                "Lambda Demo Endpoint",
                False,
                "Lambda function not found"
            )
            return False
        
        try:
            # Create test event
            test_event = {
                'httpMethod': 'POST',
                'path': '/api/devices/demo',
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': self.test_user_id
                        }
                    },
                    'identity': {
                        'sourceIp': '127.0.0.1'
                    },
                    'requestId': f'test-{int(time.time())}'
                },
                'headers': {
                    'Content-Type': 'application/json',
                    'User-Agent': 'DemoDeviceValidator/1.0'
                },
                'body': json.dumps({
                    'name': 'Validation Test Demo Device',
                    'location': 'Test Environment',
                    'readings': {
                        'pH': 7.2,
                        'turbidity': 2.1,
                        'tds': 145,
                        'temperature': 22.5
                    }
                })
            }
            
            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName=self.lambda_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            # Parse response
            payload = json.loads(response['Payload'].read())
            
            if payload.get('statusCode') == 200:
                body = json.loads(payload.get('body', '{}'))
                if body.get('success'):
                    device = body.get('device', {})
                    self.test_device_id = device.get('device_id')
                    
                    self.log_test(
                        "Lambda Demo Endpoint",
                        True,
                        f"Demo device created: {self.test_device_id}",
                        {
                            'device_id': self.test_device_id,
                            'name': device.get('name'),
                            'location': device.get('location'),
                            'is_demo': device.get('metadata', {}).get('isDemo')
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Lambda Demo Endpoint",
                        False,
                        f"Demo device creation failed: {body.get('message', 'Unknown error')}",
                        body
                    )
                    return False
            else:
                self.log_test(
                    "Lambda Demo Endpoint",
                    False,
                    f"HTTP {payload.get('statusCode')}: {payload.get('body')}",
                    payload
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Lambda Demo Endpoint",
                False,
                f"Lambda invocation failed: {str(e)}"
            )
            return False
    
    def test_dynamodb_device_storage(self) -> bool:
        """Test if demo device was stored in DynamoDB"""
        if not hasattr(self, 'test_device_id'):
            self.log_test(
                "DynamoDB Device Storage",
                False,
                "No test device ID available"
            )
            return False
        
        try:
            # Get device from DynamoDB
            table = self.dynamodb.Table('aquachain-devices')
            response = table.get_item(Key={'device_id': self.test_device_id})
            
            if 'Item' in response:
                device = response['Item']
                
                # Validate demo device structure
                validations = [
                    ('device_id', device.get('device_id') == self.test_device_id),
                    ('user_id', device.get('user_id') == self.test_user_id),
                    ('is_demo', device.get('metadata', {}).get('isDemo') == True),
                    ('status', device.get('status') == 'active'),
                    ('current_reading', 'current_reading' in device),
                    ('pH', device.get('current_reading', {}).get('pH') is not None),
                    ('turbidity', device.get('current_reading', {}).get('turbidity') is not None),
                    ('tds', device.get('current_reading', {}).get('tds') is not None),
                    ('temperature', device.get('current_reading', {}).get('temperature') is not None)
                ]
                
                failed_validations = [name for name, valid in validations if not valid]
                
                if not failed_validations:
                    self.log_test(
                        "DynamoDB Device Storage",
                        True,
                        f"Demo device properly stored with all required fields",
                        {
                            'device_id': device.get('device_id'),
                            'user_id': device.get('user_id'),
                            'is_demo': device.get('metadata', {}).get('isDemo'),
                            'readings': device.get('current_reading')
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "DynamoDB Device Storage",
                        False,
                        f"Demo device missing required fields: {failed_validations}",
                        device
                    )
                    return False
            else:
                self.log_test(
                    "DynamoDB Device Storage",
                    False,
                    f"Demo device not found in DynamoDB: {self.test_device_id}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "DynamoDB Device Storage",
                False,
                f"DynamoDB query failed: {str(e)}"
            )
            return False
    
    def test_water_quality_calculations(self) -> bool:
        """Test water quality index calculations"""
        if not hasattr(self, 'test_device_id'):
            self.log_test(
                "Water Quality Calculations",
                False,
                "No test device available"
            )
            return False
        
        try:
            # Get device data
            table = self.dynamodb.Table('aquachain-devices')
            response = table.get_item(Key={'device_id': self.test_device_id})
            
            if 'Item' not in response:
                self.log_test(
                    "Water Quality Calculations",
                    False,
                    "Test device not found"
                )
                return False
            
            device = response['Item']
            reading = device.get('current_reading', {})
            
            # Extract parameters
            pH = float(reading.get('pH', 0))
            turbidity = float(reading.get('turbidity', 0))
            tds = float(reading.get('tds', 0))
            temperature = float(reading.get('temperature', 0))
            
            # Calculate WQI (simplified version)
            pH_score = 100 if 6.5 <= pH <= 8.5 else max(0, 100 - abs(7.0 - pH) * 20)
            turbidity_score = max(0, 100 - (turbidity * 20))
            tds_score = max(0, 100 - (tds / 5))
            temp_score = 100 if 15 <= temperature <= 25 else max(0, 100 - abs(20 - temperature) * 5)
            
            wqi = (pH_score + turbidity_score + tds_score + temp_score) / 4
            
            # Validate calculations
            validations = [
                ('pH_in_range', 6.0 <= pH <= 9.0),
                ('turbidity_reasonable', 0 <= turbidity <= 10),
                ('tds_reasonable', 0 <= tds <= 1000),
                ('temperature_reasonable', 10 <= temperature <= 35),
                ('wqi_calculated', 0 <= wqi <= 100)
            ]
            
            failed_validations = [name for name, valid in validations if not valid]
            
            if not failed_validations:
                self.log_test(
                    "Water Quality Calculations",
                    True,
                    f"WQI calculated: {wqi:.1f}",
                    {
                        'pH': pH,
                        'turbidity': turbidity,
                        'tds': tds,
                        'temperature': temperature,
                        'wqi': wqi,
                        'scores': {
                            'pH_score': pH_score,
                            'turbidity_score': turbidity_score,
                            'tds_score': tds_score,
                            'temp_score': temp_score
                        }
                    }
                )
                return True
            else:
                self.log_test(
                    "Water Quality Calculations",
                    False,
                    f"Invalid parameters: {failed_validations}",
                    {
                        'pH': pH,
                        'turbidity': turbidity,
                        'tds': tds,
                        'temperature': temperature
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Water Quality Calculations",
                False,
                f"Calculation test failed: {str(e)}"
            )
            return False
    
    def test_frontend_integration(self) -> bool:
        """Test frontend integration points"""
        try:
            # Check if DemoDeviceModal component exists
            modal_path = 'frontend/src/components/Dashboard/DemoDeviceModal.tsx'
            if not os.path.exists(modal_path):
                self.log_test(
                    "Frontend Integration",
                    False,
                    f"DemoDeviceModal component not found: {modal_path}"
                )
                return False
            
            # Check if Consumer dashboard has demo device integration
            dashboard_path = 'frontend/src/components/Dashboard/ConsumerDashboard.tsx'
            if not os.path.exists(dashboard_path):
                self.log_test(
                    "Frontend Integration",
                    False,
                    f"ConsumerDashboard component not found: {dashboard_path}"
                )
                return False
            
            # Read dashboard file and check for demo device integration
            with open(dashboard_path, 'r') as f:
                dashboard_content = f.read()
            
            required_elements = [
                'DemoDeviceModal',
                'toggleDemoDevice',
                'showDemoDevice',
                'Try Demo Device',
                'handleDemoDeviceAdded'
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in dashboard_content]
            
            if not missing_elements:
                self.log_test(
                    "Frontend Integration",
                    True,
                    "All required frontend elements present",
                    {'required_elements': required_elements}
                )
                return True
            else:
                self.log_test(
                    "Frontend Integration",
                    False,
                    f"Missing frontend elements: {missing_elements}",
                    {'missing_elements': missing_elements}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Frontend Integration",
                False,
                f"Frontend integration test failed: {str(e)}"
            )
            return False
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data"""
        if not hasattr(self, 'test_device_id'):
            return True
        
        try:
            # Remove test device from DynamoDB
            table = self.dynamodb.Table('aquachain-devices')
            table.delete_item(Key={'device_id': self.test_device_id})
            
            self.log_test(
                "Cleanup Test Data",
                True,
                f"Test device removed: {self.test_device_id}"
            )
            return True
            
        except Exception as e:
            self.log_test(
                "Cleanup Test Data",
                False,
                f"Cleanup failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🧪 Starting Demo Device Validation")
        print("=" * 50)
        
        # Run tests in order
        tests = [
            self.test_lambda_function_exists,
            self.test_lambda_demo_endpoint,
            self.test_dynamodb_device_storage,
            self.test_water_quality_calculations,
            self.test_frontend_integration
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(
                    test.__name__,
                    False,
                    f"Test execution failed: {str(e)}"
                )
        
        # Cleanup
        self.cleanup_test_data()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print("📊 Validation Summary")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Save detailed results
        results_file = f"demo_device_validation_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'test_results': self.test_results,
                'timestamp': datetime.utcnow().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved: {results_file}")
        
        return {
            'success': failed_tests == 0,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'results_file': results_file
        }

def main():
    """Main validation function"""
    validator = DemoDeviceValidator()
    results = validator.run_all_tests()
    
    if results['success']:
        print("\n🎉 All validations passed! Demo device implementation is ready.")
        exit(0)
    else:
        print(f"\n⚠️ {results['failed_tests']} validation(s) failed. Check the results above.")
        exit(1)

if __name__ == "__main__":
    main()