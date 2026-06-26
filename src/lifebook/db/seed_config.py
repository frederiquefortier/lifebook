"""Seed the single-row config table from data/local/config.toml (gitignored).

author_birthdate is the one private project constant; it drives personal-time math and
is kept out of Git. On a fresh clone the file is absent and this step is skipped.

    # data/local/config.toml
    author_birthdate = "2000-08-13"

    uv run python -m lifebook.db.seed_config
"""

from __future__ import annotations

import sqlite3
import sys
import tomllib

from . import LOCAL_CONFIG_PATH, connect


def seed_config(con: sqlite3.Connection | None = None) -> bool:
    """Upsert the config row from the local TOML file. Returns True if applied."""
    if not LOCAL_CONFIG_PATH.exists():
        print(f"no local config at {LOCAL_CONFIG_PATH}, skipping")
        return False

    with LOCAL_CONFIG_PATH.open("rb") as fh:
        data = tomllib.load(fh)
    birthdate = data.get("author_birthdate")
    if not birthdate:
        print(f"{LOCAL_CONFIG_PATH} has no author_birthdate, skipping")
        return False

    own = con is None
    con = con or connect()
    try:
        con.execute(
            "INSERT INTO config (id, author_birthdate) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET author_birthdate = excluded.author_birthdate",
            (birthdate,),
        )
        con.commit()
    finally:
        if own:
            con.close()

    print(f"config: author_birthdate set to {birthdate}")
    return True


def main(argv: list[str] | None = None) -> int:
    seed_config()
    return 0


if __name__ == "__main__":
    sys.exit(main())
