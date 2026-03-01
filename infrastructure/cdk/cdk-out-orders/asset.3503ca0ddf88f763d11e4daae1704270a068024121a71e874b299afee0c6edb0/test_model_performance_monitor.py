"""
Unit tests for ML Model Performance Monitoring
Tests drift detection, async logging, and retraining triggers
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import numpy as np
from collections import deque

# Mock AWS services before importing the module
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock boto3 clients
mock_dynamodb = MagicMock()
mock_cloudwatch = MagicMock()
mock_sns = MagicMock()
mock_sagemaker = MagicMock()

with patch('boto3.resource', return_value=mock_dynamodb):
    with patch('boto3.client', side_effect=lambda service, **kwargs: {
        'cloudwatch': mock_cloudwatch,
        'sns': mock_sns,
        'sagemaker': mock_sagemaker
    }.get(service, MagicMock())):
        from model_performance_monitor import ModelPerformanceTracker, get_tracker


class TestModelPerformanceTracker(unittest.TestCase):
    """Test ModelPerformanceTracker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = ModelPerformanceTracker()
        self.model_name = 'test-wqi-model'
        
        # Reset mocks
        mock_dynamodb.reset_mock()
        mock_cloudwatch.reset_mock()
        mock_sns.reset_mock()
        mock_sagemaker.reset_mock()
    
    def test_log_prediction_basic(self):
        """Test basic prediction logging"""
        # Log a prediction
        self.tracker.log_prediction(
            model_name=self.model_name,
            prediction=75.5,
            confidence=0.95,
            latency_ms=150.0
        )
        
        # Check rolling window updated
        self.assertEqual(len(self.tracker.rolling_window), 1)
        self.assertEqual(self.tracker.rolling_window[0]['prediction'], 75.5)
        self.assertEqual(self.tracker.rolling_window[0]['confidence'], 0.95)
    
    def test_log_prediction_with_actual(self):
        """Test prediction logging with actual value"""
        self.tracker.log_prediction(
            model_name=self.model_name,
            prediction=75.5,
            actual=76.0,
            confidence=0.95,
            latency_ms=150.0
        )
        
        # Verify rolling window
        self.assertEqual(len(self.tracker.rolling_window), 1)
    
    def test_rolling_window_size_limit(self):
        """Test rolling window respects size limit"""
        # Add more than window size predictions
        for i in range(1200):
            self.tracker.log_prediction(
                model_name=self.model_name,
                prediction=float(70 + i % 20),
                confidence=0.9,
                latency_ms=100.0
            )
        
        # Check window size is limited to 1000
        self.assertEqual(len(self.tracker.rolling_window), 1000)
    
    def test_calculate_drift_score_no_baseline(self):
        """Test drift score calculation with no baseline"""
        predictions = [75.0 + np.random.randn() * 0.1 for _ in range(100)]
        
        # Mock _get_cached_baseline to return None
        with patch.object(self.tracker, '_get_cached_baseline', return_value=None):
            drift_score = self.tracker.calculate_drift_score(
                self.model_name,
                predictions
            )
            
            # Should return 0.0 when no baseline
            self.assertEqual(drift_score, 0.0)
    
    def test_calculate_drift_score_with_baseline(self):
        """Test drift score calculation with baseline"""
        # Set up baseline
        self.tracker.baseline_cache[self.model_name] = {
            'mean': 75.0,
            'std': 5.0,
            'confidence_mean': 0.9,
            'confidence_std': 0.05,
            'sample_size': 1000
        }
        self.tracker.cache_timestamps[self.model_name] = time.time()
        
        # Test with similar predictions (low drift)
        predictions = [75.0 + np.random.randn() * 5.0 for _ in range(100)]
        drift_score = self.tracker.calculate_drift_score(
            self.model_name,
            predictions
        )
        
        # Drift score should be low
        self.assertLess(drift_score, 0.5)
        
        # Test with different predictions (high drift)
        predictions_drifted = [90.0 + np.random.randn() * 10.0 for _ in range(100)]
        drift_score_high = self.tracker.calculate_drift_score(
            self.model_name,
            predictions_drifted
        )
        
        # Drift score should be higher
        self.assertGreater(drift_score_high, drift_score)
    
    def test_check_for_drift_below_threshold(self):
        """Test drift detection below threshold"""
        drift_score = 0.10  # Below 0.15 threshold
        
        drift_detected = self.tracker.check_for_drift(
            self.model_name,
            drift_score,
            threshold=0.15
        )
        
        # Should not detect drift
        self.assertFalse(drift_detected)
        self.assertEqual(self.tracker.consecutive_drift_counts.get(self.model_name, 0), 0)
    
    def test_check_for_drift_above_threshold(self):
        """Test drift detection above threshold"""
        drift_score = 0.20  # Above 0.15 threshold
        
        # First detection
        drift_detected = self.tracker.check_for_drift(
            self.model_name,
            drift_score,
            threshold=0.15
        )
        
        # Should not trigger retraining yet (need 10 consecutive)
        self.assertFalse(drift_detected)
        self.assertEqual(self.tracker.consecutive_drift_counts[self.model_name], 1)
    
    def test_check_for_drift_consecutive_limit(self):
        """Test drift detection with consecutive limit reached"""
        drift_score = 0.20
        
        # Simulate 10 consecutive drift detections
        for i in range(10):
            drift_detected = self.tracker.check_for_drift(
                self.model_name,
                drift_score,
                threshold=0.15
            )
            
            if i < 9:
                self.assertFalse(drift_detected)
            else:
                self.assertTrue(drift_detected)
        
        # Check consecutive count
        self.assertEqual(self.tracker.consecutive_drift_counts[self.model_name], 10)
    
    def test_check_for_drift_reset_on_good_score(self):
        """Test drift counter resets when score drops below threshold"""
        # Build up some drift count
        for _ in range(5):
            self.tracker.check_for_drift(self.model_name, 0.20, threshold=0.15)
        
        self.assertEqual(self.tracker.consecutive_drift_counts[self.model_name], 5)
        
        # Now send a good score
        self.tracker.check_for_drift(self.model_name, 0.10, threshold=0.15)
        
        # Counter should reset
        self.assertEqual(self.tracker.consecutive_drift_counts[self.model_name], 0)
    
    @patch.dict(os.environ, {
        'ALERT_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-topic',
        'SAGEMAKER_ROLE_ARN': 'arn:aws:iam::123456789012:role/test-role',
        'TRAINING_IMAGE': '123456789012.dkr.ecr.us-east-1.amazonaws.com/test:latest',
        'TRAINING_DATA_S3_URI': 's3://test-bucket/training-data/',
        'MODEL_OUTPUT_S3_URI': 's3://test-bucket/models/'
    })
    def test_trigger_retraining(self):
        """Test automated retraining trigger"""
        # Set up consecutive drift count
        self.tracker.consecutive_drift_counts[self.model_name] = 10
        
        # Mock SageMaker response
        mock_sagemaker.create_training_job.return_value = {
            'TrainingJobArn': 'arn:aws:sagemaker:us-east-1:123456789012:training-job/test-job'
        }
        
        # Trigger retraining
        result = self.tracker.trigger_retraining(
            self.model_name,
            reason='drift_detection'
        )
        
        # Verify SNS alert was attempted (may be called in thread)
        # Just verify the result contains expected fields
        self.assertIn('training_job_name', result)
        self.assertIn('training_job_arn', result)
        self.assertEqual(result['status'], 'InProgress')
        
        # Verify drift counter was reset
        self.assertEqual(self.tracker.consecutive_drift_counts[self.model_name], 0)
    
    def test_trigger_retraining_missing_config(self):
        """Test retraining trigger with missing configuration"""
        result = self.tracker.trigger_retraining(
            self.model_name,
            reason='test'
        )
        
        # Should return configuration missing status
        self.assertEqual(result['status'], 'ConfigurationMissing')
    
    def test_get_rolling_window_predictions(self):
        """Test getting predictions from rolling window"""
        # Add some predictions
        test_predictions = [70.0, 75.0, 80.0, 85.0, 90.0]
        for pred in test_predictions:
            self.tracker.log_prediction(
                model_name=self.model_name,
                prediction=pred,
                confidence=0.9,
                latency_ms=100.0
            )
        
        # Get predictions
        predictions = self.tracker.get_rolling_window_predictions()
        
        # Verify
        self.assertEqual(len(predictions), 5)
        self.assertEqual(predictions, test_predictions)
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics"""
        # Set up baseline
        self.tracker.baseline_cache[self.model_name] = {
            'mean': 75.0,
            'std': 5.0,
            'confidence_mean': 0.9,
            'confidence_std': 0.05,
            'sample_size': 1000
        }
        self.tracker.cache_timestamps[self.model_name] = time.time()
        
        # Add predictions
        for i in range(100):
            self.tracker.log_prediction(
                model_name=self.model_name,
                prediction=75.0 + np.random.randn() * 5.0,
                confidence=0.9,
                latency_ms=100.0
            )
        
        # Get metrics
        metrics = self.tracker.get_performance_metrics(self.model_name)
        
        # Verify
        self.assertEqual(metrics['model_name'], self.model_name)
        self.assertEqual(metrics['rolling_window_size'], 100)
        self.assertIn('current_mean', metrics)
        self.assertIn('current_std', metrics)
        self.assertIn('drift_score', metrics)
        self.assertIn('baseline', metrics)
    
    def test_async_write_metrics(self):
        """Test async metrics writing doesn't block"""
        start_time = time.time()
        
        # Log prediction (should be async)
        self.tracker.log_prediction(
            model_name=self.model_name,
            prediction=75.0,
            confidence=0.9,
            latency_ms=100.0
        )
        
        elapsed = time.time() - start_time
        
        # Should complete very quickly (< 10ms) since it's async
        self.assertLess(elapsed, 0.01)
    
    def test_thread_safety(self):
        """Test thread safety of rolling window operations"""
        import threading
        
        def add_predictions():
            for i in range(100):
                self.tracker.log_prediction(
                    model_name=self.model_name,
                    prediction=float(70 + i % 20),
                    confidence=0.9,
                    latency_ms=100.0
                )
        
        # Create multiple threads
        threads = [threading.Thread(target=add_predictions) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify rolling window is consistent
        predictions = self.tracker.get_rolling_window_predictions()
        self.assertLessEqual(len(predictions), 1000)


class TestLambdaHandler(unittest.TestCase):
    """Test Lambda handler function"""
    
    @patch('model_performance_monitor.get_tracker')
    def test_lambda_handler_log_prediction(self, mock_get_tracker):
        """Test Lambda handler for log_prediction action"""
        from model_performance_monitor import lambda_handler
        
        # Mock tracker
        mock_tracker = Mock()
        mock_get_tracker.return_value = mock_tracker
        
        # Test event
        event = {
            'action': 'log_prediction',
            'model_name': 'test-model',
            'prediction': 75.5,
            'confidence': 0.95,
            'latency_ms': 150.0
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify
        self.assertEqual(response['statusCode'], 200)
        mock_tracker.log_prediction.assert_called_once()
    
    @patch('model_performance_monitor.get_tracker')
    def test_lambda_handler_check_drift(self, mock_get_tracker):
        """Test Lambda handler for check_drift action"""
        from model_performance_monitor import lambda_handler
        
        # Mock tracker
        mock_tracker = Mock()
        mock_tracker.get_rolling_window_predictions.return_value = [75.0] * 100
        mock_tracker.calculate_drift_score.return_value = 0.20
        mock_tracker.check_for_drift.return_value = False
        mock_tracker.consecutive_drift_counts = {'test-model': 5}
        mock_get_tracker.return_value = mock_tracker
        
        # Test event
        event = {
            'action': 'check_drift',
            'model_name': 'test-model'
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertFalse(body['drift_detected'])
        self.assertEqual(body['drift_score'], 0.20)
    
    @patch('model_performance_monitor.get_tracker')
    def test_lambda_handler_get_metrics(self, mock_get_tracker):
        """Test Lambda handler for get_metrics action"""
        from model_performance_monitor import lambda_handler
        
        # Mock tracker
        mock_tracker = Mock()
        mock_tracker.get_performance_metrics.return_value = {
            'model_name': 'test-model',
            'drift_score': 0.10
        }
        mock_get_tracker.return_value = mock_tracker
        
        # Test event
        event = {
            'action': 'get_metrics',
            'model_name': 'test-model'
        }
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['model_name'], 'test-model')


if __name__ == '__main__':
    unittest.main()
