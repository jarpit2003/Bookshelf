"""models.py — SQLite schema definition and CRUD helper functions.

All database access goes through ``app.db.get_connection()``.
No ORM is used; all SQL is explicit and parameterised.
"""

from app.db import get_connection

CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn       TEXT UNIQUE,
    title      TEXT NOT NULL,
    author     TEXT,
    year       INTEGER,
    subject    TEXT,
    cover_url  TEXT,
    page_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_all_books() -> list:
    """Return every row in the books table as a list of sqlite3.Row objects."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM books ORDER BY created_at DESC").fetchall()


def get_book(book_id: int):
    """Return a single book row by primary key, or None if not found."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        ).fetchone()


def create_book(
    title: str,
    author: str = None,
    year: int = None,
    subject: str = None,
    isbn: str = None,
    cover_url: str = None,
    page_count: int = None,
) -> int:
    """Insert a new book and return its auto-assigned id."""
    sql = """
        INSERT INTO books (isbn, title, author, year, subject, cover_url, page_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (isbn, title, author, year, subject, cover_url, page_count))
        conn.commit()
        return cursor.lastrowid


def update_book(book_id: int, **fields) -> bool:
    """Update the given fields of a book row.

    Accepts any subset of: isbn, title, author, year, subject, cover_url, page_count.
    Returns True if a row was updated, False if the id was not found.
    """
    allowed = {"isbn", "title", "author", "year", "subject", "cover_url", "page_count"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [book_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE books SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_book(book_id: int) -> bool:
    """Delete a book by primary key.

    Returns True if a row was deleted, False if the id was not found.
    """
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        return cursor.rowcount > 0
