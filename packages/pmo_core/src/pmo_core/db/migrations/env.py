"""Alembic environment: runs migrations online against `sqlalchemy.url`."""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, pool, text


def run_migrations_online() -> None:
    """Run migrations with the version table in the `app` schema."""
    url = context.config.get_main_option("sqlalchemy.url")
    assert url is not None
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
        connection.commit()
        context.configure(connection=connection, version_table_schema="app")
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
