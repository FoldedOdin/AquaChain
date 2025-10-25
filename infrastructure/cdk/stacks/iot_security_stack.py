"""
IoT Security Stack
Enhanced security policies for IoT devices with strict access controls
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_iot as iot,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any


class AquaChainIoTSecurityStack(Stack):
    """
    Enhanced IoT Core security with strict device policies
    """
    
    def __init__(self, scope: Construct, construct_id: str,
                 config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.config = config
        
        # Create enhanced device policy
        self.device_policy = self._create_enhanced_device_policy()
        
        # Create IoT logging
        self._enable_iot_logging()
        
        # Create security monitoring
        self._create_security_monitoring()
        
        # Create fleet indexing for device management
        self._enable_fleet_indexing()
        
        # Create outputs
        self._create_outputs()
    
    def _create_enhanced_device_policy(self) -> iot.CfnPolicy:
        """
        Create strict IoT device policy with minimal permissions
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                # Connect - Device can only connect as itself
                {
                    "Effect": "Allow",
                    "Action": "iot:Connect",
                    "Resource": f"arn:aws:iot:{self.region}:{self.account}:client/${{iot:Connection.Thing.ThingName}}",
                    "Condition": {
                        "StringEquals": {
                            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
                        }
                    }
                },
                # Publish - Device can only publish to its own data topic
                {
                    "Effect": "Allow",
                    "Action": "iot:Publish",
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/data",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/telemetry",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/shadow/update"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
                        }
                    }
                },
                # Subscribe - Device can only subscribe to its own command topic
                {
                    "Effect": "Allow",
                    "Action": "iot:Subscribe",
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topicfilter/aquachain/${{iot:Connection.Thing.ThingName}}/commands",
                        f"arn:aws:iot:{self.region}:{self.account}:topicfilter/aquachain/${{iot:Connection.Thing.ThingName}}/shadow/update/delta"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
                        }
                    }
                },
                # Receive - Device can only receive from subscribed topics
                {
                    "Effect": "Allow",
                    "Action": "iot:Receive",
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/commands",
                        f"arn:aws:iot:{self.region}:{self.account}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/shadow/update/delta"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
                        }
                    }
                },
                # Shadow operations - Device can only access its own shadow
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:GetThingShadow",
                        "iot:UpdateThingShadow"
                    ],
                    "Resource": f"arn:aws:iot:{self.region}:{self.account}:thing/${{iot:Connection.Thing.ThingName}}",
                    "Condition": {
                        "StringEquals": {
                            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
                        }
                    }
                },
                # Explicit deny for wildcard topics
                {
                    "Effect": "Deny",
                    "Action": [
                        "iot:Publish",
                        "iot:Subscribe",
                        "iot:Receive"
                    ],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:{self.account}:topic/*",
                        f"arn:aws:iot:{self.region}:{self.account}:topicfilter/*"
                    ],
                    "Condition": {
                        "StringNotEquals": {
                            "iot:Connection.Thing.ThingName": "${iot:ClientId}"
                        }
                    }
                }
            ]
        }
        
        device_policy = iot.CfnPolicy(
            self, "EnhancedDevicePolicy",
            policy_name=f"aquachain-device-policy-{self.config['environment']}",
            policy_document=policy_document
        )
        
        return device_policy
    
    def _enable_iot_logging(self):
        """
        Enable comprehensive IoT Core logging
        """
        # Create log group for IoT logs
        log_group = logs.LogGroup(
            self, "IoTLogGroup",
            log_group_name=f"/aws/iot/aquachain-{self.config['environment']}",
            retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Create IAM role for IoT logging
        logging_role = iam.Role(
            self, "IoTLoggingRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
            description="Role for IoT Core to write logs to CloudWatch"
        )
        
        logging_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:PutMetricFilter",
                    "logs:PutRetentionPolicy"
                ],
                resources=[log_group.log_group_arn]
            )
        )
        
        # Enable IoT logging (requires AWS CLI or custom resource)
        # Note: This is typically done via AWS CLI:
        # aws iot set-v2-logging-options --role-arn <role-arn> --default-log-level INFO
        
        CfnOutput(
            self, "IoTLoggingRoleArn",
            value=logging_role.role_arn,
            description="IoT Logging Role ARN - Use with: aws iot set-v2-logging-options"
        )
    
    def _create_security_monitoring(self):
        """
        Create CloudWatch alarms for IoT security events
        """
        # Create SNS topic for security alerts
        security_topic = sns.Topic(
            self, "IoTSecurityAlertsTopic",
            topic_name=f"aquachain-iot-security-{self.config['environment']}",
            display_name="IoT Security Alerts"
        )
        
        # Alarm for connection failures
        connection_failure_alarm = cloudwatch.Alarm(
            self, "ConnectionFailureAlarm",
            alarm_name=f"aquachain-iot-connection-failures-{self.config['environment']}",
            alarm_description="Alert on high rate of IoT connection failures",
            metric=cloudwatch.Metric(
                namespace="AWS/IoT",
                metric_name="Connect.ClientError",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        connection_failure_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(security_topic)
        )
        
        # Alarm for authentication failures
        auth_failure_alarm = cloudwatch.Alarm(
            self, "AuthFailureAlarm",
            alarm_name=f"aquachain-iot-auth-failures-{self.config['environment']}",
            alarm_description="Alert on IoT authentication failures",
            metric=cloudwatch.Metric(
                namespace="AWS/IoT",
                metric_name="Connect.AuthError",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=5,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        auth_failure_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(security_topic)
        )
        
        # Alarm for publish failures (may indicate policy violations)
        publish_failure_alarm = cloudwatch.Alarm(
            self, "PublishFailureAlarm",
            alarm_name=f"aquachain-iot-publish-failures-{self.config['environment']}",
            alarm_description="Alert on IoT publish failures",
            metric=cloudwatch.Metric(
                namespace="AWS/IoT",
                metric_name="PublishIn.ClientError",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        publish_failure_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(security_topic)
        )
    
    def _enable_fleet_indexing(self):
        """
        Enable fleet indexing for device management and security auditing
        """
        # Fleet indexing configuration (requires custom resource or AWS CLI)
        # aws iot update-indexing-configuration \
        #   --thing-indexing-configuration thingIndexingMode=REGISTRY_AND_SHADOW
        
        CfnOutput(
            self, "FleetIndexingCommand",
            value=f"aws iot update-indexing-configuration --thing-indexing-configuration thingIndexingMode=REGISTRY_AND_SHADOW --region {self.region}",
            description="Command to enable fleet indexing"
        )
    
    def _create_outputs(self):
        """
        Export IoT security resources
        """
        CfnOutput(
            self, "DevicePolicyName",
            value=self.device_policy.policy_name,
            export_name=f"{Stack.of(self).stack_name}-DevicePolicyName",
            description="IoT Device Policy Name"
        )
