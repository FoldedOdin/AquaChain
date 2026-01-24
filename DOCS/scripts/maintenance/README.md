# Maintenance Scripts

Scripts for system maintenance, optimization, and fixes.

## Scripts

### check_codebase.py
Check codebase for errors and issues.

**Usage:**
```bash
python check_codebase.py
```

**Checks:**
- Syntax errors
- Import issues
- Code quality

---

### disaster_recovery.py
Disaster recovery operations.

**Usage:**
```bash
python disaster_recovery.py --action <backup|restore>
```

---

### fix-data-stack.py
Fix DynamoDB configuration issues.

**Usage:**
```bash
python fix-data-stack.py
```

---

### fix-data-stack-v2.py
Fix DynamoDB configuration (version 2).

**Usage:**
```bash
python fix-data-stack-v2.py
```

---

### optimize-lambda-memory.py
Optimize Lambda function memory allocation.

**Usage:**
```bash
python optimize-lambda-memory.py
```

**Savings:** Reduces Lambda costs by optimizing memory

---

### remove_humidity_sensor.py
Remove humidity sensor from data model.

**Usage:**
```bash
python remove_humidity_sensor.py
```

---

### switch-dynamodb-to-provisioned.py
Switch DynamoDB from on-demand to provisioned capacity.

**Usage:**
```bash
python switch-dynamodb-to-provisioned.py
```

**Savings:** Can reduce costs for predictable workloads

---

### ultra-cost-optimize.bat
Optimize costs aggressively (57-68% savings).

**Usage:**
```bash
ultra-cost-optimize.bat
```

**Time:** ~30 minutes  
**Savings:** ₹3,000-4,000/month

**Optimizations:**
- Reduces Lambda memory
- Switches to provisioned capacity
- Removes non-essential services
- Optimizes CloudWatch logs

---

### delete-everything.bat
Delete all AWS stacks and resources.

**Usage:**
```bash
delete-everything.bat
```

**Time:** ~10 minutes  
**Cost:** Reduces to ₹0/month

⚠️ **Warning:** This deletes ALL resources!

---

### lint-all.sh
Lint all code (Python, JavaScript, TypeScript).

**Usage:**
```bash
./lint-all.sh
```

---

### lint-python.sh
Lint Python code only.

**Usage:**
```bash
./lint-python.sh
```
