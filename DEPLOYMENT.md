# Deploying BookShelf on PythonAnywhere (Free Tier)

> Replace **`myusername`** with your actual PythonAnywhere username
> everywhere it appears below.

---

## Prerequisites

- A free account at https://www.pythonanywhere.com
- Your project pushed to a public GitHub repository  
  *(or you can upload a zip via the Files tab)*

---

## Step 1 — Open a Bash Console

1. Log in to PythonAnywhere.
2. Click the **Consoles** tab in the top navigation bar.
3. Under *Start a new console*, click **Bash**.

A terminal session opens in your browser. All commands below are run here.

---

## Step 2 — Clone the Repository

```bash
git clone https://github.com/<your-github-username>/bookshelf.git ~/bookshelf
```

Verify the files are present:

```bash
ls ~/bookshelf
```

You should see `app/`, `config.py`, `run.py`, `seed.py`, `wsgi.py`, etc.

---

## Step 3 — Create a Virtual Environment with Python 3.10

```bash
cd ~/bookshelf
python3.10 -m venv venv
source venv/bin/activate
```

Your prompt will change to `(venv) ...` confirming the environment is active.

---

## Step 4 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Expected output ends with something like:
```
Successfully installed flask-2.3.3 flask-restx-1.1.0 ...
```

---

## Step 5 — Seed the Database

> **Free-tier note:** PythonAnywhere free accounts **cannot make outbound
> HTTP requests** to external sites (including Open Library).  
> Choose **one** of the options below.

### Option A — Upload a pre-seeded database (recommended for free tier)

Run this on your **local machine** first:

```bash
cd bookshelf
python seed.py
```

Then upload the generated `bookshelf.db` file via the PythonAnywhere
**Files** tab to `/home/myusername/bookshelf/bookshelf.db`.

### Option B — Paid / whitelisted account

If your account can make outbound requests, run directly in the Bash console:

```bash
cd ~/bookshelf
source venv/bin/activate
python seed.py
```

---

## Step 6 — Configure the WSGI File

### 6a — Create the Web App

1. Click the **Web** tab in the top navigation bar.
2. Click **Add a new web app** → **Next**.
3. Select **Manual configuration** (not "Flask").
4. Select **Python 3.10** → **Next**.
5. PythonAnywhere creates a default WSGI file and shows you its path,
   something like:  
   `/var/www/myusername_pythonanywhere_com_wsgi.py`

### 6b — Replace the WSGI File Contents

1. Click the WSGI file path link shown on the Web tab — it opens in the
   online editor.
2. **Select all** existing content and **delete it**.
3. Paste the following (the `wsgi.py` in your repo already contains this):

```python
import sys
import os

PROJECT_ROOT = "/home/myusername/bookshelf"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("SECRET_KEY", "replace-with-a-long-random-secret")

import config as _config
_config.DEBUG = False

from app import create_app

application = create_app()
application.debug = False
```

4. Replace `myusername` with your actual username.
5. Replace `replace-with-a-long-random-secret` with a real secret key
   (generate one with `python -c "import secrets; print(secrets.token_hex(32))"`).
6. Click **Save**.

### 6c — Set the Source Code and Virtualenv Paths

Still on the **Web** tab, scroll down and fill in:

| Field | Value |
|-------|-------|
| **Source code** | `/home/myusername/bookshelf` |
| **Working directory** | `/home/myusername/bookshelf` |
| **Virtualenv** | `/home/myusername/bookshelf/venv` |

---

## Step 7 — Map the Static Files

On the **Web** tab, scroll to the **Static files** section and add one entry:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/myusername/bookshelf/static` |

This tells PythonAnywhere's nginx to serve CSS/JS directly without going
through Flask, which is faster and required for the Bootstrap stylesheet
and `style.css` to load correctly.

---

## Step 8 — Reload the Web App

At the top of the **Web** tab, click the green **Reload** button:

```
● Reload myusername.pythonanywhere.com
```

Wait a few seconds, then visit:

```
https://myusername.pythonanywhere.com
```

The BookShelf UI should load with the seeded books listed on the left panel.

---

## Verifying the Deployment

| URL | Expected result |
|-----|-----------------|
| `https://myusername.pythonanywhere.com/` | Book list page |
| `https://myusername.pythonanywhere.com/api/docs` | Swagger UI |
| `https://myusername.pythonanywhere.com/api/books/` | JSON list of books |

---

## Updating the App After Code Changes

```bash
# In a PythonAnywhere Bash console
cd ~/bookshelf
source venv/bin/activate
git pull origin main
```

Then click **Reload** on the Web tab.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **502 Bad Gateway** | Check the error log linked on the Web tab; usually a missing dependency or import error |
| **Static files return 404** | Confirm the static files URL/directory mapping in Step 7 is saved |
| **`ModuleNotFoundError: No module named 'app'`** | Confirm `PROJECT_ROOT` in the WSGI file matches the actual clone path |
| **`OperationalError: no such table: books`** | The database was not seeded; follow Step 5 |
| **Books page is empty** | Free-tier outbound HTTP is blocked; upload a pre-seeded `bookshelf.db` (Option A in Step 5) |
| **`SECRET_KEY` warning in logs** | Set a real secret key in the WSGI file (Step 6b) |
