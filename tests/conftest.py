"""Fixtures for tests that touch Postgres.

Isolation strategy - see `_docs/decisions.md#2`: one dedicated `<db>_test`
database per worktree, derived from `DATABASE_URL`, created and migrated to
head once per test session. Each test then runs inside a transaction bound
with `join_transaction_mode="create_savepoint"`: `session.commit()` inside a
test only commits a savepoint, and teardown rolls the outer transaction
back - including any `CREATE TABLE`, since Postgres DDL is transactional.
No test's writes are ever visible to another test, and this never touches
the worktree's real `DATABASE_URL`.

Tests that do not request `db_session` never open a database connection at
all - collecting the suite stays free even when Postgres is not up.
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

load_dotenv()


def _test_database_url():
    dev_url = make_url(os.environ["DATABASE_URL"])
    return dev_url.set(database=f"{dev_url.database}_test")


def _ensure_database(url) -> None:
    """Create the database `url` points at, unless it already exists."""
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).first()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    url = _test_database_url()
    _ensure_database(url)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(url))
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Session:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
