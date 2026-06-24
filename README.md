# Lifebook — a durable autobiographical system

> Not a book, a system. The book is a snapshot; the data, analyses, and tools live on
> for decades. See the full [vision](docs/00_briefing/inspirations/vision.md).

A personal project to turn years of writing into a lasting, ownable archive — and to
publish high-quality printed books from it (a "volume" is a chosen date range; cadence
TBD — decade, 5-year, or yearly, depending on size and printing).

## How it works

`life.db` (SQLite) is the single source of truth. Three clients read/write it: a
local **curation app** (capture + review), the **Python** layer (import + NLP + stats),
and **publication** (render to PDF).

```
                 Curation app (React/TipTap + local FastAPI)
                              │ read/write
                              ▼
   Python (import, NLP, stats) ──►  life.db  ──► InDesign / Affinity ──► PDF
                                source of truth         render engine
```

The layout tool is just a render engine; the data outlives it. See
[architecture.md](docs/01_building/architecture.md).

## Documentation map

### `docs/00_briefing/` — what we're building and why
- [brief.md](docs/00_briefing/brief.md) — the project brief (goals, non-goals, success criteria).
- [vision.md](docs/00_briefing/inspirations/vision.md) — the long-term system vision.
- [product.md](docs/00_briefing/product.md) — the book's structure and content layers.

(Design principles live in [vision.md](docs/00_briefing/inspirations/vision.md#principles); personas live in [brief.md](docs/00_briefing/brief.md#who-its-for).)

### `docs/01_building/` — how it's built
- [architecture.md](docs/01_building/architecture.md) — `life.db` + its clients (app, Python, publication).
- [database.md](docs/01_building/database.md) — full `life.db` schema.
- [ingestion.md](docs/01_building/ingestion.md) — importing the Word/Notion backlog.
- [decisions.md](docs/01_building/decisions.md) — architectural decision records.
- [references.md](docs/01_building/references.md) — tools and external links.
- [learnings.md](docs/01_building/learnings.md) · [sessions.md](docs/01_building/sessions.md)

### `docs/02_fixing/` — [bugs.md](docs/02_fixing/bugs.md)
### `docs/03_planning/` — [improvements.md](docs/03_planning/improvements.md)

## Principles in one breath
Data is the source of truth · durability over convenience · full ownership ·
reproducible for any date range · privacy is a first-class feature · two clocks side by side.
