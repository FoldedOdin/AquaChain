"""
Package XGBoost native format models for SageMaker deployment
Creates model.tar.gz with updated inference script
"""

import os
import tarfile
import shutil
import boto3
from datetime import datetime
import sys


def create_inference_script_native():
    """Create inference.py script that uses XGBoost native format"""
    
    inference_code = '''"""
SageMaker inference script for AquaChain WQI prediction
Uses XGBoost native format (JSON) to avoid scipy/numpy version conflicts
"""

import json
import pickle
import numpy as np
from datetime import datetime
import os
import xgboost as xgb


def model_fn(model_dir):
    """
    Load models from the model directory
    Called once when the endpoint starts
    
    Uses XGBoost native format for WQI and Anomaly models
    Uses pickle for feature scaler (sklearn StandardScaler)
    """
    print("Loading models...")
    
    # Load XGBoost models in native format (no scipy dependency)
    wqi_model = xgb.Booster()
    wqi_model.load_model(os.path.join(model_dir, 'wqi_model.json'))
    print("✓ Loaded WQI model (XGBoost native format)")
    
    anomaly_model = xgb.Booster()
    anomaly_model.load_model(os.path.join(model_dir, 'anomaly_model.json'))
    print("✓ Loaded Anomaly model (XGBoost native format)")
    
    # Load feature scaler (still pickle, but doesn't use scipy)
    scaler = pickle.load(open(os.path.join(model_dir, 'feature_scaler.pkl'), 'rb'))
    print("✓ Loaded feature scaler")
    
    return {
        'wqi_model': wqi_model,
        'anomaly_model': anomaly_model,
        'scaler': scaler
    }


def input_fn(request_body, content_type='application/json'):
    """
    Deserialize and prepare the prediction input
    """
    if content_type == 'application/json':
        input_data = json.loads(request_body)
        return prepare_features(input_data)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model):
    """
    Perform prediction on the deserialized input data
    """
    features = input_data['features']
    
    # Scale features
    scaled_features = model['scaler'].transform(features)
    
    # Convert to DMatrix for XGBoost native format
    dmatrix = xgb.DMatrix(scaled_features)
    
    # Predict WQI
    wqi_prediction = model['wqi_model'].predict(dmatrix)[0]
    wqi = float(max(0, min(100, wqi_prediction)))
    
    # Predict anomaly
    anomaly_prediction_probs = model['anomaly_model'].predict(dmatrix)
    
    # For multi-class, get class with highest probability
    if len(anomaly_prediction_probs.shape) > 1:
        anomaly_prediction = int(np.argmax(anomaly_prediction_probs[0]))
        confidence = float(np.max(anomaly_prediction_probs[0]))
    else:
        # Binary classification
        anomaly_prediction = int(anomaly_prediction_probs[0] > 0.5)
        confidence = float(abs(anomaly_prediction_probs[0] - 0.5) * 2)
    
    anomaly_classes = ['normal', 'sensor_fault', 'contamination']
    anomaly_type = anomaly_classes[min(anomaly_prediction, len(anomaly_classes) - 1)]
    
    # Get feature importance from WQI model
    feature_importance = {}
    feature_names = input_data.get('feature_names', [])
    
    # XGBoost native format uses get_score() for feature importance
    importance_dict = model['wqi_model'].get_score(importance_type='weight')
    for i, name in enumerate(feature_names):
        feature_key = f'f{i}'  # XGBoost uses f0, f1, f2, etc.
        if feature_key in importance_dict:
            feature_importance[name] = round(float(importance_dict[feature_key]), 4)
    
    return {
        'wqi': round(wqi, 2),
        'anomalyType': anomaly_type,
        'confidence': round(confidence, 3),
        'featureImportance': feature_importance,
        'modelVersion': 'sagemaker-native-v1.0'
    }


def output_fn(prediction, accept='application/json'):
    """
    Serialize the prediction result
    """
    if accept == 'application/json':
        return json.dumps(prediction), accept
    else:
        raise ValueError(f"Unsupported accept type: {accept}")


def prepare_features(input_data):
    """
    Prepare feature vector from input data
    """
    readings = input_data['readings']
    location = input_data['location']
    timestamp = input_data['timestamp']
    
    # Parse timestamp
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    # Build feature vector (same as training)
    features = [
        readings['pH'],
        readings['turbidity'],
        readings['tds'],
        readings['temperature'],
        location['latitude'],
        location['longitude'],
        dt.hour,
        dt.month,
        dt.weekday(),
        readings['pH'] * readings['temperature'],
        readings['turbidity'] / max(readings['tds'], 1),
        abs(readings['pH'] - 7.0),
        readings['temperature'] - 25.0
    ]
    
    feature_names = [
        'pH', 'turbidity', 'tds', 'temperature',
        'latitude', 'longitude',
        'hour', 'month', 'weekday',
        'pH_temp_interaction', 'turbidity_tds_ratio',
        'pH_deviation', 'temp_deviation'
    ]
    
    return {
        'features': np.array(features).reshape(1, -1),
        'feature_names': feature_names
    }
'''
    
    return inference_code


def package_native_models(models_dir: str, output_dir: str):
    """
    Package native format models into SageMaker-compatible tar.gz
    
    Args:
        models_dir: Directory containing native format models
        output_dir: Directory to save packaged model
    """
    print("\n" + "="*60)
    print("Packaging Native Format Models for SageMaker")
    print("="*60)
    
    # Create temporary directory
    temp_dir = os.path.join(output_dir, 'temp_package')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy model files
        model_files = [
            ('wqi_model.json', 'WQI Model (XGBoost native)'),
            ('anomaly_model.json', 'Anomaly Model (XGBoost native)'),
            ('feature_scaler.pkl', 'Feature Scaler (pickle)')
        ]
        
        for filename, description in model_files:
            src = os.path.join(models_dir, filename)
            dst = os.path.join(temp_dir, filename)
            
            if os.path.exists(src):
                shutil.copy(src, dst)
                file_size_kb = os.path.getsize(src) / 1024
                print(f"✓ Copied {description}: {file_size_kb:.2f} KB")
            else:
                print(f"❌ Missing: {filename}")
                raise FileNotFoundError(f"Required file not found: {src}")
        
        # Create inference script
        print("\nCreating inference script...")
        inference_script = create_inference_script_native()
        with open(os.path.join(temp_dir, 'inference.py'), 'w', encoding='utf-8') as f:
            f.write(inference_script)
        print("✓ Created inference.py (uses XGBoost native format)")
        
        # Create requirements.txt (minimal dependencies)
        print("\nCreating requirements.txt...")
        requirements = """numpy==1.26.3
scikit-learn==1.4.0
xgboost==2.0.3
"""
        with open(os.path.join(temp_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write(requirements)
        print("✓ Created requirements.txt")
        
        # Create model.tar.gz
        print("\nCreating model.tar.gz...")
        output_file = os.path.join(output_dir, 'model.tar.gz')
        
        with tarfile.open(output_file, 'w:gz') as tar:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                tar.add(file_path, arcname=file)
                print(f"  Added: {file}")
        
        # Get package size
        package_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"\n✓ Created model.tar.gz: {package_size_mb:.2f} MB")
        
        return output_file
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("✓ Cleaned up temporary files")


def upload_to_s3(local_file: str, bucket_name: str, s3_key: str):
    """
    Upload packaged model to S3
    
    Args:
        local_file: Local path to model.tar.gz
        bucket_name: S3 bucket name
        s3_key: S3 key (path) for the model
    """
    print("\n" + "="*60)
    print("Uploading to S3")
    print("="*60)
    print(f"Bucket: {bucket_name}")
    print(f"Key: {s3_key}")
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    try:
        # Upload with metadata
        s3_client.upload_file(
            local_file,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ServerSideEncryption': 'aws:kms',
                'Metadata': {
                    'upload-timestamp': datetime.now().isoformat(),
                    'model-version': '1.0-native',
                    'model-type': 'xgboost-native',
                    'format': 'json'
                }
            }
        )
        
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        print(f"\n✓ Upload successful!")
        print(f"S3 URI: {s3_uri}")
        
        return s3_uri
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        raise


def main():
    """Main execution"""
    
    print("="*60)
    print("SageMaker Model Packaging - Native Format")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    
    models_dir = os.path.join(project_root, 'ml_models_native')
    output_dir = os.path.join(project_root, 'lambda', 'ml_inference', 'sagemaker_models')
    
    # Configuration
    bucket_name = 'aquachain-ml-models-dev-758346259059'
    s3_key = 'ml-models/current/model.tar.gz'
    
    print(f"Models directory: {models_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Verify models exist
    required_files = ['wqi_model.json', 'anomaly_model.json', 'feature_scaler.pkl']
    missing_files = []
    
    for filename in required_files:
        filepath = os.path.join(models_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
    
    if missing_files:
        print("❌ Missing required files:")
        for filename in missing_files:
            print(f"   - {filename}")
        print("\nRun: python scripts/ml/convert-models-to-native.py")
        return 1
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Package models
    packaged_model = package_native_models(models_dir, output_dir)
    
    # Upload to S3
    s3_uri = upload_to_s3(packaged_model, bucket_name, s3_key)
    
    # Save S3 URI
    uri_file = os.path.join(output_dir, 'model_s3_uri.txt')
    with open(uri_file, 'w') as f:
        f.write(s3_uri)
    
    # Summary
    print("\n" + "="*60)
    print("SUCCESS! Model Packaging Complete")
    print("="*60)
    print(f"\nPackaged file: {packaged_model}")
    print(f"S3 URI: {s3_uri}")
    print(f"URI saved to: {uri_file}")
    
    print("\n" + "="*60)
    print("Next Steps")
    print("="*60)
    print("1. Deploy SageMaker stack:")
    print("   cd infrastructure/cdk")
    print("   cdk deploy AquaChain-SageMaker-dev")
    print()
    print("2. Monitor endpoint creation:")
    print("   cd scripts/ml")
    print("   .\\monitor-endpoint.bat")
    print()
    print("3. Test inference:")
    print("   .\\test-inference.bat")
    print()
    print("4. Update Lambda:")
    print("   .\\update-ml-lambda.bat")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
