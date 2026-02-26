"""
System Configuration Validation Module
Provides server-side validation for system configuration changes
"""

from typing import Dict, List, Tuple

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
