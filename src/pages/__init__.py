# This file makes the pages directory a package for proper importing
# All page modules should define a show() function

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))