"""
API Gateway Usage Plan for Rate Limiting
Implements security requirement for production deployment
"""

from aws_cdk import (
    aws_apigateway as apigateway,
    Stack
)
from constructs import Construct


class ApiGatewayUsagePlanStack(Stack):
    """
    Creates API Gateway Usage Plan with rate limiting for admin endpoints.
    
    Security Requirements (Phase 3 Production):
    - Rate limit: 100 requests/second
    - Burst limit: 200 requests
    - Quota: 10,000 requests/day
    """
    
    def __init__(self, scope: Construct, construct_id: str, api: apigateway.RestApi, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create API key for admin access
        api_key = apigateway.ApiKey(
            self, "AdminApiKey",
            api_key_name="aquachain-admin-api-key-prod",
            description="API key for admin endpoints with rate limiting",
            enabled=True
        )
        
        # Create usage plan with throttling and quota
        usage_plan = apigateway.UsagePlan(
            self, "AdminUsagePlan",
            name="aquachain-admin-usage-plan-prod",
            description="Rate limiting for admin endpoints",
            throttle=apigateway.ThrottleSettings(
                rate_limit=100,      # 100 requests per second
                burst_limit=200      # Allow bursts up to 200 requests
            ),
            quota=apigateway.QuotaSettings(
                limit=10000,         # 10,000 requests per day
                period=apigateway.Period.DAY
            )
        )
        
        # Associate API key with usage plan
        usage_plan.add_api_key(api_key)
        
        # Associate usage plan with API stage
        usage_plan.add_api_stage(
            stage=api.deployment_stage
        )
        
        # Output API key ID for reference
        self.api_key_id = api_key.key_id
        self.usage_plan_id = usage_plan.usage_plan_id
