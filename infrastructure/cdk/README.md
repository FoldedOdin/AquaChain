# AquaChain CDK Infrastructure

This directory contains the AWS CDK (Cloud Development Kit) infrastructure code for the AquaChain water quality monitoring system. The infrastructure is designed using Infrastructure as Code (IaC) principles with environment-specific configurations, automated testing, and deployment pipelines.

## Architecture Overview

The AquaChain system is built using a serverless-first architecture on AWS with the following stack layers:

1. **Security Stack**: KMS encryption keys, IAM roles, and security policies
2. **Core Stack**: VPC, networking, and shared resources (for production)
3. **Data Stack**: DynamoDB tables, S3 buckets, and IoT Core configuration
4. **Compute Stack**: Lambda functions, SageMaker ML resources, and SNS topics
5. **API Stack**: API Gateway, Cognito authentication, and WAF protection
6. **Monitoring Stack**: CloudWatch dashboards, alarms, and X-Ray tracing

## Prerequisites

- **Python 3.11+**: Required for CDK Python constructs
- **Node.js 18+**: Required for AWS CDK CLI
- **AWS CLI**: Configured with appropriate credentials
- **AWS CDK CLI**: For infrastructure deployment

## Quick Start

### 1. Environment Setup

Run the setup script to configure your development environment:

```bash
cd infrastructure/cdk
./scripts/setup_cdk_environment.sh
```

This script will:
- Verify prerequisites
- Create Python virtual environment
- Install dependencies
- Create deployment scripts
- Generate environment configurations

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Bootstrap CDK (First Time Only)

```bash
python deployment/deploy.py --environment dev --action bootstrap
```

### 4. Deploy Infrastructure

For development:
```bash
./scripts/quick-deploy.sh dev
```

For production (with full validation):
```bash
./scripts/full-deploy.sh prod
```

## Environment Configurations

### Development (dev)
- Minimal resources for cost optimization
- No deletion protection
- Basic monitoring
- Single AZ deployment
- Pay-per-request DynamoDB billing

### Staging (staging)
- Production-like configuration
- Deletion protection enabled
- Detailed monitoring
- Multi-AZ deployment
- Cross-account audit replication

### Production (prod)
- Full security hardening
- Comprehensive monitoring and alerting
- Automated backups
- Cross-region replication
- Provisioned DynamoDB capacity
- 7-year audit retention

## Manual Deployment Commands

### Deploy All Stacks
```bash
python deployment/deploy.py --environment <env> --action deploy
```

### Deploy Specific Stack
```bash
python deployment/deploy.py --environment <env> --action deploy --stack Security
```

### Show Stack Differences
```bash
python deployment/deploy.py --environment <env> --action diff
```

### Destroy Infrastructure
```bash
python deployment/deploy.py --environment <env> --action destroy
```

### List Stacks
```bash
python deployment/deploy.py --environment <env> --action list
```

## Stack Dependencies

The stacks must be deployed in the following order due to dependencies:

```
Security Stack
    ↓
Core Stack
    ↓
Data Stack (depends on Security)
    ↓
Compute Stack (depends on Data, Security)
    ↓
API Stack (depends on Compute, Security)
    ↓
Monitoring Stack (depends on all above)
```

The deployment script handles these dependencies automatically.

## Testing

### Unit Tests
```bash
python -m pytest tests/ -v
```

### Infrastructure Validation
```bash
python validation/validate_infrastructure.py --environment dev
```

### Security Scanning
```bash
# Install security tools
pip install checkov bandit

# Run Checkov for CloudFormation security
checkov -d . --framework cloudformation

# Run Bandit for Python security
bandit -r . -f json
```

## CI/CD Pipeline

The infrastructure includes a GitHub Actions workflow (`.github/workflows/cdk-deploy.yml`) that:

1. **Tests**: Runs unit tests and linting on every PR
2. **Security Scanning**: Performs security analysis with Checkov and Bandit
3. **Auto-Deploy Dev**: Deploys to dev environment on develop branch pushes
4. **Auto-Deploy Staging**: Deploys to staging on main branch pushes
5. **Manual Prod Deploy**: Requires manual approval for production deployments

### Required GitHub Secrets

Set up the following secrets in your GitHub repository:

```
AWS_ACCESS_KEY_ID_DEV
AWS_SECRET_ACCESS_KEY_DEV
AWS_ACCESS_KEY_ID_STAGING
AWS_SECRET_ACCESS_KEY_STAGING
AWS_ACCESS_KEY_ID_PROD
AWS_SECRET_ACCESS_KEY_PROD
```

## Resource Naming Convention

All resources follow a consistent naming pattern:
```
{project}-{resource_type}-{resource_name}-{environment}
```

Examples:
- `aquachain-table-readings-dev`
- `aquachain-bucket-data-lake-prod`
- `aquachain-function-data-processing-staging`

## Key Features

### Security
- **Encryption at Rest**: All data encrypted with customer-managed KMS keys
- **Encryption in Transit**: TLS/SSL for all communications
- **IAM Least Privilege**: Minimal permissions for all roles
- **WAF Protection**: API Gateway protected with AWS WAF
- **Audit Trail**: Immutable audit logs with S3 Object Lock

### Scalability
- **Serverless Architecture**: Auto-scaling Lambda functions
- **DynamoDB Auto-scaling**: Automatic capacity adjustment
- **API Gateway Throttling**: Rate limiting and burst protection
- **Multi-AZ Deployment**: High availability across zones

### Monitoring
- **CloudWatch Dashboards**: Real-time system metrics
- **Custom Alarms**: Business KPI monitoring
- **X-Ray Tracing**: Distributed request tracing
- **SNS Notifications**: Multi-channel alerting

### Compliance
- **7-Year Retention**: Audit logs retained for compliance
- **Cross-Account Replication**: Tamper-evident storage
- **Hash Chain Verification**: Cryptographic integrity checks
- **Immutable Ledger**: Blockchain-inspired data integrity

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Failed**
   ```bash
   # Ensure AWS credentials are configured
   aws sts get-caller-identity
   
   # Bootstrap with explicit account/region
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

2. **Stack Deployment Failed**
   ```bash
   # Check CloudFormation events
   aws cloudformation describe-stack-events --stack-name STACK-NAME
   
   # View detailed error logs
   cdk deploy --verbose
   ```

3. **Resource Already Exists**
   ```bash
   # Import existing resources
   cdk import STACK-NAME
   
   # Or destroy and recreate
   cdk destroy STACK-NAME
   cdk deploy STACK-NAME
   ```

4. **Permission Denied**
   ```bash
   # Verify IAM permissions
   aws iam get-user
   aws iam list-attached-user-policies --user-name USERNAME
   ```

### Validation Failures

If infrastructure validation fails:

1. Check AWS service limits
2. Verify IAM permissions
3. Ensure all dependencies are deployed
4. Check CloudWatch logs for errors

### Rollback Procedures

For production rollbacks:

```bash
# List stack versions
aws cloudformation list-stack-resources --stack-name STACK-NAME

# Rollback to previous version
aws cloudformation cancel-update-stack --stack-name STACK-NAME

# Or deploy previous CDK version
git checkout PREVIOUS-COMMIT
cdk deploy --context environment=prod
```

## Cost Optimization

### Development Environment
- Use pay-per-request DynamoDB billing
- Minimal Lambda reserved concurrency
- Basic CloudWatch monitoring
- Single AZ deployment

### Production Environment
- Monitor AWS Cost Explorer regularly
- Set up billing alerts
- Use S3 lifecycle policies for data archival
- Optimize Lambda memory allocation

## Security Best Practices

1. **Secrets Management**: Use AWS Secrets Manager for sensitive data
2. **Network Security**: VPC endpoints for private communication
3. **Access Control**: Regular IAM access reviews
4. **Monitoring**: Enable CloudTrail for API auditing
5. **Encryption**: Customer-managed KMS keys with rotation

## Support and Maintenance

### Regular Tasks
- Review CloudWatch alarms monthly
- Update CDK dependencies quarterly
- Rotate KMS keys annually
- Review IAM permissions quarterly

### Monitoring
- Check system dashboards daily
- Review security scan results weekly
- Validate backup procedures monthly
- Test disaster recovery quarterly

## Contributing

1. Create feature branch from `develop`
2. Make infrastructure changes
3. Add/update tests
4. Run validation locally
5. Submit pull request
6. Automated tests will run
7. Deploy to dev environment automatically
8. Manual approval required for production

## License

This infrastructure code is part of the AquaChain project and follows the same licensing terms.