import os
import sys

# Add the adaptive_rag directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'adaptive_rag'))

try:
    # Try to import the build_index module
    import build_index
    print("Build index module imported successfully")
    
    # Check if the retriever is created
    if hasattr(build_index, 'retriever'):
        print("Retriever created successfully")
    else:
        print("Retriever not found")
        
except Exception as e:
    print(f"Error importing build_index module: {e}")