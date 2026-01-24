# Lambda Layers

This directory contains Lambda layers for shared dependencies across AquaChain Lambda functions.

## Layers

### Common Layer (`common/`)
Contains frequently used dependencies across multiple Lambda functions:
- boto3, botocore - AWS SDK
- requests - HTTP client
- pydantic - Data validation
- jsonschema - JSON schema validation
- aws-xray-sdk - Distributed tracing
- PyJWT - JWT token handling
- python-dateutil - Date/time utilities

**Used by**: data_processing, auth_service, user_management, device_management, notification_service, readings_query, websocket_api, and others

### ML Layer (`ml/`)
Contains machine learning and data science libraries:
- scikit-learn - Machine learning algorithms
- numpy - Numerical computing
- pandas - Data manipulation
- scipy - Scientific computing
- sagemaker - AWS SageMaker SDK

**Used by**: ml_inference, ml_training

## Building Layers

Lambda layers must be packaged with dependencies in the `python/` subdirectory:

```bash
# Build common layer
cd lambda/layers/common
pip install -r requirements.txt -t python/
zip -r common-layer.zip python/

# Build ML layer
cd lambda/layers/ml
pip install -r requirements.txt -t python/
zip -r ml-layer.zip python/
```

## CDK Deployment

Layers are automatically deployed via CDK using the `LambdaLayersStack`:

```python
from aws_cdk import aws_lambda as lambda_

common_layer = lambda_.LayerVersion(
    self, 'CommonLayer',
    code=lambda_.Code.from_asset('lambda/layers/common'),
    compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
    description='Common dependencies: boto3, requests, pydantic, etc.'
)
```

## Usage in Lambda Functions

Attach layers to Lambda functions in CDK:

```python
data_processing_fn = lambda_.Function(
    self, 'DataProcessing',
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler='handler.lambda_handler',
    code=lambda_.Code.from_asset('lambda/data_processing'),
    layers=[common_layer]
)
```

## Benefits

1. **Reduced Package Size**: Individual Lambda functions don't need to include common dependencies
2. **Faster Deployments**: Only function code needs to be updated, not dependencies
3. **Consistent Versions**: All functions use the same dependency versions
4. **Reduced Cold Starts**: Smaller deployment packages load faster
5. **Better Caching**: AWS caches layers separately from function code

## Layer Size Limits

- Maximum unzipped size: 250 MB
- Maximum zipped size: 50 MB per layer
- Maximum layers per function: 5

Current layer sizes:
- Common layer: ~30 MB (unzipped)
- ML layer: ~180 MB (unzipped)
