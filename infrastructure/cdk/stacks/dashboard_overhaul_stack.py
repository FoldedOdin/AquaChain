"""
AquaChain Dashboard Overhaul Infrastructure Stack
Implements the infrastructure foundation for the role-based dashboard system
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_kms as kms,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    aws_xray as xray,
    aws_elasticache as elasticache,
    RemovalPolicy,
    Duration,
    CfnOutput,
    Tags
)
from constructs import Construct
from typing import Dict, Any
from infrastructure.cdk.config.environment_config import get_resource_name

class DashboardOverhaulStack(Stack):
    """
    Dashboard Overhaul infrastructure stack containing VPC, DynamoDB tables,
    Cognito user pools with role-based groups, API Gateway, and security controls
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.dashboard_resources = {}
        
        # Create VPC and security infrastructure
        self._create_vpc_infrastructure()
        
        # Create ElastiCache Redis cluster for caching
        self._create_redis_cache()
        
        # Create KMS keys for dashboard encryption
        self._create_kms_keys()
        
        # Create DynamoDB tables for dashboard system
        self._create_dynamodb_tables()
        
        # Create Cognito user pools with role-based groups
        self._create_cognito_resources()
        
        # Create API Gateway with security controls
        self._create_api_gateway()
        
        # Create CloudWatch logging and X-Ray tracing
        self._create_monitoring_resources()
        
        # Create AWS Secrets Manager for sensitive configuration
        self._create_secrets_manager()
        
        # Create IAM roles with least-privilege policies
        self._create_iam_roles()
        
        # Tag all resources
        self._tag_resources()
    
    def _create_vpc_infrastructure(self) -> None:
        """
        Create VPC with private subnets and security groups for dashboard services
        """
        
        # VPC for dashboard services
        self.vpc = ec2.Vpc(
            self, "DashboardVPC",
            vpc_name=get_resource_name(self.config, "vpc", "dashboard"),
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # Security group for Lambda functions
        self.lambda_security_group = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for dashboard Lambda functions",
            security_group_name=get_resource_name(self.config, "sg", "lambda")
        )
        
        # Security group for API Gateway VPC endpoint
        self.api_gateway_security_group = ec2.SecurityGroup(
            self, "ApiGatewaySecurityGroup",
            vpc=self.vpc,
            description="Security group for API Gateway VPC endpoint",
            security_group_name=get_resource_name(self.config, "sg", "api-gateway")
        )
        
        # Allow HTTPS traffic from Lambda to API Gateway
        self.api_gateway_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(443),
            description="HTTPS from Lambda functions"
        )
        
        # VPC Endpoints for AWS services
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        
        self.vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )
        
        # Interface endpoints for other AWS services
        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            security_groups=[self.lambda_security_group]
        )
        
        self.vpc.add_interface_endpoint(
            "KMSEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.KMS,
            security_groups=[self.lambda_security_group]
        )
        
        self.dashboard_resources.update({
            "vpc": self.vpc,
            "lambda_security_group": self.lambda_security_group,
            "api_gateway_security_group": self.api_gateway_security_group
        })
    
    def _create_redis_cache(self) -> None:
        """
        Create ElastiCache Redis cluster for dashboard caching with fallback mechanisms
        """
        
        # Security group for Redis cluster
        self.redis_security_group = ec2.SecurityGroup(
            self, "RedisSecurityGroup",
            vpc=self.vpc,
            description="Security group for Redis cache cluster",
            security_group_name=get_resource_name(self.config, "sg", "redis")
        )
        
        # Allow Redis access from Lambda functions
        self.redis_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(6379),
            description="Redis access from Lambda functions"
        )
        
        # Redis subnet group
        self.redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            description="Subnet group for Redis cache cluster",
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.private_subnets],
            cache_subnet_group_name=get_resource_name(self.config, "subnet-group", "redis")
        )
        
        # Redis parameter group for performance optimization
        self.redis_parameter_group = elasticache.CfnParameterGroup(
            self, "RedisParameterGroup",
            cache_parameter_group_family="redis7.x",
            description="Parameter group for dashboard Redis cache",
            properties={
                "maxmemory-policy": "allkeys-lru",  # Evict least recently used keys
                "timeout": "300",  # Connection timeout
                "tcp-keepalive": "60",  # Keep connections alive
                "maxclients": "1000"  # Maximum client connections
            }
        )
        
        # Redis replication group (cluster)
        self.redis_cluster = elasticache.CfnReplicationGroup(
            self, "DashboardRedisCluster",
            replication_group_description="Dashboard caching Redis cluster",
            replication_group_id=get_resource_name(self.config, "redis", "dashboard"),
            cache_node_type=self.config["redis_node_type"],
            num_cache_clusters=self.config["redis_num_nodes"],
            engine="redis",
            engine_version="7.0",
            port=6379,
            cache_parameter_group_name=self.redis_parameter_group.ref,
            cache_subnet_group_name=self.redis_subnet_group.ref,
            security_group_ids=[self.redis_security_group.security_group_id],
            at_rest_encryption_enabled=True,
            transit_encryption_enabled=True,
            auth_token=None,  # Will use VPC security for access control
            automatic_failover_enabled=self.config["redis_num_nodes"] > 1,
            multi_az_enabled=self.config["redis_num_nodes"] > 1,
            preferred_cache_cluster_a_zs=self.vpc.availability_zones[:self.config["redis_num_nodes"]],
            snapshot_retention_limit=self.config["redis_snapshot_retention"],
            snapshot_window="03:00-05:00",  # During low usage hours
            preferred_maintenance_window="sun:05:00-sun:07:00",  # Sunday maintenance window
            notification_topic_arn=None,  # Will be set up with monitoring
            tags=[
                elasticache.CfnReplicationGroup.TagProperty(
                    key="Name",
                    value=get_resource_name(self.config, "redis", "dashboard")
                ),
                elasticache.CfnReplicationGroup.TagProperty(
                    key="Environment",
                    value=self.config["environment"]
                ),
                elasticache.CfnReplicationGroup.TagProperty(
                    key="Purpose",
                    value="DashboardCaching"
                )
            ]
        )
        
        # CloudWatch alarms for Redis monitoring
        self._create_redis_monitoring()
        
        self.dashboard_resources.update({
            "redis_security_group": self.redis_security_group,
            "redis_subnet_group": self.redis_subnet_group,
            "redis_parameter_group": self.redis_parameter_group,
            "redis_cluster": self.redis_cluster
        })
    
    def _create_redis_monitoring(self) -> None:
        """
        Create CloudWatch alarms for Redis cache monitoring
        """
        from aws_cdk import aws_cloudwatch as cloudwatch
        
        # CPU utilization alarm
        cloudwatch.Alarm(
            self, "RedisCPUAlarm",
            alarm_name=f"{get_resource_name(self.config, 'alarm', 'redis-cpu')}",
            alarm_description="Redis cluster CPU utilization is high",
            metric=cloudwatch.Metric(
                namespace="AWS/ElastiCache",
                metric_name="CPUUtilization",
                dimensions_map={
                    "CacheClusterId": self.redis_cluster.replication_group_id
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # Memory utilization alarm
        cloudwatch.Alarm(
            self, "RedisMemoryAlarm",
            alarm_name=f"{get_resource_name(self.config, 'alarm', 'redis-memory')}",
            alarm_description="Redis cluster memory utilization is high",
            metric=cloudwatch.Metric(
                namespace="AWS/ElastiCache",
                metric_name="DatabaseMemoryUsagePercentage",
                dimensions_map={
                    "CacheClusterId": self.redis_cluster.replication_group_id
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=85,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        # Cache hit ratio alarm (should be high)
        cloudwatch.Alarm(
            self, "RedisCacheHitRatioAlarm",
            alarm_name=f"{get_resource_name(self.config, 'alarm', 'redis-hit-ratio')}",
            alarm_description="Redis cache hit ratio is low",
            metric=cloudwatch.Metric(
                namespace="AWS/ElastiCache",
                metric_name="CacheHitRate",
                dimensions_map={
                    "CacheClusterId": self.redis_cluster.replication_group_id
                },
                statistic="Average",
                period=Duration.minutes(15)
            ),
            threshold=0.8,  # 80% hit rate threshold
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
        )
    
    def _create_kms_keys(self) -> None:
        """
        Create KMS keys for dashboard data encryption and audit signing
        """
        
        # Dashboard data encryption key
        self.dashboard_data_key = kms.Key(
            self, "DashboardDataKey",
            description="Dashboard system data encryption key",
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            enable_key_rotation=True
        )
        
        kms.Alias(
            self, "DashboardDataKeyAlias",
            alias_name=f"alias/{get_resource_name(self.config, 'kms', 'dashboard-data')}",
            target_key=self.dashboard_data_key
        )
        
        # Audit trail signing key (asymmetric for digital signatures)
        self.audit_signing_key = kms.Key(
            self, "AuditSigningKey",
            description="Dashboard audit trail signing key",
            key_usage=kms.KeyUsage.SIGN_VERIFY,
            key_spec=kms.KeySpec.RSA_2048,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        kms.Alias(
            self, "AuditSigningKeyAlias",
            alias_name=f"alias/{get_resource_name(self.config, 'kms', 'audit-signing')}",
            target_key=self.audit_signing_key
        )
        
        self.dashboard_resources.update({
            "dashboard_data_key": self.dashboard_data_key,
            "audit_signing_key": self.audit_signing_key
        })
    
    def _create_dynamodb_tables(self) -> None:
        """
        Create DynamoDB tables for the dashboard overhaul system
        """
        
        # Users table with role-based access patterns
        self.dashboard_users_table = dynamodb.Table(
            self, "DashboardUsersTable",
            table_name=get_resource_name(self.config, "table", "dashboard-users"),
            partition_key=dynamodb.Attribute(
                name="PK",  # USER#{userId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # PROFILE | ROLE#{roleId}
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dashboard_data_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for role-based queries
        self.dashboard_users_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",  # ROLE#{roleId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",  # USER#{userId}
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Inventory table for Operations Dashboard
        self.inventory_table = dynamodb.Table(
            self, "InventoryTable",
            table_name=get_resource_name(self.config, "table", "inventory"),
            partition_key=dynamodb.Attribute(
                name="PK",  # ITEM#{itemId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # CURRENT | HISTORY#{timestamp}
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dashboard_data_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for warehouse-based queries
        self.inventory_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",  # WAREHOUSE#{warehouseId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",  # ITEM#{itemId}
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Purchase Orders table for Procurement Dashboard
        self.purchase_orders_table = dynamodb.Table(
            self, "PurchaseOrdersTable",
            table_name=get_resource_name(self.config, "table", "purchase-orders"),
            partition_key=dynamodb.Attribute(
                name="PK",  # ORDER#{orderId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # CURRENT | HISTORY#{timestamp}
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dashboard_data_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for status-based queries
        self.purchase_orders_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",  # STATUS#{status}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",  # CREATED#{createdAt}
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Budget table for financial controls
        self.budget_table = dynamodb.Table(
            self, "BudgetTable",
            table_name=get_resource_name(self.config, "table", "budget"),
            partition_key=dynamodb.Attribute(
                name="PK",  # BUDGET#{category}#{period}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # ALLOCATION | UTILIZATION#{timestamp}
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dashboard_data_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for period-based queries
        self.budget_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",  # PERIOD#{period}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",  # CATEGORY#{category}
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Workflows table for approval processes
        self.workflows_table = dynamodb.Table(
            self, "WorkflowsTable",
            table_name=get_resource_name(self.config, "table", "workflows"),
            partition_key=dynamodb.Attribute(
                name="PK",  # WORKFLOW#{workflowId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # STATE#{timestamp} | AUDIT#{timestamp}
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dashboard_data_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for workflow type and state queries
        self.workflows_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",  # TYPE#{workflowType}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",  # STATE#{currentState}#{createdAt}
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Audit table for immutable audit trail
        self.dashboard_audit_table = dynamodb.Table(
            self, "DashboardAuditTable",
            table_name=get_resource_name(self.config, "table", "dashboard-audit"),
            partition_key=dynamodb.Attribute(
                name="PK",  # AUDIT#{date}#{userId}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # ACTION#{timestamp}#{actionId}
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dashboard_data_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN,  # Always retain audit data
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for resource-based audit queries
        self.dashboard_audit_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK",  # RESOURCE#{resource}
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK",  # TIMESTAMP#{timestamp}
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.dashboard_resources.update({
            "dashboard_users_table": self.dashboard_users_table,
            "inventory_table": self.inventory_table,
            "purchase_orders_table": self.purchase_orders_table,
            "budget_table": self.budget_table,
            "workflows_table": self.workflows_table,
            "dashboard_audit_table": self.dashboard_audit_table
        })
    
    def _create_cognito_resources(self) -> None:
        """
        Create Cognito user pools with role-based groups for dashboard access
        """
        
        # Dashboard User Pool
        self.dashboard_user_pool = cognito.UserPool(
            self, "DashboardUserPool",
            user_pool_name=get_resource_name(self.config, "pool", "dashboard-users"),
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=False
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            mfa=cognito.Mfa.REQUIRED,  # Required for dashboard access
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # User Pool Domain
        self.dashboard_user_pool.add_domain(
            "DashboardUserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=get_resource_name(self.config, "auth", "dashboard")
            )
        )
        
        # Role-based User Pool Groups
        
        # Inventory Manager Group
        self.inventory_manager_group = cognito.CfnUserPoolGroup(
            self, "InventoryManagerGroup",
            user_pool_id=self.dashboard_user_pool.user_pool_id,
            group_name="inventory-managers",
            description="Inventory Manager role with inventory planning and reorder permissions"
        )
        
        # Warehouse Manager Group
        self.warehouse_manager_group = cognito.CfnUserPoolGroup(
            self, "WarehouseManagerGroup",
            user_pool_id=self.dashboard_user_pool.user_pool_id,
            group_name="warehouse-managers",
            description="Warehouse Manager role with receiving/dispatch workflow permissions"
        )
        
        # Supplier Coordinator Group
        self.supplier_coordinator_group = cognito.CfnUserPoolGroup(
            self, "SupplierCoordinatorGroup",
            user_pool_id=self.dashboard_user_pool.user_pool_id,
            group_name="supplier-coordinators",
            description="Supplier Coordinator role with supplier management permissions"
        )
        
        # Procurement & Finance Controller Group
        self.procurement_finance_group = cognito.CfnUserPoolGroup(
            self, "ProcurementFinanceGroup",
            user_pool_id=self.dashboard_user_pool.user_pool_id,
            group_name="procurement-finance-controllers",
            description="Procurement & Finance Controller role with approval and budget permissions"
        )
        
        # Administrator Group
        self.administrator_group = cognito.CfnUserPoolGroup(
            self, "AdministratorGroup",
            user_pool_id=self.dashboard_user_pool.user_pool_id,
            group_name="administrators",
            description="Administrator role with system configuration and oversight permissions"
        )
        
        # User Pool Client for dashboard applications
        self.dashboard_user_pool_client = cognito.UserPoolClient(
            self, "DashboardUserPoolClient",
            user_pool=self.dashboard_user_pool,
            user_pool_client_name=get_resource_name(self.config, "client", "dashboard"),
            generate_secret=False,  # For web applications
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False  # More secure
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=[
                    f"https://{self.config['domain_name']}/dashboard/auth/callback",
                    "http://localhost:3000/dashboard/auth/callback"  # For development
                ],
                logout_urls=[
                    f"https://{self.config['domain_name']}/dashboard/auth/logout",
                    "http://localhost:3000/dashboard/auth/logout"
                ]
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30)
        )
        
        # Identity Pool for AWS resource access
        self.dashboard_identity_pool = cognito.CfnIdentityPool(
            self, "DashboardIdentityPool",
            identity_pool_name=get_resource_name(self.config, "identity", "dashboard"),
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.dashboard_user_pool_client.user_pool_client_id,
                    provider_name=self.dashboard_user_pool.user_pool_provider_name
                )
            ]
        )
        
        self.dashboard_resources.update({
            "dashboard_user_pool": self.dashboard_user_pool,
            "dashboard_user_pool_client": self.dashboard_user_pool_client,
            "dashboard_identity_pool": self.dashboard_identity_pool,
            "inventory_manager_group": self.inventory_manager_group,
            "warehouse_manager_group": self.warehouse_manager_group,
            "supplier_coordinator_group": self.supplier_coordinator_group,
            "procurement_finance_group": self.procurement_finance_group,
            "administrator_group": self.administrator_group
        })
    
    def _create_api_gateway(self) -> None:
        """
        Create API Gateway with proper CORS and security headers
        """
        
        # REST API for dashboard services
        self.dashboard_api = apigateway.RestApi(
            self, "DashboardAPI",
            rest_api_name=get_resource_name(self.config, "api", "dashboard"),
            description="AquaChain Dashboard Overhaul API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["https://" + self.config['domain_name'], "http://localhost:3000"],
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                    "X-Requested-With"
                ],
                allow_credentials=True,
                max_age=Duration.hours(1)
            ),
            deploy_options=apigateway.StageOptions(
                stage_name=self.config["environment"],
                throttling_rate_limit=self.config["api_throttle_rate_limit"],
                throttling_burst_limit=self.config["api_throttle_burst_limit"],
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                tracing_enabled=True  # Enable X-Ray tracing
            ),
            cloud_watch_role=True,
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            )
        )
        
        # Cognito Authorizer - create as separate construct
        self.dashboard_authorizer = apigateway.CfnAuthorizer(
            self, "DashboardAuthorizer",
            rest_api_id=self.dashboard_api.rest_api_id,
            name="DashboardAuthorizer",
            type="COGNITO_USER_POOLS",
            identity_source="method.request.header.Authorization",
            provider_arns=[self.dashboard_user_pool.user_pool_arn]
        )
        
        # API Gateway Method Response Models for consistent error handling
        error_response_model = self.dashboard_api.add_model(
            "ErrorResponseModel",
            content_type="application/json",
            model_name="ErrorResponse",
            schema=apigateway.JsonSchema(
                schema=apigateway.JsonSchemaVersion.DRAFT4,
                type=apigateway.JsonSchemaType.OBJECT,
                properties={
                    "error": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING
                    ),
                    "message": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING
                    ),
                    "correlationId": apigateway.JsonSchema(
                        type=apigateway.JsonSchemaType.STRING
                    )
                },
                required=["error", "message"]
            )
        )
        
        # API Resources structure
        # /dashboard/api/v1
        dashboard_root = self.dashboard_api.root.add_resource("dashboard")
        api_root = dashboard_root.add_resource("api")
        v1_root = api_root.add_resource("v1")
        
        # Add security headers to all responses
        self._add_security_headers_to_api(self.dashboard_api)
        
        self.dashboard_resources.update({
            "dashboard_api": self.dashboard_api,
            "dashboard_authorizer": self.dashboard_authorizer,
            "error_response_model": error_response_model,
            "api_v1_root": v1_root
        })
    
    def _add_security_headers_to_api(self, api: apigateway.RestApi) -> None:
        """
        Add security headers to API Gateway responses
        """
        
        # Add gateway responses with security headers
        security_headers = {
            "gatewayresponse.header.Strict-Transport-Security": "'max-age=31536000; includeSubDomains'",
            "gatewayresponse.header.X-Content-Type-Options": "'nosniff'",
            "gatewayresponse.header.X-Frame-Options": "'DENY'",
            "gatewayresponse.header.X-XSS-Protection": "'1; mode=block'",
            "gatewayresponse.header.Referrer-Policy": "'strict-origin-when-cross-origin'",
            "gatewayresponse.header.Content-Security-Policy": "'default-src \\'self\\'; script-src \\'self\\' \\'unsafe-inline\\'; style-src \\'self\\' \\'unsafe-inline\\''",
        }
        
        # Apply security headers to common error responses
        for response_type in [
            apigateway.ResponseType.DEFAULT_4_XX,
            apigateway.ResponseType.DEFAULT_5_XX,
            apigateway.ResponseType.UNAUTHORIZED,
            apigateway.ResponseType.ACCESS_DENIED
        ]:
            api.add_gateway_response(
                f"SecurityHeaders{response_type.response_type}",
                type=response_type,
                response_headers=security_headers
            )
    
    def _create_monitoring_resources(self) -> None:
        """
        Create CloudWatch logging and X-Ray tracing resources
        """
        
        # CloudWatch Log Groups for dashboard services
        self.dashboard_log_group = logs.LogGroup(
            self, "DashboardLogGroup",
            log_group_name=f"/aws/lambda/{get_resource_name(self.config, 'function', 'dashboard')}",
            retention=logs.RetentionDays.ONE_MONTH if self.config["environment"] == "dev" else logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.rbac_log_group = logs.LogGroup(
            self, "RBACLogGroup",
            log_group_name=f"/aws/lambda/{get_resource_name(self.config, 'function', 'rbac')}",
            retention=logs.RetentionDays.ONE_MONTH if self.config["environment"] == "dev" else logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.audit_log_group = logs.LogGroup(
            self, "AuditLogGroup",
            log_group_name=f"/aws/lambda/{get_resource_name(self.config, 'function', 'audit')}",
            retention=logs.RetentionDays.ONE_YEAR,  # Longer retention for audit logs
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # API Gateway CloudWatch Log Group
        self.api_gateway_log_group = logs.LogGroup(
            self, "ApiGatewayLogGroup",
            log_group_name=f"API-Gateway-Execution-Logs_{self.dashboard_api.rest_api_id}/{self.config['environment']}",
            retention=logs.RetentionDays.ONE_MONTH if self.config["environment"] == "dev" else logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.dashboard_resources.update({
            "dashboard_log_group": self.dashboard_log_group,
            "rbac_log_group": self.rbac_log_group,
            "audit_log_group": self.audit_log_group,
            "api_gateway_log_group": self.api_gateway_log_group
        })
    
    def _create_secrets_manager(self) -> None:
        """
        Create AWS Secrets Manager for sensitive configuration
        """
        
        # Dashboard configuration secrets
        self.dashboard_secrets = secretsmanager.Secret(
            self, "DashboardSecrets",
            secret_name=get_resource_name(self.config, "secret", "dashboard-config"),
            description="Dashboard system sensitive configuration",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"jwt_secret": "placeholder"}',
                generate_string_key="jwt_secret",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                password_length=32
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # ML service API keys (for forecast integration)
        self.ml_service_secrets = secretsmanager.Secret(
            self, "MLServiceSecrets",
            secret_name=get_resource_name(self.config, "secret", "ml-service"),
            description="ML service API keys and configuration",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": "placeholder", "endpoint": "placeholder"}',
                generate_string_key="api_key",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                password_length=32
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        # External service integration secrets
        self.external_service_secrets = secretsmanager.Secret(
            self, "ExternalServiceSecrets",
            secret_name=get_resource_name(self.config, "secret", "external-services"),
            description="External service integration secrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"notification_webhook": "placeholder", "email_api_key": "placeholder"}',
                generate_string_key="notification_webhook",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                password_length=32
            ),
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY
        )
        
        self.dashboard_resources.update({
            "dashboard_secrets": self.dashboard_secrets,
            "ml_service_secrets": self.ml_service_secrets,
            "external_service_secrets": self.external_service_secrets
        })
    
    def _create_iam_roles(self) -> None:
        """
        Create IAM roles with least-privilege policies for dashboard services
        """
        
        # RBAC Service Role
        self.rbac_service_role = iam.Role(
            self, "RBACServiceRole",
            role_name=get_resource_name(self.config, "role", "rbac-service"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ]
        )
        
        # RBAC service permissions
        self.rbac_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminListGroupsForUser",
                    "cognito-idp:GetGroup"
                ],
                resources=[self.dashboard_user_pool.user_pool_arn]
            )
        )
        
        self.rbac_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.dashboard_users_table.table_arn,
                    f"{self.dashboard_users_table.table_arn}/index/*"
                ]
            )
        )
        
        # Audit Service Role
        self.audit_service_role = iam.Role(
            self, "AuditServiceRole",
            role_name=get_resource_name(self.config, "role", "audit-service"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ]
        )
        
        # Audit service permissions
        self.audit_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.dashboard_audit_table.table_arn,
                    f"{self.dashboard_audit_table.table_arn}/index/*"
                ]
            )
        )
        
        self.audit_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "kms:Sign",
                    "kms:Verify",
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                resources=[
                    self.audit_signing_key.key_arn,
                    self.dashboard_data_key.key_arn
                ]
            )
        )
        
        # Business Logic Service Role (for inventory, procurement, etc.)
        self.business_logic_role = iam.Role(
            self, "BusinessLogicRole",
            role_name=get_resource_name(self.config, "role", "business-logic"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ]
        )
        
        # Business logic permissions
        business_tables = [
            self.inventory_table,
            self.purchase_orders_table,
            self.budget_table,
            self.workflows_table
        ]
        
        for table in business_tables:
            self.business_logic_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem"
                    ],
                    resources=[
                        table.table_arn,
                        f"{table.table_arn}/index/*"
                    ]
                )
            )
        
        # Secrets Manager permissions for all roles
        for role in [self.rbac_service_role, self.audit_service_role, self.business_logic_role]:
            role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:GetSecretValue"
                    ],
                    resources=[
                        self.dashboard_secrets.secret_arn,
                        self.ml_service_secrets.secret_arn,
                        self.external_service_secrets.secret_arn
                    ]
                )
            )
            
            role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:GenerateDataKey"
                    ],
                    resources=[self.dashboard_data_key.key_arn]
                )
            )
        
        # ElastiCache permissions for business logic services
        self.business_logic_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "elasticache:DescribeReplicationGroups",
                    "elasticache:DescribeCacheClusters"
                ],
                resources=["*"]  # These are read-only describe operations
            )
        )
        
        self.dashboard_resources.update({
            "rbac_service_role": self.rbac_service_role,
            "audit_service_role": self.audit_service_role,
            "business_logic_role": self.business_logic_role
        })
    
    def _tag_resources(self) -> None:
        """
        Tag all resources for the dashboard overhaul
        """
        
        tags = {
            "Project": "AquaChain",
            "Component": "DashboardOverhaul",
            "Environment": self.config["environment"],
            "ManagedBy": "CDK",
            "CostCenter": "Engineering",
            "Compliance": "Required"
        }
        
        for key, value in tags.items():
            Tags.of(self).add(key, value)
    
    @property
    def outputs(self) -> Dict[str, str]:
        """
        Return important stack outputs
        """
        
        # Create CloudFormation outputs
        CfnOutput(
            self, "DashboardAPIEndpoint",
            value=self.dashboard_api.url,
            description="Dashboard API endpoint URL"
        )
        
        CfnOutput(
            self, "DashboardUserPoolId",
            value=self.dashboard_user_pool.user_pool_id,
            description="Dashboard Cognito User Pool ID"
        )
        
        CfnOutput(
            self, "DashboardUserPoolClientId",
            value=self.dashboard_user_pool_client.user_pool_client_id,
            description="Dashboard Cognito User Pool Client ID"
        )
        
        CfnOutput(
            self, "DashboardVPCId",
            value=self.vpc.vpc_id,
            description="Dashboard VPC ID"
        )
        
        CfnOutput(
            self, "DashboardDataKeyId",
            value=self.dashboard_data_key.key_id,
            description="Dashboard data encryption key ID"
        )
        
        CfnOutput(
            self, "RedisClusterEndpoint",
            value=self.redis_cluster.attr_primary_end_point_address,
            description="Redis cluster primary endpoint"
        )
        
        CfnOutput(
            self, "RedisClusterPort",
            value=self.redis_cluster.attr_primary_end_point_port,
            description="Redis cluster port"
        )
        
        return {
            "api_endpoint": self.dashboard_api.url,
            "user_pool_id": self.dashboard_user_pool.user_pool_id,
            "user_pool_client_id": self.dashboard_user_pool_client.user_pool_client_id,
            "vpc_id": self.vpc.vpc_id,
            "data_key_id": self.dashboard_data_key.key_id,
            "redis_endpoint": self.redis_cluster.attr_primary_end_point_address,
            "redis_port": self.redis_cluster.attr_primary_end_point_port
        }