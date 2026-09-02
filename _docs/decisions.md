# Decisions

Calls made while grooming the backlog - technical and scope decisions, not
the three product decisions in `DECISOES.md`. Settled here so issues stop
re-litigating them.

Where this file and `_docs/plano_implementacao.md` or `_docs/blueprint.md`
disagree, this file wins.

## 1. Postgres joins the stack, alongside file - not instead of it

`src/db.py` (SQLAlchemy) and `migrations/` (Alembic) are real infrastructure
now: `compose.yaml` runs a `db` service, and the squad's worktree isolation
(`_docs/process.md`) uses one database per worktree, `roteiros_wt<issue>`,
the same pattern `retroloop` uses.

This does not reopen `_docs/blueprint.md`'s "Por que arquivo em vez de
banco". `schema/ontologia.v1.json`, `codebook.md`, and
`perfis/<canal>.perfil.json` stay versioned files - they are read by humans,
diffed in review, and frozen per phase on purpose. What moves to Postgres is
whichever operational, queryable pipeline state a future issue's engineer
decides belongs there (corpus manifest, per-block annotations, agreement
runs, generation runs) - no table is defined yet, because no issue past
Fase 0 has been groomed.

Why: the squad process this project adopted (`_docs/process.md`) is ported
from `retroloop`, and its parallel-worktree QA/Engineer isolation depends on
each worktree owning a real, disposable resource a suite can write to
without colliding with another agent's run. A file-only design achieves the
same isolation only by convention (no two issues in a wave touch the same
path) - which still holds for `corpus/`/`gold/`/`perfis/`/`schema/` - but a
database gives that isolation for free for anything relational, the same way
it does for `retroloop`.

Open, deliberately: which entities actually live in a table. That is for
the first issue that adds a database model to decide and log here, not for
this scaffolding pass. Test isolation strategy is resolved - see item 2
below.

## 2. Test isolation: dedicated `_test` database, transaction-per-test rollback

`tests/conftest.py` derives `<db>_test` from `DATABASE_URL` (so a worktree's
own `roteiros_wt<issue>` gets its own `roteiros_wt<issue>_test`), creates it
if missing, and migrates it to head once per pytest session
(`db_engine` fixture). Each test that needs the database requests
`db_session`, which opens a connection, begins a transaction, and binds the
`Session` with `join_transaction_mode="create_savepoint"` - `commit()`
inside a test only commits a savepoint, and teardown rolls the outer
transaction back. Postgres DDL is transactional, so even a `CREATE TABLE`
inside a test vanishes with it. `tests/test_db_isolation.py` proves this
against a real database, not mocks.

Why: this is the documented SQLAlchemy 2.0 pattern for test isolation
("Joining a Session into an External Transaction"), and it is faster than
recreating the schema per test while giving every test the same guarantee
`pytest-django` gives retroloop for free - no test's writes are visible to
another test, or to the worktree's real `DATABASE_URL`.

Tests that never request `db_session` open no database connection at all,
so collecting the suite - and CI's `TEST_COUNTS` gate - never needs
Postgres up.
