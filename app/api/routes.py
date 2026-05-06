"""REST API routes for the books resource.

Endpoints
---------
GET    /api/books           – list all books (optional ?search= filter)
POST   /api/books           – create a new book
GET    /api/books/<id>      – retrieve a single book
PUT    /api/books/<id>      – update a book
DELETE /api/books/<id>      – delete a book

All responses use the envelope  {"data": ..., "message": ...}.
Swagger UI is auto-served at /api/docs.
"""

from flask import request
from flask_restx import Namespace, Resource, fields

from app.api import api
from app.db import get_connection
from app.models import (
    create_book,
    delete_book,
    get_all_books,
    get_book,
    update_book,
)

# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

ns = Namespace("books", description="Book CRUD operations")
api.add_namespace(ns, path="/books")

# ---------------------------------------------------------------------------
# RESTX model – drives Swagger schema + request body parsing
# ---------------------------------------------------------------------------

book_model = api.model(
    "Book",
    {
        "id": fields.Integer(readonly=True, description="Auto-assigned primary key"),
        "isbn": fields.String(description="ISBN (unique)"),
        "title": fields.String(required=True, description="Book title"),
        "author": fields.String(description="Author name"),
        "year": fields.Integer(description="Publication year"),
        "subject": fields.String(description="Subject / genre"),
        "cover_url": fields.String(description="URL of the cover image"),
        "page_count": fields.Integer(description="Number of pages"),
        "created_at": fields.String(readonly=True, description="Row creation timestamp"),
    },
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict safe for JSON serialisation.

    ``datetime`` values produced by ``sqlite3.PARSE_DECLTYPES`` on TIMESTAMP
    columns are converted to ISO-8601 strings so Flask-RESTX can serialise
    them without a custom JSON encoder.
    """
    if row is None:
        return None
    result = {}
    for key in row.keys():
        val = row[key]
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        result[key] = val
    return result


def _envelope(data, message: str = "OK") -> dict:
    """Wrap a response payload in the standard {data, message} envelope."""
    return {"data": data, "message": message}


def _search_books(query: str) -> list:
    """Return books whose title or author contains *query* (case-insensitive)."""
    pattern = f"%{query}%"
    sql = """
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ?
        ORDER BY created_at DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (pattern, pattern)).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@ns.route("/")
class BookList(Resource):
    """Handles the /api/books/ collection endpoint."""

    @ns.doc("list_books", params={"search": "Filter by title or author (optional)"})
    @ns.response(200, "Success")
    def get(self):
        """List all books, with an optional ?search= filter on title / author."""
        query = request.args.get("search", "").strip()
        if query:
            books = _search_books(query)
        else:
            books = [_row_to_dict(r) for r in get_all_books()]

        return _envelope(books), 200

    @ns.doc("create_book")
    @ns.expect(book_model, validate=False)
    @ns.response(201, "Book created")
    @ns.response(400, "Validation error")
    def post(self):
        """Create a new book.  *title* is required."""
        payload = request.get_json(silent=True) or {}

        title = (payload.get("title") or "").strip()
        if not title:
            return _envelope(None, "title is required"), 400

        new_id = create_book(
            title=title,
            author=payload.get("author"),
            year=payload.get("year"),
            subject=payload.get("subject"),
            isbn=payload.get("isbn"),
            cover_url=payload.get("cover_url"),
            page_count=payload.get("page_count"),
        )

        book = _row_to_dict(get_book(new_id))
        return _envelope(book, "Book created"), 201


@ns.route("/<int:book_id>")
@ns.param("book_id", "The book's primary key")
class Book(Resource):
    """Handles /api/books/<book_id> – single-resource operations."""

    @ns.doc("get_book")
    @ns.response(200, "Success")
    @ns.response(404, "Book not found")
    def get(self, book_id: int):
        """Retrieve a single book by its id."""
        row = get_book(book_id)
        if row is None:
            return _envelope(None, f"Book {book_id} not found"), 404

        return _envelope(_row_to_dict(row)), 200

    @ns.doc("update_book")
    @ns.expect(book_model, validate=False)
    @ns.response(200, "Book updated")
    @ns.response(400, "No valid fields supplied")
    @ns.response(404, "Book not found")
    def put(self, book_id: int):
        """Update one or more fields of an existing book."""
        if get_book(book_id) is None:
            return _envelope(None, f"Book {book_id} not found"), 404

        payload = request.get_json(silent=True) or {}
        allowed = {"isbn", "title", "author", "year", "subject", "cover_url", "page_count"}
        updates = {k: v for k, v in payload.items() if k in allowed}

        if not updates:
            return _envelope(None, "No valid fields supplied"), 400

        # title must not be set to an empty string
        if "title" in updates and not (updates["title"] or "").strip():
            return _envelope(None, "title must not be empty"), 400

        update_book(book_id, **updates)
        return _envelope(_row_to_dict(get_book(book_id)), "Book updated"), 200

    @ns.doc("delete_book")
    @ns.response(204, "Book deleted")
    @ns.response(404, "Book not found")
    def delete(self, book_id: int):
        """Delete a book by its id."""
        if not delete_book(book_id):
            return _envelope(None, f"Book {book_id} not found"), 404

        return "", 204
