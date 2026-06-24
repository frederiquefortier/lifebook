# Architectural Decision Records

Document architectural choices with context, alternatives considered, and trade-offs. Check this file before proposing changes that might conflict with past decisions.

## Format

### ADR-XXX: Decision Title (YYYY-MM-DD)

**Context:**
- Why the decision was needed
- What problem it solves

**Decision:**
- What was chosen

**Alternatives Considered:**
- Option 1 -> Why rejected
- Option 2 -> Why rejected

**Consequences:**
- Benefits
- Trade-offs

---

<!-- Add new entries below this line, newest first -->

### ADR-007: Content is French — tooling must be French-first (2026-06-24)

**Context:**
- The writings are in French (and so are book features like *mot de l'année* and
  *abécédaire*). Defaults in most NLP/LLM tooling are English-first, which would
  silently degrade quality on French text.

**Decision:**
- Treat French as the primary content language end-to-end:
  - **Ingestion** parses French date formats (e.g. *12 janvier 2018*) and French text.
  - **NLP** uses French-capable models — e.g. spaCy `fr_core_news_*` for person/NER,
    and French-capable embeddings / classifier models.
  - **LLM** prompts and label `definition` glosses are written in French (the model
    reads French entries best when instructed in French).
  - **Label lists:** `slug` stays neutral/English (a stable code key), while `name` and
    `definition` are French for display and prompting.
- Entry `content` is stored verbatim in its original French; no translation.

**Alternatives Considered:**
- English-first / default models -> Measurably worse on French NER, dates, and
  classification; the silent-degradation trap.
- Translate everything to English for processing -> Lossy, distorts voice and nuance,
  adds a fragile step; rejected.
- Bilingual everything -> Unnecessary overhead for a single-language corpus.

**Consequences:**
- Analysis quality holds up on the actual content.
- Trade-off: model choices are constrained to those with good French support, and the
  label-list definitions must be authored in French.

---

### ADR-006: Local-first curation app (React/TipTap + FastAPI) (2026-06-24)

**Context:**
- The "living system for decades" vision needs a day-to-day way to add new entries —
  the snapshot-from-data model said nothing about intake.
- The analysis pipeline produces *suggestions* (themes, emotions, alias matches) that a
  human must confirm; there was no place for that human-in-the-loop review.
- The data is private and must not leave the machine ([ADR-005], privacy principle).

**Decision:**
- Build a **local-first** app that is both the capture tool (write/edit entries) and
  the curation hub (review and confirm pipeline suggestions).
- **Stack:** React + TipTap frontend (Google-Docs-style rich editor) over a thin
  **local FastAPI** backend that reads/writes `life.db`. Runs on localhost only.
- Python stays the only language that writes the DB (the app's backend reuses the
  processing layer). `life.db` remains the single source of truth; the app and the
  Python batch jobs are both clients (see "who writes what" in
  [architecture.md](architecture.md)).
- Scope and features are listed in [architecture.md](architecture.md); it can be
  packaged as a desktop app (Tauri/Electron) later.

**Alternatives Considered:**
- Keep editing in Word/Notion and only ever re-import -> No place for human review of
  suggestions; keeps private content in the cloud; clunky intake.
- A hosted web app -> Sends private data off the machine; violates ADR-005.
- Electron + better-sqlite3 (all-JS) -> Works, but makes JS *and* Python both write the
  DB; rejected to keep a single DB-writing language.
- Tauri + Rust -> Smallest/most secure, but adds Rust as a third language for no
  current benefit.

**Consequences:**
- The system gains a real intake loop and a home for confirming NLP output.
- Reuses Python skills and keeps DB writes in one language; stays fully offline.
- Trade-off: it's a second codebase to build and maintain alongside the pipeline; two
  writers to `life.db` means "who writes what" must stay disciplined.

---

### ADR-005: Closed, versioned label lists for themes & emotions (2026-06-24)

**Context:**
- The value of the analysis layer is longitudinal aggregation — heatmaps, "themes
  over the decade," evolution curves. That requires labels that are *comparable and
  countable across ten years*.
- Free-form theme/emotion extraction produces inconsistent labels (e.g. `career
  anxiety` one year, `professional stress` another) that cannot be aggregated, and
  cannot be evaluated for accuracy.
- The content is intimate and NSFW-flagged; ownership and privacy are core principles.

**Decision:**
- Classify entries against a **closed, fixed list** of themes and emotions rather than
  extracting free-form labels. (The lists are flat controlled vocabularies, not a
  hierarchy — hence "label lists," not "taxonomy.")
- Rules:
  - **Multi-label** with per-label `confidence` / `intensity` (schema already supports
    this); results are *suggestions* gated by confidence and spot-reviewed.
  - Keep an **`other` / uncategorized escape hatch** so the model is never forced to
    mislabel; review `other` periodically to grow the list.
  - **Version the list** — record which `list_version` each tag was produced under,
    so additions in a later volume can be re-tagged honestly (supports
    "reproducible for any date range").
  - **Themes** are bootstrapped from the corpus (one open/clustering pass on a sample
    to discover real recurring themes), then frozen into the list — not invented from
    a generic template.
  - **Emotions** use a small discrete set, plus a per-emotion **valence** anchor
    (pleasant ↔ unpleasant) so a continuous "emotional climate" curve can be derived
    alongside the discrete labels. (Arousal was considered and dropped as
    lower-value — see [improvements.md](../03_planning/improvements.md) if revisited.)
- Tooling: a **local** open-weight LLM fed the list (returning labels +
  confidence + a supporting quote), optionally with an embeddings/similarity first
  pass as a cheap cross-check. Run locally so private content never leaves the machine.
  - **Build-time vs. run-time:** cloud LLMs (including Claude Code) are fine for
    *building* the pipeline — writing the code, schema, and seed scripts, none of
    which contain private entries. But the **run-time classifier that reads the
    entries must be local** (e.g. Ollama / llama.cpp); never send journal text to a
    cloud API. The stated bar is "data doesn't leave the machine," which is stricter
    than "won't be trained on," so cloud fails it regardless of provider policy.

**Where the lists live (source vs. runtime copy):**
- **Source of truth — flat CSV files in Git:** `data/seed/themes.csv` and
  `data/seed/emotions.csv`. These are what you hand-edit, diff, and review. Columns:
  `slug, name, definition, status` (themes) and the same plus `valence`
  (emotions). `definition` is the gloss that drives the embeddings / LLM prompt;
  `status` is `active | deprecated`.
- **Runtime copy — the `themes` / `emotions` tables in `life.db`:** seeded from the
  CSVs by a script (`seed_labels.py`), never hand-edited. These supply the `id`s that
  `entry_themes` / `entry_emotions` reference, and enable SQL aggregation.
- Sync is insert-or-update by `slug`; rows that already have tags pointing at them are
  marked `deprecated`, never deleted.
- CSV chosen over YAML/JSON: the data is tabular, CSV opens in anything forever, diffs
  cleanly line-by-line, needs no dependency or parser quirks (YAML's whitespace and
  type-coercion footguns cut against durability).
- **`nsfw_tags` follows the same pattern** — it's also a closed controlled list, so it
  lives in `data/seed/nsfw_tags.csv` and is seeded the same way (the *level* `0–3` is a
  separate intensity score on the entry; see [database.md](database.md#nsfw)).
- **Not everything controlled is seeded.** The seed-from-Git pattern is for lists the
  *pipeline/classifier reads* and must version. Purely **editorial** lookup lists with
  no classifier behind them — e.g. `top_categories` — are managed in the app
  (select-or-add) and live only in the DB, like `people` / `person_aliases`.

**Alternatives Considered:**
- Free-form / open extraction -> Inconsistent, non-aggregatable labels; unmeasurable.
- Fine-tuned classifier -> Needs labeled training data that doesn't exist at this
  scale; overkill for a few thousand entries.
- Zero-shot NLI classification -> Workable but weaker than an LLM on nuanced,
  first-person (often French) text.
- Cloud LLM API -> Rejected for sensitive content; conflicts with ownership/privacy.
- Lists living *only* in the DB -> `life.db` is not in Git, so the lists couldn't be
  versioned, diffed, or reproduced, and the LLM/embedding definitions would have no
  home.
- Lists living *only* in a file -> No referential integrity for the join tables and no
  SQL aggregation. Hence: file = source, DB = runtime copy.

**Consequences:**
- Labels are comparable across years, enabling the final analytical cartography.
- The fuzzy problem becomes measurable: hand-label a sample, measure accuracy, tune
  thresholds.
- The supporting quote per label builds trust and is reusable in the book.
- Trade-off: the lists must be curated and versioned over time, theme discovery needs
  an upfront bootstrap pass, and the CSV→DB seed step must be re-run after any edit.
  See [improvements.md](../03_planning/improvements.md) for the bootstrap task and
  [database.md](database.md) for the `list_version` columns.

---

### ADR-004: Encrypted 3-2-1 backups and a scoped Git repository (2026-06-24)

**Context:**
- A lifetime archive must survive disk failure, theft, and accidental deletion.
- `life.db` is the *concentrated* archive — consolidated, analyzed, sensitivity-tagged.
  It is far more sensitive than the scattered source docs, and the privacy principle
  (and ADR-005) says private content must not leave the machine in the clear.
- Reality: the current source writings already live in Google Drive and Notion. That
  cloud exposure is the past; the consolidated DB is what's worth protecting going
  forward.

**Decision:**
- Keep a minimum of 3 copies: local (primary computer), cloud (Google Drive / Dropbox
  / iCloud), and a cold offline copy (external drive, annual archive).
- **Encrypt any copy that leaves the machine** — the cloud copy is an encrypted
  `life.db` archive, never plaintext.
- After ingestion, the **original Word/Notion sources are retired** (archived, then
  removed): once imported and verified, `life.db` is the source of truth, so the cloud
  originals are redundant exposure.
- Track in Git: Python code, scripts, label-list CSVs, schemas, templates, the app
  source, documentation. Keep out of Git: `life.db` (data, not versioned), exported
  PDFs, large files.

**Alternatives Considered:**
- Single cloud copy only -> Single point of failure; no offline protection.
- Plaintext cloud backups -> Contradicts the privacy principle and ADR-005.
- Keeping the cloud source docs around indefinitely -> Redundant exposure once the DB
  is authoritative.
- `life.db` in Git -> It's data, not code; bloats history and would put private content
  in the repo.

**Consequences:**
- Strong protection against the common failure modes of a personal archive, without
  reintroducing the cloud-plaintext exposure the project is trying to leave behind.
- Trade-off: backups are a manual discipline, and encryption adds a key to manage
  (lose the key, lose the backup) — the key itself needs its own safe storage.

---

### ADR-003: InDesign / Affinity as a render engine, not the source (2026-06-24)

**Context:**
- The book must be high quality and allow manual typographic polish.
- Layout tools are not durable and must not own the canonical content.

**Decision:**
- Use Adobe InDesign or Affinity Publisher purely as a rendering layer.
- Workflow is one-directional: SQLite → Python → Export → InDesign → PDF.
- Manual edits (typography, pagination, images, hierarchy) happen downstream and are
  never re-imported into the data.

**Alternatives Considered:**
- Author directly in InDesign -> Couples the archive to a proprietary tool; not
  reproducible; dies with the software.
- Fully automated layout with no manual step -> Sacrifices editorial craft and print
  quality.

**Consequences:**
- The data stays portable and the output stays beautiful.
- Trade-off: manual layout work is redone if a decade is regenerated; the layout step
  is not yet automated. A future digital renderer could serve as a parallel render
  target.

---

### ADR-002: Python (with spaCy / Transformers) for the processing layer (2026-06-24)

**Context:**
- Raw writings need to be imported, cleaned, and analyzed (people, themes, emotions,
  statistics) repeatably across decades.

**Decision:**
- Use scripted Python for import (from Word), cleaning, NLP extraction, statistics,
  and export generation. Candidate libraries: spaCy and Transformers.

**Alternatives Considered:**
- Manual tagging in a spreadsheet -> Not reproducible; doesn't scale across a decade
  of entries.
- A heavyweight ML service / SaaS -> Conflicts with the ownership and durability
  principles.

**Consequences:**
- Analyses are reproducible and re-runnable for each decade.
- Trade-off: NLP results need confidence scores and human review (reflected by the
  `confidence` columns in the schema).

---

### ADR-001: SQLite (`life.db`) as the single source of truth (2026-06-24)

**Context:**
- The project must store a lifetime of writings durably and independently of any
  layout tool, with full ownership and easy backup.

**Decision:**
- Store all canonical content in a single SQLite file, `life.db`. The data does not
  live in InDesign. All outputs are regenerated from this file. See
  [database.md](database.md).

**Alternatives Considered:**
- A client/server database (Postgres/MySQL) -> Requires running a server; harder to
  back up and far less portable for a personal lifetime project.
- Flat files / Word documents as the source -> Hard to query, analyze, and keep
  consistent; no relational integrity for people/themes/emotions.
- Storing content in InDesign -> Couples the archive to a proprietary, non-durable
  tool.

**Consequences:**
- One portable, durable file holds the entire project memory; trivial to back up and
  migrate; no server.
- Enables normalized people/themes/emotions and reproducible analysis.
- Trade-off: concurrency and very large blobs are not SQLite strengths — so when media
  is added later, the files will live outside the DB (only references stored).
