"""Alembic migration environment.

Uses ``DATABASE_URL`` (via ``paper_reviewer.db``) and ORM metadata from
``paper_reviewer.models``.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from paper_reviewer.db.engine import get_database_url
from paper_reviewer.models import Base

# Import mapped modules so their tables are registered on Base.metadata.
from paper_reviewer.models import paper as _paper  # noqa: F401
from paper_reviewer.models import paper_brief as _paper_brief  # noqa: F401
from paper_reviewer.models.topic_scope import reference as _reference  # noqa: F401
from paper_reviewer.models.topic_scope import topic_analysis as _topic_analysis  # noqa: F401
from paper_reviewer.models.topic_scope import topic_brief as _topic_brief  # noqa: F401
from paper_reviewer.models.topic_scope import topic_scope as _topic_scope  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure_sqlalchemy_url() -> None:
    config.set_main_option("sqlalchemy.url", get_database_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script output only)."""
    _configure_sqlalchemy_url()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    _configure_sqlalchemy_url()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
