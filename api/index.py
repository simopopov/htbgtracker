"""Vercel serverless entrypoint.

init_db() runs at import (i.e. on every cold start) so the schema exists even
if the platform skips ASGI lifespan events; create_all is idempotent.
"""
from app.db import init_db
from app.main import app  # noqa: F401  — Vercel serves this ASGI app

init_db()
