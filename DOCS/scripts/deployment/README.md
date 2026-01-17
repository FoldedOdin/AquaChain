# Deployment Scripts

Scripts for deploying and managing AWS infrastructure.

## Scripts

### deploy-all.bat/sh/ps1
Deploy all infrastructure stacks to AWS.

**Usage:**
```bash
# Windows
deploy-all.bat

# Linux/Mac
./deploy-all.sh

# PowerShell
./deploy-all.ps1
```

**Time:** ~30 minutes  
**Cost:** Sets up full infrastructure (~₹3,000/month)

---

### deploy-minimal.bat
Deploy minimal infrastructure for development.

**Usage:**
```bash
deploy-minimal.bat
```

**Time:** ~15 minutes  
**Cost:** Minimal infrastructure (~₹1,500/month)

---

### deploy.py
General deployment script with options.

**Usage:**
```bash
python deploy.py --stack <stack-name>
```

---

### deploy-phase4-infrastructure.py
Deploy Phase 4 infrastructure (ML and advanced features).

**Usage:**
```bash
python deploy-phase4-infrastructure.py
```

**Time:** ~20 minutes

---

### destroy-all-stacks.bat/sh
Delete all AWS stacks and resources.

**Usage:**
```bash
# Windows
destroy-all-stacks.bat

# Linux/Mac
./destroy-all-stacks.sh
```

**Time:** ~10 minutes  
**Cost:** Reduces to ₹0/month

---

### rollback.py
Rollback to previous deployment.

**Usage:**
```bash
python rollback.py --stack <stack-name>
```

---

### upload-sagemaker-model.py
Upload ML models to SageMaker.

**Usage:**
```bash
python upload-sagemaker-model.py
```

**Time:** ~10 minutes
