# AI Session Records

Track AI-assisted development sessions with summaries, successes, challenges, and friction points. Review this before similar sessions to learn from past experiences.

## Format

### YYYY-MM-DD - Session Title

**What We Worked On:**
- Main objectives and tasks completed
- Features implemented or problems solved

**What Went Well:**
- Successful approaches and techniques
- Effective collaboration patterns
- Quick wins

**What Could We Do Better:**
- Areas for improvement
- Misunderstandings or miscommunications
- Process inefficiencies

**Friction Points:**
- Technical blockers encountered
- Communication challenges
- Tool or workflow limitations

**Key Takeaways:**
- Lessons learned for future sessions
- Best practices identified

---

<!-- Add new entries below this line, newest first -->

### 2026-06-25 - Themes seed: define the gate, freeze the list, full-life coverage

**What We Worked On:**
- Reviewed and redesigned `data/seed/themes.csv` before sealing it, grilling each decision
  one at a time. Net path: a 22-row provisional set down to 21 frozen, full-life themes.
- **Defined the gate first (the load-bearing move):** a theme is an aboutness, a subject
  an entry is *about*. It is not a mode of writing, a significance level, or a feeling. This
  test drove every cut and add.
- **Cut the leaks the gate exposes:** cross-dimension duplicates `emotions` and `gratitude`
  (`gratitude` is already an emotion); non-aboutness pseudo-themes `reflections` (a writing
  *mode*) and `daily-life` (a *significance level*, the worst offender, which would co-fire on most
  entries). Collapsed the fuzzy introspection cluster `identity`/`mindset`/`reflections`/
  `meaning` → `identity` + `meaning`.
- **Policy reversal → [ADR-012]:** frozen meanings, append-only, full-life-anticipated, no
  `other`. This amends ADR-005 (drops bootstrap-from-corpus-then-freeze, versioned-growth-
  as-the-plan, and the `other` escape hatch). Consequence recorded for the pipeline: the
  classifier must be allowed to emit zero themes and never forced to pick.
- **Full-life coverage:** added `spirituality`, `parenting`, `sexuality`, `society`, `leisure`,
  `body`; re-scoped `family` (→ origins/kin) and `love` (→ couple) so `parenting` and
  `sexuality` get clean edges.
- **`ambition` → `direction`/Direction de vie:** renamed to shed the success/performance
  connotation and absorb life pivots. Rejected `projects` (would double-tag every domain theme)
  and a standalone `transitions` theme (significance-level cousin of `daily-life`).
- **`society` broadened** from civic-participation to also own the outward gaze (worldview,
  social critique, ideologies, collective identity).
- **Boundary/wording fixes caught on re-reading:** narrowed `grief` off "transition/changement"
  creep; depluralized circular `identity`/`family` defs; split the `health`/`habits` seam
  ("hygiène de vie" → discipline); and, after the rename, removed "direction de vie" from the
  `meaning` def, which had started revendicating the new `direction` theme's territory.
- **Slug audit:** 21 unique, convention-consistent (lowercase single words, no separators);
  only `grief` collides with an `nsfw_tags` slug, which is intentional and documented (orthogonal axes,
  separate tables).
- **Applied across 4 files:** rewrote `themes.csv`, wrote ADR-012, trimmed the "provisional/
  bootstrap" framing out of `data/seed/README.md`, and in `improvements.md` superseded the
  corpus-bootstrap task + updated the classifier task (allow zero labels).

**What Went Well:**
- Writing the *definition of a theme* before touching the list turned vague "feels redundant"
  intuitions into a sharp, repeatable test. The aboutness gate did the actual work.
- Cross-checking each label against the *other* dimensions caught the duplicates fast
  (`gratitude` already an emotion; `grief` shared with nsfw is fine because nsfw is an
  orthogonal sensitivity axis).

**What Could We Do Better:**
- Same root cause as the emotions session: the provisional set carried errors (`emotions`,
  `gratitude`, `reflections`, `daily-life`) precisely because it was drafted before a
  definition existed and without cross-checking the other dimensions. Define the gate, then
  draft the list, in that order.

**Friction Points:**
- Scope/wording collisions only surfaced on a final re-read: the `ambition → direction` rename
  silently invalidated the `meaning` def, which still said "direction de vie." A rename needs a
  follow-up pass over every *other* theme's definition for the old term.

**Key Takeaways:**
- A theme is an aboutness. It is not a mode, a significance level, or a feeling. Cross-dimension
  slug overlap is allowed because emotions/nsfw are orthogonal axes, separate from competing subjects.
- Frozen meanings, append-only, and no `other` together mean the pipeline must support an entry with
  *no* theme (the m2m join makes zero rows the honest representation) and must never force a pick.
- For a lifetime archive, freeze the *meaning* and not the *size*: anticipate the full arc now, let
  unused themes sit, and only ever append a genuinely new life-domain.

### 2026-06-25 - Emotions seed: 2-D mood meter, 9-family wheel, "love is not an emotion"

**What We Worked On:**
- Reviewed and redesigned `data/seed/emotions.csv` before its first seed. Grilled every
  decision one at a time ([ADR-011]).
- **Vocabulary** → **35 emotions** (from a 32-entry draft): pruned trait-like entries
  (`créativité`, `bienveillance`) and redundant near-synonyms (`appreciation`, `power`,
  `frustration`, `exclusion`); added memoir-relevant gaps (`nostalgia`, `pride`, `relief`,
  `serenity`, `regret`, `awe`, `surprise`) and a `disgust`/`contempt` pair.
- **Slugs** → English nouns (resolving an adjective/noun drift vs the doc's examples);
  `name`/`definition` stay French-first (ADR-007).
- **2-D mood meter:** added `arousal` (0..1) alongside `valence`, reversing ADR-005's
  valence-only choice (the cheap, pre-data moment per ADR-010). Valence recalibrated
  symmetric, full ±1.0 used (`affection` +1.0 ↔ `powerlessness` −1.0).
- **9-family wheel** via a new `family` column. Pleasant split 3 ways (Joie / Tendresse /
  Sérénité) to match the 5 unpleasant families, avoiding Ekman's negativity bias on a
  grouped chart.
- **Dimensional clean-up:** `love`/Amour removed as an emotion. Its senses route to where
  they belong (felt warmth = `affection`; the bond = `people`+relationship_type; love-as-
  subject = the existing `love` **theme**). Confirmed "Suisse 2026" is an **event** and
  "voyage" a **theme**, with no free-form tags.
- **Applied across 6 files:** rewrote the CSV, added `arousal`+`family` to `schema.sql`,
  extended `seed_labels.py`, updated `database.md`, wrote ADR-011 (+ superseded note on
  ADR-005), and refreshed the stale `test_db_foundation.py` assertions. Full suite green.

**What Went Well:**
- One-decision-at-a-time grilling kept a wide design space (vocabulary, slugs, scale,
  families, balance) tractable and surfaced the real architectural reversal (arousal) and
  the conceptual error (love-as-emotion) deliberately rather than by accident.
- The "who / felt / about / which-happening" test gave a reusable rule for keeping people,
  emotions, themes, and events from bleeding into each other.

**What Could We Do Better:**
- The author had to catch the love/emotion conflation. The first family proposals carried
  "Amour" as a family even though `love` already existed as a theme. Should cross-check a
  new label against the *other* dimensions' existing lists before proposing it.

**Friction Points:**
- The seed tests were already stale (asserted 6 emotions vs a 32-row CSV) and `themes.csv`
  had independently grown 7 → 22 rows outside the session. Both tripped the suite, so
  the counts needed re-syncing. A seed-count test pinned to a hand-written number drifts
  every time a CSV changes; consider deriving the expected count from the CSV instead.

**Key Takeaways:**
- **Capture granularity ≠ display granularity:** keep the rich 35-label list for tagging,
  roll up to 9 families only for charts. You can aggregate up but never recover detail you
  didn't capture, so resist shrinking the *list* to fix a *graph*.
- Only **slugs** are costly to change post-seed (deprecate+insert by `slug`); `name`,
  `valence`, `arousal`, `family` are re-tunable `UPDATE`s on every re-seed.
- A label is only an *emotion* if it's a momentary felt state with an intensity. Bonds,
  subjects, and traits belong to other dimensions.

### 2026-06-24 - Project setup: the data-layer foundation (first code)

**What We Worked On:**
- First code in the repo (previously docs-only). Built the **reproducible `life.db`
  foundation**, the prerequisite for every other client (app, pipeline, publication).
- **Tooling & layout:** uv + Python 3.12 ([ADR-008]); src-layout, with `pyproject.toml` at
  the repo root, `src/lifebook/` as the sole DB-writing package, `frontend/` + `data/` +
  `tests/` at the root ([ADR-009]).
- **`schema.sql`**: all 28 tables from database.md as production-grade SQLite DDL:
  `AUTOINCREMENT` on every id, `created_at`/`updated_at` + `AFTER UPDATE` trigger on
  every table, TEXT ISO-8601 dates with a `GLOB` shape check, FK `ON DELETE`
  cascade/restrict rules, indexes, `PRAGMA user_version = 1`, inline seeds for
  `entry_types` + `relationship_types`.
- **Scripts (stdlib only):** `db.connect()` helper (enables `foreign_keys`), `build_db`
  (refuse-unless-`--force`), `seed_labels` (CSV-authoritative upsert + deprecate/
  reactivate), `seed_config` (reads gitignored `data/local/config.toml`).
- **Seed CSVs** (French names/definitions, English slugs) for themes/emotions/nsfw_tags;
  provisional emotion valences.
- **pytest** smoke test (9 tests) + documented migrations cutover ([ADR-010]); synced
  database.md and README.

**What Went Well:**
- Grilling out every schema decision *before* coding (id reuse, audit columns, FK delete
  rules, date storage, status semantics) meant the DDL was written once, deliberately.
- All-temp-DB tests let the suite run without touching the real `life.db`.

**Friction Points:**
- **GLOB vs LIKE wildcards:** first wrote the date check as `GLOB '____-__-__'`; GLOB uses
  `?`/`*` (not `_`/`%`), so it rejected valid dates. Fixed to `GLOB '????-??-??'`. (Logged
  in bugs.md.)

**Key Takeaways:**
- `connect()` centralizing `PRAGMA foreign_keys = ON` matters. FK enforcement is
  per-connection in SQLite and silently off otherwise.
- The build's refuse-unless-`--force` guard is the practical backstop for the ADR-010
  "never destroy real data" rule.

### 2026-06-24 - Location & map module

**What We Worked On:**
- Decided `events` tags aren't enough for a map (no coordinates, too coarse). Added a
  proper geographic dimension:
  - **`places`** table (canonical, `id`, `name`, `lat`, `lng`, optional `kind`),
    author-managed like `people`, not Git-seeded.
  - **`entries.place_id`**: where you were for that entry (one place; nullable).
  - Trip/year/whole-span maps are **derived by filtering** (a trip's map = places of the
    entries tagged with that event). No extra link tables, consistent with the atomic
    rule.
- Added the **map module** to the app scope (pick/confirm location) and a **Places / map**
  cartography section to product.md. Map libs (Leaflet/MapLibre) noted in references.

**Assumptions to confirm:**
- One place per entry (single `place_id`, not a multi-place join).
- A "home" default isn't modeled yet (null = home/unknown); could add `config` home later.

**Key Takeaways:**
- Same pattern again: put the atomic fact on the entry (`place_id`), let groupings
  (trips, years) emerge by filtering.

### 2026-06-24 - English slugs, author_birthdate, events become a tag

**What We Worked On:**
- **English slugs everywhere** (display labels stay French, app-side): entry type
  `fete` → `birthday_review`; tables `abecedaires`/`abecedaire_items` →
  `alphabets`/`alphabet_items`. Other slugs already English.
- **`config.author_dob` → `author_birthdate`** across all docs.
- **Dropped the `event` entry type**, replaced with an **`events` tag dimension**:
  `events` (id, name, optional start/end dates) + `entry_events` join. Author-managed in
  the app (select-or-add), not seeded, not classifier-driven, French names like
  *Suisse 2024* / *Espagne 2016*. It groups entries across time (a trip/place), which a
  theme wouldn't. Yearly "notable events" now = the events tagged that year (dropped
  `notable_events_json`).
- Swept product (double-temporality table, new "Named events / trips" section),
  ingestion (classify step), vision into line.

**Key Takeaways:**
- Three tag/grouping dimensions now, by origin: **themes/emotions** (NLP, Git-seeded),
  **people** and **events** (author-managed instances), and **nsfw_tags** (Git-seeded,
  sensitivity). Events are the new "happening/trip" grouping.

### 2026-06-24 - Renamed to Lifebook; real content model from the Word/Notion transfer

**What We Worked On:**
- **Naming:** system is now **Lifebook** (matches the git repo). The book is a
  **volume** = a chosen date range; cadence (decade / 5-year / yearly) is undecided.
  Swept "Décade"/"decade" across README, brief, CLAUDE, vision, product, architecture.
- **Decade out of `config`:** a volume is an app/export `date_range` filter, not stored.
  `config` now holds only `author_dob`. "Reproducible by decade" → "for any date range".
- **Atomic rule made explicit:** one entry = one date; multi-dated Word passages split
  into one entry each; grouping is by filter. Added `date_precision` (day/week/month/
  year) and `title` to `entries`.
- **Real content types captured** from the actual transfer:
  - `entries` types: `journal` (Lettres), `fete` (year-in-review by age, replacing the
    `birthday_reviews` table), `fun_fact`, `prompt` (title=Q, content=A), `event`.
  - New structured tables: `books` + `book_citations`, `abecedaires` + `abecedaire_items`,
    `bingos` + `bingo_cells`, `bucketlist_items` (running list, history derived).
- Updated product.md content layers, ingestion (two source shapes, split rule, precision,
  numbering-is-filing) to match.

**Assumptions to confirm:**
- Collapsing `birthday_reviews` into `fete` entries.
- Structured artifacts (books/abécédaire/bingo/bucketlist) are *not* run through
  people/themes/emotions analysis.
- `bucketlist` is one global running list (not per volume).

**Key Takeaways:**
- The atomic "one entry per date, group by filter" rule is the backbone. The author's
  own Word numbering scheme is filing, deliberately not modeled.

### 2026-06-24 - Top categories: app-managed, not Git-seeded

**What We Worked On:**
- Decided top-list categories are a small **app-managed** lookup: a select-or-add field,
  not a Git seed CSV.
- Schema: added `top_categories` (id, slug, name); `top_lists.category` (free text) →
  `category_id` FK. Stable id lets a category aggregate across years even if renamed.
- Recorded the distinguishing rule (in database.md, architecture.md, ADR-005):
  **lists the classifier reads** (themes / emotions / nsfw_tags) are seeded from Git
  and versioned; **purely editorial lists** (top_categories) live in the DB and are
  managed in the app, like people / aliases.

**Key Takeaways:**
- "Controlled list" isn't one pattern. There are two, split by whether the pipeline
  reads it. That distinction now has a written home.

### 2026-06-24 - "Music" generalized to yearly tops

**What We Worked On:**
- Clarified that the "yearly music Top 10" is really a general **yearly tops** feature:
  varied categories per year (songs, games by hours, books, reddit, …) and varied N
  (top 10 / 5 / 3).
- Replaced `yearly_reviews.top_songs_json` with two tables: `top_lists`
  (id, year, category, title) and `top_list_items` (id, list_id, rank, label, detail).
  Typed-but-flexible: any category, any length, queryable across the decade.
- Generalized the book sections accordingly (product.md "Yearly tops" + cartography
  "Tops over time"); swept brief/architecture/ingestion wording.

**Resolved (was deferred):**
- The earlier "music data source (Spotify/Last.fm)" open item is moot. The tops are
  written in the Word docs, so they come in through normal ingestion; exact parsing
  TBD when we see the files.

**Key Takeaways:**
- Normalized over a JSON blob because the cartography wants to trace a single category
  (music, games, …) across years, which needs queryable rows rather than opaque JSON.

### 2026-06-24 - Config table, French ADR, events & numbering

**What We Worked On:**
- Closed three gaps from a second structure review.
- **`config` table** added to `database.md` (single row: `author_dob`, decade
  bounds), which unblocks personal time / age, which had no birthdate to compute from.
- **ADR-007** added: content is French; tooling is French-first (spaCy `fr_core_news`,
  French dates, French LLM prompts; `slug` stays neutral, `name`/`definition` French).
- **Events & numbering** clarified: notable events are `event`-type entries, curated
  per year via `yearly_reviews.notable_events_json`; the book's entry number is a
  render-time 1..N chronological sequence, not the stable DB `id`.
- Swept French note into `ingestion.md`, `references.md`, `CLAUDE.md`.

**Decided not to capture (for now):**
- Music data source (Spotify/Last.fm), deferred by choice.

**Key Takeaways:**
- The biggest catch was conceptual rather than cosmetic: half the "two clocks" idea was
  uncomputable because no birthdate was stored anywhere.

### 2026-06-24 - Structure gap-review and the curation app

**What We Worked On:**
- Reviewed the docs for gaps and resolved a privacy contradiction.
- **ADR-004 rewritten:** encrypt cloud backups of `life.db`; retire the Word/Notion
  source docs after ingestion (DB becomes source of truth).
- **ADR-006 added:** local-first curation app, React + TipTap over a local FastAPI
  backend; capture + human-in-the-loop review; Python stays the only DB writer.
- **New `ingestion.md`:** import path for the Word-in-Google-Drive + Notion backlog,
  entry delimiting, date parsing, people/alias resolution, source retirement.
- **Schema baselined** in `database.md`: `entries.nsfw_level` (graded, replaces the
  boolean) from the start; removed the `media` table (out of scope for now).
- Updated architecture (clients-of-`life.db` model + "who writes what"), brief,
  README, CLAUDE, vision, product for consistency.
- Deferred: publication export mechanics (TBD at production time) and the run/setup
  runbook (when coding starts). Removed the now-baseline "graded NSFW" improvement.

**What Went Well:**
- The "who writes what" rule kept the second writer (the app) from muddying the
  single-source-of-truth principle.
- Resolving the cloud-backup contradiction tied ADR-004 back to ADR-005's privacy bar.

**Key Takeaways:**
- The app is best framed as the *curation hub* rather than just an editor. It's where the
  pipeline's suggestions become confirmed data.

### 2026-06-24 - Structuring the source brief into the docs system

**What We Worked On:**
- Took the raw source brief (a French source file, since removed) and distributed it
  across the documentation structure.
- Filled the empty/template docs: vision, references, decisions (ADRs), and improvements.
- Added new files to give the material a coherent home:
  - `00_briefing/editorial-concept.md`: the book's structure and content layers.
  - `01_building/architecture.md`: the three-layer system + workflow + backups.
  - `01_building/data-model.md`: the full `life.db` schema reference.
  - Root `README.md` and `CLAUDE.md` as entry points / AI guidance.
- Later trimmed the structure: folded the design principles into `vision.md` and the
  personas into `brief.md`, deleting the separate `design/` and `personas/` folders.

**What Went Well:**
- The source split cleanly along the dev-journal structure: vision → inspirations,
  architecture choices → ADRs, schema → its own reference, content spec → editorial.
- Cross-linked the docs so each concept points to its rationale and its schema.

**What Could We Do Better:**
- Meta-docs were written in English while the source is French; revisit if the author
  prefers French throughout.

**Friction Points:**
- `brief.md` initially contained a spec from an unrelated project; rewrote it as the
  actual Décade project brief and removed the stale cross-references.

**Key Takeaways:**
- The non-negotiable thread across every doc: data is the source of truth, and the
  renderer is replaceable. Everything else (durability, ownership, reproducibility)
  follows from that.
