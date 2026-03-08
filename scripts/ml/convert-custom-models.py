"""
Convert custom pickled models to XGBoost binary format (.ubj)
Uses the smaller custom models (14 MB total) instead of v1.0 models (1.2 GB)
Binary format is more compact and faster to load than JSON
"""

import pickle
import os
import json
import sys
from datetime import datetime


def convert_model_to_binary(pickle_path: str, output_path: str, model_name: str):
    """
    Convert pickled model to XGBoost binary format (.ubj)
    
    Args:
        pickle_path: Path to pickled model file
        output_path: Path to save binary model
        model_name: Name of the model (for logging)
    """
    print(f"\nConverting {model_name}...")
    print(f"  Source: {pickle_path}")
    print(f"  Target: {output_path}")
    
    try:
        # Load pickled model
        with open(pickle_path, 'rb') as f:
            model = pickle.load(f)
        
        original_size_mb = os.path.getsize(pickle_path) / (1024 * 1024)
        print(f"  ✓ Loaded pickled model ({original_size_mb:.2f} MB)")
        
        # Check model type
        model_type = type(model).__name__
        print(f"  Model type: {model_type}")
        
        # Save in binary format
        if hasattr(model, 'save_model'):
            # XGBoost Booster or sklearn wrapper
            model.save_model(output_path)
            print(f"  ✓ Saved as XGBoost binary format")
        elif hasattr(model, 'get_booster'):
            # XGBoost sklearn wrapper - extract booster
            booster = model.get_booster()
            booster.save_model(output_path)
            print(f"  ✓ Saved booster as XGBoost binary format")
        else:
            print(f"  ⚠️  Not an XGBoost model ({model_type}), keeping as pickle")
            # For non-XGBoost models (like RandomForest), just copy the pickle
            import shutil
            shutil.copy(pickle_path, output_path.replace('.ubj', '.pkl'))
            print(f"  ✓ Copied as pickle file")
            return True
        
        # Verify saved file
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        compression_ratio = (1 - file_size_mb / original_size_mb) * 100
        print(f"  ✓ File size: {file_size_mb:.2f} MB (saved {compression_ratio:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main conversion process"""
    
    print("="*60)
    print("XGBoost Model Conversion - Custom Models")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    
    # Paths
    models_dir = os.path.join(project_root, 'ml_models_backup')
    output_dir = os.path.join(project_root, 'ml_models_optimized')
    
    print(f"Models directory: {models_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Created output directory")
    
    # Models to convert (using custom models - much smaller!)
    conversions = [
        {
            'pickle': os.path.join(models_dir, 'wqi-model-vcustom.pkl'),
            'binary': os.path.join(output_dir, 'wqi_model.pkl'),
            'name': 'WQI Model (Custom)'
        },
        {
            'pickle': os.path.join(models_dir, 'anomaly-model-vcustom.pkl'),
            'binary': os.path.join(output_dir, 'anomaly_model.pkl'),
            'name': 'Anomaly Model (Custom)'
        }
    ]
    
    # Convert models
    results = []
    for conversion in conversions:
        if os.path.exists(conversion['pickle']):
            success = convert_model_to_binary(
                conversion['pickle'],
                conversion['binary'],
                conversion['name']
            )
            results.append((conversion['name'], success))
        else:
            print(f"\n❌ {conversion['name']}: File not found")
            print(f"   {conversion['pickle']}")
            results.append((conversion['name'], False))
    
    # Copy feature scaler
    print(f"\nCopying feature scaler...")
    scaler_src = os.path.join(models_dir, 'feature-scaler-vcustom.pkl')
    scaler_dst = os.path.join(output_dir, 'feature_scaler.pkl')
    
    if os.path.exists(scaler_src):
        import shutil
        shutil.copy(scaler_src, scaler_dst)
        print(f"  ✓ Copied feature scaler")
        results.append(('Feature Scaler', True))
    else:
        print(f"  ❌ Feature scaler not found")
        results.append(('Feature Scaler', False))
    
    # Copy metadata
    print(f"\nCopying metadata...")
    metadata_src = os.path.join(models_dir, 'model-metadata-vcustom.json')
    metadata_dst = os.path.join(output_dir, 'model_metadata.json')
    
    if os.path.exists(metadata_src):
        import shutil
        shutil.copy(metadata_src, metadata_dst)
        print(f"  ✓ Copied metadata")
        results.append(('Metadata', True))
    else:
        print(f"  ⚠️  Metadata not found (optional)")
    
    # Calculate total size
    print(f"\nCalculating total package size...")
    total_size_mb = 0
    for file in os.listdir(output_dir):
        filepath = os.path.join(output_dir, file)
        if os.path.isfile(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            total_size_mb += size_mb
            print(f"  {file}: {size_mb:.2f} MB")
    
    print(f"\n  Total: {total_size_mb:.2f} MB")
    
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
    print(f"Total package size: {total_size_mb:.2f} MB")
    
    if success_count >= 3:  # At least models and scaler
        print("\n✅ Models ready for packaging!")
        print(f"\nNext steps:")
        print(f"1. Review converted models in: {output_dir}")
        print(f"2. Run: python scripts/ml/package-optimized-models.py")
        print(f"3. Deploy: cdk deploy AquaChain-SageMaker-dev")
        return 0
    else:
        print("\n⚠️  Some conversions failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
