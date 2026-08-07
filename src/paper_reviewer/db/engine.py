"""SQLAlchemy engine helpers."""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine.url import make_url


def get_database_url() -> str:
    """Return ``DATABASE_URL`` with the psycopg3 SQLAlchemy driver when needed.

    Compose and docs use the standard ``postgresql://`` scheme. SQLAlchemy 2
    needs ``postgresql+psycopg://`` to load psycopg 3.
    """
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        raise RuntimeError("DATABASE_URL is not set")

    url = make_url(raw)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return url.render_as_string(hide_password=False)


def create_db_engine(*, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine from ``DATABASE_URL``."""
    return create_engine(get_database_url(), echo=echo, pool_pre_ping=True)
