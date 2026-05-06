import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE  = os.path.join(BASE_DIR, "bookshelf.db")
DEBUG     = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

# Testing overrides
TESTING_DATABASE = os.path.join(BASE_DIR, "test_bookshelf.db")
