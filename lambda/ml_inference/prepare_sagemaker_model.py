"""
Prepare trained XGBoost models for SageMaker deployment
Packages models into tar.gz format required by SageMaker
"""

import pickle
import tarfile
import json
import os
import boto3
from datetime import datetime
import shutil


def create_inference_script():
    """Create inference.py script for SageMaker endpoint"""
    
    inference_code = '''"""
SageMaker inference script for AquaChain WQI prediction
"""

import json
import pickle
import numpy as np
from datetime import datetime
import os


def model_fn(model_dir):
    """
    Load model from the model directory
    Called once when the endpoint starts
    """
    wqi_model = pickle.load(open(os.path.join(model_dir, 'wqi_model.pkl'), 'rb'))
    anomaly_model = pickle.load(open(os.path.join(model_dir, 'anomaly_model.pkl'), 'rb'))
    scaler = pickle.load(open(os.path.join(model_dir, 'feature_scaler.pkl'), 'rb'))
    
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
    
    # Predict WQI
    wqi_prediction = model['wqi_model'].predict(scaled_features)[0]
    wqi = float(max(0, min(100, wqi_prediction)))
    
    # Predict anomaly
    anomaly_prediction = model['anomaly_model'].predict(scaled_features)[0]
    anomaly_probabilities = model['anomaly_model'].predict_proba(scaled_features)[0]
    confidence = float(max(anomaly_probabilities))
    
    anomaly_classes = ['normal', 'sensor_fault', 'contamination']
    anomaly_type = anomaly_classes[anomaly_prediction]
    
    # Get feature importance
    feature_importance = {}
    feature_names = input_data.get('feature_names', [])
    if hasattr(model['wqi_model'], 'feature_importances_'):
        importance_scores = model['wqi_model'].feature_importances_
        for i, name in enumerate(feature_names):
            if i < len(importance_scores):
                feature_importance[name] = round(float(importance_scores[i]), 4)
    
    return {
        'wqi': round(wqi, 2),
        'anomalyType': anomaly_type,
        'confidence': round(confidence, 3),
        'featureImportance': feature_importance
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
    
    # Build feature vector
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


def package_model_for_sagemaker(model_dir: str, output_dir: str):
    """
    Package trained models into SageMaker-compatible tar.gz format
    
    Args:
        model_dir: Directory containing trained model files
        output_dir: Directory to save packaged model
    """
    print("Packaging models for SageMaker deployment...")
    
    # Create temporary directory for packaging
    temp_dir = os.path.join(output_dir, 'temp_model')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy model files
        model_files = [
            'wqi-model-v1.0.pkl',
            'anomaly-model-v1.0.pkl',
            'feature-scaler-v1.0.pkl'
        ]
        
        for model_file in model_files:
            src = os.path.join(model_dir, model_file)
            if os.path.exists(src):
                # Rename to standard names for inference script
                if 'wqi-model' in model_file:
                    dst = os.path.join(temp_dir, 'wqi_model.pkl')
                elif 'anomaly-model' in model_file:
                    dst = os.path.join(temp_dir, 'anomaly_model.pkl')
                elif 'feature-scaler' in model_file:
                    dst = os.path.join(temp_dir, 'feature_scaler.pkl')
                
                shutil.copy(src, dst)
                print(f"Copied {model_file} -> {os.path.basename(dst)}")
            else:
                print(f"Warning: {model_file} not found in {model_dir}")
        
        # Create inference script
        inference_script = create_inference_script()
        with open(os.path.join(temp_dir, 'inference.py'), 'w') as f:
            f.write(inference_script)
        print("Created inference.py")
        
        # Create requirements.txt for dependencies
        requirements = """numpy==1.26.3
scikit-learn==1.4.0
xgboost==2.0.3
"""
        with open(os.path.join(temp_dir, 'requirements.txt'), 'w') as f:
            f.write(requirements)
        print("Created requirements.txt")
        
        # Create model.tar.gz
        output_file = os.path.join(output_dir, 'model.tar.gz')
        with tarfile.open(output_file, 'w:gz') as tar:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                tar.add(file_path, arcname=file)
        
        print(f"Created {output_file}")
        
        # Get file size
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"Package size: {file_size_mb:.2f} MB")
        
        return output_file
        
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("Cleaned up temporary files")


def upload_to_s3(local_file: str, bucket_name: str, s3_key: str):
    """
    Upload packaged model to S3
    
    Args:
        local_file: Local path to model.tar.gz
        bucket_name: S3 bucket name
        s3_key: S3 key (path) for the model
    """
    print(f"Uploading to s3://{bucket_name}/{s3_key}...")
    
    s3_client = boto3.client('s3')
    
    try:
        s3_client.upload_file(
            local_file,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ServerSideEncryption': 'aws:kms',
                'Metadata': {
                    'upload-timestamp': datetime.now().isoformat(),
                    'model-version': '1.0',
                    'model-type': 'xgboost-wqi'
                }
            }
        )
        
        print(f"Upload successful: s3://{bucket_name}/{s3_key}")
        
        # Generate S3 URI
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        return s3_uri
        
    except Exception as e:
        print(f"Upload failed: {e}")
        raise


def main():
    """Main execution"""
    
    # Configuration - use existing bucket
    model_dir = '../../ml_models_backup'  # Relative to this script
    output_dir = './sagemaker_models'
    bucket_name = 'aquachain-ml-models-dev-758346259059'  # Existing bucket
    s3_key = 'ml-models/current/model.tar.gz'
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.abspath(os.path.join(script_dir, model_dir))
    output_dir = os.path.abspath(output_dir)
    
    print(f"Model directory: {model_dir}")
    print(f"Output directory: {output_dir}")
    
    # Package model
    packaged_model = package_model_for_sagemaker(model_dir, output_dir)
    
    # Upload to S3
    s3_uri = upload_to_s3(packaged_model, bucket_name, s3_key)
    
    print("\n" + "="*60)
    print("Model packaging and upload complete!")
    print(f"S3 URI: {s3_uri}")
    print("="*60)
    
    # Save S3 URI for reference
    with open(os.path.join(output_dir, 'model_s3_uri.txt'), 'w') as f:
        f.write(s3_uri)
    
    print(f"\nS3 URI saved to: {os.path.join(output_dir, 'model_s3_uri.txt')}")


if __name__ == "__main__":
    main()
