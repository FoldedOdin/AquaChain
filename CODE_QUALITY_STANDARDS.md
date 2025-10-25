# AquaChain Code Quality Standards

This document outlines the code quality standards and practices for the AquaChain IoT water quality monitoring system.

## Overview

Phase 4 introduces enhanced code quality infrastructure to ensure maintainable, well-documented, and thoroughly tested code across the entire project.

## Table of Contents

- [Frontend Standards (TypeScript/React)](#frontend-standards-typescriptreact)
- [Backend Standards (Python/Lambda)](#backend-standards-pythonlambda)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD Integration](#cicd-integration)
- [Running Quality Checks Locally](#running-quality-checks-locally)

## Frontend Standards (TypeScript/React)

### ESLint Configuration

The frontend uses ESLint with strict TypeScript rules configured in `frontend/.eslintrc.js`.

#### Key Rules

- **No `any` types**: `@typescript-eslint/no-explicit-any` is set to `error`
- **Explicit return types**: Functions should have explicit return types (warnings enabled)
- **Complexity limits**: Functions should not exceed complexity of 10
- **Max function length**: 50 lines per function (excluding comments and blank lines)
- **React Hooks**: Strict enforcement of hooks rules
- **Accessibility**: All JSX accessibility rules are enforced

#### Running ESLint

```bash
cd frontend

# Check for linting errors
npm run lint

# Auto-fix linting errors
npm run lint:fix
```

### Code Formatting

The project uses Prettier for consistent code formatting.

```bash
cd frontend

# Check formatting
npm run format:check

# Auto-format code
npm run format
```

### TypeScript Best Practices

1. **Always use explicit types**
   ```typescript
   // ❌ Bad
   function processData(data: any) {
     return data.map(item => item.value);
   }

   // ✅ Good
   function processData(data: SensorReading[]): number[] {
     return data.map((item: SensorReading) => item.value);
   }
   ```

2. **Use interfaces for object shapes**
   ```typescript
   interface SensorReading {
     deviceId: string;
     timestamp: Date;
     value: number;
     unit: string;
   }
   ```

3. **Avoid complexity**
   - Keep functions under 50 lines
   - Keep cyclomatic complexity under 10
   - Extract complex logic into separate functions

4. **Document complex functions**
   ```typescript
   /**
    * Processes sensor readings and calculates moving average
    * @param readings - Array of sensor readings
    * @param windowSize - Size of the moving average window
    * @returns Array of averaged values
    */
   function calculateMovingAverage(
     readings: SensorReading[],
     windowSize: number
   ): number[] {
     // Implementation
   }
   ```

## Backend Standards (Python/Lambda)

### Pylint Configuration

Python code is linted using Pylint with project-specific rules in `.pylintrc`.

#### Key Rules

- **Line length**: Maximum 100 characters
- **Function complexity**: Maximum 12 branches
- **Max arguments**: 7 parameters per function
- **Max locals**: 15 local variables per function
- **Naming conventions**: snake_case for functions and variables

#### Running Pylint

```bash
# Lint all Lambda functions
bash scripts/lint-python.sh

# Lint specific function
pylint lambda/data_processing/*.py --rcfile=.pylintrc

# Lint with score
pylint lambda/data_processing/*.py --rcfile=.pylintrc --score=yes
```

### Python Best Practices

1. **Type hints are required**
   ```python
   # ❌ Bad
   def process_sensor_data(device_id, readings):
       return sum(readings)

   # ✅ Good
   from typing import List, Dict
   
   def process_sensor_data(
       device_id: str,
       readings: List[float]
   ) -> float:
       """
       Process sensor data and return sum.
       
       Args:
           device_id: Unique identifier for the device
           readings: List of sensor reading values
           
       Returns:
           Sum of all readings
           
       Raises:
           ValueError: If readings list is empty
       """
       if not readings:
           raise ValueError("Readings list cannot be empty")
       return sum(readings)
   ```

2. **Docstrings are required for public functions**
   - Use Google-style docstrings
   - Include Args, Returns, and Raises sections
   - Minimum 10 lines for docstring requirement

3. **Error handling**
   ```python
   from lambda.shared.errors import ValidationError, DatabaseError
   
   def get_device(device_id: str) -> Dict:
       """Get device by ID."""
       if not device_id:
           raise ValidationError(
               "Device ID is required",
               error_code="INVALID_DEVICE_ID"
           )
       
       try:
           return dynamodb.get_item(Key={'device_id': device_id})
       except ClientError as e:
           raise DatabaseError(
               "Failed to retrieve device",
               error_code="DB_ERROR",
               details={'device_id': device_id, 'error': str(e)}
           )
   ```

4. **Use structured logging**
   ```python
   from lambda.shared.logging import StructuredLogger
   
   logger = StructuredLogger(__name__)
   
   logger.log('info', 'Processing device data',
       service='data_processing',
       device_id=device_id,
       duration_ms=processing_time
   )
   ```

## Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit.

### Frontend Pre-commit

Configured via `lint-staged` in `frontend/package.json`:

- Runs ESLint with auto-fix
- Runs Prettier formatting
- Fails if ESLint errors remain (max-warnings=0)

### Setup

```bash
cd frontend
npm install
npm run prepare  # Installs husky hooks
```

### Bypassing Hooks (Not Recommended)

```bash
git commit --no-verify -m "Emergency fix"
```

## CI/CD Integration

The CI/CD pipeline enforces code quality checks on every pull request and push.

### Code Quality Job

The `code-quality` job runs:

1. ESLint on frontend code
2. Prettier format checking
3. Pylint on all Lambda functions
4. TODO comment detection

### Pipeline Flow

```
code-quality (runs first)
    ↓
    ├─→ frontend-test
    ├─→ lambda-test
    └─→ security-scan
```

If code quality checks fail, subsequent jobs are blocked.

### Viewing Results

- Check the "Actions" tab in GitHub
- Failed checks will show detailed error messages
- Fix issues locally before pushing

## Running Quality Checks Locally

### Complete Quality Check

Run all quality checks at once:

```bash
# From project root
bash scripts/lint-all.sh
```

This script runs:
- Frontend ESLint
- Frontend Prettier check
- Python Pylint on all Lambda functions

### Individual Checks

```bash
# Frontend only
cd frontend
npm run lint
npm run format:check

# Backend only
bash scripts/lint-python.sh

# Specific Lambda function
pylint lambda/data_processing/*.py --rcfile=.pylintrc
```

## Development Workflow

1. **Before starting work**
   ```bash
   # Ensure dependencies are installed
   cd frontend && npm ci
   pip install -r requirements-dev.txt
   ```

2. **During development**
   - Write code following standards
   - Run linters frequently
   - Fix issues as they arise

3. **Before committing**
   ```bash
   # Run complete quality check
   bash scripts/lint-all.sh
   
   # If issues found, fix them
   cd frontend && npm run lint:fix
   cd frontend && npm run format
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # Pre-commit hooks run automatically
   ```

5. **Before pushing**
   ```bash
   # Final check
   bash scripts/lint-all.sh
   git push
   ```

## Handling Linting Errors

### Common ESLint Errors

1. **`@typescript-eslint/no-explicit-any`**
   - Replace `any` with specific types
   - Use `unknown` if type is truly unknown

2. **`complexity`**
   - Break down complex functions
   - Extract logic into helper functions

3. **`max-lines-per-function`**
   - Split large functions into smaller ones
   - Extract reusable logic

### Common Pylint Errors

1. **`line-too-long`**
   - Break long lines at 100 characters
   - Use parentheses for line continuation

2. **`too-many-arguments`**
   - Use dataclasses or dictionaries for grouped parameters
   - Consider if function is doing too much

3. **`missing-docstring`**
   - Add Google-style docstrings to all public functions

## Disabling Rules (Use Sparingly)

### ESLint

```typescript
// Disable for next line
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = legacyFunction();

// Disable for file (top of file)
/* eslint-disable @typescript-eslint/no-explicit-any */
```

### Pylint

```python
# Disable for line
result = some_function()  # pylint: disable=line-too-long

# Disable for block
# pylint: disable=too-many-arguments
def complex_function(arg1, arg2, arg3, arg4, arg5, arg6, arg7):
    pass
# pylint: enable=too-many-arguments
```

**Note**: Always add a comment explaining why a rule is disabled.

## Tools Installation

### Frontend Tools

```bash
cd frontend
npm install
```

Includes:
- ESLint
- Prettier
- TypeScript
- Husky
- lint-staged

### Backend Tools

```bash
pip install -r requirements-dev.txt
```

Includes:
- pylint
- black (code formatter)
- mypy (type checker)
- pytest
- pytest-cov

## Metrics and Goals

### Current Targets

- **ESLint**: 0 errors, 0 warnings
- **Pylint**: Score ≥ 8.0/10
- **Code Coverage**: ≥ 80%
- **Type Coverage**: 100% (no `any` types)

### Monitoring

- CI/CD pipeline tracks all metrics
- Failed checks block merges
- Coverage reports uploaded to Codecov

## Resources

- [ESLint Rules](https://eslint.org/docs/rules/)
- [TypeScript ESLint](https://typescript-eslint.io/)
- [Pylint Documentation](https://pylint.pycqa.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [React Best Practices](https://react.dev/learn)

## Support

For questions or issues with code quality standards:

1. Check this documentation
2. Review existing code examples
3. Ask in team chat
4. Create an issue in the repository

---

**Last Updated**: Phase 4 Implementation
**Version**: 1.0.0
