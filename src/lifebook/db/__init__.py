"""Database access for life.db — the single source of truth.

Every client (build/seed scripts here, the future FastAPI backend and pipeline) opens
the DB through ``connect()`` so foreign-key enforcement is never accidentally left off
(``PRAGMA foreign_keys`` is per-connection in SQLite and defaults to OFF).

Path constants are resolved relative to this package so the working directory doesn't
matter (src-layout: the package is under src/, while data/ lives at the repo root):

    repo/
      src/lifebook/db/__init__.py   <- this file
      src/lifebook/db/schema.sql
      data/seed/*.csv               (Git source of truth)
      data/local/config.toml        (gitignored)
      data/local/life.db            (gitignored, created by build_db)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# .../src/lifebook/db -> package -> src -> repo root
_DB_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = _DB_DIR.parent
REPO_ROOT = PACKAGE_ROOT.parent.parent

SCHEMA_PATH = _DB_DIR / "schema.sql"
SEED_DIR = REPO_ROOT / "data" / "seed"
# data/local: gitignored, machine-local private state — config and life.db (ADR-004).
LOCAL_DIR = REPO_ROOT / "data" / "local"
LOCAL_CONFIG_PATH = LOCAL_DIR / "config.toml"
LIFE_DB_PATH = LOCAL_DIR / "life.db"


def connect(path: Path | str = LIFE_DB_PATH) -> sqlite3.Connection:
    """Open a connection to life.db with project defaults.

    Enables foreign-key enforcement and returns rows as ``sqlite3.Row`` (name-indexable).
    """
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con
