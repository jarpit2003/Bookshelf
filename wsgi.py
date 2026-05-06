"""WSGI entry point for PythonAnywhere.

PythonAnywhere looks for a callable named `application` in this file.

Replace every occurrence of "myusername" with your actual
PythonAnywhere username before uploading.
"""

import sys
import os

# ── 1. Put the project root on the Python path ──────────────────────────────
# This lets `import app`, `import config`, and `import seed` all resolve
# without installing the project as a package.
PROJECT_ROOT = "/home/myusername/bookshelf"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── 2. Force production settings before the app is created ──────────────────
# Overwrite the DEBUG flag that config.py sets to True so the production
# server never runs in debug mode.
os.environ.setdefault("SECRET_KEY", "replace-with-a-long-random-secret")

import config as _config          # noqa: E402  (import after sys.path change)
_config.DEBUG = False              # never run debug mode in production

# ── 3. Create the WSGI application object ───────────────────────────────────
from app import create_app         # noqa: E402

application = create_app()
application.debug = False
