"""
AquaChain Landing Page Stack
Static website hosting with CloudFront, S3, Route 53, and WAF
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    aws_wafv2 as wafv2,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput
)
from aws_cdk.aws_cloudfront_origins import S3BucketOrigin
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name, get_stack_name

class AquaChainLandingPageStack(Stack):
    """
    Landing page infrastructure stack for static website hosting
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.domain_name = f"www.{config['domain_name']}" if config['environment'] == 'prod' else f"landing-{config['environment']}.aquachain.io"
        
        # Create S3 bucket for static hosting
        self._create_s3_bucket()
        
        # Create SSL certificate (skip for now, use CloudFront default)
        # self._create_ssl_certificate()
        self.certificate = None
        
        # Create WAF for security
        # NOTE: WAF for CloudFront must be created in us-east-1 region
        # Skipping WAF creation - can be added separately in us-east-1
        self.web_acl = None  # self._create_waf()
        
        # Create CloudFront distribution
        self._create_cloudfront_distribution()
        
        # Create Route 53 DNS records (skip for now due to permissions)
        # self._create_dns_records()
        
        # Create deployment user for CI/CD
        self._create_deployment_user()
        
        # Output important values
        self._create_outputs()
    
    def _create_s3_bucket(self) -> None:
        """
        Create S3 bucket for static website hosting
        """
        bucket_name = get_resource_name(self.config, "landing", "website")
        
        self.website_bucket = s3.Bucket(
            self, "LandingPageBucket",
            bucket_name=bucket_name,
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=False,  # CloudFront will handle access
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(30)
                )
            ]
        )
        
        # S3BucketOrigin will automatically create Origin Access Control
    
    def _create_ssl_certificate(self) -> None:
        """
        Create SSL certificate for the domain
        """
        if self.config["environment"] == "prod":
            # For production, use existing certificate or create new one
            if self.config.get("certificate_arn"):
                self.certificate = acm.Certificate.from_certificate_arn(
                    self, "LandingPageCertificate",
                    certificate_arn=self.config["certificate_arn"]
                )
            else:
                # Create new certificate for production
                self.certificate = acm.Certificate(
                    self, "LandingPageCertificate",
                    domain_name=self.domain_name,
                    subject_alternative_names=[f"aquachain.io", f"*.aquachain.io"],
                    validation=acm.CertificateValidation.from_dns()
                )
        else:
            # For dev/staging, create certificate
            self.certificate = acm.Certificate(
                self, "LandingPageCertificate",
                domain_name=self.domain_name,
                validation=acm.CertificateValidation.from_dns()
            )
    
    def _create_waf(self) -> None:
        """
        Create WAF for security and DDoS protection
        """
        # Create WAF rules
        rate_limit_rule = wafv2.CfnWebACL.RuleProperty(
            name="RateLimitRule",
            priority=1,
            statement=wafv2.CfnWebACL.StatementProperty(
                rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                    limit=2000,
                    aggregate_key_type="IP"
                )
            ),
            action=wafv2.CfnWebACL.RuleActionProperty(
                block={}
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="RateLimitRule"
            )
        )
        
        # AWS Managed Rules - Core Rule Set
        aws_managed_core_rule = wafv2.CfnWebACL.RuleProperty(
            name="AWSManagedRulesCommonRuleSet",
            priority=2,
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesCommonRuleSet"
                )
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(
                none={}
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="AWSManagedRulesCommonRuleSet"
            )
        )
        
        # AWS Managed Rules - Known Bad Inputs
        aws_managed_bad_inputs_rule = wafv2.CfnWebACL.RuleProperty(
            name="AWSManagedRulesKnownBadInputsRuleSet",
            priority=3,
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesKnownBadInputsRuleSet"
                )
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(
                none={}
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="AWSManagedRulesKnownBadInputsRuleSet"
            )
        )
        
        # Create WAF Web ACL
        self.web_acl = wafv2.CfnWebACL(
            self, "LandingPageWAF",
            name=get_resource_name(self.config, "landing", "waf"),
            scope="CLOUDFRONT",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow={}
            ),
            rules=[
                rate_limit_rule,
                aws_managed_core_rule,
                aws_managed_bad_inputs_rule
            ],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="LandingPageWAF"
            )
        )
    
    def _create_cloudfront_distribution(self) -> None:
        """
        Create CloudFront distribution for global content delivery
        """
        # Create cache policies
        cache_policy = cloudfront.CachePolicy(
            self, "LandingPageCachePolicy",
            cache_policy_name=f"{get_resource_name(self.config, 'landing', 'cache')}-policy",
            comment="Cache policy for AquaChain Landing Page",
            default_ttl=Duration.hours(24),
            max_ttl=Duration.days(365),
            min_ttl=Duration.seconds(0),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                "CloudFront-Viewer-Country",
                "CloudFront-Is-Mobile-Viewer",
                "CloudFront-Is-Tablet-Viewer"
            ),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )
        
        # Create origin request policy
        origin_request_policy = cloudfront.OriginRequestPolicy(
            self, "LandingPageOriginRequestPolicy",
            origin_request_policy_name=f"{get_resource_name(self.config, 'landing', 'origin')}-policy",
            comment="Origin request policy for AquaChain Landing Page",
            cookie_behavior=cloudfront.OriginRequestCookieBehavior.none(),
            header_behavior=cloudfront.OriginRequestHeaderBehavior.allow_list(
                "CloudFront-Viewer-Country",
                "CloudFront-Is-Mobile-Viewer",
                "CloudFront-Is-Tablet-Viewer"
            ),
            query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.none()
        )
        
        # Create response headers policy
        response_headers_policy = cloudfront.ResponseHeadersPolicy(
            self, "LandingPageResponseHeadersPolicy",
            response_headers_policy_name=f"{get_resource_name(self.config, 'landing', 'headers')}-policy",
            comment="Security headers for AquaChain Landing Page",
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
                    access_control_max_age=Duration.seconds(31536000),
                    include_subdomains=True,
                    preload=True,
                    override=True
                ),
                content_security_policy=cloudfront.ResponseHeadersContentSecurityPolicy(
                    content_security_policy=f"default-src 'self'; script-src 'self' 'unsafe-inline' https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ https://cognito-idp.{self.config['region']}.amazonaws.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https://*.amazonaws.com https://www.google.com/recaptcha/; connect-src 'self' https://*.amazonaws.com https://www.google-analytics.com; font-src 'self' https://fonts.gstatic.com; frame-src https://www.google.com/recaptcha/; object-src 'none'; base-uri 'self'; form-action 'self';",
                    override=True
                )
            ),
            custom_headers_behavior=cloudfront.ResponseCustomHeadersBehavior(
                custom_headers=[
                    cloudfront.ResponseCustomHeader(
                        header="X-Robots-Tag",
                        value="index, follow" if self.config["environment"] == "prod" else "noindex, nofollow",
                        override=True
                    ),
                    cloudfront.ResponseCustomHeader(
                        header="Cache-Control",
                        value="public, max-age=31536000, immutable",
                        override=False
                    )
                ]
            )
        )
        
        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "LandingPageDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=S3BucketOrigin(
                    bucket=self.website_bucket
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cache_policy,
                origin_request_policy=origin_request_policy,
                response_headers_policy=response_headers_policy,
                compress=True
            ),
            additional_behaviors={
                "/static/*": cloudfront.BehaviorOptions(
                    origin=S3BucketOrigin(
                        bucket=self.website_bucket
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    compress=True
                )
            },
            # Skip custom domain and certificate for now
            # domain_names=[self.domain_name],
            # certificate=self.certificate,
            # minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                )
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            enable_ipv6=True,
            web_acl_id=self.web_acl.attr_arn if self.web_acl else None,
            enable_logging=True,
            log_bucket=s3.Bucket(
                self, "CloudFrontLogsBucket",
                bucket_name=f"{get_resource_name(self.config, 'landing', 'logs')}-cf",
                # Enable ACLs for CloudFront logging
                object_ownership=s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
                removal_policy=RemovalPolicy.DESTROY if self.config["environment"] != "prod" else RemovalPolicy.RETAIN,
                lifecycle_rules=[
                    s3.LifecycleRule(
                        id="DeleteOldLogs",
                        enabled=True,
                        expiration=Duration.days(90)
                    )
                ]
            ),
            log_file_prefix="cloudfront-logs/"
        )
        
        # S3BucketOrigin automatically grants CloudFront access to S3 bucket
    
    def _create_dns_records(self) -> None:
        """
        Create Route 53 DNS records
        """
        # Get hosted zone
        if self.config["environment"] == "prod":
            zone_name = "aquachain.io"
        else:
            zone_name = "aquachain.io"  # Use same zone for all environments
        
        self.hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=zone_name
        )
        
        # Create A record for the domain
        self.a_record = route53.ARecord(
            self, "LandingPageARecord",
            zone=self.hosted_zone,
            record_name=self.domain_name.replace(f".{zone_name}", ""),
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            ),
            ttl=Duration.minutes(5)
        )
        
        # Create AAAA record for IPv6
        self.aaaa_record = route53.AaaaRecord(
            self, "LandingPageAAAARecord",
            zone=self.hosted_zone,
            record_name=self.domain_name.replace(f".{zone_name}", ""),
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            ),
            ttl=Duration.minutes(5)
        )
    
    def _create_deployment_user(self) -> None:
        """
        Create IAM user for CI/CD deployment
        """
        # Create deployment user
        self.deployment_user = iam.User(
            self, "LandingPageDeploymentUser",
            user_name=get_resource_name(self.config, "landing", "deploy-user")
        )
        
        # Create policy for S3 deployment
        deployment_policy = iam.Policy(
            self, "LandingPageDeploymentPolicy",
            policy_name=get_resource_name(self.config, "landing", "deploy-policy"),
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    resources=[
                        self.website_bucket.bucket_arn,
                        f"{self.website_bucket.bucket_arn}/*"
                    ]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "cloudfront:CreateInvalidation",
                        "cloudfront:GetInvalidation",
                        "cloudfront:ListInvalidations"
                    ],
                    resources=[f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"]
                )
            ]
        )
        
        # Attach policy to user
        self.deployment_user.attach_inline_policy(deployment_policy)
        
        # Create access key
        self.access_key = iam.AccessKey(
            self, "LandingPageDeploymentAccessKey",
            user=self.deployment_user
        )
    
    def _create_outputs(self) -> None:
        """
        Create CloudFormation outputs
        """
        CfnOutput(
            self, "WebsiteBucketName",
            value=self.website_bucket.bucket_name,
            description="S3 bucket name for website hosting"
        )
        
        CfnOutput(
            self, "CloudFrontDistributionId",
            value=self.distribution.distribution_id,
            description="CloudFront distribution ID"
        )
        
        CfnOutput(
            self, "CloudFrontDomainName",
            value=self.distribution.distribution_domain_name,
            description="CloudFront distribution domain name"
        )
        
        CfnOutput(
            self, "WebsiteURL",
            value=f"https://{self.domain_name}",
            description="Website URL"
        )
        
        CfnOutput(
            self, "DeploymentUserAccessKeyId",
            value=self.access_key.access_key_id,
            description="Access key ID for deployment user"
        )
        
        CfnOutput(
            self, "DeploymentUserSecretAccessKey",
            value=self.access_key.secret_access_key.unsafe_unwrap(),
            description="Secret access key for deployment user"
        )
        
        if self.web_acl:
            CfnOutput(
                self, "WAFWebACLArn",
                value=self.web_acl.attr_arn,
                description="WAF Web ACL ARN"
            )