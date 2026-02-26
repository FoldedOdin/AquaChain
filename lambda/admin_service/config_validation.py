"""
System Configuration Validation Module
Provides server-side validation for system configuration changes
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger()

# Validation rules for system configuration
VALIDATION_RULES = {
    'dataRetentionDays': {'min': 30, 'max': 3650, 'type': 'int'},
    'auditRetentionYears': {'min': 1, 'max': 10, 'type': 'int'},
    'pH_min': {'min': 0, 'max': 14, 'type': 'float'},
    'pH_max': {'min': 0, 'max': 14, 'type': 'float'},
    'temperature_min': {'min': -10, 'max': 100, 'type': 'int'},
    'temperature_max': {'min': -10, 'max': 100, 'type': 'int'},
    'tds_max': {'min': 0, 'max': 5000, 'type': 'int'},
    'turbidity_max': {'min': 0, 'max': 100, 'type': 'float'},
    'wqi_critical': {'min': 0, 'max': 100, 'type': 'int'},
    'wqi_warning': {'min': 0, 'max': 100, 'type': 'int'},
    'maxDevicesPerUser': {'min': 1, 'max': 100, 'type': 'int'},
    'maxConcurrentDevices': {'min': 1, 'max': 100000, 'type': 'int'},
    'smsPerHour': {'min': 1, 'max': 1000, 'type': 'int'},
    'emailPerHour': {'min': 1, 'max': 10000, 'type': 'int'}
}


def validate_configuration(config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate system configuration against rules
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # Validate alert thresholds
        if 'alertThresholds' in config and 'global' in config['alertThresholds']:
            thresholds = config['alertThresholds']['global']
            
            # pH validation
            if 'pH' in thresholds:
                ph = thresholds['pH']
                if 'min' in ph:
                    errors.extend(_validate_field('pH_min', ph['min']))
                if 'max' in ph:
                    errors.extend(_validate_field('pH_max', ph['max']))
                if 'min' in ph and 'max' in ph and ph['min'] >= ph['max']:
                    errors.append('pH min must be less than pH max')
            
            # Temperature validation
            if 'temperature' in thresholds:
                temp = thresholds['temperature']
                if 'min' in temp:
                    errors.extend(_validate_field('temperature_min', temp['min']))
                if 'max' in temp:
                    errors.extend(_validate_field('temperature_max', temp['max']))
                if 'min' in temp and 'max' in temp and temp['min'] >= temp['max']:
                    errors.append('Temperature min must be less than temperature max')
            
            # TDS validation
            if 'tds' in thresholds and 'max' in thresholds['tds']:
                errors.extend(_validate_field('tds_max', thresholds['tds']['max']))
            
            # Turbidity validation
            if 'turbidity' in thresholds and 'max' in thresholds['turbidity']:
                errors.extend(_validate_field('turbidity_max', thresholds['turbidity']['max']))
            
            # WQI validation
            if 'wqi' in thresholds:
                wqi = thresholds['wqi']
                if 'critical' in wqi:
                    errors.extend(_validate_field('wqi_critical', wqi['critical']))
                if 'warning' in wqi:
                    errors.extend(_validate_field('wqi_warning', wqi['warning']))
                if 'critical' in wqi and 'warning' in wqi and wqi['critical'] >= wqi['warning']:
                    errors.append('WQI critical threshold must be less than warning threshold')
        
        # Validate system limits
        if 'systemLimits' in config:
            limits = config['systemLimits']
            
            if 'dataRetentionDays' in limits:
                errors.extend(_validate_field('dataRetentionDays', limits['dataRetentionDays']))
            
            if 'auditRetentionYears' in limits:
                errors.extend(_validate_field('auditRetentionYears', limits['auditRetentionYears']))
            
            if 'maxDevicesPerUser' in limits:
                errors.extend(_validate_field('maxDevicesPerUser', limits['maxDevicesPerUser']))
            
            if 'maxConcurrentDevices' in limits:
                errors.extend(_validate_field('maxConcurrentDevices', limits['maxConcurrentDevices']))
        
        # Validate notification settings
        if 'notificationSettings' in config and 'rateLimits' in config['notificationSettings']:
            rate_limits = config['notificationSettings']['rateLimits']
            
            if 'smsPerHour' in rate_limits:
                errors.extend(_validate_field('smsPerHour', rate_limits['smsPerHour']))
            
            if 'emailPerHour' in rate_limits:
                errors.extend(_validate_field('emailPerHour', rate_limits['emailPerHour']))
        
        # Validate notification channels
        if 'notificationSettings' in config and 'criticalAlertChannels' in config['notificationSettings']:
            channels = config['notificationSettings']['criticalAlertChannels']
            valid_channels = ['sms', 'email', 'push']
            for channel in channels:
                if channel not in valid_channels:
                    errors.append(f'Invalid notification channel: {channel}')
        
        return (len(errors) == 0, errors)
        
    except Exception as e:
        return (False, [f'Validation error: {str(e)}'])


def _validate_field(field_name: str, value: any) -> List[str]:
    """
    Validate a single field against its rules
    """
    errors = []
    
    if field_name not in VALIDATION_RULES:
        return errors
    
    rules = VALIDATION_RULES[field_name]
    
    # Type validation
    if rules['type'] == 'int':
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                errors.append(f'{field_name} must be an integer')
                return errors
    elif rules['type'] == 'float':
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                errors.append(f'{field_name} must be a number')
                return errors
    
    # Range validation
    if 'min' in rules and value < rules['min']:
        errors.append(f'{field_name} must be at least {rules["min"]}')
    
    if 'max' in rules and value > rules['max']:
        errors.append(f'{field_name} must be at most {rules["max"]}')
    
    return errors


def get_validation_rules() -> Dict:
    """
    Get validation rules for frontend display
    """
    return VALIDATION_RULES


def validate_severity_thresholds(thresholds: Dict) -> Tuple[bool, List[str]]:
    """
    Validate severity threshold relationships for Phase 3a.
    
    Rules:
    - For range parameters (pH, temp): warning_min < critical_min < critical_max < warning_max
    - For max-only parameters (turbidity, tds): critical_max < warning_max
    - All values must be within valid ranges for their respective parameters
    
    Args:
        thresholds: Dictionary containing threshold configuration
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # pH validation
    if 'pH' in thresholds:
        ph = thresholds['pH']
        if 'critical' in ph and 'warning' in ph:
            try:
                c_min = ph['critical'].get('min')
                c_max = ph['critical'].get('max')
                w_min = ph['warning'].get('min')
                w_max = ph['warning'].get('max')
                
                # Check all values are present
                if None in [c_min, c_max, w_min, w_max]:
                    errors.append('pH severity thresholds must include all min/max values for both warning and critical')
                else:
                    # Validate relationship: warning_min < critical_min < critical_max < warning_max
                    if not (w_min < c_min < c_max < w_max):
                        errors.append(
                            f'pH thresholds must satisfy: warning_min ({w_min}) < '
                            f'critical_min ({c_min}) < critical_max ({c_max}) < '
                            f'warning_max ({w_max})'
                        )
                    
                    # Validate ranges
                    if w_min < 0 or w_max > 14:
                        errors.append(f'pH warning thresholds must be between 0 and 14 (got min={w_min}, max={w_max})')
                    if c_min < 0 or c_max > 14:
                        errors.append(f'pH critical thresholds must be between 0 and 14 (got min={c_min}, max={c_max})')
            except (KeyError, TypeError) as e:
                errors.append(f'Invalid pH threshold structure: {str(e)}')
    
    # Turbidity validation
    if 'turbidity' in thresholds:
        turb = thresholds['turbidity']
        if 'critical' in turb and 'warning' in turb:
            try:
                c_max = turb['critical'].get('max')
                w_max = turb['warning'].get('max')
                
                if None in [c_max, w_max]:
                    errors.append('Turbidity severity thresholds must include max values for both warning and critical')
                else:
                    # Validate relationship: critical_max < warning_max
                    if c_max >= w_max:
                        errors.append(
                            f'Turbidity critical max ({c_max}) must be less than '
                            f'warning max ({w_max})'
                        )
                    
                    # Validate ranges
                    if c_max < 0 or c_max > 100:
                        errors.append(f'Turbidity critical max must be between 0 and 100 (got {c_max})')
                    if w_max < 0 or w_max > 100:
                        errors.append(f'Turbidity warning max must be between 0 and 100 (got {w_max})')
            except (KeyError, TypeError) as e:
                errors.append(f'Invalid turbidity threshold structure: {str(e)}')
    
    # TDS validation
    if 'tds' in thresholds:
        tds = thresholds['tds']
        if 'critical' in tds and 'warning' in tds:
            try:
                c_max = tds['critical'].get('max')
                w_max = tds['warning'].get('max')
                
                if None in [c_max, w_max]:
                    errors.append('TDS severity thresholds must include max values for both warning and critical')
                else:
                    # Validate relationship: critical_max < warning_max
                    if c_max >= w_max:
                        errors.append(
                            f'TDS critical max ({c_max}) must be less than '
                            f'warning max ({w_max})'
                        )
                    
                    # Validate ranges
                    if c_max < 0 or c_max > 5000:
                        errors.append(f'TDS critical max must be between 0 and 5000 (got {c_max})')
                    if w_max < 0 or w_max > 5000:
                        errors.append(f'TDS warning max must be between 0 and 5000 (got {w_max})')
            except (KeyError, TypeError) as e:
                errors.append(f'Invalid TDS threshold structure: {str(e)}')
    
    # Temperature validation
    if 'temperature' in thresholds:
        temp = thresholds['temperature']
        if 'critical' in temp and 'warning' in temp:
            try:
                c_min = temp['critical'].get('min')
                c_max = temp['critical'].get('max')
                w_min = temp['warning'].get('min')
                w_max = temp['warning'].get('max')
                
                # Check all values are present
                if None in [c_min, c_max, w_min, w_max]:
                    errors.append('Temperature severity thresholds must include all min/max values for both warning and critical')
                else:
                    # Validate relationship: warning_min < critical_min < critical_max < warning_max
                    if not (w_min < c_min < c_max < w_max):
                        errors.append(
                            f'Temperature thresholds must satisfy: warning_min ({w_min}) < '
                            f'critical_min ({c_min}) < critical_max ({c_max}) < '
                            f'warning_max ({w_max})'
                        )
                    
                    # Validate ranges
                    if w_min < -10 or w_max > 100:
                        errors.append(f'Temperature warning thresholds must be between -10 and 100 (got min={w_min}, max={w_max})')
                    if c_min < -10 or c_max > 100:
                        errors.append(f'Temperature critical thresholds must be between -10 and 100 (got min={c_min}, max={c_max})')
            except (KeyError, TypeError) as e:
                errors.append(f'Invalid temperature threshold structure: {str(e)}')
    
    return (len(errors) == 0, errors)


def validate_notification_channels(notification_settings: Dict) -> Tuple[bool, List[str]]:
    """
    Validate notification channel configuration for Phase 3a.
    
    Rules:
    - At least one critical alert channel must be enabled
    - Warning channels cannot include SMS (SMS reserved for critical only)
    
    Args:
        notification_settings: Dictionary containing notification configuration
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Get channel lists (default to empty if not present for backward compatibility)
    critical_channels = notification_settings.get('criticalAlertChannels', [])
    warning_channels = notification_settings.get('warningAlertChannels', [])
    
    # Validate critical channels - at least one must be enabled
    if not critical_channels or len(critical_channels) == 0:
        errors.append('At least one critical alert channel must be enabled')
    
    # Validate channel values are valid
    valid_channels = ['sms', 'email', 'push']
    for channel in critical_channels:
        if channel not in valid_channels:
            errors.append(f'Invalid critical alert channel: {channel}. Valid options: {", ".join(valid_channels)}')
    
    # Validate warning channels - SMS not allowed
    if 'sms' in warning_channels:
        errors.append('SMS notifications are not allowed for warning alerts (SMS is reserved for critical alerts only)')
    
    # Validate warning channel values are valid
    for channel in warning_channels:
        if channel not in valid_channels:
            errors.append(f'Invalid warning alert channel: {channel}. Valid options: {", ".join(valid_channels)}')
    
    return (len(errors) == 0, errors)


def normalize_threshold_format(config: Dict) -> Dict:
    """
    Convert legacy single-threshold format to severity format for Phase 3a backward compatibility.
    
    This function automatically migrates configurations from the legacy format:
        { "min": 6.5, "max": 8.5 }
    To the new severity format:
        { "critical": { "min": 6.5, "max": 8.5 }, "warning": { "min": 7.0, "max": 8.0 } }
    
    Migration rules:
    - Legacy thresholds become critical thresholds
    - Warning thresholds are auto-generated:
      - For pH/temperature: warning_min = critical_min + 0.5, warning_max = critical_max - 0.5
      - For turbidity/TDS: warning_max = critical_max * 0.8
    - Configs that already have severity levels are not modified (idempotent)
    
    Args:
        config: System configuration dictionary
    
    Returns:
        Modified configuration dictionary with normalized threshold format
    """
    # Check if alertThresholds exist
    if 'alertThresholds' not in config or 'global' not in config['alertThresholds']:
        return config
    
    thresholds = config['alertThresholds']['global']
    migration_performed = False
    
    # pH migration (range parameter)
    if 'pH' in thresholds:
        ph = thresholds['pH']
        # Check if legacy format (has min/max but no critical/warning)
        if 'min' in ph and 'max' in ph and 'critical' not in ph and 'warning' not in ph:
            legacy_min = ph['min']
            legacy_max = ph['max']
            
            # Convert to severity format
            thresholds['pH'] = {
                'critical': {
                    'min': legacy_min,
                    'max': legacy_max
                },
                'warning': {
                    'min': legacy_min + 0.5,
                    'max': legacy_max - 0.5
                }
            }
            
            logger.info(f'Migrated pH thresholds from legacy format: '
                       f'critical=({legacy_min}, {legacy_max}), '
                       f'warning=({legacy_min + 0.5}, {legacy_max - 0.5})')
            migration_performed = True
    
    # Temperature migration (range parameter)
    if 'temperature' in thresholds:
        temp = thresholds['temperature']
        # Check if legacy format
        if 'min' in temp and 'max' in temp and 'critical' not in temp and 'warning' not in temp:
            legacy_min = temp['min']
            legacy_max = temp['max']
            
            # Convert to severity format
            thresholds['temperature'] = {
                'critical': {
                    'min': legacy_min,
                    'max': legacy_max
                },
                'warning': {
                    'min': legacy_min + 0.5,
                    'max': legacy_max - 0.5
                }
            }
            
            logger.info(f'Migrated temperature thresholds from legacy format: '
                       f'critical=({legacy_min}, {legacy_max}), '
                       f'warning=({legacy_min + 0.5}, {legacy_max - 0.5})')
            migration_performed = True
    
    # Turbidity migration (max-only parameter)
    if 'turbidity' in thresholds:
        turb = thresholds['turbidity']
        # Check if legacy format (has max but no critical/warning)
        if 'max' in turb and 'critical' not in turb and 'warning' not in turb:
            legacy_max = turb['max']
            
            # Convert to severity format
            thresholds['turbidity'] = {
                'critical': {
                    'max': legacy_max
                },
                'warning': {
                    'max': legacy_max * 0.8
                }
            }
            
            logger.info(f'Migrated turbidity thresholds from legacy format: '
                       f'critical={legacy_max}, warning={legacy_max * 0.8}')
            migration_performed = True
    
    # TDS migration (max-only parameter)
    if 'tds' in thresholds:
        tds = thresholds['tds']
        # Check if legacy format (has max but no critical/warning)
        if 'max' in tds and 'critical' not in tds and 'warning' not in tds:
            legacy_max = tds['max']
            
            # Convert to severity format
            thresholds['tds'] = {
                'critical': {
                    'max': legacy_max
                },
                'warning': {
                    'max': legacy_max * 0.8
                }
            }
            
            logger.info(f'Migrated TDS thresholds from legacy format: '
                       f'critical={legacy_max}, warning={legacy_max * 0.8}')
            migration_performed = True
    
    if migration_performed:
        logger.info('Legacy threshold format migration completed successfully')
    
    return config
