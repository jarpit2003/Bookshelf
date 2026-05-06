"""WSGI entry point for PythonAnywhere.

PythonAnywhere looks for a callable named `application` in this file.
"""

import sys
import os

# ── 1. Put the project root on the Python path ──────────────────────────────
PROJECT_ROOT = "/home/jarpit1710/Bookshelf"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── 2. Force production settings ────────────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "jarpit1710-bookshelf-secret-key-2024")

import config as _config
_config.DEBUG = False

# ── 3. Create the WSGI application object ───────────────────────────────────
from app import create_app

application = create_app()
application.debug = False
