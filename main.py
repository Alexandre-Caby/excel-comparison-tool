import os
import sys

# Create necessary directories
os.makedirs("temp", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def main():
    """Main entry point for the Excel Comparison Tool"""
    try:
        # Import the app module
        from src.app import run_app
        
        # Run the application
        run_app()
    except Exception as e:
        print(f"\n⚠️ Error initializing application: {str(e)}")
        print("\nPlease make sure all dependencies are installed:")
        print("    pip install -r requirements.txt\n")
        sys.exit(1)

if __name__ == "__main__":
    # Check if we are running via streamlit or directly
    if any(arg.endswith('streamlit') for arg in sys.argv) or 'streamlit.runtime' in sys.modules:
        # Running via streamlit, proceed normally
        main()
    else:
        # Not running via streamlit CLI, show instructions
        print("\n\n⚠️ Excel Comparison Tool must be run with the Streamlit CLI ⚠️")
        print("\nPlease run the application with:")
        print(f"\n    streamlit run {__file__}\n")
        print("If you don't have Streamlit installed, install it with:")
        print("\n    pip install streamlit\n")