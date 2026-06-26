"""Seed the label lists (themes / emotions / nsfw_tags) from data/seed/*.csv.

The CSVs are authoritative: a slug in the CSV is inserted/updated; a slug no longer in
the CSV is marked deprecated, never deleted, so historical tags stay valid.

    uv run python -m lifebook.db.seed_labels
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

from . import SEED_DIR, connect

# (table, csv filename, extra non-key columns beyond slug/name/definition/status)
_LABEL_TABLES = [
    ("themes", "themes.csv", []),
    ("emotions", "emotions.csv", ["valence", "arousal", "family"]),
    ("nsfw_tags", "nsfw_tags.csv", []),
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    # utf-8-sig tolerates a stray BOM from editors.
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _coerce(column: str, raw: str | None):
    value = (raw or "").strip()
    if column in ("valence", "arousal"):
        return float(value) if value else None
    if column == "status":
        return value or "active"
    if column == "definition":
        return value or None
    return value


def seed_table(
    con: sqlite3.Connection, table: str, csv_name: str, extra_cols: list[str]
) -> tuple[int, int, int]:
    """Sync one label table from its CSV. Returns (inserted, updated, deprecated)."""
    columns = ["slug", "name", "definition", "status", *extra_cols]
    rows = _read_csv(SEED_DIR / csv_name)

    existing = {r["slug"] for r in con.execute(f"SELECT slug FROM {table}")}
    csv_slugs = {r["slug"].strip() for r in rows}

    inserted = updated = 0
    for row in rows:
        slug = row["slug"].strip()
        values = {col: _coerce(col, row.get(col)) for col in columns}
        if slug in existing:
            assignments = ", ".join(f"{col} = :{col}" for col in columns if col != "slug")
            con.execute(f"UPDATE {table} SET {assignments} WHERE slug = :slug", values)
            updated += 1
        else:
            placeholders = ", ".join(f":{col}" for col in columns)
            con.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                values,
            )
            inserted += 1

    deprecated = 0
    for slug in existing - csv_slugs:
        cur = con.execute(
            f"UPDATE {table} SET status = 'deprecated' "
            "WHERE slug = ? AND status != 'deprecated'",
            (slug,),
        )
        deprecated += cur.rowcount

    return inserted, updated, deprecated


def seed(con: sqlite3.Connection | None = None) -> dict[str, tuple[int, int, int]]:
    own = con is None
    con = con or connect()
    try:
        results: dict[str, tuple[int, int, int]] = {}
        for table, csv_name, extra in _LABEL_TABLES:
            results[table] = seed_table(con, table, csv_name, extra)
        con.commit()
    finally:
        if own:
            con.close()

    for table, (ins, upd, dep) in results.items():
        print(f"{table}: {ins} inserted, {upd} updated, {dep} deprecated")
    return results


def main(argv: list[str] | None = None) -> int:
    seed()
    return 0


if __name__ == "__main__":
    sys.exit(main())
