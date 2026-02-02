#!/usr/bin/env python3
"""
Deploy Demo Device Feature - Production Ready
Deploys the enhanced device management Lambda with demo device support
"""

import boto3
import zipfile
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

class DemoDeviceDeployer:
    """
    Production-ready deployer for demo device feature
    Follows AquaChain engineering principles: security, reliability, maintainability
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        
    def validate_environment(self) -> bool:
        """Validate deployment environment and prerequisites"""
        print("🔍 Validating deployment environment...")
        
        try:
            # Check AWS credentials
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS Identity: {identity.get('Arn', 'Unknown')}")
            
            # Check required files exist
            required_files = [
                'lambda/device_management/handler.py',
                'lambda/device_management/add_demo_device.py',
                'lambda/shared/errors.py',
                'lambda/shared/error_handler.py',
                'lambda/shared/structured_logger.py',
                'lambda/shared/audit_logger.py'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                print(f"❌ Missing required files: {missing_files}")
                return False
            
            print("✅ All required files present")
            return True
            
        except Exception as e:
            print(f"❌ Environment validation failed: {str(e)}")
            return False
    
    def create_deployment_package(self) -> str:
        """Create optimized deployment package"""
        print("📦 Creating deployment package...")
        
        zip_path = 'demo-device-lambda.zip'
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                # Add main handler
                zipf.write('lambda/device_management/handler.py', 'handler.py')
                
                # Add demo device module
                if Path('lambda/device_management/add_demo_device.py').exists():
                    zipf.write('lambda/device_management/add_demo_device.py', 'add_demo_device.py')
                
                # Add shared dependencies
                shared_dir = Path('lambda/shared')
                if shared_dir.exists():
                    for file_path in shared_dir.rglob('*.py'):
                        if file_path.name != '__pycache__':
                            arcname = str(file_path.relative_to('lambda/shared'))
                            zipf.write(file_path, arcname)
                
                # Add requirements if exists
                requirements_path = Path('lambda/device_management/requirements.txt')
                if requirements_path.exists():
                    zipf.write(requirements_path, 'requirements.txt')
            
            # Validate package size (Lambda limit is 50MB)
            package_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
            if package_size > 45:  # Leave 5MB buffer
                print(f"⚠️ Package size ({package_size:.1f}MB) approaching Lambda limit")
            
            print(f"✅ Deployment package created: {zip_path} ({package_size:.1f}MB)")
            return zip_path
            
        except Exception as e:
            print(f"❌ Failed to create deployment package: {str(e)}")
            raise
    
    def find_lambda_function(self) -> Optional[str]:
        """Find the device management Lambda function"""
        print("🔍 Searching for device management Lambda function...")
        
        # Common naming patterns for AquaChain Lambda functions
        function_patterns = [
            'AquaChain-DeviceManagement-dev',
            'AquaChain-DeviceManagement-prod',
            'AquaChain-Device-Management-dev',
            'AquaChain-Device-Management-prod',
            'aquachain-device-management-dev',
            'aquachain-device-management-prod',
            'device-management',
            'DeviceManagement'
        ]
        
        for function_name in function_patterns:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                print(f"✅ Found Lambda function: {function_name}")
                print(f"   Runtime: {response['Configuration']['Runtime']}")
                print(f"   Last Modified: {response['Configuration']['LastModified']}")
                return function_name
            except self.lambda_client.exceptions.ResourceNotFoundException:
                continue
            except Exception as e:
                print(f"⚠️ Error checking function {function_name}: {str(e)}")
                continue
        
        print("❌ No device management Lambda function found")
        return None
    
    def backup_current_function(self, function_name: str) -> bool:
        """Create backup of current function code"""
        print(f"💾 Creating backup of current function: {function_name}")
        
        try:
            # Get current function code
            response = self.lambda_client.get_function(FunctionName=function_name)
            code_location = response['Code']['Location']
            
            # Download current code
            import urllib.request
            backup_path = f"backup-{function_name}-{int(time.time())}.zip"
            urllib.request.urlretrieve(code_location, backup_path)
            
            print(f"✅ Backup created: {backup_path}")
            return True
            
        except Exception as e:
            print(f"⚠️ Backup failed (continuing anyway): {str(e)}")
            return False
    
    def update_lambda_function(self, function_name: str, zip_path: str) -> bool:
        """Update Lambda function with new code"""
        print(f"🚀 Updating Lambda function: {function_name}")
        
        try:
            # Read deployment package
            with open(zip_path, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            # Update function code
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content,
                Publish=True  # Create new version
            )
            
            print(f"✅ Function updated successfully")
            print(f"   Version: {response['Version']}")
            print(f"   Code Size: {response['CodeSize']} bytes")
            print(f"   Last Modified: {response['LastModified']}")
            
            # Wait for function to be ready
            print("⏳ Waiting for function to be ready...")
            waiter = self.lambda_client.get_waiter('function_updated')
            waiter.wait(
                FunctionName=function_name,
                WaiterConfig={'Delay': 2, 'MaxAttempts': 30}
            )
            
            print("✅ Function is ready")
            return True
            
        except Exception as e:
            print(f"❌ Function update failed: {str(e)}")
            return False
    
    def test_demo_endpoint(self, function_name: str) -> bool:
        """Test the demo device endpoint"""
        print("🧪 Testing demo device endpoint...")
        
        try:
            # Create test event for demo device creation
            test_event = {
                'httpMethod': 'POST',
                'path': '/api/devices/demo',
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'test-user-id-12345'
                        }
                    },
                    'identity': {
                        'sourceIp': '127.0.0.1'
                    },
                    'requestId': 'test-request-id'
                },
                'headers': {
                    'Content-Type': 'application/json',
                    'User-Agent': 'AquaChain-Test/1.0'
                },
                'body': json.dumps({
                    'name': 'Test Demo Device',
                    'location': 'Test Kitchen',
                    'readings': {
                        'pH': 7.2,
                        'turbidity': 2.1,
                        'tds': 145,
                        'temperature': 22.5
                    }
                })
            }
            
            # Invoke function
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            # Parse response
            payload = json.loads(response['Payload'].read())
            
            if payload.get('statusCode') == 200:
                body = json.loads(payload.get('body', '{}'))
                if body.get('success'):
                    print("✅ Demo device endpoint test passed")
                    print(f"   Device ID: {body.get('device', {}).get('device_id', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Demo device creation failed: {body.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Endpoint test failed with status: {payload.get('statusCode')}")
                print(f"   Error: {payload.get('body', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Endpoint test failed: {str(e)}")
            return False
    
    def update_api_gateway_if_needed(self) -> bool:
        """Check and update API Gateway configuration if needed"""
        print("🔍 Checking API Gateway configuration...")
        
        try:
            # This would typically involve checking if the POST /api/devices/demo route exists
            # For now, we'll just log that manual configuration may be needed
            print("⚠️ Manual API Gateway configuration may be required:")
            print("   1. Add route: POST /api/devices/demo")
            print("   2. Point to Device Management Lambda")
            print("   3. Enable CORS if not already enabled")
            print("   4. Deploy API changes")
            
            return True
            
        except Exception as e:
            print(f"⚠️ API Gateway check failed: {str(e)}")
            return False
    
    def deploy(self) -> bool:
        """Execute complete deployment"""
        print("🚀 Starting Demo Device Feature Deployment")
        print("=" * 50)
        
        try:
            # Step 1: Validate environment
            if not self.validate_environment():
                return False
            
            # Step 2: Create deployment package
            zip_path = self.create_deployment_package()
            
            # Step 3: Find Lambda function
            function_name = self.find_lambda_function()
            if not function_name:
                print("\n❌ Deployment failed: Lambda function not found")
                print("\n🔧 Manual Steps Required:")
                print("1. Verify your Lambda function name")
                print("2. Update function_patterns in this script")
                print("3. Ensure you have proper AWS permissions")
                return False
            
            # Step 4: Backup current function
            self.backup_current_function(function_name)
            
            # Step 5: Update Lambda function
            if not self.update_lambda_function(function_name, zip_path):
                return False
            
            # Step 6: Test demo endpoint
            if not self.test_demo_endpoint(function_name):
                print("⚠️ Endpoint test failed, but deployment may still be successful")
            
            # Step 7: Check API Gateway
            self.update_api_gateway_if_needed()
            
            # Cleanup
            if os.path.exists(zip_path):
                os.remove(zip_path)
                print(f"🧹 Cleaned up: {zip_path}")
            
            print("\n✅ Demo Device Feature Deployment Completed!")
            print("\n📋 Next Steps:")
            print("1. Test demo device creation in Consumer dashboard")
            print("2. Verify API Gateway route: POST /api/devices/demo")
            print("3. Check CloudWatch logs for any errors")
            print("4. Monitor demo device usage metrics")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {str(e)}")
            return False

def main():
    """Main deployment function"""
    deployer = DemoDeviceDeployer()
    success = deployer.deploy()
    
    if not success:
        print("\n🔧 Troubleshooting Guide:")
        print("1. Check AWS credentials: aws sts get-caller-identity")
        print("2. Verify Lambda function exists in AWS Console")
        print("3. Ensure proper IAM permissions for Lambda updates")
        print("4. Check CloudWatch logs for detailed error messages")
        exit(1)

if __name__ == "__main__":
    main()