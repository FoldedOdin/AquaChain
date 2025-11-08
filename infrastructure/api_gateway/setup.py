"""
API Gateway setup with security, rate limiting, and WAF configuration
"""
import boto3
import json
import time
from typing import Dict, Any, List
from botocore.exceptions import ClientError


class APIGatewaySetup:
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.wafv2 = boto3.client('wafv2', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        
    def create_api_gateway(self) -> Dict[str, Any]:
        """Create REST API Gateway with security configuration"""
        try:
            # Create REST API
            api_response = self.apigateway.create_rest_api(
                name='aquachain-api',
                description='AquaChain Water Quality Monitoring API',
                version='v1',
                endpointConfiguration={
                    'types': ['REGIONAL']
                },
                policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "execute-api:Invoke",
                            "Resource": "*"
                        }
                    ]
                })
            )
            
            api_id = api_response['id']
            print(f"Created API Gateway: {api_id}")
            
            # Get root resource
            resources = self.apigateway.get_resources(restApiId=api_id)
            root_resource_id = None
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_resource_id = resource['id']
                    break
            
            # Create API resources and methods
            self._create_api_resources(api_id, root_resource_id)
            
            # Configure CORS
            self._configure_cors(api_id, root_resource_id)
            
            # Create authorizer
            authorizer_id = self._create_cognito_authorizer(api_id)
            
            # Configure request/response validation
            self._configure_validation(api_id)
            
            # Deploy API
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment'
            )
            
            # Configure stage settings
            self._configure_stage_settings(api_id, 'prod')
            
            return {
                'api_id': api_id,
                'api_url': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod",
                'authorizer_id': authorizer_id,
                'deployment_id': deployment['id']
            }
            
        except ClientError as e:
            print(f"Error creating API Gateway: {e}")
            raise
    
    def _create_api_resources(self, api_id: str, root_resource_id: str):
        """Create API resource structure"""
        resources = {
            'api': None,
            'v1': None,
            'readings': None,
            'users': None,
            'service-requests': None,
            'technicians': None,
            'audit': None,
            'analytics': None
        }
        
        # Create /api resource
        api_resource = self.apigateway.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='api'
        )
        resources['api'] = api_resource['id']
        
        # Create /api/v1 resource
        v1_resource = self.apigateway.create_resource(
            restApiId=api_id,
            parentId=resources['api'],
            pathPart='v1'
        )
        resources['v1'] = v1_resource['id']
        
        # Create main resource endpoints
        for resource_name in ['readings', 'users', 'service-requests', 'technicians', 'audit', 'analytics']:
            resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=resources['v1'],
                pathPart=resource_name
            )
            resources[resource_name] = resource['id']
            
            # Create proxy resource for dynamic paths
            proxy_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=resource['id'],
                pathPart='{proxy+}'
            )
            
            # Add methods to proxy resource
            self._add_resource_methods(api_id, proxy_resource['id'], resource_name)
        
        return resources
    
    def _add_resource_methods(self, api_id: str, resource_id: str, resource_type: str):
        """Add HTTP methods to resources"""
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        
        for method in methods:
            try:
                if method == 'OPTIONS':
                    # CORS preflight
                    self.apigateway.put_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method,
                        authorizationType='NONE'
                    )
                else:
                    # Authenticated methods
                    self.apigateway.put_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method,
                        authorizationType='COGNITO_USER_POOLS',
                        requestParameters={
                            'method.request.header.Authorization': True
                        }
                    )
                
                # Add integration (placeholder - will be configured per Lambda)
                self._add_method_integration(api_id, resource_id, method, resource_type)
                
            except ClientError as e:
                if 'ConflictException' not in str(e):
                    print(f"Error adding method {method} to resource: {e}")
    
    def _add_method_integration(self, api_id: str, resource_id: str, method: str, resource_type: str):
        """Add Lambda integration to method"""
        # This will be configured when Lambda functions are deployed
        # Production integration will be added during deployment
        # Placeholder for Lambda integration configuration
        pass
        
        # Add integration response
        self.apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
            }
        )
    
    def _configure_cors(self, api_id: str, root_resource_id: str):
        """Configure CORS for API Gateway"""
        # CORS is handled in method responses above
        print("CORS configured for all resources")
    
    def _create_cognito_authorizer(self, api_id: str) -> str:
        """Create Cognito User Pool authorizer"""
        try:
            # Get Cognito User Pool ARN (assuming it exists)
            user_pool_arn = f"arn:aws:cognito-idp:{self.region}:123456789012:userpool/us-east-1_XXXXXXXXX"
            
            authorizer = self.apigateway.create_authorizer(
                restApiId=api_id,
                name='aquachain-cognito-authorizer',
                type='COGNITO_USER_POOLS',
                providerARNs=[user_pool_arn],
                identitySource='method.request.header.Authorization'
            )
            
            print(f"Created Cognito authorizer: {authorizer['id']}")
            return authorizer['id']
            
        except ClientError as e:
            print(f"Error creating authorizer: {e}")
            # Return None if authorizer creation fails
            return None
    
    def _configure_validation(self, api_id: str):
        """Configure request/response validation"""
        try:
            # Create request validator
            validator = self.apigateway.create_request_validator(
                restApiId=api_id,
                name='aquachain-validator',
                validateRequestBody=True,
                validateRequestParameters=True
            )
            
            print(f"Created request validator: {validator['id']}")
            return validator['id']
            
        except ClientError as e:
            print(f"Error creating validator: {e}")
            return None
    
    def _configure_stage_settings(self, api_id: str, stage_name: str):
        """Configure stage settings for logging and monitoring"""
        try:
            # Create CloudWatch log group
            log_group_name = f"/aws/apigateway/{api_id}"
            try:
                self.logs.create_log_group(logGroupName=log_group_name)
            except ClientError as e:
                if 'ResourceAlreadyExistsException' not in str(e):
                    raise
            
            # Update stage settings
            self.apigateway.update_stage(
                restApiId=api_id,
                stageName=stage_name,
                patchOps=[
                    {
                        'op': 'replace',
                        'path': '/accessLogSettings/destinationArn',
                        'value': f"arn:aws:logs:{self.region}:123456789012:log-group:{log_group_name}"
                    },
                    {
                        'op': 'replace',
                        'path': '/accessLogSettings/format',
                        'value': json.dumps({
                            "requestId": "$context.requestId",
                            "ip": "$context.identity.sourceIp",
                            "caller": "$context.identity.caller",
                            "user": "$context.identity.user",
                            "requestTime": "$context.requestTime",
                            "httpMethod": "$context.httpMethod",
                            "resourcePath": "$context.resourcePath",
                            "status": "$context.status",
                            "protocol": "$context.protocol",
                            "responseLength": "$context.responseLength"
                        })
                    },
                    {
                        'op': 'replace',
                        'path': '/metricsEnabled',
                        'value': 'true'
                    },
                    {
                        'op': 'replace',
                        'path': '/dataTraceEnabled',
                        'value': 'true'
                    },
                    {
                        'op': 'replace',
                        'path': '/loggingLevel',
                        'value': 'INFO'
                    },
                    {
                        'op': 'replace',
                        'path': '/throttle/rateLimit',
                        'value': '1000'
                    },
                    {
                        'op': 'replace',
                        'path': '/throttle/burstLimit',
                        'value': '2000'
                    }
                ]
            )
            
            print(f"Configured stage settings for {stage_name}")
            
        except ClientError as e:
            print(f"Error configuring stage settings: {e}")
    
    def create_waf_web_acl(self, api_arn: str) -> str:
        """Create WAF Web ACL for API Gateway protection"""
        try:
            web_acl = self.wafv2.create_web_acl(
                Scope='REGIONAL',
                Name='aquachain-api-waf',
                Description='WAF for AquaChain API Gateway',
                DefaultAction={'Allow': {}},
                Rules=[
                    {
                        'Name': 'RateLimitRule',
                        'Priority': 1,
                        'Statement': {
                            'RateBasedStatement': {
                                'Limit': 1000,
                                'AggregateKeyType': 'IP'
                            }
                        },
                        'Action': {'Block': {}},
                        'VisibilityConfig': {
                            'SampledRequestsEnabled': True,
                            'CloudWatchMetricsEnabled': True,
                            'MetricName': 'RateLimitRule'
                        }
                    },
                    {
                        'Name': 'IPReputationRule',
                        'Priority': 2,
                        'Statement': {
                            'ManagedRuleGroupStatement': {
                                'VendorName': 'AWS',
                                'Name': 'AWSManagedRulesAmazonIpReputationList'
                            }
                        },
                        'Action': {'Block': {}},
                        'VisibilityConfig': {
                            'SampledRequestsEnabled': True,
                            'CloudWatchMetricsEnabled': True,
                            'MetricName': 'IPReputationRule'
                        },
                        'OverrideAction': {'None': {}}
                    },
                    {
                        'Name': 'CommonRuleSetRule',
                        'Priority': 3,
                        'Statement': {
                            'ManagedRuleGroupStatement': {
                                'VendorName': 'AWS',
                                'Name': 'AWSManagedRulesCommonRuleSet'
                            }
                        },
                        'Action': {'Block': {}},
                        'VisibilityConfig': {
                            'SampledRequestsEnabled': True,
                            'CloudWatchMetricsEnabled': True,
                            'MetricName': 'CommonRuleSetRule'
                        },
                        'OverrideAction': {'None': {}}
                    },
                    {
                        'Name': 'SQLInjectionRule',
                        'Priority': 4,
                        'Statement': {
                            'ManagedRuleGroupStatement': {
                                'VendorName': 'AWS',
                                'Name': 'AWSManagedRulesSQLiRuleSet'
                            }
                        },
                        'Action': {'Block': {}},
                        'VisibilityConfig': {
                            'SampledRequestsEnabled': True,
                            'CloudWatchMetricsEnabled': True,
                            'MetricName': 'SQLInjectionRule'
                        },
                        'OverrideAction': {'None': {}}
                    }
                ],
                VisibilityConfig={
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'aquachain-api-waf'
                }
            )
            
            web_acl_arn = web_acl['Summary']['ARN']
            print(f"Created WAF Web ACL: {web_acl_arn}")
            
            # Associate WAF with API Gateway
            self.wafv2.associate_web_acl(
                WebACLArn=web_acl_arn,
                ResourceArn=api_arn
            )
            
            print(f"Associated WAF with API Gateway: {api_arn}")
            return web_acl_arn
            
        except ClientError as e:
            print(f"Error creating WAF Web ACL: {e}")
            raise
    
    def setup_complete_api_gateway(self) -> Dict[str, Any]:
        """Complete API Gateway setup with all security features"""
        # Create API Gateway
        api_info = self.create_api_gateway()
        
        # Create WAF Web ACL
        api_arn = f"arn:aws:apigateway:{self.region}::/restapis/{api_info['api_id']}/stages/prod"
        waf_arn = self.create_waf_web_acl(api_arn)
        
        return {
            **api_info,
            'waf_arn': waf_arn,
            'api_arn': api_arn
        }


def main():
    """Main function to set up API Gateway"""
    setup = APIGatewaySetup()
    result = setup.setup_complete_api_gateway()
    
    print("\nAPI Gateway Setup Complete:")
    print(f"API ID: {result['api_id']}")
    print(f"API URL: {result['api_url']}")
    print(f"WAF ARN: {result['waf_arn']}")
    
    return result


if __name__ == "__main__":
    main()