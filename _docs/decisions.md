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

## 3. Fase 1 corpus size: 21 videos, not 30 - authorized reduction, not a bug fix

QA FAILed Issue #1 correctly: `corpus/zenn0009/manifesto.csv` did not exist
(0 rows vs. the 30 the issue's gate requires), because `collect()` only
writes the manifest after every selected video succeeds, and video 22/30
hit a real YouTube per-IP rate limit (`IpBlocked`) that did not clear during
the run - exactly the risk `_docs/blueprint.md` names ("~100-200 req/hora
por IP"). 21 real raw+clean transcript pairs are committed and correct.

The project owner authorized proceeding with the 21 videos actually
collected instead of blocking on all 30. This is a scope call, not
something QA or the Engineer may decide alone.

What changes: `collect()` writes `manifesto.csv` for however many videos it
successfully fetched, not only when all 30 succeed. The Fase 1 gate for
*this* corpus is "manifesto has a row per successfully collected video, none
below 60% of expected word count" - the fixed "30" in
`_docs/plano_implementacao.md` and in Issue #1's acceptance criteria is
superseded by this entry for `@Zenn0009`.

Consequence flagged, not solved here: Fase 4/5 of `_docs/plano_implementacao.md`
assume a 30-video corpus (5 gold + 25 batch-annotated). Whoever grooms the
Fase 4 issue re-derives that split from the actual corpus size at the time
(`corpus/zenn0009/manifesto.csv` row count), not from the plan's literal
numbers. If the IP block clears later and someone reruns collection to grow
the corpus toward 30, that is additive and fine; nothing here forbids it.
