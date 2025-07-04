import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import app
if __name__ == "__main__":
    app.app.run(debug=False, port=5000, host='localhost')