"""
API Gateway Throttling Stack
Implements rate limiting, usage plans, and API keys
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any, List


class AquaChainAPIThrottlingStack(Stack):
    """
    API Gateway throttling and usage plan configuration
    """
    
    def __init__(self, scope: Construct, construct_id: str,
                 config: Dict[str, Any], rest_api_id: str, rest_api_stage_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.rest_api_id = rest_api_id
        self.rest_api_stage_name = rest_api_stage_name
        
        # Create usage plans
        self.usage_plans = self._create_usage_plans()
        
        # Create API keys
        self.api_keys = self._create_api_keys()
        
        # Create CloudWatch alarms
        self._create_throttling_alarms()
        
        # Create outputs
        self._create_outputs()
    
    def _create_usage_plans(self) -> Dict[str, apigateway.UsagePlan]:
        """
        Create tiered usage plans with different rate limits
        """
        usage_plans = {}
        
        # Free tier - Limited access
        usage_plans['free'] = apigateway.UsagePlan(
            self, "FreeTier",
            name=f"aquachain-free-{self.config['environment']}",
            description="Free tier with basic rate limits",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10,  # 10 requests per second
                burst_limit=20   # 20 burst capacity
            ),
            quota=apigateway.QuotaSettings(
                limit=1000,  # 1,000 requests per day
                period=apigateway.Period.DAY
            )
        )
        
        # Standard tier - Normal usage
        usage_plans['standard'] = apigateway.UsagePlan(
            self, "StandardTier",
            name=f"aquachain-standard-{self.config['environment']}",
            description="Standard tier for regular users",
            throttle=apigateway.ThrottleSettings(
                rate_limit=100,   # 100 requests per second
                burst_limit=200   # 200 burst capacity
            ),
            quota=apigateway.QuotaSettings(
                limit=10000,  # 10,000 requests per day
                period=apigateway.Period.DAY
            )
        )
        
        # Premium tier - High volume
        usage_plans['premium'] = apigateway.UsagePlan(
            self, "PremiumTier",
            name=f"aquachain-premium-{self.config['environment']}",
            description="Premium tier for high-volume users",
            throttle=apigateway.ThrottleSettings(
                rate_limit=1000,  # 1,000 requests per second
                burst_limit=2000  # 2,000 burst capacity
            ),
            quota=apigateway.QuotaSettings(
                limit=100000,  # 100,000 requests per day
                period=apigateway.Period.DAY
            )
        )
        
        # Internal tier - No limits for internal services
        usage_plans['internal'] = apigateway.UsagePlan(
            self, "InternalTier",
            name=f"aquachain-internal-{self.config['environment']}",
            description="Internal services with no rate limits",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10000,  # 10,000 requests per second
                burst_limit=20000  # 20,000 burst capacity
            )
            # No quota for internal services
        )
        
        return usage_plans
    
    def _create_api_keys(self) -> Dict[str, apigateway.ApiKey]:
        """
        Create API keys for different tiers
        """
        from aws_cdk import aws_apigateway as apigw
        
        api_keys = {}
        
        # Create API keys for each tier
        for tier_name, usage_plan in self.usage_plans.items():
            api_key = apigateway.ApiKey(
                self, f"{tier_name.capitalize()}ApiKey",
                api_key_name=f"aquachain-{tier_name}-{self.config['environment']}",
                description=f"API key for {tier_name} tier",
                enabled=True
            )
            
            # Associate API key with usage plan
            usage_plan.add_api_key(api_key)
            
            # Add API stage to usage plan using low-level construct
            # This avoids circular dependency by using string references
            cfn_usage_plan = usage_plan.node.default_child
            cfn_usage_plan.api_stages = [
                apigw.CfnUsagePlan.ApiStageProperty(
                    api_id=self.rest_api_id,
                    stage=self.rest_api_stage_name
                )
            ]
            
            api_keys[tier_name] = api_key
        
        return api_keys
    
    def _create_throttling_alarms(self):
        """
        Create CloudWatch alarms for throttling events
        """
        # Create SNS topic for throttling alerts
        throttling_topic = sns.Topic(
            self, "ThrottlingAlertsTopic",
            topic_name=f"aquachain-throttling-alerts-{self.config['environment']}",
            display_name="API Gateway Throttling Alerts"
        )
        
        # Alarm for 4XX errors (client errors including throttling)
        client_error_alarm = cloudwatch.Alarm(
            self, "ClientErrorAlarm",
            alarm_name=f"aquachain-api-4xx-{self.config['environment']}",
            alarm_description="Alert when API returns high rate of 4XX errors",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={
                    "ApiId": self.rest_api_id
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=50,  # 50 errors in 5 minutes
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        client_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(throttling_topic)
        )
        
        # Alarm for 429 (Too Many Requests) specifically
        throttle_alarm = cloudwatch.Alarm(
            self, "ThrottleAlarm",
            alarm_name=f"aquachain-api-throttle-{self.config['environment']}",
            alarm_description="Alert when API throttling occurs frequently",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Count",
                dimensions_map={
                    "ApiId": self.rest_api_id,
                    "Stage": self.rest_api_stage_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=100,  # 100 throttled requests in 5 minutes
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        throttle_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(throttling_topic)
        )
        
        # Alarm for high latency (may indicate throttling impact)
        latency_alarm = cloudwatch.Alarm(
            self, "LatencyAlarm",
            alarm_name=f"aquachain-api-latency-{self.config['environment']}",
            alarm_description="Alert when API latency is high",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Latency",
                dimensions_map={
                    "ApiId": self.rest_api_id
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=1000,  # 1 second
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        latency_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(throttling_topic)
        )
    
    def _create_outputs(self):
        """
        Export API keys and usage plan information
        """
        # Export API key IDs (values are sensitive and retrieved separately)
        for tier_name, api_key in self.api_keys.items():
            CfnOutput(
                self, f"{tier_name.capitalize()}ApiKeyId",
                value=api_key.key_id,
                export_name=f"{Stack.of(self).stack_name}-{tier_name}-ApiKeyId",
                description=f"API Key ID for {tier_name} tier"
            )
        
        # Export usage plan IDs
        for tier_name, usage_plan in self.usage_plans.items():
            CfnOutput(
                self, f"{tier_name.capitalize()}UsagePlanId",
                value=usage_plan.usage_plan_id,
                export_name=f"{Stack.of(self).stack_name}-{tier_name}-UsagePlanId",
                description=f"Usage Plan ID for {tier_name} tier"
            )


def add_method_throttling(
    method: apigateway.Method,
    rate_limit: int,
    burst_limit: int
) -> None:
    """
    Helper function to add throttling to a specific API method
    
    Args:
        method: API Gateway method
        rate_limit: Requests per second
        burst_limit: Burst capacity
    """
    cfn_method = method.node.default_child
    cfn_method.add_property_override(
        "ThrottlingRateLimit",
        rate_limit
    )
    cfn_method.add_property_override(
        "ThrottlingBurstLimit",
        burst_limit
    )


def create_method_with_throttling(
    resource: apigateway.Resource,
    http_method: str,
    integration: apigateway.Integration,
    rate_limit: int = 100,
    burst_limit: int = 200,
    require_api_key: bool = True
) -> apigateway.Method:
    """
    Create an API method with throttling configuration
    
    Args:
        resource: API Gateway resource
        http_method: HTTP method (GET, POST, etc.)
        integration: Lambda integration
        rate_limit: Requests per second
        burst_limit: Burst capacity
        require_api_key: Whether to require API key
        
    Returns:
        Configured API Gateway method
    """
    method = resource.add_method(
        http_method,
        integration,
        api_key_required=require_api_key,
        method_responses=[
            apigateway.MethodResponse(
                status_code="200",
                response_models={
                    "application/json": apigateway.Model.EMPTY_MODEL
                }
            ),
            apigateway.MethodResponse(
                status_code="400",
                response_models={
                    "application/json": apigateway.Model.ERROR_MODEL
                }
            ),
            apigateway.MethodResponse(
                status_code="429",
                response_models={
                    "application/json": apigateway.Model.ERROR_MODEL
                },
                response_parameters={
                    "method.response.header.Retry-After": True,
                    "method.response.header.X-RateLimit-Limit": True,
                    "method.response.header.X-RateLimit-Remaining": True,
                    "method.response.header.X-RateLimit-Reset": True
                }
            ),
            apigateway.MethodResponse(
                status_code="500",
                response_models={
                    "application/json": apigateway.Model.ERROR_MODEL
                }
            )
        ]
    )
    
    # Add throttling configuration
    add_method_throttling(method, rate_limit, burst_limit)
    
    return method
