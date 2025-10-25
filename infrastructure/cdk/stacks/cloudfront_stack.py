"""
CloudFront Distribution Stack
Global CDN for frontend with WAF protection
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_wafv2 as waf,
    aws_iam as iam
)
from constructs import Construct
from typing import Dict, Any


class AquaChainCloudFrontStack(Stack):
    """
    CloudFront distribution with S3 origin, WAF, and SSL
    """
    
    def __init__(self, scope: Construct, construct_id: str,
                 config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        
        # Create S3 bucket for frontend
        self.frontend_bucket = self._create_frontend_bucket()
        
        # Create CloudFront Origin Access Identity
        self.oai = self._create_origin_access_identity()
        
        # Create WAF Web ACL
        self.web_acl = self._create_waf_acl()
        
        # Create SSL certificate (if domain configured)
        self.certificate = self._create_certificate()
        
        # Create CloudFront distribution
        self.distribution = self._create_distribution()
        
        # Create Route53 records (if domain configured)
        self._create_dns_records()
        
        # Deploy frontend files
        self._deploy_frontend()
        
        # Create outputs
        self._create_outputs()
    
    def _create_frontend_bucket(self) -> s3.Bucket:
        """
        Create S3 bucket for frontend hosting
        """
        bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=f"aquachain-frontend-{self.config['environment']}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY if self.config['environment'] == 'dev' else RemovalPolicy.RETAIN,
            auto_delete_objects=self.config['environment'] == 'dev',
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(30),
                    enabled=True
                )
            ]
        )
        
        return bucket
    
    def _create_origin_access_identity(self) -> cloudfront.OriginAccessIdentity:
        """
        Create CloudFront Origin Access Identity for S3 access
        """
        oai = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment=f"OAI for AquaChain frontend {self.config['environment']}"
        )
        
        # Grant CloudFront read access to S3 bucket
        self.frontend_bucket.grant_read(oai)
        
        return oai
    
    def _create_waf_acl(self) -> waf.CfnWebACL:
        """
        Create WAF Web ACL for DDoS and bot protection
        """
        web_acl = waf.CfnWebACL(
            self, "WebACL",
            scope="CLOUDFRONT",  # Must be CLOUDFRONT for CloudFront distributions
            default_action=waf.CfnWebACL.DefaultActionProperty(
                allow={}
            ),
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name=f"aquachain-waf-{self.config['environment']}",
                sampled_requests_enabled=True
            ),
            name=f"aquachain-waf-{self.config['environment']}",
            rules=[
                # Rate limiting rule
                waf.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    statement=waf.CfnWebACL.StatementProperty(
                        rate_based_statement=waf.CfnWebACL.RateBasedStatementProperty(
                            limit=2000,  # 2000 requests per 5 minutes
                            aggregate_key_type="IP"
                        )
                    ),
                    action=waf.CfnWebACL.RuleActionProperty(
                        block={}
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule",
                        sampled_requests_enabled=True
                    )
                ),
                # AWS Managed Rules - Common Rule Set
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=2,
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet"
                        )
                    ),
                    override_action=waf.CfnWebACL.OverrideActionProperty(
                        none={}
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesCommonRuleSet",
                        sampled_requests_enabled=True
                    )
                ),
                # AWS Managed Rules - Known Bad Inputs
                waf.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesKnownBadInputsRuleSet",
                    priority=3,
                    statement=waf.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesKnownBadInputsRuleSet"
                        )
                    ),
                    override_action=waf.CfnWebACL.OverrideActionProperty(
                        none={}
                    ),
                    visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesKnownBadInputsRuleSet",
                        sampled_requests_enabled=True
                    )
                ),
                # Geo-blocking (optional - block specific countries)
                # Uncomment and configure if needed
                # waf.CfnWebACL.RuleProperty(
                #     name="GeoBlockRule",
                #     priority=4,
                #     statement=waf.CfnWebACL.StatementProperty(
                #         geo_match_statement=waf.CfnWebACL.GeoMatchStatementProperty(
                #             country_codes=["CN", "RU"]  # Block China and Russia
                #         )
                #     ),
                #     action=waf.CfnWebACL.RuleActionProperty(
                #         block={}
                #     ),
                #     visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                #         cloud_watch_metrics_enabled=True,
                #         metric_name="GeoBlockRule",
                #         sampled_requests_enabled=True
                #     )
                # )
            ]
        )
        
        return web_acl
    
    def _create_certificate(self) -> acm.Certificate:
        """
        Create SSL certificate for custom domain
        Note: Certificate must be in us-east-1 for CloudFront
        """
        domain_name = self.config.get('domain_name')
        
        if not domain_name:
            return None
        
        # Certificate must be created in us-east-1 for CloudFront
        certificate = acm.Certificate(
            self, "Certificate",
            domain_name=domain_name,
            subject_alternative_names=[f"*.{domain_name}"],
            validation=acm.CertificateValidation.from_dns()
        )
        
        return certificate
    
    def _create_distribution(self) -> cloudfront.Distribution:
        """
        Create CloudFront distribution
        """
        # Cache policy for SPA
        cache_policy = cloudfront.CachePolicy(
            self, "SPACachePolicy",
            cache_policy_name=f"aquachain-spa-{self.config['environment']}",
            comment="Cache policy for Single Page Application",
            default_ttl=Duration.hours(24),
            min_ttl=Duration.seconds(0),
            max_ttl=Duration.days(365),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )
        
        # Origin request policy
        origin_request_policy = cloudfront.OriginRequestPolicy(
            self, "SPAOriginRequestPolicy",
            origin_request_policy_name=f"aquachain-spa-origin-{self.config['environment']}",
            comment="Origin request policy for SPA",
            cookie_behavior=cloudfront.OriginRequestCookieBehavior.none(),
            header_behavior=cloudfront.OriginRequestHeaderBehavior.none(),
            query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.none()
        )
        
        # Response headers policy
        response_headers_policy = cloudfront.ResponseHeadersPolicy(
            self, "SecurityHeadersPolicy",
            response_headers_policy_name=f"aquachain-security-headers-{self.config['environment']}",
            comment="Security headers for AquaChain frontend",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(
                    override=True
                ),
                frame_options=cloudfront.ResponseHeadersFrameOptions(
                    frame_option=cloudfront.HeadersFrameOption.DENY,
                    override=True
                ),
                referrer_policy=cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
                    override=True
                ),
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.days(365),
                    include_subdomains=True,
                    override=True
                ),
                xss_protection=cloudfront.ResponseHeadersXSSProtection(
                    protection=True,
                    mode_block=True,
                    override=True
                )
            )
        )
        
        # Create distribution
        distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_identity=self.oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress=True,
                cache_policy=cache_policy,
                origin_request_policy=origin_request_policy,
                response_headers_policy=response_headers_policy
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                )
            ],
            certificate=self.certificate,
            domain_names=[self.config['domain_name']] if self.config.get('domain_name') else None,
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # US, Canada, Europe
            enable_logging=True,
            log_bucket=self._create_logs_bucket(),
            log_file_prefix="cloudfront/",
            web_acl_id=self.web_acl.attr_arn,
            comment=f"AquaChain Frontend {self.config['environment']}"
        )
        
        return distribution
    
    def _create_logs_bucket(self) -> s3.Bucket:
        """
        Create S3 bucket for CloudFront logs
        """
        logs_bucket = s3.Bucket(
            self, "LogsBucket",
            bucket_name=f"aquachain-cloudfront-logs-{self.config['environment']}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY if self.config['environment'] == 'dev' else RemovalPolicy.RETAIN,
            auto_delete_objects=self.config['environment'] == 'dev',
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldLogs",
                    expiration=Duration.days(90),
                    enabled=True
                )
            ]
        )
        
        return logs_bucket
    
    def _create_dns_records(self):
        """
        Create Route53 DNS records for custom domain
        """
        domain_name = self.config.get('domain_name')
        hosted_zone_id = self.config.get('hosted_zone_id')
        
        if not domain_name or not hosted_zone_id:
            return
        
        # Get hosted zone
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone",
            hosted_zone_id=hosted_zone_id,
            zone_name=domain_name
        )
        
        # Create A record
        route53.ARecord(
            self, "AliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            )
        )
        
        # Create AAAA record (IPv6)
        route53.AaaaRecord(
            self, "AliasRecordIPv6",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            )
        )
    
    def _deploy_frontend(self):
        """
        Deploy frontend build to S3
        """
        # Deploy frontend files from build directory
        s3deploy.BucketDeployment(
            self, "DeployFrontend",
            sources=[s3deploy.Source.asset("../../frontend/build")],
            destination_bucket=self.frontend_bucket,
            distribution=self.distribution,
            distribution_paths=["/*"],
            memory_limit=512,
            prune=True  # Remove old files
        )
    
    def _create_outputs(self):
        """
        Export CloudFront information
        """
        CfnOutput(
            self, "DistributionId",
            value=self.distribution.distribution_id,
            export_name=f"{Stack.of(self).stack_name}-DistributionId",
            description="CloudFront Distribution ID"
        )
        
        CfnOutput(
            self, "DistributionDomainName",
            value=self.distribution.distribution_domain_name,
            export_name=f"{Stack.of(self).stack_name}-DistributionDomainName",
            description="CloudFront Distribution Domain Name"
        )
        
        CfnOutput(
            self, "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            export_name=f"{Stack.of(self).stack_name}-FrontendBucketName",
            description="Frontend S3 Bucket Name"
        )
        
        CfnOutput(
            self, "FrontendURL",
            value=f"https://{self.config.get('domain_name', self.distribution.distribution_domain_name)}",
            description="Frontend URL"
        )
