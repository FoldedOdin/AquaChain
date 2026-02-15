"""
ML Pipeline Orchestrator
Coordinates the complete ML lifecycle from data generation to deployment
"""

import boto3
import json
from datetime import datetime
from typing import Dict
import logging

from synthetic_data_generator import SyntheticDataGenerator
from sagemaker_pipeline import AquaChainMLPipeline
from model_deployment import ModelDeploymentManager
from model_monitoring import ModelMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPipelineOrchestrator:
    """
    Orchestrates the complete ML pipeline lifecycle
    """
    
    def __init__(self, config: Dict):
        """
        Initialize orchestrator with configuration
        
        Args:
            config: Configuration dictionary with AWS settings
        """
        self.config = config
        self.s3_client = boto3.client('s3', region_name=config['region'])
        
        # Initialize components
        self.data_generator = SyntheticDataGenerator(seed=config.get('seed', 42))
        self.sagemaker_pipeline = AquaChainMLPipeline(
            role_arn=config['sagemaker_role_arn'],
            bucket_name=config['s3_bucket'],
            region=config['region']
        )
        self.deployment_manager = ModelDeploymentManager(
            lambda_function_name=config['lambda_function_name'],
            s3_bucket=config['s3_bucket'],
            region=config['region']
        )
        self.model_monitor = ModelMonitor(
            model_name=config['model_name'],
            s3_bucket=config['s3_bucket'],
            region=config['region']
        )
    
    def run_full_pipeline(self, auto_deploy: bool = False) -> Dict:
        """
        Run complete ML pipeline from data generation to deployment
        
        Args:
            auto_deploy: If True, automatically deploy to production after training
            
        Returns:
            Pipeline execution summary
        """
        logger.info("Starting full ML pipeline execution")
        
        results = {
            'pipeline_start': datetime.utcnow().isoformat(),
            'steps': {}
        }
        
        try:
            # Step 1: Generate synthetic training data
            logger.info("Step 1: Generating synthetic training data")
            data_result = self._generate_and_upload_data()
            results['steps']['data_generation'] = data_result
            
            # Step 2: Deploy SageMaker pipeline
            logger.info("Step 2: Deploying SageMaker training pipeline")
            pipeline_result = self._deploy_training_pipeline()
            results['steps']['pipeline_deployment'] = pipeline_result
            
            # Step 3: Start pipeline execution
            logger.info("Step 3: Starting pipeline execution")
            execution_result = self._start_pipeline_execution()
            results['steps']['pipeline_execution'] = execution_result
            
            # Step 4: Wait for training completion (in production, use EventBridge)
            logger.info("Step 4: Training pipeline started. Monitor via SageMaker console.")
            results['steps']['training_status'] = 'in_progress'
            
            # Step 5: Model deployment (manual or automatic)
            if auto_deploy:
                logger.info("Step 5: Automatic deployment enabled (will deploy after training)")
                results['steps']['deployment'] = 'scheduled'
            else:
                logger.info("Step 5: Manual deployment required after training completion")
                results['steps']['deployment'] = 'manual_approval_required'
            
            results['status'] = 'success'
            results['pipeline_end'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            results['pipeline_end'] = datetime.utcnow().isoformat()
        
        return results
    
    def _generate_and_upload_data(self) -> Dict:
        """Generate synthetic data and upload to S3"""
        
        # Generate dataset
        features_df, wqi_targets, anomaly_labels = self.data_generator.generate_dataset(
            n_samples=self.config.get('training_samples', 50000),
            contamination_rate=0.05,
            sensor_fault_rate=0.03
        )
        
        # Save locally
        local_path = '/tmp/training_data.csv'
        self.data_generator.save_dataset(
            features_df, wqi_targets, anomaly_labels, local_path
        )
        
        # Upload to S3
        s3_key = f"training-data/raw/training_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        self.s3_client.upload_file(
            local_path,
            self.config['s3_bucket'],
            s3_key
        )
        
        logger.info(f"Training data uploaded to s3://{self.config['s3_bucket']}/{s3_key}")
        
        return {
            'samples': len(features_df),
            's3_uri': f"s3://{self.config['s3_bucket']}/{s3_key}",
            'contamination_count': int((anomaly_labels == 2).sum()),
            'sensor_fault_count': int((anomaly_labels == 1).sum())
        }
    
    def _deploy_training_pipeline(self) -> Dict:
        """Deploy SageMaker training pipeline"""
        
        # Create model package group
        self.sagemaker_pipeline.create_model_package_group()
        
        # Deploy pipeline
        pipeline = self.sagemaker_pipeline.deploy_pipeline()
        
        return {
            'pipeline_name': self.sagemaker_pipeline.pipeline_name,
            'status': 'deployed'
        }
    
    def _start_pipeline_execution(self) -> Dict:
        """Start SageMaker pipeline execution"""
        
        execution = self.sagemaker_pipeline.start_pipeline_execution()
        
        return {
            'execution_arn': execution['PipelineExecutionArn'],
            'status': 'started'
        }
    
    def deploy_approved_model(self, model_package_arn: str, 
                             model_version: str) -> Dict:
        """
        Deploy an approved model from the registry
        
        Args:
            model_package_arn: ARN of approved model package
            model_version: Version identifier
            
        Returns:
            Deployment result
        """
        logger.info(f"Deploying approved model: {model_package_arn}")
        
        # Extract model artifacts S3 URI from model package
        sm_client = boto3.client('sagemaker', region_name=self.config['region'])
        model_package = sm_client.describe_model_package(
            ModelPackageName=model_package_arn
        )
        
        model_s3_uri = model_package['InferenceSpecification']['Containers'][0]['ModelDataUrl']
        
        # Deploy using blue-green strategy
        result = self.deployment_manager.deploy_new_model(
            model_version=model_version,
            model_artifacts_s3_uri=model_s3_uri,
            auto_promote=self.config.get('auto_promote', False)
        )
        
        return result
    
    def monitor_production_model(self) -> Dict:
        """
        Monitor production model performance
        
        Returns:
            Monitoring results
        """
        logger.info("Monitoring production model performance")
        
        # Calculate performance metrics
        performance = self.model_monitor.calculate_model_performance(hours=24)
        
        # Check for performance degradation
        # (In production, compare against baseline metrics)
        
        return performance
    
    def check_data_drift(self, baseline_data_s3_uri: str,
                        current_data_s3_uri: str) -> Dict:
        """
        Check for data drift between baseline and current data
        
        Args:
            baseline_data_s3_uri: S3 URI of baseline data
            current_data_s3_uri: S3 URI of current production data
            
        Returns:
            Drift detection results
        """
        logger.info("Checking for data drift")
        
        # Load baseline and current data
        # (Implementation would load from S3 and extract features)
        
        # For now, return placeholder
        return {
            'status': 'not_implemented',
            'message': 'Load data from S3 and call model_monitor.detect_data_drift()'
        }
    
    def get_pipeline_status(self) -> Dict:
        """
        Get current status of all pipeline components
        
        Returns:
            Status summary
        """
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # SageMaker pipeline status
        try:
            sm_client = boto3.client('sagemaker', region_name=self.config['region'])
            executions = sm_client.list_pipeline_executions(
                PipelineName=self.sagemaker_pipeline.pipeline_name,
                MaxResults=1
            )
            
            if executions['PipelineExecutionSummaries']:
                latest = executions['PipelineExecutionSummaries'][0]
                status['components']['training_pipeline'] = {
                    'status': latest['PipelineExecutionStatus'],
                    'start_time': latest['StartTime'].isoformat()
                }
        except Exception as e:
            status['components']['training_pipeline'] = {'error': str(e)}
        
        # Deployment status
        try:
            deployment_status = self.deployment_manager.get_deployment_status()
            status['components']['deployment'] = deployment_status
        except Exception as e:
            status['components']['deployment'] = {'error': str(e)}
        
        # Model versions
        try:
            versions = self.sagemaker_pipeline.list_model_versions()
            status['components']['model_registry'] = {
                'total_versions': len(versions),
                'latest_version': versions[0] if versions else None
            }
        except Exception as e:
            status['components']['model_registry'] = {'error': str(e)}
        
        return status


def main():
    """
    Example usage of ML Pipeline Orchestrator
    """
    
    # Configuration
    config = {
        'region': 'us-east-1',
        's3_bucket': 'aquachain-data-lake',
        'sagemaker_role_arn': 'arn:aws:iam::ACCOUNT_ID:role/SageMakerExecutionRole',
        'lambda_function_name': 'aquachain-ml-inference',
        'model_name': 'aquachain-wqi-model',
        'training_samples': 50000,
        'seed': 42,
        'auto_promote': False
    }
    
    # Initialize orchestrator
    orchestrator = MLPipelineOrchestrator(config)
    
    # Run full pipeline
    result = orchestrator.run_full_pipeline(auto_deploy=False)
    
    print("\nPipeline Execution Summary:")
    print(json.dumps(result, indent=2))
    
    # Get pipeline status
    status = orchestrator.get_pipeline_status()
    print("\nPipeline Status:")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
