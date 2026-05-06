from flask import Blueprint
from flask_restx import Api

bp = Blueprint("api", __name__)

api = Api(
    bp,
    title="Bookshelf API",
    version="1.0",
    description="CRUD API for the Bookshelf app.",
    doc="/docs",          # reachable at /api/docs via the blueprint prefix
)

from app.api import routes  # noqa: E402, F401
