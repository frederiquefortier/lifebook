# Architecture

`life.db` is the **single source of truth** at the center. Everything else is a client
that reads or writes it: the curation app (capture + human review), the Python
processing layer (import + analysis), and the publication step (render to PDF).

```
        ┌────────────────────────────────────┐
        │  CURATION APP                       │  capture + human-in-the-loop review
        │  React + TipTap  →  local FastAPI   │
        └──────────────────┬─────────────────┘
                           │ read / write (localhost)
                           ▼
   ┌──────────────────────────────────────────────┐
   │  DATA   life.db (SQLite)  ← single source of truth
   └───────────────▲──────────────────┬───────────┘
       read/write  │                  │ read (export)
   ┌───────────────┴───────┐   ┌──────▼────────────────────┐
   │ PROCESSING  Python     │   │ PUBLICATION  InDesign /    │
   │ import, NLP, stats      │   │ Affinity Publisher → PDF   │
   └────────────────────────┘   └────────────────────────────┘
```

**Who writes what** (two writers, one truth):
- **Curation app** writes the human-authored and human-curated data: entries, entry
  metadata (date, type, `nsfw_level`, tags), people/alias decisions, and accept/reject
  verdicts on the analysis suggestions.
- **Python** writes the machine-generated data: imported entries, and *suggested*
  themes/emotions/people (gated by `confidence`, left for the app to confirm).
- Neither is the source of truth. `life.db` is. Both are clients.

---

## 1. Data: the source of truth

The data does not live in InDesign. It is stored in a durable database.

**Chosen solution: SQLite** (`life.db`)

Why SQLite:
- a single file;
- no server to install;
- extremely durable;
- trivial to back up;
- perfect for a personal project.

All the project's memory resides in this one file. See
[database.md](database.md) for the full schema, and
[ADR-001](decisions.md) for the rationale.

---

## 2. Processing: Python

Python scripts are responsible for:
- importing the existing writings (Word docs in Google Drive, and Notion), see
  [ingestion.md](ingestion.md);
- cleaning;
- extracting people;
- detecting themes;
- emotional analysis;
- statistics;
- generating exports.

Candidate tools: Python, spaCy, Transformers, a local open-weight LLM.

The processing layer is scripted rather than manual, so any volume (date range) can be
reproduced. See [ADR-002](decisions.md).

### Label lists (themes & emotions)

Themes and emotions are classified against closed, versioned lists. They are not
extracted free-form. The lists live as flat CSV files in Git and are the source of truth:

```
data/seed/themes.csv      slug, name, definition, status
data/seed/emotions.csv    slug, name, definition, status, valence
data/seed/nsfw_tags.csv   slug, name, definition, status
```

A seed script (`seed_labels.py`) loads them into the `themes` / `emotions` /
`nsfw_tags` tables in `life.db` (the runtime copy that the join tables reference). Edit
the CSV, re-run the seed. See [ADR-005](decisions.md) for the rationale and [database.md](database.md) for
the `list_version` columns.

> These three are seeded from Git because the classifier reads them (they need
> definitions + versioning). Purely editorial lookup lists (e.g. `top_categories`)
> are *not* seeded; they're managed in the app and live only in the DB. See
> [database.md](database.md#yearly-tops).

---

## Curation app:  capture & review

A local-first app for writing new entries and curating the data. It is the
day-to-day intake (so the system keeps growing) and the human-in-the-loop review hub
(so the NLP suggestions get confirmed by a person). See [ADR-006](decisions.md).

**Stack:** React + TipTap frontend (a Google-Docs-style rich editor), a thin local
FastAPI backend over `life.db`. Runs locally only. The private database never leaves
the machine. Python remains the only language that writes the DB (reused from the
processing layer). Packageable as a desktop app (Tauri/Electron) later if wanted.

**Scope (v1 candidate):**
- Entries: add / edit / delete, with metadata (date, type, `nsfw_level`, tags).
- Structured content beyond journal prose: books & citations, prompts, fun facts,
  *fêtes*, abécédaires, bingo, bucketlist (a template/editor per type; the structured
  ones write to their own tables).
- Yearly tops: build a year's ranked lists; the category is a select-or-add field
  backed by `top_categories` (pick an existing kind or add a new one).
- People & alias review: assign people to entries; the consolidation queue
  ("is *Maman* the same as *Louise*?").
- Events & places: tag entries with named happenings (`events`) and a location; a
  map module to pick/confirm where you were (writes `places` + `entries.place_id`).
- Theme/emotion review queue: accept/reject the classifier's confidence-gated
  suggestions ([ADR-005](decisions.md)).
- Search & filter: by date, person, theme, emotion, event, place, type, `nsfw_level`.
- Two-temporality views: a calendar timeline *and* a birthday/personal-time view.
- Dashboard / cartography preview: live mini-versions of the book's end analytics
  (people frequency, theme/emotion over time, the valence mood curve, the map).

---

## 3. Publication: layout engine

Layout is done in Adobe InDesign or Affinity Publisher.

### Relationship with InDesign

Fundamental principle: InDesign is a render engine. It is not the source of truth.

Workflow (one direction only):

```
SQLite → Python → Export → InDesign → PDF
```

> **Export mechanics: TBD at production time.** The exact export format (IDML, tagged
> text, or a data-merge feed) and how data flows into the layout are deferred until
> there's data to publish. InDesign has data-merge, scripting (ExtendScript/UXP), and
> IDML import; the right one is decided when the book is actually produced.

### Manual edits

Yes, after generation, the following remain possible:
- typographic adjustments;
- pagination;
- images;
- visual hierarchy.

Editorial corrections are expected; they are downstream polish, never re-imported
upstream. See [ADR-003](decisions.md).

> **Note: the renderer is replaceable.** A future digital edition (e.g. a web
> renderer) is possible as an additional render target for the same data, parallel to
> the InDesign print path. Both honor the same principle: the data is the source of
> truth, the renderer is replaceable.

---

## Backups: the 3-2-1 rule

Minimum 3 copies:

1. **Local copy:** primary computer.
2. **Cloud copy:** Google Drive, Dropbox, or iCloud, encrypted before upload.
3. **Cold copy:** external hard drive; annual archive.

`life.db` is the concentrated, consolidated, sensitivity-tagged archive, far more
sensitive than the scattered source docs. Any copy that leaves the machine (the cloud
copy) must be encrypted. See [ADR-004](decisions.md).

## Version control: Git scope

**In Git:** Python code, scripts, schemas, label-list CSVs, templates, documentation,
the app source.

**Out of Git:** `life.db` (it's data, backed up via 3-2-1, not versioned in Git),
exported PDFs, and large files.

See [ADR-004](decisions.md) for the backup and Git-scope decisions.
