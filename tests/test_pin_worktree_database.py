"""Tests for `scripts/pin_worktree_database.py`.

Everything here runs entirely inside `tmp_path`-managed temp directories
standing in for a worktree and its `.venv` site-packages - never the real
test-runner's own `.venv`, checkout, or site-packages. No live Postgres,
no `db_session` fixture: this only exercises `DATABASE_URL` env-var
precedence and file generation via subprocesses.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "pin_worktree_database.py"

AMBIENT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5433/roteiros_dev_shell"


def _run_pin_script(project_root: Path, site_packages_dir: Path) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--project-root",
            str(project_root),
            "--site-packages-dir",
            str(site_packages_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result


def _probe_database_url(site_packages_dir: Path, ambient_value: str) -> str:
    """Spawn a fresh Python subprocess with `site_packages_dir` injected
    ahead of the real site-packages via `PYTHONPATH`, and report what that
    subprocess sees as `DATABASE_URL` after interpreter startup (which
    auto-imports `sitecustomize`, same as any real Python invocation).
    """
    env = dict(os.environ)
    env["DATABASE_URL"] = ambient_value
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{site_packages_dir}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(site_packages_dir)
    )
    result = subprocess.run(
        [sys.executable, "-c", "import os; print(os.environ.get('DATABASE_URL', ''))"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_worktree_env_wins_over_ambient_database_url(tmp_path):
    """The bug this closes: a real ambient DATABASE_URL (the launching
    shell's) must not win over a worktree's own .env once sitecustomize
    is pinned - `sitecustomize` is auto-imported before `src/db.py`'s
    `load_dotenv()` ever runs.
    """
    fake_worktree = tmp_path / "worktree"
    fake_worktree.mkdir()
    fake_db_url = "postgresql+psycopg://postgres:postgres@localhost:5433/roteiros_wt5"
    (fake_worktree / ".env").write_text(f"DATABASE_URL={fake_db_url}\n", encoding="utf-8")
    site_packages_dir = tmp_path / "site-packages"

    _run_pin_script(fake_worktree, site_packages_dir)

    observed = _probe_database_url(site_packages_dir, AMBIENT_DATABASE_URL)
    assert observed == fake_db_url


def test_no_env_file_has_zero_effect(tmp_path):
    """Simulates CI: `.github/workflows/ci.yml` sets DATABASE_URL as a
    real workflow env var and never writes a `.env`. With no `.env`
    anywhere the script can find one, the generated sitecustomize.py must
    have zero effect - the ambient value passes through unchanged.
    """
    fake_worktree = tmp_path / "worktree_no_env"
    fake_worktree.mkdir()
    site_packages_dir = tmp_path / "site-packages"

    _run_pin_script(fake_worktree, site_packages_dir)

    observed = _probe_database_url(site_packages_dir, AMBIENT_DATABASE_URL)
    assert observed == AMBIENT_DATABASE_URL


def test_running_twice_is_idempotent(tmp_path):
    """`uv sync` can be re-run, and the setup sequence runs this script
    again after it. Running it twice must not error, and must leave
    exactly one correct sitecustomize.py - not a duplicate or an append.
    """
    fake_worktree = tmp_path / "worktree"
    fake_worktree.mkdir()
    fake_db_url = "postgresql+psycopg://postgres:postgres@localhost:5433/roteiros_wt5"
    (fake_worktree / ".env").write_text(f"DATABASE_URL={fake_db_url}\n", encoding="utf-8")
    site_packages_dir = tmp_path / "site-packages"

    _run_pin_script(fake_worktree, site_packages_dir)
    first_content = (site_packages_dir / "sitecustomize.py").read_text(encoding="utf-8")

    _run_pin_script(fake_worktree, site_packages_dir)
    second_content = (site_packages_dir / "sitecustomize.py").read_text(encoding="utf-8")

    written = list(site_packages_dir.glob("sitecustomize*"))
    assert len(written) == 1
    assert first_content == second_content

    observed = _probe_database_url(site_packages_dir, AMBIENT_DATABASE_URL)
    assert observed == fake_db_url
