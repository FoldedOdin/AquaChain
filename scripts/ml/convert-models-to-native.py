"""
Convert pickled XGBoost models to native JSON format
Solves scipy/numpy version incompatibility in SageMaker containers
"""

import pickle
import os
import json
import sys
from datetime import datetime


def convert_model_to_native(pickle_path: str, output_path: str, model_name: str):
    """
    Convert pickled XGBoost model to native JSON format
    
    Args:
        pickle_path: Path to pickled model file
        output_path: Path to save JSON model
        model_name: Name of the model (for logging)
    """
    print(f"\nConverting {model_name}...")
    print(f"  Source: {pickle_path}")
    print(f"  Target: {output_path}")
    
    try:
        # Load pickled model
        with open(pickle_path, 'rb') as f:
            model = pickle.load(f)
        
        print(f"  ✓ Loaded pickled model")
        
        # Check if it's an XGBoost model
        model_type = type(model).__name__
        print(f"  Model type: {model_type}")
        
        # Save in native format
        if hasattr(model, 'save_model'):
            # XGBoost Booster or sklearn wrapper
            model.save_model(output_path)
            print(f"  ✓ Saved as XGBoost native format")
        elif hasattr(model, 'get_booster'):
            # XGBoost sklearn wrapper - extract booster
            booster = model.get_booster()
            booster.save_model(output_path)
            print(f"  ✓ Saved booster as XGBoost native format")
        else:
            print(f"  ⚠️  Warning: Not an XGBoost model, keeping as pickle")
            return False
        
        # Verify saved file
        file_size_kb = os.path.getsize(output_path) / 1024
        print(f"  ✓ File size: {file_size_kb:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Main conversion process"""
    
    print("="*60)
    print("XGBoost Model Conversion to Native Format")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    
    # Paths
    models_dir = os.path.join(project_root, 'ml_models_backup')
    output_dir = os.path.join(project_root, 'ml_models_native')
    
    print(f"Models directory: {models_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Created output directory")
    
    # Models to convert
    conversions = [
        {
            'pickle': os.path.join(models_dir, 'WQI-model-v1.0.pkl'),
            'native': os.path.join(output_dir, 'wqi_model.json'),
            'name': 'WQI Model'
        },
        {
            'pickle': os.path.join(models_dir, 'Anomaly-model-v1.0.pkl'),
            'native': os.path.join(output_dir, 'anomaly_model.json'),
            'name': 'Anomaly Model'
        }
    ]
    
    # Convert models
    results = []
    for conversion in conversions:
        if os.path.exists(conversion['pickle']):
            success = convert_model_to_native(
                conversion['pickle'],
                conversion['native'],
                conversion['name']
            )
            results.append((conversion['name'], success))
        else:
            print(f"\n❌ {conversion['name']}: File not found")
            print(f"   {conversion['pickle']}")
            results.append((conversion['name'], False))
    
    # Copy feature scaler (keep as pickle - it's sklearn, not XGBoost)
    print(f"\nCopying feature scaler...")
    scaler_src = os.path.join(models_dir, 'feature-scaler-v1.0.pkl')
    scaler_dst = os.path.join(output_dir, 'feature_scaler.pkl')
    
    if os.path.exists(scaler_src):
        import shutil
        shutil.copy(scaler_src, scaler_dst)
        print(f"  ✓ Copied feature scaler (keeping as pickle)")
        results.append(('Feature Scaler', True))
    else:
        print(f"  ❌ Feature scaler not found")
        results.append(('Feature Scaler', False))
    
    # Summary
    print("\n" + "="*60)
    print("Conversion Summary")
    print("="*60)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for name, success in results:
        status = "✓" if success else "❌"
        print(f"{status} {name}")
    
    print()
    print(f"Success: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✅ All models converted successfully!")
        print(f"\nNext steps:")
        print(f"1. Review converted models in: {output_dir}")
        print(f"2. Run: python scripts/ml/package-native-models.py")
        print(f"3. Deploy: cdk deploy AquaChain-SageMaker-dev")
        return 0
    else:
        print("\n⚠️  Some conversions failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
