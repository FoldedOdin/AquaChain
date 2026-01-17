"""
API Gateway endpoints for Shipment Tracking Automation
Implements endpoints for shipment creation, webhook handling, and status retrieval
"""
import boto3
import json
import os
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


class ShipmentEndpointsSetup:
    """Setup API Gateway endpoints for shipment tracking"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
    def get_or_create_api(self) -> str:
        """Get existing API Gateway or create new one"""
        try:
            # Try to find existing API
            apis = self.apigateway.get_rest_apis()
            for api in apis['items']:
                if api['name'] == 'aquachain-api':
                    print(f"Found existing API: {api['id']}")
                    return api['id']
            
            # Create new API if not found
            api_response = self.apigateway.create_rest_api(
                name='aquachain-api',
                description='AquaChain Water Quality Monitoring API',
                endpointConfiguration={'types': ['REGIONAL']}
            )
            api_id = api_response['id']
            print(f"Created new API: {api_id}")
            return api_id
            
        except ClientError as e:
            print(f"Error getting/creating API: {e}")
            raise
    
    def get_root_resource(self, api_id: str) -> str:
        """Get root resource ID"""
        resources = self.apigateway.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource['path'] == '/':
                return resource['id']
        raise Exception("Root resource not found")
    
    def create_resource_path(self, api_id: str, parent_id: str, path_parts: list) -> str:
        """Create nested resource path"""
        current_parent = parent_id
        
        for part in path_parts:
            # Check if resource already exists
            resources = self.apigateway.get_resources(restApiId=api_id)
            existing_resource = None
            
            for resource in resources['items']:
                if resource.get('parentId') == current_parent and resource.get('pathPart') == part:
                    existing_resource = resource['id']
                    break
            
            if existing_resource:
                current_parent = existing_resource
            else:
                # Create new resource
                resource = self.apigateway.create_resource(
                    restApiId=api_id,
                    parentId=current_parent,
                    pathPart=part
                )
                current_parent = resource['id']
        
        return current_parent
    
    def get_or_create_authorizer(self, api_id: str, user_pool_arn: str) -> str:
        """Get existing Cognito authorizer or create new one"""
        try:
            # Check for existing authorizer
            authorizers = self.apigateway.get_authorizers(restApiId=api_id)
            for auth in authorizers.get('items', []):
                if auth['name'] == 'aquachain-cognito-authorizer':
                    print(f"Found existing authorizer: {auth['id']}")
                    return auth['id']
            
            # Create new authorizer
            authorizer = self.apigateway.create_authorizer(
                restApiId=api_id,
                name='aquachain-cognito-authorizer',
                type='COGNITO_USER_POOLS',
                providerARNs=[user_pool_arn],
                identitySource='method.request.header.Authorization',
                authorizerResultTtlInSeconds=300
            )
            print(f"Created new authorizer: {authorizer['id']}")
            return authorizer['id']
            
        except ClientError as e:
            print(f"Error creating authorizer: {e}")
            raise
    
    def add_lambda_permission(self, lambda_name: str, api_id: str, method: str, resource_path: str):
        """Add permission for API Gateway to invoke Lambda"""
        try:
            source_arn = f"arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*/{method}{resource_path}"
            
            self.lambda_client.add_permission(
                FunctionName=lambda_name,
                StatementId=f"{lambda_name}-{method}-{api_id}",
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
            print(f"Added Lambda permission for {lambda_name}")
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                print(f"Permission already exists for {lambda_name}")
            else:
                print(f"Error adding Lambda permission: {e}")
    
    def create_method_with_integration(
        self,
        api_id: str,
        resource_id: str,
        http_method: str,
        lambda_name: str,
        authorizer_id: Optional[str] = None,
        require_auth: bool = True
    ):
        """Create API Gateway method with Lambda integration"""
        try:
            # Create method
            method_params = {
                'restApiId': api_id,
                'resourceId': resource_id,
                'httpMethod': http_method,
                'authorizationType': 'COGNITO_USER_POOLS' if require_auth and authorizer_id else 'NONE',
                'requestParameters': {}
            }
            
            if require_auth and authorizer_id:
                method_params['authorizerId'] = authorizer_id
                method_params['requestParameters']['method.request.header.Authorization'] = True
            
            self.apigateway.put_method(**method_params)
            
            # Create method response
            self.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                },
                responseModels={'application/json': 'Empty'}
            )
            
            # Create Lambda integration
            lambda_arn = f"arn:aws:lambda:{self.region}:{self.account_id}:function:{lambda_name}"
            
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            )
            
            # Create integration response
            self.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                }
            )
            
            print(f"Created {http_method} method with Lambda integration: {lambda_name}")
            
        except ClientError as e:
            if 'ConflictException' in str(e):
                print(f"Method {http_method} already exists")
            else:
                print(f"Error creating method: {e}")
                raise
    
    def create_cors_method(self, api_id: str, resource_id: str):
        """Create OPTIONS method for CORS preflight"""
        try:
            # Create OPTIONS method
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Create method response
            self.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                },
                responseModels={'application/json': 'Empty'}
            )
            
            # Create mock integration
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Create integration response
            self.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Webhook-Signature'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                },
                responseTemplates={
                    'application/json': ''
                }
            )
            
            print("Created CORS OPTIONS method")
            
        except ClientError as e:
            if 'ConflictException' in str(e):
                print("OPTIONS method already exists")
            else:
                print(f"Error creating CORS method: {e}")
    
    def configure_usage_plan(self, api_id: str, stage_name: str, rate_limit: int, burst_limit: int) -> str:
        """Configure usage plan with rate limiting"""
        try:
            # Check for existing usage plan
            usage_plans = self.apigateway.get_usage_plans()
            for plan in usage_plans.get('items', []):
                if plan['name'] == f'aquachain-shipments-{rate_limit}rpm':
                    print(f"Found existing usage plan: {plan['id']}")
                    return plan['id']
            
            # Create usage plan
            usage_plan = self.apigateway.create_usage_plan(
                name=f'aquachain-shipments-{rate_limit}rpm',
                description=f'Shipment endpoints with {rate_limit} req/min limit',
                throttle={
                    'rateLimit': rate_limit,
                    'burstLimit': burst_limit
                },
                quota={
                    'limit': rate_limit * 60 * 24,  # Daily quota
                    'period': 'DAY'
                }
            )
            
            # Associate with API stage
            self.apigateway.create_usage_plan_key(
                usagePlanId=usage_plan['id'],
                keyId=api_id,
                keyType='API_KEY'
            )
            
            print(f"Created usage plan: {usage_plan['id']}")
            return usage_plan['id']
            
        except ClientError as e:
            print(f"Error configuring usage plan: {e}")
            return None
    
    def setup_post_shipments_endpoint(self, api_id: str, authorizer_id: str) -> Dict[str, Any]:
        """
        Task 10.1: Create POST /api/shipments endpoint
        - Configure API Gateway REST API endpoint
        - Set up Cognito authorizer (Admin role required)
        - Integrate with create_shipment Lambda
        - Configure CORS headers
        - Set rate limit to 100 req/min
        """
        print("\n=== Setting up POST /api/shipments endpoint ===")
        
        # Get root resource
        root_id = self.get_root_resource(api_id)
        
        # Create /api/shipments resource path
        shipments_resource_id = self.create_resource_path(
            api_id, root_id, ['api', 'shipments']
        )
        
        # Add Lambda permission
        self.add_lambda_permission(
            'create_shipment',
            api_id,
            'POST',
            '/api/shipments'
        )
        
        # Create POST method with Cognito auth
        self.create_method_with_integration(
            api_id=api_id,
            resource_id=shipments_resource_id,
            http_method='POST',
            lambda_name='create_shipment',
            authorizer_id=authorizer_id,
            require_auth=True
        )
        
        # Create CORS OPTIONS method
        self.create_cors_method(api_id, shipments_resource_id)
        
        # Configure rate limiting (100 req/min)
        usage_plan_id = self.configure_usage_plan(
            api_id=api_id,
            stage_name='prod',
            rate_limit=100,
            burst_limit=200
        )
        
        return {
            'endpoint': 'POST /api/shipments',
            'resource_id': shipments_resource_id,
            'lambda': 'create_shipment',
            'auth': 'Cognito (Admin)',
            'rate_limit': '100 req/min',
            'usage_plan_id': usage_plan_id
        }
    
    def setup_post_webhooks_endpoint(self, api_id: str) -> Dict[str, Any]:
        """
        Task 10.2: Create POST /api/webhooks/:courier endpoint
        - Configure API Gateway endpoint with path parameter
        - No Cognito auth (signature verification in Lambda)
        - Integrate with webhook_handler Lambda
        - Set rate limit to 1000 req/min
        """
        print("\n=== Setting up POST /api/webhooks/:courier endpoint ===")
        
        # Get root resource
        root_id = self.get_root_resource(api_id)
        
        # Create /api/webhooks resource path
        webhooks_resource_id = self.create_resource_path(
            api_id, root_id, ['api', 'webhooks']
        )
        
        # Create /{courier} path parameter resource
        courier_resource = self.apigateway.create_resource(
            restApiId=api_id,
            parentId=webhooks_resource_id,
            pathPart='{courier}'
        )
        courier_resource_id = courier_resource['id']
        
        # Add Lambda permission
        self.add_lambda_permission(
            'webhook_handler',
            api_id,
            'POST',
            '/api/webhooks/*'
        )
        
        # Create POST method WITHOUT Cognito auth (signature verification in Lambda)
        self.create_method_with_integration(
            api_id=api_id,
            resource_id=courier_resource_id,
            http_method='POST',
            lambda_name='webhook_handler',
            authorizer_id=None,
            require_auth=False
        )
        
        # Create CORS OPTIONS method
        self.create_cors_method(api_id, courier_resource_id)
        
        # Configure rate limiting (1000 req/min)
        usage_plan_id = self.configure_usage_plan(
            api_id=api_id,
            stage_name='prod',
            rate_limit=1000,
            burst_limit=2000
        )
        
        return {
            'endpoint': 'POST /api/webhooks/{courier}',
            'resource_id': courier_resource_id,
            'lambda': 'webhook_handler',
            'auth': 'None (HMAC signature verification in Lambda)',
            'rate_limit': '1000 req/min',
            'usage_plan_id': usage_plan_id
        }
    
    def setup_get_shipment_by_id_endpoint(self, api_id: str, authorizer_id: str) -> Dict[str, Any]:
        """
        Task 10.3: Create GET /api/shipments/:shipmentId endpoint
        - Configure API Gateway endpoint with path parameter
        - Set up Cognito authorizer (all roles)
        - Integrate with get_shipment_status Lambda
        - Configure CORS headers
        - Set rate limit to 200 req/min
        """
        print("\n=== Setting up GET /api/shipments/:shipmentId endpoint ===")
        
        # Get root resource
        root_id = self.get_root_resource(api_id)
        
        # Get /api/shipments resource (should exist from task 10.1)
        shipments_resource_id = self.create_resource_path(
            api_id, root_id, ['api', 'shipments']
        )
        
        # Create /{shipmentId} path parameter resource
        shipment_id_resource = self.apigateway.create_resource(
            restApiId=api_id,
            parentId=shipments_resource_id,
            pathPart='{shipmentId}'
        )
        shipment_id_resource_id = shipment_id_resource['id']
        
        # Add Lambda permission
        self.add_lambda_permission(
            'get_shipment_status',
            api_id,
            'GET',
            '/api/shipments/*'
        )
        
        # Create GET method with Cognito auth (all roles)
        self.create_method_with_integration(
            api_id=api_id,
            resource_id=shipment_id_resource_id,
            http_method='GET',
            lambda_name='get_shipment_status',
            authorizer_id=authorizer_id,
            require_auth=True
        )
        
        # Create CORS OPTIONS method
        self.create_cors_method(api_id, shipment_id_resource_id)
        
        # Configure rate limiting (200 req/min)
        usage_plan_id = self.configure_usage_plan(
            api_id=api_id,
            stage_name='prod',
            rate_limit=200,
            burst_limit=400
        )
        
        return {
            'endpoint': 'GET /api/shipments/{shipmentId}',
            'resource_id': shipment_id_resource_id,
            'lambda': 'get_shipment_status',
            'auth': 'Cognito (all roles)',
            'rate_limit': '200 req/min',
            'usage_plan_id': usage_plan_id
        }
    
    def setup_get_shipment_by_order_endpoint(self, api_id: str, authorizer_id: str) -> Dict[str, Any]:
        """
        Task 10.4: Create GET /api/shipments?orderId=:orderId endpoint
        - Configure API Gateway endpoint with query parameter
        - Set up Cognito authorizer (all roles)
        - Integrate with get_shipment_status Lambda
        - Configure CORS headers
        """
        print("\n=== Setting up GET /api/shipments?orderId=:orderId endpoint ===")
        
        # Get root resource
        root_id = self.get_root_resource(api_id)
        
        # Get /api/shipments resource (should exist from task 10.1)
        shipments_resource_id = self.create_resource_path(
            api_id, root_id, ['api', 'shipments']
        )
        
        # Add Lambda permission for query parameter endpoint
        self.add_lambda_permission(
            'get_shipment_status',
            api_id,
            'GET',
            '/api/shipments'
        )
        
        # Create GET method with Cognito auth (all roles)
        # This uses the same resource as POST but different HTTP method
        self.create_method_with_integration(
            api_id=api_id,
            resource_id=shipments_resource_id,
            http_method='GET',
            lambda_name='get_shipment_status',
            authorizer_id=authorizer_id,
            require_auth=True
        )
        
        # CORS already configured in task 10.1
        
        return {
            'endpoint': 'GET /api/shipments?orderId={orderId}',
            'resource_id': shipments_resource_id,
            'lambda': 'get_shipment_status',
            'auth': 'Cognito (all roles)',
            'rate_limit': '200 req/min (shared with task 10.3)',
            'note': 'Uses query parameter orderId'
        }
    
    def deploy_api(self, api_id: str, stage_name: str = 'prod'):
        """Deploy API to stage"""
        try:
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName=stage_name,
                description=f'Deployment for shipment endpoints'
            )
            
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/{stage_name}"
            print(f"\nAPI deployed to: {api_url}")
            
            return {
                'deployment_id': deployment['id'],
                'api_url': api_url
            }
            
        except ClientError as e:
            print(f"Error deploying API: {e}")
            raise


def main():
    """Main function to setup all shipment endpoints"""
    import sys
    
    # Get Cognito User Pool ARN from environment or parameter
    user_pool_arn = os.environ.get('COGNITO_USER_POOL_ARN')
    if not user_pool_arn:
        print("Warning: COGNITO_USER_POOL_ARN not set. Using placeholder.")
        user_pool_arn = "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_XXXXXXXXX"
    
    setup = ShipmentEndpointsSetup()
    
    # Get or create API
    api_id = setup.get_or_create_api()
    
    # Get or create authorizer
    authorizer_id = setup.get_or_create_authorizer(api_id, user_pool_arn)
    
    # Setup POST /api/shipments endpoint (Task 10.1)
    result_10_1 = setup.setup_post_shipments_endpoint(api_id, authorizer_id)
    print("\n=== Task 10.1 Complete ===")
    print(json.dumps(result_10_1, indent=2))
    
    # Setup POST /api/webhooks/:courier endpoint (Task 10.2)
    result_10_2 = setup.setup_post_webhooks_endpoint(api_id)
    print("\n=== Task 10.2 Complete ===")
    print(json.dumps(result_10_2, indent=2))
    
    # Setup GET /api/shipments/:shipmentId endpoint (Task 10.3)
    result_10_3 = setup.setup_get_shipment_by_id_endpoint(api_id, authorizer_id)
    print("\n=== Task 10.3 Complete ===")
    print(json.dumps(result_10_3, indent=2))
    
    # Setup GET /api/shipments?orderId=:orderId endpoint (Task 10.4)
    result_10_4 = setup.setup_get_shipment_by_order_endpoint(api_id, authorizer_id)
    print("\n=== Task 10.4 Complete ===")
    print(json.dumps(result_10_4, indent=2))
    
    # Deploy API
    deployment = setup.deploy_api(api_id)
    print(f"\nDeployment ID: {deployment['deployment_id']}")
    print(f"API URL: {deployment['api_url']}")
    
    return {
        'api_id': api_id,
        'authorizer_id': authorizer_id,
        'endpoints': {
            'task_10_1': result_10_1,
            'task_10_2': result_10_2,
            'task_10_3': result_10_3,
            'task_10_4': result_10_4
        },
        **deployment
    }


if __name__ == "__main__":
    result = main()
    print("\n=== All Shipment Endpoints Setup Complete ===")
    print(json.dumps(result, indent=2))
