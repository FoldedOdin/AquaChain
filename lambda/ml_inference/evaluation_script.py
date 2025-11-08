"""
Model evaluation script for SageMaker Pipeline
Evaluates trained models on test set and generates comprehensive metrics
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (mean_squared_error, r2_score, mean_absolute_error,
                            classification_report, confusion_matrix, f1_score,
                            precision_score, recall_score, accuracy_score)
import argparse
import os
import pickle
import json
from datetime import datetime


def evaluate_models(model_path: str, test_path: str, output_path: str):
    """
    Evaluate trained models on test set
    
    Args:
        model_path: Path to trained models
        test_path: Path to test data
        output_path: Path to save evaluation results
    """
    print("Loading models and test data...")
    
    # Load models
    with open(os.path.join(model_path, 'wqi_model.pkl'), 'rb') as f:
        wqi_model = pickle.load(f)
    
    with open(os.path.join(model_path, 'anomaly_model.pkl'), 'rb') as f:
        anomaly_model = pickle.load(f)
    
    # Load test data
    test_df = pd.read_csv(os.path.join(test_path, 'test.csv'))
    
    feature_columns = [col for col in test_df.columns 
                      if col not in ['wqi_target', 'anomaly_label']]
    
    X_test = test_df[feature_columns].values
    y_wqi_test = test_df['wqi_target'].values
    y_anom_test = test_df['anomaly_label'].values
    
    print(f"Test samples: {len(X_test)}")
    
    # Evaluate WQI model
    print("\nEvaluating WQI regression model...")
    y_wqi_pred = wqi_model.predict(X_test)
    
    wqi_metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_wqi_test, y_wqi_pred))),
        'mae': float(mean_absolute_error(y_wqi_test, y_wqi_pred)),
        'r2': float(r2_score(y_wqi_test, y_wqi_pred)),
        'mape': float(np.mean(np.abs((y_wqi_test - y_wqi_pred) / y_wqi_test)) * 100)
    }
    
    print(f"WQI Model Test Metrics:")
    print(f"  RMSE: {wqi_metrics['rmse']:.4f}")
    print(f"  MAE: {wqi_metrics['mae']:.4f}")
    print(f"  R²: {wqi_metrics['r2']:.4f}")
    print(f"  MAPE: {wqi_metrics['mape']:.2f}%")
    
    # Calculate residuals
    residuals = y_wqi_test - y_wqi_pred
    wqi_metrics['residual_mean'] = float(np.mean(residuals))
    wqi_metrics['residual_std'] = float(np.std(residuals))
    
    # Evaluate anomaly detection model
    print("\nEvaluating anomaly detection model...")
    y_anom_pred = anomaly_model.predict(X_test)
    y_anom_proba = anomaly_model.predict_proba(X_test)
    
    anomaly_metrics = {
        'accuracy': float(accuracy_score(y_anom_test, y_anom_pred)),
        'f1_score': float(f1_score(y_anom_test, y_anom_pred, average='weighted')),
        'precision': float(precision_score(y_anom_test, y_anom_pred, average='weighted')),
        'recall': float(recall_score(y_anom_test, y_anom_pred, average='weighted'))
    }
    
    # Per-class metrics
    class_names = ['normal', 'sensor_fault', 'contamination']
    per_class_metrics = {}
    
    for i, class_name in enumerate(class_names):
        class_mask = (y_anom_test == i)
        if np.sum(class_mask) > 0:
            per_class_metrics[class_name] = {
                'precision': float(precision_score(y_anom_test == i, y_anom_pred == i)),
                'recall': float(recall_score(y_anom_test == i, y_anom_pred == i)),
                'f1_score': float(f1_score(y_anom_test == i, y_anom_pred == i)),
                'support': int(np.sum(class_mask))
            }
    
    anomaly_metrics['per_class'] = per_class_metrics
    
    print(f"Anomaly Model Test Metrics:")
    print(f"  Accuracy: {anomaly_metrics['accuracy']:.4f}")
    print(f"  F1 Score: {anomaly_metrics['f1_score']:.4f}")
    print(f"  Precision: {anomaly_metrics['precision']:.4f}")
    print(f"  Recall: {anomaly_metrics['recall']:.4f}")
    
    # Confusion matrix
    cm = confusion_matrix(y_anom_test, y_anom_pred)
    anomaly_metrics['confusion_matrix'] = cm.tolist()
    
    print("\nConfusion Matrix:")
    print(cm)
    
    print("\nClassification Report:")
    print(classification_report(y_anom_test, y_anom_pred, target_names=class_names))
    
    # Feature importance
    print("\nCalculating feature importance...")
    wqi_feature_importance = dict(zip(feature_columns, 
                                     wqi_model.feature_importances_.tolist()))
    anomaly_feature_importance = dict(zip(feature_columns,
                                         anomaly_model.feature_importances_.tolist()))
    
    # Sort by importance
    wqi_feature_importance = dict(sorted(wqi_feature_importance.items(),
                                        key=lambda x: x[1], reverse=True))
    anomaly_feature_importance = dict(sorted(anomaly_feature_importance.items(),
                                            key=lambda x: x[1], reverse=True))
    
    print("\nTop 5 WQI Features:")
    for feature, importance in list(wqi_feature_importance.items())[:5]:
        print(f"  {feature}: {importance:.4f}")
    
    print("\nTop 5 Anomaly Detection Features:")
    for feature, importance in list(anomaly_feature_importance.items())[:5]:
        print(f"  {feature}: {importance:.4f}")
    
    # Model performance by WQI range
    wqi_ranges = [(0, 50), (50, 70), (70, 85), (85, 100)]
    wqi_range_metrics = {}
    
    for low, high in wqi_ranges:
        mask = (y_wqi_test >= low) & (y_wqi_test < high)
        if np.sum(mask) > 0:
            range_rmse = float(np.sqrt(mean_squared_error(
                y_wqi_test[mask], y_wqi_pred[mask]
            )))
            wqi_range_metrics[f'{low}-{high}'] = {
                'rmse': range_rmse,
                'count': int(np.sum(mask))
            }
    
    # Compile evaluation report
    evaluation_report = {
        'evaluation_timestamp': datetime.utcnow().isoformat(),
        'test_samples': len(X_test),
        'wqi_metrics': wqi_metrics,
        'anomaly_metrics': anomaly_metrics,
        'wqi_feature_importance': wqi_feature_importance,
        'anomaly_feature_importance': anomaly_feature_importance,
        'wqi_range_performance': wqi_range_metrics,
        'model_quality': {
            'wqi_model_acceptable': wqi_metrics['rmse'] < 8.0,
            'anomaly_model_acceptable': anomaly_metrics['f1_score'] > 0.85
        }
    }
    
    # Save evaluation report
    os.makedirs(output_path, exist_ok=True)
    
    with open(os.path.join(output_path, 'evaluation.json'), 'w') as f:
        json.dump(evaluation_report, f, indent=2)
    
    print(f"\nEvaluation report saved to {output_path}/evaluation.json")
    
    # Save predictions for analysis
    predictions_df = pd.DataFrame({
        'wqi_actual': y_wqi_test,
        'wqi_predicted': y_wqi_pred,
        'wqi_error': y_wqi_test - y_wqi_pred,
        'anomaly_actual': y_anom_test,
        'anomaly_predicted': y_anom_pred,
        'anomaly_prob_normal': y_anom_proba[:, 0],
        'anomaly_prob_sensor_fault': y_anom_proba[:, 1],
        'anomaly_prob_contamination': y_anom_proba[:, 2]
    })
    
    predictions_df.to_csv(os.path.join(output_path, 'predictions.csv'), index=False)
    print(f"Predictions saved to {output_path}/predictions.csv")
    
    print("\nEvaluation complete!")
    
    # Return pass/fail status
    if (wqi_metrics['rmse'] < 8.0 and anomaly_metrics['f1_score'] > 0.85):
        print("✓ Model quality meets acceptance criteria")
        return 0
    else:
        print("✗ Model quality does not meet acceptance criteria")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', type=str, default='/opt/ml/processing/model')
    parser.add_argument('--test-path', type=str, default='/opt/ml/processing/test')
    parser.add_argument('--output-path', type=str, default='/opt/ml/processing/evaluation')
    
    args = parser.parse_args()
    
    exit_code = evaluate_models(args.model_path, args.test_path, args.output_path)
    exit(exit_code)
