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

### ADR-015: A manual override layer for letters the parser cannot place (2026-07-04)

**Context:**
- The prose importer classifies each Drive letter by counting its standalone date headers
  (0 / 1 / 2+). A tail of ~20 letters defeats that heuristic, each in a different way:
  - dateless letters (no header at all);
  - year-in-review letters whose date is written messily at the end (`1819 août 2024.`,
    `12... nop 13 août 2020.`), so no header parses;
  - files where the date sits at the *end* of each passage, which the header-then-content
    parser silently misdates by one;
  - répertoires and goal-bilans whose internal date lines get shredded into dozens of bogus
    daily entries;
  - titled two-part letters that need a title attached per section.
  These were held out into a report, and "held out" means never ingested.
- Fixing this in the parser's own heuristics would make the generic classifier fragile: a
  date-at-end rule misfires on ordinary journals, and nothing reliably separates a répertoire
  from a sporadic journal. And baking the private per-letter dates into git-tracked code
  violates the out-of-git privacy rule ([ADR-004]).

**Decision:**
- Add a gitignored `data/local/date_overrides.toml`, keyed by source filename with DD-MM-YYYY
  dates, that the importer consults per file before the automatic classifier. Modes: `whole`
  (one entry at a fixed date, internal headers ignored), `preamble` (the orphan preamble
  becomes its own dated entry, the rest splits normally), `defer_preamble` (drop a leading
  goals block, keep the dailies), `end_dates` (a date header closes the passage *above* it),
  `sections` (split on detected headers and attach given titles), and `skip` (defer the whole
  file to a future special-type pass).
- The overrides are *data* beside `life.db`, not code: the parser stays generic and private
  dates never enter git. Filename lookup is NFC-normalized, because Drive stores some accents
  decomposed (NFD `août`) and others precomposed.

**Alternatives Considered:**
- Extend the parser heuristics (auto date-at-end, auto répertoire detection) -> fragile; a
  trailing-date rule misfires on normal journals, and no signal cleanly flags a répertoire.
- Hardcode a dict in `prose.py` -> puts private journal dates into git-tracked source,
  against the out-of-git rule ([ADR-004]).
- Edit the source `.docx` to insert clean headers -> mutates raw upstream assets; the
  pipeline is one-way and the raw files are read-only.
- Leave them held out -> ~20 real entries (two of them birthday reviews) never ingested, and
  the silently mis-ingested répertoires keep polluting the corpus with bogus dailies.

**Consequences:**
- Every held-out letter resolves (held-out files 20 -> 0); répertoires / goals / prompts are
  explicitly deferred rather than shredded (removed dozens of bogus daily entries).
- Surfaced a real parser bug: end-dated files were misdated by one passage (a St-Valentin
  entry landed on 3 février instead of 14). `end_dates` fixes it; sibling files that are
  start-dated were already correct.
- To keep the module's "nothing is dropped silently" promise at the override layer itself,
  the importer tracks which keys matched and holds out any leftover (a typo, or a name that
  lost the dedup race or is a special), rather than letting that letter fall back to the
  automatic classifier unnoticed. Hand-authored overrides are validated up front and fail
  naming the offending file.
- Trade-off: the overrides file is hand-maintained and lives outside git, so it is backed up
  with `life.db` ([ADR-004]) and must be kept in sync if a source filename changes. The
  deferred specials still need first-class modeling (tracked in
  [improvements.md](../03_planning/improvements.md)).

---

### ADR-014: `entries.end_date` for passages that span a range of days (2026-07-04)

**Context:**
- A few backlog passages are written about a span rather than a day (`1e novembre au 23
  novembre 2022`; `Samedi, 6 mai 2023 au lundi, 15 mai 2023`). Each is one block of
  reflection, so it cannot be split into per-day entries, and the atomic "one entry = one
  date" rule has no single date for it.
- The schema stored only `date` + `date_precision` (day/week/month/year). We are
  pre-cutover ([ADR-010]), so a schema change is a free edit now and a migration later.

**Decision:**
- Add a nullable `entries.end_date` (TEXT ISO date) with
  `CHECK (end_date IS NULL OR (end_date GLOB '????-??-??' AND end_date >= date))`. A ranged
  passage stores the start in `date` and the end in `end_date`; every other entry leaves it
  null (a single-dated entry).
- `date_precision` stays orthogonal: it says how precise the anchor date is; `end_date`
  says whether the entry spans. A consumer may treat a null `end_date` as a single date.
- `13(14) août 2021` (a letter begun the 13th, finished the 14th) resolves to the start day
  (13) with no `end_date`; only explicit `X au Y` ranges get one.

**Alternatives Considered:**
- Start date + coarser precision (week/month) -> loses the exact end and fits badly
  (`1-23 nov` is neither a clean week nor a month).
- Start date, day precision (treat like `13(14)`) -> a 23-day span then looks identical to
  a single day.
- Hold the ~2 ranges out for manual entry -> avoids the model, but the author chose to
  represent them faithfully while the change is free.

**Consequences:**
- The 2 spanning passages are captured without losing the span; the "capture detail you
  cannot recover later" principle ([ADR-011]) holds.
- One nullable column to carry in `schema.sql`, the importer, and `database.md`; the range
  parser inherits the month/year of the left endpoint from the right.
- Trade-off: consumers that care about spans must read `end_date`; those that do not can
  ignore it.

---

### ADR-013: Backlog ingestion: Drive is the spine, prose first (2026-07-04)

**Context:**
- The backlog lives in two overlapping places: Word `.docx` in Google Drive (the fuller
  original, ~101 unique letters) and a Notion "Journals" template (a hand-curated but
  partial subset). The author had begun transferring Drive to Notion by hand, renumbering
  along the way. A strategy was needed before writing the importer: which source is
  authoritative, and how to avoid importing the same content twice.

**Decision:**
- **Drive is the spine** for entry bodies and dates. Drive letters carry their own French
  dates in-body, so Notion is not needed for dating.
- **Notion per-entry metadata is dropped.** Coverage is near-empty (emotions 0/87, tags 6%,
  people 64%, all re-derivable later by the classifier). Matching Notion to Drive to salvage
  it would be costly (the renumbering makes the `Lettre N.x` number an unreliable join key)
  for almost no gain.
- **Keep only the Notion-only tail:** entries dated >= 2025-11-01 in the Lettres journal (14
  letters typed straight into Notion). Drive prose ends 2025-08-16, so the two sources meet
  at a clean seam and no cross-source dedup is required. Recent Bingo/Abécédaire Notion pages
  are specials, excluded here.
- **First pass is prose only:** no people, emotions, tags, or structured specials (bingo,
  abécédaire, music tops, bucketlist; the "poésie" file is a compilation of other letters and
  is ignored). Later passes handle those.
- **Within-Drive duplicates** (byte-twin `(1)/(2)/(3)` downloads) are removed by hashing the
  body text, not by filename.
- **Date-less letters are held out, not guessed** (`entries.date` is NOT NULL): reported to a
  CSV for manual dating. Prose that appears before the first date header of a monthly file
  (often a continuation of the previous month's last entry) is held out the same way, never
  silently dropped.
- **Provenance is kept.** Each imported entry records its originating file or Notion page in
  the nullable `entries.source`, so the one-way import stays verifiable against the originals
  before they are retired ([ADR-004]). App-created entries leave it null.

**Alternatives Considered:**
- Notion as the spine -> its subset misses the untransferred majority and its bodies are no
  richer; only its dates and the Personnes list have value.
- Match Notion to Drive to merge metadata -> expensive fuzzy matching (renumbered, sometimes
  edited) for metadata that is 0 to 6% populated.
- Union both fully as separate entries and dedup by hand -> unnecessary once the seam is shown
  to be clean; the tail is only 14 entries.
- Infer missing dates from the filing numbers -> the numbering is "just filing"
  ([ingestion.md](ingestion.md)) and guessing dates corrupts a lifetime archive.

**Consequences:**
- One authoritative source for bodies, hand-work reused only for the recent tail, and no
  double-import (guaranteed by the date seam). ~1224 prose entries in pass 1; 8 held out;
  specials and people deferred.
- Trade-off: Notion's hand-tagged people are not reused now; the classifier re-derives people
  later. The Personnes list (75 people, de-aliased, with relationships) is noted for the
  deferred people pass.

---

### ADR-012: Themes: frozen, full-life, append-only, no `other` (2026-06-25)

**Context:**
- Seeding `data/seed/themes.csv` forced the question of what the theme list *is*. ADR-005
  framed it as a provisional starter set, bootstrapped from a corpus sample and then
  frozen, kept honest over time by versioned growth and an `other` escape hatch.
- Reviewing the starter set surfaced a different intent: the author would rather settle a
  stable, full-life set now, anticipating the whole arc of a life (including themes that
  may go unused for years or never), than discover it from an early, unrepresentative slice
  of writing. A stable axis set makes decade-over-decade aggregation trivially honest.
- The starter set also leaked across dimensions and within itself (an `emotions` theme
  duplicating the emotions dimension; `gratitude` already an emotion; `reflections` and
  `daily-life` describing a *mode* or a *significance level* rather than a subject; a fuzzy
  introspection cluster `identity`/`mindset`/`reflections`/`meaning` that co-fired).

**Decision:**
- **Definition (the gate).** A theme is an *aboutness*: a subject an entry is *about*.
  Not a mode of writing (`reflections`), not a significance level (`daily-life`), not a
  feeling (those are the emotions dimension, ADR-011). Each theme owns a slice no other theme
  or dimension owns. Every candidate must pass this test before entering the list.
- **Frozen meanings, append-only.** A theme's `slug` and meaning are immutable once set.
  A 2024 `health` tag must mean the same thing in 2044. The list may only grow by appending
  a genuinely new life-domain (tracked by `list_version`, per ADR-005's schema); existing
  meanings are never redrawn or deleted. Definitions may be *worded* more clearly without
  changing scope.
- **Full-life, anticipated now.** The list is built for a whole life up front rather than
  bootstrapped from a corpus sample. Unused themes are acceptable and expected; mis-bounded ones are not,
  because the freeze makes a bad boundary permanent.
- **No `other`.** ADR-005's uncategorized escape hatch is dropped. An entry that fits no theme
  simply carries no theme: `entry_themes` is many-to-many, so zero rows is the natural,
  honest representation. Consequence for the pipeline: the classifier and its confidence
  gating must be allowed to emit *zero* themes and must never be built to force a pick.
- **The list (21).** `identity`, `meaning`, `spirituality`, `family`, `parenting`, `love`,
  `sexuality`, `friendship`, `society`, `work`, `direction`, `learning`, `creativity`,
  `leisure`, `health`, `body`, `habits`, `finance`, `travel`, `home`, `grief`. Cross-dimension
  slug overlap is allowed: `grief` is both a theme and an nsfw tag because nsfw is an orthogonal
  *sensitivity* axis rather than a competing subject.

**Alternatives Considered:**
- Bootstrap-then-freeze with versioned growth + `other` (ADR-005 as written) -> Defers the
  hard boundary work to an early, unrepresentative corpus slice and leans on `other` as a
  crutch; the author prefers to anticipate the full arc now and let unfitting entries stay
  untagged.
- A free-form / open theme list -> The typo/synonym rot ADR-005 exists to prevent.
- Keep the fuzzy starter set (`emotions`, `reflections`, `daily-life`, the introspection four)
  -> Themes that co-fire on most entries aggregate to noise; they fail the aboutness gate.

**Consequences:**
- One stable, full-life axis set; decade-over-decade theme charts are honest by construction.
- The aboutness gate + frozen meanings keep boundaries clean and comparable for a lifetime.
- This amends ADR-005: bootstrap-then-freeze, versioned-growth-as-the-plan, and the `other`
  hatch are superseded by frozen/append-only/full-life/no-`other`. ADR-005's mechanics that
  still hold (closed list, `list_version`, CSV-is-source / DB-is-runtime-copy) are unchanged.
- Trade-off: the author must get the full-life boundaries right *now*; a missing domain can
  only be appended later, never carved out of an existing theme's frozen meaning.

---

### ADR-011: Emotions  2-D mood meter, 9-family wheel, and "love is not an emotion" (2026-06-25)

**Context:**
- Seeding `data/seed/emotions.csv` forced three latent decisions: how rich the discrete
  emotion list should be, how it feeds the "emotional climate" graph, and where the line
  sits between an *emotion* and the other entry dimensions (people, themes, events).
- ADR-005 anchored each emotion with valence only and explicitly dropped arousal.
  That collapses calm-vs-energetic states at the same valence (`serenity` ≈ `excitement`
  on the curve) and, grouped by Ekman-style families, renders the *pleasant* side as one
  flat block against a finely-split *unpleasant* side (Ekman is negativity-biased).
- The seed list also mislabeled `love` as an emotion ("Amour"), conflating three
  different things that already have homes in the schema.

**Decision:**
- **2-D mood meter.** Add an `arousal REAL` (0..1, calm..activated) column alongside
  `valence` (−1..+1). The pair places each emotion on the valence×arousal plane; the
  continuous curve still uses `valence` × per-entry `intensity`, with `arousal` available
  for energy-aware views. (Done now, pre-data, per ADR-010; post-cutover it would be a
  migration.)
- **35 emotions in a 9-family wheel.** Slugs are English nouns (matching the doc's own
  examples and resolving an adjective/noun drift); `name`/`definition` stay French-first
  (ADR-007). A `family TEXT` column groups the 35 into 9 families: `joy`, `tenderness`,
  `serenity` (3 pleasant) · `sadness`, `anger`, `fear`, `disgust`, `shame` (5 unpleasant) ·
  `surprise` (neutral), each named after its prototype emotion. Splitting the pleasant
  side into three matches the unpleasant side's granularity, so good times are as legible
  as hard times on a grouped chart.
- **"Love is not an emotion."** Drop `love`/Amour as both an emotion and a family. Its three
  senses are routed to where they belong: the *felt warmth* is the `affection` emotion
  (family `tenderness`); the *bond* is `people` + relationship_type; love *as a subject* is
  the existing `love` theme (`themes.csv`). The same "who / felt / about / which
  happening" test keeps people, emotions, themes, and events from bleeding into each other
  (notably: "Suisse 2026" is an event, "voyage" is a theme; no free-form tags).
- Values (valence/arousal/family) are re-tunable: `seed_labels.py` upserts them by `slug`
  on every re-seed, so only slug changes are costly.

**Alternatives Considered:**
- Keep valence-only (ADR-005) -> Loses the calm/energetic axis permanently after data
  exists; the cheap moment to add arousal is now.
- A literal textbook wheel (Plutchik-8 / Ekman-6) -> `trust`/`disgust`/`anticipation` fit a
  French memoir poorly, and both lump `love` into `joy`; love/connection is a primary
  storyline of an autobiography and earns its own family register.
- Shrink the list to ~10 "big" emotions for a simpler graph -> Permanently lossy; you can
  aggregate 35→9 for display but never recover `nostalgia`/`regret`/`relief` after the fact.
  Capture granularity ≠ display granularity.
- A free-form `tags` dimension -> Reintroduces the typo/synonym rot that closed `themes` +
  dated `events` exist to prevent.

**Consequences:**
- The climate graph gains an energy axis and a balanced family rollup; the discrete list is
  rich enough for a memoir without flattening the positive side.
- Clean dimensional boundaries: each fact (who / felt / about / which happening) has exactly
  one home, so the classifier and the author aren't choosing between overlapping systems.
- Trade-off: the classifier must emit `arousal` as well as `valence`, and the family
  taxonomy is one more curated column to keep coherent as the list evolves.

---

### ADR-010: Deferred schema migrations with a first-ingestion cutover (2026-06-24)

**Context:**
- The schema will evolve over a lifetime. While `life.db` holds no real data, the cheapest
  way to change it is to edit `schema.sql` and rebuild. Once it holds irreplaceable
  entries, that's destructive: changes must be additive and applied in place.

**Decision:**
- `schema.sql` is the authoritative baseline; the DB stamps `PRAGMA user_version = 1`.
- **Pre-data phase (now):** edit `schema.sql` freely and rebuild with `build_db --force`.
- **Cutover:** the first real ingestion of entries freezes `schema.sql`. From then on,
  schema changes are additive, numbered SQL migrations (`migrations/0002_*.sql`, …),
  each bumping `user_version`; `schema.sql` is never destructively edited again.
- No migration framework is adopted yet (Alembic is SQLAlchemy-oriented; we use raw
  `sqlite3`). A lightweight runner is added at cutover.

**Alternatives Considered:**
- Stand up migrations from day one -> Structure before it's needed; slows iteration while
  the schema is still churning and there's nothing to lose.
- Alembic now -> Heavy ORM dependency for a raw-`sqlite3` project.

**Consequences:**
- Fast iteration now, safety later, with a clearly defined switch-over moment.
- Trade-off: the discipline of "never `--force` once data exists" must be remembered
  (the `build_db` refuse-unless-`--force` guard backs it up).

---

### ADR-009: Repository layout: one `lifebook` Python package as the sole DB writer (2026-06-24)

**Context:**
- Code is starting. ADR-006 establishes that Python is the only language that writes
  `life.db` and that the curation app's FastAPI backend *reuses* the processing layer.
  The layout should encode that, not fight it.

**Decision:**
- Use the src-layout: `pyproject.toml` at the repo root, and `src/` holding *only*
  the importable Python package. A single package `lifebook` is the only DB writer;
  its subpackages are `db` (schema, build/seed, the shared `connect()` helper), and
  (built later) `ingest`, `nlp`, `stats`, `export`, `api` (the FastAPI backend, *inside*
  the package so it imports the pipeline directly).
- The React/TipTap frontend is the one separate, non-Python piece: `frontend/` at
  the repo root.
- Non-code assets live at the repo root, not under `src/`: seed CSVs in `data/seed/`
  (Git source of truth, ADR-005); all gitignored machine-local private state in
  `data/local/` (ADR-004): the `config.toml` inputs and `life.db` itself
  (`data/local/life.db`).
- Layout sketch:
  ```
  repo/  pyproject.toml  README.md  .gitignore  docs/
         src/lifebook/{db,ingest,nlp,stats,export,api}/
         frontend/   data/{seed,local}/   tests/
  ```

**Why src-layout (vs flat-layout):** keeping `src/` thin (package-only) means the code
can't be imported from the working directory by accident (tests run against the
*installed* package, catching packaging mistakes), and it avoids the repo-dir/package
name repetition (`lifebook/lifebook/`) that a flat layout would produce.

**Alternatives Considered:**
- Split `db/` + `pipeline/` + `app/{backend,frontend}` -> The backend reuses the
  pipeline, so it would import across sibling top-level dirs; a single package is cleaner
  and avoids interpreter/import friction for a Python newcomer.
- Flat `src/` (schema/scripts/data) -> Fine short-term but doesn't express the
  package-vs-frontend boundary that's coming.

**Consequences:**
- Clean imports, one `pyproject.toml`, one DB-writing package; the only language boundary
  (Python vs JS) is also the only directory boundary that matters.
- Trade-off: a tighter coupling of backend and pipeline (by design, they share the DB
  layer).

---

### ADR-008: Python tooling: uv, pinned to Python 3.12 (2026-06-24)

**Context:**
- The project needs a reproducible Python environment, runnable by someone new to Python,
  on a Windows machine where `python` resolves to a stray 2.7 and only `py` finds 3.11.
  That interpreter ambiguity is the classic beginner foot-gun.

**Decision:**
- Use uv for environment + dependency management. uv pins the interpreter
  (`.python-version`) and `uv run` always uses the right one: no venv-activation ritual,
  no "which Python" confusion. It writes standard `pyproject.toml`, so there's no lock-in.
- Pin Python 3.12 (uv fetches it): modern, with mature wheel support across the
  spaCy / transformers / numpy stack the NLP steps will need, avoiding 3.13's bleeding-edge
  wheel gaps.
- The data-layer foundation has no runtime dependencies (stdlib `sqlite3` / `csv` /
  `tomllib`); `pytest` is a dev dependency-group only.

**Alternatives Considered:**
- venv + pip -> Works and is universal, but re-exposes the interpreter-ambiguity foot-gun
  this machine already demonstrates.
- Poetry -> Heavier, slower resolver; uv covers the same ground faster.
- Python 3.11 (already installed) / 3.13 (newest) -> 3.11 ages out sooner; 3.13 risks
  ML-wheel gaps when the NLP work starts.

**Consequences:**
- One fast tool handles interpreter, venv, and deps reproducibly; trivial onboarding
  (`uv sync`, `uv run …`).
- Trade-off: uv is a newer tool, so some web answers still assume pip, mitigated by uv's
  standard-file output and pip-compatibility.

---

### ADR-007: Content is French: tooling must be French-first (2026-06-24)

**Context:**
- The writings are in French (and so are book features like *mot de l'année* and
  *abécédaire*). Defaults in most NLP/LLM tooling are English-first, which would
  silently degrade quality on French text.

**Decision:**
- Treat French as the primary content language end-to-end:
  - **Ingestion** parses French date formats (e.g. *12 janvier 2018*) and French text.
  - **NLP** uses French-capable models, e.g. spaCy `fr_core_news_*` for person/NER,
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
- The "living system for decades" vision needs a day-to-day way to add new entries;
  the snapshot-from-data model said nothing about intake.
- The analysis pipeline produces *suggestions* (themes, emotions, alias matches) that a
  human must confirm; there was no place for that human-in-the-loop review.
- The data is private and must not leave the machine ([ADR-005], privacy principle).

**Decision:**
- Build a local-first app that is both the capture tool (write/edit entries) and
  the curation hub (review and confirm pipeline suggestions).
- **Stack:** React + TipTap frontend (Google-Docs-style rich editor) over a thin
  local FastAPI backend that reads/writes `life.db`. Runs on localhost only.
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
- The value of the analysis layer is longitudinal aggregation: heatmaps, "themes
  over the decade," evolution curves. That requires labels that are *comparable and
  countable across ten years*.
- Free-form theme/emotion extraction produces inconsistent labels (e.g. `career
  anxiety` one year, `professional stress` another) that cannot be aggregated, and
  cannot be evaluated for accuracy.
- The content is intimate and NSFW-flagged; ownership and privacy are core principles.

**Decision:**
- Classify entries against a closed, fixed list of themes and emotions rather than
  extracting free-form labels. (The lists are flat controlled vocabularies, not a
  hierarchy, hence "label lists," not "taxonomy.")
- Rules:
  - **Multi-label** with per-label `confidence` / `intensity` (schema already supports
    this); results are *suggestions* gated by confidence and spot-reviewed.
  - Keep an `other` / uncategorized escape hatch so the model is never forced to
    mislabel; review `other` periodically to grow the list.
  - **Version the list** by recording which `list_version` each tag was produced under,
    so additions in a later volume can be re-tagged honestly (supports
    "reproducible for any date range").
  - **Themes** are bootstrapped from the corpus (one open/clustering pass on a sample
    to discover real recurring themes), then frozen into the list rather than invented from
    a generic template.
  - **Emotions** use a small discrete set, plus a per-emotion valence anchor
    (pleasant ↔ unpleasant) so a continuous "emotional climate" curve can be derived
    alongside the discrete labels. (Arousal was considered and dropped as
    lower-value; superseded by [ADR-011](#adr-011-emotions--2-d-mood-meter-9-family-wheel-and-love-is-not-an-emotion-2026-06-25), which adds it.)
- Tooling: a local open-weight LLM fed the list (returning labels +
  confidence + a supporting quote), optionally with an embeddings/similarity first
  pass as a cheap cross-check. Run locally so private content never leaves the machine.
  - **Build-time vs. run-time:** cloud LLMs (including Claude Code) are fine for
    *building* the pipeline: writing the code, schema, and seed scripts, none of
    which contain private entries. But the run-time classifier that reads the
    entries must be local (e.g. Ollama / llama.cpp); never send journal text to a
    cloud API. The stated bar is "data doesn't leave the machine," which is stricter
    than "won't be trained on," so cloud fails it regardless of provider policy.

**Where the lists live (source vs. runtime copy):**
- **Source of truth (flat CSV files in Git):** `data/seed/themes.csv` and
  `data/seed/emotions.csv`. These are what you hand-edit, diff, and review. Columns:
  `slug, name, definition, status` (themes) and the same plus `valence`
  (emotions). `definition` is the gloss that drives the embeddings / LLM prompt;
  `status` is `active | deprecated`.
- **Runtime copy (the `themes` / `emotions` tables in `life.db`):** seeded from the
  CSVs by a script (`seed_labels.py`), never hand-edited. These supply the `id`s that
  `entry_themes` / `entry_emotions` reference, and enable SQL aggregation.
- Sync is insert-or-update by `slug`; rows that already have tags pointing at them are
  marked `deprecated`, never deleted.
- CSV chosen over YAML/JSON: the data is tabular, CSV opens in anything forever, diffs
  cleanly line-by-line, needs no dependency or parser quirks (YAML's whitespace and
  type-coercion footguns cut against durability).
- **`nsfw_tags` follows the same pattern**: it's also a closed controlled list, so it
  lives in `data/seed/nsfw_tags.csv` and is seeded the same way (the *level* `0–3` is a
  separate intensity score on the entry; see [database.md](database.md#nsfw)).
- **Not everything controlled is seeded.** The seed-from-Git pattern is for lists the
  *pipeline/classifier reads* and must version. Purely editorial lookup lists with
  no classifier behind them, e.g. `top_categories`, are managed in the app
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
- `life.db` is the *concentrated* archive: consolidated, analyzed, sensitivity-tagged.
  It is far more sensitive than the scattered source docs, and the privacy principle
  (and ADR-005) says private content must not leave the machine in the clear.
- Reality: the current source writings already live in Google Drive and Notion. That
  cloud exposure is the past; the consolidated DB is what's worth protecting going
  forward.

**Decision:**
- Keep a minimum of 3 copies: local (primary computer), cloud (Google Drive / Dropbox
  / iCloud), and a cold offline copy (external drive, annual archive).
- **Encrypt any copy that leaves the machine**: the cloud copy is an encrypted
  `life.db` archive, never plaintext.
- After ingestion, the original Word/Notion sources are retired (archived, then
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
  (lose the key, lose the backup); the key itself needs its own safe storage.

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
- Trade-off: concurrency and very large blobs are not SQLite strengths, so when media
  is added later, the files will live outside the DB (only references stored).
