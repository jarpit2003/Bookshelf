# BookShelf

A full-stack Flask web application that fetches books from the
[Open Library API](https://openlibrary.org/developers/api), stores them in
SQLite, and exposes them through a Bootstrap 5 UI and a self-documenting
REST API (Swagger UI included).

---

## Quick Start (copy-paste)

```bash
# 1. Clone
git clone <your-repo-url>
cd bookshelf

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database (fetches 20 books from Open Library)
python seed.py

# 5. Run
python run.py
```

Open your browser:

| URL | What you see |
|-----|-------------|
| http://127.0.0.1:5000 | Book list + detail UI |
| http://127.0.0.1:5000/api/docs | Swagger UI (all endpoints) |
| http://127.0.0.1:5000/api/books/ | Raw JSON API |

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Web framework | Flask 3.1.3 |
| REST API | Flask-RESTX 1.3.0 — Swagger at `/api/docs` |
| Database | SQLite via built-in `sqlite3` (no ORM) |
| Frontend | Jinja2 + Bootstrap 5.3.3 CDN + Bootstrap Icons |
| HTTP client | `requests` 2.32.4 |
| Tests | pytest 8.3.5 — 23 tests, in-memory SQLite |

---

## Project Structure

```
bookshelf/
├── app/
│   ├── __init__.py        # application factory
│   ├── db.py              # sqlite3 connection helpers
│   ├── models.py          # schema + CRUD functions
│   ├── api/
│   │   ├── __init__.py    # Flask-RESTX Api object
│   │   └── routes.py      # BookList + Book resources
│   ├── web/
│   │   ├── __init__.py    # web blueprint
│   │   └── routes.py      # index, detail, add, edit, delete, fetch
│   └── templates/
│       ├── base.html      # navbar, modals, flash messages
│       ├── index.html     # two-column list-detail layout
│       ├── detail.html    # standalone book page
│       ├── 404.html
│       └── 500.html
├── static/style.css
├── tests/
│   ├── conftest.py
│   └── test_crud.py       # 23 CRUD tests (in-memory DB)
├── config.py
├── seed.py                # Open Library fetcher
├── run.py                 # dev server
├── wsgi.py                # PythonAnywhere entry point
├── requirements.txt
└── DEPLOYMENT.md          # step-by-step PythonAnywhere guide
```

---

## Database Schema

```sql
CREATE TABLE books (
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
```

---

## REST API Endpoints

All responses use `{"data": ..., "message": ...}`.

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/books/` | List all books (`?search=` supported) | 200 |
| POST | `/api/books/` | Create a book (`title` required) | 201 |
| GET | `/api/books/<id>` | Get one book | 200 / 404 |
| PUT | `/api/books/<id>` | Update fields | 200 / 400 / 404 |
| DELETE | `/api/books/<id>` | Delete a book | 204 / 404 |

### Example — create

```bash
curl -X POST http://127.0.0.1:5000/api/books/ \
     -H "Content-Type: application/json" \
     -d '{"title": "Fluent Python", "author": "Luciano Ramalho", "year": 2022}'
```

### Example — search

```bash
curl "http://127.0.0.1:5000/api/books/?search=fluent"
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected: **23 passed**.

---

## Seed with a custom topic

```bash
python seed.py "machine learning"
python seed.py "data science"
```

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full PythonAnywhere step-by-step instructions.

Live app: `https://<yourpawid>.pythonanywhere.com`
