"""
AquaChain API Stack
API Gateway, Cognito, and authentication infrastructure
"""

from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_apigatewayv2 as apigatewayv2,
    aws_cognito as cognito,
    aws_wafv2 as waf,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_iam as iam,
    aws_lambda as lambda_,
    Duration,
    CfnOutput,
    IAspect
)
from constructs import Construct, IConstruct
from typing import Dict, Any
from config.environment_config import get_resource_name
import jsii


@jsii.implements(IAspect)
class RemoveAdminLambdaPermissionsAspect:
    """
    CDK Aspect to remove auto-generated Lambda permissions for admin endpoints.
    This keeps only the wildcard permission, preventing policy size from exceeding 20KB.
    """
    
    def visit(self, node: IConstruct) -> None:
        """Visit each node in the construct tree and remove admin Lambda permissions."""
        # Check if this is a CfnPermission resource
        if isinstance(node, lambda_.CfnPermission):
            # Get the logical ID of the permission
            logical_id = node.node.id
            
            # Remove auto-generated permissions for admin endpoints (keep only wildcard)
            # Auto-generated permissions have IDs like "RestAPIapiadminusersGETApiPermission..."
            # Our wildcard permission has ID "AdminLambdaApiGatewayPermission"
            if logical_id.startswith("RestAPIapiadmin") and "ApiPermission" in logical_id:
                # This is an auto-generated permission for an admin endpoint
                # Remove it from the parent's children
                parent = node.node.scope
                if parent:
                    parent.node.try_remove_child(logical_id)

class AquaChainApiStack(Stack):
    """
    API layer stack containing API Gateway, Cognito, and WAF
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 lambda_functions: Dict[str, Any] = None, 
                 compute_resources: Dict[str, Any] = None,
                 security_resources: Dict[str, Any] = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        # Accept either lambda_functions or compute_resources for backward compatibility
        self.lambda_functions = lambda_functions or compute_resources or {}
        self.security_resources = security_resources or {}
        self.api_resources = {}
        
        # Import payment Lambda from Enhanced Ordering stack (if it exists)
        try:
            payment_lambda = lambda_.Function.from_function_name(
                self, "PaymentServiceLambda",
                function_name=get_resource_name(self.config, "function", "payment-service")
            )
            self.lambda_functions["payment_service"] = payment_lambda
        except Exception as e:
            # Payment Lambda doesn't exist yet, skip
            pass
        
        # Import razorpay webhook Lambda from Enhanced Ordering stack (if it exists)
        try:
            razorpay_webhook_lambda = lambda_.Function.from_function_name(
                self, "RazorpayWebhookLambda",
                function_name=get_resource_name(self.config, "function", "razorpay-webhook")
            )
            self.lambda_functions["razorpay_webhook"] = razorpay_webhook_lambda
        except Exception as e:
            # Razorpay webhook Lambda doesn't exist yet, skip
            pass
        
        # Create Cognito User Pool
        self._create_cognito_resources()
        
        # Create API Gateway
        self._create_api_gateway()
        
        # Create WebSocket API
        self._create_websocket_api()
        
        # Create WAF for API protection
        self._create_waf_resources()
        
        # Apply aspect to remove auto-generated admin Lambda permissions
        # This ensures only the wildcard permission is used, keeping policy size under 20KB
        from aws_cdk import Aspects
        Aspects.of(self).add(RemoveAdminLambdaPermissionsAspect())
    
    def _create_cognito_resources(self) -> None:
        """
        Create Cognito User Pool and related resources
        """
        
        # User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=get_resource_name(self.config, "pool", "users"),
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=False
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=self._get_removal_policy()
        )
        
        # Add custom attributes
        self.user_pool.add_domain(
            "UserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=get_resource_name(self.config, "auth", "domain")
            )
        )
        
        # User Pool Groups
        self.consumer_group = cognito.CfnUserPoolGroup(
            self, "ConsumerGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="consumers",
            description="Consumer users who monitor water quality"
        )
        
        self.technician_group = cognito.CfnUserPoolGroup(
            self, "TechnicianGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="technicians",
            description="Technician users who service devices"
        )
        
        self.admin_group = cognito.CfnUserPoolGroup(
            self, "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="administrators",
            description="Administrator users with full system access"
        )
        
        # User Pool Client for web application
        self.user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name=get_resource_name(self.config, "client", "web"),
            generate_secret=False,  # For web applications
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=[
                    f"https://{self.config['domain_name']}/auth/callback",
                    "http://localhost:3000/auth/callback"  # For development
                ],
                logout_urls=[
                    f"https://{self.config['domain_name']}/auth/logout",
                    "http://localhost:3000/auth/logout"
                ]
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ] + ([cognito.UserPoolClientIdentityProvider.GOOGLE] if self.config.get("google_client_id") else []),
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30)
        )
        
        # Identity Pool for AWS resource access
        self.identity_pool = cognito.CfnIdentityPool(
            self, "IdentityPool",
            identity_pool_name=get_resource_name(self.config, "identity", "pool"),
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                )
            ]
        )
        
        # Google Identity Provider (if configured)
        if self.config.get("google_client_id"):
            self.google_provider = cognito.CfnUserPoolIdentityProvider(
                self, "GoogleProvider",
                user_pool_id=self.user_pool.user_pool_id,
                provider_name="Google",
                provider_type="Google",
                provider_details={
                    "client_id": self.config["google_client_id"],
                    "client_secret": self.config["google_client_secret"],
                    "authorize_scopes": "email openid profile"
                },
                attribute_mapping={
                    "email": "email",
                    "given_name": "given_name",
                    "family_name": "family_name"
                }
            )
        
        self.api_resources.update({
            "user_pool": self.user_pool,
            "user_pool_client": self.user_pool_client,
            "identity_pool": self.identity_pool,
            "consumer_group": self.consumer_group,
            "technician_group": self.technician_group,
            "admin_group": self.admin_group
        })
    
    def _create_api_gateway(self) -> None:
        """
        Create REST API Gateway with authentication and rate limiting
        """
        
        # Cognito Authorizer
        # IMPORTANT: results_cache_ttl enables token caching for better performance
        # Cache tokens for 5 minutes (300 seconds) to reduce Cognito API calls
        # identity_source ensures the Authorization header is used for caching
        self.cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer",
            cognito_user_pools=[self.user_pool],
            authorizer_name="AquaChainAuthorizer",
            identity_source="method.request.header.Authorization",
            results_cache_ttl=Duration.seconds(300)  # Cache for 5 minutes (production recommended)
        )
        
        # REST API
        self.rest_api = apigateway.RestApi(
            self, "RestAPI",
            rest_api_name=get_resource_name(self.config, "api", "rest"),
            description="AquaChain REST API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token"
                ],
                allow_credentials=True
            ),
            deploy_options=apigateway.StageOptions(
                stage_name=self.config["environment"],
                throttling_rate_limit=self.config["api_throttle_rate_limit"],
                throttling_burst_limit=self.config["api_throttle_burst_limit"],
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True
            ),
            cloud_watch_role=True
        )
        
        # API Resources and Methods
        
        # Create /api root resource once
        api_root = self.rest_api.root.add_resource("api")
        
        # /api/v1 root
        api_v1 = api_root.add_resource("v1")
        
        # /api/v1/readings
        readings_resource = api_v1.add_resource("readings")
        device_readings_resource = readings_resource.add_resource("{deviceId}")
        
        # GET /api/v1/readings/{deviceId}
        device_readings_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["data_processing"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # GET /api/v1/readings/{deviceId}/history
        history_resource = device_readings_resource.add_resource("history")
        history_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["data_processing"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/users
        users_resource = api_v1.add_resource("users")
        users_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["user_management"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        users_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["user_management"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/profile - Profile management endpoints
        profile_resource = api_root.add_resource("profile")
        
        # /api/profile/update - Direct profile operations (GET and PUT)
        update_resource = profile_resource.add_resource("update")
        update_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["user_management"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        update_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions["user_management"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/profile/request-otp - Request OTP for profile updates
        request_otp_resource = profile_resource.add_resource("request-otp")
        request_otp_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["user_management"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/profile/verify-and-update - Verify OTP and update profile
        verify_update_resource = profile_resource.add_resource("verify-and-update")
        verify_update_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions["user_management"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/service-requests
        service_requests_resource = api_v1.add_resource("service-requests")
        service_requests_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        service_requests_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/service-requests/{requestId}
        service_request_resource = service_requests_resource.add_resource("{requestId}")
        service_request_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        service_request_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician - Technician-specific endpoints
        technician_resource = api_v1.add_resource("technician")
        
        # /api/v1/technician/tasks - Get assigned tasks for technician
        technician_tasks_resource = technician_resource.add_resource("tasks")
        technician_tasks_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/{taskId}/accept - Accept a task
        technician_task_resource = technician_tasks_resource.add_resource("{taskId}")
        technician_task_accept_resource = technician_task_resource.add_resource("accept")
        technician_task_accept_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/{taskId}/status - Update task status
        technician_task_status_resource = technician_task_resource.add_resource("status")
        technician_task_status_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/{taskId}/notes - Add notes to task
        technician_task_notes_resource = technician_task_resource.add_resource("notes")
        technician_task_notes_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/{taskId}/attachments - Upload attachments
        technician_task_attachments_resource = technician_task_resource.add_resource("attachments")
        technician_task_attachments_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/{taskId}/complete - Complete a task
        technician_task_complete_resource = technician_task_resource.add_resource("complete")
        technician_task_complete_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/history - Get task history
        technician_tasks_history_resource = technician_tasks_resource.add_resource("history")
        technician_tasks_history_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/tasks/{taskId}/route - Get route to task location
        technician_task_route_resource = technician_task_resource.add_resource("route")
        technician_task_route_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/location - Update technician location
        technician_location_resource = technician_resource.add_resource("location")
        technician_location_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/inventory
        technician_inventory_resource = technician_resource.add_resource("inventory")
        technician_inventory_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/inventory/checkout
        technician_inventory_checkout_resource = technician_inventory_resource.add_resource("checkout")
        technician_inventory_checkout_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/inventory/return
        technician_inventory_return_resource = technician_inventory_resource.add_resource("return")
        technician_inventory_return_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/technician/inventory/request-restock
        technician_inventory_restock_resource = technician_inventory_resource.add_resource("request-restock")
        technician_inventory_restock_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(self.lambda_functions["service_request"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/v1/audit
        audit_resource = api_v1.add_resource("audit")
        hash_chain_resource = audit_resource.add_resource("hash-chain")
        hash_chain_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["audit_processor"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        # /api/admin root - Admin endpoints
        api_admin = api_root.add_resource("admin")
        
        # Admin Lambda integration (if admin service exists)
        if "admin_service" in self.lambda_functions:
            # Add a single wildcard permission for all admin endpoints
            # This replaces individual permissions per endpoint to stay under the 20KB policy limit
            from aws_cdk import aws_lambda as lambda_
            lambda_.CfnPermission(
                self, "AdminLambdaApiGatewayPermission",
                action="lambda:InvokeFunction",
                function_name=self.lambda_functions["admin_service"].function_name,
                principal="apigateway.amazonaws.com",
                source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{self.rest_api.rest_api_id}/*/*"
            )
            
            # Use LambdaIntegration for proper proxy behavior, but prevent automatic permission creation
            # by using a custom integration that references the Lambda ARN without granting permissions
            # This ensures only the wildcard permission above is used, keeping policy size under 20KB
            from aws_cdk import aws_iam as iam
            
            # Create a custom integration role that uses the wildcard permission
            # Note: We set credentials_role=None to use resource-based policy (our wildcard permission)
            admin_integration = apigateway.LambdaIntegration(
                self.lambda_functions["admin_service"],
                proxy=True,
                allow_test_invoke=False,  # Prevents test-invoke-stage permissions
                # This is the key: we already have the wildcard permission, so we don't want
                # LambdaIntegration to create additional permissions
            )
            
            # /api/admin/users - User management
            admin_users_resource = api_admin.add_resource("users")
            admin_users_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            admin_users_resource.add_method(
                "POST",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            # Note: CORS preflight is already handled by default_cors_preflight_options at API level
            
            # /api/admin/users/track-login - Login tracking (accessible to all authenticated users)
            admin_users_track_login_resource = admin_users_resource.add_resource("track-login")
            admin_users_track_login_resource.add_method(
                "POST",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/users/{userId}
            admin_user_resource = admin_users_resource.add_resource("{userId}")
            # GET method for user details (supports ?reveal=true for PII access)
            admin_user_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            admin_user_resource.add_method(
                "PUT",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            admin_user_resource.add_method(
                "DELETE",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/users/{userId}/reset-password
            admin_user_reset_resource = admin_user_resource.add_resource("reset-password")
            admin_user_reset_resource.add_method(
                "POST",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/users/{userId}/sensitive - Secure PII access (audit logged)
            admin_user_sensitive_resource = admin_user_resource.add_resource("sensitive")
            admin_user_sensitive_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/system - System management
            admin_system_resource = api_admin.add_resource("system")
            
            # /api/admin/system/configuration
            admin_config_resource = admin_system_resource.add_resource("configuration")
            admin_config_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            admin_config_resource.add_method(
                "PUT",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            # Note: CORS preflight is already handled by default_cors_preflight_options at API level
            
            # /api/admin/system/configuration/history
            admin_config_history_resource = admin_config_resource.add_resource("history")
            admin_config_history_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/system/configuration/validate
            admin_config_validate_resource = admin_config_resource.add_resource("validate")
            admin_config_validate_resource.add_method(
                "POST",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/system/configuration/rollback
            admin_config_rollback_resource = admin_config_resource.add_resource("rollback")
            admin_config_rollback_resource.add_method(
                "POST",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/system/health
            admin_health_resource = admin_system_resource.add_resource("health")
            admin_health_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            # Note: CORS preflight is already handled by default_cors_preflight_options at API level
            
            # /api/admin/system/performance
            admin_performance_resource = admin_system_resource.add_resource("performance")
            admin_performance_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/incidents - Incident management
            admin_incidents_resource = api_admin.add_resource("incidents")
            admin_incidents_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            admin_incidents_resource.add_method(
                "POST",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/incidents/stats
            admin_incidents_stats_resource = admin_incidents_resource.add_resource("stats")
            admin_incidents_stats_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/incidents/{incidentId}
            admin_incident_resource = admin_incidents_resource.add_resource("{incidentId}")
            admin_incident_resource.add_method(
                "PUT",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/audit - Audit management
            admin_audit_resource = api_admin.add_resource("audit")
            admin_audit_trail_resource = admin_audit_resource.add_resource("trail")
            admin_audit_trail_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/devices - Device management
            admin_devices_resource = api_admin.add_resource("devices")
            admin_devices_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/compliance - Compliance reporting
            admin_compliance_resource = api_admin.add_resource("compliance")
            admin_compliance_report_resource = admin_compliance_resource.add_resource("report")
            admin_compliance_report_resource.add_method(
                "GET",
                admin_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
        
        # /api/admin/security - Security audit endpoints
        # Import security audit Lambda if it exists
        try:
            security_audit_lambda = lambda_.Function.from_function_name(
                self, "SecurityAuditLambda",
                function_name=f"AquaChain-SecurityAudit-{self.config['environment']}"
            )
            
            # Add wildcard permission for security audit Lambda
            lambda_.CfnPermission(
                self, "SecurityAuditLambdaApiGatewayPermission",
                action="lambda:InvokeFunction",
                function_name=security_audit_lambda.function_name,
                principal="apigateway.amazonaws.com",
                source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{self.rest_api.rest_api_id}/*/*"
            )
            
            # Create integration
            security_audit_integration = apigateway.LambdaIntegration(
                security_audit_lambda,
                proxy=True,
                allow_test_invoke=False
            )
            
            # /api/admin/security
            admin_security_resource = api_admin.add_resource("security")
            
            # /api/admin/security/audit
            admin_security_audit_resource = admin_security_resource.add_resource("audit")
            admin_security_audit_resource.add_method(
                "GET",
                security_audit_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/security/audit/export
            admin_security_audit_export_resource = admin_security_audit_resource.add_resource("export")
            admin_security_audit_export_resource.add_method(
                "POST",
                security_audit_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/security/integrity
            admin_security_integrity_resource = admin_security_resource.add_resource("integrity")
            admin_security_integrity_resource.add_method(
                "GET",
                security_audit_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
            
            # /api/admin/security/integrity/verify
            admin_security_integrity_verify_resource = admin_security_integrity_resource.add_resource("verify")
            admin_security_integrity_verify_resource.add_method(
                "POST",
                security_audit_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
                method_responses=[
                    apigateway.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Credentials": True
                        }
                    )
                ]
            )
        except Exception as e:
            # Security audit Lambda doesn't exist yet, skip
            print(f"Security audit Lambda not found, skipping API integration: {e}")
            pass
        
        # /api/payments - Payment endpoints (authenticated)
        if "payment_service" in self.lambda_functions:
            api_payments = api_root.add_resource("payments")
            payment_integration = apigateway.LambdaIntegration(
                self.lambda_functions["payment_service"],
                proxy=True
            )
            
            # /api/payments/create-razorpay-order
            create_razorpay_order_resource = api_payments.add_resource("create-razorpay-order")
            create_razorpay_order_resource.add_method(
                "POST",
                payment_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO
            )
            
            # /api/payments/verify-payment
            verify_payment_resource = api_payments.add_resource("verify-payment")
            verify_payment_resource.add_method(
                "POST",
                payment_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO
            )
            
            # /api/payments/create-cod-payment
            create_cod_payment_resource = api_payments.add_resource("create-cod-payment")
            create_cod_payment_resource.add_method(
                "POST",
                payment_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO
            )
            
            # /api/payments/payment-status
            payment_status_resource = api_payments.add_resource("payment-status")
            payment_status_resource.add_method(
                "GET",
                payment_integration,
                authorizer=self.cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO
            )
        
        # /api/orders - Order management endpoints (authenticated)
        # Import order management Lambda from Enhanced Ordering stack
        try:
            order_management_lambda = lambda_.Function.from_function_name(
                self, "OrderManagementLambda",
                function_name=get_resource_name(self.config, "function", "order-management")
            )
            
            # Create /api/orders resource (or reuse if it already exists)
            # Check if the resource already exists to avoid duplicate creation errors
            api_orders = api_root.node.try_find_child("orders")
            if not api_orders:
                api_orders = api_root.add_resource("orders")
            
            # POST /api/orders - Create order
            api_orders.add_method(
                "POST",
                apigateway.LambdaIntegration(order_management_lambda),
                authorization_type=apigateway.AuthorizationType.COGNITO,
                authorizer=self.cognito_authorizer
            )
            
            # GET /api/orders - Get orders by consumer (with query parameter)
            api_orders.add_method(
                "GET",
                apigateway.LambdaIntegration(order_management_lambda),
                authorization_type=apigateway.AuthorizationType.COGNITO,
                authorizer=self.cognito_authorizer
            )
            
            # /api/orders/{orderId} resource
            api_order_id = api_orders.add_resource("{orderId}")
            
            # GET /api/orders/{orderId} - Get specific order
            api_order_id.add_method(
                "GET",
                apigateway.LambdaIntegration(order_management_lambda),
                authorization_type=apigateway.AuthorizationType.COGNITO,
                authorizer=self.cognito_authorizer
            )
            
            # /api/orders/{orderId}/status resource
            api_order_status = api_order_id.add_resource("status")
            
            # PUT /api/orders/{orderId}/status - Update order status
            api_order_status.add_method(
                "PUT",
                apigateway.LambdaIntegration(order_management_lambda),
                authorization_type=apigateway.AuthorizationType.COGNITO,
                authorizer=self.cognito_authorizer
            )
            
            # /api/orders/{orderId}/cancel resource
            api_order_cancel = api_order_id.add_resource("cancel")
            
            # PUT /api/orders/{orderId}/cancel - Cancel order
            api_order_cancel.add_method(
                "PUT",
                apigateway.LambdaIntegration(order_management_lambda),
                authorization_type=apigateway.AuthorizationType.COGNITO,
                authorizer=self.cognito_authorizer
            )
            
            print("[OK] Order management API routes configured successfully")
            print(f"  Lambda ARN: {order_management_lambda.function_arn}")
            print("  Routes created:")
            print("    - POST /api/orders")
            print("    - GET /api/orders")
            print("    - GET /api/orders/{orderId}")
            print("    - PUT /api/orders/{orderId}/status")
            print("    - PUT /api/orders/{orderId}/cancel")
        except Exception as e:
            # Order management Lambda doesn't exist yet, skip
            print(f"[WARNING] Order management Lambda not found, skipping API integration: {e}")
            pass
        
        # /api/webhooks - Webhook endpoints (no authentication required)
        api_webhooks = api_root.add_resource("webhooks")
        
        # /api/webhooks/razorpay - Razorpay payment webhooks
        if "razorpay_webhook" in self.lambda_functions:
            razorpay_webhook_resource = api_webhooks.add_resource("razorpay")
            razorpay_webhook_resource.add_method(
                "POST",
                apigateway.LambdaIntegration(self.lambda_functions["razorpay_webhook"]),
                authorization_type=apigateway.AuthorizationType.NONE  # Webhook uses signature verification
            )
        
        self.api_resources.update({
            "rest_api": self.rest_api,
            "cognito_authorizer": self.cognito_authorizer
        })
        
        # Export API Gateway ID for use by other stacks (avoids circular dependency)
        CfnOutput(
            self, "ApiGatewayId",
            value=self.rest_api.rest_api_id,
            export_name=f"AquaChain-ApiGatewayId-{self.config['environment']}",
            description="API Gateway REST API ID for CloudWatch metrics"
        )
    
    def _create_websocket_api(self) -> None:
        """
        Create WebSocket API for real-time updates
        """
        
        # WebSocket API
        self.websocket_api = apigatewayv2.CfnApi(
            self, "WebSocketAPI",
            name=get_resource_name(self.config, "api", "websocket"),
            protocol_type="WEBSOCKET",
            route_selection_expression="$request.body.action",
            description="AquaChain WebSocket API for real-time updates"
        )
        
        # WebSocket Stage
        self.websocket_stage = apigatewayv2.CfnStage(
            self, "WebSocketStage",
            api_id=self.websocket_api.ref,
            stage_name=self.config["environment"],
            auto_deploy=True,
            default_route_settings=apigatewayv2.CfnStage.RouteSettingsProperty(
                throttling_rate_limit=self.config["api_throttle_rate_limit"],
                throttling_burst_limit=self.config["api_throttle_burst_limit"]
            )
        )
        
        # WebSocket Integration
        self.websocket_integration = apigatewayv2.CfnIntegration(
            self, "WebSocketIntegration",
            api_id=self.websocket_api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{self.lambda_functions['websocket'].function_arn}/invocations"
        )
        
        # WebSocket Routes
        connect_route = apigatewayv2.CfnRoute(
            self, "ConnectRoute",
            api_id=self.websocket_api.ref,
            route_key="$connect",
            target=f"integrations/{self.websocket_integration.ref}"
        )
        
        disconnect_route = apigatewayv2.CfnRoute(
            self, "DisconnectRoute",
            api_id=self.websocket_api.ref,
            route_key="$disconnect",
            target=f"integrations/{self.websocket_integration.ref}"
        )
        
        default_route = apigatewayv2.CfnRoute(
            self, "DefaultRoute",
            api_id=self.websocket_api.ref,
            route_key="$default",
            target=f"integrations/{self.websocket_integration.ref}"
        )
        
        # Note: Lambda permission for WebSocket API is granted via IAM role
        # to avoid circular dependency between API and Compute stacks
        
        self.api_resources.update({
            "websocket_api": self.websocket_api,
            "websocket_stage": self.websocket_stage
        })
    
    def _create_waf_resources(self) -> None:
        """
        Create WAF Web ACL for API protection
        """
        
        # WAF Web ACL
        self.web_acl = waf.CfnWebACL(
            self, "WebACL",
            name=get_resource_name(self.config, "waf", "api-protection"),
            scope="REGIONAL",
            default_action=waf.CfnWebACL.DefaultActionProperty(allow={}),
            description="WAF protection for AquaChain API",
            rules=[
                # Rate limiting rule
                waf.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    statement=waf.CfnWebACL.StatementProperty(
                        rate_based_statement=waf.CfnWebACL.RateBasedStatementProperty(
                            limit=self.config["api_throttle_rate_limit"] * 2,  # Allow 2x API Gateway limit
                            aggregate_key_type="IP"
                        )
                    ),
                    action=waf.CfnWebACL.RuleActionProperty(block={}),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule"
                    )
                ),
                # AWS Managed Rules - Common Rule Set
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=2,
                    override_action=waf.CfnWebACL.OverrideActionProperty(none={}),
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet"
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="CommonRuleSetMetric"
                    )
                ),
                # AWS Managed Rules - IP Reputation List
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesAmazonIpReputationList",
                    priority=3,
                    override_action=waf.CfnWebACL.OverrideActionProperty(none={}),
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesAmazonIpReputationList"
                        )
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="IpReputationMetric"
                    )
                )
            ],
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="AquaChainWebACL"
            )
        )
        
        # Associate WAF with API Gateway
        # Add explicit dependency to ensure API Gateway stage is fully created
        self.waf_association = waf.CfnWebACLAssociation(
            self, "WebACLAssociation",
            resource_arn=f"arn:aws:apigateway:{self.region}::/restapis/{self.rest_api.rest_api_id}/stages/{self.config['environment']}",
            web_acl_arn=self.web_acl.attr_arn
        )
        # Ensure WAF association happens after API deployment is complete
        self.waf_association.node.add_dependency(self.rest_api.deployment_stage)
        
        self.api_resources.update({
            "web_acl": self.web_acl,
            "waf_association": self.waf_association
        })
        
        # Outputs
        CfnOutput(
            self, "RestAPIEndpoint",
            value=self.rest_api.url,
            description="REST API endpoint URL"
        )
        
        CfnOutput(
            self, "WebSocketAPIEndpoint",
            value=f"wss://{self.websocket_api.ref}.execute-api.{self.region}.amazonaws.com/{self.config['environment']}",
            description="WebSocket API endpoint URL"
        )
        
        CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )
        
        CfnOutput(
            self, "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )
    
    def _get_removal_policy(self):
        """Get removal policy based on environment"""
        from aws_cdk import RemovalPolicy
        return RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY