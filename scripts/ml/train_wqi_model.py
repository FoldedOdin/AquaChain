#!/usr/bin/env python3
"""
AquaChain Water Quality Index (WQI) Model Training Script

This script trains an XGBoost model to predict water quality index from sensor readings.
Uses synthetic data that matches the expected sensor input format.
"""

import os
import json
import pickle
import tarfile
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import boto3
from datetime import datetime

# Configuration
MODEL_BUCKET = "aquachain-ml-models-dev-758346259059"
MODEL_PREFIX = "models/wqi-model"
REGION = "ap-south-1"

def generate_synthetic_data(n_samples=10000):
    """Generate synthetic water quality data for training"""
    np.random.seed(42)
    
    # Generate realistic sensor readings
    data = []
    
    for _ in range(n_samples):
        # pH: 6.0-8.5 (normal range), with some outliers
        ph = np.random.normal(7.2, 0.8)
        ph = np.clip(ph, 4.0, 10.0)
        
        # Turbidity: 0-10 NTU (normal), with some high values
        turbidity = np.random.exponential(2.0)
        turbidity = np.clip(turbidity, 0, 50)
        
        # TDS: 100-800 ppm (normal), with some high values
        tds = np.random.normal(400, 150)
        tds = np.clip(tds, 50, 1500)
        
        # Temperature: 15-35°C (normal range)
        temperature = np.random.normal(25, 5)
        temperature = np.clip(temperature, 10, 40)
        
        # Calculate WQI based on water quality standards
        wqi_score = calculate_wqi(ph, turbidity, tds, temperature)
        wqi_class = classify_wqi(wqi_score)
        
        data.append({
            'pH': ph,
            'turbidity': turbidity,
            'tds': tds,
            'temperature': temperature,
            'wqi_score': wqi_score,
            'wqi_class': wqi_class
        })
    
    return pd.DataFrame(data)

def calculate_wqi(ph, turbidity, tds, temperature):
    """Calculate Water Quality Index based on sensor readings"""
    # pH sub-index (optimal: 7.0-8.5)
    if 7.0 <= ph <= 8.5:
        ph_score = 100
    elif 6.5 <= ph < 7.0 or 8.5 < ph <= 9.0:
        ph_score = 80
    elif 6.0 <= ph < 6.5 or 9.0 < ph <= 9.5:
        ph_score = 60
    else:
        ph_score = 20
    
    # Turbidity sub-index (optimal: <1 NTU)
    if turbidity <= 1:
        turbidity_score = 100
    elif turbidity <= 5:
        turbidity_score = 80
    elif turbidity <= 10:
        turbidity_score = 60
    elif turbidity <= 25:
        turbidity_score = 40
    else:
        turbidity_score = 20
    
    # TDS sub-index (optimal: 300-600 ppm)
    if 300 <= tds <= 600:
        tds_score = 100
    elif 150 <= tds < 300 or 600 < tds <= 900:
        tds_score = 80
    elif 50 <= tds < 150 or 900 < tds <= 1200:
        tds_score = 60
    else:
        tds_score = 40
    
    # Temperature sub-index (optimal: 20-30°C)
    if 20 <= temperature <= 30:
        temp_score = 100
    elif 15 <= temperature < 20 or 30 < temperature <= 35:
        temp_score = 90
    else:
        temp_score = 70
    
    # Weighted average (pH and turbidity are most critical)
    wqi = (ph_score * 0.35 + turbidity_score * 0.35 + tds_score * 0.20 + temp_score * 0.10)
    return round(wqi, 2)

def classify_wqi(wqi_score):
    """Classify WQI score into quality categories"""
    if wqi_score >= 90:
        return 0  # Excellent
    elif wqi_score >= 70:
        return 1  # Good
    elif wqi_score >= 50:
        return 2  # Fair
    elif wqi_score >= 25:
        return 3  # Poor
    else:
        return 4  # Very Poor

def train_model():
    """Train XGBoost model for water quality prediction"""
    print("Generating synthetic training data...")
    df = generate_synthetic_data(10000)
    
    # Prepare features and target
    features = ['pH', 'turbidity', 'tds', 'temperature']
    X = df[features]
    y = df['wqi_class']
    
    print(f"Dataset shape: {X.shape}")
    print(f"Class distribution:\n{y.value_counts().sort_index()}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train XGBoost model
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Model accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    
    # Get unique classes in test set
    unique_classes = sorted(np.unique(np.concatenate([y_test, y_pred])))
    quality_labels = ['Excellent', 'Good', 'Fair', 'Poor', 'Very Poor']
    active_labels = [quality_labels[i] for i in unique_classes]
    
    print(classification_report(y_test, y_pred, 
                              labels=unique_classes,
                              target_names=active_labels))
    
    return model, features

def create_inference_script():
    """Create inference script for SageMaker XGBoost container"""
    inference_code = '''#!/usr/bin/env python3

import os
import json
import pickle
import numpy as np
import xgboost as xgb

def model_fn(model_dir):
    """
    Load model from the model directory.
    SageMaker will call this function to load the model.
    """
    try:
        model_path = os.path.join(model_dir, "model.pkl")
        print(f"Loading model from: {model_path}")
        
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        
        print(f"Model loaded successfully: {type(model)}")
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise

def input_fn(request_body, request_content_type):
    """
    Parse input data for prediction.
    SageMaker will call this function to parse the request.
    """
    try:
        print(f"Processing input with content type: {request_content_type}")
        print(f"Request body: {request_body}")
        
        if request_content_type == "text/csv":
            # Parse CSV input: pH,turbidity,tds,temperature
            values = [float(x.strip()) for x in request_body.split(",")]
            if len(values) != 4:
                raise ValueError("Expected 4 values: pH,turbidity,tds,temperature")
            return np.array([values])
            
        elif request_content_type == "application/json":
            data = json.loads(request_body)
            if isinstance(data, dict):
                # Extract values in the correct order
                values = [
                    float(data["pH"]), 
                    float(data["turbidity"]), 
                    float(data["tds"]), 
                    float(data["temperature"])
                ]
            elif isinstance(data, list):
                values = [float(x) for x in data]
            else:
                raise ValueError("JSON data must be dict or list")
                
            if len(values) != 4:
                raise ValueError("Expected 4 values: pH,turbidity,tds,temperature")
            return np.array([values])
            
        else:
            raise ValueError(f"Unsupported content type: {request_content_type}")
            
    except Exception as e:
        print(f"Error in input_fn: {str(e)}")
        raise

def predict_fn(input_data, model):
    """
    Make prediction using the loaded model.
    SageMaker will call this function to make predictions.
    """
    try:
        print(f"Making prediction for input: {input_data}")
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0]
        
        # Map class to quality label
        quality_labels = ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
        
        result = {
            "prediction": int(prediction),
            "quality": quality_labels[int(prediction)],
            "confidence": float(probability[int(prediction)]),
            "probabilities": {
                quality_labels[i]: float(prob) 
                for i, prob in enumerate(probability)
            }
        }
        
        print(f"Prediction result: {result}")
        return result
        
    except Exception as e:
        print(f"Error in predict_fn: {str(e)}")
        raise

def output_fn(prediction, content_type):
    """
    Format the prediction output.
    SageMaker will call this function to format the response.
    """
    try:
        if content_type == "application/json":
            return json.dumps(prediction)
        else:
            return str(prediction)
    except Exception as e:
        print(f"Error in output_fn: {str(e)}")
        raise
'''
    return inference_code

def package_model(model, features):
    """Package model for SageMaker deployment - XGBoost native format only"""
    print("Packaging model for SageMaker...")
    
    # Create temporary directory
    os.makedirs("temp_model", exist_ok=True)
    
    # Save model in XGBoost format (this is what SageMaker XGBoost container expects)
    model_path = "temp_model/xgboost-model"
    model.save_model(model_path)
    
    # Create model tarball with ONLY the model file (no features.json)
    # The XGBoost container gets confused if there are extra files
    with tarfile.open("model.tar.gz", "w:gz") as tar:
        tar.add("temp_model/xgboost-model", arcname="xgboost-model")
    
    print("Model packaged successfully: model.tar.gz")
    print("Note: Only xgboost-model file included (no features.json)")
    return "model.tar.gz"

def upload_to_s3(model_path):
    """Upload model to S3"""
    print(f"Uploading model to S3: s3://{MODEL_BUCKET}/{MODEL_PREFIX}/")
    
    s3_client = boto3.client('s3', region_name=REGION)
    
    # Upload model tarball
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    s3_key = f"{MODEL_PREFIX}/{timestamp}/model.tar.gz"
    
    s3_client.upload_file(model_path, MODEL_BUCKET, s3_key)
    
    # Also upload to latest
    latest_key = f"{MODEL_PREFIX}/latest/model.tar.gz"
    s3_client.upload_file(model_path, MODEL_BUCKET, latest_key)
    
    model_url = f"s3://{MODEL_BUCKET}/{latest_key}"
    print(f"Model uploaded to: {model_url}")
    
    return model_url

def cleanup():
    """Clean up temporary files"""
    import shutil
    if os.path.exists("temp_model"):
        shutil.rmtree("temp_model")
    if os.path.exists("model.tar.gz"):
        os.remove("model.tar.gz")

def main():
    """Main training pipeline"""
    try:
        print("=== AquaChain WQI Model Training ===")
        
        # Train model
        model, features = train_model()
        
        # Package model
        model_path = package_model(model, features)
        
        # Upload to S3
        model_url = upload_to_s3(model_path)
        
        print(f"\n✅ Training completed successfully!")
        print(f"Model URL: {model_url}")
        print(f"Features: {features}")
        
        return model_url
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    main()