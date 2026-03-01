"""
Cold Start Monitor for Lambda Functions

This module provides utilities to detect and log cold starts in Lambda functions.
It tracks initialization time and logs warnings when cold starts exceed thresholds.
"""

import time
import os
import json
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime

# Global variable to track if this is a cold start
_is_cold_start = True
_init_start_time = time.time()


class ColdStartMonitor:
    """Monitor and log Lambda cold starts"""

    def __init__(self, threshold_ms: int = 2000):
        """
        Initialize cold start monitor

        Args:
            threshold_ms: Threshold in milliseconds for cold start warning (default: 2000ms)
        """
        self.threshold_ms = threshold_ms
        self.cold_start_threshold_seconds = threshold_ms / 1000.0

    def log_cold_start(self, duration_ms: float, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log cold start metrics

        Args:
            duration_ms: Cold start duration in milliseconds
            context: Additional context to log
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "cold_start",
            "duration_ms": duration_ms,
            "threshold_ms": self.threshold_ms,
            "exceeded_threshold": duration_ms > self.threshold_ms,
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
            "function_version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "unknown"),
            "memory_size": os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "unknown"),
        }

        if context:
            log_entry["context"] = context

        # Log as JSON for structured logging
        print(json.dumps(log_entry))

        # Log warning if threshold exceeded
        if duration_ms > self.threshold_ms:
            print(
                f"WARNING: Cold start duration ({duration_ms:.2f}ms) exceeded threshold ({self.threshold_ms}ms)"
            )

    def track_init_duration(self) -> float:
        """
        Track initialization duration since module load

        Returns:
            Initialization duration in milliseconds
        """
        global _init_start_time
        init_duration_ms = (time.time() - _init_start_time) * 1000
        return init_duration_ms

    def is_cold_start(self) -> bool:
        """
        Check if this is a cold start

        Returns:
            True if this is a cold start, False otherwise
        """
        global _is_cold_start
        return _is_cold_start

    def mark_warm_start(self) -> None:
        """Mark that the function has warmed up"""
        global _is_cold_start
        _is_cold_start = False


# Global monitor instance
cold_start_monitor = ColdStartMonitor()


def monitor_cold_start(func):
    """
    Decorator to monitor cold starts in Lambda handlers

    Usage:
        @monitor_cold_start
        def lambda_handler(event, context):
            # Your handler code
            pass
    """

    @wraps(func)
    def wrapper(event, context):
        global _is_cold_start

        # Check if this is a cold start
        if _is_cold_start:
            init_duration_ms = cold_start_monitor.track_init_duration()

            # Log cold start metrics
            cold_start_monitor.log_cold_start(
                duration_ms=init_duration_ms,
                context={
                    "request_id": getattr(context, "request_id", None),
                    "invoked_function_arn": getattr(context, "invoked_function_arn", None),
                },
            )

            # Mark as warm for subsequent invocations
            _is_cold_start = False

        # Execute the handler
        return func(event, context)

    return wrapper


def log_performance_metrics(
    operation: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log performance metrics for operations

    Args:
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        metadata: Additional metadata to log
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "performance_metric",
        "operation": operation,
        "duration_ms": duration_ms,
        "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
    }

    if metadata:
        log_entry["metadata"] = metadata

    print(json.dumps(log_entry))


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize performance timer

        Args:
            operation: Name of the operation to time
            metadata: Additional metadata to log
        """
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.duration_ms = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.time() - self.start_time) * 1000
        log_performance_metrics(self.operation, self.duration_ms, self.metadata)
        return False


# Example usage:
"""
from lambda.shared.cold_start_monitor import monitor_cold_start, PerformanceTimer

@monitor_cold_start
def lambda_handler(event, context):
    # Track specific operations
    with PerformanceTimer("database_query", {"table": "Devices"}):
        result = query_database()
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
"""
