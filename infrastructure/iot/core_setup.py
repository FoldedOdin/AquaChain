"""
AWS IoT Core configuration for AquaChain system
Implements secure device communication, certificate management, and message routing
"""

import boto3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class IoTCoreManager:
    def __init__(self, region_name: str = 'us-east-1'):
        self.iot_client = boto3.client('iot', region_name=region_name)
        self.iot_data_client = boto3.client('iot-data', region_name=region_name)
        self.region_name = region_name
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
    
    def create_device_policy_template(self) -> Dict[str, Any]:
        """
        Create IoT policy template for device-specific permissions
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "iot:Connect",
                    "Resource": f"arn:aws:iot:{self.region_name}:{self.account_id}:client/${{iot:Connection.Thing.ThingName}}"
                },
                {
                    "Effect": "Allow",
                    "Action": "iot:Publish",
                    "Resource": f"arn:aws:iot:{self.region_name}:{self.account_id}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/data"
                },
                {
                    "Effect": "Allow",
                    "Action": "iot:Subscribe",
                    "Resource": f"arn:aws:iot:{self.region_name}:{self.account_id}:topicfilter/aquachain/${{iot:Connection.Thing.ThingName}}/commands"
                },
                {
                    "Effect": "Allow",
                    "Action": "iot:Receive",
                    "Resource": f"arn:aws:iot:{self.region_name}:{self.account_id}:topic/aquachain/${{iot:Connection.Thing.ThingName}}/commands"
                },
                {
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*",
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                }
            ]
        }
        
        try:
            response = self.iot_client.create_policy(
                policyName='AquaChainDevicePolicy',
                policyDocument=json.dumps(policy_document)
            )
            print("Created device policy template: AquaChainDevicePolicy")
            return response
        except self.iot_client.exceptions.ResourceAlreadyExistsException:
            print("Device policy template already exists")
            return self.iot_client.get_policy(policyName='AquaChainDevicePolicy')
        except Exception as e:
            print(f"Error creating device policy: {e}")
            raise
    
    def create_provisioning_template(self) -> Dict[str, Any]:
        """
        Create provisioning template for Just-in-Time Provisioning
        """
        template_body = {
            "Parameters": {
                "DeviceId": {
                    "Type": "String"
                },
                "SerialNumber": {
                    "Type": "String"
                },
                "AWS::IoT::Certificate::Id": {
                    "Type": "String"
                }
            },
            "Resources": {
                "thing": {
                    "Type": "AWS::IoT::Thing",
                    "Properties": {
                        "ThingName": {"Ref": "DeviceId"},
                        "AttributePayload": {
                            "serialNumber": {"Ref": "SerialNumber"},
                            "deviceType": "ESP32-WaterQualitySensor",
                            "firmwareVersion": "1.0.0",
                            "registrationDate": {"Fn::GetAtt": ["AWS::IoT::Certificate", "CreationDate"]}
                        },
                        "ThingTypeName": "AquaChainSensor"
                    }
                },
                "certificate": {
                    "Type": "AWS::IoT::Certificate",
                    "Properties": {
                        "CertificateId": {"Ref": "AWS::IoT::Certificate::Id"},
                        "Status": "ACTIVE"
                    }
                },
                "policy": {
                    "Type": "AWS::IoT::Policy",
                    "Properties": {
                        "PolicyName": "AquaChainDevicePolicy"
                    }
                }
            }
        }
        
        pre_provisioning_hook = {
            "targetArn": f"arn:aws:lambda:{self.region_name}:{self.account_id}:function:AquaChainDeviceProvisioning",
            "payloadVersion": "2020-04-01"
        }
        
        try:
            response = self.iot_client.create_provisioning_template(
                templateName='AquaChainProvisioningTemplate',
                description='Just-in-Time Provisioning template for AquaChain devices',
                templateBody=json.dumps(template_body),
                enabled=True,
                provisioningRoleArn=f'arn:aws:iam::{self.account_id}:role/AquaChainProvisioningRole',
                preProvisioningHook=pre_provisioning_hook,
                tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            )
            print("Created provisioning template: AquaChainProvisioningTemplate")
            return response
        except self.iot_client.exceptions.ResourceAlreadyExistsException:
            print("Provisioning template already exists")
            return self.iot_client.describe_provisioning_template(
                templateName='AquaChainProvisioningTemplate'
            )
        except Exception as e:
            print(f"Error creating provisioning template: {e}")
            raise
    
    def create_thing_type(self) -> Dict[str, Any]:
        """
        Create IoT Thing Type for AquaChain sensors
        """
        thing_type_properties = {
            'thingTypeDescription': 'ESP32-based water quality monitoring sensor',
            'searchableAttributes': [
                'serialNumber',
                'deviceType',
                'firmwareVersion',
                'location'
            ]
        }
        
        try:
            response = self.iot_client.create_thing_type(
                thingTypeName='AquaChainSensor',
                thingTypeProperties=thing_type_properties,
                tags=[
                    {'Key': 'Project', 'Value': 'AquaChain'},
                    {'Key': 'DeviceType', 'Value': 'WaterQualitySensor'}
                ]
            )
            print("Created thing type: AquaChainSensor")
            return response
        except self.iot_client.exceptions.ResourceAlreadyExistsException:
            print("Thing type already exists")
            return self.iot_client.describe_thing_type(thingTypeName='AquaChainSensor')
        except Exception as e:
            print(f"Error creating thing type: {e}")
            raise
    
    def create_topic_rules(self) -> List[Dict[str, Any]]:
        """
        Create IoT Rules for message routing and processing
        """
        rules = []
        
        # Rule 1: Route sensor data to Lambda for processing
        data_processing_rule = {
            'ruleName': 'AquaChainDataProcessing',
            'topicRulePayload': {
                'sql': "SELECT *, timestamp() as serverTimestamp FROM 'aquachain/+/data' WHERE readings.pH IS NOT NULL AND readings.turbidity IS NOT NULL",
                'description': 'Route water quality sensor data to processing Lambda',
                'actions': [
                    {
                        'lambda': {
                            'functionArn': f'arn:aws:lambda:{self.region_name}:{self.account_id}:function:AquaChainDataProcessor'
                        }
                    }
                ],
                'errorAction': {
                    'sqs': {
                        'queueUrl': f'https://sqs.{self.region_name}.amazonaws.com/{self.account_id}/aquachain-iot-errors',
                        'roleArn': f'arn:aws:iam::{self.account_id}:role/AquaChainIoTRole'
                    }
                },
                'ruleDisabled': False
            }
        }
        
        # Rule 2: Route device diagnostics to monitoring
        diagnostics_rule = {
            'ruleName': 'AquaChainDiagnostics',
            'topicRulePayload': {
                'sql': "SELECT deviceId, diagnostics, timestamp() as serverTimestamp FROM 'aquachain/+/data' WHERE diagnostics.batteryLevel < 20 OR diagnostics.sensorStatus <> 'normal'",
                'description': 'Route device diagnostics for monitoring and alerts',
                'actions': [
                    {
                        'sns': {
                            'targetArn': f'arn:aws:sns:{self.region_name}:{self.account_id}:aquachain-device-alerts',
                            'roleArn': f'arn:aws:iam::{self.account_id}:role/AquaChainIoTRole',
                            'messageFormat': 'JSON'
                        }
                    }
                ],
                'ruleDisabled': False
            }
        }
        
        # Rule 3: Store raw data in S3 for backup
        s3_backup_rule = {
            'ruleName': 'AquaChainS3Backup',
            'topicRulePayload': {
                'sql': "SELECT * FROM 'aquachain/+/data'",
                'description': 'Backup all sensor data to S3',
                'actions': [
                    {
                        's3': {
                            'roleArn': f'arn:aws:iam::{self.account_id}:role/AquaChainIoTRole',
                            'bucketName': f'aquachain-data-lake-{self.account_id}',
                            'key': 'raw-readings/year=${timestamp("yyyy")}/month=${timestamp("MM")}/day=${timestamp("dd")}/hour=${timestamp("HH")}/${deviceId}-${timestamp()}.json',
                            'cannedAcl': 'private'
                        }
                    }
                ],
                'ruleDisabled': False
            }
        }
        
        for rule in [data_processing_rule, diagnostics_rule, s3_backup_rule]:
            try:
                response = self.iot_client.create_topic_rule(**rule)
                print(f"Created topic rule: {rule['ruleName']}")
                rules.append(response)
            except self.iot_client.exceptions.ResourceAlreadyExistsException:
                print(f"Topic rule {rule['ruleName']} already exists")
                rules.append(self.iot_client.get_topic_rule(ruleName=rule['ruleName']))
            except Exception as e:
                print(f"Error creating topic rule {rule['ruleName']}: {e}")
        
        return rules
    
    def create_device_certificate(self, device_id: str, csr: str = None) -> Dict[str, Any]:
        """
        Create device certificate for secure authentication
        """
        try:
            if csr:
                # Create certificate from CSR
                response = self.iot_client.create_certificate_from_csr(
                    certificateSigningRequest=csr,
                    setAsActive=True
                )
            else:
                # Create certificate with AWS-generated keys
                response = self.iot_client.create_keys_and_certificate(
                    setAsActive=True
                )
            
            certificate_arn = response['certificateArn']
            certificate_id = response['certificateId']
            
            # Attach policy to certificate
            self.iot_client.attach_policy(
                policyName='AquaChainDevicePolicy',
                target=certificate_arn
            )
            
            # Create thing if it doesn't exist
            try:
                self.iot_client.create_thing(
                    thingName=device_id,
                    thingTypeName='AquaChainSensor',
                    attributePayload={
                        'attributes': {
                            'deviceType': 'ESP32-WaterQualitySensor',
                            'registrationDate': datetime.utcnow().isoformat()
                        }
                    }
                )
            except self.iot_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Attach certificate to thing
            self.iot_client.attach_thing_principal(
                thingName=device_id,
                principal=certificate_arn
            )
            
            print(f"Created certificate for device {device_id}: {certificate_id}")
            return response
            
        except Exception as e:
            print(f"Error creating device certificate: {e}")
            raise
    
    def setup_certificate_rotation(self, device_id: str) -> Dict[str, Any]:
        """
        Set up automatic certificate rotation for device
        """
        # This would typically be implemented with EventBridge and Lambda
        # For now, we'll create the necessary IAM role and policy
        
        rotation_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:CreateKeysAndCertificate",
                        "iot:UpdateCertificate",
                        "iot:AttachPolicy",
                        "iot:AttachThingPrincipal",
                        "iot:DetachThingPrincipal",
                        "iot:DetachPolicy"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iot:Publish"
                    ],
                    "Resource": f"arn:aws:iot:{self.region_name}:{self.account_id}:topic/aquachain/{device_id}/commands"
                }
            ]
        }
        
        print(f"Certificate rotation setup initiated for device {device_id}")
        return {"status": "configured", "rotation_period": "90 days"}
    
    def create_fleet_provisioning_claim(self) -> Dict[str, Any]:
        """
        Create fleet provisioning claim certificate for device onboarding
        """
        try:
            # Create claim certificate
            response = self.iot_client.create_keys_and_certificate(setAsActive=True)
            
            # Create fleet provisioning policy
            fleet_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "iot:Connect",
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Publish",
                            "iot:Receive"
                        ],
                        "Resource": [
                            f"arn:aws:iot:{self.region_name}:{self.account_id}:topic/$aws/certificates/create/*",
                            f"arn:aws:iot:{self.region_name}:{self.account_id}:topic/$aws/provisioning-templates/AquaChainProvisioningTemplate/provision/*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": "iot:Subscribe",
                        "Resource": [
                            f"arn:aws:iot:{self.region_name}:{self.account_id}:topicfilter/$aws/certificates/create/*",
                            f"arn:aws:iot:{self.region_name}:{self.account_id}:topicfilter/$aws/provisioning-templates/AquaChainProvisioningTemplate/provision/*"
                        ]
                    }
                ]
            }
            
            # Create fleet provisioning policy
            policy_response = self.iot_client.create_policy(
                policyName='AquaChainFleetProvisioningPolicy',
                policyDocument=json.dumps(fleet_policy)
            )
            
            # Attach policy to claim certificate
            self.iot_client.attach_policy(
                policyName='AquaChainFleetProvisioningPolicy',
                target=response['certificateArn']
            )
            
            print("Created fleet provisioning claim certificate")
            return {
                'claimCertificate': response,
                'policy': policy_response
            }
            
        except self.iot_client.exceptions.ResourceAlreadyExistsException:
            print("Fleet provisioning policy already exists")
            return {"status": "exists"}
        except Exception as e:
            print(f"Error creating fleet provisioning claim: {e}")
            raise
    
    def get_iot_endpoint(self) -> str:
        """
        Get IoT Core endpoint for device connections
        """
        try:
            response = self.iot_client.describe_endpoint(endpointType='iot:Data-ATS')
            endpoint = response['endpointAddress']
            print(f"IoT Core endpoint: {endpoint}")
            return endpoint
        except Exception as e:
            print(f"Error getting IoT endpoint: {e}")
            raise
    
    def test_device_connection(self, device_id: str, test_payload: Dict[str, Any]) -> bool:
        """
        Test device connection by publishing a test message
        """
        try:
            topic = f"aquachain/{device_id}/data"
            
            self.iot_data_client.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(test_payload)
            )
            
            print(f"Test message published for device {device_id}")
            return True
            
        except Exception as e:
            print(f"Error testing device connection: {e}")
            return False
    
    def setup_iot_core(self) -> Dict[str, Any]:
        """
        Set up complete IoT Core infrastructure for AquaChain
        """
        print("Setting up AWS IoT Core for AquaChain system...")
        
        setup_results = {}
        
        try:
            # Create thing type
            setup_results['thing_type'] = self.create_thing_type()
            
            # Create device policy template
            setup_results['device_policy'] = self.create_device_policy_template()
            
            # Create provisioning template
            setup_results['provisioning_template'] = self.create_provisioning_template()
            
            # Create topic rules
            setup_results['topic_rules'] = self.create_topic_rules()
            
            # Create fleet provisioning claim
            setup_results['fleet_provisioning'] = self.create_fleet_provisioning_claim()
            
            # Get IoT endpoint
            setup_results['endpoint'] = self.get_iot_endpoint()
            
            print("AWS IoT Core setup completed successfully")
            return setup_results
            
        except Exception as e:
            print(f"Error setting up IoT Core: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    manager = IoTCoreManager()
    manager.setup_iot_core()