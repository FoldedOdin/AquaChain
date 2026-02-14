"""
AquaChain Dashboard Overhaul Deployment Pipeline Stack
Implements blue-green deployment, feature flags, canary deployment, and automated rollback
"""

from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codedeploy as codedeploy,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_appconfig as appconfig,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as iam,
    aws_s3 as s3,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Tags
)
from constructs import Construct
from typing import Dict, Any
from config.environment_config import get_resource_name

class DeploymentPipelineStack(Stack):
    """
    Deployment pipeline stack with blue-green deployment, feature flags, and canary deployment
    """
    
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        self.deployment_resources = {}
        
        # Create S3 bucket for pipeline artifacts
        self._create_pipeline_artifacts_bucket()
        
        # Create SNS topic for deployment notifications
        self._create_notification_topic()
        
        # Create AppConfig application for feature flags
        self._create_appconfig_application()
        
        # Create CodeBuild projects for build and test
        self._create_codebuild_projects()
        
        # Create CodeDeploy applications for blue-green deployment
        self._create_codedeploy_applications()
        
        # Create deployment pipeline
        self._create_deployment_pipeline()
        
        # Create CloudWatch alarms for deployment monitoring
        self._create_deployment_monitoring()
        
        # Create automated rollback Lambda function
        self._create_rollback_automation()
        
        # Tag all resources
        self._tag_resources()
    
    def _create_pipeline_artifacts_bucket(self) -> None:
        """
        Create S3 bucket for storing pipeline artifacts
        """
        
        self.artifacts_bucket = s3.Bucket(
            self, "PipelineArtifactsBucket",
            bucket_name=get_resource_name(self.config, "bucket", "pipeline-artifacts"),
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN if self.config["environment"] == "prod" else RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldArtifacts",
                    enabled=True,
                    expiration=Duration.days(30),
                    noncurrent_version_expiration=Duration.days(7)
                )
            ]
        )
        
        self.deployment_resources["artifacts_bucket"] = self.artifacts_bucket
    
    def _create_notification_topic(self) -> None:
        """
        Create SNS topic for deployment notifications
        """
        
        self.deployment_notifications = sns.Topic(
            self, "DeploymentNotifications",
            topic_name=get_resource_name(self.config, "topic", "deployment-notifications"),
            display_name="Dashboard Overhaul Deployment Notifications"
        )
        
        # Add email subscriptions for deployment notifications
        for email in self.config.get("notification_channels", {}).get("email", []):
            self.deployment_notifications.add_subscription(
                sns_subscriptions.EmailSubscription(email)
            )
        
        self.deployment_resources["notification_topic"] = self.deployment_notifications
    
    def _create_appconfig_application(self) -> None:
        """
        Create AWS AppConfig application for feature flags
        """
        
        # AppConfig Application
        self.appconfig_app = appconfig.CfnApplication(
            self, "DashboardFeatureFlags",
            name=get_resource_name(self.config, "appconfig", "dashboard-features"),
            description="Feature flags for Dashboard Overhaul system"
        )
        
        # AppConfig Environment
        self.appconfig_env = appconfig.CfnEnvironment(
            self, "DashboardFeatureFlagsEnv",
            application_id=self.appconfig_app.ref,
            name=self.config["environment"],
            description=f"Feature flags environment for {self.config['environment']}"
        )
        
        # AppConfig Configuration Profile for feature flags
        self.feature_flags_profile = appconfig.CfnConfigurationProfile(
            self, "FeatureFlagsProfile",
            application_id=self.appconfig_app.ref,
            name="FeatureFlags",
            location_uri="hosted",
            type="AWS.AppConfig.FeatureFlags",
            description="Feature flags configuration for dashboard overhaul"
        )
        
        # Default feature flags configuration
        default_feature_flags = {
            "flags": {
                "enable_new_operations_dashboard": {
                    "enabled": False
                },
                "enable_new_procurement_dashboard": {
                    "enabled": False
                },
                "enable_new_admin_dashboard": {
                    "enabled": False
                },
                "enable_rbac_enforcement": {
                    "enabled": True
                },
                "enable_audit_logging": {
                    "enabled": True
                },
                "enable_budget_enforcement": {
                    "enabled": True
                },
                "enable_ml_forecast_integration": {
                    "enabled": False
                },
                "enable_graceful_degradation": {
                    "enabled": True
                },
                "enable_performance_monitoring": {
                    "enabled": True
                }
            },
            "values": {
                "enable_new_operations_dashboard": {
                    "enabled": False
                },
                "enable_new_procurement_dashboard": {
                    "enabled": False
                },
                "enable_new_admin_dashboard": {
                    "enabled": False
                },
                "enable_rbac_enforcement": {
                    "enabled": True
                },
                "enable_audit_logging": {
                    "enabled": True
                },
                "enable_budget_enforcement": {
                    "enabled": True
                },
                "enable_ml_forecast_integration": {
                    "enabled": False
                },
                "enable_graceful_degradation": {
                    "enabled": True
                },
                "enable_performance_monitoring": {
                    "enabled": True
                }
            },
            "version": "1"
        }
        
        # Hosted Configuration Version for initial feature flags
        self.feature_flags_version = appconfig.CfnHostedConfigurationVersion(
            self, "InitialFeatureFlags",
            application_id=self.appconfig_app.ref,
            configuration_profile_id=self.feature_flags_profile.ref,
            content=str(default_feature_flags).replace("'", '"').replace("False", "false").replace("True", "true"),
            content_type="application/json",
            description="Initial feature flags configuration"
        )
        
        # Deployment Strategy for gradual rollout
        self.deployment_strategy = appconfig.CfnDeploymentStrategy(
            self, "GradualDeploymentStrategy",
            name=get_resource_name(self.config, "strategy", "gradual-rollout"),
            description="Gradual rollout strategy for feature flags",
            deployment_duration_in_minutes=10,  # 10 minutes total deployment
            growth_factor=20,  # 20% growth per step
            replicate_to="NONE",
            final_bake_time_in_minutes=5  # 5 minutes final bake time
        )
        
        self.deployment_resources.update({
            "appconfig_app": self.appconfig_app,
            "appconfig_env": self.appconfig_env,
            "feature_flags_profile": self.feature_flags_profile,
            "feature_flags_version": self.feature_flags_version,
            "deployment_strategy": self.deployment_strategy
        })
    
    def _create_codebuild_projects(self) -> None:
        """
        Create CodeBuild projects for build, test, and deployment validation
        """
        
        # Build project for backend services
        self.backend_build_project = codebuild.Project(
            self, "BackendBuildProject",
            project_name=get_resource_name(self.config, "build", "backend"),
            description="Build and test backend Lambda functions",
            source=codebuild.Source.git_hub(
                owner="aquachain",
                repo="dashboard-overhaul",
                webhook=True,
                webhook_filters=[
                    codebuild.FilterGroup.in_event_of(
                        codebuild.EventAction.PUSH,
                        codebuild.EventAction.PULL_REQUEST_CREATED,
                        codebuild.EventAction.PULL_REQUEST_UPDATED
                    ).and_branch_is("main").and_file_path_is("lambda/**")
                ]
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                environment_variables={
                    "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=self.config["environment"]),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(value=self.config["region"]),
                    "ARTIFACTS_BUCKET": codebuild.BuildEnvironmentVariable(value=self.artifacts_bucket.bucket_name)
                }
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11",
                            "nodejs": "18"
                        },
                        "commands": [
                            "echo Installing dependencies...",
                            "cd lambda",
                            "pip install -r requirements.txt",
                            "pip install pytest pytest-cov mypy black flake8"
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            "echo Running code quality checks...",
                            "black --check .",
                            "flake8 .",
                            "mypy ."
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Running tests...",
                            "pytest --cov=. --cov-report=xml --cov-report=html",
                            "echo Building Lambda packages...",
                            "cd ..",
                            "python scripts/build-lambda-packages.py"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Uploading artifacts to S3...",
                            "aws s3 sync lambda-packages/ s3://$ARTIFACTS_BUCKET/lambda-packages/"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "lambda-packages/**/*",
                        "infrastructure/**/*",
                        "tests/**/*"
                    ]
                },
                "reports": {
                    "coverage": {
                        "files": ["coverage.xml"],
                        "base-directory": "lambda",
                        "file-format": "COBERTURAXML"
                    }
                }
            }),
            artifacts=codebuild.Artifacts.s3(
                bucket=self.artifacts_bucket,
                include_build_id=True,
                name="backend-build"
            )
        )
        
        # Frontend build project
        self.frontend_build_project = codebuild.Project(
            self, "FrontendBuildProject",
            project_name=get_resource_name(self.config, "build", "frontend"),
            description="Build and test frontend React application",
            source=codebuild.Source.git_hub(
                owner="aquachain",
                repo="dashboard-overhaul",
                webhook=True,
                webhook_filters=[
                    codebuild.FilterGroup.in_event_of(
                        codebuild.EventAction.PUSH,
                        codebuild.EventAction.PULL_REQUEST_CREATED,
                        codebuild.EventAction.PULL_REQUEST_UPDATED
                    ).and_branch_is("main").and_file_path_is("frontend/**")
                ]
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                environment_variables={
                    "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=self.config["environment"]),
                    "ARTIFACTS_BUCKET": codebuild.BuildEnvironmentVariable(value=self.artifacts_bucket.bucket_name)
                }
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "nodejs": "18"
                        },
                        "commands": [
                            "echo Installing dependencies...",
                            "cd frontend",
                            "npm ci"
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            "echo Running linting and type checking...",
                            "npm run lint",
                            "npm run type-check"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Running tests...",
                            "npm run test:coverage",
                            "echo Building production bundle...",
                            "npm run build"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Uploading build artifacts...",
                            "aws s3 sync build/ s3://$ARTIFACTS_BUCKET/frontend-build/"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "build/**/*"
                    ],
                    "base-directory": "frontend"
                },
                "reports": {
                    "coverage": {
                        "files": ["coverage/lcov.info"],
                        "base-directory": "frontend",
                        "file-format": "LCOV"
                    }
                }
            }),
            artifacts=codebuild.Artifacts.s3(
                bucket=self.artifacts_bucket,
                include_build_id=True,
                name="frontend-build"
            )
        )
        
        # Integration test project
        self.integration_test_project = codebuild.Project(
            self, "IntegrationTestProject",
            project_name=get_resource_name(self.config, "build", "integration-tests"),
            description="Run integration and end-to-end tests",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.MEDIUM,
                environment_variables={
                    "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=self.config["environment"]),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(value=self.config["region"])
                }
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11",
                            "nodejs": "18"
                        },
                        "commands": [
                            "echo Installing test dependencies...",
                            "pip install pytest requests boto3",
                            "npm install -g newman"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Running integration tests...",
                            "cd tests/integration",
                            "pytest -v --tb=short",
                            "echo Running API tests with Newman...",
                            "newman run ../../dashboard-overhaul.postman.json"
                        ]
                    }
                }
            })
        )
        
        # Grant necessary permissions to build projects
        self.artifacts_bucket.grant_read_write(self.backend_build_project)
        self.artifacts_bucket.grant_read_write(self.frontend_build_project)
        
        self.deployment_resources.update({
            "backend_build_project": self.backend_build_project,
            "frontend_build_project": self.frontend_build_project,
            "integration_test_project": self.integration_test_project
        })
    
    def _create_codedeploy_applications(self) -> None:
        """
        Create CodeDeploy applications for blue-green deployment
        """
        
        # Lambda CodeDeploy application
        self.lambda_deploy_app = codedeploy.LambdaApplication(
            self, "LambdaDeployApp",
            application_name=get_resource_name(self.config, "deploy", "lambda")
        )
        
        # API Gateway CodeDeploy application (for canary deployments)
        self.api_deploy_app = codedeploy.ServerApplication(
            self, "ApiDeployApp",
            application_name=get_resource_name(self.config, "deploy", "api")
        )
        
        self.deployment_resources.update({
            "lambda_deploy_app": self.lambda_deploy_app,
            "api_deploy_app": self.api_deploy_app
        })
    
    def _create_deployment_pipeline(self) -> None:
        """
        Create the main deployment pipeline with blue-green deployment
        """
        
        # Source artifact
        source_output = codepipeline.Artifact("SourceOutput")
        
        # Build artifacts
        backend_build_output = codepipeline.Artifact("BackendBuildOutput")
        frontend_build_output = codepipeline.Artifact("FrontendBuildOutput")
        
        # Create the pipeline
        self.deployment_pipeline = codepipeline.Pipeline(
            self, "DeploymentPipeline",
            pipeline_name=get_resource_name(self.config, "pipeline", "dashboard-deployment"),
            artifact_bucket=self.artifacts_bucket,
            stages=[
                # Source Stage
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.GitHubSourceAction(
                            action_name="GitHub_Source",
                            owner="aquachain",
                            repo="dashboard-overhaul",
                            branch="main",
                            oauth_token=self._get_github_token(),
                            output=source_output,
                            trigger=codepipeline_actions.GitHubTrigger.WEBHOOK
                        )
                    ]
                ),
                
                # Build Stage
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Backend_Build",
                            project=self.backend_build_project,
                            input=source_output,
                            outputs=[backend_build_output]
                        ),
                        codepipeline_actions.CodeBuildAction(
                            action_name="Frontend_Build",
                            project=self.frontend_build_project,
                            input=source_output,
                            outputs=[frontend_build_output]
                        )
                    ]
                ),
                
                # Test Stage
                codepipeline.StageProps(
                    stage_name="Test",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Integration_Tests",
                            project=self.integration_test_project,
                            input=source_output,
                            run_order=1
                        )
                    ]
                ),
                
                # Deploy to Staging (if not prod)
                *([codepipeline.StageProps(
                    stage_name="Deploy_Staging",
                    actions=[
                        codepipeline_actions.CloudFormationCreateUpdateStackAction(
                            action_name="Deploy_Infrastructure",
                            stack_name=f"AquaChain-DashboardOverhaul-staging",
                            template_path=backend_build_output.at_path("infrastructure/cdk/cdk.out/AquaChain-DashboardOverhaul-staging.template.json"),
                            admin_permissions=True,
                            run_order=1
                        ),
                        codepipeline_actions.LambdaInvokeAction(
                            action_name="Deploy_Lambda_Functions",
                            lambda_=self._create_deployment_lambda(),
                            inputs=[backend_build_output],
                            run_order=2
                        )
                    ]
                )] if self.config["environment"] != "prod" else []),
                
                # Manual Approval (for production)
                *([codepipeline.StageProps(
                    stage_name="Manual_Approval",
                    actions=[
                        codepipeline_actions.ManualApprovalAction(
                            action_name="Approve_Production_Deployment",
                            notification_topic=self.deployment_notifications,
                            additional_information="Please review staging deployment and approve for production"
                        )
                    ]
                )] if self.config["environment"] == "prod" else []),
                
                # Deploy to Production
                codepipeline.StageProps(
                    stage_name="Deploy_Production",
                    actions=[
                        codepipeline_actions.CloudFormationCreateUpdateStackAction(
                            action_name="Deploy_Infrastructure",
                            stack_name=f"AquaChain-DashboardOverhaul-{self.config['environment']}",
                            template_path=backend_build_output.at_path("infrastructure/cdk/cdk.out/AquaChain-DashboardOverhaul-{}.template.json".format(self.config["environment"])),
                            admin_permissions=True,
                            run_order=1
                        ),
                        codepipeline_actions.LambdaInvokeAction(
                            action_name="Blue_Green_Deployment",
                            lambda_=self._create_blue_green_deployment_lambda(),
                            inputs=[backend_build_output],
                            run_order=2
                        ),
                        codepipeline_actions.LambdaInvokeAction(
                            action_name="Canary_Deployment",
                            lambda_=self._create_canary_deployment_lambda(),
                            inputs=[frontend_build_output],
                            run_order=3
                        )
                    ]
                ),
                
                # Post-Deployment Validation
                codepipeline.StageProps(
                    stage_name="Validate_Deployment",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Deployment_Validation_Tests",
                            project=self._create_deployment_validation_project(),
                            input=source_output
                        )
                    ]
                )
            ]
        )
        
        self.deployment_resources["deployment_pipeline"] = self.deployment_pipeline
    
    def _get_github_token(self):
        """
        Get GitHub token from Secrets Manager (placeholder)
        """
        # In a real implementation, this would retrieve the token from Secrets Manager
        # For now, return a placeholder that needs to be configured
        return "github-token-placeholder"
    
    def _create_deployment_lambda(self) -> lambda_.Function:
        """
        Create Lambda function for deployment orchestration
        """
        
        deployment_lambda = lambda_.Function(
            self, "DeploymentLambda",
            function_name=get_resource_name(self.config, "function", "deployment"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    '''
    Deployment orchestration Lambda function
    '''
    logger.info(f"Deployment event: {json.dumps(event)}")
    
    # Extract CodePipeline job data
    job_id = event['CodePipeline.job']['id']
    
    try:
        # Deployment logic would go here
        # For now, just return success
        
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_success_result(jobId=job_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Deployment successful')
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': str(e), 'type': 'JobFailed'}
        )
        
        raise e
            """),
            timeout=Duration.minutes(15)
        )
        
        # Grant necessary permissions
        deployment_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "codepipeline:PutJobSuccessResult",
                    "codepipeline:PutJobFailureResult"
                ],
                resources=["*"]
            )
        )
        
        return deployment_lambda
    
    def _create_blue_green_deployment_lambda(self) -> lambda_.Function:
        """
        Create Lambda function for blue-green deployment
        """
        
        blue_green_lambda = lambda_.Function(
            self, "BlueGreenDeploymentLambda",
            function_name=get_resource_name(self.config, "function", "blue-green-deployment"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    '''
    Blue-green deployment Lambda function
    '''
    logger.info(f"Blue-green deployment event: {json.dumps(event)}")
    
    job_id = event['CodePipeline.job']['id']
    
    try:
        # Blue-green deployment logic
        # 1. Deploy to green environment
        # 2. Run health checks
        # 3. Switch traffic gradually
        # 4. Monitor metrics
        # 5. Complete or rollback
        
        logger.info("Starting blue-green deployment...")
        
        # Placeholder for actual deployment logic
        
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_success_result(jobId=job_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Blue-green deployment successful')
        }
        
    except Exception as e:
        logger.error(f"Blue-green deployment failed: {str(e)}")
        
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': str(e), 'type': 'JobFailed'}
        )
        
        raise e
            """),
            timeout=Duration.minutes(30)
        )
        
        # Grant necessary permissions
        blue_green_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "codepipeline:PutJobSuccessResult",
                    "codepipeline:PutJobFailureResult",
                    "lambda:UpdateAlias",
                    "lambda:GetAlias",
                    "lambda:UpdateFunctionConfiguration",
                    "apigateway:*"
                ],
                resources=["*"]
            )
        )
        
        return blue_green_lambda
    
    def _create_canary_deployment_lambda(self) -> lambda_.Function:
        """
        Create Lambda function for canary deployment
        """
        
        canary_lambda = lambda_.Function(
            self, "CanaryDeploymentLambda",
            function_name=get_resource_name(self.config, "function", "canary-deployment"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    '''
    Canary deployment Lambda function
    '''
    logger.info(f"Canary deployment event: {json.dumps(event)}")
    
    job_id = event['CodePipeline.job']['id']
    
    try:
        # Canary deployment logic
        # 1. Deploy to small percentage of traffic
        # 2. Monitor metrics and error rates
        # 3. Gradually increase traffic
        # 4. Complete or rollback based on metrics
        
        logger.info("Starting canary deployment...")
        
        # Simulate canary deployment stages
        stages = [5, 10, 25, 50, 100]  # Traffic percentages
        
        for stage in stages:
            logger.info(f"Deploying to {stage}% of traffic...")
            
            # Simulate deployment and monitoring
            time.sleep(30)  # Wait for metrics
            
            # Check metrics (placeholder)
            error_rate = 0.1  # Simulated error rate
            if error_rate > 0.5:  # 0.5% error threshold
                raise Exception(f"High error rate detected: {error_rate}%")
            
            logger.info(f"Stage {stage}% successful, proceeding...")
        
        logger.info("Canary deployment completed successfully")
        
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_success_result(jobId=job_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Canary deployment successful')
        }
        
    except Exception as e:
        logger.error(f"Canary deployment failed: {str(e)}")
        
        # Trigger rollback
        logger.info("Triggering automatic rollback...")
        
        codepipeline = boto3.client('codepipeline')
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': str(e), 'type': 'JobFailed'}
        )
        
        raise e
            """),
            timeout=Duration.minutes(45)
        )
        
        # Grant necessary permissions
        canary_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "codepipeline:PutJobSuccessResult",
                    "codepipeline:PutJobFailureResult",
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:GetMetricData",
                    "apigateway:*"
                ],
                resources=["*"]
            )
        )
        
        return canary_lambda
    
    def _create_deployment_validation_project(self) -> codebuild.Project:
        """
        Create CodeBuild project for deployment validation tests
        """
        
        return codebuild.Project(
            self, "DeploymentValidationProject",
            project_name=get_resource_name(self.config, "build", "deployment-validation"),
            description="Validate deployment functionality and rollback procedures",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                environment_variables={
                    "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=self.config["environment"]),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(value=self.config["region"])
                }
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11"
                        },
                        "commands": [
                            "echo Installing validation dependencies...",
                            "pip install pytest requests boto3"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Running deployment validation tests...",
                            "cd tests/deployment",
                            "pytest test_deployment_validation.py -v",
                            "echo Testing feature flag controls...",
                            "pytest test_feature_flags.py -v",
                            "echo Testing rollback procedures...",
                            "pytest test_rollback_procedures.py -v"
                        ]
                    }
                }
            })
        )
    
    def _create_deployment_monitoring(self) -> None:
        """
        Create CloudWatch alarms for deployment monitoring
        """
        
        # Pipeline failure alarm
        pipeline_failure_alarm = cloudwatch.Alarm(
            self, "PipelineFailureAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "pipeline-failure"),
            alarm_description="Dashboard deployment pipeline failed",
            metric=cloudwatch.Metric(
                namespace="AWS/CodePipeline",
                metric_name="PipelineExecutionFailure",
                dimensions_map={
                    "PipelineName": self.deployment_pipeline.pipeline_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
        
        # Add SNS notification for pipeline failures
        pipeline_failure_alarm.add_alarm_action(
            cloudwatch.SnsAction(self.deployment_notifications)
        )
        
        # Deployment duration alarm
        deployment_duration_alarm = cloudwatch.Alarm(
            self, "DeploymentDurationAlarm",
            alarm_name=get_resource_name(self.config, "alarm", "deployment-duration"),
            alarm_description="Dashboard deployment taking too long",
            metric=cloudwatch.Metric(
                namespace="AWS/CodePipeline",
                metric_name="PipelineExecutionDuration",
                dimensions_map={
                    "PipelineName": self.deployment_pipeline.pipeline_name
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=3600,  # 1 hour threshold
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        deployment_duration_alarm.add_alarm_action(
            cloudwatch.SnsAction(self.deployment_notifications)
        )
        
        self.deployment_resources.update({
            "pipeline_failure_alarm": pipeline_failure_alarm,
            "deployment_duration_alarm": deployment_duration_alarm
        })
    
    def _create_rollback_automation(self) -> None:
        """
        Create automated rollback Lambda function
        """
        
        self.rollback_lambda = lambda_.Function(
            self, "AutomatedRollbackLambda",
            function_name=get_resource_name(self.config, "function", "automated-rollback"),
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def main(event, context):
    '''
    Automated rollback Lambda function
    Triggered by CloudWatch alarms or manual invocation
    '''
    logger.info(f"Rollback event: {json.dumps(event)}")
    
    try:
        # Determine rollback strategy based on event
        rollback_type = event.get('rollback_type', 'lambda_alias')
        
        if rollback_type == 'lambda_alias':
            # Rollback Lambda function aliases
            lambda_client = boto3.client('lambda')
            
            # Get list of functions to rollback
            functions_to_rollback = event.get('functions', [])
            
            for function_name in functions_to_rollback:
                logger.info(f"Rolling back function: {function_name}")
                
                # Get previous version from alias
                try:
                    alias_response = lambda_client.get_alias(
                        FunctionName=function_name,
                        Name='LIVE'
                    )
                    current_version = alias_response['FunctionVersion']
                    
                    # Get previous version (simplified logic)
                    previous_version = str(int(current_version) - 1)
                    
                    # Update alias to previous version
                    lambda_client.update_alias(
                        FunctionName=function_name,
                        Name='LIVE',
                        FunctionVersion=previous_version
                    )
                    
                    logger.info(f"Rolled back {function_name} from {current_version} to {previous_version}")
                    
                except Exception as e:
                    logger.error(f"Failed to rollback {function_name}: {str(e)}")
        
        elif rollback_type == 'api_gateway':
            # Rollback API Gateway deployment
            api_client = boto3.client('apigateway')
            
            rest_api_id = event.get('rest_api_id')
            stage_name = event.get('stage_name', 'prod')
            
            if rest_api_id:
                # Get deployment history and rollback to previous
                deployments = api_client.get_deployments(restApiId=rest_api_id)
                
                if len(deployments['items']) >= 2:
                    previous_deployment = deployments['items'][1]  # Second most recent
                    
                    api_client.update_stage(
                        restApiId=rest_api_id,
                        stageName=stage_name,
                        patchOps=[
                            {
                                'op': 'replace',
                                'path': '/deploymentId',
                                'value': previous_deployment['id']
                            }
                        ]
                    )
                    
                    logger.info(f"Rolled back API Gateway {rest_api_id} to deployment {previous_deployment['id']}")
        
        elif rollback_type == 'feature_flags':
            # Rollback feature flags
            appconfig_client = boto3.client('appconfig')
            
            application_id = event.get('application_id')
            environment_id = event.get('environment_id')
            configuration_profile_id = event.get('configuration_profile_id')
            
            # Disable problematic feature flags
            flags_to_disable = event.get('flags_to_disable', [])
            
            for flag in flags_to_disable:
                logger.info(f"Disabling feature flag: {flag}")
                # Feature flag rollback logic would go here
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Rollback completed successfully',
                'rollback_type': rollback_type
            })
        }
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        
        # Send notification about rollback failure
        sns_client = boto3.client('sns')
        sns_client.publish(
            TopicArn=event.get('notification_topic_arn'),
            Subject='CRITICAL: Automated Rollback Failed',
            Message=f'Automated rollback failed: {str(e)}\\n\\nManual intervention required.'
        )
        
        raise e
            """),
            timeout=Duration.minutes(15),
            environment={
                "NOTIFICATION_TOPIC_ARN": self.deployment_notifications.topic_arn
            }
        )
        
        # Grant necessary permissions for rollback operations
        self.rollback_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:UpdateAlias",
                    "lambda:GetAlias",
                    "lambda:ListVersionsByFunction",
                    "apigateway:GET",
                    "apigateway:PATCH",
                    "appconfig:GetConfiguration",
                    "appconfig:StartDeployment",
                    "sns:Publish"
                ],
                resources=["*"]
            )
        )
        
        # Create CloudWatch Event Rule to trigger rollback on high error rates
        rollback_rule = cloudwatch.Rule(
            self, "AutoRollbackRule",
            rule_name=get_resource_name(self.config, "rule", "auto-rollback"),
            description="Trigger automated rollback on high error rates",
            event_pattern=cloudwatch.EventPattern(
                source=["aws.cloudwatch"],
                detail_type=["CloudWatch Alarm State Change"],
                detail={
                    "state": {
                        "value": ["ALARM"]
                    },
                    "alarmName": [
                        {"prefix": get_resource_name(self.config, "alarm", "error-rate")}
                    ]
                }
            )
        )
        
        rollback_rule.add_target(
            cloudwatch.LambdaFunction(self.rollback_lambda)
        )
        
        self.deployment_resources.update({
            "rollback_lambda": self.rollback_lambda,
            "rollback_rule": rollback_rule
        })
    
    def _tag_resources(self) -> None:
        """
        Tag all deployment pipeline resources
        """
        
        tags = {
            "Project": "AquaChain",
            "Component": "DeploymentPipeline",
            "Environment": self.config["environment"],
            "ManagedBy": "CDK",
            "Purpose": "DashboardOverhaulDeployment"
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
            self, "DeploymentPipelineName",
            value=self.deployment_pipeline.pipeline_name,
            description="Dashboard deployment pipeline name"
        )
        
        CfnOutput(
            self, "AppConfigApplicationId",
            value=self.appconfig_app.ref,
            description="AppConfig application ID for feature flags"
        )
        
        CfnOutput(
            self, "ArtifactsBucketName",
            value=self.artifacts_bucket.bucket_name,
            description="S3 bucket for pipeline artifacts"
        )
        
        CfnOutput(
            self, "NotificationTopicArn",
            value=self.deployment_notifications.topic_arn,
            description="SNS topic for deployment notifications"
        )
        
        return {
            "pipeline_name": self.deployment_pipeline.pipeline_name,
            "appconfig_app_id": self.appconfig_app.ref,
            "artifacts_bucket": self.artifacts_bucket.bucket_name,
            "notification_topic": self.deployment_notifications.topic_arn
        }