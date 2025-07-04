import os
import sys
import importlib

# Get directory paths
file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(file_dir)))
sys.path.insert(0, project_root)

sys.modules['src'] = importlib.import_module('secure_src')
sys.modules['src.utils'] = importlib.import_module('secure_src.utils')
sys.modules['src.utils.config'] = importlib.import_module('secure_src.utils.config')
sys.modules['src.core'] = importlib.import_module('secure_src.core')
sys.modules['src.models'] = importlib.import_module('secure_src.models')

import app
if __name__ == "__main__":
    app.app.run(debug=False, port=5000, host='localhost')