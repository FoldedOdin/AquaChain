"""
Generic Health Check Endpoint Handler
Provides a standardized health check endpoint for all Lambda services
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from health_check_service import get_health_service

def create_health_endpoint(service_name: str, version: str = "1.0.0", 
                          dependencies: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized health check response for a Lambda service
    
    Args:
        service_name: Name of the service
        version: Service version
        dependencies: Dictionary of dependency check functions
        
    Returns:
        Health check response
    """
    try:
        health_service = get_health_service(service_name, version)
        
        # Add common dependencies if provided
        if dependencies:
            for dep_name, dep_config in dependencies.items():
                dep_type = dep_config.get('type', 'optional')
                check_func = dep_config.get('check_function')
                
                if check_func:
                    if dep_type == 'critical':
                        health_service.add_critical_dependency(dep_name, check_func)
                    elif dep_type == 'optional':
                        health_service.add_optional_dependency(dep_name, check_func)
                    else:
                        health_service.add_custom_check(dep_name, check_func)
        
        # Perform health check
        health_result = health_service.perform_health_check()
        
        # Determine HTTP status code
        if health_result['status'] == 'healthy':
            status_code = 200
        elif health_result['status'] == 'degraded':
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            },
            'body': json.dumps(health_result, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'service': service_name,
                'version': version,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def add_health_route_to_handler(handler_func, service_name: str, version: str = "1.0.0",
                               dependencies: Optional[Dict[str, Any]] = None):
    """
    Decorator to add health check route to existing Lambda handler
    
    Args:
        handler_func: Original Lambda handler function
        service_name: Name of the service
        version: Service version
        dependencies: Dictionary of dependency check functions
        
    Returns:
        Enhanced handler with health check route
    """
    def enhanced_handler(event, context):
        # Check if this is a health check request
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'GET' and path.endswith('/health'):
            return create_health_endpoint(service_name, version, dependencies)
        
        # Otherwise, call the original handler
        return handler_func(event, context)
    
    return enhanced_handler

# Common dependency check functions
def create_dynamodb_check(table_name: str):
    """Create a DynamoDB table health check function"""
    def check_dynamodb():
        health_service = get_health_service('temp', '1.0.0')
        return health_service.check_dynamodb_table(table_name)
    return check_dynamodb

def create_s3_check(bucket_name: str):
    """Create an S3 bucket health check function"""
    def check_s3():
        health_service = get_health_service('temp', '1.0.0')
        return health_service.check_s3_bucket(bucket_name)
    return check_s3

def create_lambda_check(function_name: str):
    """Create a Lambda function health check function"""
    def check_lambda():
        health_service = get_health_service('temp', '1.0.0')
        return health_service.check_lambda_function(function_name)
    return check_lambda

def create_secrets_check(secret_name: str):
    """Create a Secrets Manager secret health check function"""
    def check_secret():
        health_service = get_health_service('temp', '1.0.0')
        return health_service.check_secrets_manager_secret(secret_name)
    return check_secret

# Example usage for different services
def get_rbac_service_dependencies() -> Dict[str, Any]:
    """Get health check dependencies for RBAC service"""
    return {
        'cognito_user_pool': {
            'type': 'critical',
            'check_function': lambda: {
                'status': 'healthy',
                'user_pool_id': os.environ.get('USER_POOL_ID', 'not_configured'),
                'timestamp': datetime.utcnow().isoformat()
            }
        },
        'users_table': {
            'type': 'critical',
            'check_function': create_dynamodb_check(os.environ.get('USERS_TABLE', 'dashboard-users'))
        }
    }

def get_audit_service_dependencies() -> Dict[str, Any]:
    """Get health check dependencies for audit service"""
    return {
        'audit_table': {
            'type': 'critical',
            'check_function': create_dynamodb_check(os.environ.get('AUDIT_TABLE', 'dashboard-audit'))
        },
        'audit_bucket': {
            'type': 'critical',
            'check_function': create_s3_check(os.environ.get('AUDIT_BUCKET', 'dashboard-audit-logs'))
        },
        'kms_key': {
            'type': 'critical',
            'check_function': lambda: {
                'status': 'healthy',
                'kms_key_id': os.environ.get('KMS_KEY_ID', 'not_configured'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    }

def get_procurement_service_dependencies() -> Dict[str, Any]:
    """Get health check dependencies for procurement service"""
    return {
        'purchase_orders_table': {
            'type': 'critical',
            'check_function': create_dynamodb_check(os.environ.get('PURCHASE_ORDERS_TABLE', 'purchase-orders'))
        },
        'budget_table': {
            'type': 'critical',
            'check_function': create_dynamodb_check(os.environ.get('BUDGET_TABLE', 'budget'))
        },
        'workflow_service': {
            'type': 'optional',
            'check_function': create_lambda_check(os.environ.get('WORKFLOW_SERVICE', 'workflow-service'))
        }
    }

def get_budget_service_dependencies() -> Dict[str, Any]:
    """Get health check dependencies for budget service"""
    return {
        'budget_table': {
            'type': 'critical',
            'check_function': create_dynamodb_check(os.environ.get('BUDGET_TABLE', 'budget'))
        },
        'ml_forecast_service': {
            'type': 'optional',
            'check_function': create_lambda_check(os.environ.get('ML_FORECAST_SERVICE', 'ml-forecast-service'))
        }
    }

def get_workflow_service_dependencies() -> Dict[str, Any]:
    """Get health check dependencies for workflow service"""
    return {
        'workflows_table': {
            'type': 'critical',
            'check_function': create_dynamodb_check(os.environ.get('WORKFLOWS_TABLE', 'workflows'))
        },
        'notification_service': {
            'type': 'optional',
            'check_function': lambda: {
                'status': 'healthy',
                'sns_topic': os.environ.get('NOTIFICATION_TOPIC', 'not_configured'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    }