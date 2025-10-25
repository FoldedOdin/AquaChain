"""
ML Model Performance Monitoring
Tracks model predictions, detects drift, and triggers retraining workflows
"""

import os
import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from collections import deque
import threading
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')
sagemaker = boto3.client('sagemaker')

# Environment variables
METRICS_TABLE = os.environ.get('METRICS_TABLE', 'aquachain-model-metrics')
DRIFT_THRESHOLD = float(os.environ.get('DRIFT_THRESHOLD', '0.15'))  # 15%
CONSECUTIVE_DRIFT_LIMIT = int(os.environ.get('CONSECUTIVE_DRIFT_LIMIT', '10'))
ROLLING_WINDOW_SIZE = int(os.environ.get('ROLLING_WINDOW_SIZE', '1000'))
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
SAGEMAKER_TRAINING_JOB_PREFIX = os.environ.get('SAGEMAKER_TRAINING_JOB_PREFIX', 'aquachain-wqi-training')

metrics_table = dynamodb.Table(METRICS_TABLE)


class ModelPerformanceTracker:
    """
    Track ML model performance with async logging and drift detection
    
    Features:
    - Async DynamoDB writes to avoid latency impact
    - Rolling window drift detection (1000 predictions)
    - Configurable drift threshold (default 15%)
    - Baseline metrics caching
    """
    
    def __init__(self):
        self.namespace = 'AquaChain/ML'
        self.rolling_window = deque(maxlen=ROLLING_WINDOW_SIZE)
        self.baseline_cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.consecutive_drift_counts = {}
        self.async_write_queue = []
        self.lock = threading.Lock()
    
    def log_prediction(
        self,
        model_name: str,
        prediction: float,
        actual: Optional[float] = None,
        confidence: float = 1.0,
        latency_ms: float = 0
    ) -> None:
        """
        Log a model prediction asynchronously to avoid latency impact
        
        Args:
            model_name: Model identifier
            prediction: Predicted value
            actual: Actual value (if available for validation)
            confidence: Prediction confidence score (0-1)
            latency_ms: Prediction latency in milliseconds
        """
        timestamp = int(time.time() * 1000)  # milliseconds
        
        # Add to rolling window for drift detection
        with self.lock:
            self.rolling_window.append({
                'prediction': prediction,
                'confidence': confidence,
                'timestamp': timestamp
            })
        
        # Prepare metrics for async write
        metrics = {
            'model_name': model_name,
            'timestamp': timestamp,
            'prediction': Decimal(str(prediction)),
            'confidence': Decimal(str(confidence)),
            'latency_ms': Decimal(str(latency_ms)),
            'ttl': int(time.time()) + (90 * 24 * 3600)  # 90 days TTL
        }
        
        if actual is not None:
            metrics['actual'] = Decimal(str(actual))
            metrics['error'] = Decimal(str(abs(prediction - actual)))
        
        # Async write to DynamoDB (non-blocking)
        self._async_write_metrics(metrics)
        
        # Send to CloudWatch (async)
        self._send_cloudwatch_metrics_async(model_name, confidence, latency_ms)
    
    def _async_write_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Write metrics to DynamoDB asynchronously
        Uses threading to avoid blocking the main prediction flow
        """
        def write_to_dynamodb():
            try:
                metrics_table.put_item(Item=metrics)
            except ClientError as e:
                print(f"Error writing metrics to DynamoDB: {e}")
        
        # Start async write in background thread
        thread = threading.Thread(target=write_to_dynamodb, daemon=True)
        thread.start()
    
    def _send_cloudwatch_metrics_async(
        self,
        model_name: str,
        confidence: float,
        latency_ms: float
    ) -> None:
        """Send metrics to CloudWatch asynchronously"""
        def send_metrics():
            try:
                cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'PredictionConfidence',
                            'Value': confidence,
                            'Unit': 'None',
                            'Dimensions': [
                                {'Name': 'ModelName', 'Value': model_name}
                            ]
                        },
                        {
                            'MetricName': 'PredictionLatency',
                            'Value': latency_ms,
                            'Unit': 'Milliseconds',
                            'Dimensions': [
                                {'Name': 'ModelName', 'Value': model_name}
                            ]
                        }
                    ]
                )
            except ClientError as e:
                print(f"Error sending CloudWatch metrics: {e}")
        
        # Start async send in background thread
        thread = threading.Thread(target=send_metrics, daemon=True)
        thread.start()
    
    def send_drift_score_metric(self, model_name: str, drift_score: float) -> None:
        """
        Send drift score metric to CloudWatch for alarming
        
        Args:
            model_name: Model identifier
            drift_score: Calculated drift score
        """
        def send_metric():
            try:
                cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'DriftScore',
                            'Value': drift_score,
                            'Unit': 'None',
                            'Dimensions': [
                                {'Name': 'ModelName', 'Value': model_name}
                            ]
                        }
                    ]
                )
            except ClientError as e:
                print(f"Error sending drift score metric: {e}")
        
        # Start async send in background thread
        thread = threading.Thread(target=send_metric, daemon=True)
        thread.start()
    
    def calculate_drift_score(
        self,
        model_name: str,
        recent_predictions: List[float]
    ) -> float:
        """
        Calculate drift score using rolling window (1000 predictions)
        Uses KL divergence to compare current distribution to baseline
        
        Args:
            model_name: Model identifier
            recent_predictions: List of recent prediction values
        
        Returns:
            Drift score (0.0 = no drift, higher = more drift)
        """
        if len(recent_predictions) < 100:
            # Not enough data for reliable drift detection
            return 0.0
        
        # Get baseline metrics (with caching)
        baseline = self._get_cached_baseline(model_name)
        if not baseline:
            print(f"No baseline found for {model_name}")
            return 0.0
        
        baseline_mean = baseline.get('mean', 0)
        baseline_std = baseline.get('std', 1)
        
        # Calculate current distribution metrics
        current_mean = np.mean(recent_predictions)
        current_std = np.std(recent_predictions)
        
        # Calculate drift score using statistical distance
        # Normalized difference in means
        mean_drift = abs(current_mean - baseline_mean) / max(baseline_std, 0.01)
        
        # Ratio of standard deviations
        std_ratio = current_std / max(baseline_std, 0.01)
        std_drift = abs(np.log(std_ratio))
        
        # Combined drift score
        drift_score = (mean_drift + std_drift) / 2
        
        return float(drift_score)
    
    def check_for_drift(
        self,
        model_name: str,
        drift_score: float,
        threshold: float = DRIFT_THRESHOLD
    ) -> bool:
        """
        Check if drift score exceeds threshold
        Tracks consecutive drift detections
        
        Args:
            model_name: Model identifier
            drift_score: Calculated drift score
            threshold: Drift threshold (default 15%)
        
        Returns:
            True if drift detected for consecutive limit, False otherwise
        """
        if drift_score > threshold:
            # Increment consecutive drift counter
            with self.lock:
                self.consecutive_drift_counts[model_name] = \
                    self.consecutive_drift_counts.get(model_name, 0) + 1
                
                drift_count = self.consecutive_drift_counts[model_name]
            
            print(f"Drift detected for {model_name}: score={drift_score:.3f}, "
                  f"consecutive={drift_count}/{CONSECUTIVE_DRIFT_LIMIT}")
            
            # Trigger retraining if consecutive limit reached
            if drift_count >= CONSECUTIVE_DRIFT_LIMIT:
                return True
        else:
            # Reset drift counter
            with self.lock:
                self.consecutive_drift_counts[model_name] = 0
        
        return False
    
    def _get_cached_baseline(self, model_name: str) -> Optional[Dict[str, float]]:
        """
        Get baseline metrics with caching
        
        Args:
            model_name: Model identifier
        
        Returns:
            Baseline metrics dictionary or None
        """
        current_time = time.time()
        
        # Check cache
        if model_name in self.baseline_cache:
            cache_time = self.cache_timestamps.get(model_name, 0)
            if current_time - cache_time < self.cache_ttl:
                return self.baseline_cache[model_name]
        
        # Load from DynamoDB
        try:
            response = metrics_table.query(
                KeyConditionExpression='model_name = :name',
                ExpressionAttributeValues={':name': model_name},
                ScanIndexForward=False,
                Limit=1000
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            # Calculate baseline from historical data
            predictions = [float(item['prediction']) for item in items]
            confidences = [float(item['confidence']) for item in items]
            
            baseline = {
                'mean': np.mean(predictions),
                'std': np.std(predictions),
                'confidence_mean': np.mean(confidences),
                'confidence_std': np.std(confidences),
                'sample_size': len(predictions)
            }
            
            # Update cache
            with self.lock:
                self.baseline_cache[model_name] = baseline
                self.cache_timestamps[model_name] = current_time
            
            return baseline
            
        except ClientError as e:
            print(f"Error loading baseline for {model_name}: {e}")
            return None
    
    def trigger_retraining(
        self,
        model_name: str,
        reason: str = 'drift_detection'
    ) -> Dict[str, Any]:
        """
        Trigger automated model retraining
        Creates SageMaker training job and sends notifications
        
        Args:
            model_name: Model identifier
            reason: Reason for retraining
        
        Returns:
            Training job information
        """
        timestamp = datetime.utcnow().isoformat()
        training_job_name = f"{SAGEMAKER_TRAINING_JOB_PREFIX}-{int(time.time())}"
        
        print(f"TRIGGERING RETRAINING: {model_name} - Reason: {reason}")
        
        # Send SNS alert
        if ALERT_TOPIC_ARN:
            try:
                sns.publish(
                    TopicArn=ALERT_TOPIC_ARN,
                    Subject=f'Model Retraining Triggered: {model_name}',
                    Message=json.dumps({
                        'model_name': model_name,
                        'reason': reason,
                        'timestamp': timestamp,
                        'training_job_name': training_job_name,
                        'consecutive_drift_count': self.consecutive_drift_counts.get(model_name, 0)
                    }, indent=2)
                )
                print(f"SNS alert sent for {model_name} retraining")
            except ClientError as e:
                print(f"Error sending SNS alert: {e}")
        
        # Create SageMaker training job
        try:
            # Training job configuration
            training_config = {
                'TrainingJobName': training_job_name,
                'RoleArn': os.environ.get('SAGEMAKER_ROLE_ARN', ''),
                'AlgorithmSpecification': {
                    'TrainingImage': os.environ.get('TRAINING_IMAGE', ''),
                    'TrainingInputMode': 'File'
                },
                'InputDataConfig': [
                    {
                        'ChannelName': 'training',
                        'DataSource': {
                            'S3DataSource': {
                                'S3DataType': 'S3Prefix',
                                'S3Uri': os.environ.get('TRAINING_DATA_S3_URI', ''),
                                'S3DataDistributionType': 'FullyReplicated'
                            }
                        },
                        'ContentType': 'text/csv'
                    }
                ],
                'OutputDataConfig': {
                    'S3OutputPath': os.environ.get('MODEL_OUTPUT_S3_URI', '')
                },
                'ResourceConfig': {
                    'InstanceType': 'ml.m5.xlarge',
                    'InstanceCount': 1,
                    'VolumeSizeInGB': 30
                },
                'StoppingCondition': {
                    'MaxRuntimeInSeconds': 3600
                },
                'HyperParameters': {
                    'model_name': model_name,
                    'trigger_reason': reason
                },
                'Tags': [
                    {'Key': 'ModelName', 'Value': model_name},
                    {'Key': 'TriggerReason', 'Value': reason},
                    {'Key': 'Timestamp', 'Value': timestamp}
                ]
            }
            
            # Only create training job if required env vars are set
            if training_config['RoleArn'] and training_config['AlgorithmSpecification']['TrainingImage']:
                response = sagemaker.create_training_job(**training_config)
                print(f"SageMaker training job created: {training_job_name}")
                
                # Reset consecutive drift counter
                with self.lock:
                    self.consecutive_drift_counts[model_name] = 0
                
                return {
                    'training_job_name': training_job_name,
                    'training_job_arn': response['TrainingJobArn'],
                    'status': 'InProgress',
                    'timestamp': timestamp
                }
            else:
                print("SageMaker training job not created - missing configuration")
                return {
                    'training_job_name': training_job_name,
                    'status': 'ConfigurationMissing',
                    'timestamp': timestamp
                }
                
        except ClientError as e:
            print(f"Error creating SageMaker training job: {e}")
            return {
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_rolling_window_predictions(self) -> List[float]:
        """
        Get predictions from rolling window
        
        Returns:
            List of prediction values
        """
        with self.lock:
            return [item['prediction'] for item in self.rolling_window]
    
    def get_performance_metrics(self, model_name: str) -> Dict[str, Any]:
        """
        Get current performance metrics for a model
        
        Args:
            model_name: Model identifier
        
        Returns:
            Performance metrics dictionary
        """
        predictions = self.get_rolling_window_predictions()
        
        if not predictions:
            return {'error': 'No predictions in rolling window'}
        
        # Calculate drift score
        drift_score = self.calculate_drift_score(model_name, predictions)
        
        # Get baseline
        baseline = self._get_cached_baseline(model_name)
        
        metrics = {
            'model_name': model_name,
            'rolling_window_size': len(predictions),
            'current_mean': float(np.mean(predictions)),
            'current_std': float(np.std(predictions)),
            'drift_score': drift_score,
            'drift_threshold': DRIFT_THRESHOLD,
            'consecutive_drift_count': self.consecutive_drift_counts.get(model_name, 0),
            'drift_limit': CONSECUTIVE_DRIFT_LIMIT
        }
        
        if baseline:
            metrics['baseline'] = {
                'mean': baseline['mean'],
                'std': baseline['std'],
                'sample_size': baseline['sample_size']
            }
        
        return metrics


# Global tracker instance for Lambda reuse
_tracker_instance = None

def get_tracker() -> ModelPerformanceTracker:
    """Get or create global tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ModelPerformanceTracker()
    return _tracker_instance


def lambda_handler(event, context):
    """
    Lambda handler for model performance monitoring
    
    Event types:
    - log_prediction: Log a new prediction
    - check_drift: Check for drift and trigger retraining if needed
    - get_metrics: Get current performance metrics
    - trigger_retraining: Manually trigger retraining
    """
    tracker = get_tracker()
    
    action = event.get('action', 'log_prediction')
    
    try:
        if action == 'log_prediction':
            tracker.log_prediction(
                model_name=event['model_name'],
                prediction=event['prediction'],
                actual=event.get('actual'),
                confidence=event.get('confidence', 1.0),
                latency_ms=event.get('latency_ms', 0)
            )
            
            result = {
                'status': 'logged',
                'model_name': event['model_name']
            }
            
        elif action == 'check_drift':
            model_name = event['model_name']
            predictions = tracker.get_rolling_window_predictions()
            
            if len(predictions) >= 100:
                drift_score = tracker.calculate_drift_score(model_name, predictions)
                drift_detected = tracker.check_for_drift(model_name, drift_score)
                
                if drift_detected:
                    retraining_result = tracker.trigger_retraining(
                        model_name,
                        reason='drift_detection'
                    )
                    result = {
                        'drift_detected': True,
                        'drift_score': drift_score,
                        'retraining_triggered': True,
                        'retraining_info': retraining_result
                    }
                else:
                    result = {
                        'drift_detected': False,
                        'drift_score': drift_score,
                        'consecutive_count': tracker.consecutive_drift_counts.get(model_name, 0)
                    }
            else:
                result = {
                    'status': 'insufficient_data',
                    'predictions_count': len(predictions),
                    'required': 100
                }
            
        elif action == 'get_metrics':
            result = tracker.get_performance_metrics(event['model_name'])
            
        elif action == 'trigger_retraining':
            result = tracker.trigger_retraining(
                model_name=event['model_name'],
                reason=event.get('reason', 'manual_trigger')
            )
            
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        print(f"Error in model performance monitoring: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
