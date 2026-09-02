"""Proves the db_session fixture never leaks state between tests.

Runs against the real `<worktree>_test` database via the `db_session`
fixture in conftest.py - not mocked. If these two tests disagree with each
other, the isolation strategy in `_docs/decisions.md#2` is broken, not this
file. Order matters: the first test must run before the second for the
assertion to mean anything, which is pytest's default (file order, no
randomization plugin configured).
"""

from sqlalchemy import text


def test_write_is_visible_within_the_same_session(db_session):
    db_session.execute(text("CREATE TABLE isolation_probe (id integer)"))
    db_session.execute(text("INSERT INTO isolation_probe VALUES (1)"))
    db_session.commit()  # commits a savepoint only, never the outer transaction

    rows = db_session.execute(text("SELECT id FROM isolation_probe")).fetchall()
    assert rows == [(1,)]


def test_previous_test_left_nothing_behind(db_session):
    # Postgres DDL is transactional: the CREATE TABLE above was rolled back
    # along with the row, so the table itself must not exist here.
    exists = db_session.execute(text("SELECT to_regclass('isolation_probe')")).scalar()
    assert exists is None
