#!/usr/bin/env python3
"""
Secure Device Validation Module for AquaChain IoT Provisioning
Implements strict input validation to prevent injection attacks
"""

import re
from datetime import datetime, timedelta
from typing import Tuple, Optional
import html


class DeviceValidationError(Exception):
    """Custom exception for device validation errors"""
    pass


class DeviceValidator:
    """
    Secure validator for IoT device credentials and parameters
    """
    
    # Strict regex patterns
    DEVICE_ID_PATTERN = r'^DEV-[A-Z0-9]{4}$'
    SERIAL_NUMBER_PATTERN = r'^AQ-\d{8}-[A-Z0-9]{4}$'
    THING_NAME_PATTERN = r'^[a-zA-Z0-9:_-]+$'
    
    # SQL injection detection
    SQL_INJECTION_PATTERN = r"[';\"\\]|(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|SCRIPT)\b)"
    
    # XSS detection
    XSS_PATTERN = r'(<script|javascript:|on\w+\s*=|<iframe|<object|<embed)'
    
    # Maximum age for devices (years)
    MAX_DEVICE_AGE_YEARS = 10
    
    @classmethod
    def validate_device_id(cls, device_id: str) -> str:
        """
        Validate and sanitize device ID
        
        Args:
            device_id: Device identifier to validate
            
        Returns:
            Sanitized device ID
            
        Raises:
            DeviceValidationError: If validation fails
        """
        if not device_id or not isinstance(device_id, str):
            raise DeviceValidationError("Device ID is required and must be a string")
        
        # Remove whitespace
        device_id = device_id.strip().upper()
        
        # Check length
        if len(device_id) != 8:
            raise DeviceValidationError(
                f"Device ID must be exactly 8 characters, got {len(device_id)}"
            )
        
        # Check format
        if not re.match(cls.DEVICE_ID_PATTERN, device_id):
            raise DeviceValidationError(
                f"Invalid device ID format: {device_id}. "
                "Expected format: DEV-XXXX (e.g., DEV-3421)"
            )
        
        # Check for injection patterns
        if re.search(cls.SQL_INJECTION_PATTERN, device_id, re.IGNORECASE):
            raise DeviceValidationError(
                f"Device ID contains invalid characters: {device_id}"
            )
        
        if re.search(cls.XSS_PATTERN, device_id, re.IGNORECASE):
            raise DeviceValidationError(
                f"Device ID contains potentially malicious content: {device_id}"
            )
        
        return device_id
    
    @classmethod
    def validate_serial_number(cls, serial_number: str) -> Tuple[str, datetime]:
        """
        Validate and sanitize serial number
        
        Args:
            serial_number: Serial number to validate
            
        Returns:
            Tuple of (sanitized serial number, manufacture date)
            
        Raises:
            DeviceValidationError: If validation fails
        """
        if not serial_number or not isinstance(serial_number, str):
            raise DeviceValidationError("Serial number is required and must be a string")
        
        # Remove whitespace
        serial_number = serial_number.strip().upper()
        
        # Check length
        if len(serial_number) != 16:
            raise DeviceValidationError(
                f"Serial number must be exactly 16 characters, got {len(serial_number)}"
            )
        
        # Check format
        if not re.match(cls.SERIAL_NUMBER_PATTERN, serial_number):
            raise DeviceValidationError(
                f"Invalid serial number format: {serial_number}. "
                "Expected format: AQ-YYYYMMDD-XXXX (e.g., AQ-20251024-A1B2)"
            )
        
        # Check for injection patterns
        if re.search(cls.SQL_INJECTION_PATTERN, serial_number, re.IGNORECASE):
            raise DeviceValidationError(
                f"Serial number contains invalid characters: {serial_number}"
            )
        
        # Validate date component
        date_part = serial_number.split('-')[1]
        try:
            manufacture_date = datetime.strptime(date_part, '%Y%m%d')
        except ValueError:
            raise DeviceValidationError(
                f"Invalid date in serial number: {date_part}"
            )
        
        # Check if date is reasonable
        current_date = datetime.now()
        
        # Not in the future
        if manufacture_date > current_date:
            raise DeviceValidationError(
                f"Serial number date is in the future: {date_part}"
            )
        
        # Not too old
        age_years = (current_date - manufacture_date).days / 365.25
        if age_years > cls.MAX_DEVICE_AGE_YEARS:
            raise DeviceValidationError(
                f"Device is too old ({age_years:.1f} years). "
                f"Maximum age: {cls.MAX_DEVICE_AGE_YEARS} years"
            )
        
        return serial_number, manufacture_date
    
    @classmethod
    def validate_thing_name(cls, thing_name: str) -> str:
        """
        Validate AWS IoT Thing name
        
        Args:
            thing_name: Thing name to validate
            
        Returns:
            Sanitized thing name
            
        Raises:
            DeviceValidationError: If validation fails
        """
        if not thing_name or not isinstance(thing_name, str):
            raise DeviceValidationError("Thing name is required and must be a string")
        
        # Remove whitespace
        thing_name = thing_name.strip()
        
        # Check length (AWS IoT limit is 128 characters)
        if len(thing_name) > 128:
            raise DeviceValidationError(
                f"Thing name too long: {len(thing_name)} characters (max 128)"
            )
        
        # Check format (AWS IoT allows: a-zA-Z0-9:_-)
        if not re.match(cls.THING_NAME_PATTERN, thing_name):
            raise DeviceValidationError(
                f"Invalid thing name format: {thing_name}. "
                "Only alphanumeric characters, colons, underscores, and hyphens allowed"
            )
        
        return thing_name
    
    @classmethod
    def sanitize_attribute_value(cls, value: str, max_length: int = 800) -> str:
        """
        Sanitize attribute values for AWS IoT Thing attributes
        
        Args:
            value: Value to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized value
            
        Raises:
            DeviceValidationError: If validation fails
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise DeviceValidationError(
                f"Attribute value too long: {len(value)} characters (max {max_length})"
            )
        
        # HTML escape to prevent XSS
        value = html.escape(value)
        
        # Check for injection patterns
        if re.search(cls.SQL_INJECTION_PATTERN, value, re.IGNORECASE):
            raise DeviceValidationError(
                "Attribute value contains potentially malicious content"
            )
        
        return value
    
    @classmethod
    def validate_firmware_version(cls, version: str) -> str:
        """
        Validate firmware version string
        
        Args:
            version: Version string to validate (e.g., "1.0.0")
            
        Returns:
            Sanitized version string
            
        Raises:
            DeviceValidationError: If validation fails
        """
        if not version or not isinstance(version, str):
            raise DeviceValidationError("Firmware version is required and must be a string")
        
        # Semantic versioning pattern
        version_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
        
        version = version.strip()
        
        if not re.match(version_pattern, version):
            raise DeviceValidationError(
                f"Invalid firmware version format: {version}. "
                "Expected format: X.Y.Z or X.Y.Z-suffix (e.g., 1.0.0 or 1.0.0-beta)"
            )
        
        return version
    
    @classmethod
    def validate_location(cls, latitude: float, longitude: float) -> Tuple[float, float]:
        """
        Validate GPS coordinates
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            Tuple of validated (latitude, longitude)
            
        Raises:
            DeviceValidationError: If validation fails
        """
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError):
            raise DeviceValidationError(
                f"Invalid coordinates: latitude={latitude}, longitude={longitude}"
            )
        
        # Validate ranges
        if not (-90 <= lat <= 90):
            raise DeviceValidationError(
                f"Latitude out of range: {lat} (must be between -90 and 90)"
            )
        
        if not (-180 <= lon <= 180):
            raise DeviceValidationError(
                f"Longitude out of range: {lon} (must be between -180 and 180)"
            )
        
        return lat, lon
    
    @classmethod
    def validate_complete_device(cls, device_id: str, serial_number: str,
                                 firmware_version: str = "1.0.0",
                                 location: Optional[Tuple[float, float]] = None) -> dict:
        """
        Perform complete device validation
        
        Args:
            device_id: Device identifier
            serial_number: Device serial number
            firmware_version: Firmware version
            location: Optional GPS coordinates (latitude, longitude)
            
        Returns:
            Dictionary with validated device information
            
        Raises:
            DeviceValidationError: If any validation fails
        """
        validated = {}
        
        # Validate device ID
        validated['device_id'] = cls.validate_device_id(device_id)
        
        # Validate serial number
        validated['serial_number'], validated['manufacture_date'] = \
            cls.validate_serial_number(serial_number)
        
        # Validate firmware version
        validated['firmware_version'] = cls.validate_firmware_version(firmware_version)
        
        # Validate location if provided
        if location:
            validated['latitude'], validated['longitude'] = \
                cls.validate_location(location[0], location[1])
        
        return validated


def validate_device_for_provisioning(device_id: str, serial_number: str) -> bool:
    """
    Convenience function for device provisioning validation
    
    Args:
        device_id: Device identifier
        serial_number: Device serial number
        
    Returns:
        True if validation passes
        
    Raises:
        DeviceValidationError: If validation fails
    """
    try:
        validator = DeviceValidator()
        result = validator.validate_complete_device(device_id, serial_number)
        
        print(f"✅ Device validation passed:")
        print(f"   Device ID: {result['device_id']}")
        print(f"   Serial Number: {result['serial_number']}")
        print(f"   Manufacture Date: {result['manufacture_date'].strftime('%Y-%m-%d')}")
        print(f"   Firmware Version: {result['firmware_version']}")
        
        return True
        
    except DeviceValidationError as e:
        print(f"❌ Device validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test cases
    print("Testing Device Validator...")
    print("=" * 60)
    
    # Valid cases
    test_cases = [
        ("DEV-3421", "AQ-20251024-A1B2", True),
        ("DEV-ABCD", "AQ-20230101-XYZ9", True),
        ("dev-1234", "aq-20251024-test", False),  # Lowercase
        ("DEV-123", "AQ-20251024-A1B2", False),   # Too short
        ("DEV-'; DROP TABLE devices; --", "AQ-20251024-A1B2", False),  # SQL injection
        ("DEV-3421", "AQ-99991231-A1B2", False),  # Future date
        ("DEV-3421", "AQ-19001231-A1B2", False),  # Too old
    ]
    
    for device_id, serial, should_pass in test_cases:
        print(f"\nTesting: {device_id}, {serial}")
        try:
            result = validate_device_for_provisioning(device_id, serial)
            if result == should_pass:
                print(f"✅ Test passed (expected: {should_pass})")
            else:
                print(f"❌ Test failed (expected: {should_pass}, got: {result})")
        except Exception as e:
            if not should_pass:
                print(f"✅ Test passed (correctly rejected)")
            else:
                print(f"❌ Test failed (unexpected error): {e}")
