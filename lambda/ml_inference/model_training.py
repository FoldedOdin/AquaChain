"""
ML model training script for AquaChain WQI calculation
Production model structure and training process
"""

import numpy as np
import pickle
import json
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, classification_report
from datetime import datetime
import boto3

def generate_synthetic_data(n_samples: int = 10000):
    """
    Generate synthetic water quality data for training
    """
    np.random.seed(42)
    
    # Generate base sensor readings
    pH = np.random.normal(7.0, 1.5, n_samples)
    pH = np.clip(pH, 0, 14)
    
    turbidity = np.random.exponential(2.0, n_samples)
    turbidity = np.clip(turbidity, 0, 100)
    
    tds = np.random.normal(300, 200, n_samples)
    tds = np.clip(tds, 0, 2000)
    
    temperature = np.random.normal(25, 8, n_samples)
    temperature = np.clip(temperature, 0, 50)
    
    humidity = np.random.normal(60, 20, n_samples)
    humidity = np.clip(humidity, 0, 100)
    
    # Generate location features (example coordinates)
    latitude = np.random.uniform(8.0, 12.0, n_samples)  # Kerala region
    longitude = np.random.uniform(75.0, 78.0, n_samples)
    
    # Generate temporal features
    hour = np.random.randint(0, 24, n_samples)
    month = np.random.randint(1, 13, n_samples)
    weekday = np.random.randint(0, 7, n_samples)
    
    # Create derived features
    pH_temp_interaction = pH * temperature
    turbidity_tds_ratio = turbidity / np.maximum(tds, 1)
    pH_deviation = np.abs(pH - 7.0)
    temp_deviation = temperature - 25.0
    
    # Combine all features
    features = np.column_stack([
        pH, turbidity, tds, temperature, humidity,
        latitude, longitude, hour, month, weekday,
        pH_temp_interaction, turbidity_tds_ratio, pH_deviation, temp_deviation
    ])
    
    # Generate WQI targets (synthetic formula)
    wqi = calculate_synthetic_wqi(pH, turbidity, tds, temperature, humidity)
    
    # Generate anomaly labels
    anomaly_labels = generate_anomaly_labels(pH, turbidity, tds, temperature, humidity)
    
    return features, wqi, anomaly_labels

def calculate_synthetic_wqi(pH, turbidity, tds, temperature, humidity):
    """
    Calculate synthetic WQI for training data
    """
    # Normalize each parameter
    pH_score = 100 - np.abs(pH - 7.0) * 20
    pH_score = np.clip(pH_score, 0, 100)
    
    turbidity_score = np.where(turbidity <= 1, 100,
                              np.where(turbidity <= 5, 80,
                                      np.where(turbidity <= 10, 60,
                                              np.where(turbidity <= 25, 40,
                                                      np.maximum(0, 40 - (turbidity - 25) * 2)))))
    
    tds_score = np.where(tds <= 300, 100,
                        np.where(tds <= 600, 80,
                                np.where(tds <= 900, 60,
                                        np.where(tds <= 1200, 40,
                                                np.maximum(0, 40 - (tds - 1200) * 0.02)))))
    
    temp_score = np.where((temperature >= 20) & (temperature <= 30), 100,
                         100 - np.minimum(np.abs(temperature - 20), np.abs(temperature - 30)) * 5)
    temp_score = np.clip(temp_score, 0, 100)
    
    humidity_score = np.where((humidity >= 40) & (humidity <= 70), 100,
                             np.where(humidity < 40, 100 - (40 - humidity) * 2,
                                     100 - (humidity - 70) * 2))
    humidity_score = np.clip(humidity_score, 0, 100)
    
    # Weighted average
    weights = [0.25, 0.25, 0.20, 0.15, 0.15]
    wqi = (pH_score * weights[0] + turbidity_score * weights[1] + 
           tds_score * weights[2] + temp_score * weights[3] + 
           humidity_score * weights[4])
    
    # Add some noise
    wqi += np.random.normal(0, 5, len(wqi))
    return np.clip(wqi, 0, 100)

def generate_anomaly_labels(pH, turbidity, tds, temperature, humidity):
    """
    Generate anomaly labels for training data
    """
    labels = np.zeros(len(pH), dtype=int)  # 0 = normal
    
    # Contamination events (label = 2)
    contamination_mask = ((pH < 6.0) | (pH > 9.0)) & ((turbidity > 10) | (tds > 1000))
    contamination_mask |= (turbidity > 50) | (tds > 2000)
    labels[contamination_mask] = 2
    
    # Sensor fault events (label = 1)
    sensor_fault_mask = ((pH < 6.0) | (pH > 9.0)) & ~contamination_mask
    sensor_fault_mask |= (temperature < 0) | (temperature > 50)
    sensor_fault_mask |= (humidity > 95) | (humidity < 10)
    labels[sensor_fault_mask] = 1
    
    return labels

def train_models():
    """
    Train WQI regression and anomaly detection models
    """
    print("Generating synthetic training data...")
    features, wqi_targets, anomaly_labels = generate_synthetic_data(10000)
    
    # Split data
    X_train, X_test, y_wqi_train, y_wqi_test, y_anom_train, y_anom_test = train_test_split(
        features, wqi_targets, anomaly_labels, test_size=0.2, random_state=42
    )
    
    # Scale features
    print("Training feature scaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train WQI regression model
    print("Training WQI regression model...")
    wqi_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    wqi_model.fit(X_train_scaled, y_wqi_train)
    
    # Evaluate WQI model
    wqi_pred = wqi_model.predict(X_test_scaled)
    wqi_rmse = np.sqrt(mean_squared_error(y_wqi_test, wqi_pred))
    print(f"WQI Model RMSE: {wqi_rmse:.2f}")
    
    # Train anomaly detection model
    print("Training anomaly detection model...")
    anomaly_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    anomaly_model.fit(X_train_scaled, y_anom_train)
    
    # Evaluate anomaly model
    anom_pred = anomaly_model.predict(X_test_scaled)
    print("Anomaly Detection Classification Report:")
    print(classification_report(y_anom_test, anom_pred, 
                               target_names=['normal', 'sensor_fault', 'contamination']))
    
    return wqi_model, anomaly_model, scaler

def save_models_to_s3(wqi_model, anomaly_model, scaler, version="1.0"):
    """
    Save trained models to S3
    """
    s3_client = boto3.client('s3')
    bucket = 'aquachain-data-lake'
    prefix = f'ml-models/current/'
    
    # Save models as pickle files
    models = {
        f'wqi-model-v{version}.pkl': wqi_model,
        f'anomaly-model-v{version}.pkl': anomaly_model,
        f'feature-scaler-v{version}.pkl': scaler
    }
    
    for filename, model in models.items():
        model_bytes = pickle.dumps(model)
        s3_client.put_object(
            Bucket=bucket,
            Key=f'{prefix}{filename}',
            Body=model_bytes,
            ContentType='application/octet-stream',
            ServerSideEncryption='aws:kms'
        )
        print(f"Saved {filename} to S3")
    
    # Save version info
    version_info = {
        'version': version,
        'timestamp': datetime.utcnow().isoformat(),
        'wqi_model_rmse': 5.2,  # Example metric
        'anomaly_model_accuracy': 0.95,  # Example metric
        'feature_count': 14
    }
    
    s3_client.put_object(
        Bucket=bucket,
        Key=f'{prefix}wqi-model-version.json',
        Body=json.dumps(version_info, indent=2),
        ContentType='application/json',
        ServerSideEncryption='aws:kms'
    )
    print(f"Saved version info for v{version}")

if __name__ == "__main__":
    # Train models
    wqi_model, anomaly_model, scaler = train_models()
    
    # Save to S3 (uncomment when ready to deploy)
    # save_models_to_s3(wqi_model, anomaly_model, scaler, "1.0")
    
    print("Model training completed!")