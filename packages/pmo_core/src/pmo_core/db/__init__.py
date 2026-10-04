"""Database access: engine/session factory and Alembic migrations."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def make_engine(database_url: str) -> Engine:
    """Create a pooled engine with pre-ping so dropped connections recover."""
    return create_engine(database_url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory bound to the engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def run_migrations(database_url: str) -> None:
    """Upgrade the database to the latest Alembic revision."""
    alembic_config = Config()
    alembic_config.set_main_option("script_location", str(MIGRATIONS_DIR))
    alembic_config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(alembic_config, "head")


def ping(engine: Engine) -> None:
    """Raise if the database is unreachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
