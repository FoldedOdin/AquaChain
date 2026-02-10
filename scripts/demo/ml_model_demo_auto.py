#!/usr/bin/env python3
"""
AquaChain ML Model Demo Script (Auto Mode)
Demonstrates XGBoost model predictions with various water quality scenarios
Runs automatically without user input - perfect for presentations
"""

import pickle
import json
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
import time

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

class AquaChainMLDemo:
    """Demo class for AquaChain ML models"""
    
    def __init__(self, models_dir="ml_models_backup"):
        """Initialize the demo with model directory"""
        self.models_dir = Path(models_dir)
        self.wqi_model = None
        self.anomaly_model = None
        self.scaler = None
        self.metadata = None
        
    def load_models(self):
        """Load the trained models"""
        print_header("Loading AquaChain XGBoost Models")
        
        try:
            # Load WQI model
            wqi_path = self.models_dir / "WQI-model-v1.0.pkl"
            with open(wqi_path, 'rb') as f:
                self.wqi_model = pickle.load(f)
            print_success(f"Loaded WQI Model (XGBRegressor)")
            
            # Load Anomaly model
            anomaly_path = self.models_dir / "Anomaly-model-v1.0.pkl"
            with open(anomaly_path, 'rb') as f:
                self.anomaly_model = pickle.load(f)
            print_success(f"Loaded Anomaly Model (XGBClassifier)")
            
            # Load scaler
            scaler_path = self.models_dir / "feature-scaler-v1.0.pkl"
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            print_success(f"Loaded Feature Scaler (StandardScaler)")
            
            # Load metadata
            metadata_path = self.models_dir / "model-metadata-v1.0.json"
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            print_success(f"Loaded Model Metadata (v{self.metadata['version']})")
            
            print_info(f"Model trained on: {self.metadata['created_at']}")
            print_info(f"Features: {len(self.metadata['features'])} engineered features")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to load models: {str(e)}")
            return False
    
    def engineer_features(self, sensor_data):
        """Engineer features from raw sensor data"""
        # Extract base features
        pH = sensor_data['pH']
        turbidity = sensor_data['turbidity']
        tds = sensor_data['tds']
        temperature = sensor_data['temperature']
        humidity = sensor_data.get('humidity', 60.0)
        latitude = sensor_data.get('latitude', 10.0)
        longitude = sensor_data.get('longitude', 76.0)
        
        # Temporal features
        now = datetime.now()
        hour = now.hour
        month = now.month
        weekday = now.weekday()
        
        # Engineered features
        pH_temp_interaction = pH * temperature
        turbidity_tds_ratio = turbidity / (tds + 1e-6)  # Avoid division by zero
        pH_deviation = abs(pH - 7.0)
        temp_deviation = temperature - 25.0
        
        # Create feature array in correct order
        features = np.array([[
            pH,
            turbidity,
            tds,
            temperature,
            humidity,
            latitude,
            longitude,
            hour,
            month,
            weekday,
            pH_temp_interaction,
            turbidity_tds_ratio,
            pH_deviation,
            temp_deviation
        ]])
        
        return features
    
    def predict(self, sensor_data, scenario_name=""):
        """Make predictions for given sensor data"""
        import xgboost as xgb
        
        # Engineer features
        features = self.engineer_features(sensor_data)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Get feature names from metadata
        feature_names = self.metadata['features']
        
        # Create DMatrix with feature names for XGBoost models
        dmatrix = xgb.DMatrix(features_scaled, feature_names=feature_names)
        
        # Predict WQI (regression)
        wqi = float(self.wqi_model.predict(dmatrix)[0])
        
        # Predict anomaly (classification)
        # Native XGBoost returns raw predictions, need to convert to probabilities
        raw_predictions = self.anomaly_model.predict(dmatrix, output_margin=False)
        
        # For multi-class, XGBoost returns probabilities directly when ntree_limit=0
        # Shape will be (n_samples, n_classes)
        if len(raw_predictions.shape) > 1 and raw_predictions.shape[1] > 1:
            # Multi-class probabilities
            anomaly_proba = raw_predictions[0]
            anomaly_class = int(np.argmax(anomaly_proba))
        else:
            # Binary or single prediction - treat as class index
            anomaly_class = int(raw_predictions[0])
            # Create one-hot probabilities
            anomaly_proba = np.zeros(3)
            anomaly_proba[anomaly_class] = 1.0
        
        # Get class names (assuming: 0=normal, 1=contamination, 2=sensor_fault)
        class_names = ['Normal', 'Contamination', 'Sensor Fault']
        anomaly_label = class_names[anomaly_class] if anomaly_class < len(class_names) else f"Class {anomaly_class}"
        
        return {
            'scenario': scenario_name,
            'sensor_data': sensor_data,
            'wqi': wqi,
            'anomaly_class': anomaly_label,
            'anomaly_confidence': float(np.max(anomaly_proba)),
            'class_probabilities': {
                'Normal': float(anomaly_proba[0]) if len(anomaly_proba) > 0 else 0.0,
                'Contamination': float(anomaly_proba[1]) if len(anomaly_proba) > 1 else 0.0,
                'Sensor Fault': float(anomaly_proba[2]) if len(anomaly_proba) > 2 else 0.0
            }
        }
    
    def display_prediction(self, result):
        """Display prediction results in a formatted way"""
        print(f"\n{Colors.BOLD}Scenario: {result['scenario']}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'─'*70}{Colors.ENDC}")
        
        # Display sensor readings
        print(f"\n{Colors.BOLD}Sensor Readings:{Colors.ENDC}")
        data = result['sensor_data']
        print(f"  pH Level:      {data['pH']:.2f}")
        print(f"  Turbidity:     {data['turbidity']:.2f} NTU")
        print(f"  TDS:           {data['tds']:.0f} ppm")
        print(f"  Temperature:   {data['temperature']:.1f}°C")
        
        # Display WQI
        wqi = result['wqi']
        anomaly = result['anomaly_class']
        
        # Adjust color based on both WQI and anomaly status
        if anomaly != 'Normal':
            wqi_color = Colors.FAIL  # Red if contamination or sensor fault detected
        elif wqi >= 80:
            wqi_color = Colors.OKGREEN
        elif wqi >= 50:
            wqi_color = Colors.WARNING
        else:
            wqi_color = Colors.FAIL
            
        print(f"\n{Colors.BOLD}Water Quality Index (WQI):{Colors.ENDC}")
        print(f"  {wqi_color}{wqi:.2f}/100{Colors.ENDC}")
        
        # WQI interpretation - modified to account for anomaly detection
        if anomaly != 'Normal':
            print(f"  {Colors.FAIL}⚠ UNSAFE - {anomaly} Detected{Colors.ENDC}")
            print(f"  {Colors.FAIL}Not suitable for consumption{Colors.ENDC}")
        elif wqi >= 90:
            print(f"  {Colors.OKGREEN}Excellent - Safe for all uses{Colors.ENDC}")
        elif wqi >= 70:
            print(f"  {Colors.OKGREEN}Good - Safe for drinking{Colors.ENDC}")
        elif wqi >= 50:
            print(f"  {Colors.WARNING}Fair - Treatment recommended{Colors.ENDC}")
        elif wqi >= 25:
            print(f"  {Colors.WARNING}Poor - Not suitable for drinking{Colors.ENDC}")
        else:
            print(f"  {Colors.FAIL}Very Poor - Unsafe{Colors.ENDC}")
        
        # Display anomaly detection
        anomaly = result['anomaly_class']
        confidence = result['anomaly_confidence']
        
        print(f"\n{Colors.BOLD}Anomaly Detection:{Colors.ENDC}")
        
        if anomaly == 'Normal':
            print(f"  Status: {Colors.OKGREEN}{anomaly}{Colors.ENDC}")
        elif anomaly == 'Contamination':
            print(f"  Status: {Colors.FAIL}{anomaly}{Colors.ENDC}")
        else:
            print(f"  Status: {Colors.WARNING}{anomaly}{Colors.ENDC}")
        
        print(f"  Confidence: {confidence*100:.2f}%")
        
        # Display class probabilities
        print(f"\n{Colors.BOLD}Class Probabilities:{Colors.ENDC}")
        probs = result['class_probabilities']
        for class_name, prob in probs.items():
            bar_length = int(prob * 30)
            bar = '█' * bar_length + '░' * (30 - bar_length)
            print(f"  {class_name:15s} {bar} {prob*100:5.2f}%")
        
        print(f"\n{Colors.OKCYAN}{'─'*70}{Colors.ENDC}")

def main():
    """Main demo function"""
    print_header("AquaChain ML Model Demo (Auto Mode)")
    print_info("XGBoost-based Water Quality Prediction System")
    print_info("Accuracy: 99.74% | Features: 14 | GPU-Accelerated Training\n")
    
    # Initialize demo
    demo = AquaChainMLDemo()
    
    # Load models
    if not demo.load_models():
        print_error("Failed to load models. Exiting.")
        sys.exit(1)
    
    # Define test scenarios
    scenarios = [
        {
            'name': '🟢 Scenario 1: Excellent Water Quality',
            'data': {
                'pH': 7.2,
                'turbidity': 1.5,
                'tds': 180,
                'temperature': 22.0,
                'humidity': 65.0,
                'latitude': 10.0,
                'longitude': 76.0
            }
        },
        {
            'name': '🟡 Scenario 2: Moderate Quality (High TDS)',
            'data': {
                'pH': 7.5,
                'turbidity': 3.2,
                'tds': 450,
                'temperature': 26.0,
                'humidity': 70.0,
                'latitude': 10.0,
                'longitude': 76.0
            }
        },
        {
            'name': '🔴 Scenario 3: Poor Quality (High Turbidity)',
            'data': {
                'pH': 6.8,
                'turbidity': 15.0,
                'tds': 320,
                'temperature': 28.0,
                'humidity': 75.0,
                'latitude': 10.0,
                'longitude': 76.0
            }
        },
        {
            'name': '⚠️  Scenario 4: Potential Contamination (Acidic)',
            'data': {
                'pH': 5.2,
                'turbidity': 8.5,
                'tds': 280,
                'temperature': 24.0,
                'humidity': 68.0,
                'latitude': 10.0,
                'longitude': 76.0
            }
        },
        {
            'name': '⚠️  Scenario 5: Severe Contamination (Extreme pH)',
            'data': {
                'pH': 12.5,
                'turbidity': 0.1,
                'tds': 50,
                'temperature': 45.0,
                'humidity': 90.0,
                'latitude': 10.0,
                'longitude': 76.0
            }
        }
    ]
    
    # Run predictions for each scenario
    print_header("Running Predictions")
    
    for i, scenario in enumerate(scenarios, 1):
        result = demo.predict(scenario['data'], scenario['name'])
        demo.display_prediction(result)
        
        # Auto-advance after 3 seconds (except last scenario)
        if i < len(scenarios):
            print(f"\n{Colors.OKCYAN}Advancing to next scenario in 3 seconds...{Colors.ENDC}")
            time.sleep(3)
    
    # Summary
    print_header("Demo Complete")
    print_success("All scenarios processed successfully!")
    print_info("Model Performance:")
    print_info("  • Accuracy: 99.74%")
    print_info("  • Algorithm: XGBoost (GPU-accelerated)")
    print_info("  • Features: 14 engineered features")
    print_info("  • Inference Time: <500ms")
    print_info("\nThank you for watching the AquaChain ML Demo!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Demo interrupted by user.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
