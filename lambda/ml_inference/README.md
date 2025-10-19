# AquaChain ML Model Training and Deployment Pipeline

## Overview

This directory contains the complete ML pipeline for the AquaChain water quality monitoring system, including:

- **Synthetic Data Generation**: Realistic water quality data with seasonal patterns and anomaly injection
- **SageMaker Training Pipeline**: Automated model training with hyperparameter tuning
- **Model Evaluation**: Comprehensive model validation and metrics
- **Blue-Green Deployment**: Safe model deployment with gradual traffic shifting
- **Model Monitoring**: Performance tracking and data drift detection

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML Training Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Synthetic Data Generation                                    │
│     └─> Generate 50K samples with seasonal patterns              │
│         └─> Inject contamination (5%) and sensor faults (3%)     │
│                                                                   │
│  2. Data Preprocessing                                           │
│     └─> Train/Val/Test split (70/15/15)                         │
│         └─> Feature scaling with StandardScaler                  │
│                                                                   │
│  3. Model Training (SageMaker Pipeline)                          │
│     └─> Random Forest Regressor (WQI prediction)                │
│     └─> Random Forest Classifier (Anomaly detection)            │
│     └─> Hyperparameter tuning with Bayesian optimization        │
│                                                                   │
│  4. Model Evaluation                                             │
│     └─> Test set evaluation                                      │
│     └─> Quality gates: RMSE < 8.0, F1 > 0.85                   │
│                                                                   │
│  5. Model Registry                                               │
│     └─> Version management                                       │
│     └─> Approval workflow                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  Model Deployment Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Staging Deployment                                           │
│     └─> Deploy to Lambda staging alias                          │
│         └─> Run validation tests                                 │
│                                                                   │
│  2. Blue-Green Deployment                                        │
│     └─> Gradual traffic shift: 10% → 25% → 50% → 75% → 100%    │
│         └─> Monitor metrics at each step                         │
│         └─> Automatic rollback on degradation                    │
│                                                                   │
│  3. Production Monitoring                                        │
│     └─> Track prediction accuracy                               │
│     └─> Detect data drift                                        │
│     └─> Trigger retraining on significant drift                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Synthetic Data Generator (`synthetic_data_generator.py`)

Generates realistic water quality data for model training with:

- **Geographic Variation**: 4 regions (coastal, inland, mountain, urban) with different water quality characteristics
- **Seasonal Patterns**: Monsoon, summer, winter, and post-monsoon variations
- **Temporal Features**: Hour of day, day of week, month
- **Anomaly Injection**:
  - Contamination events (5%): Chemical, biological, and industrial contamination
  - Sensor faults (3%): Stuck sensors, drift, noise, out-of-range values

**Usage:**
```python
from synthetic_data_generator import SyntheticDataGenerator

generator = SyntheticDataGenerator(seed=42)
features_df, wqi_targets, anomaly_labels = generator.generate_dataset(
    n_samples=50000,
    contamination_rate=0.05,
    sensor_fault_rate=0.03
)
generator.save_dataset(features_df, wqi_targets, anomaly_labels, 'training_data.csv')
```

### 2. SageMaker Pipeline (`sagemaker_pipeline.py`)

Automated ML training pipeline with:

- **Preprocessing Step**: Data splitting and feature scaling
- **Training Step**: Random Forest model training with configurable hyperparameters
- **Evaluation Step**: Comprehensive model evaluation on test set
- **Conditional Registration**: Automatic model registration if quality gates pass
- **Hyperparameter Tuning**: Bayesian optimization for optimal hyperparameters

**Usage:**
```python
from sagemaker_pipeline import AquaChainMLPipeline

pipeline = AquaChainMLPipeline(
    role_arn="arn:aws:iam::ACCOUNT_ID:role/SageMakerExecutionRole",
    bucket_name="aquachain-data-lake",
    region="us-east-1"
)

# Deploy pipeline
pipeline.deploy_pipeline()

# Start execution
pipeline.start_pipeline_execution()
```

### 3. Model Deployment (`model_deployment.py`)

Blue-green deployment with Lambda aliases:

- **Staging Validation**: Automated testing on staging alias
- **Gradual Traffic Shift**: 10% → 25% → 50% → 75% → 100%
- **Metric Monitoring**: Error rate and latency tracking
- **Automatic Rollback**: Revert on performance degradation

**Usage:**
```python
from model_deployment import ModelDeploymentManager

deployer = ModelDeploymentManager(
    lambda_function_name="aquachain-ml-inference",
    s3_bucket="aquachain-data-lake"
)

# Deploy new model version
result = deployer.deploy_new_model(
    model_version="2.0",
    model_artifacts_s3_uri="s3://aquachain-data-lake/ml-models/v2.0/",
    auto_promote=True
)

# Manual promotion (if auto_promote=False)
deployer.promote_staging_to_production()
```

### 4. Model Monitoring (`model_monitoring.py`)

Production model monitoring with:

- **Performance Tracking**: MAE, RMSE, accuracy, F1 score
- **Data Drift Detection**: Kolmogorov-Smirnov test and PSI calculation
- **Automatic Retraining**: Trigger pipeline on significant drift
- **CloudWatch Integration**: Publish metrics for alerting

**Usage:**
```python
from model_monitoring import ModelMonitor

monitor = ModelMonitor(
    model_name='aquachain-wqi-model',
    s3_bucket='aquachain-data-lake'
)

# Calculate performance
performance = monitor.calculate_model_performance(hours=24)

# Detect drift
drift_report = monitor.detect_data_drift(baseline_features, current_features)
```

## Model Architecture

### WQI Prediction Model
- **Algorithm**: Random Forest Regressor
- **Features**: 14 features (5 sensor readings + 2 location + 3 temporal + 4 derived)
- **Target**: Water Quality Index (0-100)
- **Performance Target**: RMSE < 8.0

### Anomaly Detection Model
- **Algorithm**: Random Forest Classifier
- **Classes**: Normal, Sensor Fault, Contamination
- **Performance Target**: F1 Score > 0.85

## Feature Engineering

### Base Features (5)
- pH (0-14)
- Turbidity (NTU)
- TDS (ppm)
- Temperature (°C)
- Humidity (%)

### Location Features (2)
- Latitude
- Longitude

### Temporal Features (3)
- Hour of day (0-23)
- Month (1-12)
- Day of week (0-6)

### Derived Features (4)
- pH × Temperature interaction
- Turbidity / TDS ratio
- |pH - 7.0| deviation
- Temperature - 25°C deviation

## Deployment Process

### 1. Generate Training Data
```bash
python synthetic_data_generator.py
```

### 2. Upload to S3
```bash
aws s3 cp training_data.csv s3://aquachain-data-lake/training-data/raw/
```

### 3. Deploy SageMaker Pipeline
```bash
python sagemaker_pipeline.py
```

### 4. Monitor Pipeline Execution
```bash
aws sagemaker list-pipeline-executions --pipeline-name aquachain-ml-training-pipeline
```

### 5. Approve Model
```bash
aws sagemaker update-model-package \
  --model-package-arn <MODEL_PACKAGE_ARN> \
  --model-approval-status Approved
```

### 6. Deploy to Production
```bash
python model_deployment.py
```

## Monitoring and Alerting

### CloudWatch Metrics
- `AquaChain/MLModel/WQI_MAE`: Mean Absolute Error for WQI predictions
- `AquaChain/MLModel/WQI_RMSE`: Root Mean Squared Error
- `AquaChain/MLModel/Anomaly_Accuracy`: Anomaly detection accuracy

### Drift Detection
- **Scheduled**: Daily drift detection via EventBridge
- **Threshold**: PSI > 0.1 or KS test p-value < 0.05
- **Action**: Automatic retraining pipeline trigger

### Performance Degradation
- **Threshold**: 15% degradation in RMSE or accuracy
- **Action**: Alert to ML team, manual investigation

## Quality Gates

### Training Pipeline
- WQI RMSE < 8.0
- Anomaly F1 Score > 0.85
- No missing feature importance values

### Deployment
- Staging validation: 80% test pass rate
- Error rate < 5% during traffic shift
- P99 latency < 15 seconds

## Rollback Procedures

### Automatic Rollback
Triggered when:
- Error rate > 5% during traffic shift
- P99 latency > 15 seconds
- Staging validation fails

### Manual Rollback
```python
deployer = ModelDeploymentManager(...)
deployer._rollback_deployment()
```

## Model Versioning

Models are versioned using semantic versioning:
- **Major**: Breaking changes to input/output schema
- **Minor**: New features or significant improvements
- **Patch**: Bug fixes or minor improvements

Example: `v2.1.3`

## Cost Optimization

### Training
- Use Spot instances for training jobs (70% cost savings)
- Automatic model compression for deployment
- Scheduled training (off-peak hours)

### Inference
- Lambda reserved concurrency for cost predictability
- Model caching to reduce S3 GET requests
- Batch inference for historical analysis

## Troubleshooting

### Training Pipeline Fails
1. Check CloudWatch logs for SageMaker jobs
2. Verify S3 data paths and permissions
3. Review hyperparameter ranges

### Deployment Fails
1. Check Lambda function logs
2. Verify IAM permissions for S3 and Lambda
3. Test staging alias manually

### Drift Detection False Positives
1. Review baseline data quality
2. Adjust drift thresholds
3. Increase monitoring window

## References

- [SageMaker Pipelines Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html)
- [Lambda Aliases and Versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html)
- [Model Monitoring Best Practices](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html)
