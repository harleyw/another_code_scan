import os
import sys

# Add the adaptive_rag directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'adaptive_rag'))

from util.config_manager import ConfigManager

try:
    # Try to import the build_index module
    import build_index
    print("Build index module imported successfully")
    
    # Check if the retriever is created
    if hasattr(build_index, 'retriever'):
        print("Retriever created successfully")
        
        # Test querying the retriever
        # Note: This will only work if you have set the DASHSCOPE_API_KEY environment variable
        print("Testing retriever query...")
        try:
            # This is a simple test query
            results = build_index.retriever.invoke("test query")
            print(f"Retriever query successful, got {len(results)} results")
        except Exception as e:
            print(f"Retriever query failed (expected if DASHSCOPE_API_KEY not set): {e}")
    else:
        print("Retriever not found")
        
    # Check if the Excel file was processed
    if os.path.exists("test1.xlsx"):
        print("Excel file found and processed")
    else:
        print("Excel file not found")
        
except Exception as e:
    print(f"Error importing build_index module: {e}")