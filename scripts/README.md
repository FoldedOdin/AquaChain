# AquaChain Scripts Directory

Centralized collection of automation scripts for development, deployment, testing, and maintenance of the AquaChain IoT water quality monitoring system.

## 📁 Directory Structure

```
scripts/
├── core/                    # Core build and deployment utilities
├── deployment/              # Deployment automation
├── setup/                   # Environment setup and configuration
├── testing/                 # Testing and validation
├── security/                # Security scanning and auditing
├── maintenance/             # System maintenance utilities
├── monitoring/              # Monitoring and cost tracking
├── performance/             # Performance testing
├── demo/                    # Demo and presentation scripts
└── README.md               # This file
```

## 🚀 Quick Start

### First-Time Setup
```bash
# Windows
scripts\setup\quick-start.bat

# Linux/Mac
./scripts/setup/quick-start.sh
```

### Local Development
```bash
# Start local development environment
scripts\setup\start-local.bat    # Windows
./scripts/setup/start-local.sh   # Linux/Mac
```

### Deploy to AWS
```bash
# Deploy all stacks
scripts\deployment\deploy-all.bat    # Windows
./scripts/deployment/deploy-all.sh   # Linux/Mac
```

### Run Tests
```bash
# Comprehensive system test
scripts\testing\run-comprehensive-test.bat dev    # Windows
./scripts/testing/run-comprehensive-test.sh dev   # Linux/Mac
```

## 📂 Folder Details

### core/
Core utilities used across multiple workflows.

**Key Scripts:**
- `build-lambda-packages.py` - Package Lambda functions with dependencies

**Usage:**
```bash
python scripts/core/build-lambda-packages.py
```

### deployment/
Deployment automation for AWS infrastructure.

**Key Scripts:**
- `deploy-all.bat/.ps1/.sh` - Deploy all CDK stacks
- `destroy-all-stacks.bat/.sh` - Tear down all infrastructure
- `rollback.py` - Rollback to previous deployment

**Usage:**
```bash
# Deploy everything
scripts\deployment\deploy-all.bat

# Deploy specific environment
scripts\deployment\deploy-all.ps1 -Environment staging

# Rollback
python scripts/deployment/rollback.py --stack AquaChain-Core-dev
```

**See:** [deployment/README.md](deployment/README.md)

### setup/
Environment setup and initial configuration.

**Key Scripts:**
- `quick-start.bat/.sh` - One-command setup for new developers
- `setup-local.bat/.sh` - Configure local development environment
- `start-local.bat/.sh` - Start local dev servers
- `create-admin-user.ps1` - Create admin user in Cognito

**Usage:**
```bash
# First time setup
scripts\setup\quick-start.bat

# Start development
scripts\setup\start-local.bat
```

**See:** [setup/README.md](setup/README.md)

### testing/
Comprehensive testing suite and validation scripts.

**Key Scripts:**
- `comprehensive-system-test.py` - All-in-one test suite with detailed reporting
- `run-comprehensive-test.bat/.ps1` - Test runner with HTML reports
- `production_readiness_validation.py` - Pre-production validation
- `test-everything.bat` - Quick test wrapper

**Usage:**
```bash
# Run comprehensive tests
scripts\testing\run-comprehensive-test.bat dev

# Production readiness check
python scripts/testing/production_readiness_validation.py --environment prod
```

**See:** [testing/COMPREHENSIVE_TEST_README.md](testing/COMPREHENSIVE_TEST_README.md)

### security/
Security scanning, vulnerability detection, and compliance tools.

**Key Scripts:**
- `dependency-security-scan.py` - Scan dependencies for vulnerabilities
- `generate-sbom.py` - Generate Software Bill of Materials
- `compare-sboms.py` - Compare SBOMs for changes
- `vulnerability-report-generator.py` - Generate security reports
- `check-sensitive-data.py` - Scan for hardcoded secrets
- `remove-sensitive-data.ps1` - Remove sensitive data from codebase

**Usage:**
```bash
# Security scan
python scripts/security/dependency-security-scan.py

# Generate SBOM
python scripts/security/generate-sbom.py

# Check for secrets
python scripts/security/check-sensitive-data.py
```

### maintenance/
System maintenance and optimization utilities.

**Key Scripts:**
- `disaster_recovery.py` - Disaster recovery procedures
- `optimize-lambda-memory.py` - Optimize Lambda memory allocation
- `reduce-log-retention.ps1` - Reduce CloudWatch log retention
- `check_codebase.py` - Codebase health check

**Usage:**
```bash
# Disaster recovery
python scripts/maintenance/disaster_recovery.py --action backup

# Optimize Lambda
python scripts/maintenance/optimize-lambda-memory.py
```

### monitoring/
Monitoring, alerting, and cost tracking.

**Key Scripts:**
- `check-aws-costs.ps1` - Check current AWS costs
- `create-payment-alarms.ps1` - Create CloudWatch alarms

**Usage:**
```bash
# Check costs
.\scripts\monitoring\check-aws-costs.ps1

# Create alarms
.\scripts\monitoring\create-payment-alarms.ps1
```

### performance/
Performance testing and load testing.

**Key Scripts:**
- `run_load_tests.py` - Run load tests against API

**Usage:**
```bash
python scripts/performance/run_load_tests.py --users 1000 --duration 300
```

### demo/
Demo scripts for presentations and showcases.

**Key Scripts:**
- `ml_model_demo.py` - Interactive ML model demo
- `ml_model_demo_auto.py` - Automated ML demo
- `run-ml-demo.bat` - Demo runner

**Usage:**
```bash
scripts\demo\run-ml-demo.bat
```

**See:** [demo/README.md](demo/README.md)

## 🔧 Common Tasks

### Deploy New Feature
```bash
# 1. Build Lambda packages
python scripts/core/build-lambda-packages.py

# 2. Deploy to dev
scripts\deployment\deploy-all.bat

# 3. Run tests
scripts\testing\run-comprehensive-test.bat dev

# 4. Deploy to staging
scripts\deployment\deploy-all.ps1 -Environment staging
```

### Troubleshoot Production Issue
```bash
# 1. Check system health
python scripts/testing/production_readiness_validation.py --environment prod

# 2. Check costs
.\scripts\monitoring\check-aws-costs.ps1

# 3. Review logs (use AWS Console or CloudWatch Insights)

# 4. Rollback if needed
python scripts/deployment/rollback.py --stack AquaChain-API-prod
```

### Security Audit
```bash
# 1. Scan dependencies
python scripts/security/dependency-security-scan.py

# 2. Check for secrets
python scripts/security/check-sensitive-data.py

# 3. Generate SBOM
python scripts/security/generate-sbom.py

# 4. Generate report
python scripts/security/vulnerability-report-generator.py
```

### Performance Optimization
```bash
# 1. Run load tests
python scripts/performance/run_load_tests.py --users 1000

# 2. Optimize Lambda memory
python scripts/maintenance/optimize-lambda-memory.py

# 3. Reduce log retention
.\scripts\maintenance\reduce-log-retention.ps1
```

## 🛠️ Prerequisites

### Required Tools
- **Python 3.11+** - For Python scripts
- **Node.js 18+** - For frontend development
- **AWS CLI** - Configured with appropriate credentials
- **PowerShell 5.1+** - For Windows scripts
- **Bash** - For Linux/Mac scripts

### Python Dependencies
```bash
pip install boto3 requests pytest
```

### AWS Credentials
Ensure AWS CLI is configured:
```bash
aws configure
```

## 📝 Script Naming Conventions

- **Batch files (`.bat`)**: Windows CMD scripts
- **PowerShell (`.ps1`)**: Windows PowerShell scripts
- **Shell scripts (`.sh`)**: Linux/Mac bash scripts
- **Python (`.py`)**: Cross-platform Python scripts

## 🔒 Security Best Practices

1. **Never commit secrets** - Use AWS Secrets Manager
2. **Review scripts before running** - Especially in production
3. **Use least-privilege IAM** - Scripts should have minimal permissions
4. **Audit script changes** - Review all script modifications
5. **Test in dev first** - Always test scripts in dev environment

## 🐛 Troubleshooting

### Script Won't Run
```bash
# Windows: Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Linux/Mac: Make script executable
chmod +x scripts/setup/quick-start.sh
```

### AWS Credentials Error
```bash
# Check AWS configuration
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### Python Module Not Found
```bash
# Install dependencies
pip install -r requirements.txt
```

### Permission Denied
```bash
# Windows: Run as Administrator
# Linux/Mac: Use sudo or check file permissions
```

## 📚 Additional Resources

- [AquaChain Documentation](../DOCS/)
- [Deployment Guide](../DOCS/deployment/)
- [Testing Guide](testing/COMPREHENSIVE_TEST_README.md)
- [Security Guide](../SECURITY_REMEDIATION_GUIDE.md)

## 🤝 Contributing

When adding new scripts:

1. **Place in appropriate folder** - Follow the directory structure
2. **Add documentation** - Include usage examples
3. **Follow naming conventions** - Use descriptive names
4. **Test thoroughly** - Test in dev before committing
5. **Update README** - Document new scripts here

## 📞 Support

For issues or questions:
- Check troubleshooting section above
- Review script-specific README files
- Consult main AquaChain documentation
- Contact engineering team

## 🗑️ Cleanup

To remove old/redundant scripts:
```bash
# Run cleanup script (creates backup first)
.\scripts\cleanup-scripts.ps1
```

---

**Last Updated:** March 2026  
**Maintained By:** AquaChain Engineering Team
