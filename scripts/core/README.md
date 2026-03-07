# Core Utilities

Essential build and deployment utilities used across multiple workflows.

## Scripts

### build-lambda-packages.py

Packages Lambda functions with their dependencies for deployment.

**Purpose:**
- Bundles Lambda function code with requirements
- Creates deployment packages for AWS Lambda
- Handles dependency resolution

**Usage:**
```bash
python scripts/core/build-lambda-packages.py
```

**Options:**
```bash
python scripts/core/build-lambda-packages.py --function data_processing
python scripts/core/build-lambda-packages.py --all
```

**Output:**
- Creates `.zip` files in `lambda/dist/` directory
- Includes all dependencies from `requirements.txt`
- Ready for Lambda deployment

**When to Use:**
- Before deploying Lambda functions
- After updating Lambda dependencies
- When creating new Lambda functions

**Requirements:**
- Python 3.11+
- pip installed
- Lambda function directories in `lambda/`

## Best Practices

1. **Run before deployment** - Always build packages before deploying
2. **Check package size** - Lambda has 50MB (zipped) / 250MB (unzipped) limits
3. **Use Lambda layers** - For large dependencies (boto3, pandas)
4. **Test locally** - Verify packages work before deploying

## Troubleshooting

**Issue: Package too large**
```bash
# Solution: Use Lambda layers for large dependencies
# Move boto3, pandas, etc. to layers
```

**Issue: Missing dependencies**
```bash
# Solution: Check requirements.txt is complete
pip freeze > requirements.txt
```

**Issue: Import errors after deployment**
```bash
# Solution: Verify all dependencies are included
# Check Lambda handler path is correct
```
