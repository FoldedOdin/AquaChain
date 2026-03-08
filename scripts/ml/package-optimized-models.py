"""
Package optimized custom models for SageMaker deployment
Uses smaller custom models (14 MB) instead of large v1.0 models (1.2 GB)
Creates model.tar.gz with RandomForest-compatible inference script
"""

import os
import tarfile
import shutil
import boto3
from datetime import datetime
import sys


def create_inference_script_randomforest():
    """Create inference.py script for RandomForest models"""
    
    inference_code = '''"""
SageMaker inference script for AquaChain WQI prediction
Uses RandomForest models (custom version - optimized for size)
"""

import json
import pickle
import numpy as np
from datetime import datetime
import os


def model_fn(model_dir):
    """
    Load models from the model directory
    Called once when the endpoint starts
    
    Uses pickle format for RandomForest models
    """
    print("Loading models...")
    print(f"Model directory: {model_dir}")
    print(f"Files in directory: {os.listdir(model_dir)}")
    
    try:
        # Load RandomForest models (pickle format)
        wqi_model_path = os.path.join(model_dir, 'wqi_model.pkl')
        anomaly_model_path = os.path.join(model_dir, 'anomaly_model.pkl')
        scaler_path = os.path.join(model_dir, 'feature_scaler.pkl')
        
        print(f"Loading WQI model from: {wqi_model_path}")
        with open(wqi_model_path, 'rb') as f:
            wqi_model = pickle.load(f)
        print(f"✓ Loaded WQI model: {type(wqi_model).__name__}")
        
        print(f"Loading Anomaly model from: {anomaly_model_path}")
        with open(anomaly_model_path, 'rb') as f:
            anomaly_model = pickle.load(f)
        print(f"✓ Loaded Anomaly model: {type(anomaly_model).__name__}")
        
        print(f"Loading feature scaler from: {scaler_path}")
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        print(f"✓ Loaded feature scaler: {type(scaler).__name__}")
        
        return {
            'wqi_model': wqi_model,
            'anomaly_model': anomaly_model,
            'scaler': scaler
        }
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        import traceback
        traceback.print_exc()
        raise


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
    try:
        features = input_data['features']
        
        # Scale features
        scaled_features = model['scaler'].transform(features)
        
        # Predict WQI
        wqi_prediction = model['wqi_model'].predict(scaled_features)[0]
        wqi = float(max(0, min(100, wqi_prediction)))
        
        # Predict anomaly
        anomaly_prediction_probs = model['anomaly_model'].predict_proba(scaled_features)[0]
        anomaly_prediction = int(np.argmax(anomaly_prediction_probs))
        confidence = float(np.max(anomaly_prediction_probs))
        
        anomaly_classes = ['normal', 'sensor_fault', 'contamination']
        anomaly_type = anomaly_classes[min(anomaly_prediction, len(anomaly_classes) - 1)]
        
        # Get feature importance from WQI model
        feature_importance = {}
        feature_names = input_data.get('feature_names', [])
        
        if hasattr(model['wqi_model'], 'feature_importances_'):
            importances = model['wqi_model'].feature_importances_
            for i, name in enumerate(feature_names):
                if i < len(importances):
                    feature_importance[name] = round(float(importances[i]), 4)
        
        return {
            'wqi': round(wqi, 2),
            'anomalyType': anomaly_type,
            'confidence': round(confidence, 3),
            'featureImportance': feature_importance,
            'modelVersion': 'sagemaker-custom-v1.0'
        }
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        raise


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
        readings.get('humidity', 60.0),  # Default humidity if not provided
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
        'pH', 'turbidity', 'tds', 'temperature', 'humidity',
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


def package_optimized_models(models_dir: str, output_dir: str):
    """
    Package optimized models into SageMaker-compatible tar.gz
    
    Args:
        models_dir: Directory containing optimized models
        output_dir: Directory to save packaged model
    """
    print("\n" + "="*60)
    print("Packaging Optimized Models for SageMaker")
    print("="*60)
    
    # Create temporary directory
    temp_dir = os.path.join(output_dir, 'temp_package')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy model files
        model_files = [
            ('wqi_model.pkl', 'WQI Model (RandomForest)'),
            ('anomaly_model.pkl', 'Anomaly Model (RandomForest)'),
            ('feature_scaler.pkl', 'Feature Scaler')
        ]
        
        total_size_mb = 0
        for filename, description in model_files:
            src = os.path.join(models_dir, filename)
            dst = os.path.join(temp_dir, filename)
            
            if os.path.exists(src):
                shutil.copy(src, dst)
                file_size_mb = os.path.getsize(src) / (1024 * 1024)
                total_size_mb += file_size_mb
                print(f"✓ Copied {description}: {file_size_mb:.2f} MB")
            else:
                print(f"❌ Missing: {filename}")
                raise FileNotFoundError(f"Required file not found: {src}")
        
        print(f"\nTotal model size: {total_size_mb:.2f} MB")
        
        # Create inference script
        print("\nCreating inference script...")
        inference_script = create_inference_script_randomforest()
        with open(os.path.join(temp_dir, 'inference.py'), 'w', encoding='utf-8') as f:
            f.write(inference_script)
        print("✓ Created inference.py (RandomForest compatible)")
        
        # Create requirements.txt
        print("\nCreating requirements.txt...")
        requirements = """numpy==1.26.3
scikit-learn==1.4.0
scipy==1.11.4
"""
        with open(os.path.join(temp_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write(requirements)
        print("✓ Created requirements.txt (with scipy dependency)")
        
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
        print(f"  Compression ratio: {(1 - package_size_mb / total_size_mb) * 100:.1f}%")
        
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
                    'model-version': 'custom-v1.0',
                    'model-type': 'randomforest',
                    'format': 'pickle-optimized'
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
    print("SageMaker Model Packaging - Optimized Custom Models")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    
    models_dir = os.path.join(project_root, 'ml_models_optimized')
    output_dir = os.path.join(project_root, 'lambda', 'ml_inference', 'sagemaker_models')
    
    # Configuration
    bucket_name = 'aquachain-ml-models-dev-758346259059'
    s3_key = 'ml-models/current/model.tar.gz'
    
    print(f"Models directory: {models_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Verify models exist
    required_files = ['wqi_model.pkl', 'anomaly_model.pkl', 'feature_scaler.pkl']
    missing_files = []
    
    for filename in required_files:
        filepath = os.path.join(models_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
    
    if missing_files:
        print("❌ Missing required files:")
        for filename in missing_files:
            print(f"   - {filename}")
        print("\nRun: python scripts/ml/convert-custom-models.py")
        return 1
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Package models
    packaged_model = package_optimized_models(models_dir, output_dir)
    
    # Upload to S3
    s3_uri = upload_to_s3(packaged_model, bucket_name, s3_key)
    
    # Save S3 URI
    uri_file = os.path.join(output_dir, 'model_s3_uri.txt')
    with open(uri_file, 'w') as f:
        f.write(s3_uri)
    
    # Summary
    print("\n" + "="*60)
    print("SUCCESS! Optimized Model Packaging Complete")
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
    print("2. Monitor endpoint creation (should be much faster now!):")
    print("   cd scripts/ml")
    print("   .\\monitor-endpoint.bat")
    print()
    print("3. Test inference:")
    print("   .\\test-inference.bat")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
