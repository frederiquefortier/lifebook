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

### 2026-06-24 - Location & map module

**What We Worked On:**
- Decided `events` tags aren't enough for a map (no coordinates, too coarse). Added a
  proper geographic dimension:
  - **`places`** table (canonical, `id`, `name`, `lat`, `lng`, optional `kind`) —
    author-managed like `people`, not Git-seeded.
  - **`entries.place_id`** — where you were for that entry (one place; nullable).
  - Trip/year/whole-span maps are **derived by filtering** (a trip's map = places of the
    entries tagged with that event) — no extra link tables, consistent with the atomic
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
- **Dropped the `event` entry type** — replaced with an **`events` tag dimension**:
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
  - `entries` types: `journal` (Lettres), `fete` (year-in-review by age — replaces the
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
- The atomic "one entry per date, group by filter" rule is the backbone — the author's
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
- "Controlled list" isn't one pattern — there are two, split by whether the pipeline
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
- The earlier "music data source (Spotify/Last.fm)" open item is moot — the tops are
  written in the Word docs, so they come in through normal ingestion; exact parsing
  TBD when we see the files.

**Key Takeaways:**
- Normalized over a JSON blob because the cartography wants to trace a single category
  (music, games, …) across years — that needs queryable rows, not opaque JSON.

### 2026-06-24 - Config table, French ADR, events & numbering

**What We Worked On:**
- Closed three gaps from a second structure review.
- **`config` table** added to `database.md` (single row: `author_dob`, decade
  bounds) — unblocks personal time / age, which had no birthdate to compute from.
- **ADR-007** added: content is French; tooling is French-first (spaCy `fr_core_news`,
  French dates, French LLM prompts; `slug` stays neutral, `name`/`definition` French).
- **Events & numbering** clarified: notable events are `event`-type entries, curated
  per year via `yearly_reviews.notable_events_json`; the book's entry number is a
  render-time 1..N chronological sequence, not the stable DB `id`.
- Swept French note into `ingestion.md`, `references.md`, `CLAUDE.md`.

**Decided not to capture (for now):**
- Music data source (Spotify/Last.fm) — deferred by choice.

**Key Takeaways:**
- The biggest catch was conceptual, not cosmetic: half the "two clocks" idea was
  uncomputable because no birthdate was stored anywhere.

### 2026-06-24 - Structure gap-review and the curation app

**What We Worked On:**
- Reviewed the docs for gaps and resolved a privacy contradiction.
- **ADR-004 rewritten:** encrypt cloud backups of `life.db`; retire the Word/Notion
  source docs after ingestion (DB becomes source of truth).
- **ADR-006 added:** local-first curation app — React + TipTap over a local FastAPI
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
- The app is best framed as the *curation hub*, not just an editor — it's where the
  pipeline's suggestions become confirmed data.

### 2026-06-24 - Structuring the source brief into the docs system

**What We Worked On:**
- Took the raw source brief (a French source file, since removed) and distributed it
  across the documentation structure.
- Filled the empty/template docs: vision, references, decisions (ADRs), and improvements.
- Added new files to give the material a coherent home:
  - `00_briefing/editorial-concept.md` — the book's structure and content layers.
  - `01_building/architecture.md` — the three-layer system + workflow + backups.
  - `01_building/data-model.md` — the full `life.db` schema reference.
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
- The non-negotiable thread across every doc: data is the source of truth, the
  renderer is replaceable. Everything else (durability, ownership, reproducibility)
  follows from that.
