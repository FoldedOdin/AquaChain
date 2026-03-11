#!/usr/bin/env python3
"""
Test SageMaker endpoint with multiple water quality scenarios
"""

import boto3
import json

def test_endpoint_with_data(runtime, endpoint_name, test_data, description):
    """Test endpoint with specific data"""
    csv_data = ",".join(map(str, test_data))
    
    print(f"\n--- {description} ---")
    print(f"Input: pH={test_data[0]}, turbidity={test_data[1]}, TDS={test_data[2]}, temp={test_data[3]}")
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=csv_data
        )
        
        result = response['Body'].read().decode()
        probabilities = [float(x) for x in result.strip().split(',')]
        predicted_class = probabilities.index(max(probabilities))
        quality_labels = ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
        quality = quality_labels[predicted_class]
        confidence = max(probabilities)
        
        print(f"✅ Prediction: {quality} (class {predicted_class})")
        print(f"✅ Confidence: {confidence:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Test multiple scenarios"""
    runtime = boto3.client('sagemaker-runtime', region_name='ap-south-1')
    endpoint_name = "aquachain-wqi-working-dev"
    
    print("=== Testing Multiple Water Quality Scenarios ===")
    
    # Test cases: [pH, turbidity, TDS, temperature]
    test_cases = [
        ([7.2, 2.5, 450, 25.0], "Good quality water (normal parameters)"),
        ([6.0, 15.0, 800, 30.0], "Poor quality water (low pH, high turbidity)"),
        ([8.5, 1.0, 300, 22.0], "Excellent quality water (optimal parameters)"),
        ([5.5, 25.0, 1200, 35.0], "Very poor quality water (acidic, high turbidity & TDS)"),
        ([7.5, 8.0, 600, 28.0], "Fair quality water (moderate issues)"),
    ]
    
    success_count = 0
    for test_data, description in test_cases:
        if test_endpoint_with_data(runtime, endpoint_name, test_data, description):
            success_count += 1
    
    print(f"\n=== Results ===")
    print(f"✅ {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("🎉 All tests passed! ML endpoint is working correctly.")
    else:
        print("⚠️  Some tests failed.")

if __name__ == "__main__":
    main()