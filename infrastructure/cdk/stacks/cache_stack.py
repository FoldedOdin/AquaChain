"""
AquaChain Cache Stack
ElastiCache Redis cluster for caching frequently accessed data
"""

from aws_cdk import (
    Stack,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    aws_logs as logs,
    CfnOutput,
    RemovalPolicy,
    Fn
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name


class AquaChainCacheStack(Stack):
    """
    Cache layer stack containing ElastiCache Redis cluster
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any],
                 vpc: ec2.IVpc, lambda_security_group: ec2.ISecurityGroup, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.vpc = vpc
        self.lambda_security_group = lambda_security_group
        self.cache_resources = {}
        
        # Create Redis security group
        self.redis_security_group = self._create_redis_security_group()
        
        # Create Redis subnet group
        self.redis_subnet_group = self._create_redis_subnet_group()
        
        # Create Redis cluster
        self.redis_cluster = self._create_redis_cluster()
        
        # Create outputs
        self._create_outputs()
    
    def _create_redis_security_group(self) -> ec2.SecurityGroup:
        """
        Create security group for Redis cluster
        """
        sg = ec2.SecurityGroup(
            self, "RedisSecurityGroup",
            vpc=self.vpc,
            security_group_name=get_resource_name(self.config, "sg", "redis"),
            description="Security group for AquaChain Redis cluster",
            allow_all_outbound=False
        )
        
        # Allow inbound from Lambda security group on Redis port
        sg.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(6379),
            description="Allow Lambda functions to access Redis"
        )
        
        # Allow Redis cluster nodes to communicate with each other
        sg.add_ingress_rule(
            peer=sg,
            connection=ec2.Port.tcp(6379),
            description="Allow Redis cluster nodes to communicate"
        )
        
        return sg
    
    def _create_redis_subnet_group(self) -> elasticache.CfnSubnetGroup:
        """
        Create subnet group for Redis cluster
        """
        # Get private subnet IDs from VPC
        private_subnets = self.vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        )
        
        subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            cache_subnet_group_name=get_resource_name(self.config, "subnet-group", "redis"),
            description="Subnet group for AquaChain Redis cluster",
            subnet_ids=private_subnets.subnet_ids
        )
        
        return subnet_group
    
    def _create_redis_cluster(self) -> elasticache.CfnCacheCluster:
        """
        Create ElastiCache Redis cluster
        """
        # Determine node type based on environment
        node_type = self.config.get("redis_node_type", "cache.t3.micro")
        num_cache_nodes = self.config.get("redis_num_nodes", 1)
        
        # Create parameter group for Redis configuration
        parameter_group = elasticache.CfnParameterGroup(
            self, "RedisParameterGroup",
            cache_parameter_group_family="redis7",
            description="Parameter group for AquaChain Redis cluster",
            properties={
                "maxmemory-policy": "allkeys-lru",  # Evict least recently used keys
                "timeout": "300",  # Connection timeout in seconds
                "tcp-keepalive": "300"  # TCP keepalive interval
            }
        )
        
        # Create Redis cluster
        cluster = elasticache.CfnCacheCluster(
            self, "RedisCluster",
            cache_node_type=node_type,
            engine="redis",
            engine_version="7.0",
            num_cache_nodes=num_cache_nodes,
            cache_subnet_group_name=self.redis_subnet_group.cache_subnet_group_name,
            vpc_security_group_ids=[self.redis_security_group.security_group_id],
            cache_parameter_group_name=parameter_group.ref,
            cluster_name=get_resource_name(self.config, "cache", "redis"),
            auto_minor_version_upgrade=True,
            preferred_maintenance_window="sun:05:00-sun:06:00",
            snapshot_retention_limit=self.config.get("redis_snapshot_retention", 7) if self.config["environment"] == "prod" else 0,
            snapshot_window="03:00-04:00" if self.config["environment"] == "prod" else None,
            az_mode="single-az" if num_cache_nodes == 1 else "cross-az",
            notification_topic_arn=None,  # Can be configured for SNS notifications
            tags=[
                {
                    "key": "Environment",
                    "value": self.config["environment"]
                },
                {
                    "key": "Project",
                    "value": "AquaChain"
                },
                {
                    "key": "ManagedBy",
                    "value": "CDK"
                }
            ]
        )
        
        # Add dependencies
        cluster.add_dependency(self.redis_subnet_group)
        cluster.add_dependency(parameter_group)
        
        self.cache_resources.update({
            "redis_cluster": cluster,
            "redis_security_group": self.redis_security_group,
            "redis_subnet_group": self.redis_subnet_group,
            "redis_parameter_group": parameter_group
        })
        
        return cluster
    
    def _create_outputs(self):
        """
        Export Redis cluster information for other stacks
        """
        CfnOutput(
            self, "RedisEndpoint",
            value=self.redis_cluster.attr_redis_endpoint_address,
            export_name=f"{Stack.of(self).stack_name}-RedisEndpoint",
            description="Redis cluster endpoint address"
        )
        
        CfnOutput(
            self, "RedisPort",
            value=self.redis_cluster.attr_redis_endpoint_port,
            export_name=f"{Stack.of(self).stack_name}-RedisPort",
            description="Redis cluster port"
        )
        
        CfnOutput(
            self, "RedisSecurityGroupId",
            value=self.redis_security_group.security_group_id,
            export_name=f"{Stack.of(self).stack_name}-RedisSecurityGroupId",
            description="Redis security group ID"
        )
