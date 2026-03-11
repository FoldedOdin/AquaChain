#!/usr/bin/env python3
"""
Test script for SageMaker XGBoost endpoint
"""

import boto3
import json
import numpy as np

def test_xgboost_endpoint():
    """Test the SageMaker XGBoost endpoint with sample data"""
    
    # Initialize SageMaker runtime client
    runtime = boto3.client('sagemaker-runtime', region_name='ap-south-1')
    
    # Test data - good water quality (should predict class 0 or 1)
    test_data = [7.2, 2.5, 450, 25.0]  # pH, turbidity, TDS, temperature
    
    # Convert to CSV format (XGBoost expects CSV)
    csv_data = ",".join(map(str, test_data))
    
    endpoint_name = "aquachain-wqi-working-dev"  # Use the new working endpoint
    
    try:
        print(f"Testing SageMaker XGBoost endpoint: {endpoint_name}")
        print(f"Input data: pH={test_data[0]}, turbidity={test_data[1]}, TDS={test_data[2]}, temp={test_data[3]}")
        print(f"CSV format: {csv_data}")
        
        # Invoke endpoint with CSV data
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=csv_data
        )
        
        # Parse response
        result = response['Body'].read().decode()
        print(f"✅ Raw endpoint response: {result}")
        
        # Parse probabilities (XGBoost returns comma-separated probabilities)
        try:
            probabilities = [float(x) for x in result.strip().split(',')]
            predicted_class = probabilities.index(max(probabilities))  # Get class with highest probability
            quality_labels = ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
            quality = quality_labels[predicted_class] if predicted_class < len(quality_labels) else "Unknown"
            confidence = max(probabilities)
            
            print(f"✅ Predicted class: {predicted_class} ({quality})")
            print(f"✅ Confidence: {confidence:.4f}")
            print(f"✅ All probabilities: {dict(zip(quality_labels[:len(probabilities)], probabilities))}")
        except (ValueError, IndexError) as e:
            print(f"✅ Response parsing error: {e}")
            print(f"✅ Raw response: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    test_xgboost_endpoint()