# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this is
**Lifebook** is a durable, ownable autobiographical system. The printed book is a
*snapshot* (a "volume" is a chosen date range; cadence undecided); the data and tooling
are the lasting product. Start with the [README](README.md) and the
[vision](docs/00_briefing/inspirations/vision.md).

## Core principle (do not violate)
**The data is the single source of truth.** `life.db` (SQLite) is authoritative. The
layout tool (InDesign / Affinity, or a future web renderer) is a *render engine* only.
The pipeline flows one way: `SQLite → Python → Export → InDesign → PDF`. Never treat a
typeset file as something to import back upstream.

See the [Principles section in vision.md](docs/00_briefing/inspirations/vision.md#principles)
before proposing changes: durability over convenience, full ownership, reproducible
for any date range, privacy first, two clocks (calendar + personal time).

## Architecture
`life.db` (SQLite) is the single source of truth; everything else is a client.
1. **Data.** SQLite `life.db`. Schema in [database.md](docs/01_building/database.md).
2. **Curation app.** Local-first React/TipTap + local FastAPI: write entries, review
   NLP suggestions, people/alias consolidation ([ADR-006](docs/01_building/decisions.md)).
3. **Processing.** Python (spaCy, Transformers, local LLM): import (Word/Notion, see
   [ingestion.md](docs/01_building/ingestion.md)), clean, extract people/themes/emotions, stats, export.
4. **Publication.** InDesign / Affinity Publisher to PDF.

The app and Python are both DB clients; see "who writes what" in
[architecture.md](docs/01_building/architecture.md). Python is the only language that
writes the DB.

## Working in the docs (dev journal)
- Before changing direction, check [decisions.md](docs/01_building/decisions.md) (ADRs).
- Log bug fixes in [bugs.md](docs/02_fixing/bugs.md), new concepts in
  [learnings.md](docs/01_building/learnings.md), AI sessions in
  [sessions.md](docs/01_building/sessions.md), and ideas in
  [improvements.md](docs/03_planning/improvements.md).
- Keep each doc in the format defined at the top of its file.

## Conventions
- Meta-documentation is written in **English**; the **content (entries) is French**, and
  tooling must be French-first: NLP models, date parsing, LLM prompts ([ADR-007](docs/01_building/decisions.md)).
- **In Git:** code, scripts, label-list CSVs, schemas, app source, docs. **Out of Git:**
  `life.db` (data), exported PDFs, large files. Back up 3-2-1 (local + cloud + cold);
  **encrypt the cloud copy** ([ADR-004](docs/01_building/decisions.md)).
- Write in a plain, human voice across prose, comments, docstrings, and commits. No em
  dashes; use periods, commas, colons, or parentheses. Avoid the AI tells: "X, not Y"
  antithesis, "it's not just X, it's Y" framing, filler adjectives, and bold scattered
  mid-sentence. Keep comments minimal and factual.
