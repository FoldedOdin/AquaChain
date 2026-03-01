"""
Health Check Service for Dashboard Services
Provides comprehensive health checks with dependency status monitoring
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import uuid

logger = logging.getLogger(__name__)

class HealthCheckService:
    """
    Comprehensive health check service for dashboard Lambda functions
    """
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        """
        Initialize health check service
        
        Args:
            service_name: Name of the service being monitored
            version: Service version
        """
        self.service_name = service_name
        self.version = version
        self.start_time = datetime.utcnow()
        
        # AWS clients for dependency checks
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.sns = boto3.client('sns')
        self.lambda_client = boto3.client('lambda')
        self.secretsmanager = boto3.client('secretsmanager')
        
        # Health check configuration
        self.timeout_seconds = 5
        self.critical_dependencies = []
        self.optional_dependencies = []
        self.custom_checks = []
        
        logger.info(f"Health check service initialized for {service_name}")
    
    def add_critical_dependency(self, name: str, check_function: Callable[[], Dict[str, Any]]) -> None:
        """
        Add a critical dependency check
        
        Args:
            name: Dependency name
            check_function: Function that returns health status dict
        """
        self.critical_dependencies.append({
            'name': name,
            'check': check_function
        })
    
    def add_optional_dependency(self, name: str, check_function: Callable[[], Dict[str, Any]]) -> None:
        """
        Add an optional dependency check
        
        Args:
            name: Dependency name
            check_function: Function that returns health status dict
        """
        self.optional_dependencies.append({
            'name': name,
            'check': check_function
        })
    
    def add_custom_check(self, name: str, check_function: Callable[[], Dict[str, Any]]) -> None:
        """
        Add a custom health check
        
        Args:
            name: Check name
            check_function: Function that returns health status dict
        """
        self.custom_checks.append({
            'name': name,
            'check': check_function
        })
    
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            Health check results with overall status and dependency details
        """
        health_result = {
            'service': self.service_name,
            'version': self.version,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': int((datetime.utcnow() - self.start_time).total_seconds()),
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'critical_failures': 0
            }
        }
        
        try:
            # Perform basic service health check
            basic_check = self._perform_basic_health_check()
            health_result['checks']['basic'] = basic_check
            health_result['summary']['total_checks'] += 1
            
            if basic_check['status'] == 'healthy':
                health_result['summary']['passed_checks'] += 1
            else:
                health_result['summary']['failed_checks'] += 1
                health_result['status'] = 'degraded'
            
            # Check critical dependencies
            for dependency in self.critical_dependencies:
                try:
                    check_result = self._execute_check_with_timeout(dependency['check'])
                    health_result['checks'][f"critical_{dependency['name']}"] = check_result
                    health_result['summary']['total_checks'] += 1
                    
                    if check_result['status'] == 'healthy':
                        health_result['summary']['passed_checks'] += 1
                    else:
                        health_result['summary']['failed_checks'] += 1
                        health_result['summary']['critical_failures'] += 1
                        health_result['status'] = 'unhealthy'
                        
                except Exception as e:
                    error_result = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    health_result['checks'][f"critical_{dependency['name']}"] = error_result
                    health_result['summary']['total_checks'] += 1
                    health_result['summary']['failed_checks'] += 1
                    health_result['summary']['critical_failures'] += 1
                    health_result['status'] = 'unhealthy'
            
            # Check optional dependencies
            for dependency in self.optional_dependencies:
                try:
                    check_result = self._execute_check_with_timeout(dependency['check'])
                    health_result['checks'][f"optional_{dependency['name']}"] = check_result
                    health_result['summary']['total_checks'] += 1
                    
                    if check_result['status'] == 'healthy':
                        health_result['summary']['passed_checks'] += 1
                    else:
                        health_result['summary']['failed_checks'] += 1
                        # Optional dependency failures only degrade service if currently healthy
                        if health_result['status'] == 'healthy':
                            health_result['status'] = 'degraded'
                            
                except Exception as e:
                    error_result = {
                        'status': 'degraded',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    health_result['checks'][f"optional_{dependency['name']}"] = error_result
                    health_result['summary']['total_checks'] += 1
                    health_result['summary']['failed_checks'] += 1
                    if health_result['status'] == 'healthy':
                        health_result['status'] = 'degraded'
            
            # Perform custom checks
            for custom_check in self.custom_checks:
                try:
                    check_result = self._execute_check_with_timeout(custom_check['check'])
                    health_result['checks'][f"custom_{custom_check['name']}"] = check_result
                    health_result['summary']['total_checks'] += 1
                    
                    if check_result['status'] == 'healthy':
                        health_result['summary']['passed_checks'] += 1
                    else:
                        health_result['summary']['failed_checks'] += 1
                        if health_result['status'] == 'healthy':
                            health_result['status'] = 'degraded'
                            
                except Exception as e:
                    error_result = {
                        'status': 'degraded',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    health_result['checks'][f"custom_{custom_check['name']}"] = error_result
                    health_result['summary']['total_checks'] += 1
                    health_result['summary']['failed_checks'] += 1
                    if health_result['status'] == 'healthy':
                        health_result['status'] = 'degraded'
            
            # Calculate health score
            if health_result['summary']['total_checks'] > 0:
                health_result['health_score'] = (
                    health_result['summary']['passed_checks'] / 
                    health_result['summary']['total_checks']
                ) * 100
            else:
                health_result['health_score'] = 100
            
            logger.info(
                f"Health check completed for {self.service_name}",
                extra={
                    'status': health_result['status'],
                    'health_score': health_result['health_score'],
                    'total_checks': health_result['summary']['total_checks']
                }
            )
            
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed for {self.service_name}: {str(e)}")
            return {
                'service': self.service_name,
                'version': self.version,
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'health_score': 0
            }
    
    def _perform_basic_health_check(self) -> Dict[str, Any]:
        """
        Perform basic service health check
        
        Returns:
            Basic health status
        """
        try:
            # Check memory usage
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            # Check disk usage (if applicable)
            disk_percent = psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
            
            # Determine status based on resource usage
            status = 'healthy'
            warnings = []
            
            if memory_percent > 90:
                status = 'degraded'
                warnings.append(f"High memory usage: {memory_percent}%")
            elif memory_percent > 80:
                warnings.append(f"Elevated memory usage: {memory_percent}%")
            
            if disk_percent > 90:
                status = 'degraded'
                warnings.append(f"High disk usage: {disk_percent}%")
            
            return {
                'status': status,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'warnings': warnings,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ImportError:
            # psutil not available, return basic status
            return {
                'status': 'healthy',
                'message': 'Basic health check (psutil not available)',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _execute_check_with_timeout(self, check_function: Callable) -> Dict[str, Any]:
        """
        Execute health check function with timeout
        
        Args:
            check_function: Function to execute
            
        Returns:
            Check result with timeout handling
        """
        import threading
        import time
        
        result_container = {'result': None, 'exception': None, 'timed_out': False}
        
        def run_check():
            try:
                result_container['result'] = check_function()
            except Exception as e:
                result_container['exception'] = e
        
        # Start check in separate thread
        thread = threading.Thread(target=run_check)
        thread.daemon = True
        thread.start()
        
        # Wait for completion or timeout
        thread.join(timeout=self.timeout_seconds)
        
        if thread.is_alive():
            # Thread is still running, it timed out
            result_container['timed_out'] = True
            return {
                'status': 'degraded',
                'error': f'Check timed out after {self.timeout_seconds} seconds',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Check if there was an exception
        if result_container['exception']:
            return {
                'status': 'unhealthy',
                'error': str(result_container['exception']),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Return the result
        return result_container['result'] or {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Pre-built dependency check functions
    
    def check_dynamodb_table(self, table_name: str) -> Dict[str, Any]:
        """
        Check DynamoDB table health
        
        Args:
            table_name: DynamoDB table name
            
        Returns:
            Table health status
        """
        try:
            table = self.dynamodb.Table(table_name)
            
            # Check table status
            table_status = table.table_status
            
            # Perform a simple query to test connectivity
            response = table.scan(Limit=1)
            
            return {
                'status': 'healthy' if table_status == 'ACTIVE' else 'degraded',
                'table_status': table_status,
                'item_count': table.item_count,
                'table_size_bytes': table.table_size_bytes,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """
        Check S3 bucket health
        
        Args:
            bucket_name: S3 bucket name
            
        Returns:
            Bucket health status
        """
        try:
            # Check bucket exists and is accessible
            self.s3.head_bucket(Bucket=bucket_name)
            
            # List objects to test permissions
            response = self.s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            
            return {
                'status': 'healthy',
                'bucket_exists': True,
                'accessible': True,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                status = 'unhealthy'
                message = 'Bucket not found'
            elif error_code == '403':
                status = 'degraded'
                message = 'Access denied'
            else:
                status = 'unhealthy'
                message = f'S3 error: {error_code}'
            
            return {
                'status': status,
                'error': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_lambda_function(self, function_name: str) -> Dict[str, Any]:
        """
        Check Lambda function health
        
        Args:
            function_name: Lambda function name
            
        Returns:
            Function health status
        """
        try:
            # Get function configuration
            response = self.lambda_client.get_function(FunctionName=function_name)
            
            config = response['Configuration']
            state = config.get('State', 'Unknown')
            
            return {
                'status': 'healthy' if state == 'Active' else 'degraded',
                'function_state': state,
                'runtime': config.get('Runtime'),
                'last_modified': config.get('LastModified'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_secrets_manager_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Check Secrets Manager secret health
        
        Args:
            secret_name: Secret name or ARN
            
        Returns:
            Secret health status
        """
        try:
            # Describe secret (doesn't retrieve actual secret value)
            response = self.secretsmanager.describe_secret(SecretId=secret_name)
            
            return {
                'status': 'healthy',
                'secret_exists': True,
                'last_changed_date': response.get('LastChangedDate', '').isoformat() if response.get('LastChangedDate') else None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_cache_service(self, cache_service) -> Dict[str, Any]:
        """
        Check cache service health
        
        Args:
            cache_service: Cache service instance
            
        Returns:
            Cache health status
        """
        try:
            if hasattr(cache_service, 'health_check'):
                return cache_service.health_check()
            else:
                # Basic cache test
                test_key = f"health_check_{uuid.uuid4()}"
                cache_service.set(test_key, "test_value", 10)
                value = cache_service.get(test_key)
                cache_service.delete(test_key)
                
                return {
                    'status': 'healthy' if value == "test_value" else 'degraded',
                    'cache_test_passed': value == "test_value",
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Convenience function for creating health check endpoints
def create_health_check_handler(service_name: str, version: str = "1.0.0") -> Callable:
    """
    Create a health check handler function for Lambda
    
    Args:
        service_name: Name of the service
        version: Service version
        
    Returns:
        Lambda handler function for health checks
    """
    health_service = HealthCheckService(service_name, version)
    
    def health_check_handler(event, context):
        """
        Lambda handler for health check endpoint
        """
        try:
            # Perform health check
            health_result = health_service.perform_health_check()
            
            # Determine HTTP status code based on health status
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
            logger.error(f"Health check handler error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'service': service_name,
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
    
    return health_check_handler

# Global health check service instance
_health_services = {}

def get_health_service(service_name: str, version: str = "1.0.0") -> HealthCheckService:
    """
    Get or create health check service instance (singleton per service)
    
    Args:
        service_name: Name of the service
        version: Service version
        
    Returns:
        HealthCheckService instance
    """
    key = f"{service_name}:{version}"
    
    if key not in _health_services:
        _health_services[key] = HealthCheckService(service_name, version)
    
    return _health_services[key]