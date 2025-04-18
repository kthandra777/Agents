import importlib
import sys
import os

def apply_patch():
    """
    Apply patches to make ChromaDB work with older SQLite versions
    by monkey patching the version check
    """
    # First try to import pysqlite3 if available
    try:
        import pysqlite3
        sys.modules["sqlite3"] = pysqlite3
        print("Successfully loaded pysqlite3 as a replacement for sqlite3")
        return True
    except ImportError:
        print("pysqlite3 not available, attempting to patch ChromaDB")
    
    # If pysqlite3 is not available, monkey patch the version check
    try:
        # Try to load chromadb with a patched version check
        import chromadb
        
        # Find the chromadb.__init__ module
        init_spec = importlib.util.find_spec('chromadb')
        if not init_spec:
            print("Could not find chromadb module")
            return False
        
        # Rewrite the __init__.py file to disable the version check
        init_path = init_spec.origin
        with open(init_path, 'r') as f:
            init_content = f.read()
        
        # Replace the version check logic with a pass statement
        patched_content = init_content.replace(
            "if not has_pysqlite and not sqlite_version_info >= (3, 35, 0):",
            "if False:  # Patched to bypass SQLite version check"
        )
        
        # Write back the patched file
        with open(init_path, 'w') as f:
            f.write(patched_content)
            
        print("Successfully patched ChromaDB to bypass SQLite version check")
        
        # Force reload of the module
        if 'chromadb' in sys.modules:
            del sys.modules['chromadb']
        importlib.import_module('chromadb')
        
        return True
    except Exception as e:
        print(f"Failed to patch ChromaDB: {str(e)}")
        return False 