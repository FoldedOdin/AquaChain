"""
Comprehensive security middleware for AquaChain Lambda functions.
Implements input validation, sanitization, rate limiting, and security controls.
Requirements: 8.5
"""

import json
import re
import html
import time
import hashlib
import hmac
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from structured_logger import get_logger

logger = get_logger(__name__, service='security-middleware')

class SecurityError(Exception):
    """Base exception for security-related errors"""
    pass

class ValidationError(SecurityError):
    """Exception for input validation errors"""
    pass

class RateLimitError(SecurityError):
    """Exception for rate limiting violations"""
    pass

class InputValidator:
    """
    Comprehensive input validation and sanitization.
    Implements requirement 8.5 for input validation and XSS protection.
    """
    
    # Regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2}$'),
        'phone': re.compile(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$'),
        'device_id': re.compile(r'^DEV-[A-Z0-9]{4,8}$'),
        'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9_-]+$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]+$'),
        'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b|[\'";]|--|\*|/\*|\*/)', re.IGNORECASE),
        'xss_patterns': re.compile(r'(<script|javascript:|on\w+\s*=|<iframe|<object|<embed)', re.IGNORECASE)
    }
    
    # Data type constraints
    CONSTRAINTS = {
        'pH': {'min': 0.0, 'max': 14.0, 'type': float},
        'turbidity': {'min': 0.0, 'max': 4000.0, 'type': float},
        'tds': {'min': 0.0, 'max': 5000.0, 'type': float},
        'temperature': {'min': -40.0, 'max': 125.0, 'type': float},
        
        'wqi'
        'latitude': {'min': -90.0, 'max': 90.0, 'type': float},
        'longitude': {'min': -180.0, 'max': 180.0, 'type': float},
        'battery_level': {'min': 0, 'max': 100, 'type': int},
        'signal_strength': {'min': -120, 'max': 0, 'type': int}
    }
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and sanitize email address"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required and must be a string")
        
        email = email.strip().lower()
        
        if len(email) > 254:
            raise ValidationError("Email address too long")
        
        if not cls.PATTERNS['email'].match(email):
            raise ValidationError("Invalid email format")
        
        return email
    
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """Validate and sanitize phone number"""
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone number is required and must be a string")
        
        # Remove all non-digit characters except +
        phone = re.sub(r'[^\d+]', '', phone)
        
        if not cls.PATTERNS['phone'].match(phone):
            raise ValidationError("Invalid phone number format")
        
        return phone
    
    @classmethod
    def validate_device_id(cls, device_id: str) -> str:
        """Validate device ID format"""
        if not device_id or not isinstance(device_id, str):
            raise ValidationError("Device ID is required and must be a string")
        
        device_id = device_id.strip().upper()
        
        if not cls.PATTERNS['device_id'].match(device_id):
            raise ValidationError("Invalid device ID format")
        
        return device_id
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> str:
        """Validate UUID format"""
        if not uuid_str or not isinstance(uuid_str, str):
            raise ValidationError("UUID is required and must be a string")
        
        uuid_str = uuid_str.strip().lower()
        
        if not cls.PATTERNS['uuid'].match(uuid_str):
            raise ValidationError("Invalid UUID format")
        
        return uuid_str
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")
        
        # Check for SQL injection patterns
        if cls.PATTERNS['sql_injection'].search(text):
            raise ValidationError("Input contains potentially malicious SQL patterns")
        
        # Check for XSS patterns
        if cls.PATTERNS['xss_patterns'].search(text):
            raise ValidationError("Input contains potentially malicious script patterns")
        
        # Trim whitespace
        text = text.strip()
        
        # Check length
        if len(text) > max_length:
            raise ValidationError(f"Input too long (max {max_length} characters)")
        
        # HTML escape if not allowing HTML
        if not allow_html:
            text = html.escape(text)
        
        return text
    
    @classmethod
    def validate_sensor_reading(cls, reading_type: str, value: Union[int, float]) -> Union[int, float]:
        """Validate sensor reading values"""
        if reading_type not in cls.CONSTRAINTS:
            raise ValidationError(f"Unknown sensor reading type: {reading_type}")
        
        constraint = cls.CONSTRAINTS[reading_type]
        expected_type = constraint['type']
        
        # Type conversion and validation
        try:
            if expected_type == float:
                value = float(value)
            elif expected_type == int:
                value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid {reading_type} value type")
        
        # Range validation
        if value < constraint['min'] or value > constraint['max']:
            raise ValidationError(
                f"{reading_type} value {value} outside valid range "
                f"({constraint['min']} - {constraint['max']})"
            )
        
        return value
    
    @classmethod
    def validate_coordinates(cls, latitude: float, longitude: float) -> tuple:
        """Validate GPS coordinates"""
        lat = cls.validate_sensor_reading('latitude', latitude)
        lon = cls.validate_sensor_reading('longitude', longitude)
        return lat, lon
    
    @classmethod
    def validate_json_schema(cls, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON data against schema"""
        validated_data = {}
        
        # Check required fields
        required_fields = schema.get('required', '')
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Required field missing: {field}")
        
        # Validate each field
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in data:
                value = data[field]
                field_type = field_schema.get('type')
                
                # Type validation
                if field_type == 'string':
                    if not isinstance(value, str):
                        raise ValidationError(f"Field {field} must be a string")
                    max_length = field_schema.get('maxLength', 1000)
                    validated_data[field] = cls.sanitize_string(value, max_length)
                
                elif field_type == 'number':
                    if not isinstance(value, (int, float)):
                        raise ValidationError(f"Field {field} must be a number")
                    validated_data[field] = float(value)
                
                elif field_type == 'integer':
                    if not isinstance(value, int):
                        raise ValidationError(f"Field {field} must be an integer")
                    validated_data[field] = int(value)
                
                elif field_type == 'object':
                    if not isinstance(value, dict):
                        raise ValidationError(f"Field {field} must be an object")
                    # Recursively validate nested objects
                    nested_schema = field_schema.get('properties', {})
                    if nested_schema:
                        validated_data[field] = cls.validate_json_schema(value, field_schema)
                    else:
                        validated_data[field] = value
                
                elif field_type == 'array':
                    if not isinstance(value, list):
                        raise ValidationError(f"Field {field} must be an array")
                    validated_data[field] = value
                
                else:
                    validated_data[field] = value
        
        return validated_data

class RateLimiter:
    """
    Rate limiting with exponential backoff.
    Implements requirement 8.5 for rate limiting and DDoS protection.
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.rate_limit_table = self.dynamodb.Table('aquachain-rate-limits')
    
    def check_rate_limit(self, identifier: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Check if request is within rate limit.
        Returns True if allowed, False if rate limited.
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Get current request count
            response = self.rate_limit_table.get_item(
                Key={'identifier': identifier}
            )
            
            if 'Item' not in response:
                # First request - create entry
                self.rate_limit_table.put_item(
                    Item={
                        'identifier': identifier,
                        'requests': 1,
                        'window_start': current_time,
                        'ttl': current_time + window_seconds
                    }
                )
                return True
            
            item = response['Item']
            
            # Check if we're in a new window
            if item['window_start'] < window_start:
                # New window - reset counter
                self.rate_limit_table.put_item(
                    Item={
                        'identifier': identifier,
                        'requests': 1,
                        'window_start': current_time,
                        'ttl': current_time + window_seconds
                    }
                )
                return True
            
            # Check if within limit
            if item['requests'] >= limit:
                return False
            
            # Increment counter
            self.rate_limit_table.update_item(
                Key={'identifier': identifier},
                UpdateExpression='ADD requests :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
            return True
            
        except ClientError as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request if rate limiting fails
            return True
    
    def get_backoff_delay(self, attempt_count: int) -> int:
        """Calculate exponential backoff delay"""
        return min(300, (2 ** attempt_count) + (attempt_count * 2))  # Max 5 minutes

class CaptchaValidator:
    """
    CAPTCHA validation for authentication endpoints.
    Implements requirement 8.5 for CAPTCHA protection.
    """
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self._recaptcha_secret = None
    
    def _get_recaptcha_secret(self) -> str:
        """Get reCAPTCHA secret from AWS Secrets Manager"""
        if self._recaptcha_secret:
            return self._recaptcha_secret
        
        try:
            response = self.secrets_client.get_secret_value(
                SecretId='aquachain/recaptcha-secret'
            )
            self._recaptcha_secret = json.loads(response['SecretString'])['secret']
            return self._recaptcha_secret
        except ClientError as e:
            logger.error(f"Error getting reCAPTCHA secret: {e}")
            raise SecurityError("CAPTCHA validation unavailable")
    
    def verify_recaptcha(self, recaptcha_response: str, user_ip: str) -> bool:
        """Verify reCAPTCHA response"""
        import requests
        
        try:
            secret = self._get_recaptcha_secret()
            
            verification_url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': secret,
                'response': recaptcha_response,
                'remoteip': user_ip
            }
            
            response = requests.post(verification_url, data=data, timeout=10)
            result = response.json()
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {e}")
            return False

class SecurityMiddleware:
    """
    Main security middleware class that combines all security controls.
    """
    
    def __init__(self):
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter()
        self.captcha_validator = CaptchaValidator()
    
    def create_security_decorator(self, 
                                rate_limit: Optional[int] = None,
                                require_captcha: bool = False,
                                validate_schema: Optional[Dict[str, Any]] = None):
        """
        Create security decorator with specified controls.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
                try:
                    # Extract client information
                    client_ip = self._get_client_ip(event)
                    user_agent = event.get('headers', {}).get('User-Agent', '')
                    
                    # Rate limiting
                    if rate_limit:
                        identifier = f"{client_ip}:{func.__name__}"
                        if not self.rate_limiter.check_rate_limit(identifier, rate_limit):
                            return self._create_error_response(
                                429, "Rate limit exceeded", 
                                {"retryAfter": 60}
                            )
                    
                    # CAPTCHA validation
                    if require_captcha:
                        body = json.loads(event.get('body', '{}'))
                        recaptcha_response = body.get('recaptchaResponse')
                        
                        if not recaptcha_response:
                            return self._create_error_response(
                                400, "CAPTCHA response required"
                            )
                        
                        if not self.captcha_validator.verify_recaptcha(recaptcha_response, client_ip):
                            return self._create_error_response(
                                400, "CAPTCHA verification failed"
                            )
                    
                    # Input validation
                    if validate_schema and event.get('body'):
                        try:
                            body = json.loads(event['body'])
                            validated_body = self.validator.validate_json_schema(body, validate_schema)
                            event['body'] = json.dumps(validated_body)
                        except json.JSONDecodeError:
                            return self._create_error_response(
                                400, "Invalid JSON in request body"
                            )
                        except ValidationError as e:
                            return self._create_error_response(
                                400, f"Validation error: {str(e)}"
                            )
                    
                    # Validate path parameters
                    if event.get('pathParameters'):
                        event['pathParameters'] = self._validate_path_parameters(
                            event['pathParameters']
                        )
                    
                    # Validate query parameters
                    if event.get('queryStringParameters'):
                        event['queryStringParameters'] = self._validate_query_parameters(
                            event['queryStringParameters']
                        )
                    
                    # Add security headers to event context
                    event['securityContext'] = {
                        'clientIp': client_ip,
                        'userAgent': user_agent,
                        'timestamp': datetime.utcnow().isoformat(),
                        'requestId': context.aws_request_id if hasattr(context, 'aws_request_id') else None
                    }
                    
                    # Call original function
                    response = func(event, context)
                    
                    # Add security headers to response
                    if isinstance(response, dict) and 'headers' in response:
                        response['headers'].update(self._get_security_headers())
                    
                    return response
                    
                except ValidationError as e:
                    logger.warning(f"Validation error: {e}")
                    return self._create_error_response(400, str(e))
                
                except RateLimitError as e:
                    logger.warning(f"Rate limit error: {e}")
                    return self._create_error_response(429, str(e))
                
                except SecurityError as e:
                    logger.error(f"Security error: {e}")
                    return self._create_error_response(403, "Security validation failed")
                
                except Exception as e:
                    logger.error(f"Unexpected security middleware error: {e}")
                    return self._create_error_response(500, "Internal server error")
            
            return wrapper
        return decorator
    
    def _get_client_ip(self, event: Dict[str, Any]) -> str:
        """Extract client IP from event"""
        # Check for IP in various headers (considering load balancers/proxies)
        headers = event.get('headers', {})
        
        # X-Forwarded-For header (most common)
        forwarded_for = headers.get('X-Forwarded-For', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # X-Real-IP header
        real_ip = headers.get('X-Real-IP', '')
        if real_ip:
            return real_ip
        
        # Request context source IP
        request_context = event.get('requestContext', {})
        identity = request_context.get('identity', {})
        source_ip = identity.get('sourceIp', '')
        
        return source_ip or '0.0.0.0'
    
    def _validate_path_parameters(self, path_params: Dict[str, str]) -> Dict[str, str]:
        """Validate and sanitize path parameters"""
        validated_params = {}
        
        for key, value in path_params.items():
            if not isinstance(value, str):
                raise ValidationError(f"Path parameter {key} must be a string")
            
            # Sanitize based on parameter name
            if key in ['deviceId']:
                validated_params[key] = self.validator.validate_device_id(value)
            elif key in ['userId', 'requestId']:
                validated_params[key] = self.validator.validate_uuid(value)
            else:
                validated_params[key] = self.validator.sanitize_string(value, 100)
        
        return validated_params
    
    def _validate_query_parameters(self, query_params: Dict[str, str]) -> Dict[str, str]:
        """Validate and sanitize query parameters"""
        validated_params = {}
        
        for key, value in query_params.items():
            if not isinstance(value, str):
                raise ValidationError(f"Query parameter {key} must be a string")
            
            # Sanitize based on parameter name
            if key in ['days', 'limit']:
                try:
                    int_value = int(value)
                    if int_value < 0 or int_value > 1000:
                        raise ValidationError(f"Query parameter {key} out of range")
                    validated_params[key] = str(int_value)
                except ValueError:
                    raise ValidationError(f"Query parameter {key} must be an integer")
            else:
                validated_params[key] = self.validator.sanitize_string(value, 200)
        
        return validated_params
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def _create_error_response(self, status_code: int, message: str, 
                             extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        body = {'error': message}
        if extra_data:
            body.update(extra_data)
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                **self._get_security_headers()
            },
            'body': json.dumps(body)
        }

# Global security middleware instance
security_middleware = SecurityMiddleware()

# Convenience decorators
def secure_endpoint(rate_limit: int = 100, require_captcha: bool = False, 
                   validate_schema: Optional[Dict[str, Any]] = None):
    """Decorator for securing API endpoints"""
    return security_middleware.create_security_decorator(
        rate_limit=rate_limit,
        require_captcha=require_captcha,
        validate_schema=validate_schema
    )

def auth_endpoint(rate_limit: int = 10, require_captcha: bool = True):
    """Decorator for authentication endpoints with stricter security"""
    return security_middleware.create_security_decorator(
        rate_limit=rate_limit,
        require_captcha=require_captcha
    )