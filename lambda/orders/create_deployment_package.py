"""
Create deployment package for orders API Lambda
"""
import zipfile
import os
from pathlib import Path


def create_zip(output_filename='orders-api-deployment.zip'):
    """Create a zip file with all necessary files"""
    
    # Files to include
    files_to_include = [
        'lambda_function.py',
        'create_order.py',
        'get_orders.py',
        'update_order_status.py',
        'cancel_order.py'
    ]
    
    # Create zip file
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add Python files
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file, file)
                print(f"Added: {file}")
            else:
                print(f"Warning: {file} not found")
        
        # Add dependencies from package directory if it exists
        if os.path.exists('package'):
            for root, dirs, files in os.walk('package'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'package')
                    zipf.write(file_path, arcname)
    
    print(f"\nDeployment package created: {output_filename}")
    print(f"Size: {os.path.getsize(output_filename) / 1024 / 1024:.2f} MB")
    return output_filename


if __name__ == '__main__':
    create_zip()
