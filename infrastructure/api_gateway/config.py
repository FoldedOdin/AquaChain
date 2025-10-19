"""
API Gateway configuration constants and utilities
"""
from typing import Dict, Any, List


class APIGatewayConfig:
    """Configuration constants for API Gateway setup"""
    
    # API Gateway settings
    API_NAME = 'aquachain-api'
    API_DESCRIPTION = 'AquaChain Water Quality Monitoring API'
    API_VERSION = 'v1'
    STAGE_NAME = 'prod'
    
    # Rate limiting settings
    RATE_LIMIT = 1000  # requests per minute per IP
    BURST_LIMIT = 2000  # burst capacity
    
    # CORS settings
    CORS_ORIGINS = ['*']  # In production, specify actual domains
    CORS_HEADERS = [
        'Content-Type',
        'X-Amz-Date',
        'Authorization',
        'X-Api-Key',
        'X-Amz-Security-Token'
    ]
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # WAF settings
    WAF_NAME = 'aquachain-api-waf'
    WAF_RATE_LIMIT = 1000  # requests per 5-minute window per IP
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    METRICS_ENABLED = True
    DATA_TRACE_ENABLED = True
    
    @staticmethod
    def get_api_resources() -> Dict[str, Dict[str, Any]]:
        """Get API resource structure configuration"""
        return {
            'readings': {
                'methods': ['GET', 'POST'],
                'auth_required': True,
                'rate_limit': 500,
                'description': 'Water quality readings endpoints'
            },
            'users': {
                'methods': ['GET', 'POST', 'PUT', 'DELETE'],
                'auth_required': True,
                'rate_limit': 100,
                'description': 'User management endpoints'
            },
            'service-requests': {
                'methods': ['GET', 'POST', 'PUT'],
                'auth_required': True,
                'rate_limit': 200,
                'description': 'Service request management endpoints'
            },
            'technicians': {
                'methods': ['GET', 'PUT'],
                'auth_required': True,
                'rate_limit': 100,
                'description': 'Technician management endpoints'
            },
            'audit': {
                'methods': ['GET'],
                'auth_required': True,
                'rate_limit': 50,
                'description': 'Audit trail and compliance endpoints'
            },
            'analytics': {
                'methods': ['GET'],
                'auth_required': True,
                'rate_limit': 100,
                'description': 'Analytics and reporting endpoints'
            }
        }
    
    @staticmethod
    def get_waf_rules() -> List[Dict[str, Any]]:
        """Get WAF rule configurations"""
        return [
            {
                'name': 'RateLimitRule',
                'priority': 1,
                'type': 'rate_based',
                'limit': APIGatewayConfig.WAF_RATE_LIMIT,
                'action': 'block'
            },
            {
                'name': 'IPReputationRule',
                'priority': 2,
                'type': 'managed_rule_group',
                'vendor': 'AWS',
                'rule_group': 'AWSManagedRulesAmazonIpReputationList',
                'action': 'block'
            },
            {
                'name': 'CommonRuleSetRule',
                'priority': 3,
                'type': 'managed_rule_group',
                'vendor': 'AWS',
                'rule_group': 'AWSManagedRulesCommonRuleSet',
                'action': 'block'
            },
            {
                'name': 'SQLInjectionRule',
                'priority': 4,
                'type': 'managed_rule_group',
                'vendor': 'AWS',
                'rule_group': 'AWSManagedRulesSQLiRuleSet',
                'action': 'block'
            }
        ]
    
    @staticmethod
    def get_request_templates() -> Dict[str, str]:
        """Get API Gateway request templates"""
        return {
            'application/json': '''
            {
                "body": $input.json('$'),
                "headers": {
                    #foreach($header in $input.params().header.keySet())
                    "$header": "$util.escapeJavaScript($input.params().header.get($header))"
                    #if($foreach.hasNext),#end
                    #end
                },
                "pathParameters": {
                    #foreach($param in $input.params().path.keySet())
                    "$param": "$util.escapeJavaScript($input.params().path.get($param))"
                    #if($foreach.hasNext),#end
                    #end
                },
                "queryStringParameters": {
                    #foreach($queryParam in $input.params().querystring.keySet())
                    "$queryParam": "$util.escapeJavaScript($input.params().querystring.get($queryParam))"
                    #if($foreach.hasNext),#end
                    #end
                },
                "requestContext": {
                    "requestId": "$context.requestId",
                    "httpMethod": "$context.httpMethod",
                    "resourcePath": "$context.resourcePath",
                    "identity": {
                        "sourceIp": "$context.identity.sourceIp",
                        "userAgent": "$context.identity.userAgent"
                    },
                    "authorizer": {
                        "claims": {
                            "sub": "$context.authorizer.claims.sub",
                            "email": "$context.authorizer.claims.email",
                            "cognito:groups": "$context.authorizer.claims['cognito:groups']"
                        }
                    }
                }
            }
            '''
        }
    
    @staticmethod
    def get_response_templates() -> Dict[str, str]:
        """Get API Gateway response templates"""
        return {
            'application/json': '''
            #set($inputRoot = $input.path('$'))
            {
                "statusCode": $inputRoot.statusCode,
                "body": $inputRoot.body,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
                }
            }
            '''
        }
    
    @staticmethod
    def get_error_responses() -> Dict[str, Dict[str, Any]]:
        """Get standard error response configurations"""
        return {
            '400': {
                'statusCode': '400',
                'responseTemplates': {
                    'application/json': '''
                    {
                        "error": "Bad Request",
                        "message": "Invalid request parameters",
                        "timestamp": "$context.requestTime",
                        "requestId": "$context.requestId"
                    }
                    '''
                }
            },
            '401': {
                'statusCode': '401',
                'responseTemplates': {
                    'application/json': '''
                    {
                        "error": "Unauthorized",
                        "message": "Authentication required",
                        "timestamp": "$context.requestTime",
                        "requestId": "$context.requestId"
                    }
                    '''
                }
            },
            '403': {
                'statusCode': '403',
                'responseTemplates': {
                    'application/json': '''
                    {
                        "error": "Forbidden",
                        "message": "Insufficient permissions",
                        "timestamp": "$context.requestTime",
                        "requestId": "$context.requestId"
                    }
                    '''
                }
            },
            '429': {
                'statusCode': '429',
                'responseTemplates': {
                    'application/json': '''
                    {
                        "error": "Too Many Requests",
                        "message": "Rate limit exceeded",
                        "timestamp": "$context.requestTime",
                        "requestId": "$context.requestId"
                    }
                    '''
                }
            },
            '500': {
                'statusCode': '500',
                'responseTemplates': {
                    'application/json': '''
                    {
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred",
                        "timestamp": "$context.requestTime",
                        "requestId": "$context.requestId"
                    }
                    '''
                }
            }
        }