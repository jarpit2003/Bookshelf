"""seed.py – Populate the books table from the Open Library Search API.

Usage
-----
    python seed.py                  # default query: python programming
    python seed.py "data science"   # custom search query

The script is safe to re-run; duplicate ISBNs are silently skipped thanks
to INSERT OR IGNORE and the UNIQUE constraint on the isbn column.
"""

import sys
import uuid

import requests

from app.db import get_connection, init_db

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEARCH_URL   = "https://openlibrary.org/search.json"
COVER_URL    = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
DEFAULT_QUERY = "python programming"
LIMIT        = 20

INSERT_SQL = """
    INSERT OR IGNORE INTO books (isbn, title, author, year, subject, cover_url, page_count)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class FetchError(RuntimeError):
    """Raised when the Open Library request fails or returns bad data."""


# ---------------------------------------------------------------------------
# Network layer
# ---------------------------------------------------------------------------


def fetch_books(query: str, limit: int = LIMIT) -> list[dict]:
    """Fetch raw book docs from the Open Library Search API.

    Parameters
    ----------
    query:
        Free-text search string forwarded to Open Library.
    limit:
        Maximum number of results to request.

    Returns
    -------
    list[dict]
        The ``docs`` list from the API response (may be empty).

    Raises
    ------
    FetchError
        On any network failure, HTTP error, or malformed JSON response.
    """
    url = SEARCH_URL
    params = {"q": query, "limit": limit}

    print(f"Fetching: {url}?q={query}&limit={limit}")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.HTTPError as exc:
        raise FetchError(f"HTTP {exc.response.status_code} from Open Library: {exc}") from exc
    except requests.exceptions.ConnectionError as exc:
        raise FetchError(f"Network error contacting Open Library: {exc}") from exc
    except requests.exceptions.Timeout as exc:
        raise FetchError("Open Library request timed out.") from exc
    except requests.exceptions.JSONDecodeError as exc:
        raise FetchError(f"Malformed JSON from Open Library: {exc}") from exc

    docs = payload.get("docs")
    if not isinstance(docs, list):
        raise FetchError("Unexpected API response: 'docs' key missing or not a list.")

    return docs


# ---------------------------------------------------------------------------
# Parsing layer
# ---------------------------------------------------------------------------


def _fallback_isbn() -> str:
    """Generate a unique placeholder ISBN when the API provides none."""
    return f"UNKNOWN-{uuid.uuid4().hex[:8].upper()}"


def parse_book(doc: dict) -> dict | None:
    """Extract and normalise fields from a single Open Library doc.

    Parameters
    ----------
    doc:
        A single element from the ``docs`` list returned by the API.

    Returns
    -------
    dict | None
        Normalised book dict ready for DB insertion, or ``None`` if the
        doc lacks a title (the only NOT NULL column without a default).
    """
    title = (doc.get("title") or "").strip()
    if not title:
        return None

    isbn_list = doc.get("isbn") or []
    isbn = isbn_list[0] if isbn_list else _fallback_isbn()

    authors = doc.get("author_name") or []
    author = ", ".join(authors) if authors else None

    year = doc.get("first_publish_year") or None

    subjects = doc.get("subject") or []
    subject = subjects[0] if subjects else None

    cover_id = doc.get("cover_i")
    cover_url = COVER_URL.format(cover_id=cover_id) if cover_id else ""

    page_count = doc.get("number_of_pages_median") or 0

    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "year": year,
        "subject": subject,
        "cover_url": cover_url,
        "page_count": page_count,
    }


# ---------------------------------------------------------------------------
# DB layer
# ---------------------------------------------------------------------------


def seed(query: str = DEFAULT_QUERY) -> int:
    """Fetch books from Open Library and insert them into the local DB.

    Parameters
    ----------
    query:
        Search term forwarded to the Open Library API.

    Returns
    -------
    int
        Number of new rows inserted (duplicates are skipped).

    Raises
    ------
    FetchError
        Propagated from ``fetch_books`` on network / parse failures.
    """
    init_db()

    docs  = fetch_books(query)
    books = [b for doc in docs if (b := parse_book(doc)) is not None]

    if not books:
        print("No valid books found in the API response. Nothing seeded.")
        return 0

    inserted = 0
    with get_connection() as conn:
        for book in books:
            cursor = conn.execute(
                INSERT_SQL,
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

    skipped = len(books) - inserted
    print(f"Seeded {inserted} books successfully.")
    if skipped:
        print(f"Skipped {skipped} duplicate(s) already in the database.")

    return inserted


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        search_query = " ".join(sys.argv[1:]) or DEFAULT_QUERY
        seed(search_query)
    except FetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
