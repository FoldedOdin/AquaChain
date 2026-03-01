"""
SageMaker Pipeline for AquaChain ML Model Training
Implements automated training pipeline with hyperparameter tuning,
model evaluation, and model registry integration.
"""

import boto3
import sagemaker
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep, CreateModelStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.parameters import ParameterInteger, ParameterFloat, ParameterString
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.tuner import HyperparameterTuner, IntegerParameter, ContinuousParameter
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.inputs import TrainingInput
import json
from datetime import datetime


class AquaChainMLPipeline:
    """
    SageMaker Pipeline for automated ML model training and deployment
    """
    
    def __init__(self, role_arn: str, bucket_name: str, region: str = 'us-east-1'):
        """
        Initialize SageMaker pipeline
        
        Args:
            role_arn: IAM role ARN for SageMaker execution
            bucket_name: S3 bucket for pipeline artifacts
            region: AWS region
        """
        self.role_arn = role_arn
        self.bucket_name = bucket_name
        self.region = region
        
        self.sagemaker_session = sagemaker.Session(
            boto_session=boto3.Session(region_name=region)
        )
        self.sm_client = boto3.client('sagemaker', region_name=region)
        
        # Pipeline parameters
        self.pipeline_name = "aquachain-ml-training-pipeline"
        self.model_package_group_name = "aquachain-wqi-models"
    
    def create_pipeline(self) -> Pipeline:
        """
        Create complete SageMaker pipeline with all steps
        
        Returns:
            SageMaker Pipeline object
        """
        # Define pipeline parameters
        processing_instance_type = ParameterString(
            name="ProcessingInstanceType",
            default_value="ml.m5.xlarge"
        )
        
        training_instance_type = ParameterString(
            name="TrainingInstanceType",
            default_value="ml.m5.2xlarge"
        )
        
        model_approval_status = ParameterString(
            name="ModelApprovalStatus",
            default_value="PendingManualApproval"
        )
        
        min_wqi_rmse = ParameterFloat(
            name="MinWQIRMSE",
            default_value=8.0
        )
        
        min_anomaly_f1 = ParameterFloat(
            name="MinAnomalyF1Score",
            default_value=0.85
        )
        
        # Step 1: Data preprocessing
        preprocessing_step = self._create_preprocessing_step(processing_instance_type)
        
        # Step 2: Model training with hyperparameter tuning
        training_step = self._create_training_step(
            training_instance_type,
            preprocessing_step
        )
        
        # Step 3: Model evaluation
        evaluation_step = self._create_evaluation_step(
            processing_instance_type,
            training_step
        )
        
        # Step 4: Conditional model registration
        register_step = self._create_registration_step(
            training_step,
            evaluation_step,
            model_approval_status
        )
        
        # Step 5: Conditional registration based on metrics
        condition_step = self._create_condition_step(
            evaluation_step,
            register_step,
            min_wqi_rmse,
            min_anomaly_f1
        )
        
        # Create pipeline
        pipeline = Pipeline(
            name=self.pipeline_name,
            parameters=[
                processing_instance_type,
                training_instance_type,
                model_approval_status,
                min_wqi_rmse,
                min_anomaly_f1
            ],
            steps=[preprocessing_step, training_step, evaluation_step, condition_step],
            sagemaker_session=self.sagemaker_session
        )
        
        return pipeline
    
    def _create_preprocessing_step(self, instance_type: ParameterString) -> ProcessingStep:
        """Create data preprocessing step"""
        
        sklearn_processor = SKLearnProcessor(
            framework_version="1.2-1",
            role=self.role_arn,
            instance_type=instance_type,
            instance_count=1,
            base_job_name="aquachain-preprocessing",
            sagemaker_session=self.sagemaker_session
        )
        
        preprocessing_step = ProcessingStep(
            name="PreprocessData",
            processor=sklearn_processor,
            code="preprocessing_script.py",
            inputs=[
                sagemaker.processing.ProcessingInput(
                    source=f"s3://{self.bucket_name}/training-data/raw/",
                    destination="/opt/ml/processing/input"
                )
            ],
            outputs=[
                sagemaker.processing.ProcessingOutput(
                    output_name="train",
                    source="/opt/ml/processing/train",
                    destination=f"s3://{self.bucket_name}/training-data/processed/train"
                ),
                sagemaker.processing.ProcessingOutput(
                    output_name="validation",
                    source="/opt/ml/processing/validation",
                    destination=f"s3://{self.bucket_name}/training-data/processed/validation"
                ),
                sagemaker.processing.ProcessingOutput(
                    output_name="test",
                    source="/opt/ml/processing/test",
                    destination=f"s3://{self.bucket_name}/training-data/processed/test"
                )
            ]
        )
        
        return preprocessing_step
    
    def _create_training_step(self, instance_type: ParameterString,
                             preprocessing_step: ProcessingStep) -> TrainingStep:
        """Create model training step with hyperparameter tuning"""
        
        sklearn_estimator = SKLearn(
            entry_point="training_script.py",
            framework_version="1.2-1",
            role=self.role_arn,
            instance_type=instance_type,
            instance_count=1,
            base_job_name="aquachain-training",
            sagemaker_session=self.sagemaker_session,
            hyperparameters={
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2
            }
        )
        
        training_step = TrainingStep(
            name="TrainModel",
            estimator=sklearn_estimator,
            inputs={
                "train": TrainingInput(
                    s3_data=preprocessing_step.properties.ProcessingOutputConfig.Outputs[
                        "train"
                    ].S3Output.S3Uri,
                    content_type="text/csv"
                ),
                "validation": TrainingInput(
                    s3_data=preprocessing_step.properties.ProcessingOutputConfig.Outputs[
                        "validation"
                    ].S3Output.S3Uri,
                    content_type="text/csv"
                )
            }
        )
        
        return training_step
    
    def _create_evaluation_step(self, instance_type: ParameterString,
                                training_step: TrainingStep) -> ProcessingStep:
        """Create model evaluation step"""
        
        sklearn_processor = SKLearnProcessor(
            framework_version="1.2-1",
            role=self.role_arn,
            instance_type=instance_type,
            instance_count=1,
            base_job_name="aquachain-evaluation",
            sagemaker_session=self.sagemaker_session
        )
        
        evaluation_step = ProcessingStep(
            name="EvaluateModel",
            processor=sklearn_processor,
            code="evaluation_script.py",
            inputs=[
                sagemaker.processing.ProcessingInput(
                    source=training_step.properties.ModelArtifacts.S3ModelArtifacts,
                    destination="/opt/ml/processing/model"
                ),
                sagemaker.processing.ProcessingInput(
                    source=f"s3://{self.bucket_name}/training-data/processed/test/",
                    destination="/opt/ml/processing/test"
                )
            ],
            outputs=[
                sagemaker.processing.ProcessingOutput(
                    output_name="evaluation",
                    source="/opt/ml/processing/evaluation",
                    destination=f"s3://{self.bucket_name}/evaluation-results/"
                )
            ],
            property_files=[
                sagemaker.workflow.properties.PropertyFile(
                    name="EvaluationReport",
                    output_name="evaluation",
                    path="evaluation.json"
                )
            ]
        )
        
        return evaluation_step
    
    def _create_registration_step(self, training_step: TrainingStep,
                                  evaluation_step: ProcessingStep,
                                  approval_status: ParameterString) -> RegisterModel:
        """Create model registration step"""
        
        model_metrics = ModelMetrics(
            model_statistics=MetricsSource(
                s3_uri=f"{evaluation_step.properties.ProcessingOutputConfig.Outputs['evaluation'].S3Output.S3Uri}/evaluation.json",
                content_type="application/json"
            )
        )
        
        register_step = RegisterModel(
            name="RegisterModel",
            estimator=training_step.estimator,
            model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
            content_types=["application/json"],
            response_types=["application/json"],
            inference_instances=["ml.t2.medium", "ml.m5.large"],
            transform_instances=["ml.m5.large"],
            model_package_group_name=self.model_package_group_name,
            approval_status=approval_status,
            model_metrics=model_metrics
        )
        
        return register_step
    
    def _create_condition_step(self, evaluation_step: ProcessingStep,
                              register_step: RegisterModel,
                              min_wqi_rmse: ParameterFloat,
                              min_anomaly_f1: ParameterFloat) -> ConditionStep:
        """Create conditional step for model registration based on metrics"""
        
        # Condition: WQI RMSE must be below threshold
        wqi_rmse_condition = ConditionGreaterThanOrEqualTo(
            left=JsonGet(
                step_name=evaluation_step.name,
                property_file="EvaluationReport",
                json_path="wqi_metrics.rmse"
            ),
            right=min_wqi_rmse
        )
        
        # Condition: Anomaly F1 score must be above threshold
        anomaly_f1_condition = ConditionGreaterThanOrEqualTo(
            left=JsonGet(
                step_name=evaluation_step.name,
                property_file="EvaluationReport",
                json_path="anomaly_metrics.f1_score"
            ),
            right=min_anomaly_f1
        )
        
        condition_step = ConditionStep(
            name="CheckModelQuality",
            conditions=[wqi_rmse_condition, anomaly_f1_condition],
            if_steps=[register_step],
            else_steps=[]
        )
        
        return condition_step
    
    def create_hyperparameter_tuning_job(self, training_data_uri: str,
                                        validation_data_uri: str) -> str:
        """
        Create hyperparameter tuning job with Bayesian optimization
        
        Args:
            training_data_uri: S3 URI for training data
            validation_data_uri: S3 URI for validation data
            
        Returns:
            Tuning job name
        """
        sklearn_estimator = SKLearn(
            entry_point="training_script.py",
            framework_version="1.2-1",
            role=self.role_arn,
            instance_type="ml.m5.2xlarge",
            instance_count=1,
            base_job_name="aquachain-hpo",
            sagemaker_session=self.sagemaker_session
        )
        
        # Define hyperparameter ranges
        hyperparameter_ranges = {
            "n_estimators": IntegerParameter(50, 300),
            "max_depth": IntegerParameter(5, 30),
            "min_samples_split": IntegerParameter(2, 20),
            "min_samples_leaf": IntegerParameter(1, 10),
            "max_features": ContinuousParameter(0.3, 1.0)
        }
        
        # Define objective metric
        objective_metric_name = "validation:rmse"
        objective_type = "Minimize"
        
        # Create tuner
        tuner = HyperparameterTuner(
            estimator=sklearn_estimator,
            objective_metric_name=objective_metric_name,
            hyperparameter_ranges=hyperparameter_ranges,
            metric_definitions=[
                {"Name": "validation:rmse", "Regex": "validation_rmse: ([0-9\\.]+)"},
                {"Name": "validation:r2", "Regex": "validation_r2: ([0-9\\.]+)"}
            ],
            max_jobs=20,
            max_parallel_jobs=4,
            objective_type=objective_type,
            strategy="Bayesian",
            base_tuning_job_name="aquachain-hpo"
        )
        
        # Start tuning job
        tuner.fit({
            "train": training_data_uri,
            "validation": validation_data_uri
        })
        
        return tuner.latest_tuning_job.name
    
    def deploy_pipeline(self):
        """Deploy the SageMaker pipeline"""
        pipeline = self.create_pipeline()
        
        # Upsert pipeline
        pipeline.upsert(role_arn=self.role_arn)
        
        print(f"Pipeline '{self.pipeline_name}' deployed successfully")
        return pipeline
    
    def start_pipeline_execution(self, parameters: dict = None):
        """
        Start pipeline execution
        
        Args:
            parameters: Optional pipeline parameters to override defaults
        """
        execution = self.sm_client.start_pipeline_execution(
            PipelineName=self.pipeline_name,
            PipelineParameters=parameters or [],
            PipelineExecutionDisplayName=f"execution-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        )
        
        print(f"Pipeline execution started: {execution['PipelineExecutionArn']}")
        return execution
    
    def create_model_package_group(self):
        """Create model package group for model registry"""
        try:
            response = self.sm_client.create_model_package_group(
                ModelPackageGroupName=self.model_package_group_name,
                ModelPackageGroupDescription="AquaChain WQI prediction models"
            )
            print(f"Model package group created: {response['ModelPackageGroupArn']}")
        except self.sm_client.exceptions.ResourceInUse:
            print(f"Model package group '{self.model_package_group_name}' already exists")
    
    def list_model_versions(self):
        """List all model versions in the registry"""
        response = self.sm_client.list_model_packages(
            ModelPackageGroupName=self.model_package_group_name,
            SortBy="CreationTime",
            SortOrder="Descending"
        )
        
        return response['ModelPackageSummaryList']
    
    def approve_model(self, model_package_arn: str):
        """
        Approve a model for deployment
        
        Args:
            model_package_arn: ARN of the model package to approve
        """
        self.sm_client.update_model_package(
            ModelPackageArn=model_package_arn,
            ModelApprovalStatus="Approved"
        )
        print(f"Model approved: {model_package_arn}")
    
    def reject_model(self, model_package_arn: str, reason: str):
        """
        Reject a model
        
        Args:
            model_package_arn: ARN of the model package to reject
            reason: Reason for rejection
        """
        self.sm_client.update_model_package(
            ModelPackageArn=model_package_arn,
            ModelApprovalStatus="Rejected",
            ApprovalDescription=reason
        )
        print(f"Model rejected: {model_package_arn}")


def main():
    """Example usage of the SageMaker pipeline"""
    
    # Configuration
    role_arn = "arn:aws:iam::ACCOUNT_ID:role/SageMakerExecutionRole"
    bucket_name = "aquachain-data-lake"
    region = "us-east-1"
    
    # Initialize pipeline
    pipeline = AquaChainMLPipeline(role_arn, bucket_name, region)
    
    # Create model package group
    pipeline.create_model_package_group()
    
    # Deploy pipeline
    pipeline.deploy_pipeline()
    
    # Start pipeline execution
    pipeline.start_pipeline_execution()
    
    print("SageMaker pipeline setup complete!")


if __name__ == "__main__":
    main()
