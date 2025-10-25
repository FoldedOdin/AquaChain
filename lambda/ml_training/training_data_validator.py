"""
Training Data Validation
Validates data quality before model training
"""

import os
import json
import boto3
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Environment variables
VALIDATION_RESULTS_TABLE = os.environ.get('VALIDATION_RESULTS_TABLE', 'aquachain-data-validation')
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
MIN_CLASS_REPRESENTATION = float(os.environ.get('MIN_CLASS_REPRESENTATION', '0.05'))  # 5%

validation_table = dynamodb.Table(VALIDATION_RESULTS_TABLE)

# Default expected ranges for water quality features
DEFAULT_FEATURE_RANGES = {
    'pH': (0.0, 14.0),  # Physical pH range
    'turbidity': (0.0, 100.0),  # NTU - normal range, higher indicates contamination
    'tds': (0.0, 2000.0),  # mg/L - Total Dissolved Solids
    'temperature': (0.0, 50.0),  # Celsius - typical water temperature range
    'humidity': (0.0, 100.0),  # Percentage
    'latitude': (-90.0, 90.0),  # Geographic coordinate
    'longitude': (-180.0, 180.0),  # Geographic coordinate
}

# Recommended ranges for safe water quality
RECOMMENDED_FEATURE_RANGES = {
    'pH': (6.5, 8.5),  # WHO recommended range
    'turbidity': (0.0, 5.0),  # NTU - acceptable range
    'tds': (50.0, 500.0),  # mg/L - acceptable range
    'temperature': (15.0, 30.0),  # Celsius - comfortable range
    'humidity': (30.0, 70.0),  # Percentage - typical range
}


class DataQualityValidator:
    """
    Data Quality Validator for water quality training data
    Implements comprehensive validation checks for features and labels
    """
    
    def __init__(self, expected_ranges: Dict[str, Tuple[float, float]] = None):
        """
        Initialize validator with configurable validation rules
        
        Args:
            expected_ranges: Dictionary of feature names to (min, max) tuples
        """
        self.expected_ranges = expected_ranges or DEFAULT_FEATURE_RANGES
        self.recommended_ranges = RECOMMENDED_FEATURE_RANGES
    
    def validate_features(
        self,
        features: pd.DataFrame,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Validate features for NaN, Inf, and range checks
        
        Args:
            features: DataFrame containing feature data
            feature_names: List of feature column names to validate
        
        Returns:
            Validation result dictionary with pass/fail status and details
        """
        result = {
            'passed': True,
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # Check for NaN values
        nan_check = self._check_nan_values(features, feature_names)
        result['checks']['nan_check'] = nan_check
        if not nan_check['passed']:
            result['passed'] = False
            result['errors'].append(nan_check['message'])
        
        # Check for infinite values
        inf_check = self._check_infinite_values(features, feature_names)
        result['checks']['inf_check'] = inf_check
        if not inf_check['passed']:
            result['passed'] = False
            result['errors'].append(inf_check['message'])
        
        # Check feature ranges
        range_check = self._check_feature_ranges(features, feature_names)
        result['checks']['range_check'] = range_check
        if not range_check['passed']:
            result['passed'] = False
            result['errors'].append(range_check['message'])
        if range_check.get('warnings'):
            result['warnings'].extend(range_check['warnings'])
        
        return result
    
    def validate_labels(
        self,
        labels: pd.Series,
        min_representation: float = MIN_CLASS_REPRESENTATION
    ) -> Dict[str, Any]:
        """
        Validate labels for distribution and representation
        
        Args:
            labels: Series containing label data
            min_representation: Minimum percentage representation per class (0-1)
        
        Returns:
            Validation result dictionary with distribution analysis
        """
        result = {
            'passed': True,
            'distribution': {},
            'underrepresented_classes': {},
            'recommendations': [],
            'errors': [],
            'warnings': []
        }
        
        # Calculate label distribution
        label_counts = labels.value_counts()
        total = len(labels)
        
        if total == 0:
            result['passed'] = False
            result['errors'].append('No labels provided')
            return result
        
        label_distribution = (label_counts / total).to_dict()
        result['distribution'] = label_distribution
        
        # Check for underrepresented classes
        underrepresented = {}
        for label, pct in label_distribution.items():
            if pct < min_representation:
                underrepresented[str(label)] = float(pct)
                result['warnings'].append(
                    f'Class {label} is underrepresented: {pct*100:.2f}% (minimum: {min_representation*100}%)'
                )
        
        result['underrepresented_classes'] = underrepresented
        
        # Generate recommendations
        if underrepresented:
            result['passed'] = False
            result['errors'].append(
                f'{len(underrepresented)} classes below {min_representation*100}% threshold'
            )
            result['recommendations'] = self._generate_collection_recommendations(
                underrepresented, label_counts, total
            )
        
        return result
    
    def check_distribution(
        self,
        data: pd.DataFrame,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Check feature distribution for anomalies and statistical properties
        
        Args:
            data: DataFrame containing feature data
            feature_names: List of feature names to analyze
        
        Returns:
            Distribution analysis results
        """
        result = {
            'features': {},
            'warnings': []
        }
        
        for feature in feature_names:
            if feature not in data.columns:
                continue
            
            feature_data = data[feature].dropna()
            
            if len(feature_data) == 0:
                continue
            
            # Calculate distribution statistics
            stats = {
                'mean': float(feature_data.mean()),
                'std': float(feature_data.std()),
                'min': float(feature_data.min()),
                'max': float(feature_data.max()),
                'median': float(feature_data.median()),
                'q25': float(feature_data.quantile(0.25)),
                'q75': float(feature_data.quantile(0.75)),
                'skewness': float(feature_data.skew()),
                'kurtosis': float(feature_data.kurtosis())
            }
            
            # Check for distribution anomalies
            warnings = []
            
            # High skewness indicates asymmetric distribution
            if abs(stats['skewness']) > 2:
                warnings.append(f'High skewness: {stats["skewness"]:.2f}')
            
            # High kurtosis indicates heavy tails or outliers
            if abs(stats['kurtosis']) > 5:
                warnings.append(f'High kurtosis: {stats["kurtosis"]:.2f}')
            
            # Check if data is outside recommended ranges
            if feature in self.recommended_ranges:
                rec_min, rec_max = self.recommended_ranges[feature]
                below_rec = (feature_data < rec_min).sum()
                above_rec = (feature_data > rec_max).sum()
                
                if below_rec > 0 or above_rec > 0:
                    warnings.append(
                        f'{below_rec} values below recommended min ({rec_min}), '
                        f'{above_rec} values above recommended max ({rec_max})'
                    )
            
            stats['warnings'] = warnings
            result['features'][feature] = stats
            
            if warnings:
                result['warnings'].extend([f'{feature}: {w}' for w in warnings])
        
        return result
    
    def _check_nan_values(
        self,
        data: pd.DataFrame,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """Check for NaN values in features"""
        nan_counts = {}
        total_nans = 0
        
        for feature in feature_names:
            if feature in data.columns:
                nan_count = int(data[feature].isna().sum())
                if nan_count > 0:
                    nan_counts[feature] = nan_count
                    total_nans += nan_count
        
        return {
            'passed': total_nans == 0,
            'nan_counts': nan_counts,
            'total_nans': total_nans,
            'message': f'Found {total_nans} NaN values in {len(nan_counts)} features' if total_nans > 0 else 'No NaN values detected'
        }
    
    def _check_infinite_values(
        self,
        data: pd.DataFrame,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """Check for infinite values in features"""
        inf_counts = {}
        total_infs = 0
        
        for feature in feature_names:
            if feature in data.columns and pd.api.types.is_numeric_dtype(data[feature]):
                inf_count = int(np.isinf(data[feature]).sum())
                if inf_count > 0:
                    inf_counts[feature] = inf_count
                    total_infs += inf_count
        
        return {
            'passed': total_infs == 0,
            'inf_counts': inf_counts,
            'total_infs': total_infs,
            'message': f'Found {total_infs} infinite values in {len(inf_counts)} features' if total_infs > 0 else 'No infinite values detected'
        }
    
    def _check_feature_ranges(
        self,
        data: pd.DataFrame,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """Check if feature values fall within expected ranges"""
        out_of_range = {}
        warnings = []
        flagged_for_review = []
        
        for feature in feature_names:
            if feature not in data.columns:
                continue
            
            if feature not in self.expected_ranges:
                continue
            
            min_val, max_val = self.expected_ranges[feature]
            feature_data = data[feature].dropna()
            
            below_min = int((feature_data < min_val).sum())
            above_max = int((feature_data > max_val).sum())
            
            if below_min > 0 or above_max > 0:
                out_of_range[feature] = {
                    'below_min': below_min,
                    'above_max': above_max,
                    'expected_range': (min_val, max_val),
                    'actual_range': (float(feature_data.min()), float(feature_data.max()))
                }
                
                warning_msg = (
                    f'{feature}: {below_min} values below {min_val}, '
                    f'{above_max} values above {max_val}'
                )
                warnings.append(warning_msg)
                
                # Flag for manual review if significant portion is out of range
                total_out = below_min + above_max
                pct_out = total_out / len(feature_data) * 100
                if pct_out > 5:  # More than 5% out of range
                    flagged_for_review.append({
                        'feature': feature,
                        'percentage_out_of_range': pct_out,
                        'reason': f'{pct_out:.1f}% of values outside expected range'
                    })
        
        return {
            'passed': len(out_of_range) == 0,
            'out_of_range': out_of_range,
            'warnings': warnings,
            'flagged_for_review': flagged_for_review,
            'message': f'{len(out_of_range)} features have out-of-range values' if out_of_range else 'All values within expected ranges'
        }
    
    def _generate_collection_recommendations(
        self,
        underrepresented: Dict[str, float],
        label_counts: pd.Series,
        total: int
    ) -> List[str]:
        """Generate recommendations for data collection to balance classes"""
        recommendations = []
        
        for label, current_pct in underrepresented.items():
            current_count = label_counts.get(label, 0)
            target_count = int(total * MIN_CLASS_REPRESENTATION)
            needed = target_count - current_count
            
            recommendations.append(
                f'Collect {needed} more samples for class {label} '
                f'(current: {current_count}, target: {target_count})'
            )
        
        return recommendations


class TrainingDataValidator:
    """Validate training data quality"""
    
    def __init__(self):
        self.validation_rules = {
            'no_nulls': self._check_nulls,
            'no_infinites': self._check_infinites,
            'value_ranges': self._check_value_ranges,
            'label_distribution': self._check_label_distribution,
            'feature_correlation': self._check_feature_correlation
        }
        self.data_quality_validator = DataQualityValidator()
    
    def validate_dataset(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        label_column: str,
        expected_ranges: Dict[str, Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Validate training dataset using DataQualityValidator
        
        Args:
            data: Training data DataFrame
            feature_columns: List of feature column names
            label_column: Label column name
            expected_ranges: Expected value ranges for features
        
        Returns:
            Validation results with pass/fail status
        """
        validation_id = f"validation_{int(datetime.utcnow().timestamp())}"
        
        results = {
            'validation_id': validation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_rows': len(data),
            'feature_count': len(feature_columns),
            'checks': {},
            'passed': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # Initialize validator with custom ranges if provided
        if expected_ranges:
            validator = DataQualityValidator(expected_ranges)
        else:
            validator = self.data_quality_validator
        
        # Validate features
        try:
            feature_validation = validator.validate_features(data, feature_columns)
            results['checks']['feature_validation'] = feature_validation
            
            if not feature_validation['passed']:
                results['passed'] = False
                results['errors'].extend(feature_validation['errors'])
            
            if feature_validation.get('warnings'):
                results['warnings'].extend(feature_validation['warnings'])
        except Exception as e:
            results['checks']['feature_validation'] = {
                'passed': False,
                'error': str(e)
            }
            results['passed'] = False
            results['errors'].append(f'Feature validation error: {str(e)}')
        
        # Validate labels
        try:
            label_validation = validator.validate_labels(data[label_column])
            results['checks']['label_validation'] = label_validation
            
            if not label_validation['passed']:
                results['passed'] = False
                results['errors'].extend(label_validation['errors'])
            
            if label_validation.get('warnings'):
                results['warnings'].extend(label_validation['warnings'])
            
            if label_validation.get('recommendations'):
                results['recommendations'].extend(label_validation['recommendations'])
        except Exception as e:
            results['checks']['label_validation'] = {
                'passed': False,
                'error': str(e)
            }
            results['passed'] = False
            results['errors'].append(f'Label validation error: {str(e)}')
        
        # Check feature distribution
        try:
            distribution_check = validator.check_distribution(data, feature_columns)
            results['checks']['distribution_check'] = distribution_check
            
            if distribution_check.get('warnings'):
                results['warnings'].extend(distribution_check['warnings'])
        except Exception as e:
            results['checks']['distribution_check'] = {
                'error': str(e)
            }
            results['warnings'].append(f'Distribution check error: {str(e)}')
        
        # Run legacy validation checks for backward compatibility
        for check_name, check_func in self.validation_rules.items():
            try:
                check_result = check_func(
                    data, feature_columns, label_column, expected_ranges
                )
                results['checks'][check_name] = check_result
                
                if not check_result['passed']:
                    results['passed'] = False
                    if check_result.get('message') and check_result['message'] not in results['errors']:
                        results['errors'].append(check_result['message'])
                
                if check_result.get('warnings'):
                    for warning in check_result['warnings']:
                        if warning not in results['warnings']:
                            results['warnings'].append(warning)
                    
            except Exception as e:
                results['checks'][check_name] = {
                    'passed': False,
                    'error': str(e)
                }
                results['passed'] = False
                results['errors'].append(f'{check_name}: {str(e)}')
        
        # Store validation results
        self._store_results(results)
        
        # Send alert if validation failed
        if not results['passed']:
            self._send_alert(results)
        
        return results

    
    def _check_nulls(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        label_column: str,
        expected_ranges: Dict = None
    ) -> Dict[str, Any]:
        """Check for null/NaN values"""
        null_counts = data[feature_columns + [label_column]].isnull().sum()
        has_nulls = null_counts.sum() > 0
        
        return {
            'passed': not has_nulls,
            'null_counts': null_counts.to_dict(),
            'message': f'Found {null_counts.sum()} null values' if has_nulls else 'No null values'
        }
    
    def _check_infinites(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        label_column: str,
        expected_ranges: Dict = None
    ) -> Dict[str, Any]:
        """Check for infinite values"""
        inf_counts = {}
        total_infs = 0
        
        for col in feature_columns:
            if pd.api.types.is_numeric_dtype(data[col]):
                inf_count = np.isinf(data[col]).sum()
                if inf_count > 0:
                    inf_counts[col] = int(inf_count)
                    total_infs += inf_count
        
        return {
            'passed': total_infs == 0,
            'infinite_counts': inf_counts,
            'message': f'Found {total_infs} infinite values' if total_infs > 0 else 'No infinite values'
        }
    
    def _check_value_ranges(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        label_column: str,
        expected_ranges: Dict = None
    ) -> Dict[str, Any]:
        """Check if values are within expected ranges"""
        if not expected_ranges:
            return {'passed': True, 'message': 'No expected ranges provided'}
        
        out_of_range = {}
        warnings = []
        
        for col, (min_val, max_val) in expected_ranges.items():
            if col in data.columns:
                below_min = (data[col] < min_val).sum()
                above_max = (data[col] > max_val).sum()
                
                if below_min > 0 or above_max > 0:
                    out_of_range[col] = {
                        'below_min': int(below_min),
                        'above_max': int(above_max)
                    }
                    warnings.append(
                        f'{col}: {below_min} values below {min_val}, {above_max} values above {max_val}'
                    )
        
        return {
            'passed': len(out_of_range) == 0,
            'out_of_range': out_of_range,
            'warnings': warnings,
            'message': f'{len(out_of_range)} features have out-of-range values' if out_of_range else 'All values in range'
        }
    
    def _check_label_distribution(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        label_column: str,
        expected_ranges: Dict = None
    ) -> Dict[str, Any]:
        """Check label distribution for class imbalance"""
        label_counts = data[label_column].value_counts()
        total = len(data)
        label_distribution = (label_counts / total).to_dict()
        
        # Check if any class is underrepresented
        underrepresented = {
            label: pct for label, pct in label_distribution.items()
            if pct < MIN_CLASS_REPRESENTATION
        }
        
        return {
            'passed': len(underrepresented) == 0,
            'distribution': label_distribution,
            'underrepresented_classes': underrepresented,
            'message': f'{len(underrepresented)} classes below {MIN_CLASS_REPRESENTATION*100}% threshold' if underrepresented else 'Label distribution acceptable'
        }
    
    def _check_feature_correlation(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        label_column: str,
        expected_ranges: Dict = None
    ) -> Dict[str, Any]:
        """Check for highly correlated features"""
        numeric_features = [col for col in feature_columns if pd.api.types.is_numeric_dtype(data[col])]
        
        if len(numeric_features) < 2:
            return {'passed': True, 'message': 'Not enough numeric features for correlation check'}
        
        corr_matrix = data[numeric_features].corr()
        
        # Find highly correlated pairs (>0.95)
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > 0.95:
                    high_corr_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': float(corr_matrix.iloc[i, j])
                    })
        
        warnings = [
            f'{pair["feature1"]} and {pair["feature2"]}: {pair["correlation"]:.3f}'
            for pair in high_corr_pairs
        ]
        
        return {
            'passed': True,  # Warning only, not a failure
            'high_correlation_pairs': high_corr_pairs,
            'warnings': warnings,
            'message': f'Found {len(high_corr_pairs)} highly correlated feature pairs' if high_corr_pairs else 'No high correlations detected'
        }
    
    def _store_results(self, results: Dict[str, Any]):
        """Store validation results in DynamoDB"""
        try:
            # Convert numpy and float types to Decimal for DynamoDB
            def convert_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(item) for item in obj]
                elif isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32, float)):
                    return Decimal(str(obj))
                elif isinstance(obj, bool):
                    return obj
                elif isinstance(obj, str):
                    return obj
                elif obj is None:
                    return obj
                return obj
            
            clean_results = convert_types(results)
            validation_table.put_item(Item=clean_results)
            
        except ClientError as e:
            print(f"Error storing validation results: {e}")
        except Exception as e:
            print(f"Error converting types for DynamoDB: {e}")
    
    def _send_alert(self, results: Dict[str, Any]):
        """Send alert for failed validation"""
        if not ALERT_TOPIC_ARN:
            return
        
        try:
            message = {
                'validation_id': results['validation_id'],
                'timestamp': results['timestamp'],
                'status': 'FAILED',
                'errors': results['errors'],
                'warnings': results['warnings']
            }
            
            sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject='Training Data Validation Failed',
                Message=json.dumps(message, indent=2)
            )
        except ClientError as e:
            print(f"Error sending alert: {e}")
    
    def generate_report(self, validation_id: str) -> Dict[str, Any]:
        """Generate detailed validation report"""
        try:
            response = validation_table.get_item(Key={'validation_id': validation_id})
            
            if 'Item' not in response:
                return {'error': 'Validation results not found'}
            
            results = response['Item']
            
            # Generate summary
            report = {
                'validation_id': validation_id,
                'timestamp': results['timestamp'],
                'status': 'PASSED' if results['passed'] else 'FAILED',
                'summary': {
                    'total_rows': results['total_rows'],
                    'feature_count': results['feature_count'],
                    'checks_passed': sum(1 for check in results['checks'].values() if check.get('passed')),
                    'checks_failed': sum(1 for check in results['checks'].values() if not check.get('passed')),
                    'total_errors': len(results['errors']),
                    'total_warnings': len(results['warnings'])
                },
                'details': results['checks'],
                'errors': results['errors'],
                'warnings': results['warnings']
            }
            
            return report
            
        except ClientError as e:
            return {'error': f'Error generating report: {str(e)}'}


def lambda_handler(event, context):
    """
    Lambda handler for training data validation
    
    Event types:
    - S3 event: Triggered by new file upload to S3
    - Direct invocation with action: validate or get_report
    """
    validator = TrainingDataValidator()
    cloudwatch = boto3.client('cloudwatch')
    
    try:
        # Check if this is an S3 event
        if 'Records' in event and event['Records']:
            # S3 event trigger
            for record in event['Records']:
                if 's3' not in record:
                    continue
                
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                
                print(f"Processing S3 event: s3://{bucket}/{key}")
                
                # Load data from S3
                try:
                    obj = s3.get_object(Bucket=bucket, Key=key)
                    
                    # Determine file format
                    if key.endswith('.csv'):
                        data = pd.read_csv(obj['Body'])
                    elif key.endswith('.parquet'):
                        data = pd.read_parquet(obj['Body'])
                    else:
                        print(f"Unsupported file format: {key}")
                        continue
                    
                    # Infer feature columns and label column
                    # Assume last column is the label
                    feature_columns = list(data.columns[:-1])
                    label_column = data.columns[-1]
                    
                    # Filter to only water quality features
                    water_quality_features = ['pH', 'turbidity', 'tds', 'temperature', 'humidity',
                                             'latitude', 'longitude', 'hour', 'month', 'weekday']
                    feature_columns = [col for col in feature_columns if col in water_quality_features or col in data.columns]
                    
                    print(f"Validating {len(data)} rows with {len(feature_columns)} features")
                    
                    # Validate
                    results = validator.validate_dataset(
                        data=data,
                        feature_columns=feature_columns,
                        label_column=label_column,
                        expected_ranges=None  # Use defaults
                    )
                    
                    # Send CloudWatch metrics
                    try:
                        cloudwatch.put_metric_data(
                            Namespace='AquaChain/DataValidation',
                            MetricData=[
                                {
                                    'MetricName': 'ValidationSuccess' if results['passed'] else 'ValidationFailure',
                                    'Value': 1,
                                    'Unit': 'Count'
                                },
                                {
                                    'MetricName': 'RowsValidated',
                                    'Value': results['total_rows'],
                                    'Unit': 'Count'
                                },
                                {
                                    'MetricName': 'ErrorCount',
                                    'Value': len(results['errors']),
                                    'Unit': 'Count'
                                },
                                {
                                    'MetricName': 'WarningCount',
                                    'Value': len(results['warnings']),
                                    'Unit': 'Count'
                                }
                            ]
                        )
                    except Exception as e:
                        print(f"Error sending CloudWatch metrics: {e}")
                    
                    print(f"Validation {'PASSED' if results['passed'] else 'FAILED'}: {results['validation_id']}")
                    
                except Exception as e:
                    print(f"Error processing file {key}: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Send failure metric
                    try:
                        cloudwatch.put_metric_data(
                            Namespace='AquaChain/DataValidation',
                            MetricData=[
                                {
                                    'MetricName': 'ValidationError',
                                    'Value': 1,
                                    'Unit': 'Count'
                                }
                            ]
                        )
                    except:
                        pass
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'S3 event processed'})
            }
        
        # Direct invocation
        action = event.get('action', 'validate')
        
        if action == 'validate':
            # Load data from S3
            bucket = event['bucket']
            key = event['key']
            
            obj = s3.get_object(Bucket=bucket, Key=key)
            
            # Determine file format
            if key.endswith('.csv'):
                data = pd.read_csv(obj['Body'])
            elif key.endswith('.parquet'):
                data = pd.read_parquet(obj['Body'])
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Unsupported file format: {key}'})
                }
            
            # Validate
            results = validator.validate_dataset(
                data=data,
                feature_columns=event['feature_columns'],
                label_column=event['label_column'],
                expected_ranges=event.get('expected_ranges')
            )
            
            # Send CloudWatch metrics
            try:
                cloudwatch.put_metric_data(
                    Namespace='AquaChain/DataValidation',
                    MetricData=[
                        {
                            'MetricName': 'ValidationSuccess' if results['passed'] else 'ValidationFailure',
                            'Value': 1,
                            'Unit': 'Count'
                        }
                    ]
                )
            except Exception as e:
                print(f"Error sending CloudWatch metrics: {e}")
            
            return {
                'statusCode': 200 if results['passed'] else 400,
                'body': json.dumps(results, default=str)
            }
            
        elif action == 'get_report':
            report = validator.generate_report(event['validation_id'])
            
            return {
                'statusCode': 200,
                'body': json.dumps(report, default=str)
            }
            
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
            
    except Exception as e:
        print(f"Error in training data validation: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
