"""
Model Performance Monitoring and Data Drift Detection
Monitors model performance in production and detects data drift
"""

import boto3
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from scipy import stats
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ModelMonitor:
    """
    Monitor ML model performance and detect data drift
    """
    
    def __init__(self, model_name: str, s3_bucket: str, region: str = 'us-east-1'):
        """
        Initialize model monitor
        
        Args:
            model_name: Name of the model to monitor
            s3_bucket: S3 bucket for storing monitoring data
            region: AWS region
        """
        self.model_name = model_name
        self.s3_bucket = s3_bucket
        self.region = region
        
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Monitoring configuration
        self.drift_threshold = 0.1  # 10% drift threshold
        self.performance_degradation_threshold = 0.15  # 15% degradation
        self.monitoring_window_hours = 24
        
        # DynamoDB table for storing predictions and actuals
        self.predictions_table_name = 'aquachain-ml-predictions'
    
    def log_prediction(self, device_id: str, timestamp: str, features: Dict,
                      prediction: Dict, model_version: str):
        """
        Log prediction for monitoring
        
        Args:
            device_id: Device identifier
            timestamp: Prediction timestamp
            features: Input features
            prediction: Model prediction
            model_version: Model version used
        """
        table = self.dynamodb.Table(self.predictions_table_name)
        
        item = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'features': json.dumps(features),
            'wqi_predicted': prediction['wqi'],
            'anomaly_predicted': prediction['anomalyType'],
            'confidence': prediction['confidence'],
            'model_version': model_version,
            'logged_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
    
    def log_actual_outcome(self, device_id: str, timestamp: str,
                          actual_wqi: float, actual_anomaly: str):
        """
        Log actual outcome for prediction validation
        
        Args:
            device_id: Device identifier
            timestamp: Original prediction timestamp
            actual_wqi: Actual WQI value
            actual_anomaly: Actual anomaly type
        """
        table = self.dynamodb.Table(self.predictions_table_name)
        
        # Update the prediction record with actual values
        table.update_item(
            Key={'deviceId': device_id, 'timestamp': timestamp},
            UpdateExpression='SET actual_wqi = :wqi, actual_anomaly = :anom, validated_at = :val',
            ExpressionAttributeValues={
                ':wqi': actual_wqi,
                ':anom': actual_anomaly,
                ':val': datetime.utcnow().isoformat()
            }
        )
    
    def calculate_model_performance(self, hours: int = 24) -> Dict:
        """
        Calculate model performance metrics over time window
        
        Args:
            hours: Time window in hours
            
        Returns:
            Performance metrics dictionary
        """
        # Query predictions with actual outcomes
        table = self.dynamodb.Table(self.predictions_table_name)
        
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        response = table.scan(
            FilterExpression='validated_at > :cutoff AND attribute_exists(actual_wqi)',
            ExpressionAttributeValues={':cutoff': cutoff_time}
        )
        
        items = response['Items']
        
        if not items:
            return {'error': 'No validated predictions in time window'}
        
        # Calculate WQI prediction metrics
        wqi_predicted = np.array([float(item['wqi_predicted']) for item in items])
        wqi_actual = np.array([float(item['actual_wqi']) for item in items])
        
        wqi_mae = np.mean(np.abs(wqi_predicted - wqi_actual))
        wqi_rmse = np.sqrt(np.mean((wqi_predicted - wqi_actual) ** 2))
        wqi_mape = np.mean(np.abs((wqi_actual - wqi_predicted) / wqi_actual)) * 100
        
        # Calculate anomaly detection metrics
        anomaly_predicted = [item['anomaly_predicted'] for item in items]
        anomaly_actual = [item['actual_anomaly'] for item in items]
        
        anomaly_accuracy = sum(p == a for p, a in zip(anomaly_predicted, anomaly_actual)) / len(items)
        
        # Calculate per-class metrics
        classes = ['normal', 'sensor_fault', 'contamination']
        per_class_metrics = {}
        
        for cls in classes:
            true_positives = sum((p == cls and a == cls) 
                               for p, a in zip(anomaly_predicted, anomaly_actual))
            false_positives = sum((p == cls and a != cls) 
                                for p, a in zip(anomaly_predicted, anomaly_actual))
            false_negatives = sum((p != cls and a == cls) 
                                for p, a in zip(anomaly_predicted, anomaly_actual))
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            per_class_metrics[cls] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'time_window_hours': hours,
            'sample_count': len(items),
            'wqi_metrics': {
                'mae': float(wqi_mae),
                'rmse': float(wqi_rmse),
                'mape': float(wqi_mape)
            },
            'anomaly_metrics': {
                'accuracy': float(anomaly_accuracy),
                'per_class': per_class_metrics
            }
        }
        
        # Publish metrics to CloudWatch
        self._publish_metrics_to_cloudwatch(metrics)
        
        return metrics
    
    def detect_data_drift(self, baseline_features: Dict[str, np.ndarray],
                         current_features: Dict[str, np.ndarray]) -> Dict:
        """
        Detect data drift using statistical tests
        
        Args:
            baseline_features: Baseline feature distributions (training data)
            current_features: Current feature distributions (production data)
            
        Returns:
            Drift detection results
        """
        drift_results = {}
        
        for feature_name in baseline_features.keys():
            if feature_name not in current_features:
                continue
            
            baseline = baseline_features[feature_name]
            current = current_features[feature_name]
            
            # Kolmogorov-Smirnov test for distribution drift
            ks_statistic, ks_pvalue = stats.ks_2samp(baseline, current)
            
            # Population Stability Index (PSI)
            psi = self._calculate_psi(baseline, current)
            
            # Determine if drift is significant
            drift_detected = (ks_pvalue < 0.05) or (psi > self.drift_threshold)
            
            drift_results[feature_name] = {
                'ks_statistic': float(ks_statistic),
                'ks_pvalue': float(ks_pvalue),
                'psi': float(psi),
                'drift_detected': drift_detected,
                'baseline_mean': float(np.mean(baseline)),
                'current_mean': float(np.mean(current)),
                'baseline_std': float(np.std(baseline)),
                'current_std': float(np.std(current))
            }
        
        # Overall drift assessment
        features_with_drift = sum(1 for r in drift_results.values() if r['drift_detected'])
        drift_percentage = features_with_drift / len(drift_results) if drift_results else 0
        
        overall_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'features_analyzed': len(drift_results),
            'features_with_drift': features_with_drift,
            'drift_percentage': drift_percentage,
            'significant_drift': drift_percentage > 0.3,  # >30% features drifted
            'feature_drift': drift_results
        }
        
        # Save drift report
        self._save_drift_report(overall_result)
        
        # Trigger retraining if significant drift detected
        if overall_result['significant_drift']:
            self._trigger_retraining_pipeline()
        
        return overall_result
    
    def _calculate_psi(self, baseline: np.ndarray, current: np.ndarray,
                      bins: int = 10) -> float:
        """
        Calculate Population Stability Index (PSI)
        
        Args:
            baseline: Baseline distribution
            current: Current distribution
            bins: Number of bins for histogram
            
        Returns:
            PSI value
        """
        # Create bins based on baseline distribution
        bin_edges = np.percentile(baseline, np.linspace(0, 100, bins + 1))
        
        # Calculate histograms
        baseline_hist, _ = np.histogram(baseline, bins=bin_edges)
        current_hist, _ = np.histogram(current, bins=bin_edges)
        
        # Convert to proportions
        baseline_prop = baseline_hist / len(baseline)
        current_prop = current_hist / len(current)
        
        # Avoid division by zero
        baseline_prop = np.where(baseline_prop == 0, 0.0001, baseline_prop)
        current_prop = np.where(current_prop == 0, 0.0001, current_prop)
        
        # Calculate PSI
        psi = np.sum((current_prop - baseline_prop) * np.log(current_prop / baseline_prop))
        
        return psi
    
    def _publish_metrics_to_cloudwatch(self, metrics: Dict):
        """Publish performance metrics to CloudWatch"""
        
        metric_data = [
            {
                'MetricName': 'WQI_MAE',
                'Value': metrics['wqi_metrics']['mae'],
                'Unit': 'None',
                'Timestamp': datetime.utcnow()
            },
            {
                'MetricName': 'WQI_RMSE',
                'Value': metrics['wqi_metrics']['rmse'],
                'Unit': 'None',
                'Timestamp': datetime.utcnow()
            },
            {
                'MetricName': 'Anomaly_Accuracy',
                'Value': metrics['anomaly_metrics']['accuracy'],
                'Unit': 'Percent',
                'Timestamp': datetime.utcnow()
            }
        ]
        
        self.cloudwatch.put_metric_data(
            Namespace='AquaChain/MLModel',
            MetricData=metric_data
        )
    
    def _save_drift_report(self, drift_report: Dict):
        """Save drift detection report to S3"""
        
        report_key = f'ml-monitoring/drift-reports/{datetime.utcnow().strftime("%Y/%m/%d")}/drift-report-{datetime.utcnow().isoformat()}.json'
        
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=report_key,
            Body=json.dumps(drift_report, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Drift report saved to s3://{self.s3_bucket}/{report_key}")
    
    def _trigger_retraining_pipeline(self):
        """Trigger automated model retraining pipeline"""
        
        logger.warning("Significant data drift detected. Triggering retraining pipeline.")
        
        # Trigger SageMaker pipeline execution
        sm_client = boto3.client('sagemaker', region_name=self.region)
        
        try:
            response = sm_client.start_pipeline_execution(
                PipelineName='aquachain-ml-training-pipeline',
                PipelineExecutionDisplayName=f'drift-triggered-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}',
                PipelineParameters=[
                    {
                        'Name': 'ModelApprovalStatus',
                        'Value': 'PendingManualApproval'
                    }
                ]
            )
            
            logger.info(f"Retraining pipeline started: {response['PipelineExecutionArn']}")
            
            # Send notification
            self._send_drift_notification(response['PipelineExecutionArn'])
            
        except Exception as e:
            logger.error(f"Failed to trigger retraining pipeline: {e}")
    
    def _send_drift_notification(self, pipeline_arn: str):
        """Send notification about drift detection and retraining"""
        
        sns_client = boto3.client('sns', region_name=self.region)
        
        message = f"""
        Data Drift Detected - AquaChain ML Model
        
        Significant data drift has been detected in the production ML model.
        Automated retraining pipeline has been triggered.
        
        Pipeline Execution: {pipeline_arn}
        Timestamp: {datetime.utcnow().isoformat()}
        
        Action Required: Review drift report and approve new model after training completes.
        """
        
        try:
            sns_client.publish(
                TopicArn=f'arn:aws:sns:{self.region}:ACCOUNT_ID:aquachain-ml-alerts',
                Subject='Data Drift Detected - Model Retraining Triggered',
                Message=message
            )
        except Exception as e:
            logger.error(f"Failed to send drift notification: {e}")
    
    def check_performance_degradation(self, baseline_metrics: Dict,
                                     current_metrics: Dict) -> bool:
        """
        Check if model performance has degraded significantly
        
        Args:
            baseline_metrics: Baseline performance metrics
            current_metrics: Current performance metrics
            
        Returns:
            True if significant degradation detected
        """
        # Check WQI RMSE degradation
        baseline_rmse = baseline_metrics['wqi_metrics']['rmse']
        current_rmse = current_metrics['wqi_metrics']['rmse']
        rmse_degradation = (current_rmse - baseline_rmse) / baseline_rmse
        
        # Check anomaly accuracy degradation
        baseline_accuracy = baseline_metrics['anomaly_metrics']['accuracy']
        current_accuracy = current_metrics['anomaly_metrics']['accuracy']
        accuracy_degradation = (baseline_accuracy - current_accuracy) / baseline_accuracy
        
        degraded = (rmse_degradation > self.performance_degradation_threshold or
                   accuracy_degradation > self.performance_degradation_threshold)
        
        if degraded:
            logger.warning(f"Performance degradation detected: RMSE +{rmse_degradation*100:.1f}%, Accuracy -{accuracy_degradation*100:.1f}%")
        
        return degraded


def lambda_handler(event, context):
    """
    Lambda handler for scheduled model monitoring
    """
    monitor = ModelMonitor(
        model_name='aquachain-wqi-model',
        s3_bucket='aquachain-data-lake'
    )
    
    # Calculate current performance
    performance = monitor.calculate_model_performance(hours=24)
    
    logger.info(f"Model performance: {json.dumps(performance)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(performance)
    }


if __name__ == "__main__":
    # Example usage
    monitor = ModelMonitor(
        model_name='aquachain-wqi-model',
        s3_bucket='aquachain-data-lake'
    )
    
    # Calculate performance
    performance = monitor.calculate_model_performance(hours=24)
    print(json.dumps(performance, indent=2))
