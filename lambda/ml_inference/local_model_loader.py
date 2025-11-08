"""
Local Model Loader for Development and Testing
Loads models from local filesystem instead of S3 for development purposes
"""

import pickle
import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger()


class LocalModelLoader:
    """
    Load ML models from local filesystem for development
    """
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize local model loader
        
        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = models_dir
        self._model_cache = {}
        self._model_version = None
    
    def load_models(self, version: str = "1.0") -> Dict[str, Any]:
        """
        Load all models for a specific version
        
        Args:
            version: Model version to load
            
        Returns:
            Dictionary containing all models and metadata
        """
        if self._model_version == version and self._model_cache:
            return self._model_cache
        
        try:
            # Load WQI model
            wqi_model_path = os.path.join(self.models_dir, f"wqi-model-v{version}.pkl")
            with open(wqi_model_path, 'rb') as f:
                wqi_model = pickle.load(f)
            
            # Load anomaly model
            anomaly_model_path = os.path.join(self.models_dir, f"anomaly-model-v{version}.pkl")
            with open(anomaly_model_path, 'rb') as f:
                anomaly_model = pickle.load(f)
            
            # Load feature scaler
            scaler_path = os.path.join(self.models_dir, f"feature-scaler-v{version}.pkl")
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            
            # Load metadata
            metadata_path = os.path.join(self.models_dir, f"model-metadata-v{version}.json")
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Cache models
            self._model_cache = {
                'wqi_model': wqi_model,
                'anomaly_model': anomaly_model,
                'scaler': scaler,
                'metadata': metadata,
                'version': version
            }
            self._model_version = version
            
            logger.info(f"Loaded models version {version} from local filesystem")
            return self._model_cache
            
        except Exception as e:
            logger.error(f"Error loading local models: {e}")
            raise
    
    def get_model_info(self, version: str = "1.0") -> Dict[str, Any]:
        """
        Get model information without loading the actual models
        
        Args:
            version: Model version
            
        Returns:
            Model metadata
        """
        try:
            metadata_path = os.path.join(self.models_dir, f"model-metadata-v{version}.json")
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading model metadata: {e}")
            return {}
    
    def list_available_versions(self) -> list:
        """
        List all available model versions
        
        Returns:
            List of available versions
        """
        versions = []
        try:
            for filename in os.listdir(self.models_dir):
                if filename.startswith('wqi-model-v') and filename.endswith('.pkl'):
                    # Extract version from filename
                    version = filename.replace('wqi-model-v', '').replace('.pkl', '')
                    versions.append(version)
            return sorted(versions)
        except Exception as e:
            logger.error(f"Error listing model versions: {e}")
            return []
    
    def test_model_inference(self, version: str = "1.0") -> Dict[str, Any]:
        """
        Test model inference with sample data
        
        Args:
            version: Model version to test
            
        Returns:
            Test results
        """
        models = self.load_models(version)
        
        # Test data (normal water quality)
        test_features = [7.0, 1.5, 200, 25.0, 60.0, 10.0, 76.0, 12, 6, 1, 175.0, 0.0075, 0.0, 0.0]
        
        import numpy as np
        features = np.array(test_features).reshape(1, -1)
        features_scaled = models['scaler'].transform(features)
        
        # WQI prediction
        wqi_pred = models['wqi_model'].predict(features_scaled)[0]
        
        # Anomaly prediction
        anomaly_pred = models['anomaly_model'].predict(features_scaled)[0]
        anomaly_proba = models['anomaly_model'].predict_proba(features_scaled)[0]
        
        anomaly_classes = ['normal', 'sensor_fault', 'contamination']
        anomaly_type = anomaly_classes[anomaly_pred]
        confidence = max(anomaly_proba)
        
        return {
            'version': version,
            'test_features': test_features,
            'wqi_prediction': float(wqi_pred),
            'anomaly_type': anomaly_type,
            'confidence': float(confidence),
            'status': 'success'
        }


def main():
    """
    Test the local model loader
    """
    loader = LocalModelLoader("models")
    
    # List available versions
    versions = loader.list_available_versions()
    print(f"Available model versions: {versions}")
    
    if versions:
        version = versions[0]
        
        # Get model info
        info = loader.get_model_info(version)
        print(f"\nModel v{version} info:")
        print(f"  Created: {info.get('created_at', 'Unknown')}")
        print(f"  Training samples: {info.get('training_samples', 'Unknown')}")
        print(f"  WQI R² score: {info.get('wqi_model', {}).get('r2_score', 'Unknown')}")
        print(f"  Anomaly accuracy: {info.get('anomaly_model', {}).get('accuracy', 'Unknown')}")
        
        # Test inference
        result = loader.test_model_inference(version)
        print(f"\nInference test:")
        print(f"  WQI: {result['wqi_prediction']:.2f}")
        print(f"  Anomaly: {result['anomaly_type']} (confidence: {result['confidence']:.3f})")
    else:
        print("No models found. Run create_initial_models.py first.")


if __name__ == "__main__":
    main()