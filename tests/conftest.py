"""pytest configuration for the bookshelf test suite.

Adds the project root to ``sys.path`` so that ``import app`` and
``import config`` resolve correctly when pytest is run from any directory.
"""

import sys
import os

# Insert the bookshelf/ project root (one level above this file) onto the
# path so all absolute imports work without an installed package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
