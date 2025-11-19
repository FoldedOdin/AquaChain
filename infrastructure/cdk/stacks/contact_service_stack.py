"""
CDK Stack for Contact Form Service
Deploys Lambda function, API Gateway, and integrates with DynamoDB and SES
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct


class ContactServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Environment variables
        admin_email = self.node.try_get_context('admin_email') or 'admin@aquachain.io'
        from_email = self.node.try_get_context('from_email') or 'noreply@aquachain.io'
        
        # DynamoDB Table for Contact Submissions
        contact_table = dynamodb.Table(
            self, 'ContactSubmissionsTable',
            table_name='aquachain-contact-submissions',
            partition_key=dynamodb.Attribute(
                name='submissionId',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute='ttl'
        )
        
        # GSI for email lookup
        contact_table.add_global_secondary_index(
            index_name='email-createdAt-index',
            partition_key=dynamodb.Attribute(
                name='email',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='createdAt',
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for inquiry type
        contact_table.add_global_secondary_index(
            index_name='inquiryType-createdAt-index',
            partition_key=dynamodb.Attribute(
                name='inquiryType',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='createdAt',
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for status
        contact_table.add_global_secondary_index(
            index_name='status-createdAt-index',
            partition_key=dynamodb.Attribute(
                name='status',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='createdAt',
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Lambda Function for Contact Form Handler
        contact_lambda = lambda_.Function(
            self, 'ContactFormHandler',
            function_name='aquachain-contact-form-handler',
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler='handler.lambda_handler',
            code=lambda_.Code.from_asset('lambda/contact_service'),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                'CONTACT_TABLE_NAME': contact_table.table_name,
                'ADMIN_EMAIL': admin_email,
                'FROM_EMAIL': from_email,
                'AWS_REGION': self.region
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Grant Lambda permissions to DynamoDB
        contact_table.grant_read_write_data(contact_lambda)
        
        # Grant Lambda permissions to SES
        contact_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'ses:SendEmail',
                    'ses:SendRawEmail'
                ],
                resources=['*']
            )
        )
        
        # API Gateway REST API
        api = apigateway.RestApi(
            self, 'ContactFormApi',
            rest_api_name='AquaChain Contact Form API',
            description='API for handling contact form submissions',
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    'Content-Type',
                    'Authorization',
                    'X-Amz-Date',
                    'X-Api-Key',
                    'X-Amz-Security-Token'
                ]
            ),
            deploy_options=apigateway.StageOptions(
                stage_name='prod',
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True
            )
        )
        
        # Lambda Integration
        contact_integration = apigateway.LambdaIntegration(
            contact_lambda,
            proxy=True,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code='200',
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
            ]
        )
        
        # API Resource and Method
        contact_resource = api.root.add_resource('contact')
        contact_resource.add_method(
            'POST',
            contact_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code='200',
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            ]
        )
        
        # Outputs
        CfnOutput(
            self, 'ContactTableName',
            value=contact_table.table_name,
            description='DynamoDB table name for contact submissions'
        )
        
        CfnOutput(
            self, 'ContactLambdaArn',
            value=contact_lambda.function_arn,
            description='Lambda function ARN for contact form handler'
        )
        
        CfnOutput(
            self, 'ContactApiUrl',
            value=api.url,
            description='API Gateway URL for contact form submissions'
        )
        
        CfnOutput(
            self, 'ContactApiEndpoint',
            value=f'{api.url}contact',
            description='Full endpoint URL for contact form'
        )
