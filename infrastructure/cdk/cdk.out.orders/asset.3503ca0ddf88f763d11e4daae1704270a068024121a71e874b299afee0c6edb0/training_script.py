"""
Model training script for SageMaker Pipeline
Trains Random Forest models for WQI prediction and anomaly detection
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, r2_score, classification_report, f1_score
import argparse
import os
import pickle
import json


def train_models(train_path: str, validation_path: str, model_path: str,
                n_estimators: int = 100, max_depth: int = 10,
                min_samples_split: int = 5, min_samples_leaf: int = 2,
                max_features: float = 0.8):
    """
    Train WQI regression and anomaly detection models
    
    Args:
        train_path: Path to training data
        validation_path: Path to validation data
        model_path: Path to save trained models
        n_estimators: Number of trees in forest
        max_depth: Maximum depth of trees
        min_samples_split: Minimum samples to split node
        min_samples_leaf: Minimum samples in leaf node
        max_features: Fraction of features to consider for split
    """
    print("Loading training data...")
    train_df = pd.read_csv(os.path.join(train_path, 'train.csv'))
    val_df = pd.read_csv(os.path.join(validation_path, 'validation.csv'))
    
    # Separate features and targets
    feature_columns = [col for col in train_df.columns 
                      if col not in ['wqi_target', 'anomaly_label']]
    
    X_train = train_df[feature_columns].values
    y_wqi_train = train_df['wqi_target'].values
    y_anom_train = train_df['anomaly_label'].values
    
    X_val = val_df[feature_columns].values
    y_wqi_val = val_df['wqi_target'].values
    y_anom_val = val_df['anomaly_label'].values
    
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Features: {len(feature_columns)}")
    
    # Train WQI regression model
    print("\nTraining WQI regression model...")
    wqi_model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    wqi_model.fit(X_train, y_wqi_train)
    
    # Evaluate WQI model
    y_wqi_pred_train = wqi_model.predict(X_train)
    y_wqi_pred_val = wqi_model.predict(X_val)
    
    train_rmse = np.sqrt(mean_squared_error(y_wqi_train, y_wqi_pred_train))
    train_r2 = r2_score(y_wqi_train, y_wqi_pred_train)
    val_rmse = np.sqrt(mean_squared_error(y_wqi_val, y_wqi_pred_val))
    val_r2 = r2_score(y_wqi_val, y_wqi_pred_val)
    
    print(f"WQI Model - Train RMSE: {train_rmse:.4f}, R²: {train_r2:.4f}")
    print(f"WQI Model - Validation RMSE: {val_rmse:.4f}, R²: {val_r2:.4f}")
    
    # Log metrics for hyperparameter tuning
    print(f"validation_rmse: {val_rmse:.4f}")
    print(f"validation_r2: {val_r2:.4f}")
    
    # Train anomaly detection model
    print("\nTraining anomaly detection model...")
    anomaly_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced',
        verbose=1
    )
    
    anomaly_model.fit(X_train, y_anom_train)
    
    # Evaluate anomaly model
    y_anom_pred_train = anomaly_model.predict(X_train)
    y_anom_pred_val = anomaly_model.predict(X_val)
    
    train_f1 = f1_score(y_anom_train, y_anom_pred_train, average='weighted')
    val_f1 = f1_score(y_anom_val, y_anom_pred_val, average='weighted')
    
    print(f"Anomaly Model - Train F1: {train_f1:.4f}")
    print(f"Anomaly Model - Validation F1: {val_f1:.4f}")
    
    print("\nValidation Classification Report:")
    print(classification_report(y_anom_val, y_anom_pred_val,
                               target_names=['normal', 'sensor_fault', 'contamination']))
    
    # Save models
    os.makedirs(model_path, exist_ok=True)
    
    with open(os.path.join(model_path, 'wqi_model.pkl'), 'wb') as f:
        pickle.dump(wqi_model, f)
    
    with open(os.path.join(model_path, 'anomaly_model.pkl'), 'wb') as f:
        pickle.dump(anomaly_model, f)
    
    # Save feature names
    with open(os.path.join(model_path, 'feature_names.json'), 'w') as f:
        json.dump(feature_columns, f)
    
    # Save training metrics
    metrics = {
        'wqi_metrics': {
            'train_rmse': float(train_rmse),
            'train_r2': float(train_r2),
            'validation_rmse': float(val_rmse),
            'validation_r2': float(val_r2)
        },
        'anomaly_metrics': {
            'train_f1': float(train_f1),
            'validation_f1': float(val_f1)
        },
        'hyperparameters': {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'max_features': max_features
        }
    }
    
    with open(os.path.join(model_path, 'training_metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\nModels saved to {model_path}")
    print("Training complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # Data paths
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--validation', type=str, default=os.environ.get('SM_CHANNEL_VALIDATION'))
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    
    # Hyperparameters
    parser.add_argument('--n_estimators', type=int, default=100)
    parser.add_argument('--max_depth', type=int, default=10)
    parser.add_argument('--min_samples_split', type=int, default=5)
    parser.add_argument('--min_samples_leaf', type=int, default=2)
    parser.add_argument('--max_features', type=float, default=0.8)
    
    args = parser.parse_args()
    
    train_models(
        train_path=args.train,
        validation_path=args.validation,
        model_path=args.model_dir,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        min_samples_leaf=args.min_samples_leaf,
        max_features=args.max_features
    )
