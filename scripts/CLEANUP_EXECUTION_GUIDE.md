# Scripts Cleanup Execution Guide

## 🎯 What This Cleanup Does

This cleanup reorganizes the AquaChain scripts folder from 250+ disorganized files to ~40 well-organized, documented scripts.

### Before & After

**BEFORE:**
```
scripts/
├── 24 root-level scripts (mixed purposes)
├── deployment/ (140+ scripts, many duplicates)
├── testing/ (60+ scripts, many one-off tests)
├── setup/ (25+ scripts, many redundant)
├── maintenance/ (15+ scripts, some outdated)
└── Other folders...
```

**AFTER:**
```
scripts/
├── README.md (comprehensive guide)
├── core/ (1 essential utility)
├── deployment/ (6 essential scripts)
├── setup/ (7 essential scripts)
├── testing/ (6 essential scripts)
├── security/ (7 scripts)
├── maintenance/ (4 scripts)
├── monitoring/ (2 scripts)
├── performance/ (1 script)
└── demo/ (4 scripts)
```

## 📋 Pre-Execution Checklist

Before running the cleanup:

- [ ] **Backup your work** - Commit any uncommitted changes
- [ ] **Review the plan** - Read `CLEANUP_PLAN.md`
- [ ] **Check dependencies** - Ensure no CI/CD depends on old scripts
- [ ] **Notify team** - Let team know about upcoming changes
- [ ] **Test environment** - Ensure you can test scripts after cleanup

## 🚀 Execution Steps

### Option 1: Automated Cleanup (Recommended)

```bash
# Run the cleanup script
scripts\run-cleanup.bat

# Or directly with PowerShell
.\scripts\cleanup-scripts.ps1
```

**What it does:**
1. Creates backup folder with timestamp
2. Removes 150+ redundant scripts
3. Reorganizes remaining scripts
4. Creates core utilities folder
5. Generates summary report

**Duration:** 2-3 minutes

### Option 2: Manual Review First

```bash
# 1. Review what will be deleted
Get-Content scripts\CLEANUP_PLAN.md

# 2. Create manual backup
Copy-Item scripts scripts-backup-manual -Recurse

# 3. Run cleanup
.\scripts\cleanup-scripts.ps1

# 4. Review changes
git status
```

## ✅ Post-Execution Verification

### 1. Verify Essential Scripts Exist

```bash
# Check core scripts
Test-Path scripts\core\build-lambda-packages.py

# Check deployment scripts
Test-Path scripts\deployment\deploy-all.bat
Test-Path scripts\deployment\deploy-all.ps1
Test-Path scripts\deployment\rollback.py

# Check setup scripts
Test-Path scripts\setup\quick-start.bat
Test-Path scripts\setup\start-local.bat

# Check testing scripts
Test-Path scripts\testing\comprehensive-system-test.py
Test-Path scripts\testing\run-comprehensive-test.bat
```

### 2. Test Critical Scripts

```bash
# Test deployment (dry run)
scripts\deployment\deploy-all.bat --help

# Test setup
scripts\setup\quick-start.bat --help

# Test testing
scripts\testing\run-comprehensive-test.bat --help
```

### 3. Verify Documentation

```bash
# Check main README exists
Test-Path scripts\README.md

# Check folder READMEs
Test-Path scripts\core\README.md
Test-Path scripts\deployment\README.md
Test-Path scripts\setup\README.md
Test-Path scripts\testing\COMPREHENSIVE_TEST_README.md
```

### 4. Review Git Changes

```bash
# See what was deleted
git status

# Review specific changes
git diff scripts/

# Check file count
Get-ChildItem scripts -Recurse -File | Measure-Object
```

## 🔄 Rollback Procedure

If you need to undo the cleanup:

### Option 1: From Automated Backup

```bash
# Find backup folder
Get-ChildItem scripts -Filter "backup-*"

# Restore from backup
$backupFolder = "scripts\backup-20260307-143022"  # Use actual folder name
Copy-Item "$backupFolder\*" scripts -Recurse -Force
```

### Option 2: From Git

```bash
# Discard all changes
git checkout -- scripts/

# Or reset to specific commit
git reset --hard HEAD~1
```

### Option 3: From Manual Backup

```bash
# If you created manual backup
Copy-Item scripts-backup-manual\* scripts -Recurse -Force
```

## 📊 Expected Results

### File Count Reduction

| Category | Before | After | Reduction |
|----------|--------|-------|-----------|
| Root Level | 24 | 0 | 100% |
| Deployment | 140+ | 6 | 96% |
| Testing | 60+ | 6 | 90% |
| Setup | 25+ | 7 | 72% |
| Maintenance | 15+ | 4 | 73% |
| **TOTAL** | **250+** | **~40** | **84%** |

### Size Reduction

- **Before:** ~15MB
- **After:** ~3MB
- **Reduction:** 80%

### Organization Improvement

- **Before:** Scattered, unclear structure
- **After:** Clear folder hierarchy
- **Documentation:** 5 new README files

## 🐛 Troubleshooting

### Issue: Cleanup Script Fails

**Solution:**
```bash
# Check PowerShell execution policy
Get-ExecutionPolicy

# Set if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run again
.\scripts\cleanup-scripts.ps1
```

### Issue: Backup Not Created

**Solution:**
```bash
# Create manual backup first
Copy-Item scripts scripts-backup-manual -Recurse

# Then run cleanup
.\scripts\cleanup-scripts.ps1
```

### Issue: Essential Script Missing

**Solution:**
```bash
# Restore from backup
$backupFolder = "scripts\backup-*"  # Use actual folder
Copy-Item "$backupFolder\{missing-script}" scripts\{target-folder}\
```

### Issue: Git Shows Too Many Changes

**Solution:**
```bash
# This is expected - 150+ files deleted
# Review changes carefully
git status | more

# Commit in stages if needed
git add scripts/core/
git commit -m "Add core utilities folder"

git add scripts/deployment/
git commit -m "Clean deployment folder"
# etc.
```

## 📝 Post-Cleanup Tasks

### 1. Update CI/CD Pipelines

Check if any CI/CD pipelines reference old scripts:

```yaml
# OLD
- run: scripts/deploy-orders-complete.ps1

# NEW
- run: scripts/deployment/deploy-all.ps1
```

### 2. Update Documentation

Update any documentation referencing old scripts:

- README files
- Wiki pages
- Runbooks
- Training materials

### 3. Notify Team

Send team notification:

```
Subject: Scripts Folder Reorganized

The scripts folder has been cleaned and reorganized:
- 150+ redundant scripts removed
- Clear folder structure created
- Comprehensive documentation added

Please review:
- scripts/README.md (main guide)
- scripts/CLEANUP_SUMMARY.md (what changed)
- scripts/ORGANIZATION_GUIDE.md (how to use)

Old scripts have been removed. See migration guide in CLEANUP_SUMMARY.md.
```

### 4. Delete Backup (After Verification)

After 1-2 weeks of successful usage:

```bash
# Delete automated backup
Remove-Item scripts\backup-* -Recurse -Force

# Delete manual backup (if created)
Remove-Item scripts-backup-manual -Recurse -Force
```

## 🎓 Training Team

### For Developers

1. **Share main README**: `scripts/README.md`
2. **Demo quick start**: Show `scripts/setup/quick-start.bat`
3. **Show testing**: Demo `scripts/testing/run-comprehensive-test.bat`
4. **Explain structure**: Walk through folder organization

### For DevOps

1. **Review deployment**: `scripts/deployment/README.md`
2. **Update pipelines**: Migrate to new script paths
3. **Test rollback**: Verify `rollback.py` works
4. **Monitor usage**: Track script execution

### For Security Team

1. **Review security scripts**: `scripts/security/`
2. **Schedule scans**: Set up automated security scans
3. **Review reports**: Check vulnerability reports
4. **Update procedures**: Update security runbooks

## ✨ Benefits Realized

### Immediate Benefits

- ✅ **Clarity**: Easy to find the right script
- ✅ **Speed**: Faster onboarding for new developers
- ✅ **Safety**: Reduced risk of using wrong script
- ✅ **Documentation**: Comprehensive guides available

### Long-Term Benefits

- ✅ **Maintainability**: Easier to maintain and update
- ✅ **Scalability**: Clear structure for adding new scripts
- ✅ **Quality**: Higher quality through organization
- ✅ **Efficiency**: Less time wasted searching for scripts

## 📞 Support

If you encounter issues:

1. **Check troubleshooting section** above
2. **Review CLEANUP_SUMMARY.md** for details
3. **Check backup folder** for rollback
4. **Ask in #dev-help** Slack channel
5. **Contact DevOps team** for assistance

## 🎉 Success Criteria

Cleanup is successful when:

- [ ] All essential scripts work correctly
- [ ] Documentation is comprehensive
- [ ] Team can find and use scripts easily
- [ ] CI/CD pipelines updated
- [ ] No critical functionality lost
- [ ] Team trained on new structure

---

**Cleanup Date:** March 2026  
**Executed By:** Kiro AI Assistant  
**Verified By:** Engineering Team  
**Status:** Ready for Execution
