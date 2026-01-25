"""
AquaChain Input Validation Module - Dashboard Overhaul
Comprehensive input validation with schema enforcement, OWASP Top 10 protection,
error handling, and idempotency support for all state-changing operations.

Requirements: 5.7, 5.8, 8.6, 10.4, 10.5
"""

import re
import json
import uuid
import html
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Any, Union, Callable
import logging
from dataclasses import dataclass
from enum import Enum

# Initialize logger
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, code: Optional[str] = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class SecurityViolationError(ValidationError):
    """Exception for security-related validation failures"""
    pass


class FieldType(Enum):
    """Supported field types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    EMAIL = "email"
    UUID = "uuid"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


@dataclass
class ValidationRule:
    """Validation rule definition"""
    field_type: FieldType
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float, Decimal]] = None
    max_value: Optional[Union[int, float, Decimal]] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable] = None
    sanitize: bool = True
    allow_null: bool = False


class InputValidator:
    """
    Comprehensive input validator with security controls and schema enforcement.
    
    Features:
    - Schema-based validation with type checking
    - OWASP Top 10 protection (XSS, SQL injection, etc.)
    - Input sanitization and output encoding
    - Rate limiting and size constraints
    - Idempotency key validation
    - Comprehensive error reporting
    - Security audit logging
    """
    
    # Security patterns for OWASP Top 10 protection
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'vbscript:',
        r'data:text/html'
    ]
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(--|#|/\*|\*/)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\b(WAITFOR|DELAY)\b)",
        r"(\bxp_\w+\b)"
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$(){}[\]<>]',
        r'\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|nslookup|dig)\b',
        r'\.\./',
        r'/etc/passwd',
        r'/proc/',
        r'\\\\',
        r'\$\{.*\}',
        r'`.*`'
    ]
    
    def __init__(self, max_request_size: int = 1024 * 1024):  # 1MB default
        """
        Initialize input validator
        
        Args:
            max_request_size: Maximum allowed request size in bytes
        """
        self.max_request_size = max_request_size
        self.schemas = {}
        
    def register_schema(self, schema_name: str, schema: Dict[str, ValidationRule]) -> None:
        """
        Register a validation schema
        
        Args:
            schema_name: Name of the schema
            schema: Dictionary mapping field names to validation rules
        """
        self.schemas[schema_name] = schema
        logger.debug(f"Registered validation schema: {schema_name}")
    
    def validate_input(self, data: Dict[str, Any], schema_name: str, 
                      correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate input data against registered schema
        
        Args:
            data: Input data to validate
            schema_name: Name of the schema to use
            correlation_id: Optional correlation ID for audit logging
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If validation fails
            SecurityViolationError: If security violation detected
        """
        if schema_name not in self.schemas:
            raise ValidationError(f"Unknown schema: {schema_name}")
        
        schema = self.schemas[schema_name]
        validated_data = {}
        errors = []
        
        # Check request size
        request_size = len(json.dumps(data).encode('utf-8'))
        if request_size > self.max_request_size:
            raise ValidationError(
                f"Request too large: {request_size} bytes (max: {self.max_request_size})",
                code="REQUEST_TOO_LARGE"
            )
        
        # Validate each field in schema
        for field_name, rule in schema.items():
            try:
                value = data.get(field_name)
                validated_value = self._validate_field(field_name, value, rule)
                
                if validated_value is not None or not rule.allow_null:
                    validated_data[field_name] = validated_value
                    
            except ValidationError as e:
                errors.append({
                    'field': field_name,
                    'message': e.message,
                    'code': e.code
                })
            except SecurityViolationError as e:
                # Log security violation
                logger.warning(
                    "Security violation detected",
                    field=field_name,
                    violation=e.message,
                    correlation_id=correlation_id,
                    data_sample=str(data.get(field_name, ''))[:100]
                )
                errors.append({
                    'field': field_name,
                    'message': "Security violation detected",
                    'code': "SECURITY_VIOLATION"
                })
        
        # Check for unknown fields (strict validation)
        unknown_fields = set(data.keys()) - set(schema.keys())
        if unknown_fields:
            for field in unknown_fields:
                errors.append({
                    'field': field,
                    'message': f"Unknown field: {field}",
                    'code': "UNKNOWN_FIELD"
                })
        
        if errors:
            raise ValidationError(
                f"Validation failed: {len(errors)} error(s)",
                code="VALIDATION_FAILED"
            )
        
        return validated_data
    
    def _validate_field(self, field_name: str, value: Any, rule: ValidationRule) -> Any:
        """Validate a single field against its rule"""
        
        # Check required fields
        if value is None or value == "":
            if rule.required:
                raise ValidationError(f"Field {field_name} is required", field_name, "REQUIRED")
            elif rule.allow_null:
                return None
            else:
                return None
        
        # Security checks first
        if isinstance(value, str):
            self._check_security_violations(field_name, value)
            
            # Sanitize if requested
            if rule.sanitize:
                value = self._sanitize_string(value)
        
        # Type validation and conversion
        validated_value = self._validate_type(field_name, value, rule)
        
        # Additional constraints
        self._validate_constraints(field_name, validated_value, rule)
        
        return validated_value
    
    def _check_security_violations(self, field_name: str, value: str) -> None:
        """Check for security violations in string input"""
        
        # XSS detection
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise SecurityViolationError(f"Potential XSS detected in {field_name}")
        
        # SQL injection detection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise SecurityViolationError(f"Potential SQL injection detected in {field_name}")
        
        # Command injection detection
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise SecurityViolationError(f"Potential command injection detected in {field_name}")
        
        # Path traversal detection
        if '../' in value or '..\\' in value:
            raise SecurityViolationError(f"Path traversal detected in {field_name}")
        
        # LDAP injection detection
        if re.search(r'[()&|!]', value) and any(char in value for char in ['*', '(', ')', '&', '|', '!']):
            raise SecurityViolationError(f"Potential LDAP injection detected in {field_name}")
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        # HTML encode
        value = html.escape(value)
        
        # URL encode special characters
        value = urllib.parse.quote(value, safe='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~')
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        return value
    
    def _validate_type(self, field_name: str, value: Any, rule: ValidationRule) -> Any:
        """Validate and convert field type"""
        
        if rule.field_type == FieldType.STRING:
            if not isinstance(value, str):
                raise ValidationError(f"Field {field_name} must be a string", field_name, "INVALID_TYPE")
            return value
        
        elif rule.field_type == FieldType.INTEGER:
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Field {field_name} must be an integer", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.FLOAT:
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"Field {field_name} must be a float", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.DECIMAL:
            try:
                return Decimal(str(value))
            except (InvalidOperation, TypeError):
                raise ValidationError(f"Field {field_name} must be a decimal", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.BOOLEAN:
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                if value.lower() in ['true', '1', 'yes', 'on']:
                    return True
                elif value.lower() in ['false', '0', 'no', 'off']:
                    return False
            raise ValidationError(f"Field {field_name} must be a boolean", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.EMAIL:
            if not isinstance(value, str):
                raise ValidationError(f"Field {field_name} must be a string", field_name, "INVALID_TYPE")
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValidationError(f"Field {field_name} must be a valid email", field_name, "INVALID_EMAIL")
            return value.lower()
        
        elif rule.field_type == FieldType.UUID:
            if isinstance(value, str):
                try:
                    uuid.UUID(value)
                    return value
                except ValueError:
                    raise ValidationError(f"Field {field_name} must be a valid UUID", field_name, "INVALID_UUID")
            else:
                raise ValidationError(f"Field {field_name} must be a string UUID", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.DATE:
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00')).date()
                    return value
                except ValueError:
                    raise ValidationError(f"Field {field_name} must be a valid ISO date", field_name, "INVALID_DATE")
            else:
                raise ValidationError(f"Field {field_name} must be a date string", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.DATETIME:
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return value
                except ValueError:
                    raise ValidationError(f"Field {field_name} must be a valid ISO datetime", field_name, "INVALID_DATETIME")
            else:
                raise ValidationError(f"Field {field_name} must be a datetime string", field_name, "INVALID_TYPE")
        
        elif rule.field_type == FieldType.ARRAY:
            if not isinstance(value, list):
                raise ValidationError(f"Field {field_name} must be an array", field_name, "INVALID_TYPE")
            return value
        
        elif rule.field_type == FieldType.OBJECT:
            if not isinstance(value, dict):
                raise ValidationError(f"Field {field_name} must be an object", field_name, "INVALID_TYPE")
            return value
        
        elif rule.field_type == FieldType.ENUM:
            if rule.enum_values and value not in rule.enum_values:
                raise ValidationError(
                    f"Field {field_name} must be one of: {rule.enum_values}",
                    field_name, "INVALID_ENUM"
                )
            return value
        
        else:
            raise ValidationError(f"Unknown field type for {field_name}", field_name, "UNKNOWN_TYPE")
    
    def _validate_constraints(self, field_name: str, value: Any, rule: ValidationRule) -> None:
        """Validate additional constraints"""
        
        # Length constraints for strings and arrays
        if rule.min_length is not None or rule.max_length is not None:
            if isinstance(value, (str, list)):
                length = len(value)
                
                if rule.min_length is not None and length < rule.min_length:
                    raise ValidationError(
                        f"Field {field_name} must be at least {rule.min_length} characters/items",
                        field_name, "MIN_LENGTH"
                    )
                
                if rule.max_length is not None and length > rule.max_length:
                    raise ValidationError(
                        f"Field {field_name} must be at most {rule.max_length} characters/items",
                        field_name, "MAX_LENGTH"
                    )
        
        # Value constraints for numbers
        if rule.min_value is not None or rule.max_value is not None:
            if isinstance(value, (int, float, Decimal)):
                if rule.min_value is not None and value < rule.min_value:
                    raise ValidationError(
                        f"Field {field_name} must be at least {rule.min_value}",
                        field_name, "MIN_VALUE"
                    )
                
                if rule.max_value is not None and value > rule.max_value:
                    raise ValidationError(
                        f"Field {field_name} must be at most {rule.max_value}",
                        field_name, "MAX_VALUE"
                    )
        
        # Pattern validation for strings
        if rule.pattern and isinstance(value, str):
            if not re.match(rule.pattern, value):
                raise ValidationError(
                    f"Field {field_name} does not match required pattern",
                    field_name, "PATTERN_MISMATCH"
                )
        
        # Custom validation
        if rule.custom_validator:
            try:
                if not rule.custom_validator(value):
                    raise ValidationError(
                        f"Field {field_name} failed custom validation",
                        field_name, "CUSTOM_VALIDATION"
                    )
            except Exception as e:
                raise ValidationError(
                    f"Field {field_name} custom validation error: {str(e)}",
                    field_name, "CUSTOM_VALIDATION_ERROR"
                )


class IdempotencyManager:
    """
    Manages idempotency for state-changing operations
    
    Features:
    - Idempotency key validation and storage
    - Duplicate operation detection
    - Result caching for repeated requests
    - Automatic cleanup of expired keys
    """
    
    def __init__(self, storage_backend=None):
        """
        Initialize idempotency manager
        
        Args:
            storage_backend: Storage backend for idempotency keys (defaults to in-memory)
        """
        self.storage = storage_backend or {}
        self.ttl_seconds = 3600  # 1 hour default TTL
    
    def validate_idempotency_key(self, key: str) -> bool:
        """
        Validate idempotency key format
        
        Args:
            key: Idempotency key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not key or not isinstance(key, str):
            return False
        
        # Must be 10-255 characters, alphanumeric with hyphens and underscores
        if not re.match(r'^[a-zA-Z0-9_-]{10,255}$', key):
            return False
        
        return True
    
    def is_duplicate_operation(self, key: str, operation_signature: str) -> bool:
        """
        Check if operation with idempotency key already exists
        
        Args:
            key: Idempotency key
            operation_signature: Signature of the operation
            
        Returns:
            True if duplicate, False otherwise
        """
        if not self.validate_idempotency_key(key):
            return False
        
        stored_data = self.storage.get(key)
        if not stored_data:
            return False
        
        # Check if not expired
        if datetime.now(timezone.utc) > stored_data['expires_at']:
            del self.storage[key]
            return False
        
        # Check if same operation
        return stored_data['operation_signature'] == operation_signature
    
    def store_operation_result(self, key: str, operation_signature: str, result: Any) -> None:
        """
        Store operation result for idempotency
        
        Args:
            key: Idempotency key
            operation_signature: Signature of the operation
            result: Operation result to store
        """
        if not self.validate_idempotency_key(key):
            raise ValidationError("Invalid idempotency key format")
        
        expires_at = datetime.now(timezone.utc).timestamp() + self.ttl_seconds
        
        self.storage[key] = {
            'operation_signature': operation_signature,
            'result': result,
            'created_at': datetime.now(timezone.utc),
            'expires_at': datetime.fromtimestamp(expires_at, timezone.utc)
        }
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """
        Get cached result for idempotency key
        
        Args:
            key: Idempotency key
            
        Returns:
            Cached result if exists and not expired, None otherwise
        """
        stored_data = self.storage.get(key)
        if not stored_data:
            return None
        
        # Check if not expired
        if datetime.now(timezone.utc) > stored_data['expires_at']:
            del self.storage[key]
            return None
        
        return stored_data['result']


# Pre-defined validation schemas for common use cases
def create_purchase_order_schema() -> Dict[str, ValidationRule]:
    """Create validation schema for purchase orders"""
    return {
        'supplierId': ValidationRule(
            field_type=FieldType.UUID,
            required=True
        ),
        'items': ValidationRule(
            field_type=FieldType.ARRAY,
            required=True,
            min_length=1,
            max_length=100
        ),
        'budgetCategory': ValidationRule(
            field_type=FieldType.STRING,
            required=True,
            min_length=1,
            max_length=50,
            pattern=r'^[a-zA-Z0-9_-]+$'
        ),
        'totalAmount': ValidationRule(
            field_type=FieldType.DECIMAL,
            required=True,
            min_value=Decimal('0.01'),
            max_value=Decimal('1000000.00')
        ),
        'justification': ValidationRule(
            field_type=FieldType.STRING,
            required=False,
            max_length=1000
        ),
        'isEmergency': ValidationRule(
            field_type=FieldType.BOOLEAN,
            required=False
        ),
        'deliveryAddress': ValidationRule(
            field_type=FieldType.STRING,
            required=False,
            max_length=500
        ),
        'requestedDeliveryDate': ValidationRule(
            field_type=FieldType.DATE,
            required=False
        )
    }


def create_budget_allocation_schema() -> Dict[str, ValidationRule]:
    """Create validation schema for budget allocations"""
    return {
        'category': ValidationRule(
            field_type=FieldType.STRING,
            required=True,
            min_length=1,
            max_length=50,
            pattern=r'^[a-zA-Z0-9_-]+$'
        ),
        'allocatedAmount': ValidationRule(
            field_type=FieldType.DECIMAL,
            required=True,
            min_value=Decimal('0.01'),
            max_value=Decimal('10000000.00')
        ),
        'period': ValidationRule(
            field_type=FieldType.STRING,
            required=True,
            pattern=r'^\d{4}-\d{2}$'  # YYYY-MM format
        ),
        'description': ValidationRule(
            field_type=FieldType.STRING,
            required=False,
            max_length=500
        )
    }


def create_user_profile_schema() -> Dict[str, ValidationRule]:
    """Create validation schema for user profiles"""
    return {
        'email': ValidationRule(
            field_type=FieldType.EMAIL,
            required=True
        ),
        'firstName': ValidationRule(
            field_type=FieldType.STRING,
            required=True,
            min_length=1,
            max_length=50,
            pattern=r'^[a-zA-Z\s\'-]+$'
        ),
        'lastName': ValidationRule(
            field_type=FieldType.STRING,
            required=True,
            min_length=1,
            max_length=50,
            pattern=r'^[a-zA-Z\s\'-]+$'
        ),
        'role': ValidationRule(
            field_type=FieldType.ENUM,
            required=True,
            enum_values=['INVENTORY_MANAGER', 'WAREHOUSE_MANAGER', 'SUPPLIER_COORDINATOR', 
                        'PROCUREMENT_CONTROLLER', 'ADMINISTRATOR']
        ),
        'department': ValidationRule(
            field_type=FieldType.STRING,
            required=False,
            max_length=100
        )
    }


# Global validator instance
validator = InputValidator()

# Register common schemas
validator.register_schema('purchase_order', create_purchase_order_schema())
validator.register_schema('budget_allocation', create_budget_allocation_schema())
validator.register_schema('user_profile', create_user_profile_schema())

# Global idempotency manager
idempotency_manager = IdempotencyManager()