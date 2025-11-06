# AquaChain ML Models Directory

## Overview

This directory contains the trained ML models for the AquaChain water quality monitoring system. The models are used for:

1. **WQI Prediction**: Random Forest Regressor for Water Quality Index calculation (0-100)
2. **Anomaly Detection**: Random Forest Classifier for detecting normal/sensor_fault/contamination

## Model Files

### Current Model Files (v1.0)

- `wqi-model-v1.0.pkl` - Trained Random Forest Regressor for WQI prediction
- `anomaly-model-v1.0.pkl` - Trained Random Forest Classifier for anomaly detection  
- `feature-scaler-v1.0.pkl` - StandardScaler for feature normalization
- `model-metadata-v1.0.json` - Model metadata and training information
- `wqi-model-version.json` - Version information for compatibility with existing handler

### Model Performance (v1.0)

- **WQI Model**: R² Score = 0.944 (94.4% variance explained)
- **Anomaly Model**: Accuracy = 98.6%
- **Training Data**: 5,000 synthetic samples
- **Features**: 14 engineered features

## Usage

### Development/Testing (Local Models)

```python
from local_model_loader import LocalModelLoader
from dev_handler import lambda_handler

# Load models locally
loader = LocalModelLoader("models")
models = loader.load_models("1.0")

# Test inference
event = {
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

result = lambda_handler(event)
```

### Production (S3 Models)

```bash
# Upload models to S3
aws s3 sync models/ s3://aquachain-data-lake/ml-models/current/

# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name aquachain-ml-inference \
  --environment Variables='{
    "MODEL_BUCKET":"aquachain-data-lake",
    "MODEL_VERSION":"1.0"
  }'
```

## Model Creation

### Generate New Models

```bash
# Create initial models for development
python create_initial_models.py

# This will generate:
# - 5,000 synthetic training samples
# - Trained WQI and anomaly detection models
# - Feature scaler and metadata
```

### Model Training Pipeline

For production model training, use the SageMaker pipeline:

```python
from sagemaker_pipeline import AquaChainMLPipeline

pipeline = AquaChainMLPipeline(role_arn, bucket_name, region)
pipeline.deploy_pipeline()
pipeline.start_pipeline_execution()
```

## Model Architecture

### Input Features (14)

1. **Sensor Readings (5)**:
   - pH (0-14)
   - Turbidity (NTU)
   - TDS (ppm)
   - Temperature (°C)
   - Humidity (%)

2. **Location Features (2)**:
   - Latitude
   - Longitude

3. **Temporal Features (3)**:
   - Hour of day (0-23)
   - Month (1-12)
   - Day of week (0-6)

4. **Derived Features (4)**:
   - pH × Temperature interaction
   - Turbidity / TDS ratio
   - |pH - 7.0| deviation
   - Temperature - 25°C deviation

### Model Outputs

1. **WQI Prediction**: Float value 0-100
2. **Anomaly Detection**: 
   - Class: 'normal', 'sensor_fault', 'contamination'
   - Confidence: Float 0-1

## Model Versioning

Models follow semantic versioning:
- **Major.Minor.Patch** (e.g., 1.0.0)
- **Major**: Breaking changes to input/output schema
- **Minor**: New features or significant improvements  
- **Patch**: Bug fixes or minor improvements

## Quality Metrics

### WQI Model Thresholds
- **Acceptable**: RMSE < 8.0
- **Good**: RMSE < 5.0
- **Excellent**: RMSE < 3.0

### Anomaly Model Thresholds
- **Acceptable**: F1 Score > 0.85
- **Good**: F1 Score > 0.90
- **Excellent**: F1 Score > 0.95

## Model Monitoring

Production models are continuously monitored for:

1. **Performance Degradation**: RMSE/accuracy drift
2. **Data Drift**: Input feature distribution changes
3. **Prediction Drift**: Output distribution changes

Monitoring triggers automatic retraining when:
- Performance degrades by >15%
- Data drift PSI > 0.1
- Significant distribution changes detected

## Troubleshooting

### Model Loading Issues

```python
# Check available models
from local_model_loader import LocalModelLoader
loader = LocalModelLoader("models")
versions = loader.list_available_versions()
print(f"Available versions: {versions}")

# Test model inference
result = loader.test_model_inference("1.0")
print(f"Test result: {result}")
```

### Performance Issues

1. **High RMSE**: Retrain with more data or tune hyperparameters
2. **Low Confidence**: Check feature scaling and data quality
3. **Slow Inference**: Optimize model size or use model compression

### Common Errors

- **FileNotFoundError**: Models not found - run `create_initial_models.py`
- **PickleError**: Corrupted model files - regenerate models
- **ShapeError**: Feature mismatch - check input feature count (should be 14)

## Development Workflow

1. **Generate Models**: `python create_initial_models.py`
2. **Test Locally**: `python dev_handler.py`
3. **Upload to S3**: `aws s3 sync models/ s3://bucket/ml-models/current/`
4. **Deploy to Lambda**: Update environment variables
5. **Monitor Performance**: Use CloudWatch metrics

## Files in This Directory

After running `create_initial_models.py`:

```
models/
├── README.md                    # This file
├── wqi-model-v1.0.pkl          # WQI prediction model (1.9MB)
├── anomaly-model-v1.0.pkl      # Anomaly detection model (659KB)
├── feature-scaler-v1.0.pkl     # Feature scaler (786B)
├── model-metadata-v1.0.json    # Training metadata (690B)
└── wqi-model-version.json       # Version info (169B)
```

Total size: ~2.6MB

## Next Steps

1. **Production Training**: Use SageMaker pipeline with larger datasets
2. **Real Data**: Replace synthetic data with actual sensor readings
3. **Model Optimization**: Experiment with different algorithms (XGBoost, Neural Networks)
4. **Feature Engineering**: Add more domain-specific features
5. **Ensemble Methods**: Combine multiple models for better performance

## Support

For issues with models:
1. Check logs in CloudWatch
2. Verify model file integrity
3. Test with known good data
4. Contact ML team for model retraining