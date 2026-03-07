# AquaChain Scripts Organization Guide

## 📊 Quick Reference Chart

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCRIPTS DIRECTORY MAP                         │
└─────────────────────────────────────────────────────────────────┘

🔧 CORE                    📦 DEPLOYMENT              ⚙️ SETUP
├─ build-lambda-packages   ├─ deploy-all             ├─ quick-start
└─ README                  ├─ destroy-all-stacks     ├─ setup-local
                           ├─ rollback               ├─ start-local
                           └─ README                 ├─ create-admin-user
                                                     └─ README

🧪 TESTING                 🔒 SECURITY                🛠️ MAINTENANCE
├─ comprehensive-test      ├─ dependency-scan        ├─ disaster-recovery
├─ run-comprehensive-test  ├─ generate-sbom          ├─ optimize-lambda
├─ production-validation   ├─ compare-sboms          ├─ reduce-log-retention
├─ test-everything         ├─ vulnerability-report   └─ check-codebase
└─ README                  ├─ check-sensitive-data
                           ├─ remove-sensitive-data
                           └─ manage-api-keys

📊 MONITORING              ⚡ PERFORMANCE             🎬 DEMO
├─ check-aws-costs         └─ run-load-tests         ├─ ml-model-demo
└─ create-payment-alarms                             ├─ ml-model-demo-auto
                                                     ├─ run-ml-demo
                                                     └─ README
```

## 🎯 Use Case → Script Mapping

### "I want to..."

#### Get Started
```
→ scripts/setup/quick-start.bat
   Complete setup for new developers
```

#### Deploy Changes
```
→ scripts/deployment/deploy-all.bat
   Deploy all infrastructure to AWS
```

#### Run Tests
```
→ scripts/testing/run-comprehensive-test.bat
   Run complete test suite with reports
```

#### Check Security
```
→ scripts/security/dependency-security-scan.py
   Scan for vulnerabilities
```

#### Monitor Costs
```
→ scripts/monitoring/check-aws-costs.ps1
   Check current AWS spending
```

#### Optimize Performance
```
→ scripts/performance/run-load-tests.py
   Run load tests
```

#### Recover from Disaster
```
→ scripts/maintenance/disaster-recovery.py
   Backup and restore procedures
```

#### Demo the System
```
→ scripts/demo/run-ml-demo.bat
   Run ML model demonstration
```

## 📋 Workflow Checklists

### New Developer Onboarding

```
□ Run scripts/setup/quick-start.bat
□ Verify AWS credentials: aws sts get-caller-identity
□ Start local dev: scripts/setup/start-local.bat
□ Run tests: scripts/testing/test-everything.bat
□ Read scripts/README.md
```

### Feature Development

```
□ Create feature branch: git checkout -b feature/my-feature
□ Make changes
□ Test locally: scripts/testing/run-comprehensive-test.bat dev
□ Deploy to dev: scripts/deployment/deploy-all.bat
□ Verify deployment: Check CloudWatch logs
□ Create PR
```

### Production Deployment

```
□ Merge to main branch
□ Run security scan: python scripts/security/dependency-security-scan.py
□ Run production validation: python scripts/testing/production-validation.py
□ Deploy: scripts/deployment/deploy-all.ps1 -Environment prod
□ Monitor: Check CloudWatch dashboards
□ Verify: Test critical paths
□ Document: Update deployment log
```

### Security Audit

```
□ Scan dependencies: python scripts/security/dependency-security-scan.py
□ Generate SBOM: python scripts/security/generate-sbom.py
□ Check for secrets: python scripts/security/check-sensitive-data.py
□ Generate report: python scripts/security/vulnerability-report-generator.py
□ Review findings
□ Remediate issues
```

### Performance Optimization

```
□ Run load tests: python scripts/performance/run-load-tests.py
□ Analyze results
□ Optimize Lambda: python scripts/maintenance/optimize-lambda-memory.py
□ Reduce logs: scripts/maintenance/reduce-log-retention.ps1
□ Re-test
□ Deploy optimizations
```

## 🗂️ File Naming Conventions

### Script Types

| Extension | Platform | Example |
|-----------|----------|---------|
| `.bat` | Windows CMD | `deploy-all.bat` |
| `.ps1` | Windows PowerShell | `deploy-all.ps1` |
| `.sh` | Linux/Mac Bash | `deploy-all.sh` |
| `.py` | Cross-platform Python | `rollback.py` |

### Naming Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| `{action}-{target}` | Action on target | `deploy-all.bat` |
| `{verb}-{noun}` | Verb-noun pattern | `check-costs.ps1` |
| `run-{name}` | Runner scripts | `run-comprehensive-test.bat` |
| `{name}-{platform}` | Platform-specific | `setup-local.bat` |

## 📚 Documentation Hierarchy

```
scripts/README.md                          ← Start here
├─ core/README.md                          ← Core utilities
├─ deployment/README.md                    ← Deployment guide
├─ setup/README.md                         ← Setup guide
├─ testing/COMPREHENSIVE_TEST_README.md    ← Testing guide
├─ CLEANUP_PLAN.md                         ← Cleanup rationale
├─ CLEANUP_SUMMARY.md                      ← Cleanup results
└─ ORGANIZATION_GUIDE.md                   ← This file
```

## 🔍 Finding the Right Script

### Decision Tree

```
What do you need to do?
│
├─ Setup/Install
│  └─ → scripts/setup/
│
├─ Deploy/Infrastructure
│  └─ → scripts/deployment/
│
├─ Test/Validate
│  └─ → scripts/testing/
│
├─ Security/Audit
│  └─ → scripts/security/
│
├─ Monitor/Costs
│  └─ → scripts/monitoring/
│
├─ Optimize/Performance
│  └─ → scripts/performance/
│
├─ Maintain/Recover
│  └─ → scripts/maintenance/
│
└─ Demo/Present
   └─ → scripts/demo/
```

## 🚀 Common Commands

### Daily Development

```bash
# Start work
git pull origin develop
scripts\setup\start-local.bat

# Test changes
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

# Update dependencies
pip install --upgrade -r requirements.txt
npm update
```

### Monthly Tasks

```bash
# Generate SBOM
python scripts/security/generate-sbom.py

# Optimize Lambda
python scripts/maintenance/optimize-lambda-memory.py

# Review logs retention
.\scripts\maintenance\reduce-log-retention.ps1
```

## 💡 Tips and Tricks

### Faster Workflows

1. **Create aliases** for frequently used scripts
   ```bash
   # PowerShell profile
   Set-Alias deploy scripts\deployment\deploy-all.ps1
   Set-Alias test scripts\testing\run-comprehensive-test.ps1
   ```

2. **Use tab completion** in PowerShell
   ```bash
   scripts\dep<TAB>  # Completes to scripts\deployment\
   ```

3. **Chain commands** for common workflows
   ```bash
   scripts\deployment\deploy-all.bat && scripts\testing\test-everything.bat
   ```

### Troubleshooting

1. **Check README first** - Most issues documented
2. **Review error messages** - Often self-explanatory
3. **Check prerequisites** - Ensure tools installed
4. **Verify AWS credentials** - `aws sts get-caller-identity`
5. **Ask for help** - #dev-help Slack channel

## 📞 Getting Help

### Resources

1. **Main README**: `scripts/README.md`
2. **Folder READMEs**: `scripts/{folder}/README.md`
3. **Cleanup docs**: `scripts/CLEANUP_*.md`
4. **Main docs**: `DOCS/`

### Support Channels

- **Slack**: #dev-help
- **Email**: engineering@aquachain.example.com
- **Wiki**: https://wiki.aquachain.example.com

## ✅ Best Practices

### DO

- ✅ Read README before running scripts
- ✅ Test in dev before staging/prod
- ✅ Create backups before destructive operations
- ✅ Document new scripts
- ✅ Follow naming conventions
- ✅ Keep scripts simple and focused

### DON'T

- ❌ Run production scripts without understanding
- ❌ Skip testing
- ❌ Hardcode credentials
- ❌ Create duplicate scripts
- ❌ Leave temporary scripts uncommitted
- ❌ Ignore error messages

## 🎓 Learning Path

### Beginner

1. Read `scripts/README.md`
2. Run `scripts/setup/quick-start.bat`
3. Explore `scripts/setup/` folder
4. Try `scripts/testing/test-everything.bat`

### Intermediate

1. Read `scripts/deployment/README.md`
2. Deploy to dev environment
3. Run comprehensive tests
4. Review security scripts

### Advanced

1. Create custom scripts
2. Optimize workflows
3. Contribute improvements
4. Mentor others

---

**Last Updated:** March 2026  
**Maintained By:** AquaChain Engineering Team
