"""Smoke test for the life.db data-layer foundation.

Covers: build (28 tables, inline seeds, user_version), label seeding counts,
idempotency, the deprecate/reactivate sync rule, FK enforcement, and config seeding.
Everything runs against temp databases; the real src/life.db is never touched.
"""

from __future__ import annotations

import sqlite3

import pytest

from lifebook.db import SCHEMA_PATH, connect
from lifebook.db import build_db, seed_config as seed_config_mod, seed_labels


def _fresh_db(path):
    """Build a temp life.db from schema.sql and return an open connection."""
    con = connect(path)
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    con.commit()
    return con


def _table_count(con):
    (n,) = con.execute(
        "SELECT count(*) FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()
    return n


def _seed_rows(csv_name):
    """Expected row count for a seed CSV, read with the seeder's own parser so the
    number tracks the file (one insert per slug) instead of being hand-pinned."""
    return len(seed_labels._read_csv(seed_labels.SEED_DIR / csv_name))


# ── build ──────────────────────────────────────────────────────────────────

def test_build_creates_schema(tmp_path, monkeypatch):
    db = tmp_path / "life.db"
    monkeypatch.setattr(build_db, "LIFE_DB_PATH", db)

    assert build_db.build(force=True) == 28
    assert db.exists()

    con = connect(db)
    try:
        assert _table_count(con) == 28
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1
        # inline static seeds
        assert con.execute("SELECT count(*) FROM entry_types").fetchone()[0] == 4
        assert con.execute("SELECT count(*) FROM relationship_types").fetchone()[0] == 5
    finally:
        con.close()


def test_build_refuses_without_force(tmp_path, monkeypatch):
    db = tmp_path / "life.db"
    monkeypatch.setattr(build_db, "LIFE_DB_PATH", db)
    assert build_db.build(force=True) == 28
    # second build without --force must refuse and leave the file intact
    assert build_db.build(force=False) == -1
    assert db.exists()


# ── label seeding ────────────────────────────────────────────────────────────

def test_seed_labels_counts(tmp_path):
    con = _fresh_db(tmp_path / "life.db")
    try:
        results = seed_labels.seed(con)
        # guard: each list actually seeded something (so a derived 0 == 0 can't pass blind)
        assert all(inserted > 0 for inserted, _, _ in results.values())
        assert results["themes"] == (_seed_rows("themes.csv"), 0, 0)
        assert results["emotions"] == (_seed_rows("emotions.csv"), 0, 0)
        assert results["nsfw_tags"] == (_seed_rows("nsfw_tags.csv"), 0, 0)
        # valence / arousal / family landed for a known emotion (ADR-011)
        row = con.execute(
            "SELECT valence, arousal, family FROM emotions WHERE slug = 'joy'"
        ).fetchone()
        assert row["valence"] == pytest.approx(0.85)
        assert row["arousal"] == pytest.approx(0.6)
        assert row["family"] == "joy"
    finally:
        con.close()


def test_seed_labels_idempotent(tmp_path):
    con = _fresh_db(tmp_path / "life.db")
    try:
        seed_labels.seed(con)
        second = seed_labels.seed(con)
        assert second["themes"] == (0, _seed_rows("themes.csv"), 0)
        assert second["emotions"] == (0, _seed_rows("emotions.csv"), 0)
        assert second["nsfw_tags"] == (0, _seed_rows("nsfw_tags.csv"), 0)
        # no duplication
        assert con.execute("SELECT count(*) FROM themes").fetchone()[0] == _seed_rows("themes.csv")
    finally:
        con.close()


def test_deprecate_then_reactivate(tmp_path, monkeypatch):
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    themes = seed_dir / "themes.csv"
    monkeypatch.setattr(seed_labels, "SEED_DIR", seed_dir)

    con = _fresh_db(tmp_path / "life.db")
    try:
        themes.write_text(
            "slug,name,definition,status\n"
            "love,Amour,desc,active\n"
            "family,Famille,desc,active\n",
            encoding="utf-8",
        )
        assert seed_labels.seed_table(con, "themes", "themes.csv", []) == (2, 0, 0)

        # drop 'love' -> it is deprecated, not deleted
        themes.write_text(
            "slug,name,definition,status\nfamily,Famille,desc,active\n", encoding="utf-8"
        )
        assert seed_labels.seed_table(con, "themes", "themes.csv", []) == (0, 1, 1)
        status = con.execute("SELECT status FROM themes WHERE slug = 'love'").fetchone()[0]
        assert status == "deprecated"
        assert con.execute("SELECT count(*) FROM themes").fetchone()[0] == 2

        # re-add 'love' as active -> reactivated
        themes.write_text(
            "slug,name,definition,status\n"
            "love,Amour,desc,active\n"
            "family,Famille,desc,active\n",
            encoding="utf-8",
        )
        assert seed_labels.seed_table(con, "themes", "themes.csv", []) == (0, 2, 0)
        status = con.execute("SELECT status FROM themes WHERE slug = 'love'").fetchone()[0]
        assert status == "active"
    finally:
        con.close()


# ── foreign keys & triggers ──────────────────────────────────────────────────

def test_foreign_keys_enforced(tmp_path):
    con = _fresh_db(tmp_path / "life.db")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO entry_people (entry_id, person_id) VALUES (999, 999)"
            )
            con.commit()
    finally:
        con.close()


def test_updated_at_trigger(tmp_path):
    con = _fresh_db(tmp_path / "life.db")
    try:
        con.execute("INSERT INTO people (display_name) VALUES ('Louise')")
        con.commit()
        before = con.execute("SELECT created_at, updated_at FROM people WHERE id = 1").fetchone()
        # force a distinct timestamp, then update a real column
        con.execute("UPDATE people SET updated_at = '2000-01-01 00:00:00' WHERE id = 1")
        con.execute("UPDATE people SET display_name = 'Maman' WHERE id = 1")
        con.commit()
        after = con.execute("SELECT updated_at FROM people WHERE id = 1").fetchone()[0]
        assert after != "2000-01-01 00:00:00"  # trigger bumped it
        assert before["created_at"] is not None
    finally:
        con.close()


# ── config seeding ───────────────────────────────────────────────────────────

def test_seed_config_from_toml(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    cfg.write_text('author_birthdate = "2000-08-13"\n', encoding="utf-8")
    monkeypatch.setattr(seed_config_mod, "LOCAL_CONFIG_PATH", cfg)

    con = _fresh_db(tmp_path / "life.db")
    try:
        assert seed_config_mod.seed_config(con) is True
        row = con.execute("SELECT author_birthdate FROM config WHERE id = 1").fetchone()
        assert row[0] == "2000-08-13"
        # idempotent upsert
        assert seed_config_mod.seed_config(con) is True
        assert con.execute("SELECT count(*) FROM config").fetchone()[0] == 1
    finally:
        con.close()


def test_seed_config_missing_file_skips(tmp_path, monkeypatch):
    monkeypatch.setattr(seed_config_mod, "LOCAL_CONFIG_PATH", tmp_path / "absent.toml")
    con = _fresh_db(tmp_path / "life.db")
    try:
        assert seed_config_mod.seed_config(con) is False
    finally:
        con.close()
