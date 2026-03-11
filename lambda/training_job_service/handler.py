"""
SageMaker Training Job Service

This Lambda function manages SageMaker training jobs for model retraining.
It provides endpoints to create, monitor, and manage training jobs.
"""

import json
import logging
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Initialize AWS clients
sagemaker_client = boto3.client("sagemaker")
s3_client = boto3.client("s3")

# Environment variables
MODEL_BUCKET = os.getenv("MODEL_BUCKET")
SAGEMAKER_ROLE_ARN = os.getenv("SAGEMAKER_ROLE_ARN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for training job operations
    
    Args:
        event: Lambda event containing operation and parameters
        context: Lambda context
        
    Returns:
        Response with operation result
    """
    
    request_id = context.aws_request_id
    logger.info(f"Processing training job request", extra={
        "requestId": request_id,
        "operation": event.get("operation"),
        "environment": ENVIRONMENT
    })
    
    try:
        operation = event.get("operation")
        
        if operation == "create_training_job":
            return create_training_job(event, request_id)
        elif operation == "describe_training_job":
            return describe_training_job(event, request_id)
        elif operation == "list_training_jobs":
            return list_training_jobs(event, request_id)
        elif operation == "stop_training_job":
            return stop_training_job(event, request_id)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"Training job operation failed: {str(e)}", extra={
            "requestId": request_id,
            "operation": event.get("operation")
        }, exc_info=True)
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Training job operation failed",
                "code": "TRAINING_JOB_ERROR",
                "requestId": request_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        }


def create_training_job(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Create a new SageMaker training job
    
    Args:
        event: Event containing training job parameters
        request_id: Request correlation ID
        
    Returns:
        Training job creation response
    """
    
    training_data_s3_uri = event.get("training_data_s3_uri")
    if not training_data_s3_uri:
        raise ValueError("training_data_s3_uri is required")
    
    # Generate unique training job name
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    training_job_name = f"aquachain-wqi-training-{ENVIRONMENT}-{timestamp}"
    
    # Training job configuration
    training_job_config = {
        "TrainingJobName": training_job_name,
        "RoleArn": SAGEMAKER_ROLE_ARN,
        "AlgorithmSpecification": {
            "TrainingImage": f"246618743249.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1",
            "TrainingInputMode": "File",
        },
        "InputDataConfig": [
            {
                "ChannelName": "training",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": training_data_s3_uri,
                        "S3DataDistributionType": "FullyReplicated",
                    }
                },
                "ContentType": "text/csv",
                "CompressionType": "None",
            }
        ],
        "OutputDataConfig": {
            "S3OutputPath": f"s3://{MODEL_BUCKET}/training-output/"
        },
        "ResourceConfig": {
            "InstanceType": "ml.m5.large",
            "InstanceCount": 1,
            "VolumeSizeInGB": 30,
        },
        "StoppingCondition": {
            "MaxRuntimeInSeconds": 3600  # 1 hour max
        },
        "HyperParameters": {
            "objective": "reg:squarederror",
            "num_round": "100",
            "max_depth": "6",
            "eta": "0.3",
            "subsample": "0.8",
            "colsample_bytree": "0.8",
        },
        "Tags": [
            {"Key": "Project", "Value": "AquaChain"},
            {"Key": "Environment", "Value": ENVIRONMENT},
            {"Key": "ModelType", "Value": "WaterQualityIndex"},
            {"Key": "RequestId", "Value": request_id},
        ],
    }
    
    try:
        response = sagemaker_client.create_training_job(**training_job_config)
        
        logger.info(f"Training job created successfully", extra={
            "requestId": request_id,
            "trainingJobName": training_job_name,
            "trainingJobArn": response["TrainingJobArn"]
        })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "trainingJobName": training_job_name,
                "trainingJobArn": response["TrainingJobArn"],
                "status": "InProgress",
                "requestId": request_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"Failed to create training job: {error_code}", extra={
            "requestId": request_id,
            "trainingJobName": training_job_name
        })
        raise


def describe_training_job(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Get training job status and details
    
    Args:
        event: Event containing training job name
        request_id: Request correlation ID
        
    Returns:
        Training job details
    """
    
    training_job_name = event.get("training_job_name")
    if not training_job_name:
        raise ValueError("training_job_name is required")
    
    try:
        response = sagemaker_client.describe_training_job(
            TrainingJobName=training_job_name
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "trainingJobName": response["TrainingJobName"],
                "trainingJobStatus": response["TrainingJobStatus"],
                "creationTime": response["CreationTime"].isoformat(),
                "trainingStartTime": response.get("TrainingStartTime", "").isoformat() if response.get("TrainingStartTime") else None,
                "trainingEndTime": response.get("TrainingEndTime", "").isoformat() if response.get("TrainingEndTime") else None,
                "modelArtifacts": response.get("ModelArtifacts", {}),
                "requestId": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }, default=str)
        }
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ValidationException":
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Training job not found",
                    "code": "TRAINING_JOB_NOT_FOUND",
                    "requestId": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        raise


def list_training_jobs(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    List training jobs with optional filtering
    
    Args:
        event: Event containing optional filters
        request_id: Request correlation ID
        
    Returns:
        List of training jobs
    """
    
    # Optional filters
    status_equals = event.get("status_equals")
    max_results = min(event.get("max_results", 10), 100)  # Cap at 100
    
    list_params = {
        "MaxResults": max_results,
        "SortBy": "CreationTime",
        "SortOrder": "Descending"
    }
    
    if status_equals:
        list_params["StatusEquals"] = status_equals
    
    try:
        response = sagemaker_client.list_training_jobs(**list_params)
        
        training_jobs = []
        for job in response["TrainingJobSummaries"]:
            training_jobs.append({
                "trainingJobName": job["TrainingJobName"],
                "trainingJobStatus": job["TrainingJobStatus"],
                "creationTime": job["CreationTime"].isoformat(),
                "trainingEndTime": job.get("TrainingEndTime", "").isoformat() if job.get("TrainingEndTime") else None,
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "trainingJobs": training_jobs,
                "nextToken": response.get("NextToken"),
                "requestId": request_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except ClientError as e:
        logger.error(f"Failed to list training jobs: {e.response['Error']['Code']}", extra={
            "requestId": request_id
        })
        raise


def stop_training_job(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Stop a running training job
    
    Args:
        event: Event containing training job name
        request_id: Request correlation ID
        
    Returns:
        Stop operation result
    """
    
    training_job_name = event.get("training_job_name")
    if not training_job_name:
        raise ValueError("training_job_name is required")
    
    try:
        sagemaker_client.stop_training_job(TrainingJobName=training_job_name)
        
        logger.info(f"Training job stop requested", extra={
            "requestId": request_id,
            "trainingJobName": training_job_name
        })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Training job stop requested",
                "trainingJobName": training_job_name,
                "requestId": request_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ValidationException":
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Training job not found or cannot be stopped",
                    "code": "TRAINING_JOB_NOT_STOPPABLE",
                    "requestId": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        raise