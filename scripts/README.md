# 🛠️ AquaChain Scripts

All automation scripts for deployment, testing, and cost optimization.

---

## 🚀 Essential Scripts (Windows .bat)

| Script                        | Purpose                          | Time   |
| ----------------------------- | -------------------------------- | ------ |
| **deploy-all.bat**            | Deploy all infrastructure stacks | 30 min |
| **quick-start.bat**           | Interactive setup wizard         | 5 min  |
| **ultra-cost-optimize.bat**   | Optimize costs (57-68% savings)  | 30 min |
| **delete-everything.bat**     | Delete all stacks (₹0 cost)      | 10 min |
| **test-everything.bat**       | Test all infrastructure          | 5 min  |
| **check-aws.bat**             | Check AWS connection             | 1 min  |
| **check-free-tier-usage.bat** | Check free tier usage            | 2 min  |
| **verify-region.bat**         | Verify AWS region                | 1 min  |

---

## 🐧 Linux/Mac Scripts (.sh)

| Script             | Purpose                       | Time   |
| ------------------ | ----------------------------- | ------ |
| **deploy-all.sh**  | Deploy all stacks (Linux/Mac) | 30 min |
| **quick-start.sh** | Quick start (Linux/Mac)       | 15 min |
| **lint-all.sh**    | Lint all code                 | 5 min  |
| **lint-python.sh** | Lint Python code              | 3 min  |

---

## 🐍 Python Utility Scripts

### Testing & Validation

| Script                                | Purpose                    | Time  |
| ------------------------------------- | -------------------------- | ----- |
| **test_email_verification.py**        | Test email verification    | 2 min |
| **check_codebase.py**                 | Check codebase for errors  | 5 min |
| **validate-phase3-deployment.py**     | Validate Phase 3           | 3 min |
| **validate-phase4-deployment.py**     | Validate Phase 4           | 3 min |
| **validate-phase4-implementation.py** | Validate Phase 4 impl      | 3 min |
| **validate_dr_implementation.py**     | Validate disaster recovery | 3 min |
| **test_dr_integration.py**            | Test DR integration        | 5 min |
| **test_enhanced_dr_features.py**      | Test enhanced DR           | 5 min |

### Security & Compliance

| Script                                | Purpose              | Time  |
| ------------------------------------- | -------------------- | ----- |
| **dependency-security-scan.py**       | Scan dependencies    | 5 min |
| **dependency-check.py**               | Check dependencies   | 3 min |
| **generate-sbom.py**                  | Generate SBOM        | 5 min |
| **compare-sboms.py**                  | Compare SBOMs        | 2 min |
| **vulnerability-report-generator.py** | Generate vuln report | 5 min |

### Deployment & Management

| Script                              | Purpose                    | Time   |
| ----------------------------------- | -------------------------- | ------ |
| **upload-sagemaker-model.py**       | Upload ML model            | 10 min |
| **manage-api-keys.py**              | Manage API keys            | 2 min  |
| **rollback.py**                     | Rollback deployment        | 10 min |
| **disaster_recovery.py**            | Disaster recovery          | 15 min |
| **deploy-phase4-infrastructure.py** | Deploy Phase 4             | 20 min |
| **deploy.py**                       | General deployment         | 15 min |
| **optimize-lambda-memory.py**       | Optimize Lambda memory     | 5 min  |
| **fix-data-stack.py**               | Fix DynamoDB configuration | 1 min  |
| **fix-data-stack-v2.py**            | Fix DynamoDB (v2)          | 1 min  |
| **remove_humidity_sensor.py**       | Remove humidity sensor     | 2 min  |

---

## 🎯 Quick Start Guide

### First Time Setup

```bash
# Windows
quick-start.bat

# Linux/Mac
./quick-start.sh
```

### Deploy Everything

```bash
# Windows
deploy-all.bat

# Linux/Mac
./deploy-all.sh
```

### Optimize Costs (Save 57-68%)

```bash
ultra-cost-optimize.bat
```

### Test Infrastructure

```bash
test-everything.bat
```

### Delete Everything (₹0 cost)

```bash
delete-everything.bat
```

---

## 💰 Cost Management

### Current Deployment Status

- **Deployed Stacks**: 9/22
- **Monthly Cost**: ~₹2,500-3,500 (optimized)
- **Savings**: 57-68% from original

### Cost Options

| Option               | Monthly Cost | Script                  |
| -------------------- | ------------ | ----------------------- |
| **Keep Running**     | ₹3,000       | Do nothing              |
| **Optimize Further** | ₹2,500       | ultra-cost-optimize.bat |
| **Delete All**       | ₹0           | delete-everything.bat   |

**See**: [../docs/cost-optimization/](../docs/cost-optimization/) for detailed guides

---

## 📖 Documentation

For detailed guides:

- **[../docs/cost-optimization/](../docs/cost-optimization/)** - Cost optimization guides
- **[../docs/SETUP_GUIDE.md](../docs/SETUP_GUIDE.md)** - Setup instructions
- **[../docs/QUICK_FIX_GUIDE.md](../docs/QUICK_FIX_GUIDE.md)** - Troubleshooting
- **[../PROJECT_REPORT.md](../PROJECT_REPORT.md)** - Complete documentation

---

## 💡 Common Tasks

### "I want to deploy"

→ `deploy-all.bat` (Windows) or `./deploy-all.sh` (Linux/Mac)

### "I want to save money"

→ `ultra-cost-optimize.bat`

### "I want to test"

→ `test-everything.bat`

### "I want ₹0 cost"

→ `delete-everything.bat`

### "I want to check costs"

→ `check-free-tier-usage.bat`

### "I want to check my setup"

→ `check-aws.bat`

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

**Last Updated**: November 1, 2025  
**Status**: ✅ Scripts Cleaned & Organized
