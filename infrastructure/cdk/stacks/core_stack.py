"""
AquaChain Core Stack
Core infrastructure components like VPC, networking, and shared resources
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_logs as logs,
    RemovalPolicy
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class AquaChainCoreStack(Stack):
    """
    Core infrastructure stack for networking and shared resources
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.core_resources = {}
        
        # Create VPC if needed (for SageMaker, RDS, etc.)
        self._create_vpc()
        
        # Create shared log groups
        self._create_log_groups()
    
    def _get_retention_days(self, days: int) -> logs.RetentionDays:
        """Convert numeric days to valid RetentionDays enum"""
        # Map common values to valid enum values
        retention_mapping = {
            1: logs.RetentionDays.ONE_DAY,
            3: logs.RetentionDays.THREE_DAYS,
            5: logs.RetentionDays.FIVE_DAYS,
            7: logs.RetentionDays.ONE_WEEK,
            14: logs.RetentionDays.TWO_WEEKS,
            30: logs.RetentionDays.ONE_MONTH,
            60: logs.RetentionDays.TWO_MONTHS,
            90: logs.RetentionDays.THREE_MONTHS,
            120: logs.RetentionDays.FOUR_MONTHS,
            150: logs.RetentionDays.FIVE_MONTHS,
            180: logs.RetentionDays.SIX_MONTHS,
            365: logs.RetentionDays.ONE_YEAR,
            400: logs.RetentionDays.THIRTEEN_MONTHS,
            545: logs.RetentionDays.EIGHTEEN_MONTHS,
            731: logs.RetentionDays.TWO_YEARS,
            1827: logs.RetentionDays.FIVE_YEARS,
            3653: logs.RetentionDays.TEN_YEARS
        }
        
        # Return exact match or closest valid value
        if days in retention_mapping:
            return retention_mapping[days]
        
        # Find closest valid value
        valid_days = sorted(retention_mapping.keys())
        closest = min(valid_days, key=lambda x: abs(x - days))
        return retention_mapping[closest]
    
    def _create_vpc(self) -> None:
        """
        Create VPC for resources that need it (optional for serverless architecture)
        """
        
        # For production, we might need VPC for SageMaker, RDS, or other services
        if self.config["environment"] == "prod":
            self.vpc = ec2.Vpc(
                self, "AquaChainVPC",
                vpc_name=get_resource_name(self.config, "vpc", "main"),
                max_azs=3,
                cidr="10.0.0.0/16",
                subnet_configuration=[
                    ec2.SubnetConfiguration(
                        name="Public",
                        subnet_type=ec2.SubnetType.PUBLIC,
                        cidr_mask=24
                    ),
                    ec2.SubnetConfiguration(
                        name="Private",
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                        cidr_mask=24
                    ),
                    ec2.SubnetConfiguration(
                        name="Isolated",
                        subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                        cidr_mask=24
                    )
                ],
                enable_dns_hostnames=True,
                enable_dns_support=True
            )
            
            # VPC Flow Logs for security monitoring
            self.vpc_flow_logs = ec2.FlowLog(
                self, "VPCFlowLogs",
                resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
                destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                    logs.LogGroup(
                        self, "VPCFlowLogsGroup",
                        log_group_name=f"/aws/vpc/flowlogs/{get_resource_name(self.config, 'vpc', 'main')}",
                        retention=logs.RetentionDays.ONE_MONTH,
                        removal_policy=RemovalPolicy.DESTROY
                    )
                )
            )
            
            self.core_resources["vpc"] = self.vpc
            self.core_resources["vpc_flow_logs"] = self.vpc_flow_logs
        else:
            # For dev/staging, we'll use serverless architecture without VPC
            self.vpc = None
    
    def _create_log_groups(self) -> None:
        """
        Create shared CloudWatch log groups
        """
        
        # Application log group
        self.app_log_group = logs.LogGroup(
            self, "ApplicationLogs",
            log_group_name=f"/aws/lambda/{get_resource_name(self.config, 'app', 'logs')}",
            retention=self._get_retention_days(self.config["log_retention_days"]),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN
        )
        
        # API Gateway log group
        self.api_log_group = logs.LogGroup(
            self, "APIGatewayLogs",
            log_group_name=f"/aws/apigateway/{get_resource_name(self.config, 'api', 'logs')}",
            retention=self._get_retention_days(self.config["log_retention_days"]),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN
        )
        
        # IoT Core log group
        self.iot_log_group = logs.LogGroup(
            self, "IoTCoreLogs",
            log_group_name=f"/aws/iot/{get_resource_name(self.config, 'iot', 'logs')}",
            retention=self._get_retention_days(self.config["log_retention_days"]),
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN
        )
        
        self.core_resources.update({
            "app_log_group": self.app_log_group,
            "api_log_group": self.api_log_group,
            "iot_log_group": self.iot_log_group
        })