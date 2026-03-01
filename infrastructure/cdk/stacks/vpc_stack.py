"""
VPC Stack for AquaChain
Provides secure networking for Lambda functions and other resources
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_logs as logs,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct
from typing import Dict, Any


class AquaChainVPCStack(Stack):
    """
    VPC Stack with public and private subnets for secure Lambda deployment
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        
        # Create VPC
        self.vpc = self._create_vpc()
        
        # Create security groups
        self.lambda_security_group = self._create_lambda_security_group()
        self.rds_security_group = self._create_rds_security_group()
        
        # Create VPC endpoints for AWS services
        self._create_vpc_endpoints()
        
        # Export VPC information
        self._create_outputs()
    
    def _create_vpc(self) -> ec2.Vpc:
        """
        Create VPC with public and private subnets
        Cost-optimized: dev uses 1 NAT Gateway, prod uses 2 for redundancy
        """
        # Environment-based NAT Gateway configuration
        # Dev: 1 NAT Gateway (saves ~$35/month)
        # Prod: 2 NAT Gateways for high availability
        nat_gateway_count = 1 if self.config['environment'] == 'dev' else 2
        
        vpc = ec2.Vpc(
            self, "AquaChainVPC",
            vpc_name=f"aquachain-vpc-{self.config['environment']}",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,  # Use 3 availability zones for high availability
            nat_gateways=nat_gateway_count,  # Cost-optimized based on environment
            subnet_configuration=[
                # Public subnets for NAT gateways and load balancers
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                # Private subnets for Lambda functions
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                # Isolated subnets for databases (no internet access)
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # Enable VPC Flow Logs for security monitoring
        log_group = logs.LogGroup(
            self, "VPCFlowLogsGroup",
            log_group_name=f"/aws/vpc/aquachain-{self.config['environment']}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY if self.config['environment'] == 'dev' else RemovalPolicy.RETAIN
        )
        
        ec2.FlowLog(
            self, "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group),
            traffic_type=ec2.FlowLogTrafficType.ALL
        )
        
        return vpc
    
    def _create_lambda_security_group(self) -> ec2.SecurityGroup:
        """
        Create security group for Lambda functions
        """
        sg = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"aquachain-lambda-sg-{self.config['environment']}",
            description="Security group for AquaChain Lambda functions",
            allow_all_outbound=True  # Lambda needs outbound for AWS services
        )
        
        # Add tags
        sg.node.add_metadata("Purpose", "Lambda Functions")
        
        return sg
    
    def _create_rds_security_group(self) -> ec2.SecurityGroup:
        """
        Create security group for RDS (if needed in future)
        """
        sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"aquachain-rds-sg-{self.config['environment']}",
            description="Security group for AquaChain RDS instances",
            allow_all_outbound=False
        )
        
        # Allow inbound from Lambda security group
        sg.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(5432),  # PostgreSQL
            description="Allow Lambda to access RDS"
        )
        
        return sg
    
    def _create_vpc_endpoints(self):
        """
        Create VPC endpoints for AWS services to avoid NAT gateway costs
        Cost-optimized: dev uses fewer interface endpoints
        """
        # DynamoDB endpoint (Gateway endpoint - free)
        self.vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)]
        )
        
        # S3 endpoint (Gateway endpoint - free)
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)]
        )
        
        # Secrets Manager endpoint (Interface endpoint - costs apply)
        # Keep for all environments - critical for security
        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.lambda_security_group]
        )
        
        # KMS endpoint (Interface endpoint)
        # Keep for all environments - critical for encryption
        self.vpc.add_interface_endpoint(
            "KMSEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.KMS,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.lambda_security_group]
        )
        
        # CloudWatch Logs endpoint (Interface endpoint)
        # Only create for production - dev can use NAT Gateway (saves ~$7.30/month)
        if self.config['environment'] != 'dev':
            self.vpc.add_interface_endpoint(
                "CloudWatchLogsEndpoint",
                service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
                subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                security_groups=[self.lambda_security_group]
            )
    
    def _create_outputs(self):
        """
        Export VPC information for other stacks
        """
        CfnOutput(
            self, "VPCId",
            value=self.vpc.vpc_id,
            export_name=f"{Stack.of(self).stack_name}-VPCId",
            description="VPC ID"
        )
        
        CfnOutput(
            self, "LambdaSecurityGroupId",
            value=self.lambda_security_group.security_group_id,
            export_name=f"{Stack.of(self).stack_name}-LambdaSecurityGroupId",
            description="Lambda Security Group ID"
        )
        
        # Export private subnet IDs
        private_subnet_ids = [subnet.subnet_id for subnet in self.vpc.private_subnets]
        CfnOutput(
            self, "PrivateSubnetIds",
            value=",".join(private_subnet_ids),
            export_name=f"{Stack.of(self).stack_name}-PrivateSubnetIds",
            description="Private Subnet IDs (comma-separated)"
        )
