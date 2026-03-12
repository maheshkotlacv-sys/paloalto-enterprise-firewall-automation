import sys
import os

# add python/ dir to path so tests can import modules directly
python_dir = os.path.join(os.path.dirname(__file__), '..', 'python')
if python_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(python_dir))
