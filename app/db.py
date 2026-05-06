"""Database connection helpers for the Bookshelf app.

``_cfg["database"]`` is set by the application factory (``create_app``) before
any request is served.  Tests override it to ``":memory:"`` so they never touch
the production database file.

Note on ``":memory:"``: SQLite creates a *new* empty database for every
``sqlite3.connect(":memory:")`` call, so ``_cfg["conn"]`` caches a single
persistent connection that is reused for the lifetime of the test session.
"""

import sqlite3
import config

_cfg: dict = {
    "database": config.DATABASE,
    "conn": None,
}


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection to the configured database.

    For file-based databases a new connection is opened on every call.
    For ``":memory:"`` the same connection is reused so all callers share
    the single in-memory database created by ``init_db()``.

    ``row_factory`` is set to ``sqlite3.Row`` so columns are accessible
    by name.  ``PARSE_DECLTYPES`` is intentionally omitted to avoid the
    Python 3.12 deprecation warning for the built-in TIMESTAMP converter;
    ``created_at`` is stored and returned as a plain ISO-8601 string.
    """
    if _cfg["database"] == ":memory:":
        if _cfg["conn"] is None:
            _cfg["conn"] = sqlite3.connect(
                ":memory:",
                check_same_thread=False,
            )
            _cfg["conn"].row_factory = sqlite3.Row
        return _cfg["conn"]

    conn = sqlite3.connect(_cfg["database"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all required tables if they do not already exist.

    Called once by ``create_app()`` at startup before any blueprint is
    registered or request is served.
    """
    from app.models import CREATE_BOOKS_TABLE

    conn = get_connection()
    conn.execute(CREATE_BOOKS_TABLE)
    conn.commit()


def reset_db() -> None:
    """Drop and recreate all tables.

    Used exclusively by the test suite to wipe state between tests when
    running against an in-memory database.
    """
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS books")
    conn.commit()
    init_db()
