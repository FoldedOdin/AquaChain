"""
IoT Job Document Templates
Templates for different types of IoT jobs
"""

from typing import Dict, Any


def create_firmware_update_job_document(
    firmware_version: str,
    firmware_url: str,
    firmware_size: int,
    checksum: str,
    checksum_algorithm: str = 'SHA256'
) -> Dict[str, Any]:
    """
    Create job document for firmware update
    
    Args:
        firmware_version: Target firmware version
        firmware_url: Presigned S3 URL for firmware download
        firmware_size: Size of firmware in bytes
        checksum: Firmware checksum
        checksum_algorithm: Algorithm used for checksum
    
    Returns:
        Job document dictionary
    """
    return {
        'operation': 'firmware_update',
        'firmware_version': firmware_version,
        'firmware_url': firmware_url,
        'firmware_size': firmware_size,
        'checksum': checksum,
        'checksum_algorithm': checksum_algorithm,
        'instructions': {
            'steps': [
                'Download firmware from provided URL',
                'Verify checksum matches',
                'Apply firmware update',
                'Reboot device',
                'Report update status'
            ]
        },
        'timeout_minutes': 30,
        'retry_policy': {
            'max_retries': 3,
            'retry_delay_seconds': 60
        }
    }


def create_rollback_job_document(
    firmware_version: str,
    firmware_url: str,
    firmware_size: int,
    checksum: str,
    reason: str = 'manual_rollback'
) -> Dict[str, Any]:
    """
    Create job document for firmware rollback
    
    Args:
        firmware_version: Target firmware version to rollback to
        firmware_url: Presigned S3 URL for firmware download
        firmware_size: Size of firmware in bytes
        checksum: Firmware checksum
        reason: Reason for rollback
    
    Returns:
        Job document dictionary
    """
    return {
        'operation': 'firmware_rollback',
        'firmware_version': firmware_version,
        'firmware_url': firmware_url,
        'firmware_size': firmware_size,
        'checksum': checksum,
        'checksum_algorithm': 'SHA256',
        'reason': reason,
        'instructions': {
            'steps': [
                'Download previous firmware version',
                'Verify checksum matches',
                'Apply firmware rollback',
                'Reboot device',
                'Report rollback status'
            ]
        },
        'timeout_minutes': 15,
        'priority': 'high'
    }


def create_gradual_rollout_config(
    stage: str = 'initial'
) -> Dict[str, Any]:
    """
    Create rollout configuration for gradual deployment
    
    Args:
        stage: Rollout stage (initial, medium, full)
    
    Returns:
        Rollout configuration
    """
    configs = {
        'initial': {
            'maximumPerMinute': 5,
            'exponentialRate': {
                'baseRatePerMinute': 2,
                'incrementFactor': 1.5,
                'rateIncreaseCriteria': {
                    'numberOfNotifiedThings': 5,
                    'numberOfSucceededThings': 4
                }
            }
        },
        'medium': {
            'maximumPerMinute': 20,
            'exponentialRate': {
                'baseRatePerMinute': 10,
                'incrementFactor': 2,
                'rateIncreaseCriteria': {
                    'numberOfNotifiedThings': 20,
                    'numberOfSucceededThings': 15
                }
            }
        },
        'full': {
            'maximumPerMinute': 100,
            'exponentialRate': {
                'baseRatePerMinute': 50,
                'incrementFactor': 2,
                'rateIncreaseCriteria': {
                    'numberOfNotifiedThings': 50,
                    'numberOfSucceededThings': 40
                }
            }
        }
    }
    
    return configs.get(stage, configs['initial'])


def create_abort_config(
    failure_threshold: float = 20.0,
    timeout_threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Create abort configuration for job safety
    
    Args:
        failure_threshold: Percentage of failures to trigger abort
        timeout_threshold: Percentage of timeouts to trigger abort
    
    Returns:
        Abort configuration
    """
    return {
        'criteriaList': [
            {
                'failureType': 'FAILED',
                'action': 'CANCEL',
                'thresholdPercentage': failure_threshold,
                'minNumberOfExecutedThings': 5
            },
            {
                'failureType': 'TIMED_OUT',
                'action': 'CANCEL',
                'thresholdPercentage': timeout_threshold,
                'minNumberOfExecutedThings': 5
            },
            {
                'failureType': 'REJECTED',
                'action': 'CANCEL',
                'thresholdPercentage': 15.0,
                'minNumberOfExecutedThings': 3
            }
        ]
    }


def create_timeout_config(
    in_progress_timeout: int = 30
) -> Dict[str, Any]:
    """
    Create timeout configuration for job execution
    
    Args:
        in_progress_timeout: Timeout in minutes for in-progress jobs
    
    Returns:
        Timeout configuration
    """
    return {
        'inProgressTimeoutInMinutes': in_progress_timeout
    }


def create_job_execution_status_details(
    status: str,
    status_details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create job execution status details
    
    Args:
        status: Execution status (QUEUED, IN_PROGRESS, SUCCEEDED, FAILED, etc.)
        status_details: Additional status details
    
    Returns:
        Status details dictionary
    """
    details = {
        'status': status,
        'timestamp': None  # Will be set by device
    }
    
    if status_details:
        details.update(status_details)
    
    return details
