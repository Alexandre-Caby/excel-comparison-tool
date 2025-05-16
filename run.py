"""
Excel Comparison Tool Entry Point
This script serves as the main entry point for PyInstaller to build a standalone executable.
"""
import os
import sys
import importlib.metadata

# Add metadata fix for Streamlit when compiled with PyInstaller
def patched_version(self):
    return "1.28.1"

# Apply the monkey patch if needed
try:
    dist = importlib.metadata.distribution("streamlit")
    dist.version = patched_version
except:
    pass

# Create required directories
os.makedirs("temp", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Add the project directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    # Fix for streamlit.web.bootstrap.run() requiring arguments
    import streamlit.web.bootstrap
    
    # Get the path to main.py
    main_script_path = os.path.join(current_dir, "main.py")
    
    # Set up the command line arguments
    args = [
        "streamlit", "run",
        main_script_path,
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.serverAddress", "localhost",
        "--global.developmentMode", "false"
    ]
    
    # Call the bootstrap run function with all required arguments
    sys.argv = args
    
    try:
        # Try newer API first (4 args)
        sys.exit(streamlit.web.bootstrap.run(
            main_script_path,  # main script path
            False,            # is_hello (always False for our app)
            args,             # command line args
            {}                # flag options (empty dict)
        ))
    except TypeError:
        # Fall back to older API version if TypeError occurs
        try:
            # Try with just the script path
            sys.exit(streamlit.web.bootstrap.run(main_script_path))
        except:
            # Last resort: import and run our app directly
            print("Using fallback method to start streamlit...")
            from streamlit.web import cli as stcli
            sys.exit(stcli._main_run_clExplicit(main_script_path))
