"""
Automated Model Deployment with Blue-Green Strategy
Implements Lambda alias-based deployment with traffic shifting and rollback
"""

import boto3
import json
from datetime import datetime
from typing import Dict, Optional
import time


class ModelDeploymentManager:
    """
    Manages blue-green deployment of ML models using Lambda aliases
    """
    
    def __init__(self, lambda_function_name: str, s3_bucket: str, region: str = 'us-east-1'):
        """
        Initialize deployment manager
        
        Args:
            lambda_function_name: Name of ML inference Lambda function
            s3_bucket: S3 bucket for model artifacts
            region: AWS region
        """
        self.lambda_function_name = lambda_function_name
        self.s3_bucket = s3_bucket
        self.region = region
        
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Deployment configuration
        self.production_alias = 'production'
        self.staging_alias = 'staging'
        self.traffic_shift_interval = 300  # 5 minutes between shifts
        self.traffic_shift_increments = [0.1, 0.25, 0.5, 0.75, 1.0]  # 10%, 25%, 50%, 75%, 100%
    
    def deploy_new_model(self, model_version: str, model_artifacts_s3_uri: str,
                        auto_promote: bool = False) -> Dict:
        """
        Deploy new model version with blue-green strategy
        
        Args:
            model_version: Version identifier for the model
            model_artifacts_s3_uri: S3 URI containing model artifacts
            auto_promote: If True, automatically promote to production after validation
            
        Returns:
            Deployment status dictionary
        """
        print(f"Starting deployment of model version {model_version}")
        
        # Step 1: Update Lambda environment with new model version
        new_version = self._update_lambda_function(model_version, model_artifacts_s3_uri)
        
        # Step 2: Update staging alias to point to new version
        self._update_alias(self.staging_alias, new_version)
        print(f"Staging alias updated to version {new_version}")
        
        # Step 3: Run validation tests on staging
        validation_passed = self._validate_staging_deployment(new_version)
        
        if not validation_passed:
            print("Staging validation failed. Deployment aborted.")
            return {
                'status': 'failed',
                'reason': 'staging_validation_failed',
                'version': new_version
            }
        
        print("Staging validation passed")
        
        # Step 4: Begin gradual traffic shift to production
        if auto_promote:
            shift_result = self._gradual_traffic_shift(new_version)
            
            if shift_result['status'] == 'success':
                print(f"Model version {model_version} successfully deployed to production")
                return {
                    'status': 'success',
                    'version': new_version,
                    'model_version': model_version,
                    'deployment_time': datetime.utcnow().isoformat()
                }
            else:
                print(f"Traffic shift failed. Rolling back to previous version.")
                self._rollback_deployment()
                return {
                    'status': 'failed',
                    'reason': 'traffic_shift_failed',
                    'version': new_version
                }
        else:
            print(f"Model deployed to staging. Manual promotion required.")
            return {
                'status': 'staged',
                'version': new_version,
                'model_version': model_version,
                'staging_time': datetime.utcnow().isoformat()
            }
    
    def _update_lambda_function(self, model_version: str, model_s3_uri: str) -> str:
        """
        Update Lambda function with new model version
        
        Returns:
            New Lambda version number
        """
        # Update environment variables with new model version
        response = self.lambda_client.update_function_configuration(
            FunctionName=self.lambda_function_name,
            Environment={
                'Variables': {
                    'MODEL_VERSION': model_version,
                    'MODEL_S3_URI': model_s3_uri,
                    'MODEL_BUCKET': self.s3_bucket
                }
            }
        )
        
        # Wait for update to complete
        waiter = self.lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=self.lambda_function_name)
        
        # Publish new version
        version_response = self.lambda_client.publish_version(
            FunctionName=self.lambda_function_name,
            Description=f'Model version {model_version}'
        )
        
        return version_response['Version']
    
    def _update_alias(self, alias_name: str, version: str, 
                     routing_config: Optional[Dict] = None):
        """
        Update Lambda alias to point to specific version
        
        Args:
            alias_name: Name of the alias
            version: Lambda version number
            routing_config: Optional routing configuration for traffic splitting
        """
        try:
            if routing_config:
                self.lambda_client.update_alias(
                    FunctionName=self.lambda_function_name,
                    Name=alias_name,
                    FunctionVersion=version,
                    RoutingConfig=routing_config
                )
            else:
                self.lambda_client.update_alias(
                    FunctionName=self.lambda_function_name,
                    Name=alias_name,
                    FunctionVersion=version
                )
        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Create alias if it doesn't exist
            self.lambda_client.create_alias(
                FunctionName=self.lambda_function_name,
                Name=alias_name,
                FunctionVersion=version,
                Description=f'{alias_name.capitalize()} environment'
            )
    
    def _validate_staging_deployment(self, version: str) -> bool:
        """
        Validate staging deployment with test invocations
        
        Args:
            version: Lambda version to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        print("Running staging validation tests...")
        
        # Test cases with different scenarios
        test_cases = [
            # Normal water quality
            {
                'deviceId': 'TEST-001',
                'timestamp': datetime.utcnow().isoformat(),
                'readings': {
                    'pH': 7.0,
                    'turbidity': 1.5,
                    'tds': 200,
                    'temperature': 25.0,
                    'humidity': 60.0
                },
                'location': {'latitude': 10.0, 'longitude': 76.0}
            },
            # Contamination scenario
            {
                'deviceId': 'TEST-002',
                'timestamp': datetime.utcnow().isoformat(),
                'readings': {
                    'pH': 4.5,
                    'turbidity': 50.0,
                    'tds': 2000,
                    'temperature': 25.0,
                    'humidity': 60.0
                },
                'location': {'latitude': 10.0, 'longitude': 76.0}
            },
            # Sensor fault scenario
            {
                'deviceId': 'TEST-003',
                'timestamp': datetime.utcnow().isoformat(),
                'readings': {
                    'pH': 12.0,
                    'turbidity': 1.0,
                    'tds': 200,
                    'temperature': -5.0,
                    'humidity': 60.0
                },
                'location': {'latitude': 10.0, 'longitude': 76.0}
            }
        ]
        
        passed_tests = 0
        
        for i, test_case in enumerate(test_cases):
            try:
                response = self.lambda_client.invoke(
                    FunctionName=self.lambda_function_name,
                    Qualifier=self.staging_alias,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_case)
                )
                
                result = json.loads(response['Payload'].read())
                
                # Check if response is valid
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    if 'wqi' in body and 'anomalyType' in body:
                        passed_tests += 1
                        print(f"  Test {i+1}: PASS (WQI={body['wqi']}, Anomaly={body['anomalyType']})")
                    else:
                        print(f"  Test {i+1}: FAIL (Invalid response format)")
                else:
                    print(f"  Test {i+1}: FAIL (Status code: {result.get('statusCode')})")
                    
            except Exception as e:
                print(f"  Test {i+1}: FAIL (Exception: {e})")
        
        success_rate = passed_tests / len(test_cases)
        print(f"Validation success rate: {success_rate*100:.1f}%")
        
        return success_rate >= 0.8  # Require 80% success rate
    
    def _gradual_traffic_shift(self, new_version: str) -> Dict:
        """
        Gradually shift traffic from old version to new version
        
        Args:
            new_version: New Lambda version to shift traffic to
            
        Returns:
            Status dictionary
        """
        print("Starting gradual traffic shift...")
        
        # Get current production version
        alias_info = self.lambda_client.get_alias(
            FunctionName=self.lambda_function_name,
            Name=self.production_alias
        )
        old_version = alias_info['FunctionVersion']
        
        print(f"Shifting traffic from version {old_version} to {new_version}")
        
        for i, traffic_weight in enumerate(self.traffic_shift_increments):
            print(f"\nShift {i+1}/{len(self.traffic_shift_increments)}: {traffic_weight*100:.0f}% to new version")
            
            # Update alias with traffic split
            routing_config = {
                'AdditionalVersionWeights': {
                    new_version: traffic_weight
                }
            }
            
            self._update_alias(self.production_alias, old_version, routing_config)
            
            # Monitor metrics during shift
            if traffic_weight < 1.0:  # Don't wait after final shift
                print(f"Monitoring for {self.traffic_shift_interval} seconds...")
                time.sleep(self.traffic_shift_interval)
                
                # Check metrics
                metrics_ok = self._check_deployment_metrics(new_version)
                
                if not metrics_ok:
                    print("Metrics degraded. Aborting traffic shift.")
                    return {'status': 'failed', 'reason': 'metrics_degraded'}
        
        # Final shift: 100% to new version
        self._update_alias(self.production_alias, new_version)
        print("Traffic shift complete. 100% on new version.")
        
        return {'status': 'success'}
    
    def _check_deployment_metrics(self, version: str) -> bool:
        """
        Check CloudWatch metrics for deployment health
        
        Args:
            version: Lambda version to check
            
        Returns:
            True if metrics are healthy, False otherwise
        """
        # Check error rate
        error_rate = self._get_error_rate(version)
        
        # Check latency
        p99_latency = self._get_p99_latency(version)
        
        print(f"  Error rate: {error_rate*100:.2f}%")
        print(f"  P99 latency: {p99_latency:.0f}ms")
        
        # Thresholds
        max_error_rate = 0.05  # 5%
        max_p99_latency = 15000  # 15 seconds
        
        return error_rate < max_error_rate and p99_latency < max_p99_latency
    
    def _get_error_rate(self, version: str) -> float:
        """Get error rate for specific Lambda version"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': self.lambda_function_name},
                    {'Name': 'Resource', 'Value': f'{self.lambda_function_name}:{version}'}
                ],
                StartTime=datetime.utcnow().timestamp() - 300,  # Last 5 minutes
                EndTime=datetime.utcnow().timestamp(),
                Period=300,
                Statistics=['Sum']
            )
            
            errors = sum(dp['Sum'] for dp in response['Datapoints'])
            
            # Get invocation count
            inv_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': self.lambda_function_name},
                    {'Name': 'Resource', 'Value': f'{self.lambda_function_name}:{version}'}
                ],
                StartTime=datetime.utcnow().timestamp() - 300,
                EndTime=datetime.utcnow().timestamp(),
                Period=300,
                Statistics=['Sum']
            )
            
            invocations = sum(dp['Sum'] for dp in inv_response['Datapoints'])
            
            if invocations > 0:
                return errors / invocations
            return 0.0
            
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return 0.0
    
    def _get_p99_latency(self, version: str) -> float:
        """Get P99 latency for specific Lambda version"""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': self.lambda_function_name},
                    {'Name': 'Resource', 'Value': f'{self.lambda_function_name}:{version}'}
                ],
                StartTime=datetime.utcnow().timestamp() - 300,
                EndTime=datetime.utcnow().timestamp(),
                Period=300,
                Statistics=['Maximum'],
                ExtendedStatistics=['p99']
            )
            
            if response['Datapoints']:
                return response['Datapoints'][0].get('p99', 0)
            return 0.0
            
        except Exception as e:
            print(f"Error getting latency metrics: {e}")
            return 0.0
    
    def _rollback_deployment(self):
        """Rollback to previous production version"""
        print("Rolling back deployment...")
        
        # Get version history
        versions = self.lambda_client.list_versions_by_function(
            FunctionName=self.lambda_function_name
        )
        
        # Get current production alias
        alias_info = self.lambda_client.get_alias(
            FunctionName=self.lambda_function_name,
            Name=self.production_alias
        )
        
        current_version = alias_info['FunctionVersion']
        
        # Find previous version
        version_numbers = [int(v['Version']) for v in versions['Versions'] 
                          if v['Version'] != '$LATEST']
        version_numbers.sort(reverse=True)
        
        if len(version_numbers) >= 2:
            previous_version = str(version_numbers[1])
            
            # Revert production alias
            self._update_alias(self.production_alias, previous_version)
            print(f"Rolled back from version {current_version} to {previous_version}")
        else:
            print("No previous version available for rollback")
    
    def promote_staging_to_production(self):
        """Manually promote staging version to production"""
        # Get staging version
        staging_info = self.lambda_client.get_alias(
            FunctionName=self.lambda_function_name,
            Name=self.staging_alias
        )
        
        staging_version = staging_info['FunctionVersion']
        
        print(f"Promoting staging version {staging_version} to production")
        
        # Perform gradual traffic shift
        return self._gradual_traffic_shift(staging_version)
    
    def get_deployment_status(self) -> Dict:
        """Get current deployment status"""
        try:
            production_info = self.lambda_client.get_alias(
                FunctionName=self.lambda_function_name,
                Name=self.production_alias
            )
            
            staging_info = self.lambda_client.get_alias(
                FunctionName=self.lambda_function_name,
                Name=self.staging_alias
            )
            
            return {
                'production': {
                    'version': production_info['FunctionVersion'],
                    'description': production_info.get('Description', ''),
                    'routing_config': production_info.get('RoutingConfig', {})
                },
                'staging': {
                    'version': staging_info['FunctionVersion'],
                    'description': staging_info.get('Description', '')
                }
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    """Example usage"""
    
    # Configuration
    lambda_function_name = "aquachain-ml-inference"
    s3_bucket = "aquachain-data-lake"
    
    # Initialize deployment manager
    deployer = ModelDeploymentManager(lambda_function_name, s3_bucket)
    
    # Deploy new model
    result = deployer.deploy_new_model(
        model_version="2.0",
        model_artifacts_s3_uri="s3://aquachain-data-lake/ml-models/v2.0/",
        auto_promote=False  # Manual promotion required
    )
    
    print(f"\nDeployment result: {json.dumps(result, indent=2)}")
    
    # Check deployment status
    status = deployer.get_deployment_status()
    print(f"\nDeployment status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    main()
