# Testing Scripts

Scripts for testing and validating infrastructure and functionality.

## Scripts

### test-everything.bat
Run all infrastructure tests.

**Usage:**
```bash
test-everything.bat
```

**Time:** ~5 minutes  
**Tests:** All deployed stacks and services

---

### test_dr_integration.py
Test disaster recovery integration.

**Usage:**
```bash
python test_dr_integration.py
```

**Tests:**
- Backup functionality
- Restore procedures
- Failover mechanisms

---

### test_email_verification.py
Test email verification flow.

**Usage:**
```bash
python test_email_verification.py
```

**Tests:**
- Email sending
- Verification links
- Token validation

---

### test_enhanced_dr_features.py
Test enhanced disaster recovery features.

**Usage:**
```bash
python test_enhanced_dr_features.py
```

---

### validate_dr_implementation.py
Validate disaster recovery implementation.

**Usage:**
```bash
python validate_dr_implementation.py
```

---

### validate-phase3-deployment.py
Validate Phase 3 deployment.

**Usage:**
```bash
python validate-phase3-deployment.py
```

---

### validate-phase4-deployment.py
Validate Phase 4 deployment.

**Usage:**
```bash
python validate-phase4-deployment.py
```

---

### validate-phase4-implementation.py
Validate Phase 4 implementation details.

**Usage:**
```bash
python validate-phase4-implementation.py
```
