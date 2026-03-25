"""Helper script to create the Lambda deployment zip."""
import zipfile
import os

zip_path = 'function.zip'

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    # Handler is "orders/enhanced_order_management.lambda_handler"
    # so the file must live at orders/enhanced_order_management.py inside the zip
    z.write('enhanced_order_management.py', 'orders/enhanced_order_management.py')
    for root, dirs, files in os.walk('shared'):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                full_path = os.path.join(root, f)
                # Place shared/ at root so sys.path('../shared') and './shared' both resolve
                z.write(full_path, full_path.replace('\\', '/'))

print('ZIP created:', zip_path)
