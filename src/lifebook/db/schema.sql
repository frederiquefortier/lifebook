-- Lifebook — life.db schema (SQLite).
-- The single source of truth. Generated/maintained by hand from docs/01_building/database.md.
--
-- Conventions (see ADR-008/009/010 and database.md):
--   * Every id is INTEGER PRIMARY KEY AUTOINCREMENT  -> ids are never reused.
--   * Every table carries created_at / updated_at (TEXT, ISO-8601 via CURRENT_TIMESTAMP);
--     an AFTER UPDATE trigger keeps updated_at current. The WHEN guard prevents recursion.
--   * Dates are TEXT ISO-8601 'YYYY-MM-DD'. date_precision says how to render them.
--   * Foreign keys: join rows CASCADE when their entry is deleted; references to
--     dimension rows (people/themes/...) RESTRICT so a tagged dimension can't vanish.
--   * PRAGMA foreign_keys is per-connection and is enabled by lifebook.db.connect().
--
-- This file is the authoritative baseline. While there is no real data it may be edited
-- and the DB rebuilt with `build_db --force`. Once life.db holds real entries, freeze
-- this file and evolve with additive numbered migrations instead (ADR-010).

PRAGMA user_version = 1;

-- ───────────────────────────── Project config ─────────────────────────────

-- Single-row table: the one constant that can't be derived — the author's birthdate,
-- which makes personal time (age, birthday-to-birthday) computable. Seeded locally from
-- a gitignored file, never committed (ADR-004); see lifebook/db/seed_config.py.
CREATE TABLE config (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    author_birthdate TEXT NOT NULL CHECK (author_birthdate GLOB '????-??-??'),
    created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ───────────────────────── Dimension / lookup tables ──────────────────────

-- Prose-shaped entry types (English slugs; UI labels are an app concern). Seeded below.
CREATE TABLE entry_types (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Canonical people — each individual exists exactly once.
CREATE TABLE people (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Alternate names that resolve to one person (Mom / Maman / Louise -> one row).
CREATE TABLE person_aliases (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id  INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    alias      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Relationship taxonomy (English slugs). Seeded below; extendable in-app later.
CREATE TABLE relationship_types (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- How a relationship evolves over time; one person may hold several at once.
CREATE TABLE person_relationships (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id            INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    relationship_type_id INTEGER NOT NULL REFERENCES relationship_types(id) ON DELETE RESTRICT,
    start_date           TEXT,
    end_date             TEXT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Closed, versioned theme list — runtime copy of data/seed/themes.csv (ADR-005).
CREATE TABLE themes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    definition TEXT,
    status     TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Closed, versioned emotion list — runtime copy of data/seed/emotions.csv (ADR-005, ADR-011).
-- valence (-1..+1, unpleasant..pleasant) and arousal (0..1, calm..activated) place each
-- emotion on the 2-D mood meter; `family` is its slug in the 9-family wheel for grouped
-- views. valence × per-entry intensity drives the continuous "emotional climate" curve.
CREATE TABLE emotions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    definition TEXT,
    status     TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated')),
    valence    REAL,
    arousal    REAL,
    family     TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Closed sensitivity-category list — runtime copy of data/seed/nsfw_tags.csv (ADR-005).
-- (The 0-3 intensity LEVEL is a separate column on entries.)
CREATE TABLE nsfw_tags (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    definition TEXT,
    status     TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Named happenings that group entries (a trip, a milestone). App-managed; not seeded.
CREATE TABLE events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    start_date TEXT,
    end_date   TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Geographic points — the map module backbone. App-managed; not seeded.
CREATE TABLE places (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    lat        REAL,
    lng        REAL,
    kind       TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Kinds of yearly "top" list (songs, games, ...). App-managed select-or-add; not seeded.
CREATE TABLE top_categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ───────────────────────────── Core content ───────────────────────────────

-- The atomic unit: one dated, taggable, analyzable piece of content.
CREATE TABLE entries (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL CHECK (date GLOB '????-??-??'),
    date_precision TEXT NOT NULL DEFAULT 'day'
                       CHECK (date_precision IN ('day', 'week', 'month', 'year')),
    entry_type_id  INTEGER NOT NULL REFERENCES entry_types(id) ON DELETE RESTRICT,
    place_id       INTEGER REFERENCES places(id) ON DELETE RESTRICT,
    title          TEXT,
    content        TEXT NOT NULL,
    nsfw_level     INTEGER NOT NULL DEFAULT 0 CHECK (nsfw_level BETWEEN 0 AND 3),
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ───────────────────────── Join tables (many-to-many) ─────────────────────

CREATE TABLE entry_people (
    entry_id   INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    person_id  INTEGER NOT NULL REFERENCES people(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, person_id)
);

CREATE TABLE entry_themes (
    entry_id     INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    theme_id     INTEGER NOT NULL REFERENCES themes(id) ON DELETE RESTRICT,
    confidence   REAL,
    list_version INTEGER,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, theme_id)
);

CREATE TABLE entry_emotions (
    entry_id     INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    emotion_id   INTEGER NOT NULL REFERENCES emotions(id) ON DELETE RESTRICT,
    intensity    REAL,
    confidence   REAL,
    list_version INTEGER,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, emotion_id)
);

CREATE TABLE entry_events (
    entry_id   INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    event_id   INTEGER NOT NULL REFERENCES events(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, event_id)
);

CREATE TABLE entry_nsfw_tags (
    entry_id    INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    nsfw_tag_id INTEGER NOT NULL REFERENCES nsfw_tags(id) ON DELETE RESTRICT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, nsfw_tag_id)
);

-- ─────────────────────── Yearly summary (calendar time) ───────────────────

CREATE TABLE yearly_reviews (
    year              INTEGER PRIMARY KEY,
    word_of_year      TEXT,
    retrospective     TEXT,
    annual_stats_json TEXT,
    created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ───────────────────────────── Yearly tops ────────────────────────────────

CREATE TABLE top_lists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER NOT NULL,
    category_id INTEGER NOT NULL REFERENCES top_categories(id) ON DELETE RESTRICT,
    title       TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE top_list_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id    INTEGER NOT NULL REFERENCES top_lists(id) ON DELETE CASCADE,
    rank       INTEGER NOT NULL,
    label      TEXT NOT NULL,
    detail     TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────── Structured content ───────────────────────────

CREATE TABLE books (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    author         TEXT,
    commentary     TEXT,
    date           TEXT,
    date_precision TEXT NOT NULL DEFAULT 'day'
                       CHECK (date_precision IN ('day', 'week', 'month', 'year')),
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE book_citations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id    INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    rank       INTEGER,
    text       TEXT NOT NULL,
    reflection TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alphabets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    year       INTEGER NOT NULL,
    title      TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alphabet_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    alphabet_id INTEGER NOT NULL REFERENCES alphabets(id) ON DELETE CASCADE,
    position    INTEGER,
    letter      TEXT,
    word        TEXT,
    text        TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bingos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    year       INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bingo_cells (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    bingo_id   INTEGER NOT NULL REFERENCES bingos(id) ON DELETE CASCADE,
    "row"      INTEGER,
    "col"      INTEGER,
    label      TEXT,
    icon       TEXT,
    checked_at TEXT,                 -- NULL = unchecked
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A single running list (not per year): goals added, checked, or removed over time.
CREATE TABLE bucketlist_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    number     INTEGER,
    text       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active', 'done', 'removed')),
    added_date TEXT,
    done_date  TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ───────────────────────────────── Indexes ────────────────────────────────

CREATE INDEX idx_entries_date         ON entries(date);
CREATE INDEX idx_entries_entry_type   ON entries(entry_type_id);
CREATE INDEX idx_entries_place        ON entries(place_id);

CREATE INDEX idx_person_aliases_person ON person_aliases(person_id);
CREATE INDEX idx_person_aliases_alias  ON person_aliases(alias);
CREATE INDEX idx_person_rel_person     ON person_relationships(person_id);
CREATE INDEX idx_person_rel_type       ON person_relationships(relationship_type_id);

CREATE INDEX idx_entry_people_person   ON entry_people(person_id);
CREATE INDEX idx_entry_themes_theme    ON entry_themes(theme_id);
CREATE INDEX idx_entry_emotions_emotion ON entry_emotions(emotion_id);
CREATE INDEX idx_entry_events_event    ON entry_events(event_id);
CREATE INDEX idx_entry_nsfw_tag        ON entry_nsfw_tags(nsfw_tag_id);

CREATE INDEX idx_top_lists_category    ON top_lists(category_id);
CREATE INDEX idx_top_lists_year        ON top_lists(year);
CREATE INDEX idx_top_list_items_list   ON top_list_items(list_id);

CREATE INDEX idx_book_citations_book   ON book_citations(book_id);
CREATE INDEX idx_alphabet_items_alpha  ON alphabet_items(alphabet_id);
CREATE INDEX idx_bingo_cells_bingo     ON bingo_cells(bingo_id);

-- ───────────── updated_at triggers (one per table; WHEN guard = no recursion) ─────────────
-- Pattern: bump updated_at only when the caller didn't already change it, so the
-- trigger's own UPDATE doesn't re-fire. rowid works uniformly across all tables.

CREATE TRIGGER trg_config_updated_at AFTER UPDATE ON config FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE config SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entry_types_updated_at AFTER UPDATE ON entry_types FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entry_types SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_people_updated_at AFTER UPDATE ON people FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE people SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_person_aliases_updated_at AFTER UPDATE ON person_aliases FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE person_aliases SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_relationship_types_updated_at AFTER UPDATE ON relationship_types FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE relationship_types SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_person_relationships_updated_at AFTER UPDATE ON person_relationships FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE person_relationships SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_themes_updated_at AFTER UPDATE ON themes FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE themes SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_emotions_updated_at AFTER UPDATE ON emotions FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE emotions SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_nsfw_tags_updated_at AFTER UPDATE ON nsfw_tags FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE nsfw_tags SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_events_updated_at AFTER UPDATE ON events FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE events SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_places_updated_at AFTER UPDATE ON places FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE places SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_top_categories_updated_at AFTER UPDATE ON top_categories FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE top_categories SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entries_updated_at AFTER UPDATE ON entries FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entries SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entry_people_updated_at AFTER UPDATE ON entry_people FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entry_people SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entry_themes_updated_at AFTER UPDATE ON entry_themes FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entry_themes SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entry_emotions_updated_at AFTER UPDATE ON entry_emotions FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entry_emotions SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entry_events_updated_at AFTER UPDATE ON entry_events FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entry_events SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_entry_nsfw_tags_updated_at AFTER UPDATE ON entry_nsfw_tags FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE entry_nsfw_tags SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_yearly_reviews_updated_at AFTER UPDATE ON yearly_reviews FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE yearly_reviews SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_top_lists_updated_at AFTER UPDATE ON top_lists FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE top_lists SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_top_list_items_updated_at AFTER UPDATE ON top_list_items FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE top_list_items SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_books_updated_at AFTER UPDATE ON books FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE books SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_book_citations_updated_at AFTER UPDATE ON book_citations FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE book_citations SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_alphabets_updated_at AFTER UPDATE ON alphabets FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE alphabets SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_alphabet_items_updated_at AFTER UPDATE ON alphabet_items FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE alphabet_items SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_bingos_updated_at AFTER UPDATE ON bingos FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE bingos SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_bingo_cells_updated_at AFTER UPDATE ON bingo_cells FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE bingo_cells SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

CREATE TRIGGER trg_bucketlist_items_updated_at AFTER UPDATE ON bucketlist_items FOR EACH ROW
  WHEN OLD.updated_at = NEW.updated_at
  BEGIN UPDATE bucketlist_items SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid; END;

-- ──────────────────────── Inline static seeds ─────────────────────────────
-- Fixed code-like lists the pipeline references. Editorial/app-managed lists
-- (events, places, top_categories, people) are intentionally left empty.

INSERT INTO entry_types (name) VALUES
    ('journal'), ('birthday'), ('fun_fact'), ('prompt');

INSERT INTO relationship_types (name) VALUES
    ('family'), ('romantic'), ('friendship'), ('work'), ('school');
