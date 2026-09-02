"""Engine and declarative base for the Postgres-backed pipeline state.

DATABASE_URL is a real environment variable in production and in CI, and
read from `.env` in development - the same rule AGENTS.md states for every
other setting. `load_dotenv()` never overrides a name already set in the
process environment, so a real `DATABASE_URL` (a worktree's own, or CI's)
always wins over whatever `.env` says - by design, not by accident.
`_docs/decisions.md` explains what lives in Postgres versus what stays a
versioned file under corpus/, gold/, perfis/ and schema/.

Alembic (migrations/env.py) imports Base.metadata from this module for
autogenerate. No table is defined here yet - Fase 0's three decisions in
DECISOES.md are still open, and no phase past Fase 0 has been groomed.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

load_dotenv()


class Base(DeclarativeBase):
    pass


def get_engine():
    url = os.environ["DATABASE_URL"]
    return create_engine(url)


def get_session() -> Session:
    return Session(get_engine())
