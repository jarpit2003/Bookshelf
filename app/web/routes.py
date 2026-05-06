"""Web (server-rendered) routes for the Bookshelf app.

Routes
------
GET  /                      – book list, supports ?search= filter
GET  /books/<id>            – book detail page
POST /books/<id>/edit       – update a book, redirect to detail
POST /books/<id>/delete     – delete a book, redirect to /
GET  /fetch                 – pull results from Open Library (?topic=), redirect to /
POST /add                   – create a new book from the web form, redirect to detail
"""

from flask import abort, flash, redirect, render_template, request, url_for

from app.db import get_connection
from app.models import create_book, delete_book, get_all_books, get_book, update_book
from app.web import bp

# ---------------------------------------------------------------------------
# Internal DB helpers
# ---------------------------------------------------------------------------

_SEARCH_SQL = """
    SELECT * FROM books
    WHERE title LIKE ? OR author LIKE ?
    ORDER BY created_at DESC
"""

_INSERT_OR_IGNORE_SQL = """
    INSERT OR IGNORE INTO books
        (isbn, title, author, year, subject, cover_url, page_count)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""


def _search_books(query: str) -> list:
    """Return books whose title or author contains *query* (case-insensitive)."""
    pattern = f"%{query}%"
    with get_connection() as conn:
        return conn.execute(_SEARCH_SQL, (pattern, pattern)).fetchall()


def _insert_books(books: list[dict]) -> int:
    """Bulk-insert parsed book dicts, skipping ISBN duplicates.

    Returns the number of rows actually inserted.
    """
    inserted = 0
    with get_connection() as conn:
        for book in books:
            cursor = conn.execute(
                _INSERT_OR_IGNORE_SQL,
                (
                    book["isbn"],
                    book["title"],
                    book["author"],
                    book["year"],
                    book["subject"],
                    book["cover_url"],
                    book["page_count"],
                ),
            )
            inserted += cursor.rowcount
        conn.commit()
    return inserted


def _int_or_none(value: str) -> int | None:
    """Convert a string to int, returning None if blank or non-numeric."""
    value = (value or "").strip()
    try:
        return int(value) if value else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@bp.route("/")
def index():
    """Render the book list page.

    Supports an optional ``?search=`` query parameter that filters results
    by title or author (case-insensitive LIKE match).
    """
    query = request.args.get("search", "").strip()
    books = _search_books(query) if query else get_all_books()
    return render_template("index.html", books=books, search=query)


@bp.route("/books/<int:book_id>")
def detail(book_id: int):
    """Render the detail page for a single book.  Returns 404 if not found."""
    book = get_book(book_id)
    if book is None:
        abort(404)
    return render_template("detail.html", book=book)


@bp.route("/add", methods=["POST"])
def add():
    """Create a new book from the web form and redirect to its detail page."""
    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("web.index"))

    new_id = create_book(
        title=title,
        author=request.form.get("author", "").strip() or None,
        year=_int_or_none(request.form.get("year")),
        subject=request.form.get("subject", "").strip() or None,
        isbn=request.form.get("isbn", "").strip() or None,
        cover_url=request.form.get("cover_url", "").strip() or None,
        page_count=_int_or_none(request.form.get("page_count")),
    )

    flash(f'"{title}" added to your library.', "success")
    return redirect(url_for("web.detail", book_id=new_id))


@bp.route("/books/<int:book_id>/edit", methods=["POST"])
def edit(book_id: int):
    """Update a book from HTML form data and redirect to its detail page."""
    if get_book(book_id) is None:
        abort(404)

    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("web.detail", book_id=book_id))

    update_book(
        book_id,
        isbn=request.form.get("isbn", "").strip() or None,
        title=title,
        author=request.form.get("author", "").strip() or None,
        year=_int_or_none(request.form.get("year")),
        subject=request.form.get("subject", "").strip() or None,
        cover_url=request.form.get("cover_url", "").strip() or None,
        page_count=_int_or_none(request.form.get("page_count")),
    )

    flash("Book updated successfully.", "success")
    return redirect(url_for("web.detail", book_id=book_id))


@bp.route("/books/<int:book_id>/delete", methods=["POST"])
def delete(book_id: int):
    """Delete a book and redirect to the index page."""
    if not delete_book(book_id):
        abort(404)

    flash("Book deleted.", "info")
    return redirect(url_for("web.index"))


@bp.route("/fetch")
def fetch():
    """Fetch books from Open Library and insert new ones into the DB.

    Accepts an optional ``?topic=`` query parameter (defaults to
    ``"python programming"``).  Uses ``FetchError`` instead of
    ``SystemExit`` so network failures surface as flash messages rather
    than crashing the server.
    """
    from seed import FetchError, fetch_books, parse_book

    topic = request.args.get("topic", "python programming").strip() or "python programming"

    try:
        docs = fetch_books(topic)
    except FetchError as exc:
        flash(f"Fetch failed: {exc}", "danger")
        return redirect(url_for("web.index"))

    books    = [b for doc in docs if (b := parse_book(doc)) is not None]
    inserted = _insert_books(books)

    flash(f'Fetched {inserted} new book(s) for "{topic}".', "success")
    return redirect(url_for("web.index"))
