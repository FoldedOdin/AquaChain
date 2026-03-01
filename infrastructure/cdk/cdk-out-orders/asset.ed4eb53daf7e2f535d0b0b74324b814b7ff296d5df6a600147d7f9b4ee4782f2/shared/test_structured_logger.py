"""
Unit tests for StructuredLogger
"""

import json
import logging
from io import StringIO
from structured_logger import StructuredLogger, get_logger


def test_structured_logger_basic():
    """Test basic structured logging functionality"""
    logger = StructuredLogger('test', service='test-service')
    
    # Capture log output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.logger.handlers = [handler]
    
    # Log a message
    logger.info("Test message", request_id="req-123", user_id="user-456")
    
    # Parse the JSON output
    log_output = stream.getvalue().strip()
    log_entry = json.loads(log_output)
    
    # Verify standard fields
    assert log_entry['level'] == 'INFO'
    assert log_entry['message'] == 'Test message'
    assert log_entry['service'] == 'test-service'
    assert log_entry['request_id'] == 'req-123'
    assert log_entry['user_id'] == 'user-456'
    assert 'timestamp' in log_entry
    
    print("✓ Basic structured logging test passed")


def test_structured_logger_custom_fields():
    """Test custom fields in structured logging"""
    logger = StructuredLogger('test', service='test-service')
    
    # Capture log output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.logger.handlers = [handler]
    
    # Log with custom fields
    logger.info(
        "Processing completed",
        request_id="req-123",
        device_id="DEV-1234",
        duration_ms=250.5,
        wqi=85.3
    )
    
    # Parse the JSON output
    log_output = stream.getvalue().strip()
    log_entry = json.loads(log_output)
    
    # Verify custom fields
    assert log_entry['device_id'] == 'DEV-1234'
    assert log_entry['duration_ms'] == 250.5
    assert log_entry['wqi'] == 85.3
    
    print("✓ Custom fields test passed")


def test_structured_logger_error_level():
    """Test error level logging"""
    logger = StructuredLogger('test', service='test-service')
    
    # Capture log output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.logger.handlers = [handler]
    
    # Log an error
    logger.error(
        "Operation failed",
        request_id="req-123",
        error_code="VALIDATION_ERROR",
        error_message="Invalid input"
    )
    
    # Parse the JSON output
    log_output = stream.getvalue().strip()
    log_entry = json.loads(log_output)
    
    # Verify error fields
    assert log_entry['level'] == 'ERROR'
    assert log_entry['message'] == 'Operation failed'
    assert log_entry['error_code'] == 'VALIDATION_ERROR'
    assert log_entry['error_message'] == 'Invalid input'
    
    print("✓ Error level logging test passed")


def test_get_logger_factory():
    """Test get_logger factory function"""
    logger = get_logger('test', service='factory-test')
    
    assert isinstance(logger, StructuredLogger)
    assert logger.service == 'factory-test'
    
    print("✓ Factory function test passed")


if __name__ == '__main__':
    test_structured_logger_basic()
    test_structured_logger_custom_fields()
    test_structured_logger_error_level()
    test_get_logger_factory()
    print("\n✅ All structured logger tests passed!")
