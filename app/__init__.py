"""Application factory for the Bookshelf Flask app."""

import logging
import os
import sqlite3

from flask import Flask, render_template

import config

_log = logging.getLogger(__name__)

# Absolute path to the static/ folder at the project root.
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


def create_app(database: str | None = None) -> Flask:
    """Create, configure, and return the Flask application.

    Parameters
    ----------
    database:
        Optional path to the SQLite database file.  Defaults to
        ``config.DATABASE``.  Pass ``":memory:"`` in tests to get a
        fully isolated, throwaway database for every test session.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder=os.path.abspath(_STATIC_DIR),
    )

    db_path = database or config.DATABASE
    app.config["DATABASE"]   = db_path
    app.config["DEBUG"]      = config.DEBUG
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["TESTING"]    = database == ":memory:"

    import app.db as _db_module
    _db_module._cfg["database"] = db_path

    if db_path == ":memory:":
        if _db_module._cfg["conn"] is not None:
            try:
                _db_module._cfg["conn"].close()
            except sqlite3.Error as exc:
                _log.warning("Could not close in-memory connection: %s", exc)
        _db_module._cfg["conn"] = None

    from app.db import init_db
    init_db()

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from app.web import bp as web_bp
    app.register_blueprint(web_bp)

    # ── Custom error pages ───────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    return app
