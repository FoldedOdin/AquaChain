"""
ML Inference Lambda Function for AquaChain System
Handles Water Quality Index calculation and anomaly detection using Random Forest
"""

import json
import boto3
import pickle
import numpy as np
import time
from datetime import datetime
from typing import Dict, Any, Tuple
import logging
import os
import sys

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(__file__))

# Add shared utilities to path
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import structured logging
from structured_logger import get_logger

# Configure structured logging
logger = get_logger(__name__, service='ml-inference')

# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
MODEL_BUCKET = 'aquachain-data-lake'
MODEL_KEY_PREFIX = 'ml-models/current/'
MODEL_VERSION_KEY = 'wqi-model-version.json'
ENABLE_MONITORING = os.environ.get('ENABLE_MONITORING', 'true').lower() == 'true'

# Global model cache
_model_cache = {}
_model_version = None

# Import performance tracker
try:
    from model_performance_monitor import get_tracker
    _performance_tracker = None
except ImportError:
    logger.warning("ModelPerformanceTracker not available - monitoring disabled")
    get_tracker = None
    _performance_tracker = None

class MLInferenceError(Exception):
    """Custom exception for ML inference errors"""
    pass

def lambda_handler(event, context):
    """
    Main Lambda handler for ML inference with performance monitoring
    """
    start_time = time.time()
    
    try:
        logger.info(f"ML inference request: {json.dumps(event)}")
        
        # Extract input data
        device_id = event['deviceId']
        timestamp = event['timestamp']
        readings = event['readings']
        location = event['location']
        
        # Load ML model
        model = load_ml_model()
        
        # Prepare features for inference
        features = prepare_features(readings, location, timestamp)
        
        # Calculate WQI
        wqi = calculate_wqi(features, model)
        
        # Detect anomalies
        anomaly_type, confidence = detect_anomaly(features, model)
        
        # Get feature importance for explainability
        feature_importance = get_feature_importance(model, features)
        
        # Calculate prediction latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log prediction to performance tracker (async - no latency impact)
        if ENABLE_MONITORING and get_tracker:
            try:
                global _performance_tracker
                if _performance_tracker is None:
                    _performance_tracker = get_tracker()
                
                _performance_tracker.log_prediction(
                    model_name='wqi-model',
                    prediction=wqi,
                    actual=None,  # Actual value not available at inference time
                    confidence=confidence,
                    latency_ms=latency_ms
                )
                
                # Periodically check for drift (every 100 predictions)
                predictions = _performance_tracker.get_rolling_window_predictions()
                if len(predictions) >= 100 and len(predictions) % 100 == 0:
                    drift_score = _performance_tracker.calculate_drift_score('wqi-model', predictions)
                    
                    # Send drift score to CloudWatch for alarming
                    _performance_tracker.send_drift_score_metric('wqi-model', drift_score)
                    
                    drift_detected = _performance_tracker.check_for_drift('wqi-model', drift_score)
                    
                    if drift_detected:
                        logger.warning(f"Model drift detected! Score: {drift_score:.3f}")
                        _performance_tracker.trigger_retraining('wqi-model', 'drift_detection')
                
            except Exception as e:
                logger.warning(f"Performance monitoring error (non-critical): {e}")
        
        result = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'wqi': round(wqi, 2),
            'anomalyType': anomaly_type,
            'confidence': round(confidence, 3),
            'modelVersion': _model_version,
            'featureImportance': feature_importance,
            'latencyMs': round(latency_ms, 2)
        }
        
        logger.info(f"ML inference completed: WQI={wqi}, Anomaly={anomaly_type}, Latency={latency_ms:.2f}ms")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"ML inference error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def load_ml_model() -> Dict[str, Any]:
    """
    Load ML model from S3 with caching and version management
    """
    global _model_cache, _model_version
    
    try:
        # Check for model version updates
        current_version = get_current_model_version()
        
        if _model_version != current_version or not _model_cache:
            logger.info(f"Loading model version: {current_version}")
            
            # Load WQI regression model
            wqi_model_key = f"{MODEL_KEY_PREFIX}wqi-model-v{current_version}.pkl"
            wqi_model = load_model_from_s3(wqi_model_key)
            
            # Load anomaly detection model
            anomaly_model_key = f"{MODEL_KEY_PREFIX}anomaly-model-v{current_version}.pkl"
            anomaly_model = load_model_from_s3(anomaly_model_key)
            
            # Load feature scaler
            scaler_key = f"{MODEL_KEY_PREFIX}feature-scaler-v{current_version}.pkl"
            scaler = load_model_from_s3(scaler_key)
            
            # Cache models
            _model_cache = {
                'wqi_model': wqi_model,
                'anomaly_model': anomaly_model,
                'scaler': scaler,
                'version': current_version
            }
            _model_version = current_version
            
            logger.info(f"Model loaded successfully: version {current_version}")
        
        return _model_cache
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        # Return fallback model if loading fails
        return get_fallback_model()

def get_current_model_version() -> str:
    """
    Get current model version from S3
    """
    try:
        response = s3_client.get_object(
            Bucket=MODEL_BUCKET,
            Key=f"{MODEL_KEY_PREFIX}{MODEL_VERSION_KEY}"
        )
        version_info = json.loads(response['Body'].read())
        return version_info['version']
    except Exception as e:
        logger.warning(f"Error getting model version: {e}")
        return "1.0"  # Default version

def load_model_from_s3(model_key: str) -> Any:
    """
    Load pickled model from S3
    """
    try:
        response = s3_client.get_object(
            Bucket=MODEL_BUCKET,
            Key=model_key
        )
        model = pickle.loads(response['Body'].read())
        return model
    except Exception as e:
        logger.error(f"Error loading model from {model_key}: {e}")
        raise MLInferenceError(f"Failed to load model: {e}")

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
        raise MLInferenceError(f"Feature preparation failed: {e}")

def calculate_wqi(features: np.ndarray, model: Dict[str, Any]) -> float:
    """
    Calculate Water Quality Index using Random Forest regression
    """
    try:
        # Scale features
        scaled_features = model['scaler'].transform(features)
        
        # Predict WQI
        wqi_prediction = model['wqi_model'].predict(scaled_features)[0]
        
        # Ensure WQI is in valid range (0-100)
        wqi = max(0, min(100, wqi_prediction))
        
        return float(wqi)
        
    except Exception as e:
        logger.error(f"Error calculating WQI: {e}")
        # Fallback WQI calculation
        return calculate_fallback_wqi(features)

def detect_anomaly(features: np.ndarray, model: Dict[str, Any]) -> Tuple[str, float]:
    """
    Detect anomalies using Random Forest classifier
    Returns anomaly type and confidence score
    """
    try:
        # Scale features
        scaled_features = model['scaler'].transform(features)
        
        # Predict anomaly class
        anomaly_prediction = model['anomaly_model'].predict(scaled_features)[0]
        
        # Get prediction probabilities for confidence
        probabilities = model['anomaly_model'].predict_proba(scaled_features)[0]
        confidence = max(probabilities)
        
        # Map prediction to anomaly type
        anomaly_classes = ['normal', 'sensor_fault', 'contamination']
        anomaly_type = anomaly_classes[anomaly_prediction]
        
        return anomaly_type, float(confidence)
        
    except Exception as e:
        logger.error(f"Error detecting anomaly: {e}")
        # Fallback anomaly detection
        return detect_fallback_anomaly(features)

def get_feature_importance(model: Dict[str, Any], features: np.ndarray) -> Dict[str, float]:
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
        importance_scores = model['wqi_model'].feature_importances_
        
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
    """
    Fallback WQI calculation using simple weighted formula
    """
    try:
        # Extract basic sensor readings (first 5 features)
        pH, turbidity, tds, temperature, humidity = features[0][:5]
        
        # Simple WQI calculation with weights
        weights = {
            'pH': 0.25,
            'turbidity': 0.25,
            'tds': 0.20,
            'temperature': 0.15,
            'humidity': 0.15
        }
        
        # Normalize each parameter to 0-100 scale
        pH_score = normalize_ph(pH)
        turbidity_score = normalize_turbidity(turbidity)
        tds_score = normalize_tds(tds)
        temp_score = normalize_temperature(temperature)
        humidity_score = normalize_humidity(humidity)
        
        # Calculate weighted WQI
        wqi = (pH_score * weights['pH'] +
               turbidity_score * weights['turbidity'] +
               tds_score * weights['tds'] +
               temp_score * weights['temperature'] +
               humidity_score * weights['humidity'])
        
        return max(0, min(100, wqi))
        
    except Exception as e:
        logger.error(f"Fallback WQI calculation error: {e}")
        return 50.0  # Neutral WQI

def detect_fallback_anomaly(features: np.ndarray) -> Tuple[str, float]:
    """
    Fallback anomaly detection using rule-based approach
    """
    try:
        pH, turbidity, tds, temperature, humidity = features[0][:5]
        
        # Rule-based anomaly detection
        if pH < 6.0 or pH > 9.0:
            if turbidity > 10 or tds > 1000:
                return 'contamination', 0.8
            else:
                return 'sensor_fault', 0.7
        
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

def normalize_ph(pH: float) -> float:
    """Normalize pH to 0-100 scale (7.0 = 100, further from 7 = lower score)"""
    deviation = abs(pH - 7.0)
    return max(0, 100 - (deviation * 20))

def normalize_turbidity(turbidity: float) -> float:
    """Normalize turbidity to 0-100 scale (lower is better)"""
    if turbidity <= 1:
        return 100
    elif turbidity <= 5:
        return 80
    elif turbidity <= 10:
        return 60
    elif turbidity <= 25:
        return 40
    else:
        return max(0, 40 - (turbidity - 25) * 2)

def normalize_tds(tds: float) -> float:
    """Normalize TDS to 0-100 scale"""
    if tds <= 300:
        return 100
    elif tds <= 600:
        return 80
    elif tds <= 900:
        return 60
    elif tds <= 1200:
        return 40
    else:
        return max(0, 40 - (tds - 1200) * 0.02)

def normalize_temperature(temperature: float) -> float:
    """Normalize temperature to 0-100 scale (20-30°C is optimal)"""
    if 20 <= temperature <= 30:
        return 100
    else:
        deviation = min(abs(temperature - 20), abs(temperature - 30))
        return max(0, 100 - deviation * 5)

def normalize_humidity(humidity: float) -> float:
    """Normalize humidity to 0-100 scale (40-70% is optimal)"""
    if 40 <= humidity <= 70:
        return 100
    else:
        if humidity < 40:
            return max(0, 100 - (40 - humidity) * 2)
        else:
            return max(0, 100 - (humidity - 70) * 2)

def get_fallback_model() -> Dict[str, Any]:
    """
    Return fallback model structure when S3 model loading fails
    """
    logger.warning("Using fallback model - ML predictions may be less accurate")
    
    return {
        'wqi_model': None,
        'anomaly_model': None,
        'scaler': None,
        'version': 'fallback'
    }