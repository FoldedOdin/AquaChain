# Quick Linting Guide

Fast reference for running code quality checks in AquaChain.

## 🚀 Quick Commands

### Run Everything
```bash
bash scripts/lint-all.sh
```

### Frontend Only
```bash
cd frontend
npm run lint              # Check for errors
npm run lint:fix          # Auto-fix errors
npm run format:check      # Check formatting
npm run format            # Auto-format
```

### Backend Only
```bash
bash scripts/lint-python.sh
```

### Specific Lambda Function
```bash
pylint lambda/data_processing/*.py --rcfile=.pylintrc
```

## 🔧 Setup (First Time)

### Frontend
```bash
cd frontend
npm ci
npm run prepare
```

### Backend
```bash
pip install -r requirements-dev.txt
```

## ✅ Pre-commit Checklist

1. Run linters: `bash scripts/lint-all.sh`
2. Fix any errors
3. Commit: `git commit -m "your message"`
4. Pre-commit hooks run automatically
5. Push: `git push`

## 🐛 Common Fixes

### "no-explicit-any" Error
```typescript
// ❌ Bad
const data: any = getData();

// ✅ Good
const data: SensorReading[] = getData();
```

### "line-too-long" Error
```python
# ❌ Bad
result = some_very_long_function_name(argument1, argument2, argument3, argument4, argument5)

# ✅ Good
result = some_very_long_function_name(
    argument1, argument2, argument3,
    argument4, argument5
)
```

### "missing-docstring" Error
```python
# ✅ Add docstring
def process_data(device_id: str) -> Dict:
    """
    Process device data.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Processed data dictionary
    """
    pass
```

## 🚫 Bypass Hooks (Emergency Only)
```bash
git commit --no-verify -m "Emergency fix"
```

## 📊 Check CI/CD Status

View pipeline results: GitHub → Actions tab

## 📚 Full Documentation

See [CODE_QUALITY_STANDARDS.md](./CODE_QUALITY_STANDARDS.md) for complete details.
