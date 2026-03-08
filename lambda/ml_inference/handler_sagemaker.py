"""
ML Inference Lambda Function using SageMaker Endpoint
Handles Water Quality Index calculation via SageMaker real-time inference
"""

import json
import boto3
import time
from datetime import datetime
from typing import Dict, Any
import logging
import os
import sys

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure logging
logger = get_logger(__name__, service='ml-inference-sagemaker')

# Initialize AWS clients
sagemaker_runtime = boto3.client('sagemaker-runtime')

# Environment variables
SAGEMAKER_ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME', 'aquachain-wqi-endpoint-dev')
ENABLE_MONITORING = os.environ.get('ENABLE_MONITORING', 'true').lower() == 'true'

# Import performance tracker
try:
    from model_performance_monitor import get_tracker
    _performance_tracker = None
except ImportError:
    logger.warning("ModelPerformanceTracker not available")
    get_tracker = None
    _performance_tracker = None


class MLInferenceError(Exception):
    """Custom exception for ML inference errors"""
    pass


def lambda_handler(event, context):
    """
    Main Lambda handler for ML inference using SageMaker endpoint
    """
    start_time = time.time()
    
    try:
        logger.info(f"ML inference request: {json.dumps(event)}")
        
        # Extract input data
        device_id = event['deviceId']
        timestamp = event['timestamp']
        readings = event['readings']
        location = event['location']
        
        # Prepare payload for SageMaker
        payload = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'readings': readings,
            'location': location
        }
        
        # Invoke SageMaker endpoint
        prediction = invoke_sagemaker_endpoint(payload)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log prediction to performance tracker
        if ENABLE_MONITORING and get_tracker:
            try:
                global _performance_tracker
                if _performance_tracker is None:
                    _performance_tracker = get_tracker()
                
                _performance_tracker.log_prediction(
                    model_name='wqi-model-sagemaker',
                    prediction=prediction['wqi'],
                    actual=None,
                    confidence=prediction['confidence'],
                    latency_ms=latency_ms
                )
            except Exception as e:
                logger.warning(f"Performance monitoring error: {e}")
        
        # Build response
        result = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'wqi': prediction['wqi'],
            'anomalyType': prediction['anomalyType'],
            'confidence': prediction['confidence'],
            'modelVersion': 'sagemaker-v1.0',
            'featureImportance': prediction.get('featureImportance', {}),
            'latencyMs': round(latency_ms, 2)
        }
        
        logger.info(f"ML inference completed: WQI={prediction['wqi']}, Latency={latency_ms:.2f}ms")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"ML inference error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to rule-based calculation
        try:
            fallback_result = calculate_fallback_wqi(event)
            return {
                'statusCode': 200,
                'body': json.dumps(fallback_result)
            }
        except:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }


def invoke_sagemaker_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke SageMaker endpoint for real-time inference
    """
    try:
        # Convert payload to JSON
        payload_json = json.dumps(payload)
        
        # Invoke endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType='application/json',
            Accept='application/json',
            Body=payload_json
        )
        
        # Parse response
        result = json.loads(response['Body'].read().decode('utf-8'))
        
        return result
        
    except Exception as e:
        logger.error(f"SageMaker endpoint invocation failed: {e}")
        raise MLInferenceError(f"SageMaker inference failed: {e}")


def calculate_fallback_wqi(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback WQI calculation using rule-based approach
    """
    readings = event['readings']
    
    pH = readings['pH']
    turbidity = readings['turbidity']
    tds = readings['tds']
    temperature = readings['temperature']
    
    # Simple WQI calculation
    pH_score = max(0, 100 - abs(pH - 7.0) * 20)
    
    if turbidity <= 1:
        turbidity_score = 100
    elif turbidity <= 5:
        turbidity_score = 80
    elif turbidity <= 10:
        turbidity_score = 60
    else:
        turbidity_score = max(0, 60 - (turbidity - 10) * 3)
    
    if tds <= 300:
        tds_score = 100
    elif tds <= 600:
        tds_score = 80
    else:
        tds_score = max(0, 80 - (tds - 600) * 0.05)
    
    if 20 <= temperature <= 30:
        temp_score = 100
    else:
        temp_score = max(0, 100 - min(abs(temperature - 20), abs(temperature - 30)) * 5)
    
    wqi = (pH_score * 0.3 + turbidity_score * 0.3 + tds_score * 0.25 + temp_score * 0.15)
    
    # Simple anomaly detection
    if pH < 6.0 or pH > 9.0 or turbidity > 50 or tds > 2000:
        anomaly_type = 'contamination'
        confidence = 0.8
    elif temperature < 0 or temperature > 50:
        anomaly_type = 'sensor_fault'
        confidence = 0.7
    else:
        anomaly_type = 'normal'
        confidence = 0.8
    
    return {
        'deviceId': event['deviceId'],
        'timestamp': event['timestamp'],
        'wqi': round(wqi, 2),
        'anomalyType': anomaly_type,
        'confidence': confidence,
        'modelVersion': 'fallback-v1.0',
        'featureImportance': {},
        'latencyMs': 0
    }
