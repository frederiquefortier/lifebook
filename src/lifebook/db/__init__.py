"""Database access for life.db, the single source of truth.

Every client opens the DB through ``connect()`` so foreign-key enforcement is never
left off (``PRAGMA foreign_keys`` is per-connection in SQLite and defaults to OFF).
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
LOCAL_DIR = REPO_ROOT / "data" / "local"  # gitignored: config + life.db
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
