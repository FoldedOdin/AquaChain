# 🛠️ AquaChain Scripts

All automation scripts for deployment, testing, security, maintenance, and setup - now organized into logical categories.

---

## 📁 Directory Structure

```
scripts/
├── deployment/          # Deployment and infrastructure management
│   ├── deploy-all.bat/sh/ps1
│   ├── deploy-minimal.bat
│   ├── deploy.py
│   ├── deploy-phase4-infrastructure.py
│   ├── destroy-all-stacks.bat/sh
│   ├── rollback.py
│   └── upload-sagemaker-model.py
│
├── testing/            # Testing and validation
│   ├── test-everything.bat
│   ├── test_dr_integration.py
│   ├── test_email_verification.py
│   ├── test_enhanced_dr_features.py
│   ├── validate_dr_implementation.py
│   ├── validate-phase3-deployment.py
│   ├── validate-phase4-deployment.py
│   └── validate-phase4-implementation.py
│
├── security/           # Security scanning and compliance
│   ├── check-sensitive-data.py
│   ├── dependency-check.py
│   ├── dependency-security-scan.py
│   ├── generate-sbom.py
│   ├── compare-sboms.py
│   ├── vulnerability-report-generator.py
│   └── manage-api-keys.py
│
├── maintenance/        # System maintenance and optimization
│   ├── check_codebase.py
│   ├── disaster_recovery.py
│   ├── fix-data-stack.py
│   ├── fix-data-stack-v2.py
│   ├── optimize-lambda-memory.py
│   ├── remove_humidity_sensor.py
│   ├── switch-dynamodb-to-provisioned.py
│   ├── ultra-cost-optimize.bat
│   ├── delete-everything.bat
│   ├── lint-all.sh
│   └── lint-python.sh
│
├── setup/              # Initial setup and local development
│   ├── quick-start.bat/sh
│   ├── setup-local.bat/sh
│   ├── start-local.bat/sh
│   ├── check-aws.bat
│   ├── check-free-tier-usage.bat
│   └── verify-region.bat
│
└── README.md           # This file
```

---

## 🚀 Quick Reference

### 🎯 Most Common Tasks

| Task | Script | Location |
|------|--------|----------|
| **Deploy everything** | `deploy-all.bat` | `deployment/` |
| **Start local dev** | `setup-local.bat` then `start-local.bat` | `setup/` |
| **Test infrastructure** | `test-everything.bat` | `testing/` |
| **Optimize costs** | `ultra-cost-optimize.bat` | `maintenance/` |
| **Security scan** | `dependency-security-scan.py` | `security/` |
| **Check AWS setup** | `check-aws.bat` | `setup/` |

---

## 📂 Category Details

### 🚀 Deployment Scripts (`deployment/`)

Deploy and manage infrastructure stacks.

| Script | Purpose | Time |
|--------|---------|------|
| **deploy-all.bat/sh/ps1** | Deploy all infrastructure stacks | 30 min |
| **deploy-minimal.bat** | Deploy minimal infrastructure | 15 min |
| **deploy.py** | General deployment script | 15 min |
| **deploy-phase4-infrastructure.py** | Deploy Phase 4 infrastructure | 20 min |
| **destroy-all-stacks.bat/sh** | Delete all AWS stacks | 10 min |
| **rollback.py** | Rollback to previous deployment | 10 min |
| **upload-sagemaker-model.py** | Upload ML models to SageMaker | 10 min |

**Usage:**
```bash
# Windows
cd scripts/deployment
deploy-all.bat

# Linux/Mac
cd scripts/deployment
./deploy-all.sh
```

---

### 🧪 Testing Scripts (`testing/`)

Validate deployments and test functionality.

| Script | Purpose | Time |
|--------|---------|------|
| **test-everything.bat** | Run all infrastructure tests | 5 min |
| **test_dr_integration.py** | Test disaster recovery integration | 5 min |
| **test_email_verification.py** | Test email verification flow | 2 min |
| **test_enhanced_dr_features.py** | Test enhanced DR features | 5 min |
| **validate_dr_implementation.py** | Validate DR implementation | 3 min |
| **validate-phase3-deployment.py** | Validate Phase 3 deployment | 3 min |
| **validate-phase4-deployment.py** | Validate Phase 4 deployment | 3 min |
| **validate-phase4-implementation.py** | Validate Phase 4 implementation | 3 min |

**Usage:**
```bash
cd scripts/testing
test-everything.bat

# Or run specific tests
python test_email_verification.py
```

---

### 🔒 Security Scripts (`security/`)

Security scanning, vulnerability checks, and compliance.

| Script | Purpose | Time |
|--------|---------|------|
| **check-sensitive-data.py** | Scan for sensitive data in code | 3 min |
| **dependency-check.py** | Check dependency versions | 3 min |
| **dependency-security-scan.py** | Scan dependencies for vulnerabilities | 5 min |
| **generate-sbom.py** | Generate Software Bill of Materials | 5 min |
| **compare-sboms.py** | Compare SBOM versions | 2 min |
| **vulnerability-report-generator.py** | Generate vulnerability reports | 5 min |
| **manage-api-keys.py** | Manage API keys securely | 2 min |

**Usage:**
```bash
cd scripts/security

# Run security scan
python dependency-security-scan.py

# Generate SBOM
python generate-sbom.py

# Check for sensitive data
python check-sensitive-data.py
```

---

### 🔧 Maintenance Scripts (`maintenance/`)

System maintenance, optimization, and fixes.

| Script | Purpose | Time |
|--------|---------|------|
| **check_codebase.py** | Check codebase for errors | 5 min |
| **disaster_recovery.py** | Disaster recovery operations | 15 min |
| **fix-data-stack.py** | Fix DynamoDB configuration | 1 min |
| **fix-data-stack-v2.py** | Fix DynamoDB (v2) | 1 min |
| **optimize-lambda-memory.py** | Optimize Lambda memory allocation | 5 min |
| **remove_humidity_sensor.py** | Remove humidity sensor | 2 min |
| **switch-dynamodb-to-provisioned.py** | Switch DynamoDB to provisioned | 5 min |
| **ultra-cost-optimize.bat** | Optimize costs (57-68% savings) | 30 min |
| **delete-everything.bat** | Delete all stacks (₹0 cost) | 10 min |
| **lint-all.sh** | Lint all code | 5 min |
| **lint-python.sh** | Lint Python code | 3 min |

**Usage:**
```bash
cd scripts/maintenance

# Optimize costs
ultra-cost-optimize.bat

# Check codebase
python check_codebase.py

# Delete everything
delete-everything.bat
```

---

### ⚙️ Setup Scripts (`setup/`)

Initial setup and local development environment.

| Script | Purpose | Time |
|--------|---------|------|
| **quick-start.bat/sh** | Interactive setup wizard | 5 min |
| **setup-local.bat/sh** | Setup local development environment | 10 min |
| **start-local.bat/sh** | Start local development servers | 2 min |
| **check-aws.bat** | Check AWS connection and credentials | 1 min |
| **check-free-tier-usage.bat** | Check AWS free tier usage | 2 min |
| **verify-region.bat** | Verify AWS region configuration | 1 min |

**Usage:**
```bash
cd scripts/setup

# First time setup
setup-local.bat

# Start development servers
start-local.bat

# Check AWS setup
check-aws.bat
```

---

## 💰 Cost Management

### Current Deployment Status

- **Deployed Stacks**: 9/22
- **Monthly Cost**: ~₹2,500-3,500 (optimized)
- **Savings**: 57-68% from original

### Cost Options

| Option | Monthly Cost | Script | Location |
|--------|--------------|--------|----------|
| **Keep Running** | ₹3,000 | Do nothing | - |
| **Optimize Further** | ₹2,500 | `ultra-cost-optimize.bat` | `maintenance/` |
| **Delete All** | ₹0 | `delete-everything.bat` | `maintenance/` |

---

## 🎯 Common Workflows

### First Time Setup
```bash
# 1. Check AWS credentials
cd scripts/setup
check-aws.bat

# 2. Run quick start
quick-start.bat

# 3. Deploy infrastructure
cd ../deployment
deploy-all.bat
```

### Local Development
```bash
# 1. Setup local environment (first time only)
cd scripts/setup
setup-local.bat

# 2. Start development servers
start-local.bat

# Access at http://localhost:3000
```

### Security Audit
```bash
cd scripts/security

# 1. Scan dependencies
python dependency-security-scan.py

# 2. Check for sensitive data
python check-sensitive-data.py

# 3. Generate SBOM
python generate-sbom.py

# 4. Generate vulnerability report
python vulnerability-report-generator.py
```

### Testing & Validation
```bash
cd scripts/testing

# 1. Run all tests
test-everything.bat

# 2. Validate specific phase
python validate-phase4-deployment.py

# 3. Test disaster recovery
python test_dr_integration.py
```

### Cost Optimization
```bash
cd scripts/maintenance

# 1. Check current usage
cd ../setup
check-free-tier-usage.bat

# 2. Optimize costs
cd ../maintenance
ultra-cost-optimize.bat

# 3. Or delete everything
delete-everything.bat
```

---

## 📖 Documentation

For detailed guides:

- **[../docs/cost-optimization/](../docs/cost-optimization/)** - Cost optimization guides
- **[../docs/SETUP_GUIDE.md](../docs/SETUP_GUIDE.md)** - Setup instructions
- **[../docs/QUICK_FIX_GUIDE.md](../docs/QUICK_FIX_GUIDE.md)** - Troubleshooting
- **[../PROJECT_REPORT.md](../PROJECT_REPORT.md)** - Complete documentation
- **[../ESP32_CONNECTION_CHECKLIST.md](../ESP32_CONNECTION_CHECKLIST.md)** - ESP32 setup

---

## 🔄 Migration Notes

**Scripts have been reorganized from root directory:**

- `setup-local.bat/sh` → `scripts/setup/`
- `start-local.bat/sh` → `scripts/setup/`

**All scripts remain functional in their new locations.**

To use scripts from project root, use relative paths:
```bash
# Windows
scripts\setup\setup-local.bat
scripts\deployment\deploy-all.bat

# Linux/Mac
./scripts/setup/setup-local.sh
./scripts/deployment/deploy-all.sh
```

---

## 🗑️ Removed Scripts

The following duplicate/unnecessary scripts have been removed:

- ~~deploy-simple.bat~~ (use deploy-all.bat instead)
- ~~deploy-core-only.bat~~ (not needed - only 9 stacks deployed)
- ~~deploy-no-bootstrap.bat~~ (use deploy-all.bat)
- ~~fix-and-redeploy.bat~~ (no failed stacks to fix)
- ~~cleanup-failed-stacks.bat~~ (duplicate)
- ~~delete-failed-stacks.bat~~ (duplicate)
- ~~reduce-costs.bat~~ (use ultra-cost-optimize.bat)
- ~~reduce-costs-aggressive.bat~~ (use ultra-cost-optimize.bat)

---

**Last Updated**: November 8, 2025  
**Status**: ✅ Scripts Organized & Categorized
