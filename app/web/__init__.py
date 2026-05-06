"""Web blueprint – server-rendered HTML pages.

Registered in create_app() with no url_prefix so routes live at /.
"""

from flask import Blueprint

bp = Blueprint("web", __name__)

from app.web import routes  # noqa: E402, F401
