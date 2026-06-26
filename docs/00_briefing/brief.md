# Project Brief: Lifebook

## One-liner
Build a durable, ownable autobiographical system ("Lifebook") that turns years of
personal writing into a lasting archive, and publishes high-quality printed books from
it (a "volume" is a chosen date range; cadence TBD: decade / 5-year / yearly).

## The problem
Years of personal writing (journal entries, books & citations, fun facts, fêtes,
prompts, tops…) accumulate in scattered Word documents and Notion. Turning them into a
keepsake book is a one-off effort that dies with the tool it was made in. What's needed
is a system that preserves the data, analyzes it, and can
reproduce a book for any span: this one and every one after.

## Goals
- **Centralize** all personal writings in one place.
- **Preserve** the data in durable, open formats.
- **Analyze** automatically: people, themes, emotions, statistics.
- **Generate** a high-quality printed book.
- **Reproduce** the process for each following volume (any date range).
- **Retain full ownership** of the data, forever.

## Non-goals
- Not a SaaS or hosted product. This is a personal, local-first system.
- Not driven by a layout tool: InDesign/Affinity render the book, they don't own the data.
- Not censorship of sensitive content: the goal is informed reader consent rather than removal.
- Not a one-off book. Every artifact must be regenerable from the data.

## The system
`life.db` (SQLite) is the single source of truth; everything else is a client of it.
```
        Curation app (React/TipTap + local FastAPI)
                       │ read/write
                       ▼
   Python (import, NLP, stats) ──► life.db ──► InDesign / Affinity ──► PDF
                              source of truth        render engine
```
1. **Data.** A single SQLite file is the source of truth ([database.md](../01_building/database.md)).
2. **Curation app.** Local-first; write entries and review the analysis suggestions.
3. **Processing.** Python scripts (spaCy, Transformers, local LLM) import, clean,
   extract, and analyze.
4. **Publication.** InDesign or Affinity Publisher renders the book to PDF.

Details in [architecture.md](../01_building/architecture.md). Key decisions in
[decisions.md](../01_building/decisions.md).

## The book
A **volume** (title and cadence TBD: *Décade* was a candidate when it was assumed to be
ten years; the span now depends on size/printing). Primarily chronological, with layered
content: yearly/monthly separators, numbered entries, books & citations, weekly fun
facts, prompts, yearly tops (songs, games, books, …), abécédaires, bingo, year-in-review
*fêtes*, and a final analytical cartography (people, themes, emotions, tops). Full spec
in [product.md](product.md).

## Who it's for
Ordered by priority. When needs conflict, the higher one wins.

- **The Author** (primary): owner, writer, and maintainer. Writes the entries, runs
  the pipeline, curates the analyses, and produces each volume. Technical enough
  to run Python and SQLite; cares about owning the data outright. Every decision serves
  this persona first: ownership, durability, and reproducibility outrank reader
  convenience or polish.
- **The Future Self** (archivist): the same author years or decades later, returning
  to reconstruct a past volume or publish the next. Needs the data to still open and
  the scripts to still run. This persona is *why* durability and reproducibility are
  non-negotiable; it outranks any outside reader.
- **The Loved One** (invited reader): family, partner, or friend reading the finished
  book. Holds the printed snapshot rather than the system. Shapes the *reading experience*
  (clear navigation, emotional pacing, and explicit warnings before sensitive content),
  but yields whenever their convenience conflicts with the two personas above.

## Guiding principles
Data is the source of truth · durability over convenience · full ownership ·
reproducible for any date range · privacy is a first-class feature · two clocks
(calendar + personal time) side by side. See the [Principles section in vision.md](inspirations/vision.md#principles).

## Success criteria
- A first volume is produced end-to-end from `life.db`.
- Re-running the pipeline reproduces the same output from the same data.
- The data survives independently of any layout tool, backed up 3-2-1.
- A future volume (any date range) can be published by re-running the same process.
