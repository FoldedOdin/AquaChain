"""
Data preprocessing script for SageMaker Pipeline
Handles data splitting, feature engineering, and scaling
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import argparse
import os
import pickle


def preprocess_data(input_path: str, output_path: str):
    """
    Preprocess raw data for ML training
    
    Args:
        input_path: Path to raw data
        output_path: Path to save processed data
    """
    print("Loading raw data...")
    
    # Load data
    data_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
    dfs = []
    for file in data_files:
        df = pd.read_csv(os.path.join(input_path, file))
        dfs.append(df)
    
    data = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(data)} samples")
    
    # Remove metadata columns
    feature_columns = [
        'pH', 'turbidity', 'tds', 'temperature', 'latitude', 'longitude', 'hour', 'month', 'weekday',
        'pH_temp_interaction', 'turbidity_tds_ratio', 
        'pH_deviation', 'temp_deviation'
    ]
    
    X = data[feature_columns].values
    y_wqi = data['wqi_target'].values
    y_anomaly = data['anomaly_label'].values
    
    # Split data: 70% train, 15% validation, 15% test
    X_train, X_temp, y_wqi_train, y_wqi_temp, y_anom_train, y_anom_temp = train_test_split(
        X, y_wqi, y_anomaly, test_size=0.3, random_state=42, stratify=y_anomaly
    )
    
    X_val, X_test, y_wqi_val, y_wqi_test, y_anom_val, y_anom_test = train_test_split(
        X_temp, y_wqi_temp, y_anom_temp, test_size=0.5, random_state=42, stratify=y_anom_temp
    )
    
    print(f"Train: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    # Fit scaler on training data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Save scaler
    scaler_path = os.path.join(output_path, 'scaler.pkl')
    os.makedirs(output_path, exist_ok=True)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler saved to {scaler_path}")
    
    # Save processed datasets
    train_path = os.path.join(output_path, 'train')
    val_path = os.path.join(output_path, 'validation')
    test_path = os.path.join(output_path, 'test')
    
    os.makedirs(train_path, exist_ok=True)
    os.makedirs(val_path, exist_ok=True)
    os.makedirs(test_path, exist_ok=True)
    
    # Save as CSV with targets
    train_df = pd.DataFrame(X_train_scaled, columns=feature_columns)
    train_df['wqi_target'] = y_wqi_train
    train_df['anomaly_label'] = y_anom_train
    train_df.to_csv(os.path.join(train_path, 'train.csv'), index=False)
    
    val_df = pd.DataFrame(X_val_scaled, columns=feature_columns)
    val_df['wqi_target'] = y_wqi_val
    val_df['anomaly_label'] = y_anom_val
    val_df.to_csv(os.path.join(val_path, 'validation.csv'), index=False)
    
    test_df = pd.DataFrame(X_test_scaled, columns=feature_columns)
    test_df['wqi_target'] = y_wqi_test
    test_df['anomaly_label'] = y_anom_test
    test_df.to_csv(os.path.join(test_path, 'test.csv'), index=False)
    
    print("Data preprocessing complete!")
    print(f"  Train samples: {len(train_df)}")
    print(f"  Validation samples: {len(val_df)}")
    print(f"  Test samples: {len(test_df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', type=str, default='/opt/ml/processing/input')
    parser.add_argument('--output-path', type=str, default='/opt/ml/processing')
    
    args = parser.parse_args()
    
    preprocess_data(args.input_path, args.output_path)
