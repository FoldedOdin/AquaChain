# Phase 4 Code Quality Standards and Practices

## Overview

This document defines the code quality standards and practices for the AquaChain IoT water quality monitoring system. These standards ensure maintainability, reliability, and consistency across the codebase.

## Table of Contents

1. [Type Safety Standards](#type-safety-standards)
2. [Code Documentation](#code-documentation)
3. [Linting and Formatting](#linting-and-formatting)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Logging Standards](#logging-standards)
6. [Testing Requirements](#testing-requirements)
7. [Code Review Guidelines](#code-review-guidelines)

---

## Type Safety Standards

### Python Type Annotations

**Requirement**: All Python functions must include type hints for parameters and return values.

**Standard Format**:
```python
from typing import Dict, List, Optional, Union
from datetime import datetime

def process_sensor_data(
    device_id: str,
    readings: List[Dict[str, Union[float, str]]],
    timestamp: datetime
) -> Dict[str, any]:
    """
    Process sensor data from IoT devices.
    
    Args:
        device_id: Unique identifier for the IoT device
        readings: List of sensor readings with metric names and values
        timestamp: Time when readings were captured
        
    Returns:
        Processed data dictionary with validation results
        
    Raises:
        ValueError: If device_id is invalid or readings are malformed
    """
    pass
```

**Type Checking**:
- Use `mypy` for static type checking
- Configuration in `lambda/mypy.ini`
- Run: `mypy lambda/` before committing
- CI/CD pipeline enforces type checking

**Common Type Patterns**:
```python
# Optional values
user_id: Optional[str] = None

# Union types
value: Union[int, float, str]

# Generic collections
devices: List[Device]
config: Dict[str, any]

# Custom types
from typing import TypedDict

class SensorReading(TypedDict):
    device_id: str
    timestamp: datetime
    value: float
    unit: str
```

### TypeScript Type Definitions

**Requirement**: All TypeScript code must use strict type checking.

**Configuration** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

**Interface Definitions**:
```typescript
// Define interfaces for all data structures
interface Device {
  deviceId: string;
  userId: string;
  name: string;
  status: DeviceStatus;
  location?: GeoLocation;
  createdAt: Date;
  lastSeen: Date;
}

type DeviceStatus = 'active' | 'inactive' | 'maintenance' | 'error';

interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy: number;
}

// Function signatures
function getDevice(deviceId: string): Promise<Device>;
function updateDevice(deviceId: string, updates: Partial<Device>): Promise<Device>;
```

**React Component Types**:
```typescript
// Props interfaces
interface DeviceCardProps {
  device: Device;
  onSelect: (deviceId: string) => void;
  loading?: boolean;
}

// Component with typed props
const DeviceCard: React.FC<DeviceCardProps> = ({ device, onSelect, loading = false }) => {
  // Implementation
};

// Hook return types
function useDeviceData(deviceId: string): {
  device: Device | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
} {
  // Implementation
}
```

---

## Code Documentation

### Python Docstrings

**Standard**: Use Google-style docstrings for all public functions and classes.

**Format**:
```python
def calculate_water_quality_index(
    ph: float,
    turbidity: float,
    temperature: float,
    dissolved_oxygen: float
) -> float:
    """
    Calculate the Water Quality Index (WQI) from sensor readings.
    
    The WQI is a composite score from 0-100 indicating overall water quality.
    Higher scores indicate better water quality.
    
    Args:
        ph: pH level (0-14 scale)
        turbidity: Turbidity in NTU (Nephelometric Turbidity Units)
        temperature: Water temperature in Celsius
        dissolved_oxygen: Dissolved oxygen in mg/L
        
    Returns:
        Water Quality Index score (0-100)
        
    Raises:
        ValueError: If any parameter is outside valid range
        
    Example:
        >>> calculate_water_quality_index(7.2, 5.0, 20.0, 8.5)
        85.3
    """
    pass
```

**Class Documentation**:
```python
class DataExportService:
    """
    Service for exporting user data in compliance with GDPR.
    
    This service collects data from all system tables and generates
    a comprehensive JSON export file for the user.
    
    Attributes:
        dynamodb: DynamoDB resource client
        s3: S3 client for storing exports
        sns: SNS client for notifications
        
    Example:
        service = DataExportService()
        export_url = service.export_user_data('user-123')
    """
    
    def __init__(self):
        """Initialize the data export service with AWS clients."""
        pass
```

### TypeScript JSDoc Comments

**Standard**: Use JSDoc for complex functions and all exported utilities.

**Format**:
```typescript
/**
 * Fetches device data with automatic retry and caching.
 * 
 * This function implements exponential backoff retry logic and
 * caches successful responses for 5 minutes.
 * 
 * @param deviceId - Unique identifier for the device
 * @param options - Optional configuration for the request
 * @returns Promise resolving to device data
 * @throws {DeviceNotFoundError} If device doesn't exist
 * @throws {NetworkError} If request fails after retries
 * 
 * @example
 * ```typescript
 * const device = await fetchDeviceData('device-123');
 * console.log(device.status);
 * ```
 */
async function fetchDeviceData(
  deviceId: string,
  options?: RequestOptions
): Promise<Device> {
  // Implementation
}
```

---

## Linting and Formatting

### ESLint Configuration

**Location**: `frontend/.eslintrc.js`

**Key Rules**:
```javascript
module.exports = {
  extends: [
    'react-app',
    'react-app/jest',
    'plugin:@typescript-eslint/recommended',
    'prettier'
  ],
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-explicit-any': 'error',
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'complexity': ['warn', 10]
  }
};
```

**Running ESLint**:
```bash
# Check all files
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Check specific file
npx eslint src/components/Dashboard.tsx
```

### Pylint Configuration

**Location**: `.pylintrc`

**Key Settings**:
```ini
[MASTER]
disable=
    C0111,  # missing-docstring (enable gradually)
    R0903,  # too-few-public-methods
    
[FORMAT]
max-line-length=100

[DESIGN]
max-args=7
max-locals=15
max-returns=6
max-branches=12
max-statements=50

[SIMILARITIES]
min-similarity-lines=4
```

**Running Pylint**:
```bash
# Check all Lambda functions
./scripts/lint-python.sh

# Check specific file
pylint lambda/data_processing/handler.py

# Generate report
pylint lambda/ --output-format=json > pylint-report.json
```

### Pre-commit Hooks

**Configuration**: `.husky/pre-commit`

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run linters
npm run lint
./scripts/lint-python.sh

# Run type checking
npm run type-check
mypy lambda/

# Run tests
npm test -- --watchAll=false
pytest tests/unit/
```

---

## Error Handling Patterns

### Custom Error Classes

**Location**: `lambda/shared/errors.py`

**Standard Error Hierarchy**:
```python
class AquaChainError(Exception):
    """Base exception for AquaChain system"""
    def __init__(self, message: str, error_code: str, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AquaChainError):
    """Raised when input validation fails"""
    pass

class DeviceNotFoundError(AquaChainError):
    """Raised when device lookup fails"""
    pass

class AuthenticationError(AquaChainError):
    """Raised when authentication fails"""
    pass

class DatabaseError(AquaChainError):
    """Raised when database operations fail"""
    pass
```

### Error Handler Decorator

**Usage Pattern**:
```python
from lambda.shared.error_handler import handle_errors
from lambda.shared.errors import ValidationError, DeviceNotFoundError

@handle_errors
def lambda_handler(event, context):
    """Lambda function with standardized error handling"""
    
    # Validate input
    if not event.get('device_id'):
        raise ValidationError(
            message="Device ID is required",
            error_code="MISSING_DEVICE_ID",
            details={'event': event}
        )
    
    # Business logic
    device = get_device(event['device_id'])
    if not device:
        raise DeviceNotFoundError(
            message=f"Device {event['device_id']} not found",
            error_code="DEVICE_NOT_FOUND",
            details={'device_id': event['device_id']}
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps(device)
    }
```

### Frontend Error Handling

**Pattern**:
```typescript
// Custom error classes
class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorCode: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Error handling in API calls
async function fetchDevice(deviceId: string): Promise<Device> {
  try {
    const response = await fetch(`/api/devices/${deviceId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(
        error.message,
        response.status,
        error.error,
        error.details
      );
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      // Handle API errors
      console.error('API Error:', error.errorCode, error.message);
      throw error;
    } else {
      // Handle network errors
      console.error('Network Error:', error);
      throw new ApiError('Network request failed', 0, 'NETWORK_ERROR');
    }
  }
}
```

---

## Logging Standards

### Structured Logging Format

**Standard**: All logs must use structured JSON format with consistent fields.

**Required Fields**:
- `timestamp`: ISO 8601 format
- `level`: INFO, WARNING, ERROR, CRITICAL
- `message`: Human-readable message
- `service`: Service name
- `request_id`: Request correlation ID
- `user_id`: User identifier (if applicable)

**Python Implementation**:
```python
from lambda.shared.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

# Info logging
logger.info(
    'Processing sensor data',
    service='data_processing',
    request_id=context.request_id,
    device_id=device_id,
    duration_ms=processing_time
)

# Warning logging
logger.warning(
    'Query exceeded performance threshold',
    service='device_management',
    request_id=context.request_id,
    query_time_ms=query_time,
    threshold_ms=500
)

# Error logging
logger.error(
    'Failed to process sensor data',
    service='data_processing',
    request_id=context.request_id,
    device_id=device_id,
    error=str(e),
    traceback=traceback.format_exc()
)
```

**Log Levels**:
- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for failures that don't stop execution
- **CRITICAL**: Critical messages for failures that stop execution

---

## Testing Requirements

### Coverage Thresholds

**Minimum Requirements**:
- Lambda functions: 80% coverage
- React components: 80% coverage
- Integration tests: All critical workflows
- E2E tests: Key business scenarios

### Unit Testing Standards

**Python Tests** (`pytest`):
```python
import pytest
from lambda.data_processing.handler import process_sensor_data
from lambda.shared.errors import ValidationError

class TestDataProcessing:
    """Test suite for data processing Lambda"""
    
    def test_process_valid_sensor_data(self):
        """Test processing valid sensor data"""
        event = {
            'device_id': 'device-123',
            'readings': [
                {'metric': 'ph', 'value': 7.2},
                {'metric': 'temperature', 'value': 20.0}
            ]
        }
        
        result = process_sensor_data(event, {})
        
        assert result['statusCode'] == 200
        assert 'processed_data' in result
    
    def test_process_invalid_device_id(self):
        """Test processing with invalid device ID"""
        event = {'device_id': '', 'readings': []}
        
        with pytest.raises(ValidationError) as exc_info:
            process_sensor_data(event, {})
        
        assert exc_info.value.error_code == 'INVALID_DEVICE_ID'
```

**React Tests** (`Jest`):
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeviceCard } from './DeviceCard';

describe('DeviceCard', () => {
  const mockDevice = {
    deviceId: 'device-123',
    name: 'Test Device',
    status: 'active' as const,
    lastSeen: new Date()
  };
  
  it('renders device information', () => {
    render(<DeviceCard device={mockDevice} onSelect={jest.fn()} />);
    
    expect(screen.getByText('Test Device')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });
  
  it('calls onSelect when clicked', async () => {
    const onSelect = jest.fn();
    render(<DeviceCard device={mockDevice} onSelect={onSelect} />);
    
    await userEvent.click(screen.getByRole('button'));
    
    expect(onSelect).toHaveBeenCalledWith('device-123');
  });
});
```

### Integration Testing Standards

**Pattern**:
```python
import pytest
from tests.integration.helpers import create_test_user, create_test_device

@pytest.mark.integration
class TestDeviceProvisioningFlow:
    """Integration tests for device provisioning workflow"""
    
    def test_complete_provisioning_flow(self):
        """Test complete device provisioning from start to finish"""
        # Setup
        user = create_test_user()
        
        # Provision device
        device = provision_device(user['user_id'], 'Test Device')
        assert device['status'] == 'provisioning'
        
        # Activate device
        activate_device(device['device_id'])
        
        # Verify device is active
        updated_device = get_device(device['device_id'])
        assert updated_device['status'] == 'active'
        
        # Cleanup
        delete_device(device['device_id'])
        delete_user(user['user_id'])
```

---

## Code Review Guidelines

### Review Checklist

**Before Submitting PR**:
- [ ] All tests pass locally
- [ ] Code coverage meets 80% threshold
- [ ] Linting passes with no errors
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] No console.log or print statements (use proper logging)
- [ ] Error handling is implemented
- [ ] Security considerations addressed

**Reviewer Checklist**:
- [ ] Code follows style guidelines
- [ ] Logic is clear and maintainable
- [ ] Edge cases are handled
- [ ] Tests are comprehensive
- [ ] Performance implications considered
- [ ] Security vulnerabilities checked
- [ ] Documentation is accurate

### Review Process

1. **Self-Review**: Author reviews their own code before submitting
2. **Automated Checks**: CI/CD pipeline runs all checks
3. **Peer Review**: At least one team member reviews
4. **Address Feedback**: Author addresses all comments
5. **Approval**: Reviewer approves changes
6. **Merge**: Code is merged to main branch

### Common Issues to Watch For

**Performance**:
- Unnecessary re-renders in React
- N+1 query problems
- Missing pagination
- Inefficient algorithms

**Security**:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Exposed secrets or credentials
- Missing input validation
- Insufficient error messages (information disclosure)

**Maintainability**:
- Code duplication
- Complex functions (>50 lines)
- Deep nesting (>3 levels)
- Magic numbers without constants
- Unclear variable names

---

## Continuous Improvement

### Metrics to Track

- Code coverage percentage
- Linting violations count
- Type checking errors
- Code review turnaround time
- Bug density (bugs per 1000 lines)
- Technical debt ratio

### Regular Activities

**Weekly**:
- Review code quality metrics
- Address new linting violations
- Update dependencies

**Monthly**:
- Review and update coding standards
- Conduct code quality retrospective
- Refactor high-complexity modules

**Quarterly**:
- Major dependency updates
- Architecture review
- Technical debt reduction sprint

---

## Resources

### Tools

- **ESLint**: https://eslint.org/
- **Pylint**: https://pylint.org/
- **mypy**: https://mypy.readthedocs.io/
- **Jest**: https://jestjs.io/
- **pytest**: https://pytest.org/

### Internal Documentation

- [Quick Lint Guide](QUICK_LINT_GUIDE.md)
- [Code Quality Standards](CODE_QUALITY_STANDARDS.md)
- [Testing Strategy](DOCS/testing-strategy-ui-ux.md)

### Training Materials

- Python Type Hints: https://docs.python.org/3/library/typing.html
- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/
- React Testing Library: https://testing-library.com/react

---

**Document Version**: 1.0  
**Last Updated**: Phase 4 Implementation  
**Owner**: Development Team
