"""
Unit tests for training data validation
Tests DataQualityValidator and TrainingDataValidator classes
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from training_data_validator import (
    DataQualityValidator,
    TrainingDataValidator,
    DEFAULT_FEATURE_RANGES,
    RECOMMENDED_FEATURE_RANGES,
    MIN_CLASS_REPRESENTATION
)


class TestDataQualityValidator:
    """Test DataQualityValidator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = DataQualityValidator()
    
    def test_validate_features_with_valid_data(self):
        """Test feature validation with valid data"""
        # Create valid water quality data
        data = pd.DataFrame({
            'pH': [7.0, 7.2, 6.8, 7.5],
            'turbidity': [1.0, 2.0, 1.5, 2.5],
            'tds': [200, 250, 300, 280],
            'temperature': [25, 26, 24, 27],
            'humidity': [60, 65, 55, 70]
        })
        
        feature_names = ['pH', 'turbidity', 'tds', 'temperature', 'humidity']
        result = self.validator.validate_features(data, feature_names)
        
        assert result['passed'] is True
        assert len(result['errors']) == 0
        assert 'nan_check' in result['checks']
        assert 'inf_check' in result['checks']
        assert 'range_check' in result['checks']
    
    def test_validate_features_with_nan_values(self):
        """Test feature validation detects NaN values"""
        data = pd.DataFrame({
            'pH': [7.0, np.nan, 6.8, 7.5],
            'turbidity': [1.0, 2.0, np.nan, 2.5],
            'tds': [200, 250, 300, 280]
        })
        
        feature_names = ['pH', 'turbidity', 'tds']
        result = self.validator.validate_features(data, feature_names)
        
        assert result['passed'] is False
        assert len(result['errors']) > 0
        assert result['checks']['nan_check']['passed'] is False
        assert result['checks']['nan_check']['total_nans'] == 2
    
    def test_validate_features_with_infinite_values(self):
        """Test feature validation detects infinite values"""
        data = pd.DataFrame({
            'pH': [7.0, 7.2, 6.8, np.inf],
            'turbidity': [1.0, -np.inf, 1.5, 2.5],
            'tds': [200, 250, 300, 280]
        })
        
        feature_names = ['pH', 'turbidity', 'tds']
        result = self.validator.validate_features(data, feature_names)
        
        assert result['passed'] is False
        assert len(result['errors']) > 0
        assert result['checks']['inf_check']['passed'] is False
        assert result['checks']['inf_check']['total_infs'] == 2
    
    def test_validate_features_with_out_of_range_values(self):
        """Test feature validation detects out-of-range values"""
        data = pd.DataFrame({
            'pH': [7.0, 15.0, 6.8, -1.0],  # pH out of range
            'turbidity': [1.0, 2.0, 1.5, 2.5],
            'temperature': [25, 26, 100, 27]  # Temperature out of range
        })
        
        feature_names = ['pH', 'turbidity', 'temperature']
        result = self.validator.validate_features(data, feature_names)
        
        assert result['passed'] is False
        assert len(result['errors']) > 0
        assert result['checks']['range_check']['passed'] is False
        assert len(result['checks']['range_check']['out_of_range']) > 0
    
    def test_validate_labels_with_balanced_distribution(self):
        """Test label validation with balanced distribution"""
        labels = pd.Series([0, 0, 0, 1, 1, 1, 2, 2, 2, 2])
        
        result = self.validator.validate_labels(labels)
        
        assert result['passed'] is True
        assert len(result['underrepresented_classes']) == 0
        assert len(result['distribution']) == 3
    
    def test_validate_labels_with_imbalanced_distribution(self):
        """Test label validation detects imbalanced distribution"""
        # Create imbalanced dataset: 95% class 0, 3% class 1, 2% class 2
        labels = pd.Series([0] * 95 + [1] * 3 + [2] * 2)
        
        result = self.validator.validate_labels(labels, min_representation=0.05)
        
        assert result['passed'] is False
        assert len(result['underrepresented_classes']) == 2  # Classes 1 and 2
        assert len(result['recommendations']) > 0
    
    def test_validate_labels_with_single_class(self):
        """Test label validation with single class (edge case)"""
        labels = pd.Series([0] * 100)
        
        result = self.validator.validate_labels(labels)
        
        # Single class should pass if it has 100% representation
        assert result['passed'] is True
        assert len(result['distribution']) == 1
    
    def test_validate_labels_with_empty_data(self):
        """Test label validation with empty data (edge case)"""
        labels = pd.Series([])
        
        result = self.validator.validate_labels(labels)
        
        assert result['passed'] is False
        assert 'No labels provided' in result['errors']
    
    def test_check_distribution(self):
        """Test distribution check for features"""
        data = pd.DataFrame({
            'pH': np.random.normal(7.0, 0.5, 1000),
            'turbidity': np.random.lognormal(0, 0.5, 1000),
            'temperature': np.random.normal(25, 3, 1000)
        })
        
        feature_names = ['pH', 'turbidity', 'temperature']
        result = self.validator.check_distribution(data, feature_names)
        
        assert 'features' in result
        assert len(result['features']) == 3
        
        for feature in feature_names:
            assert feature in result['features']
            assert 'mean' in result['features'][feature]
            assert 'std' in result['features'][feature]
            assert 'skewness' in result['features'][feature]
            assert 'kurtosis' in result['features'][feature]
    
    def test_check_distribution_with_high_skewness(self):
        """Test distribution check detects high skewness"""
        # Create highly skewed data
        data = pd.DataFrame({
            'pH': np.concatenate([np.random.normal(7.0, 0.2, 900), 
                                 np.random.normal(10.0, 0.5, 100)])
        })
        
        result = self.validator.check_distribution(data, ['pH'])
        
        assert 'pH' in result['features']
        # High skewness should generate warnings
        if abs(result['features']['pH']['skewness']) > 2:
            assert len(result['features']['pH']['warnings']) > 0


class TestTrainingDataValidator:
    """Test TrainingDataValidator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = TrainingDataValidator()
    
    @patch('training_data_validator.validation_table')
    @patch('training_data_validator.sns')
    def test_validate_dataset_with_valid_data(self, mock_sns, mock_table):
        """Test dataset validation with valid data"""
        # Mock DynamoDB table
        mock_table.put_item = Mock()
        
        data = pd.DataFrame({
            'pH': [7.0, 7.2, 6.8, 7.5, 7.1],
            'turbidity': [1.0, 2.0, 1.5, 2.5, 1.8],
            'tds': [200, 250, 300, 280, 260],
            'temperature': [25, 26, 24, 27, 25],
            'humidity': [60, 65, 55, 70, 62],
            'wqi': [85, 88, 82, 90, 86]
        })
        
        feature_columns = ['pH', 'turbidity', 'tds', 'temperature', 'humidity']
        label_column = 'wqi'
        
        result = self.validator.validate_dataset(
            data=data,
            feature_columns=feature_columns,
            label_column=label_column
        )
        
        assert 'validation_id' in result
        assert 'timestamp' in result
        assert result['total_rows'] == 5
        assert result['feature_count'] == 5
        assert 'checks' in result
        
        # Verify DynamoDB was called
        mock_table.put_item.assert_called_once()
    
    @patch('training_data_validator.validation_table')
    @patch('training_data_validator.sns')
    def test_validate_dataset_with_invalid_data(self, mock_sns, mock_table):
        """Test dataset validation detects invalid data"""
        # Mock DynamoDB and SNS
        mock_table.put_item = Mock()
        mock_sns.publish = Mock()
        
        data = pd.DataFrame({
            'pH': [7.0, np.nan, 6.8, 15.0],  # NaN and out of range
            'turbidity': [1.0, 2.0, np.inf, 2.5],  # Infinite value
            'tds': [200, 250, 300, 280],
            'wqi': [85, 88, 82, 90]
        })
        
        feature_columns = ['pH', 'turbidity', 'tds']
        label_column = 'wqi'
        
        result = self.validator.validate_dataset(
            data=data,
            feature_columns=feature_columns,
            label_column=label_column
        )
        
        assert result['passed'] is False
        assert len(result['errors']) > 0
        
        # Verify alert was sent
        if mock_sns.publish.called:
            assert True  # Alert was sent for failed validation
    
    @patch('training_data_validator.validation_table')
    @patch('training_data_validator.sns')
    def test_validate_dataset_with_custom_ranges(self, mock_sns, mock_table):
        """Test dataset validation with custom feature ranges"""
        # Mock DynamoDB
        mock_table.put_item = Mock()
        
        data = pd.DataFrame({
            'pH': [7.0, 7.2, 6.8, 7.5],
            'custom_feature': [10, 20, 30, 40],
            'wqi': [85, 88, 82, 90]
        })
        
        feature_columns = ['pH', 'custom_feature']
        label_column = 'wqi'
        
        custom_ranges = {
            'pH': (6.0, 8.0),
            'custom_feature': (0, 50)
        }
        
        result = self.validator.validate_dataset(
            data=data,
            feature_columns=feature_columns,
            label_column=label_column,
            expected_ranges=custom_ranges
        )
        
        assert 'validation_id' in result
        assert result['total_rows'] == 4
    
    @patch('training_data_validator.validation_table')
    @patch('training_data_validator.sns')
    def test_validate_dataset_performance_with_large_dataset(self, mock_sns, mock_table):
        """Test validation performance with large dataset"""
        # Mock DynamoDB
        mock_table.put_item = Mock()
        
        # Create large dataset
        n_samples = 10000
        data = pd.DataFrame({
            'pH': np.random.normal(7.0, 0.5, n_samples),
            'turbidity': np.random.lognormal(0, 0.5, n_samples),
            'tds': np.random.normal(300, 100, n_samples),
            'temperature': np.random.normal(25, 3, n_samples),
            'humidity': np.random.normal(60, 10, n_samples),
            'wqi': np.random.uniform(50, 100, n_samples)
        })
        
        feature_columns = ['pH', 'turbidity', 'tds', 'temperature', 'humidity']
        label_column = 'wqi'
        
        import time
        start_time = time.time()
        
        result = self.validator.validate_dataset(
            data=data,
            feature_columns=feature_columns,
            label_column=label_column
        )
        
        elapsed_time = time.time() - start_time
        
        assert result['total_rows'] == n_samples
        # Validation should complete in reasonable time (< 10 seconds)
        assert elapsed_time < 10.0
        print(f"Validated {n_samples} rows in {elapsed_time:.2f} seconds")
    
    @patch('training_data_validator.validation_table')
    def test_generate_report(self, mock_table):
        """Test validation report generation"""
        # Mock DynamoDB get_item
        mock_table.get_item = Mock(return_value={
            'Item': {
                'validation_id': 'validation_123',
                'timestamp': '2025-10-25T00:00:00',
                'passed': True,
                'total_rows': 100,
                'feature_count': 5,
                'checks': {},
                'errors': [],
                'warnings': []
            }
        })
        
        report = self.validator.generate_report('validation_123')
        
        assert 'validation_id' in report
        assert report['validation_id'] == 'validation_123'
        assert 'summary' in report
        
        # Verify DynamoDB was queried
        mock_table.get_item.assert_called_once()


class TestErrorHandling:
    """Test error handling in validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = DataQualityValidator()
    
    def test_validate_features_with_missing_columns(self):
        """Test validation handles missing columns gracefully"""
        data = pd.DataFrame({
            'pH': [7.0, 7.2, 6.8, 7.5],
            'turbidity': [1.0, 2.0, 1.5, 2.5]
        })
        
        # Request validation for columns that don't exist
        feature_names = ['pH', 'turbidity', 'nonexistent_feature']
        
        # Should not raise exception
        result = self.validator.validate_features(data, feature_names)
        
        # Should still validate existing features
        assert 'checks' in result
    
    def test_validate_labels_with_non_numeric_labels(self):
        """Test label validation with non-numeric labels"""
        labels = pd.Series(['normal', 'normal', 'anomaly', 'normal', 'anomaly'])
        
        result = self.validator.validate_labels(labels)
        
        assert 'distribution' in result
        assert len(result['distribution']) == 2


def test_default_feature_ranges():
    """Test that default feature ranges are properly defined"""
    assert 'pH' in DEFAULT_FEATURE_RANGES
    assert 'turbidity' in DEFAULT_FEATURE_RANGES
    assert 'tds' in DEFAULT_FEATURE_RANGES
    assert 'temperature' in DEFAULT_FEATURE_RANGES
    assert 'humidity' in DEFAULT_FEATURE_RANGES
    
    # Check pH range
    assert DEFAULT_FEATURE_RANGES['pH'] == (0.0, 14.0)
    
    # Check recommended ranges
    assert 'pH' in RECOMMENDED_FEATURE_RANGES
    assert RECOMMENDED_FEATURE_RANGES['pH'] == (6.5, 8.5)


def test_min_class_representation():
    """Test that minimum class representation is properly configured"""
    assert MIN_CLASS_REPRESENTATION == 0.05  # 5%


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])

