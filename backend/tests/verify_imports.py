import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing AppConfig...")
    from backend.src.config import AppConfig
    print("AppConfig imported.")
    
    print("Importing orchestrator...")
    from backend.src.orchestrator import get_orchestrator_node
    print("Imports successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
