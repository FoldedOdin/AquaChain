# Setup Scripts

Scripts for initial setup and local development environment.

## Scripts

### quick-start.bat/sh
Interactive setup wizard for quick start.

**Usage:**
```bash
# Windows
quick-start.bat

# Linux/Mac
./quick-start.sh
```

**Time:** ~5 minutes  
**Features:**
- Checks prerequisites
- Configures AWS credentials
- Sets up local environment
- Guides through deployment options

---

### setup-local.bat/sh
Setup local development environment.

**Usage:**
```bash
# Windows
setup-local.bat

# Linux/Mac
./setup-local.sh
```

**Time:** ~10 minutes  
**Actions:**
- Installs Node.js dependencies
- Installs Python dependencies
- Configures environment variables
- Sets up local database

---

### start-local.bat/sh
Start local development servers.

**Usage:**
```bash
# Windows
start-local.bat

# Linux/Mac
./start-local.sh
```

**Starts:**
- Frontend dev server (http://localhost:3000)
- Backend API server (http://localhost:8000)
- Local DynamoDB (if configured)

**Note:** Run `setup-local` first!

---

### check-aws.bat
Check AWS connection and credentials.

**Usage:**
```bash
check-aws.bat
```

**Checks:**
- AWS CLI installation
- AWS credentials configuration
- AWS region setting
- IAM permissions

---

### check-free-tier-usage.bat
Check AWS free tier usage.

**Usage:**
```bash
check-free-tier-usage.bat
```

**Shows:**
- Current usage vs free tier limits
- Estimated monthly costs
- Services exceeding free tier
- Recommendations for cost reduction

---

### verify-region.bat
Verify AWS region configuration.

**Usage:**
```bash
verify-region.bat
```

**Checks:**
- Current AWS region
- Region-specific resources
- Multi-region configuration

---

## Quick Start Workflow

```bash
# 1. Check AWS setup
check-aws.bat

# 2. Run quick start wizard
quick-start.bat

# 3. Setup local environment
setup-local.bat

# 4. Start development servers
start-local.bat

# 5. Access application
# Open browser: http://localhost:3000
```

---

## Troubleshooting

### "AWS credentials not found"
Run `check-aws.bat` and follow the instructions to configure credentials.

### "Node.js not found"
Install Node.js from https://nodejs.org/ (v18 or later)

### "Python not found"
Install Python from https://python.org/ (v3.9 or later)

### "Port 3000 already in use"
Stop other applications using port 3000 or change the port in `.env`
