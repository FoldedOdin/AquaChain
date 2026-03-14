#!/usr/bin/env python3

"""
Diagnose WQI (Water Quality Index) Issue
Checks why WQI and Quality are showing as N/A in the dashboard
"""

import boto3
import json
import sys
from datetime import datetime, timedelta

def check_sagemaker_endpoint():
    """Check if SageMaker endpoint exists and is active"""
    print("🔍 Checking SageMaker endpoint...")
    
    try:
        sagemaker = boto3.client('sagemaker')
        endpoint_name = 'aquachain-wqi-endpoint-dev'
        
        try:
            response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']
            print(f"   ✅ SageMaker endpoint '{endpoint_name}' exists")
            print(f"   📊 Status: {status}")
            
            if status == 'InService':
                print(f"   🟢 Endpoint is active and ready")
                return True
            else:
                print(f"   🟡 Endpoint exists but not ready (status: {status})")
                return False
                
        except sagemaker.exceptions.ClientError as e:
            if 'ValidationException' in str(e):
                print(f"   ❌ SageMaker endpoint '{endpoint_name}' does not exist")
                return False
            else:
                raise
                
    except Exception as e:
        print(f"   ❌ Error checking SageMaker endpoint: {e}")
        return False

def check_ml_inference_lambda():
    """Check if ML inference Lambda function exists"""
    print("\n🔍 Checking ML inference Lambda function...")
    
    try:
        lambda_client = boto3.client('lambda')
        function_names = [
            'AquaChain-Function-MLInference-dev',
            'aquachain-ml-inference-dev',
            'ml-inference-dev'
        ]
        
        for function_name in function_names:
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                print(f"   ✅ ML inference Lambda '{function_name}' exists")
                print(f"   📊 Runtime: {response['Configuration']['Runtime']}")
                print(f"   📊 Last Modified: {response['Configuration']['LastModified']}")
                return function_name
            except lambda_client.exceptions.ResourceNotFoundException:
                continue
        
        print(f"   ❌ No ML inference Lambda function found")
        return None
        
    except Exception as e:
        print(f"   ❌ Error checking Lambda functions: {e}")
        return None

def check_recent_readings():
    """Check recent readings to see if WQI is being calculated"""
    print("\n🔍 Checking recent readings for WQI data...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        
        # Try different table names
        table_names = [
            'AquaChain-Readings-dev',
            'aquachain-readings-dev',
            'AquaChain-Readings'
        ]
        
        readings_table = None
        for table_name in table_names:
            try:
                table = dynamodb.Table(table_name)
                table.load()
                readings_table = table
                print(f"   ✅ Found readings table: {table_name}")
                break
            except:
                continue
        
        if not readings_table:
            print(f"   ❌ No readings table found")
            return False
        
        # Get recent readings (last 24 hours)
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        # Scan for recent readings (not efficient but works for diagnosis)
        response = readings_table.scan(
            FilterExpression='#ts >= :yesterday',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':yesterday': yesterday.isoformat() + 'Z'},
            Limit=10
        )
        
        readings = response.get('Items', [])
        print(f"   📊 Found {len(readings)} recent readings")
        
        if readings:
            # Check first few readings for WQI
            wqi_count = 0
            for reading in readings[:5]:
                device_id = reading.get('deviceId', 'unknown')
                timestamp = reading.get('timestamp', 'unknown')
                wqi = reading.get('wqi')
                quality = reading.get('quality')
                
                print(f"   📋 Reading: {device_id} at {timestamp}")
                print(f"      WQI: {wqi}")
                print(f"      Quality: {quality}")
                
                if wqi is not None and wqi != 'N/A':
                    wqi_count += 1
            
            print(f"   📊 Readings with WQI: {wqi_count}/{len(readings[:5])}")
            return wqi_count > 0
        else:
            print(f"   ⚠️  No recent readings found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking readings: {e}")
        return False

def check_data_processing_lambda():
    """Check if data processing Lambda is configured correctly"""
    print("\n🔍 Checking data processing Lambda configuration...")
    
    try:
        lambda_client = boto3.client('lambda')
        function_names = [
            'AquaChain-Function-DataProcessing-dev',
            'aquachain-data-processing-dev',
            'data-processing-dev'
        ]
        
        for function_name in function_names:
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                config = response['Configuration']
                
                print(f"   ✅ Data processing Lambda '{function_name}' exists")
                
                # Check environment variables
                env_vars = config.get('Environment', {}).get('Variables', {})
                sagemaker_endpoint = env_vars.get('SAGEMAKER_ENDPOINT_NAME')
                
                if sagemaker_endpoint:
                    print(f"   📊 SageMaker endpoint configured: {sagemaker_endpoint}")
                else:
                    print(f"   ⚠️  No SageMaker endpoint configured")
                
                return function_name
                
            except lambda_client.exceptions.ResourceNotFoundException:
                continue
        
        print(f"   ❌ No data processing Lambda function found")
        return None
        
    except Exception as e:
        print(f"   ❌ Error checking data processing Lambda: {e}")
        return None

def test_ml_inference_directly():
    """Test ML inference Lambda directly"""
    print("\n🧪 Testing ML inference Lambda directly...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Test payload
        test_payload = {
            "deviceId": "TEST-DEVICE-001",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "readings": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            },
            "location": {
                "latitude": 12.9716,
                "longitude": 77.5946
            }
        }
        
        function_names = [
            'AquaChain-Function-MLInference-dev',
            'aquachain-ml-inference-dev',
            'ml-inference-dev'
        ]
        
        for function_name in function_names:
            try:
                print(f"   🧪 Testing function: {function_name}")
                
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_payload)
                )
                
                result = json.loads(response['Payload'].read())
                
                if response['StatusCode'] == 200:
                    body = json.loads(result.get('body', '{}'))
                    wqi = body.get('wqi')
                    quality = body.get('quality')
                    
                    print(f"   ✅ ML inference successful!")
                    print(f"   📊 WQI: {wqi}")
                    print(f"   📊 Quality: {quality}")
                    return True
                else:
                    print(f"   ❌ ML inference failed: {result}")
                    
            except lambda_client.exceptions.ResourceNotFoundException:
                continue
            except Exception as e:
                print(f"   ❌ Error testing {function_name}: {e}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Error testing ML inference: {e}")
        return False

def main():
    """Main diagnosis function"""
    print("🔧 AquaChain WQI Diagnosis Tool")
    print("=" * 50)
    
    # Check components
    sagemaker_ok = check_sagemaker_endpoint()
    ml_lambda = check_ml_inference_lambda()
    data_lambda = check_data_processing_lambda()
    readings_have_wqi = check_recent_readings()
    ml_test_ok = test_ml_inference_directly()
    
    # Summary
    print("\n📋 DIAGNOSIS SUMMARY")
    print("=" * 50)
    print(f"SageMaker Endpoint:     {'✅ Active' if sagemaker_ok else '❌ Missing/Inactive'}")
    print(f"ML Inference Lambda:    {'✅ Found' if ml_lambda else '❌ Missing'}")
    print(f"Data Processing Lambda: {'✅ Found' if data_lambda else '❌ Missing'}")
    print(f"Recent Readings WQI:    {'✅ Present' if readings_have_wqi else '❌ Missing'}")
    print(f"ML Inference Test:      {'✅ Working' if ml_test_ok else '❌ Failed'}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 50)
    
    if not sagemaker_ok and not ml_test_ok:
        print("🔧 ISSUE: Neither SageMaker endpoint nor ML Lambda is working")
        print("   → Deploy SageMaker endpoint OR fix ML inference Lambda")
        print("   → Update data processing to use working ML service")
    elif not sagemaker_ok and ml_test_ok:
        print("🔧 ISSUE: SageMaker endpoint missing but ML Lambda works")
        print("   → Update data processing Lambda to use ML inference Lambda instead of SageMaker")
        print("   → Change invoke_ml_inference() to call Lambda function")
    elif sagemaker_ok and not readings_have_wqi:
        print("🔧 ISSUE: SageMaker works but readings don't have WQI")
        print("   → Check data processing Lambda logs for errors")
        print("   → Verify IoT data is flowing through data processing")
    elif not readings_have_wqi:
        print("🔧 ISSUE: No WQI in recent readings")
        print("   → Check if IoT devices are sending data")
        print("   → Verify data processing pipeline is working")
    else:
        print("✅ All components appear to be working")
        print("   → WQI issue might be in frontend display logic")

if __name__ == "__main__":
    main()