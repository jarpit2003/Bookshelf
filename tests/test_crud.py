"""Unit tests for the Bookshelf REST API CRUD operations.

Each test function gets a brand-new in-memory SQLite database via the
``client`` fixture, so tests are fully isolated and never touch the
production ``bookshelf.db`` file.

Run with:
    cd bookshelf
    pytest tests/ -v
"""

import json
import pytest

from app import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Create a Flask app wired to a fresh in-memory SQLite database.

    ``":memory:"`` is passed to ``create_app`` so ``db._DATABASE`` is
    overwritten before ``init_db()`` runs.  A new in-memory DB is created
    for every test function because the fixture scope defaults to
    ``"function"``.
    """
    flask_app = create_app(database=":memory:")
    flask_app.config["TESTING"] = True
    yield flask_app
    # Nothing to tear down: in-memory DB is discarded when the connection
    # closes, which happens at the end of each test function.


@pytest.fixture()
def client(app):
    """Return a Flask test client bound to the isolated test app."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "year": 2008,
    "subject": "Software Engineering",
    "isbn": "9780132350884",
    "cover_url": "https://covers.openlibrary.org/b/id/8739161-M.jpg",
    "page_count": 431,
}


def _post_book(client, payload: dict | None = None):
    """POST a book to /api/books/ and return the response."""
    return client.post(
        "/api/books/",
        data=json.dumps(payload or _VALID_PAYLOAD),
        content_type="application/json",
    )


def _created_id(response) -> int:
    """Extract the ``id`` from a 201 create response."""
    return response.get_json()["data"]["id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateBook:
    """POST /api/books/ — create a new book."""

    def test_returns_201(self, client):
        """Valid payload must return HTTP 201 Created."""
        res = _post_book(client)
        assert res.status_code == 201

    def test_response_envelope(self, client):
        """Response body must use the {data, message} envelope."""
        body = _post_book(client).get_json()
        assert "data" in body
        assert "message" in body

    def test_returned_fields_match_input(self, client):
        """The ``data`` object must echo back every submitted field."""
        data = _post_book(client).get_json()["data"]
        assert data["title"]   == _VALID_PAYLOAD["title"]
        assert data["author"]  == _VALID_PAYLOAD["author"]
        assert data["year"]    == _VALID_PAYLOAD["year"]
        assert data["isbn"]    == _VALID_PAYLOAD["isbn"]

    def test_auto_assigns_id(self, client):
        """A new book must receive a positive integer primary key."""
        data = _post_book(client).get_json()["data"]
        assert isinstance(data["id"], int)
        assert data["id"] > 0


class TestGetAllBooks:
    """GET /api/books/ — list all books."""

    def test_empty_db_returns_200(self, client):
        """An empty database must still return 200 with an empty list."""
        res = client.get("/api/books/")
        assert res.status_code == 200
        assert res.get_json()["data"] == []

    def test_returns_inserted_books(self, client):
        """Books added via POST must appear in the GET list."""
        _post_book(client)
        res = client.get("/api/books/")
        assert res.status_code == 200
        assert len(res.get_json()["data"]) == 1

    def test_search_filter_matches_title(self, client):
        """?search= must filter by title (case-insensitive)."""
        _post_book(client)
        res = client.get("/api/books/?search=clean")
        assert res.status_code == 200
        assert len(res.get_json()["data"]) >= 1

    def test_search_filter_no_match_returns_empty(self, client):
        """?search= with no match must return an empty list, not 404."""
        _post_book(client)
        res = client.get("/api/books/?search=zzznomatch")
        assert res.status_code == 200
        assert res.get_json()["data"] == []


class TestGetSingleBook:
    """GET /api/books/<id> — retrieve one book."""

    def test_returns_200_and_correct_data(self, client):
        """Fetching a known id must return 200 and the correct title."""
        book_id = _created_id(_post_book(client))
        res = client.get(f"/api/books/{book_id}")
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["id"]    == book_id
        assert data["title"] == _VALID_PAYLOAD["title"]

    def test_all_fields_present(self, client):
        """The response must include every column defined in the schema."""
        book_id = _created_id(_post_book(client))
        data = client.get(f"/api/books/{book_id}").get_json()["data"]
        for field in ("id", "isbn", "title", "author", "year",
                      "subject", "cover_url", "page_count", "created_at"):
            assert field in data, f"Missing field: {field}"


class TestUpdateBook:
    """PUT /api/books/<id> — update a book."""

    def test_returns_200(self, client):
        """A valid update must return HTTP 200."""
        book_id = _created_id(_post_book(client))
        res = client.put(
            f"/api/books/{book_id}",
            data=json.dumps({"title": "The Clean Coder"}),
            content_type="application/json",
        )
        assert res.status_code == 200

    def test_data_is_changed(self, client):
        """The updated field must be reflected in the response body."""
        book_id = _created_id(_post_book(client))
        client.put(
            f"/api/books/{book_id}",
            data=json.dumps({"title": "The Clean Coder", "year": 2011}),
            content_type="application/json",
        )
        data = client.get(f"/api/books/{book_id}").get_json()["data"]
        assert data["title"] == "The Clean Coder"
        assert data["year"]  == 2011

    def test_unrelated_fields_unchanged(self, client):
        """Fields not included in the PUT payload must keep their original values."""
        book_id = _created_id(_post_book(client))
        client.put(
            f"/api/books/{book_id}",
            data=json.dumps({"year": 2011}),
            content_type="application/json",
        )
        data = client.get(f"/api/books/{book_id}").get_json()["data"]
        assert data["author"] == _VALID_PAYLOAD["author"]

    def test_empty_payload_returns_400(self, client):
        """A PUT with no recognised fields must return 400."""
        book_id = _created_id(_post_book(client))
        res = client.put(
            f"/api/books/{book_id}",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_blank_title_returns_400(self, client):
        """Setting title to an empty string must return 400."""
        book_id = _created_id(_post_book(client))
        res = client.put(
            f"/api/books/{book_id}",
            data=json.dumps({"title": "   "}),
            content_type="application/json",
        )
        assert res.status_code == 400


class TestDeleteBook:
    """DELETE /api/books/<id> — delete a book."""

    def test_returns_204(self, client):
        """Deleting an existing book must return HTTP 204 No Content."""
        book_id = _created_id(_post_book(client))
        res = client.delete(f"/api/books/{book_id}")
        assert res.status_code == 204

    def test_book_no_longer_retrievable(self, client):
        """After deletion, GET on the same id must return 404."""
        book_id = _created_id(_post_book(client))
        client.delete(f"/api/books/{book_id}")
        res = client.get(f"/api/books/{book_id}")
        assert res.status_code == 404

    def test_response_body_is_empty(self, client):
        """HTTP 204 must have no response body."""
        book_id = _created_id(_post_book(client))
        res = client.delete(f"/api/books/{book_id}")
        assert res.data == b""


class TestGetNonexistentBook:
    """GET /api/books/99999 — book that does not exist."""

    def test_returns_404(self, client):
        """Requesting an unknown id must return HTTP 404."""
        res = client.get("/api/books/99999")
        assert res.status_code == 404

    def test_error_message_in_envelope(self, client):
        """The 404 body must still use the {data, message} envelope."""
        body = client.get("/api/books/99999").get_json()
        assert "message" in body
        assert body["data"] is None


class TestCreateBookMissingTitle:
    """POST /api/books/ without a title — validation error."""

    def test_returns_400(self, client):
        """A POST with no title field must return HTTP 400."""
        res = _post_book(client, {"author": "Someone"})
        assert res.status_code == 400

    def test_empty_string_title_returns_400(self, client):
        """A POST with title='' (whitespace) must also return 400."""
        res = _post_book(client, {"title": "   ", "author": "Someone"})
        assert res.status_code == 400

    def test_error_message_present(self, client):
        """The 400 response must include a human-readable message."""
        body = _post_book(client, {"author": "Someone"}).get_json()
        assert "message" in body
        assert body["message"]  # non-empty string
