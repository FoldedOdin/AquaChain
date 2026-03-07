# 🚀 Scripts Folder - START HERE

## Welcome to AquaChain Scripts!

This folder contains all automation scripts for the AquaChain IoT water quality monitoring system.

## 📚 Documentation Index

### 🎯 Quick Start
- **[README.md](README.md)** - Main guide with quick start commands
- **[ORGANIZATION_GUIDE.md](ORGANIZATION_GUIDE.md)** - Visual guide to folder structure

### 🧹 Cleanup Information
- **[CLEANUP_EXECUTION_GUIDE.md](CLEANUP_EXECUTION_GUIDE.md)** - How to run the cleanup
- **[CLEANUP_PLAN.md](CLEANUP_PLAN.md)** - What will be cleaned and why
- **[CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)** - Results and impact analysis

### 📂 Folder-Specific Guides
- **[core/README.md](core/README.md)** - Core utilities documentation
- **[deployment/README.md](deployment/README.md)** - Deployment guide
- **[setup/README.md](setup/README.md)** - Setup and configuration guide
- **[testing/COMPREHENSIVE_TEST_README.md](testing/COMPREHENSIVE_TEST_README.md)** - Testing guide

## 🎯 What Do You Want to Do?

### I'm a New Developer
```bash
1. Read: scripts/README.md
2. Run: scripts/setup/quick-start.bat
3. Start: scripts/setup/start-local.bat
```

### I Want to Deploy
```bash
1. Read: scripts/deployment/README.md
2. Run: scripts/deployment/deploy-all.bat
3. Verify: Check CloudWatch logs
```

### I Want to Test
```bash
1. Read: scripts/testing/COMPREHENSIVE_TEST_README.md
2. Run: scripts/testing/run-comprehensive-test.bat dev
3. Review: Open HTML report
```

### I Want to Clean Up Scripts
```bash
1. Read: scripts/CLEANUP_EXECUTION_GUIDE.md
2. Run: scripts/run-cleanup.bat
3. Verify: Test essential scripts
```

## 📊 Folder Structure

```
scripts/
├── 📖 START_HERE.md              ← You are here
├── 📖 README.md                  ← Main documentation
├── 📖 ORGANIZATION_GUIDE.md      ← Visual guide
├── 🧹 CLEANUP_*.md               ← Cleanup documentation
│
├── 🔧 core/                      ← Core utilities
│   ├── build-lambda-packages.py
│   └── README.md
│
├── 📦 deployment/                ← Deployment scripts
│   ├── deploy-all.bat/.ps1/.sh
│   ├── destroy-all-stacks.bat/.sh
│   ├── rollback.py
│   └── README.md
│
├── ⚙️ setup/                     ← Setup scripts
│   ├── quick-start.bat/.sh
│   ├── setup-local.bat/.sh
│   ├── start-local.bat/.sh
│   ├── create-admin-user.ps1
│   └── README.md
│
├── 🧪 testing/                   ← Testing scripts
│   ├── comprehensive-system-test.py
│   ├── run-comprehensive-test.bat/.ps1
│   ├── production_readiness_validation.py
│   ├── test-everything.bat
│   └── COMPREHENSIVE_TEST_README.md
│
├── 🔒 security/                  ← Security tools
│   ├── dependency-security-scan.py
│   ├── generate-sbom.py
│   ├── vulnerability-report-generator.py
│   └── ...
│
├── 🛠️ maintenance/               ← Maintenance utilities
│   ├── disaster_recovery.py
│   ├── optimize-lambda-memory.py
│   └── ...
│
├── 📊 monitoring/                ← Monitoring tools
│   ├── check-aws-costs.ps1
│   └── create-payment-alarms.ps1
│
├── ⚡ performance/               ← Performance testing
│   └── run_load_tests.py
│
└── 🎬 demo/                      ← Demo scripts
    ├── ml_model_demo.py
    └── README.md
```

## 🚀 Most Common Commands

### Daily Development
```bash
# Start development
scripts\setup\start-local.bat

# Run tests
scripts\testing\test-everything.bat

# Deploy to dev
scripts\deployment\deploy-all.bat
```

### Weekly Tasks
```bash
# Security scan
python scripts/security/dependency-security-scan.py

# Check costs
.\scripts\monitoring\check-aws-costs.ps1
```

### One-Time Setup
```bash
# Complete setup
scripts\setup\quick-start.bat

# Clean up scripts folder
scripts\run-cleanup.bat
```

## 📖 Reading Order

### For New Team Members
1. **START_HERE.md** (this file)
2. **README.md** (main guide)
3. **setup/README.md** (setup guide)
4. **ORGANIZATION_GUIDE.md** (structure guide)

### For Deploying
1. **deployment/README.md** (deployment guide)
2. **testing/COMPREHENSIVE_TEST_README.md** (testing guide)
3. **README.md** (troubleshooting)

### For Cleanup
1. **CLEANUP_EXECUTION_GUIDE.md** (how to execute)
2. **CLEANUP_PLAN.md** (what will change)
3. **CLEANUP_SUMMARY.md** (expected results)

## 🎓 Learning Path

### Beginner (Week 1)
- [ ] Read START_HERE.md
- [ ] Read README.md
- [ ] Run quick-start.bat
- [ ] Explore setup folder
- [ ] Run test-everything.bat

### Intermediate (Week 2-4)
- [ ] Read deployment/README.md
- [ ] Deploy to dev environment
- [ ] Run comprehensive tests
- [ ] Review security scripts
- [ ] Understand folder structure

### Advanced (Month 2+)
- [ ] Create custom scripts
- [ ] Optimize workflows
- [ ] Contribute improvements
- [ ] Mentor new developers
- [ ] Maintain documentation

## 💡 Pro Tips

1. **Use tab completion** - PowerShell supports tab completion for paths
2. **Create aliases** - Set up aliases for frequently used scripts
3. **Read error messages** - They're usually self-explanatory
4. **Check README first** - Most questions answered in documentation
5. **Ask for help** - #dev-help Slack channel is there for you

## 🐛 Quick Troubleshooting

### Script Won't Run
```bash
# Windows: Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Linux/Mac: Make executable
chmod +x scripts/setup/quick-start.sh
```

### AWS Credentials Error
```bash
# Check credentials
aws sts get-caller-identity

# Reconfigure
aws configure
```

### Python Module Not Found
```bash
# Install dependencies
pip install -r requirements.txt
```

## 📞 Getting Help

### Resources
1. **Documentation** - Check README files
2. **Slack** - #dev-help channel
3. **Wiki** - https://wiki.aquachain.example.com
4. **Email** - engineering@aquachain.example.com

### Before Asking
- [ ] Read relevant README
- [ ] Check troubleshooting section
- [ ] Review error message
- [ ] Try basic fixes (restart, reinstall)

## ✅ Next Steps

Choose your path:

### Path 1: New Developer
```bash
→ Read README.md
→ Run scripts/setup/quick-start.bat
→ Start coding!
```

### Path 2: Deploy Changes
```bash
→ Read deployment/README.md
→ Run scripts/deployment/deploy-all.bat
→ Verify deployment
```

### Path 3: Run Tests
```bash
→ Read testing/COMPREHENSIVE_TEST_README.md
→ Run scripts/testing/run-comprehensive-test.bat
→ Review reports
```

### Path 4: Clean Up Scripts
```bash
→ Read CLEANUP_EXECUTION_GUIDE.md
→ Run scripts/run-cleanup.bat
→ Verify changes
```

## 🎉 You're Ready!

You now have everything you need to work with AquaChain scripts. Pick your path above and get started!

---

**Questions?** Check [README.md](README.md) or ask in #dev-help

**Last Updated:** March 2026  
**Maintained By:** AquaChain Engineering Team
