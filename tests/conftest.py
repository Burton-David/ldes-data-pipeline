import sys
import os

# Add src directory to PYTHONPATH for pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
