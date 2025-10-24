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
    Duration,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class AquaChainApiStack(Stack):
    """
    API layer stack containing API Gateway, Cognito, and WAF
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 lambda_functions: Dict[str, Any], security_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.lambda_functions = lambda_functions
        self.security_resources = security_resources
        self.api_resources = {}
        
        # Create Cognito User Pool
        self._create_cognito_resources()
        
        # Create API Gateway
        self._create_api_gateway()
        
        # Create WebSocket API
        self._create_websocket_api()
        
        # Create WAF for API protection
        self._create_waf_resources()
    
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
                cognito.UserPoolClientIdentityProvider.COGNITO,
                cognito.UserPoolClientIdentityProvider.GOOGLE
            ],
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
        self.cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer",
            cognito_user_pools=[self.user_pool],
            authorizer_name="AquaChainAuthorizer"
        )
        
        # REST API
        self.rest_api = apigateway.RestApi(
            self, "RestAPI",
            rest_api_name=get_resource_name(self.config, "api", "rest"),
            description="AquaChain REST API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key"]
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
        
        # /api/v1 root
        api_v1 = self.rest_api.root.add_resource("api").add_resource("v1")
        
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
        
        # /api/v1/audit
        audit_resource = api_v1.add_resource("audit")
        hash_chain_resource = audit_resource.add_resource("hash-chain")
        hash_chain_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(self.lambda_functions["audit_processor"]),
            authorizer=self.cognito_authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )
        
        self.api_resources.update({
            "rest_api": self.rest_api,
            "cognito_authorizer": self.cognito_authorizer
        })
    
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
        
        # Grant API Gateway permission to invoke Lambda
        self.lambda_functions["websocket"].add_permission(
            "WebSocketAPIPermission",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{self.websocket_api.ref}/*/*"
        )
        
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
        self.waf_association = waf.CfnWebACLAssociation(
            self, "WebACLAssociation",
            resource_arn=f"arn:aws:apigateway:{self.region}::/restapis/{self.rest_api.rest_api_id}/stages/{self.config['environment']}",
            web_acl_arn=self.web_acl.attr_arn
        )
        
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