# Security Scripts

Scripts for security scanning, vulnerability checks, and compliance.

## Scripts

### check-sensitive-data.py
Scan codebase for sensitive data (API keys, passwords, etc.).

**Usage:**
```bash
python check-sensitive-data.py
```

**Checks:**
- AWS credentials
- API keys
- Passwords
- Email addresses
- Personal information

---

### dependency-check.py
Check dependency versions and compatibility.

**Usage:**
```bash
python dependency-check.py
```

---

### dependency-security-scan.py
Scan dependencies for known vulnerabilities.

**Usage:**
```bash
python dependency-security-scan.py
```

**Output:** Vulnerability report with severity levels

---

### generate-sbom.py
Generate Software Bill of Materials (SBOM).

**Usage:**
```bash
python generate-sbom.py
```

**Output:** `sbom-artifacts/` directory with SBOM files

---

### compare-sboms.py
Compare SBOM versions to detect changes.

**Usage:**
```bash
python compare-sboms.py --old <old-sbom> --new <new-sbom>
```

---

### vulnerability-report-generator.py
Generate comprehensive vulnerability report.

**Usage:**
```bash
python vulnerability-report-generator.py
```

**Output:** Detailed vulnerability report with recommendations

---

### manage-api-keys.py
Manage API keys securely.

**Usage:**
```bash
python manage-api-keys.py --action <create|rotate|delete>
```

**Actions:**
- Create new API keys
- Rotate existing keys
- Delete old keys
