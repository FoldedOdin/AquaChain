"""
Create initial ML models for development and testing
This script generates basic trained models that can be used before the full training pipeline is run
"""

import numpy as np
import pickle
import json
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import os

from synthetic_data_generator import SyntheticDataGenerator


def create_initial_models():
    """
    Create initial trained models for development/testing
    """
    print("Creating initial ML models for development...")
    
    # Generate small training dataset
    generator = SyntheticDataGenerator(seed=42)
    features_df, wqi_targets, anomaly_labels = generator.generate_dataset(
        n_samples=5000,  # Smaller dataset for quick training
        contamination_rate=0.05,
        sensor_fault_rate=0.03
    )
    
    # Extract features
    feature_columns = [
        'pH', 'turbidity', 'tds', 'temperature', 'latitude', 'longitude', 'hour', 'month', 'weekday',
        'pH_temp_interaction', 'turbidity_tds_ratio', 
        'pH_deviation', 'temp_deviation'
    ]
    
    X = features_df[feature_columns].values
    y_wqi = wqi_targets
    y_anomaly = anomaly_labels
    
    print(f"Training data: {len(X)} samples, {len(feature_columns)} features")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train WQI regression model
    print("Training WQI regression model...")
    wqi_model = RandomForestRegressor(
        n_estimators=50,  # Smaller for quick training
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    wqi_model.fit(X_scaled, y_wqi)
    
    # Train anomaly detection model
    print("Training anomaly detection model...")
    anomaly_model = RandomForestClassifier(
        n_estimators=50,  # Smaller for quick training
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    anomaly_model.fit(X_scaled, y_anomaly)
    
    # Evaluate models
    wqi_score = wqi_model.score(X_scaled, y_wqi)
    anomaly_score = anomaly_model.score(X_scaled, y_anomaly)
    
    print(f"WQI Model R² Score: {wqi_score:.4f}")
    print(f"Anomaly Model Accuracy: {anomaly_score:.4f}")
    
    # Create models directory
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    # Save models
    model_version = "1.0"
    
    with open(f"{models_dir}/wqi-model-v{model_version}.pkl", 'wb') as f:
        pickle.dump(wqi_model, f)
    print(f"Saved WQI model to {models_dir}/wqi-model-v{model_version}.pkl")
    
    with open(f"{models_dir}/anomaly-model-v{model_version}.pkl", 'wb') as f:
        pickle.dump(anomaly_model, f)
    print(f"Saved anomaly model to {models_dir}/anomaly-model-v{model_version}.pkl")
    
    with open(f"{models_dir}/feature-scaler-v{model_version}.pkl", 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Saved feature scaler to {models_dir}/feature-scaler-v{model_version}.pkl")
    
    # Save model metadata
    metadata = {
        'version': model_version,
        'created_at': datetime.utcnow().isoformat(),
        'training_samples': len(X),
        'features': feature_columns,
        'wqi_model': {
            'algorithm': 'RandomForestRegressor',
            'n_estimators': 50,
            'r2_score': float(wqi_score)
        },
        'anomaly_model': {
            'algorithm': 'RandomForestClassifier',
            'n_estimators': 50,
            'accuracy': float(anomaly_score)
        },
        'feature_scaler': {
            'algorithm': 'StandardScaler'
        }
    }
    
    with open(f"{models_dir}/model-metadata-v{model_version}.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {models_dir}/model-metadata-v{model_version}.json")
    
    # Save version info (compatible with existing handler)
    version_info = {
        'version': model_version,
        'timestamp': datetime.utcnow().isoformat(),
        'wqi_model_r2': float(wqi_score),
        'anomaly_model_accuracy': float(anomaly_score),
        'feature_count': len(feature_columns)
    }
    
    with open(f"{models_dir}/wqi-model-version.json", 'w') as f:
        json.dump(version_info, f, indent=2)
    print(f"Saved version info to {models_dir}/wqi-model-version.json")
    
    print("\n✅ Initial models created successfully!")
    print(f"Models saved in '{models_dir}/' directory")
    print("\nTo use these models:")
    print("1. Upload to S3: aws s3 sync models/ s3://your-bucket/ml-models/current/")
    print("2. Update Lambda environment variables to point to S3 location")
    print("3. Test inference with the existing handler.py")
    
    return models_dir


def test_models():
    """
    Test the created models with sample data
    """
    print("\nTesting created models...")
    
    models_dir = "models"
    model_version = "1.0"
    
    # Load models
    with open(f"{models_dir}/wqi-model-v{model_version}.pkl", 'rb') as f:
        wqi_model = pickle.load(f)
    
    with open(f"{models_dir}/anomaly-model-v{model_version}.pkl", 'rb') as f:
        anomaly_model = pickle.load(f)
    
    with open(f"{models_dir}/feature-scaler-v{model_version}.pkl", 'rb') as f:
        scaler = pickle.load(f)
    
    # Test with sample data
    test_cases = [
        {
            'name': 'Normal water',
            'features': [7.0, 1.5, 200, 25.0, 60.0, 10.0, 76.0, 12, 6, 1, 175.0, 0.0075, 0.0, 0.0]
        },
        {
            'name': 'Contaminated water',
            'features': [4.5, 50.0, 2000, 25.0, 60.0, 10.0, 76.0, 12, 6, 1, 112.5, 0.025, 2.5, 0.0]
        },
        {
            'name': 'Sensor fault',
            'features': [12.0, 1.0, 200, -5.0, 60.0, 10.0, 76.0, 12, 6, 1, -60.0, 0.005, 5.0, -30.0]
        }
    ]
    
    for test_case in test_cases:
        features = np.array(test_case['features']).reshape(1, -1)
        features_scaled = scaler.transform(features)
        
        wqi_pred = wqi_model.predict(features_scaled)[0]
        anomaly_pred = anomaly_model.predict(features_scaled)[0]
        anomaly_proba = anomaly_model.predict_proba(features_scaled)[0]
        
        anomaly_classes = ['normal', 'sensor_fault', 'contamination']
        anomaly_type = anomaly_classes[anomaly_pred]
        confidence = max(anomaly_proba)
        
        print(f"\n{test_case['name']}:")
        print(f"  WQI: {wqi_pred:.2f}")
        print(f"  Anomaly: {anomaly_type} (confidence: {confidence:.3f})")


if __name__ == "__main__":
    # Create initial models
    models_dir = create_initial_models()
    
    # Test the models
    test_models()
    
    print(f"\n🎯 Ready for development!")
    print(f"Models are in '{models_dir}/' directory")