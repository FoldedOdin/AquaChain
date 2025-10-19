"""
Development ML Inference Handler
Uses local models instead of S3 for development and testing
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple
import logging
import os

from local_model_loader import LocalModelLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize local model loader
MODEL_LOADER = LocalModelLoader("models")

def lambda_handler(event, context=None):
    """
    Development Lambda handler for ML inference using local models
    """
    try:
        logger.info(f"ML inference request: {json.dumps(event)}")
        
        # Extract input data
        device_id = event['deviceId']
        timestamp = event['timestamp']
        readings = event['readings']
        location = event['location']
        
        # Load ML models
        models = MODEL_LOADER.load_models("1.0")
        
        # Prepare features for inference
        features = prepare_features(readings, location, timestamp)
        
        # Calculate WQI
        wqi = calculate_wqi(features, models)
        
        # Detect anomalies
        anomaly_type, confidence = detect_anomaly(features, models)
        
        # Get feature importance for explainability
        feature_importance = get_feature_importance(models, features)
        
        result = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'wqi': round(wqi, 2),
            'anomalyType': anomaly_type,
            'confidence': round(confidence, 3),
            'modelVersion': models['version'],
            'featureImportance': feature_importance
        }
        
        logger.info(f"ML inference completed: WQI={wqi}, Anomaly={anomaly_type}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"ML inference error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def prepare_features(readings: Dict[str, float], location: Dict[str, float], 
                    timestamp: str) -> np.ndarray:
    """
    Prepare feature vector for ML inference
    """
    try:
        # Parse timestamp for temporal features
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Base sensor features
        features = [
            readings['pH'],
            readings['turbidity'],
            readings['tds'],
            readings['temperature'],
            readings['humidity']
        ]
        
        # Location features
        features.extend([
            location['latitude'],
            location['longitude']
        ])
        
        # Temporal features
        features.extend([
            dt.hour,  # Hour of day (0-23)
            dt.month,  # Month (1-12)
            dt.weekday()  # Day of week (0-6)
        ])
        
        # Derived features
        features.extend([
            readings['pH'] * readings['temperature'],  # pH-temperature interaction
            readings['turbidity'] / max(readings['tds'], 1),  # Turbidity-TDS ratio
            abs(readings['pH'] - 7.0),  # pH deviation from neutral
            readings['temperature'] - 25.0,  # Temperature deviation from 25°C
        ])
        
        return np.array(features).reshape(1, -1)
        
    except Exception as e:
        logger.error(f"Error preparing features: {e}")
        raise


def calculate_wqi(features: np.ndarray, models: Dict[str, Any]) -> float:
    """
    Calculate Water Quality Index using trained model
    """
    try:
        # Scale features
        scaled_features = models['scaler'].transform(features)
        
        # Predict WQI
        wqi_prediction = models['wqi_model'].predict(scaled_features)[0]
        
        # Ensure WQI is in valid range (0-100)
        wqi = max(0, min(100, wqi_prediction))
        
        return float(wqi)
        
    except Exception as e:
        logger.error(f"Error calculating WQI: {e}")
        # Fallback WQI calculation
        return calculate_fallback_wqi(features)


def detect_anomaly(features: np.ndarray, models: Dict[str, Any]) -> Tuple[str, float]:
    """
    Detect anomalies using trained model
    """
    try:
        # Scale features
        scaled_features = models['scaler'].transform(features)
        
        # Predict anomaly class
        anomaly_prediction = models['anomaly_model'].predict(scaled_features)[0]
        
        # Get prediction probabilities for confidence
        probabilities = models['anomaly_model'].predict_proba(scaled_features)[0]
        confidence = max(probabilities)
        
        # Map prediction to anomaly type
        anomaly_classes = ['normal', 'sensor_fault', 'contamination']
        anomaly_type = anomaly_classes[anomaly_prediction]
        
        return anomaly_type, float(confidence)
        
    except Exception as e:
        logger.error(f"Error detecting anomaly: {e}")
        # Fallback anomaly detection
        return detect_fallback_anomaly(features)


def get_feature_importance(models: Dict[str, Any], features: np.ndarray) -> Dict[str, float]:
    """
    Get feature importance for model explainability
    """
    try:
        feature_names = [
            'pH', 'turbidity', 'tds', 'temperature', 'humidity',
            'latitude', 'longitude', 'hour', 'month', 'weekday',
            'pH_temp_interaction', 'turbidity_tds_ratio', 
            'pH_deviation', 'temp_deviation'
        ]
        
        # Get feature importance from Random Forest
        importance_scores = models['wqi_model'].feature_importances_
        
        # Create importance dictionary
        feature_importance = {}
        for i, name in enumerate(feature_names):
            if i < len(importance_scores):
                feature_importance[name] = round(float(importance_scores[i]), 4)
        
        return feature_importance
        
    except Exception as e:
        logger.warning(f"Error getting feature importance: {e}")
        return {}


def calculate_fallback_wqi(features: np.ndarray) -> float:
    """Fallback WQI calculation using simple weighted formula"""
    try:
        pH, turbidity, tds, temperature, humidity = features[0][:5]
        
        # Simple WQI calculation
        pH_score = max(0, 100 - abs(pH - 7.0) * 20)
        turbidity_score = max(0, 100 - turbidity * 2)
        tds_score = max(0, 100 - (tds - 300) * 0.05) if tds > 300 else 100
        temp_score = max(0, 100 - abs(temperature - 25) * 3)
        humidity_score = max(0, 100 - abs(humidity - 60) * 1)
        
        wqi = (pH_score * 0.25 + turbidity_score * 0.25 + tds_score * 0.20 + 
               temp_score * 0.15 + humidity_score * 0.15)
        
        return max(0, min(100, wqi))
        
    except Exception as e:
        logger.error(f"Fallback WQI calculation error: {e}")
        return 50.0


def detect_fallback_anomaly(features: np.ndarray) -> Tuple[str, float]:
    """Fallback anomaly detection using rule-based approach"""
    try:
        pH, turbidity, tds, temperature, humidity = features[0][:5]
        
        if pH < 6.0 or pH > 9.0:
            return 'contamination' if turbidity > 10 else 'sensor_fault', 0.7
        if turbidity > 50:
            return 'contamination', 0.9
        if tds > 2000:
            return 'contamination', 0.8
        if temperature < 0 or temperature > 50:
            return 'sensor_fault', 0.7
        if humidity > 95 or humidity < 10:
            return 'sensor_fault', 0.6
        
        return 'normal', 0.8
        
    except Exception as e:
        logger.error(f"Fallback anomaly detection error: {e}")
        return 'unknown', 0.0


def test_inference():
    """
    Test the inference handler with sample data
    """
    test_cases = [
        {
            'name': 'Normal water quality',
            'event': {
                'deviceId': 'DEV-001',
                'timestamp': '2025-10-19T13:00:00Z',
                'readings': {
                    'pH': 7.0,
                    'turbidity': 1.5,
                    'tds': 200,
                    'temperature': 25.0,
                    'humidity': 60.0
                },
                'location': {'latitude': 10.0, 'longitude': 76.0}
            }
        },
        {
            'name': 'Contaminated water',
            'event': {
                'deviceId': 'DEV-002',
                'timestamp': '2025-10-19T13:00:00Z',
                'readings': {
                    'pH': 4.5,
                    'turbidity': 50.0,
                    'tds': 2000,
                    'temperature': 25.0,
                    'humidity': 60.0
                },
                'location': {'latitude': 10.0, 'longitude': 76.0}
            }
        },
        {
            'name': 'Sensor fault',
            'event': {
                'deviceId': 'DEV-003',
                'timestamp': '2025-10-19T13:00:00Z',
                'readings': {
                    'pH': 12.0,
                    'turbidity': 1.0,
                    'tds': 200,
                    'temperature': -5.0,
                    'humidity': 60.0
                },
                'location': {'latitude': 10.0, 'longitude': 76.0}
            }
        }
    ]
    
    print("Testing ML inference with local models...\n")
    
    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        result = lambda_handler(test_case['event'])
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"  ✅ WQI: {body['wqi']}")
            print(f"  ✅ Anomaly: {body['anomalyType']} (confidence: {body['confidence']})")
            print(f"  ✅ Model version: {body['modelVersion']}")
        else:
            print(f"  ❌ Error: {result['body']}")
        print()


if __name__ == "__main__":
    test_inference()