"""Create life.db from schema.sql. Refuses to touch an existing db unless --force.

    uv run python -m lifebook.db.build_db [--force]
"""

from __future__ import annotations

import argparse
import sys

from . import LIFE_DB_PATH, SCHEMA_PATH, connect


def build(force: bool = False) -> int:
    """Build life.db; return the number of user tables created."""
    if LIFE_DB_PATH.exists():
        if not force:
            print(f"{LIFE_DB_PATH} exists, refusing. Use --force to delete and recreate.")
            return -1
        LIFE_DB_PATH.unlink()
        print(f"deleted {LIFE_DB_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    LIFE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = connect(LIFE_DB_PATH)
    try:
        con.executescript(schema_sql)
        con.commit()
        (table_count,) = con.execute(
            "SELECT count(*) FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()
    finally:
        con.close()

    print(f"created {LIFE_DB_PATH} with {table_count} tables")
    return table_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create life.db from schema.sql.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="delete an existing life.db and rebuild from scratch",
    )
    args = parser.parse_args(argv)
    result = build(force=args.force)
    return 0 if result >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
